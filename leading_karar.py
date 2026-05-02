#!/usr/bin/env python3
"""
leading_karar.py  v3  -  EMPIRIK KALIBRE + LIVE OVERLAY = TEK KARAR
====================================================================

KAYNAK: Notion Runs database (R2-R42, n=35 kapali run).
Kalibrasyon CSV (deplasman_20260430_014550.csv) uzerinden test edildi.

EMPIRIK KURALLAR (kanitlanmis, % gercek backtest):
  R1: LS_1h > 1.50                          -> LONG  86% (n=7)
  R2: depl_4h<-1.0 AND LS_1h>1.0            -> LONG  83% (n=6)
  R3: whale>1.0 AND LS_1h>1.0               -> LONG  80% (n=10)
  R4: LS_1h > 1.20                          -> LONG  73% (n=11)
  R5: whale > 1.05                          -> LONG  100% (n=3, az ornek)
  R6: hicbiri yok                           -> BEKLE veya overlay'a bak

SHORT KURALI YOK: Notion verisinde SHORT zayif (P79: %67 vs %95 LONG).
SHORT acmak icin: live overlay 3+/4 SHORT der ise DIKKATLI olarak isaretler.
Yoksa SHORT acmaktan kacin (data-driven).

LIVE OVERLAY (r_update.json):
  - depth_imbalance, CVD 5m, funding (price-aware), OI delta
  - Empirik karari TEYIT eder ya da CELER (uyari)

KULLANIM:
  python3 leading_karar.py
  (auto_fetch.py / auto_compact_fixed.py once calismali)
"""

import json
import sys
from pathlib import Path


# === Empirik esikler (n=35 backtest, KALIBRE) ===
LS_STRONG_LONG    = 1.50
LS_LONG           = 1.20
WHALE_STRONG_LONG = 1.05
WHALE_LONG        = 1.00
DEPL_DIP_THR      = -1.0

# === Live overlay esikleri (kalibre DEGIL) ===
DEPTH_LONG_THR    = 1.20
DEPTH_LONG_STRONG = 2.00
DEPTH_SHORT_THR   = 0.80
DEPTH_SHORT_STRONG = 0.50
CVD_THR_WEAK      = 100_000
CVD_THR_STRONG    = 500_000
FUNDING_EXTREME   = 5.0
FUNDING_WEAK      = 1.5
OI_THR            = 100


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


# ============================================================
#  EMPIRIK KARAR — Notion verisi, kanitlanmis
# ============================================================

def empirik_karar(whale, ls, depl):
    """Notion'da n=35 backtest'le dogrulanmis kurallar.
    Returns: (yon, dogruluk_pct, n, kural_adi) veya (None, 0, 0, sebep)
    """
    if ls is not None and ls > LS_STRONG_LONG:
        return "LONG", 86, 7, "R1: LS>1.50"
    if ls is not None and depl is not None and depl < DEPL_DIP_THR and ls > 1.0:
        return "LONG", 83, 6, "R2: depl<-1.0 + LS>1.0 (dip toplama)"
    if whale is not None and ls is not None and whale > WHALE_LONG and ls > 1.0:
        return "LONG", 80, 10, "R3: whale>1.0 + LS>1.0"
    if ls is not None and ls > LS_LONG:
        return "LONG", 73, 11, "R4: LS>1.20"
    if whale is not None and whale > WHALE_STRONG_LONG:
        return "LONG", 100, 3, "R5: whale>1.05 (n=3 az ornek)"
    return None, 0, 0, "hicbir empirik kural tetiklenmedi"


# ============================================================
#  LIVE OVERLAY
# ============================================================

def overlay_depth(d1h):
    val = float(d1h.get("depth_imbalance", 1.0))
    if val >= DEPTH_LONG_STRONG: return val, "LONG", "GUCLU"
    if val >= DEPTH_LONG_THR:    return val, "LONG", "ZAYIF"
    if val <= DEPTH_SHORT_STRONG: return val, "SHORT", "GUCLU"
    if val <= DEPTH_SHORT_THR:   return val, "SHORT", "ZAYIF"
    return val, "NOTR", "—"


