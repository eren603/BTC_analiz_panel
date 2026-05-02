#!/usr/bin/env python3
"""
leading_karar.py  v2  -  GECIKMESIZ SINYALLERLE KARAR (kalibre edilmis)
======================================================================
Felsefe: Tahmin etme. Reaksiyon ver. Kalibrasyon yetersizken sus.

V2 DEGISIKLIK NOTU (R40-R42 kismi backtest sonrasi):
  - R41 yanlis yon sorunu: funding moderate seviyede contrarian sinyal
    yaniltici. Cozum: funding price-action ile birlestirildi.
      Funding+ + Price up   = LONG momentum
      Funding+ + Price down = LONG distribution (contrarian SHORT)
      Funding- + Price down = SHORT pro-trend
      Funding- + Price up   = SHORT squeeze (contrarian LONG)
  - OI logic: funding context dahil edildi. price+ + OI- + funding<-1.5 =
    LONG (short cover devam eder). price+ + OI- + funding zayif = SHORT.
  - CVD: GUCLU/ZAYIF kademesi eklendi (100k/500k esikleri).
  - Depth: GUCLU/ZAYIF kademesi (1.20/2.00 ve 0.80/0.50).
  - LSR cross-TF (1h vs 4h ayrismasi) WARNING olarak eklendi.
  - "EDGE CASE" bolumu — esik kenarlarinda guvensizlik uyarilir.

DURUSTLUK NOTU:
  - Liquidations Coinglass kapali oldugu icin DORMANT. Script efektif
    4 sinyal calistiriyor, 5 degil.
  - Esikler kalibre DEGIL — ilk tahmin. Backtest icin gerekli tarihsel
    snapshot verisi (her r_update.json'in arsivlenmesi) yok.
  - Kismi backtest (n=3 reconstruction):
      R40: NO_DATA (leading kayitsiz) -> BEKLE
      R41 v1: GIR SHORT (yanlis), v2: BEKLE (fix)
      R42 v1: GIR LONG (dogru), v2: GIR LONG (korundu)

Kullanim:
  python3 leading_karar.py
  (auto_fetch.py veya auto_compact_fixed.py once calismali)
"""

import json
import sys
from pathlib import Path

# === Esikler (kalibre DEGIL) ===
DEPTH_LONG_THR     = 1.20
DEPTH_LONG_STRONG  = 2.00
DEPTH_SHORT_THR    = 0.80
DEPTH_SHORT_STRONG = 0.50

CVD_THR_WEAK   = 100_000
CVD_THR_STRONG = 500_000

FUNDING_LONG_EXTREME  = -5.0
FUNDING_SHORT_EXTREME = +5.0
FUNDING_WEAK_BAND     = 1.5

OI_DELTA_THR = 100

ANA_ALIGN_MIN = 2


# === Veri yolu ===
def find_r_update():
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


# === ANA SINYALLER ===

def eval_depth(d1h):
    """Order book bid/ask imbalance (anlik)."""
    val = float(d1h.get("depth_imbalance", 1.0))
    if val >= DEPTH_LONG_STRONG:
        return val, "LONG", "GUCLU", f"alici cok agir basiyor ({val:.2f})"
    if val >= DEPTH_LONG_THR:
        return val, "LONG", "ZAYIF", f"alici hafif baskin ({val:.2f})"
    if val <= DEPTH_SHORT_STRONG:
        sat_pct = 1 / (1 + val) * 100
        return val, "SHORT", "GUCLU", f"satici %{sat_pct:.0f} cok agir ({val:.2f})"
    if val <= DEPTH_SHORT_THR:
        sat_pct = 1 / (1 + val) * 100
        return val, "SHORT", "ZAYIF", f"satici %{sat_pct:.0f} hafif baskin ({val:.2f})"
    return val, "NOTR", "—", f"dengeli ({val:.2f})"


def eval_cvd(d5m):
    """Futures CVD 5m taker akisi."""
    val = float(d5m.get("futures_cvd", 0))
    if val >= CVD_THR_STRONG:
        return val, "LONG", "GUCLU", f"alici taker cok baskin (CVD {val:+,.0f})"
    if val >= CVD_THR_WEAK:
        return val, "LONG", "ZAYIF", f"alici taker hafif baskin (CVD {val:+,.0f})"
    if val <= -CVD_THR_STRONG:
        return val, "SHORT", "GUCLU", f"satici taker cok baskin (CVD {val:+,.0f})"
    if val <= -CVD_THR_WEAK:
        return val, "SHORT", "ZAYIF", f"satici taker hafif baskin (CVD {val:+,.0f})"
    return val, "NOTR", "—", f"akis zayif (CVD {val:+,.0f})"


