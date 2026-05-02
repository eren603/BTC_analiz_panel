#!/usr/bin/env python3
"""
leading_karar.py  -  SADECE GECIKMESIZ SINYALLERLE KARAR
==========================================================
Felsefe: Tahmin etme. Reaksiyon ver.

EMA, MA, scorecard, whale_acct, leading_decision -- hepsi
gecmis ortalamali, GECIKMELI. Bu script onlara HIC bakmaz.

Sadece SU AN piyasanin ne SOYLEDIGINE bakar:

  ANA (3 sinyal -- karar verici):
    1. depth_imbalance  -- emir defteri  (anlik)
    2. futures_cvd 5m   -- taker akisi   (anlik)
    3. funding rate     -- pozisyon maliyeti (anlik)

  YAN (2 sinyal -- onay/red):
    4. liquidations     -- likidite avi  (varsa)
    5. OI delta + 5m mum yonu -- pozisyon momentumu

KURAL:
  3 ANA sinyalden en az 2'si AYNI yone basmali.
  Yan sinyaller hizalaniyorsa onaylar, ters ise UYARI.
  Aksi halde BEKLE -- pozisyon ACMA.

Kullanim:
  python3 leading_karar.py
  (once auto_fetch.py veya auto_compact_fixed.py calismali --
   r_update.json olusturulmali)

==========================================================
"""

import json
import sys
from pathlib import Path

# --- Kalibrasyon esikleri ---
DEPTH_LONG_THR    = 1.20    # bid/ask orani bunun ustu = ALICI baskin
DEPTH_SHORT_THR   = 0.80    # bid/ask orani bunun alti = SATICI baskin
CVD_THR           = 200_000 # 5m taker delta -- onemli buyukluk
FUNDING_LONG_APR  = -3.0    # APR bunun altinda = SHORT prim aliyor (LONG sinyal)
FUNDING_SHORT_APR = +3.0    # APR bunun ustunde = LONG prim aliyor (SHORT sinyal)
LIQ_RATIO_THR     = 1.5     # bir taraf digerinin 1.5 kati = anlamli
OI_DELTA_THR      = 100     # OI degisimi bunun altinda = onemsiz

ANA_ALIGN_MIN = 2  # 3 ana sinyalden en az 2'si ayni yon


# ----------------------------------------------------------
#  VERI YOLU
# ----------------------------------------------------------