def overlay_cvd(d5m):
    val = float(d5m.get("futures_cvd", 0))
    if val >= CVD_THR_STRONG:  return val, "LONG", "GUCLU"
    if val >= CVD_THR_WEAK:    return val, "LONG", "ZAYIF"
    if val <= -CVD_THR_STRONG: return val, "SHORT", "GUCLU"
    if val <= -CVD_THR_WEAK:   return val, "SHORT", "ZAYIF"
    return val, "NOTR", "—"


def overlay_funding(d1h, candles):
    """Price-aware funding (v2 dersinden)."""
    fr = d1h.get("funding_rate")
    if fr is None: return None, "NO_DATA", "—", None
    apr = float(fr) * 3 * 365 * 100
    if abs(apr) < FUNDING_WEAK:
        return apr, "NOTR", "—", None
    c5 = (candles or {}).get("5m", {}).get("curr") or {}
    price_up = None
    if c5:
        o = float(c5.get("open", 0)); c = float(c5.get("close", 0))
        if o > 0: price_up = c > o
    is_extreme = abs(apr) >= FUNDING_EXTREME
    guc = "GUCLU" if is_extreme else "ZAYIF"
    if price_up is None:
        return apr, "NOTR", "WARNING", "price yon yok"
    if apr < 0:
        return (apr, "LONG" if price_up else "SHORT", guc,
                "SHORT crowding+p+" if price_up else "SHORT pro-trend")
    return (apr, "LONG" if price_up else "SHORT", guc,
            "LONG momentum" if price_up else "LONG distribution")


def overlay_oi(d1h, candles):
    delta = d1h.get("oi_delta")
    if delta is None: return None, "NO_DATA", "—"
    delta = float(delta)
    if abs(delta) < OI_THR: return delta, "NOTR", "—"
    c5 = (candles or {}).get("5m", {}).get("curr") or {}
    if not c5: return delta, "NOTR", "—"
    o = float(c5.get("open", 0)); c = float(c5.get("close", 0))
    if o == 0: return delta, "NOTR", "—"
    price_up = c > o
    fr = d1h.get("funding_rate")
    apr = (fr * 3 * 365 * 100) if fr is not None else 0.0
    short_crowded = apr < -FUNDING_WEAK
    long_crowded = apr > FUNDING_WEAK
    if price_up and delta > 0:    return delta, "LONG", "yeni LONG"
    if (not price_up) and delta < 0: return delta, "LONG", "SHORT zayifliyor"
    if price_up and delta < 0:
        if short_crowded: return delta, "LONG", "squeeze devam"
        return delta, "SHORT", "short cover fade"
    if (not price_up) and delta > 0:
        if long_crowded: return delta, "SHORT", "stop hunt"
        return delta, "SHORT", "SHORT yeni"
    return delta, "NOTR", "—"


# ============================================================
#  ANA AKIS
# ============================================================