def eval_funding(d1h, candles=None):
    """Funding rate — price-action ile birlestirilir (R41 dersi).

    Standalone contrarian guvenilmez. Kombinasyon:
      Funding+ + Price up   = LONG momentum onay (pro-trend LONG)
      Funding+ + Price down = LONG distribution (contrarian SHORT)
      Funding- + Price down = SHORT momentum onay (pro-trend SHORT)
      Funding- + Price up   = SHORT squeeze (contrarian LONG)
      Extreme + ters yon    = GUCLU; Moderate = ZAYIF
    """
    fr = d1h.get("funding_rate")
    if fr is None:
        return None, "NO_DATA", "—", "funding verisi yok"
    apr = float(fr) * 3 * 365 * 100

    if abs(apr) < FUNDING_WEAK_BAND:
        return apr, "NOTR", "—", f"dengeli ({apr:+.1f}% APR)"

    # Price direction lazim
    price_up = None
    if candles:
        c5 = (candles or {}).get("5m", {}).get("curr") or {}
        if c5:
            o = float(c5.get("open", 0))
            c = float(c5.get("close", 0))
            if o > 0:
                price_up = c > o

    is_extreme = (apr <= FUNDING_LONG_EXTREME) or (apr >= FUNDING_SHORT_EXTREME)
    guc = "GUCLU" if is_extreme else "ZAYIF"

    if price_up is None:
        return apr, "NOTR", "WARNING", \
               f"funding {apr:+.1f}% APR ama price yon yok — sinyal degil"

    # Funding negatif (SHORT crowded)
    if apr < 0:
        if price_up:
            return apr, "LONG", guc, \
                   f"SHORT crowding ({apr:+.1f}%) + p+ = squeeze rally"
        else:
            return apr, "SHORT", guc, \
                   f"SHORT crowding ({apr:+.1f}%) + p- = SHORT pro-trend"
    # Funding pozitif (LONG crowded)
    else:
        if price_up:
            return apr, "LONG", guc, \
                   f"LONG crowding ({apr:+.1f}%) + p+ = LONG momentum"
        else:
            return apr, "SHORT", guc, \
                   f"LONG crowding ({apr:+.1f}%) + p- = distribution"


# === YAN SINYALLER ===

def eval_liquidations(d1h):
    """Likidasyon (Coinglass kapali ise dormant)."""
    liq = d1h.get("liquidations") or {}
    long_liq  = float(liq.get("long",  0))
    short_liq = float(liq.get("short", 0))
    if long_liq + short_liq < 1000:
        return (long_liq, short_liq), "DORMANT", "—", \
               "Coinglass kapali / veri yok (yan sinyal devre disi)"
    if long_liq > short_liq * 1.5:
        return (long_liq, short_liq), "SHORT", "ZAYIF", \
               f"LONG likidasyon agir (${long_liq:,.0f})"
    if short_liq > long_liq * 1.5:
        return (long_liq, short_liq), "LONG", "ZAYIF", \
               f"SHORT likidasyon agir (${short_liq:,.0f})"
    return (long_liq, short_liq), "NOTR", "—", \
           f"dengeli (L=${long_liq:,.0f} S=${short_liq:,.0f})"


def eval_oi_with_funding_context(d1h, candles):
    """OI delta + 5m mum yonu + funding context.

    V2: short-cover rally ayrimi.
      price+ + OI- + funding negatif (SHORT crowded) = LONG (squeeze devam)
      price+ + OI- + funding zayif = SHORT (LONG zayifliyor, normal short cover fade)
    """
    delta = d1h.get("oi_delta")
    if delta is None:
        return None, "NO_DATA", "—", "OI delta verisi yok"
    delta = float(delta)
    if abs(delta) < OI_DELTA_THR:
        return delta, "NOTR", "—", f"OI degisimi onemsiz ({delta:+.0f})"

    c5 = (candles or {}).get("5m", {}).get("curr") or {}
    if not c5:
        return delta, "NOTR", "—", f"OI {delta:+.0f} ama 5m mum yok"
    open_p = float(c5.get("open", 0))
    close_p = float(c5.get("close", 0))
    if open_p == 0:
        return delta, "NOTR", "—", f"OI {delta:+.0f} ama 5m mum bozuk"
    price_up = close_p > open_p

    fr = d1h.get("funding_rate")
    apr = (fr * 3 * 365 * 100) if fr is not None else 0.0
    short_crowded = apr < -FUNDING_WEAK_BAND
    long_crowded = apr > FUNDING_WEAK_BAND

    if price_up and delta > 0:
        return delta, "LONG", "ZAYIF", f"OI+ p+ = yeni LONG akisi"
    if (not price_up) and delta < 0:
        return delta, "LONG", "ZAYIF", f"OI- p- = SHORT zayifliyor / dip"
    if price_up and delta < 0:
        if short_crowded:
            return delta, "LONG", "ZAYIF", \
                   f"OI- p+ + SHORT crowding ({apr:+.1f}%) = squeeze devam"
        else:
            return delta, "SHORT", "ZAYIF", \
                   f"OI- p+ + funding zayif = LONG zayifliyor (short cover fade)"
    if (not price_up) and delta > 0:
        if long_crowded:
            return delta, "SHORT", "ZAYIF", \
                   f"OI+ p- + LONG crowding ({apr:+.1f}%) = stop hunt asagi"
        else:
            return delta, "SHORT", "ZAYIF", f"OI+ p- = SHORT yeni akis"
    return delta, "NOTR", "—", f"belirsiz ({delta:+.0f})"


