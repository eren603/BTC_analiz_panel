#!/usr/bin/env python3
"""
leading_karar.py  v7.2 final  -  TEK TUS, TUM PIPELINE, LONG-ONLY KARAR
========================================================================

KULLANIM (Pydroid):
  python3 leading_karar.py  ▶️
  -> auto_compact_fixed.py CALISTIRILIR (auto_fetch + run_updater + yon_41 +
     karar_motoru hepsi tetiklenir)
  -> r_update.json olusur/guncellenir
  -> leading_karar kendi mantigiyla LONG karar uretir
  -> 3 cikti: ESKI sistem (karar_motoru), YENI sistem (leading_karar),
     karsilastirma yapabilirsin

ORCHESTRATOR PRIORITY:
  1. auto_compact_fixed.py varsa o calisir (tum pipeline)
  2. Yoksa auto_fetch.py fallback (sadece veri ceker)

V7.2 DEGISIKLIK (May 2 — Eren reconstruction case sonrasi):
  - Tier 3 (DIVERGENCE/MOMENTUM) agirliklari /2:
      CVD divergence:  +/-1.5  -> +/-0.75
      ls_slope:        +/-0.5  -> +/-0.25
                       +/-0.3  -> +/-0.15
      OI momentum:     +/-1.0  -> +/-0.5
                       +/-0.5  -> +/-0.25
  - Sebep: Reconstructed Eren snapshot 23:48 UTC -> +3.00 BEKLE der
    ama gercekte 75 dk sonra +%0.96 PUMP oldu (kacirilan firsat).
  - Tier 1 (live: depth/CVD/funding) GUCLU LONG sinyali Tier 3 (historical
    exhaustion) negatifleriyle bastirildi. Live > historical felsefesi.
  - Bu degisiklik n=35 backtest'i ETKILEMEZ (CSV'de Tier 3 verileri yok).
  - Risk analizi: clear bull (T2 yuksek) durumlarda iki versiyon AYNI karar.
    Sadece T1+ T2 zayif + T3 negatif (squeeze) durumlarda fark olusur.

V7.1 DEGISIKLIK (May 2 — Eren talep):
  - TEK TUS: r_update.json yoksa veya 5 dk'dan eski ise otomatik
    auto_fetch.py calistirir. Kullanici tek dosyaya basar, gerisi otomatik.

V7 DEGISIKLIK (May 2 — Eren karari):
  - SHORT karar TAMAMEN KALDIRILDI. Notion P79: LONG %95, SHORT %67.
    Script artik SHORT acmak icin sinyal vermez.
  - Sadece 2 cikti: GIR LONG / BEKLE
  - Rol: SECONDARY OPINION. Eren karar_motoru/auto_compact'tan
    kararsiz kalirsa BU SCRIPTI LONG icin ikinci goz olarak kullanir.
  - SHORT kararlari icin Eren ESKI sistemi kullanir (karar_motoru + entry_trigger).

V6.1 (onceki):
  - LONG esik +6 -> +4.0 (kanit: backtest %100 dogru, n=8/35)
  - SHORT esik -6 -> -3.0 (artik kullanilmiyor)

V6 (orijinal):
  - Hedge dili kaldirildi. "DIKKATLI/ORTA/KUCUK" yok.
  - SAYISAL puan, 3 tek karar: GIR LONG / BEKLE / GIR SHORT
  - Yeni sinyaller: CVD divergence, ls_slope, oi_momentum
  - Boyut puana gore otomatik

PUAN BILESENLERI (her biri -3..+3):
  Tier 1 LIVE (max ±5):
    - depth_imbalance (orderbook anlik)         : ±2
    - CVD 5m taker akis                         : ±2
    - funding (price-aware)                     : ±1
  Tier 2 STRUCTURE (max ±3):
    - LS_1h zone (Notion empirik kalibre)       : -1..+2.5
    - whale zone (Notion empirik)               : -1..+2
    - depl_4h zone                              : -1..+1
  Tier 3 DIVERGENCE (V7.2: agirlik /2, max ±1):
    - CVD 5m vs 1h zit yon = exhaustion         : ±0.75
    - ls_slope direction                        : ±0.25
    - OI momentum + price                       : ±0.5
  Tier 4 EMPIRIK BONUS:
    - Notion R1-R5 fired                        : +1 ek

KARAR ESIGI (Notion n=35 backtest kalibrasyon):
  toplam >= +4.0  ->  GIR LONG   (backtest: 8/8 dogru, 100%)
  diger          ->  BEKLE      (puan negatif olsa bile SHORT vermez!)

  Negatif puan = "LONG icin guven yok" anlamina gelir, SHORT karari DEGIL.
  SHORT trade dusunuyorsan: karar_motoru + entry_trigger kullan, BU SCRIPT DEGIL.

BOYUT (otomatik):
  risk_pct  = abs(skor) / 10 * 2.0  (max %2 bakiye risk)
  kaldirac  = abs(skor) / 10 * 5.0  (max 5x)

V5'TEN FARK: hedge yok, sayisal eşik, daha fazla sinyal,
CVD divergence ve slope analizleri eklendi.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

# === Auto-fetch ayarlari ===
AUTO_FETCH_ENABLED = True
AUTO_FETCH_MAX_AGE_MIN = 5  # bu dakikadan eski veride otomatik yeniler


# === Esikler (kalibre DEGIL) ===
DEPTH_GUCLU_LONG  = 2.0
DEPTH_LONG        = 1.2
DEPTH_SHORT       = 0.8
DEPTH_GUCLU_SHORT = 0.5
CVD_GUCLU = 500_000
CVD_HAFIF = 100_000
FUND_EXTREME = 5.0
FUND_WEAK    = 1.5
OI_MIN       = 100

KARAR_ESIK_LONG = 4.0   # Notion n=35 backtest %100 (n=8) — kanitli
# V7: SHORT esigi YOK. Script LONG-only ikinci gorus.


def find_r_update():
    """En yeni mtime'li r_update.json'u sec."""
    candidates = [
        Path(__file__).parent / "r_update.json",
        Path.cwd() / "r_update.json",
        Path("/storage/emulated/0/r_update.json"),
        Path("/storage/emulated/0/Download/r_update.json"),
        Path("/storage/emulated/0/Downloads/r_update.json"),
    ]
    existing = [p for p in candidates if p.is_file()]
    if not existing:
        return None
    existing.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return existing[0]


def find_orchestrator():
    """Veri tetikleyici bul. Oncelik: auto_compact_fixed.py
    (icinde auto_fetch + run_updater + karar_motoru tetiklenir).
    Yoksa auto_fetch.py fallback (sadece veri ceker, karar_motoru calistirmaz)."""
    base_dirs = [
        Path(__file__).parent,
        Path.cwd(),
        Path("/storage/emulated/0/Download"),
        Path("/storage/emulated/0/Downloads"),
    ]
    # Oncelik: auto_compact_fixed (tum pipeline)
    for d in base_dirs:
        ac = d / "auto_compact_fixed.py"
        if ac.is_file():
            return ac, "auto_compact_fixed"
    # Fallback: auto_fetch (sadece veri)
    for d in base_dirs:
        af = d / "auto_fetch.py"
        if af.is_file():
            return af, "auto_fetch"
    return None, None


def find_auto_fetch():
    """Geriye donuk uyumluluk icin -- find_orchestrator kullanilir."""
    return find_orchestrator()[0]


def ensure_fresh_data():
    """r_update.json yoksa veya cok eski ise orchestrator'i calistir.
    Orchestrator = auto_compact_fixed.py (tercih) veya auto_fetch.py (fallback).

    Return: (path, age_min) veya (None, None) hata."""
    rj = find_r_update()
    age_min = None
    if rj:
        age_min = (time.time() - rj.stat().st_mtime) / 60
        if age_min <= AUTO_FETCH_MAX_AGE_MIN:
            return rj, age_min  # taze, dokunma

    if not AUTO_FETCH_ENABLED:
        return rj, age_min

    orch, kind = find_orchestrator()
    if not orch:
        if rj:
            print(f"  ! orchestrator bulunamadi (auto_compact_fixed.py / auto_fetch.py)")
        return rj, age_min

    label = "auto_compact_fixed (auto_fetch + run_updater + karar_motoru)" if kind == "auto_compact_fixed" else "auto_fetch"
    print(f"  >>> Veri taze degil ({'eski' if rj else 'yok'}), {label} calistiriliyor...")
    print(f"  >>> {orch}")
    print()
    try:
        result = subprocess.run(
            [sys.executable, str(orch)],
            cwd=str(orch.parent),
            timeout=300,  # auto_compact_fixed daha uzun surebilir
        )
        if result.returncode != 0:
            print(f"  ! {kind} exit code {result.returncode}")
    except subprocess.TimeoutExpired:
        print(f"  ! {kind} timeout (5 dk)")
    except Exception as e:
        print(f"  ! {kind} hatasi: {e}")

    # Tekrar dene
    rj = find_r_update()
    if rj:
        age_min = (time.time() - rj.stat().st_mtime) / 60
    print()
    return rj, age_min


# ============================================================
#  SCORE FONKSIYONLARI — her biri (puan, aciklama) doner
# ============================================================

def score_depth(d1h):
    v = float(d1h.get("depth_imbalance", 1.0))
    if v >= DEPTH_GUCLU_LONG:  return +2.0, f"depth={v:.2f} alici cok GUCLU"
    if v >= DEPTH_LONG:        return +1.0, f"depth={v:.2f} alici hafif"
    if v <= DEPTH_GUCLU_SHORT: return -2.0, f"depth={v:.2f} satici cok GUCLU"
    if v <= DEPTH_SHORT:       return -1.0, f"depth={v:.2f} satici hafif"
    return 0.0, f"depth={v:.2f} dengeli"


def score_cvd_5m(d5m):
    v = float(d5m.get("futures_cvd", 0))
    if v >= CVD_GUCLU:   return +2.0, f"CVD5m={v:+,.0f} alici GUCLU"
    if v >= CVD_HAFIF:   return +1.0, f"CVD5m={v:+,.0f} alici hafif"
    if v <= -CVD_GUCLU:  return -2.0, f"CVD5m={v:+,.0f} satici GUCLU"
    if v <= -CVD_HAFIF:  return -1.0, f"CVD5m={v:+,.0f} satici hafif"
    return 0.0, f"CVD5m={v:+,.0f} zayif"


def score_funding(d1h, candles):
    """Price-aware funding."""
    fr = d1h.get("funding_rate")
    if fr is None:
        return 0.0, "funding yok"
    apr = float(fr) * 3 * 365 * 100
    if abs(apr) < FUND_WEAK:
        return 0.0, f"funding {apr:+.1f}% dengeli"

    c5 = (candles or {}).get("5m", {}).get("curr") or {}
    pu = None
    if c5:
        o = float(c5.get("open", 0)); c = float(c5.get("close", 0))
        if o > 0: pu = c > o
    if pu is None:
        return 0.0, f"funding {apr:+.1f}% (price yon yok)"

    is_ext = abs(apr) >= FUND_EXTREME
    mult = 1.5 if is_ext else 1.0

    if apr < 0:  # SHORT crowded
        if pu:  return +mult, f"funding {apr:+.1f}% + p+ = squeeze rally"
        return -mult, f"funding {apr:+.1f}% + p- = SHORT pro-trend"
    if pu:    return +mult, f"funding {apr:+.1f}% + p+ = LONG momentum"
    return -mult, f"funding {apr:+.1f}% + p- = LONG distribution"


def score_ls_1h(d1h):
    """Notion empirik kalibre."""
    ls = d1h.get("taker_ls_ratio")
    if ls is None: return 0.0, "LS_1h yok"
    ls = float(ls)
    if ls > 1.50: return +2.5, f"LS_1h={ls:.3f} > 1.50 (Notion R1: 86% LONG)"
    if ls > 1.20: return +1.5, f"LS_1h={ls:.3f} > 1.20 (Notion R4: 73% LONG)"
    if ls > 1.00: return +0.5, f"LS_1h={ls:.3f} > 1.00 LONG hafif"
    if ls < 0.85: return -1.0, f"LS_1h={ls:.3f} < 0.85 SHORT bias"
    return 0.0, f"LS_1h={ls:.3f} dengeli"


def score_whale(d1h):
    whale = d1h.get("whale_acct_ls")
    ls    = d1h.get("taker_ls_ratio")
    if whale is None: return 0.0, "whale yok"
    whale = float(whale)
    if whale > 1.05: return +2.0, f"whale={whale:.3f} > 1.05 (Notion R5: 100% n=3)"
    if whale > 1.00 and ls is not None and float(ls) > 1.00:
        return +1.5, f"whale={whale:.3f} + LS>1.0 (Notion R3: 80% LONG)"
    if whale > 1.00: return +0.5, f"whale={whale:.3f} > 1.00 LONG bias"
    if whale < 0.85: return -1.0, f"whale={whale:.3f} < 0.85 SHORT bias"
    return 0.0, f"whale={whale:.3f} dengeli"


def score_depl(d4h):
    p = d4h.get("current_price")
    ma = d4h.get("ma30")
    if not (p and ma and ma > 0):
        return 0.0, None, "depl_4h yok"
    depl = (float(p) - float(ma)) / float(ma) * 100
    if depl > 3.0:  return -1.0, depl, f"depl={depl:+.2f}% asiri yukari (mean rev SHORT)"
    if depl > 0:    return +1.0, depl, f"depl={depl:+.2f}% MA30 ustu LONG yapi"
    if depl < -1.0: return +0.5, depl, f"depl={depl:+.2f}% dip toplama bolge"
    return 0.0, depl, f"depl={depl:+.2f}%"


def score_divergence(d5m, d1h):
    """CVD 5m vs 1h zit yön = exhaustion. V7.2: agirlik /2 (1.5 -> 0.75)."""
    c5 = float(d5m.get("futures_cvd", 0))
    c1 = float(d1h.get("futures_cvd", 0))
    if abs(c5) < CVD_HAFIF or abs(c1) < CVD_HAFIF:
        return 0.0, None
    if c5 > 0 and c1 < 0:
        return -0.75, f"CVD div: 5m+ vs 1h- = rally exhaustion (SHORT sinyali)"
    if c5 < 0 and c1 > 0:
        return +0.75, f"CVD div: 5m- vs 1h+ = dip exhaustion (LONG sinyali)"
    return 0.0, None


def score_ls_slope(d1h):
    """V7.2: agirlik /2 (0.5/0.3 -> 0.25/0.15)."""
    s = d1h.get("ls_slope")
    if s is None: return 0.0, None
    s = float(s)
    if s > 0.05:  return +0.25, f"ls_slope={s:+.4f} hizli artiyor (LONG mom)"
    if s > 0.01:  return +0.15, f"ls_slope={s:+.4f} artiyor"
    if s < -0.05: return -0.25, f"ls_slope={s:+.4f} hizli azaliyor (SHORT mom)"
    if s < -0.01: return -0.15, f"ls_slope={s:+.4f} azaliyor"
    return 0.0, None


def score_oi_momentum(d1h, candles):
    """V7.2: agirlik /2 (1.0/0.5 -> 0.5/0.25)."""
    delta = d1h.get("oi_delta")
    if delta is None: return 0.0, None
    delta = float(delta)
    if abs(delta) < OI_MIN: return 0.0, None
    c5 = (candles or {}).get("5m", {}).get("curr") or {}
    if not c5: return 0.0, None
    o = float(c5.get("open", 0)); c = float(c5.get("close", 0))
    if o == 0: return 0.0, None
    pu = c > o
    fr = d1h.get("funding_rate")
    apr = (float(fr) * 3 * 365 * 100) if fr is not None else 0.0
    sc = apr < -FUND_WEAK   # short crowded
    lc = apr > FUND_WEAK    # long crowded

    if pu and delta > 0:    return +0.5, f"OI+ p+ yeni LONG akisi"
    if (not pu) and delta < 0: return +0.5, f"OI- p- SHORT zayifliyor"
    if pu and delta < 0:
        if sc: return +0.25, f"OI- p+ + SHORT crowded = squeeze devam"
        return -0.25, f"OI- p+ short cover fade (SHORT)"
    if (not pu) and delta > 0:
        if lc: return -0.25, f"OI+ p- + LONG crowded = stop hunt"
        return -0.25, f"OI+ p- yeni SHORT"
    return 0.0, None


def empirik_bonus(whale, ls, depl):
    """Notion n=35 R1-R5 kurallari TETIKLENDIYSE bonus."""
    if ls is not None and ls > 1.50:
        return +1.0, "R1 fired: LS>1.50 (86%)"
    if ls is not None and depl is not None and depl < -1.0 and ls > 1.0:
        return +1.0, "R2 fired: depl<-1.0 + LS>1.0 (83%)"
    if whale is not None and ls is not None and whale > 1.0 and ls > 1.0:
        return +1.0, "R3 fired: whale>1.0 + LS>1.0 (80%)"
    if ls is not None and ls > 1.20:
        return +1.0, "R4 fired: LS>1.20 (73%)"
    if whale is not None and whale > 1.05:
        return +1.0, "R5 fired: whale>1.05 (100%, n=3)"
    return 0.0, None


# ============================================================
#  ANA AKIS
# ============================================================

def main():
    print()
    print("=" * 76)
    print("  LEADING KARAR v7.2  -  hazirlanyor...")
    print("=" * 76)

    rj, age_min = ensure_fresh_data()
    if not rj:
        print("HATA: r_update.json yok ve auto_fetch.py calistirilamadi.")
        print("Manuel: python3 auto_fetch.py")
        return 1

    age_tag = (f"{age_min:.1f} dk -- TAZE" if age_min < 5
               else f"{age_min:.0f} dk -- eski" if age_min < 30
               else f"{age_min:.0f} dk -- COK ESKI")

    with open(rj, encoding="utf-8") as f:
        data = json.load(f)

    d5m = data.get("data_5m") or {}
    d1h = data.get("data_1h") or {}
    d4h = data.get("data_4h") or {}
    candles = data.get("candles") or {}

    price = d1h.get("current_price") or d5m.get("current_price", 0)
    whale = d1h.get("whale_acct_ls")
    ls    = d1h.get("taker_ls_ratio")

    bar = "=" * 76
    print()
    print(bar)
    print(f"  LEADING KARAR v7.2  -  ${price:,.0f}")
    print(f"  LONG-ONLY 2. GORUS  |  Esik: LONG +{KARAR_ESIK_LONG} (Notion n=35 backtest)")
    print(f"  SHORT icin: bu script kullanma -> karar_motoru + entry_trigger")
    print(bar)
    print(f"  Kaynak : {rj}")
    print(f"  Mtime  : {age_tag}")
    if age_min > 30:
        print(f"  ⚠ UYARI: r_update.json {age_min:.0f} dk eski. auto_fetch CALISTIR.")
    print(bar)
    print()

    # === Tier 1: LIVE ===
    tier1 = [
        score_depth(d1h),
        score_cvd_5m(d5m),
        score_funding(d1h, candles),
    ]
    # === Tier 2: STRUCTURE ===
    s_depl, depl_val, t_depl = score_depl(d4h)
    tier2 = [
        score_ls_1h(d1h),
        score_whale(d1h),
        (s_depl, t_depl),
    ]
    # === Tier 3: DIVERGENCE / MOMENTUM ===
    tier3 = []
    s, t = score_divergence(d5m, d1h)
    if t: tier3.append((s, t))
    s, t = score_ls_slope(d1h)
    if t: tier3.append((s, t))
    s, t = score_oi_momentum(d1h, candles)
    if t: tier3.append((s, t))
    # === Tier 4: EMPIRIK BONUS ===
    s_emp, t_emp = empirik_bonus(
        float(whale) if whale is not None else None,
        float(ls) if ls is not None else None,
        depl_val,
    )

    print("  TIER 1 — LIVE (orderbook + tape + funding)")
    print("  " + "-" * 72)
    t1_total = 0.0
    for s, t in tier1:
        print(f"  {s:>+5.2f}  {t}")
        t1_total += s
    print(f"  Tier 1 toplam: {t1_total:+.2f}")

    print()
    print("  TIER 2 — STRUCTURE (LS, whale, depl)")
    print("  " + "-" * 72)
    t2_total = 0.0
    for s, t in tier2:
        print(f"  {s:>+5.2f}  {t}")
        t2_total += s
    print(f"  Tier 2 toplam: {t2_total:+.2f}")

    print()
    if tier3:
        print("  TIER 3 — DIVERGENCE / MOMENTUM")
        print("  " + "-" * 72)
        t3_total = 0.0
        for s, t in tier3:
            print(f"  {s:>+5.2f}  {t}")
            t3_total += s
        print(f"  Tier 3 toplam: {t3_total:+.2f}")
    else:
        t3_total = 0.0
        print("  TIER 3 — DIVERGENCE / MOMENTUM (sinyal yok)")
        print("  " + "-" * 72)

    print()
    if t_emp:
        print("  TIER 4 — EMPIRIK BONUS (Notion n=35)")
        print("  " + "-" * 72)
        print(f"  {s_emp:>+5.2f}  {t_emp}")
    t4_total = s_emp

    grand = t1_total + t2_total + t3_total + t4_total

    print()
    print(bar)
    print(f"  TOPLAM PUAN: {grand:+.2f}  /  10  (GIR LONG esik: +{KARAR_ESIK_LONG})")
    print(bar)
    print()

    # === KARAR (V7: LONG-only) ===
    if grand >= KARAR_ESIK_LONG:
        karar = "GIR LONG"
        yon = "LONG"
    else:
        karar = "BEKLE"
        yon = None

    print(f"  >>> KARAR: {karar}")

    if yon:
        # Boyut: esikten 2x guclu olabilir, max %2 risk, max 5x kaldirac
        ratio = min(grand / KARAR_ESIK_LONG, 2.0)
        risk_pct = min(0.5 + ratio * 0.75, 2.0)
        lev = min(2.0 + ratio * 1.5, 5.0)
        print(f"  Risk    : %{risk_pct:.2f} bakiye")
        print(f"  Kaldirac: max {lev:.1f}x")
        print(f"  SL hint : ATR x 1.0  (auto_fetch ATR verisi)")
        print(f"  TP hint : ATR x 2.0  (R:R = 2.0)")
    else:
        if grand >= 0:
            gap = KARAR_ESIK_LONG - grand
            print(f"  LONG icin puan {grand:+.2f} -- esik +{KARAR_ESIK_LONG}'a {gap:.2f} uzak")
            print(f"  POZISYON ACMA. (LONG icin yetersiz kanit)")
        else:
            print(f"  LONG icin guven yok (puan {grand:+.2f}) -- sinyaller LONG'a karsi")
            print(f"  POZISYON ACMA. (Bu script SHORT karari VERMEZ -- karar_motoru kullan)")

    print()
    print(bar)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