def main():
    rj = find_r_update()
    if not rj:
        print("HATA: r_update.json yok. Once auto_fetch.py / auto_compact_fixed.py")
        return 1

    with open(rj, encoding="utf-8") as f:
        data = json.load(f)

    d5m = data.get("data_5m") or {}
    d1h = data.get("data_1h") or {}
    d4h = data.get("data_4h") or {}
    candles = data.get("candles") or {}

    price = d1h.get("current_price") or d5m.get("current_price", 0)
    whale = d1h.get("whale_acct_ls")
    ls    = d1h.get("taker_ls_ratio")
    p4    = d4h.get("current_price")
    ma30  = d4h.get("ma30")
    depl  = ((p4 - ma30) / ma30 * 100) if (p4 and ma30 and ma30 > 0) else None

    bar = "=" * 76
    print()
    print(bar)
    print(f"  LEADING KARAR v3  -  ${price:,.0f}")
    print(f"  Empirik kalibre (Notion n=35) + live overlay")
    print(bar)
    print()

    # 1) Empirik
    print("  1) EMPIRIK KURALLAR (Notion n=35 backtest)")
    print("  " + "-" * 72)
    if depl is not None:
        print(f"  Veri:  whale={whale}  LS_1h={ls}  depl_4h={depl:+.2f}%")
    else:
        print(f"  Veri:  whale={whale}  LS_1h={ls}  depl=YOK")
    print()
    yon_emp, guc_pct, n, kural = empirik_karar(whale, ls, depl)
    if yon_emp:
        print(f"  >>> Tetiklenen: {kural}")
        print(f"      Yon: {yon_emp}, gercekleme: %{guc_pct} (n={n})")
    else:
        print(f"  >>> {kural}")

    # 2) Overlay
    print()
    print("  2) LIVE OVERLAY (r_update.json anlik)")
    print("  " + "-" * 72)
    d_v, d_y, d_g = overlay_depth(d1h)
    c_v, c_y, c_g = overlay_cvd(d5m)
    f_v, f_y, f_g, f_d = overlay_funding(d1h, candles)
    o_v, o_y, o_d = overlay_oi(d1h, candles)
    def mk(y):
        return {"LONG":"[+]","SHORT":"[-]","NOTR":"[ ]","NO_DATA":"[?]"}.get(y,"[?]")
    print(f"  {mk(d_y)} depth     -> {d_y:<6} ({d_g:<6})  {d_v:.2f}")
    print(f"  {mk(c_y)} CVD 5m    -> {c_y:<6} ({c_g:<6})  {c_v:+,.0f}")
    if f_v is not None:
        f_extra = f" ({f_d})" if f_d else ""
        print(f"  {mk(f_y)} funding   -> {f_y:<6} ({f_g:<6})  {f_v:+.1f}% APR{f_extra}")
    else:
        print(f"  {mk(f_y)} funding   -> NO_DATA")
    if o_v is not None:
        print(f"  {mk(o_y)} OI mom.   -> {o_y:<6} ({o_d})  oi={o_v:+.0f}")
    else:
        print(f"  {mk(o_y)} OI mom.   -> NO_DATA")

    overlay_long  = sum(1 for y in [d_y, c_y, f_y, o_y] if y == "LONG")
    overlay_short = sum(1 for y in [d_y, c_y, f_y, o_y] if y == "SHORT")
    print()
    print(f"  Overlay sayim: LONG={overlay_long}  SHORT={overlay_short}")

    # 3) Final
    print()
    print(bar)
    print("  >>> FINAL KARAR")
    print(bar)

    if yon_emp == "LONG":
        if overlay_long >= 2 and overlay_short <= 1:
            print(f"  GIR LONG  (empirik %{guc_pct} + overlay {overlay_long}/4 LONG)")
            print(f"  Kural    : {kural}")
            print(f"  Guven    : YUKSEK")
        elif overlay_short >= 3:
            print(f"  BEKLE  (CELISKI: empirik LONG, overlay {overlay_short}/4 SHORT)")
            print(f"  Empirik  : {kural} (%{guc_pct} historical)")
            print(f"  Live     : agir basiyor SHORT — sample LONG-bias'a guvenme")
        else:
            print(f"  GIR LONG  (empirik %{guc_pct}, overlay karisik)")
            print(f"  Kural    : {kural}")
            print(f"  Guven    : ORTA — POZISYONU KUCULT")
            if overlay_short > overlay_long:
                print(f"  UYARI    : overlay SHORT={overlay_short} > LONG={overlay_long}")
    else:
        if overlay_short >= 3 and overlay_long <= 1:
            print(f"  DIKKATLI SHORT  (empirik YOK, overlay {overlay_short}/4 SHORT)")
            print(f"  UYARI: Notion'da SHORT yapisal zayif (P79: %67 vs %95 LONG)")
            print(f"  Acarsan: KUCUK BOYUT + siki SL (ATR x 1.0)")
        elif overlay_long >= 3 and overlay_short <= 1:
            print(f"  DIKKATLI LONG  (empirik YOK, overlay {overlay_long}/4 LONG)")
            print(f"  Empirik destek yok — KUCUK BOYUT")
        else:
            print(f"  BEKLE")
            print(f"  Sebep: empirik kural yok, overlay yetersiz/celisik")

    print()
    print("  DURUSTLUK:")
    print(f"    - Empirik baseline: %68.6 UP (sample LONG-bias, R2-R42 n=35)")
    print(f"    - SHORT kurali yok: Notion verisinde SHORT iyi sinyal vermiyor")
    print(f"    - Live overlay esikleri kalibre DEGIL — ilk tahmin")
    no_data = [y for y in [d_y, c_y, f_y, o_y] if y == "NO_DATA"]
    if no_data:
        print(f"    - {len(no_data)} live sinyalde veri yok")

    print()
    print(bar)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