def eval_lsr_cross_tf(data):
    """LSR 1h ve 4h ayrismasi — TF split warning."""
    d1h = data.get("data_1h") or {}
    d4h = data.get("data_4h") or {}
    ls1 = d1h.get("taker_ls_ratio")
    ls4 = d4h.get("taker_ls_ratio")
    if ls1 is None or ls4 is None:
        return None, "NO_DATA", "LSR verisi eksik"
    ls1 = float(ls1); ls4 = float(ls4)
    diff = abs(ls1 - ls4)

    same_side_long  = ls1 > 1.0 and ls4 > 1.0
    same_side_short = ls1 < 1.0 and ls4 < 1.0

    if same_side_long and diff < 0.10:
        return (ls1, ls4), "ALIGN_LONG", \
               f"LSR 1h+4h LONG hizali (1h={ls1:.2f} 4h={ls4:.2f})"
    if same_side_short and diff < 0.10:
        return (ls1, ls4), "ALIGN_SHORT", \
               f"LSR 1h+4h SHORT hizali (1h={ls1:.2f} 4h={ls4:.2f})"
    if (ls1 > 1.0) != (ls4 > 1.0):
        return (ls1, ls4), "SPLIT", \
               f"LSR TF SPLIT (1h={ls1:.2f} {'>' if ls1>1 else '<'}1, " \
               f"4h={ls4:.2f} {'>' if ls4>1 else '<'}1)"
    return (ls1, ls4), "DIVERGE", \
           f"LSR ayni taraf ama uzak (1h={ls1:.2f} 4h={ls4:.2f})"


# === ANA AKIS ===