def find_r_update():
    """r_update.json'u bul."""
    candidates = [
        Path(__file__).parent / "r_update.json",
        Path.cwd() / "r_update.json",
        Path("/storage/emulated/0/Download/r_update.json"),
        Path("/storage/emulated/0/Downloads/r_update.json"),
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


# ----------------------------------------------------------
#  ANA SINYALLER
# ----------------------------------------------------------

def eval_depth(d1h):
    """Order book bid/ask imbalance -- LEADING.

    >1.0 ALICI baskin / <1.0 SATICI baskin.
    Manipule edilmesi cok pahali -- en taze gercek sinyal.
    """
    val = float(d1h.get("depth_imbalance", 1.0))
    if val >= DEPTH_LONG_THR:
        return val, "LONG",  f"alici %{(val/(val+1))*100:.0f} baskin (oran {val:.2f})"
    if val <= DEPTH_SHORT_THR:
        # ornek: 0.35 -> satici baskin
        sat_pct = 1 / (1 + val) * 100
        return val, "SHORT", f"satici %{sat_pct:.0f} baskin (oran {val:.2f})"
    return val, "NOTR",  f"dengeli (oran {val:.2f})"


def eval_cvd(d5m):
    """Futures CVD 5m -- taker akisi, LEADING.

    Pozitif = market emriyle ALANLAR baskin.
    Negatif = market emriyle SATANLAR baskin.
    """
    val = float(d5m.get("futures_cvd", 0))
    if val >= CVD_THR:
        return val, "LONG",  f"alici taker baskin (CVD {val:+,.0f})"
    if val <= -CVD_THR:
        return val, "SHORT", f"satici taker baskin (CVD {val:+,.0f})"
    return val, "NOTR",  f"akis zayif (CVD {val:+,.0f})"


def eval_funding(d1h):
    """Funding rate -- squeeze yonu, LEADING.

    Negatif APR  -> SHORT prim aliyor -> LONG'lar sikisik -> LONG patlamasi olasi
    Pozitif APR  -> LONG prim aliyor  -> SHORT'lar sikisik -> SHORT patlamasi olasi
    """
    fr = d1h.get("funding_rate")
    if fr is None:
        return None, "NOTR", "funding verisi yok"
    apr = float(fr) * 3 * 365 * 100
    if apr <= FUNDING_LONG_APR:
        return apr, "LONG",  f"SHORT prim aliyor, squeeze yukari ({apr:+.1f}% APR)"
    if apr >= FUNDING_SHORT_APR:
        return apr, "SHORT", f"LONG prim aliyor, squeeze asagi ({apr:+.1f}% APR)"
    return apr, "NOTR",  f"dengeli ({apr:+.1f}% APR)"


# ----------------------------------------------------------
#  YAN SINYALLER (onay)
# ----------------------------------------------------------

def eval_liquidations(d1h):
    """Likidasyon avi -- LEADING (varsa).

    Bir tarafta likidasyon kasilirsa, o taraf SIKISIYOR -> trend devam.
    Coinglass kapaliyken zaten 0 -- NOTR.
    """
    liq = d1h.get("liquidations") or {}
    long_liq  = float(liq.get("long",  0))
    short_liq = float(liq.get("short", 0))
    if long_liq + short_liq < 1000:
        return (long_liq, short_liq), "NOTR", "likidasyon yok / Coinglass kapali"
    if long_liq > short_liq * LIQ_RATIO_THR:
        # LONG'lar likide oluyor -> trend asagi devam ediyor
        return (long_liq, short_liq), "SHORT", \
               f"LONG likidasyon agir (${long_liq:,.0f} vs ${short_liq:,.0f})"
    if short_liq > long_liq * LIQ_RATIO_THR:
        return (long_liq, short_liq), "LONG", \
               f"SHORT likidasyon agir (${short_liq:,.0f} vs ${long_liq:,.0f})"
    return (long_liq, short_liq), "NOTR", \
           f"dengeli (L=${long_liq:,.0f} S=${short_liq:,.0f})"


def eval_oi_momentum(d1h, candles):
    """OI delta + 5m mum yonu birlikte -- pozisyon momentumu.

    OI tek basina yon vermez. 5m mumun yonuyle birlestirilir:
      OI+ fiyat+  -> LONG trend devam
      OI- fiyat-  -> SHORT trend zayifliyor (LONG firsati)
      OI- fiyat+  -> LONG trend zayifliyor (SHORT firsati)
      OI+ fiyat-  -> SHORT trend devam
    """
    delta = d1h.get("oi_delta")
    if delta is None:
        return None, "NOTR", "OI delta verisi yok"
    delta = float(delta)
    if abs(delta) < OI_DELTA_THR:
        return delta, "NOTR", f"OI degisimi onemsiz ({delta:+.0f})"

    c5 = (candles or {}).get("5m", {}).get("curr") or {}
    if not c5:
        return delta, "NOTR", f"OI {delta:+.0f} ama 5m mum verisi yok"
    open_p  = float(c5.get("open",  0))
    close_p = float(c5.get("close", 0))
    if open_p == 0:
        return delta, "NOTR", f"OI {delta:+.0f} ama 5m mum bozuk"

    price_up = close_p > open_p

    if price_up and delta > 0:
        return delta, "LONG",  f"OI+ fiyat+ = LONG trend devam (oi {delta:+.0f})"
    if (not price_up) and delta < 0:
        return delta, "LONG",  f"OI- fiyat- = SHORT zayifliyor / dip (oi {delta:+.0f})"
    if price_up and delta < 0:
        return delta, "SHORT", f"OI- fiyat+ = LONG zayifliyor / tepe (oi {delta:+.0f})"
    if (not price_up) and delta > 0:
        return delta, "SHORT", f"OI+ fiyat- = SHORT trend devam (oi {delta:+.0f})"

    return delta, "NOTR", f"belirsiz (oi {delta:+.0f})"


# ----------------------------------------------------------
#  ANA AKIS
# ----------------------------------------------------------

def main():
    rj = find_r_update()
    if not rj:
        print("HATA: r_update.json bulunamadi.")
        print("      Once: python3 auto_fetch.py")
        print("      veya  python3 auto_compact_fixed.py")
        return 1

    with open(rj, encoding="utf-8") as f:
        data = json.load(f)

    d5m = data.get("data_5m") or {}
    d1h = data.get("data_1h") or {}
    candles = data.get("candles") or {}
    price = d1h.get("current_price") or d5m.get("current_price", 0)

    bar = "=" * 72
    print()
    print(bar)
    print(f"  LEADING-ONLY KARAR  -  ${price:,.0f}")
    print(f"  Felsefe: tahmin etme, reaksiyon ver. Gecikmesiz sinyal.")
    print(bar)
    print()

    # --- ANA 3 sinyal ---
    print("  ANA SINYALLER (karar verici)")
    print("  " + "-"*68)
    sinyal_ana = []
    sinyal_ana.append(("1. DEPTH IMBALANCE",  *eval_depth(d1h)))
    sinyal_ana.append(("2. CVD 5m (taker)",    *eval_cvd(d5m)))
    sinyal_ana.append(("3. FUNDING APR",       *eval_funding(d1h)))

    long_a = short_a = notr_a = 0
    for ad, val, yon, neden in sinyal_ana:
        mark = {"LONG": "[+]", "SHORT": "[-]", "NOTR": "[ ]"}.get(yon, "[?]")
        print(f"  {mark} {ad:<22} -> {yon:<6} {neden}")
        if   yon == "LONG":  long_a  += 1
        elif yon == "SHORT": short_a += 1
        else:                notr_a  += 1

    print()
    print("  YAN SINYALLER (onay/red)")
    print("  " + "-"*68)
    sinyal_yan = []
    sinyal_yan.append(("4. LIKIDASYON",   *eval_liquidations(d1h)))
    sinyal_yan.append(("5. OI MOMENTUM",  *eval_oi_momentum(d1h, candles)))

    long_y = short_y = 0
    for ad, val, yon, neden in sinyal_yan:
        mark = {"LONG": "[+]", "SHORT": "[-]", "NOTR": "[ ]"}.get(yon, "[?]")
        print(f"  {mark} {ad:<22} -> {yon:<6} {neden}")
        if   yon == "LONG":  long_y  += 1
        elif yon == "SHORT": short_y += 1

    print()
    print("  " + "="*68)
    print(f"  ANA HIZALANMA   :  LONG={long_a}  SHORT={short_a}  NOTR={notr_a}")
    print(f"  YAN HIZALANMA   :  LONG={long_y}  SHORT={short_y}")
    print("  " + "="*68)
    print()

    # --- KARAR ---
    if long_a >= ANA_ALIGN_MIN and long_a > short_a:
        guc = "GUCLU" if long_a == 3 else "ORTA"
        print(f"  >>> KARAR: GIR LONG  ({long_a}/3 ana sinyal LONG, {guc} hizalanma)")
        if long_y > short_y:
            print(f"      Yan sinyallerle ek onay (+{long_y}) -- guven yuksek.")
        elif short_y > 0:
            print(f"      UYARI: Yan sinyalde {short_y} ters onay -- POZISYONU KUCULT.")
        else:
            print(f"      Yan sinyaller notr -- normal pozisyon.")
        if short_a >= 1:
            print(f"      DIKKAT: {short_a} ana sinyal HALA SHORT yonunde -- temkinli ol.")

    elif short_a >= ANA_ALIGN_MIN and short_a > long_a:
        guc = "GUCLU" if short_a == 3 else "ORTA"
        print(f"  >>> KARAR: GIR SHORT  ({short_a}/3 ana sinyal SHORT, {guc} hizalanma)")
        if short_y > long_y:
            print(f"      Yan sinyallerle ek onay (+{short_y}) -- guven yuksek.")
        elif long_y > 0:
            print(f"      UYARI: Yan sinyalde {long_y} ters onay -- POZISYONU KUCULT.")
        else:
            print(f"      Yan sinyaller notr -- normal pozisyon.")
        if long_a >= 1:
            print(f"      DIKKAT: {long_a} ana sinyal HALA LONG yonunde -- temkinli ol.")

    else:
        print(f"  >>> KARAR: BEKLE")
        print(f"      Ana sinyallerden en az {ANA_ALIGN_MIN}/3'u ayni yone basmadi.")
        print(f"      Yon belirsiz -- POZISYON ACMA.")
        print(f"      Sonraki snapshot'a bak. Pas gec. Kahve ic.")

    print()
    print(bar)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