def main():
    rj = find_r_update()
    if not rj:
        print("HATA: r_update.json yok. Once auto_fetch.py / auto_compact_fixed.py")
        return 1

    with open(rj, encoding="utf-8") as f:
        data = json.load(f)

    d5m = data.get("data_5m") or {}
    d1h = data.get("data_1h") or {}
    candles = data.get("candles") or {}
    price = d1h.get("current_price") or d5m.get("current_price", 0)

    bar = "=" * 76
    print()
    print(bar)
    print(f"  LEADING-ONLY KARAR v2  -  ${price:,.0f}")
    print(f"  Felsefe: tahmin etme, reaksiyon ver. Sinyal yoksa BEKLE.")
    print(bar)
    print()

    print("  ANA SINYALLER (karar verici)")
    print("  " + "-" * 72)
    sinyal_ana = []
    sinyal_ana.append(("1. DEPTH IMBALANCE", *eval_depth(d1h)))
    sinyal_ana.append(("2. CVD 5m (taker)",   *eval_cvd(d5m)))
    sinyal_ana.append(("3. FUNDING APR",      *eval_funding(d1h, candles)))

    long_a = short_a = notr_a = nodata_a = warning_a = 0
    edge_cases = []

    for ad, val, yon, guc, neden in sinyal_ana:
        mark = {"LONG": "[+]", "SHORT": "[-]", "NOTR": "[ ]",
                "NO_DATA": "[?]"}.get(yon, "[?]")
        guc_str = f"({guc})" if guc != "—" else ""
        print(f"  {mark} {ad:<22} -> {yon:<8} {guc_str:<10} {neden}")
        if   yon == "LONG":    long_a += 1
        elif yon == "SHORT":   short_a += 1
        elif yon == "NO_DATA": nodata_a += 1
        else:                  notr_a += 1
        if guc == "WARNING":   warning_a += 1
        if guc == "ZAYIF":
            edge_cases.append(f"{ad}: {yon} ZAYIF (esik kenarinda)")

    print()
    print("  YAN SINYALLER (onay/red)")
    print("  " + "-" * 72)
    sinyal_yan = []
    sinyal_yan.append(("4. LIKIDASYON",  *eval_liquidations(d1h)))
    sinyal_yan.append(("5. OI MOMENTUM", *eval_oi_with_funding_context(d1h, candles)))

    long_y = short_y = 0
    dormant_count = 0
    for ad, val, yon, guc, neden in sinyal_yan:
        mark = {"LONG": "[+]", "SHORT": "[-]", "NOTR": "[ ]",
                "NO_DATA": "[?]", "DORMANT": "[X]"}.get(yon, "[?]")
        guc_str = f"({guc})" if guc != "—" else ""
        print(f"  {mark} {ad:<22} -> {yon:<8} {guc_str:<10} {neden}")
        if   yon == "LONG":    long_y += 1
        elif yon == "SHORT":   short_y += 1
        elif yon == "DORMANT": dormant_count += 1

    print()
    print("  EK KONTROL: LSR Cross-TF")
    print("  " + "-" * 72)
    lsr_val, lsr_status, lsr_msg = eval_lsr_cross_tf(data)
    print(f"  >>> {lsr_status}: {lsr_msg}")
    if lsr_status == "SPLIT":
        edge_cases.append("LSR TF split — yon belirsizligi yuksek")

    print()
    print("  " + "=" * 72)
    print(f"  ANA HIZALANMA   :  LONG={long_a}  SHORT={short_a}  "
          f"NOTR={notr_a}  NO_DATA={nodata_a}")
    if warning_a:
        print(f"  WARNING'LAR     :  {warning_a} adet")
    print("  " + "=" * 72)
    print()

    if nodata_a >= 2:
        print(f"  >>> KARAR: VERIFIY EDILEMEZ")
        print(f"      ANA sinyallerin {nodata_a}'i NO_DATA. Veri eksik.")
    elif long_a >= ANA_ALIGN_MIN and long_a > short_a:
        guc_total = "GUCLU" if long_a == 3 else "ORTA"
        print(f"  >>> KARAR: GIR LONG  ({long_a}/3 ana sinyal LONG, {guc_total})")
        if long_y > short_y:
            print(f"      Yan sinyal +{long_y} onay")
        elif short_y > 0:
            print(f"      UYARI: yan sinyalde {short_y} ters onay -> POZISYONU KUCULT")
        if short_a >= 1:
            print(f"      DIKKAT: {short_a} ana sinyal hala SHORT")
        if lsr_status == "SPLIT":
            print(f"      DIKKAT: LSR TF SPLIT — yon belirsiz, kucuk pozisyon")
    elif short_a >= ANA_ALIGN_MIN and short_a > long_a:
        guc_total = "GUCLU" if short_a == 3 else "ORTA"
        print(f"  >>> KARAR: GIR SHORT ({short_a}/3 ana sinyal SHORT, {guc_total})")
        if short_y > long_y:
            print(f"      Yan sinyal +{short_y} onay")
        elif long_y > 0:
            print(f"      UYARI: yan sinyalde {long_y} ters onay -> POZISYONU KUCULT")
        if long_a >= 1:
            print(f"      DIKKAT: {long_a} ana sinyal hala LONG")
        if lsr_status == "SPLIT":
            print(f"      DIKKAT: LSR TF SPLIT — yon belirsiz, kucuk pozisyon")
    else:
        print(f"  >>> KARAR: BEKLE")
        print(f"      ANA sinyallerden en az {ANA_ALIGN_MIN}/3 ayni yon basmadi.")

    if edge_cases:
        print()
        print("  EDGE CASE UYARILARI (esik kenarlari):")
        for ec in edge_cases:
            print(f"    - {ec}")

    print()
    print("  DURUSTLUK UYARILARI:")
    if dormant_count > 0:
        print("    - Liquidations DORMANT (Coinglass kapali). Efektif 4 sinyal.")
    if warning_a:
        for ad, val, yon, guc, neden in sinyal_ana:
            if guc == "WARNING":
                print(f"    - {ad}: WARNING bolgesinde ({neden})")
    print(f"    - Esikler kalibre DEGIL — backtest yetersiz (n=3 kismi reconstruction)")

    print()
    print(bar)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
