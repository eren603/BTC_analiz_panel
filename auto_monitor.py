#!/usr/bin/env python3
"""
AUTO MONITOR — Sürekli izleme + erken uyarı sistemi.
Pydroid3'te Play. 15 dakikada bir auto_fetch çalıştırır, sinyal değişikliğinde alarm verir.

P61 DEĞİŞİKLİKLER:
  - print_monitor_report: KOMPAKT ÇIKTI. Tüm hesaplamalar aynı, sadece sonuç gösterilir.
    Eski: ~40 satır detaylı rapor. Yeni: 1-4 satır özet.
    Satır 1: Ana sonuç (zaman, fiyat, leading karar, whale/LS/OI/P-MA30)
    Satır 2: Trend özeti (sadece mevcut ise)
    Satır 3+: Sadece acil uyarılar (YAKIN approach, ⚡ ETA, sinyal değişimi, deplasman)
    Sessiz durumda (GİRME + eşik uzak): sadece 1-2 satır.

P60 DEĞİŞİKLİKLER:
  - evaluate_leading: LONG_ANA ERKEN + 4h%MA30>3.0% → GİRME (LONG_ANA_DEPLASMAN)
  - Monitor raporda 4h%MA30 gösterimi eklendi

P59 YENİ — PLAN A + PLAN B:
  PLAN A (Eşik Yaklaşım Tespiti):
    Leading kurallarının eşik değerlerine ne kadar yakın olduğunu hesaplar.
    Kural tetiklenmeden ÖNCE "hazırlan" erken uyarısı verir.
    Approach zone'lar backtest verisinden (19 run) türetilmiştir.

  PLAN B (Rate of Change + ETA):
    Whale ve OI zaman serilerinin (30 entry, 1h) eğimini hesaplar.
    Eşik değerine yaklaşım HIZI ve tahmini varış süresi (ETA) gösterir.
    LS trend: 5 entry (kısa vadeli) — sınırlı ama kullanılabilir.

  METRİKLER (backtest kaynaklı):
    Whale tipik hız: 0.001-0.005 /saat (slope)
    Whale tipik 6h delta: 0.008-0.048
    Whale 0.87'ye 0.03 uzaklık → 6-30 saat ETA
    LS tipik range: 0.53-2.15
    OI_30h tipik range: -6220 to +2901

  LEADING KURALLARI (P55, öncelik sırasıyla):
    1. SHORT_TRAP:       whale<0.95 + OI_30h>0 → GİR SHORT
    2. LONG_ANA:         whale>0.87 + LS_1h>0.85 → GİR LONG
    3. LONG_LS_OVERRIDE: LS_1h>1.50 → GİR_DİKKAT LONG
    4. SHORT_ZAYIF:      whale<0.90 + LS_1h<0.85 → GİR_DİKKAT SHORT

  APPROACH ZONE TASARIMI:
    Her Leading kuralı için iki bölge:
      YAKIN:       Eşiğe <X uzaklık — kural tetiklenmeye çok yakın
      YAKLAŞIYOR:  Eşiğe <Y uzaklık — trend doğru yönde ise dikkat

    LONG_ANA:
      whale YAKIN:       [0.84, 0.87)  → eşiğe 0-0.03 uzak
      whale YAKLAŞIYOR:  [0.82, 0.84)  → eşiğe 0.03-0.05 uzak
      LS YAKIN:          [0.80, 0.85)  → eşiğe 0-0.05 uzak
      LS YAKLAŞIYOR:     [0.75, 0.80)  → eşiğe 0.05-0.10 uzak

    SHORT_TRAP:
      OI YAKIN:          [-300, 0)     → pozitife çok yakın
      OI YAKLAŞIYOR:     [-800, -300)  → trend pozitife dönüyor

    LONG_LS_OVERRIDE:
      LS YAKIN:          [1.40, 1.50)  → eşiğe 0-0.10 uzak
      LS YAKLAŞIYOR:     [1.30, 1.40)  → eşiğe 0.10-0.20 uzak

    SHORT_ZAYIF:
      whale YAKIN:       (0.90, 0.93]  → 0.90'a 0-0.03 uzak (yukarıdan)
      LS YAKIN:          (0.85, 0.90]  → 0.85'e 0-0.05 uzak (yukarıdan)

  RATE OF CHANGE:
    whale_slope_6h:  Son 6 entry lineer regresyon eğimi
    whale_slope_12h: Son 12 entry lineer regresyon eğimi
    oi_slope_6h:     Son 6 entry OI eğimi
    ls_slope_5:      Son 5 entry LS eğimi (sınırlı veri)
    ETA:             distance_to_threshold / abs(slope) (saat)
                     Sadece slope doğru yönde ise hesaplanır.
                     ETA > 48h → gösterilmez (anlamsız).

SINIRLAMALAR:
  - LS zaman serisi: sadece 5 entry (fetch_taker_ls limit=5).
    ETA tahmini güvenilmez — sadece yön bilgisi olarak kullan.
  - Whale ve OI: 30 entry (30 saat). Yeterli ama gün-üstü trend yakalanamaz.
  - ETA lineer projeksiyon. Gerçek hareket non-linear olabilir.
  - Pydroid arka plan kısıtlaması: Android kill edebilir.

KULLANIM:
  python3 auto_monitor.py              → 15dk döngü
  python3 auto_monitor.py --once       → tek sefer çalıştır
  python3 auto_monitor.py --interval 5 → 5dk döngü
"""

import json
import os
import sys
import time
import subprocess
import glob
from datetime import datetime, timezone


# ═══════════════════════════════════════════════════════════
# YAPILANDIRMA
# ═══════════════════════════════════════════════════════════

DEFAULT_INTERVAL_MIN = 15

# Leading kural eşikleri (P55 + P60)
THRESHOLDS = {
    "LONG_ANA_WHALE":    0.87,
    "LONG_ANA_LS":       0.85,
    "LONG_ANA_DEPLASMAN": 3.0,  # P60: 4h%MA30 > 3.0% → GİRME
    "SHORT_TRAP_WHALE":  0.95,  # whale < 0.95
    "SHORT_TRAP_OI":     0,     # OI_30h > 0
    "LS_OVERRIDE":       1.50,
    "SHORT_ZAYIF_WHALE": 0.90,  # whale < 0.90
    "SHORT_ZAYIF_LS":    0.85,  # LS < 0.85
}

# Approach zone marjları (backtest-derived)
APPROACH = {
    # LONG_ANA whale: yukarıdan yaklaşma
    "LONG_ANA_WHALE_YAKIN":       (0.84, 0.87),   # 0-0.03 uzak
    "LONG_ANA_WHALE_YAKLASIYOR":  (0.82, 0.84),   # 0.03-0.05 uzak
    # LONG_ANA LS: yukarıdan yaklaşma
    "LONG_ANA_LS_YAKIN":          (0.80, 0.85),   # 0-0.05 uzak
    "LONG_ANA_LS_YAKLASIYOR":     (0.75, 0.80),   # 0.05-0.10 uzak
    # P60: LONG_ANA DEPLASMAN: 4h%MA30 yukarı yaklaşma (3.0%'a doğru)
    "DEPLASMAN_YAKIN":            (2.5, 3.0),      # 0-0.5% uzak → bloklanmaya çok yakın
    "DEPLASMAN_YAKLASIYOR":       (2.0, 2.5),      # 0.5-1.0% uzak
    # SHORT_TRAP OI: negatiften pozitife yaklaşma
    "SHORT_TRAP_OI_YAKIN":        (-300, 0),       # çok yakın
    "SHORT_TRAP_OI_YAKLASIYOR":   (-800, -300),    # yaklaşıyor
    # LONG_LS_OVERRIDE LS: yukarıdan yaklaşma
    "LS_OVERRIDE_YAKIN":          (1.40, 1.50),    # 0-0.10 uzak
    "LS_OVERRIDE_YAKLASIYOR":     (1.30, 1.40),    # 0.10-0.20 uzak
    # SHORT_ZAYIF whale: aşağıdan yaklaşma (0.90'ın altına düşüyor)
    "SHORT_ZAYIF_WHALE_YAKIN":    (0.90, 0.93),    # 0-0.03 uzak
    # SHORT_ZAYIF LS: aşağıdan yaklaşma (0.85'in altına düşüyor)
    "SHORT_ZAYIF_LS_YAKIN":       (0.85, 0.90),    # 0-0.05 uzak
}

# ETA parametreleri
ETA_MAX_HOURS = 48     # Bundan uzun ETA gösterilmez
ETA_MIN_SLOPE = 0.0002 # Bundan küçük slope → "durağan"


# ═══════════════════════════════════════════════════════════
# YARDIMCI FONKSİYONLAR
# ═══════════════════════════════════════════════════════════

def calc_slope(series):
    """Lineer regresyon eğimi. series = [eski, ..., yeni]"""
    n = len(series)
    if n < 2:
        return 0.0
    x_mean = (n - 1) / 2.0
    y_mean = sum(series) / n
    num = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(series))
    den = sum((i - x_mean) ** 2 for i in range(n))
    return num / den if den != 0 else 0.0


def calc_eta(current, threshold, slope, direction="up"):
    """
    Eşiğe tahmini varış süresi (saat).
    direction="up": current'ın threshold'a ALT'tan yaklaşması (whale→0.87)
    direction="down": current'ın threshold'a ÜST'ten yaklaşması (whale→0.90↓)
    Returns: float saat veya None (yanlış yön / durağan / çok uzak)
    """
    if direction == "up":
        distance = threshold - current
        if distance <= 0:
            return 0.0  # zaten eşiğin üstünde
        if slope <= ETA_MIN_SLOPE:
            return None  # durağan veya ters yönde
        eta = distance / slope
    else:  # down
        distance = current - threshold
        if distance <= 0:
            return 0.0  # zaten eşiğin altında
        if slope >= -ETA_MIN_SLOPE:
            return None  # durağan veya ters yönde
        eta = distance / abs(slope)

    if eta > ETA_MAX_HOURS:
        return None  # çok uzak
    return round(eta, 1)


def find_script_dir():
    """yon_*.py dosyasını bularak çalışma klasörünü otomatik tespit et."""
    search_paths = [
        os.path.dirname(os.path.abspath(__file__)),
        os.getcwd(),
        "/storage/emulated/0/Download",
        "/storage/emulated/0/Downloads",
        "/storage/emulated/0/Documents",
        os.path.expanduser("~"),
    ]
    # Önce yon_*.py ara (auto_fetch ile aynı mantık)
    for p in search_paths:
        if not os.path.isdir(p):
            continue
        if glob.glob(os.path.join(p, "yon_*.py")):
            return p
    # Alt klasörlerde de ara
    for p in search_paths:
        if not os.path.isdir(p):
            continue
        try:
            for sub in os.listdir(p):
                sp = os.path.join(p, sub)
                if os.path.isdir(sp) and glob.glob(os.path.join(sp, "yon_*.py")):
                    return sp
        except:
            continue
    return None


# ═══════════════════════════════════════════════════════════
# LEADING KARAR (P55 kuralları)
# ═══════════════════════════════════════════════════════════

def evaluate_leading(whale, oi_30h, ls_1h, pct_ma30_4h=None):
    """Leading kural değerlendirmesi. Returns dict."""
    if whale is None or ls_1h is None:
        return {"karar": "VERİ_YOK", "yon": "—", "kural": "VERİ_YETERSİZ"}

    # Öncelik sırası
    if whale < 0.95 and oi_30h is not None and oi_30h > 0:
        return {"karar": "GİR", "yon": "SHORT", "kural": "SHORT_TRAP"}
    if whale > 0.87 and ls_1h > 0.85:
        if ls_1h < 1.20:
            # P60: Fiyat deplasmanı filtresi
            if pct_ma30_4h is not None and pct_ma30_4h > 3.0:
                return {"karar": "GİRME", "yon": "—", "kural": "LONG_ANA_DEPLASMAN"}
            return {"karar": "GİR", "yon": "LONG", "kural": "LONG_ANA"}
        else:
            return {"karar": "GİR_DİKKAT", "yon": "LONG", "kural": "LONG_ANA_GEÇ"}
    if ls_1h > 1.50:
        return {"karar": "GİR_DİKKAT", "yon": "LONG", "kural": "LONG_LS_OVERRIDE"}
    if whale < 0.90 and ls_1h < 0.85:
        return {"karar": "GİR_DİKKAT", "yon": "SHORT", "kural": "SHORT_ZAYIF"}
    return {"karar": "GİRME", "yon": "—", "kural": "—"}


# ═══════════════════════════════════════════════════════════
# PLAN A — EŞİK YAKLAŞIM TESPİTİ
# ═══════════════════════════════════════════════════════════

def evaluate_approach(whale, oi_30h, ls_1h, pct_ma30_4h=None):
    """
    Her Leading kuralına yakınlık analizi.
    Returns: list of approach alerts (her biri dict).
    """
    alerts = []

    if whale is None or ls_1h is None:
        return alerts

    # ─── LONG_ANA yaklaşım (whale→0.87↑, LS→0.85↑) ───
    # Whale kontrolü
    wh_dist = 0.87 - whale  # pozitif = eşiğin altında
    if APPROACH["LONG_ANA_WHALE_YAKIN"][0] <= whale < APPROACH["LONG_ANA_WHALE_YAKIN"][1]:
        alerts.append({
            "kural": "LONG_ANA", "param": "whale",
            "seviye": "YAKIN", "deger": whale,
            "esik": 0.87, "uzaklik": wh_dist,
            "mesaj": f"whale={whale:.4f} → LONG_ANA eşiği 0.87'ye {wh_dist:.4f} UZAK"
        })
    elif APPROACH["LONG_ANA_WHALE_YAKLASIYOR"][0] <= whale < APPROACH["LONG_ANA_WHALE_YAKLASIYOR"][1]:
        alerts.append({
            "kural": "LONG_ANA", "param": "whale",
            "seviye": "YAKLAŞIYOR", "deger": whale,
            "esik": 0.87, "uzaklik": wh_dist,
            "mesaj": f"whale={whale:.4f} → LONG_ANA eşiği 0.87'ye {wh_dist:.4f} uzak"
        })

    # LS kontrolü
    ls_dist = 0.85 - ls_1h
    if APPROACH["LONG_ANA_LS_YAKIN"][0] <= ls_1h < APPROACH["LONG_ANA_LS_YAKIN"][1]:
        alerts.append({
            "kural": "LONG_ANA", "param": "LS",
            "seviye": "YAKIN", "deger": ls_1h,
            "esik": 0.85, "uzaklik": ls_dist,
            "mesaj": f"LS={ls_1h:.4f} → LONG_ANA eşiği 0.85'e {ls_dist:.4f} UZAK"
        })
    elif APPROACH["LONG_ANA_LS_YAKLASIYOR"][0] <= ls_1h < APPROACH["LONG_ANA_LS_YAKLASIYOR"][1]:
        alerts.append({
            "kural": "LONG_ANA", "param": "LS",
            "seviye": "YAKLAŞIYOR", "deger": ls_1h,
            "esik": 0.85, "uzaklik": ls_dist,
            "mesaj": f"LS={ls_1h:.4f} → LONG_ANA eşiği 0.85'e {ls_dist:.4f} uzak"
        })

    # ─── SHORT_TRAP yaklaşım (OI→0↑) ───
    if oi_30h is not None and whale < 0.95:
        if APPROACH["SHORT_TRAP_OI_YAKIN"][0] <= oi_30h < APPROACH["SHORT_TRAP_OI_YAKIN"][1]:
            alerts.append({
                "kural": "SHORT_TRAP", "param": "OI_30h",
                "seviye": "YAKIN", "deger": oi_30h,
                "esik": 0, "uzaklik": -oi_30h,
                "mesaj": f"OI_30h={oi_30h:+.0f} → SHORT_TRAP pozitife {-oi_30h:.0f} UZAK"
            })
        elif APPROACH["SHORT_TRAP_OI_YAKLASIYOR"][0] <= oi_30h < APPROACH["SHORT_TRAP_OI_YAKLASIYOR"][1]:
            alerts.append({
                "kural": "SHORT_TRAP", "param": "OI_30h",
                "seviye": "YAKLAŞIYOR", "deger": oi_30h,
                "esik": 0, "uzaklik": -oi_30h,
                "mesaj": f"OI_30h={oi_30h:+.0f} → SHORT_TRAP pozitife {-oi_30h:.0f} uzak"
            })

    # ─── LONG_LS_OVERRIDE yaklaşım (LS→1.50↑) ───
    if APPROACH["LS_OVERRIDE_YAKIN"][0] <= ls_1h < APPROACH["LS_OVERRIDE_YAKIN"][1]:
        alerts.append({
            "kural": "LONG_LS_OVERRIDE", "param": "LS",
            "seviye": "YAKIN", "deger": ls_1h,
            "esik": 1.50, "uzaklik": 1.50 - ls_1h,
            "mesaj": f"LS={ls_1h:.4f} → LS_OVERRIDE eşiği 1.50'ye {1.50-ls_1h:.4f} UZAK"
        })
    elif APPROACH["LS_OVERRIDE_YAKLASIYOR"][0] <= ls_1h < APPROACH["LS_OVERRIDE_YAKLASIYOR"][1]:
        alerts.append({
            "kural": "LONG_LS_OVERRIDE", "param": "LS",
            "seviye": "YAKLAŞIYOR", "deger": ls_1h,
            "esik": 1.50, "uzaklik": 1.50 - ls_1h,
            "mesaj": f"LS={ls_1h:.4f} → LS_OVERRIDE eşiği 1.50'ye {1.50-ls_1h:.4f} uzak"
        })

    # ─── SHORT_ZAYIF yaklaşım (whale→0.90↓, LS→0.85↓) ───
    if APPROACH["SHORT_ZAYIF_WHALE_YAKIN"][0] < whale <= APPROACH["SHORT_ZAYIF_WHALE_YAKIN"][1]:
        alerts.append({
            "kural": "SHORT_ZAYIF", "param": "whale",
            "seviye": "YAKIN", "deger": whale,
            "esik": 0.90, "uzaklik": whale - 0.90,
            "mesaj": f"whale={whale:.4f} → SHORT_ZAYIF eşiği 0.90'a {whale-0.90:.4f} UZAK"
        })
    if APPROACH["SHORT_ZAYIF_LS_YAKIN"][0] < ls_1h <= APPROACH["SHORT_ZAYIF_LS_YAKIN"][1]:
        alerts.append({
            "kural": "SHORT_ZAYIF", "param": "LS",
            "seviye": "YAKIN", "deger": ls_1h,
            "esik": 0.85, "uzaklik": ls_1h - 0.85,
            "mesaj": f"LS={ls_1h:.4f} → SHORT_ZAYIF eşiği 0.85'e {ls_1h-0.85:.4f} UZAK"
        })

    # ─── P60: LONG_ANA DEPLASMAN yaklaşım (4h%MA30→3.0%↑) ───
    # LONG_ANA koşulları sağlanıyorken 4h%MA30 bloklama eşiğine yaklaşıyorsa uyar
    if pct_ma30_4h is not None and whale > 0.87 and ls_1h > 0.85 and ls_1h < 1.20:
        if APPROACH["DEPLASMAN_YAKIN"][0] <= pct_ma30_4h < APPROACH["DEPLASMAN_YAKIN"][1]:
            alerts.append({
                "kural": "LONG_ANA_DEPLASMAN", "param": "4h%MA30",
                "seviye": "YAKIN", "deger": pct_ma30_4h,
                "esik": 3.0, "uzaklik": 3.0 - pct_ma30_4h,
                "mesaj": f"4h%MA30={pct_ma30_4h:+.2f}% → DEPLASMAN bloğuna {3.0-pct_ma30_4h:.2f}% UZAK"
            })
        elif APPROACH["DEPLASMAN_YAKLASIYOR"][0] <= pct_ma30_4h < APPROACH["DEPLASMAN_YAKLASIYOR"][1]:
            alerts.append({
                "kural": "LONG_ANA_DEPLASMAN", "param": "4h%MA30",
                "seviye": "YAKLAŞIYOR", "deger": pct_ma30_4h,
                "esik": 3.0, "uzaklik": 3.0 - pct_ma30_4h,
                "mesaj": f"4h%MA30={pct_ma30_4h:+.2f}% → DEPLASMAN bloğuna {3.0-pct_ma30_4h:.2f}% uzak"
            })

    return alerts


# ═══════════════════════════════════════════════════════════
# PLAN B — RATE OF CHANGE + ETA
# ═══════════════════════════════════════════════════════════

def evaluate_rate_of_change(whale, ls_1h, whale_ts, oi_ts, ls_series):
    """
    Zaman serisi eğim analizi + eşiğe tahmini varış süresi.

    Args:
        whale: float — anlık whale_acct_ls
        ls_1h: float — anlık taker LS ratio (1h)
        whale_ts: list — api_whale_account [[ts, value], ...] (30 entry)
        oi_ts: list — api_open_interest [[ts, value], ...] (30 entry)
        ls_series: list — taker LS son 5 değer (fetch_taker_ls)

    Returns: dict with slopes, ETAs, trend descriptions.
    """
    result = {
        "whale_slope_6h": None,
        "whale_slope_12h": None,
        "whale_slope_30h": None,
        "whale_trend": "VERİ_YOK",
        "whale_eta_long_ana": None,      # 0.87'ye ETA (saat)
        "whale_eta_short_zayif": None,   # 0.90'a ETA (aşağı, saat)
        "oi_slope_6h": None,
        "oi_slope_12h": None,
        "oi_30h": None,
        "oi_trend": "VERİ_YOK",
        "oi_eta_zero": None,             # OI_30h=0'a ETA (saat)
        "ls_slope": None,
        "ls_trend": "VERİ_YOK",
        "ls_eta_085": None,              # 0.85'e ETA
        "ls_eta_150": None,              # 1.50'ye ETA
        "signals": [],                   # erken uyarı mesajları
    }

    # ─── WHALE TREND ───
    if whale_ts and len(whale_ts) >= 7:  # P59 FIX: 7 entry = 6 interval = gerçek 6h
        wh_vals = [x[1] for x in whale_ts]

        s6 = calc_slope(wh_vals[-7:])  # P59 FIX: 7 entry = 6h
        result["whale_slope_6h"] = round(s6, 6)

        if len(wh_vals) >= 13:  # P59 FIX: 13 entry = 12h
            s12 = calc_slope(wh_vals[-13:])
            result["whale_slope_12h"] = round(s12, 6)

        s30 = calc_slope(wh_vals)
        result["whale_slope_30h"] = round(s30, 6)

        # Trend etiketi (6h baz)
        if s6 > 0.001:
            result["whale_trend"] = "YUKARI"
        elif s6 < -0.001:
            result["whale_trend"] = "ASAGI"
        elif abs(s6) <= 0.001:
            result["whale_trend"] = "YATAY"

        # ETA: whale → 0.87 (LONG_ANA) — sadece whale < 0.87 ise
        if whale is not None and whale < 0.87:
            eta = calc_eta(whale, 0.87, s6, direction="up")
            result["whale_eta_long_ana"] = eta
            if eta is not None and eta <= 12:
                result["signals"].append(
                    f"⚡ WHALE→0.87: {eta:.1f}h ETA (slope={s6:+.4f}/h, şu an={whale:.4f})"
                )
            elif eta is not None:
                result["signals"].append(
                    f"📈 WHALE→0.87: ~{eta:.0f}h ETA (slope={s6:+.4f}/h)"
                )

        # ETA: whale → 0.90↓ (SHORT_ZAYIF) — sadece whale > 0.90 ise
        if whale is not None and whale > 0.90:
            eta = calc_eta(whale, 0.90, s6, direction="down")
            result["whale_eta_short_zayif"] = eta
            if eta is not None and eta <= 12:
                result["signals"].append(
                    f"⚡ WHALE→0.90↓: {eta:.1f}h ETA (slope={s6:+.4f}/h, şu an={whale:.4f})"
                )

    # ─── OI TREND ───
    if oi_ts and len(oi_ts) >= 7:  # P59 FIX: 7 entry = 6h
        oi_vals = [x[1] for x in oi_ts]

        s6 = calc_slope(oi_vals[-7:])  # P59 FIX: 7 entry = 6h
        result["oi_slope_6h"] = round(s6, 1)

        if len(oi_vals) >= 13:  # P59 FIX: 13 entry = 12h
            s12 = calc_slope(oi_vals[-13:])
            result["oi_slope_12h"] = round(s12, 1)

        oi_30h = oi_vals[-1] - oi_vals[0]
        result["oi_30h"] = round(oi_30h, 1)

        # Trend etiketi
        if s6 > 50:
            result["oi_trend"] = "ARTIYOR"
        elif s6 < -50:
            result["oi_trend"] = "AZALIYOR"
        else:
            result["oi_trend"] = "YATAY"

        # ETA: OI_30h → 0 (SHORT_TRAP tetikleme) — sadece OI negatif ise
        if oi_30h < 0 and s6 > 10:
            # OI 30h delta her saat ne kadar değişiyor?
            # Basitleştirme: son 6 saatteki OI artış hızıyla
            # OI_30h'ın pozitife dönme süresi
            hours_to_zero = abs(oi_30h) / s6 if s6 > 0 else None
            if hours_to_zero and hours_to_zero <= ETA_MAX_HOURS:
                result["oi_eta_zero"] = round(hours_to_zero, 1)
                if hours_to_zero <= 8:
                    result["signals"].append(
                        f"⚡ OI→0: {hours_to_zero:.1f}h ETA (OI_30h={oi_30h:+.0f}, slope_6h={s6:+.0f}/h)"
                    )
                else:
                    result["signals"].append(
                        f"📊 OI→0: ~{hours_to_zero:.0f}h ETA (OI_30h={oi_30h:+.0f})"
                    )

    # ─── LS TREND ───
    if ls_series and len(ls_series) >= 3:
        sl = calc_slope(ls_series)
        result["ls_slope"] = round(sl, 6)

        if sl > 0.01:
            result["ls_trend"] = "YUKARI"
        elif sl < -0.01:
            result["ls_trend"] = "ASAGI"
        else:
            result["ls_trend"] = "YATAY"

        # ETA: LS → 0.85 (LONG_ANA) — sadece LS < 0.85 ise
        if ls_1h is not None and ls_1h < 0.85:
            eta = calc_eta(ls_1h, 0.85, sl, direction="up")
            result["ls_eta_085"] = eta
            if eta is not None and eta <= 12:
                result["signals"].append(
                    f"⚡ LS→0.85: {eta:.1f}h ETA (slope={sl:+.4f}, şu an={ls_1h:.4f})"
                )

        # ETA: LS → 1.50 (LS_OVERRIDE) — sadece LS < 1.50 ve yükseliyorsa
        if ls_1h is not None and 1.20 < ls_1h < 1.50:
            eta = calc_eta(ls_1h, 1.50, sl, direction="up")
            result["ls_eta_150"] = eta
            if eta is not None and eta <= 12:
                result["signals"].append(
                    f"📈 LS→1.50: {eta:.1f}h ETA (slope={sl:+.4f}, şu an={ls_1h:.4f})"
                )

    return result


# ═══════════════════════════════════════════════════════════
# ANA ÇIKTI
# ═══════════════════════════════════════════════════════════

def print_monitor_report(data, prev_leading=None):
    """
    Monitoring raporu yazdır.
    data: r_update.json parse edilmiş dict.
    prev_leading: önceki döngüdeki leading karar dict (değişim tespiti için).
    Returns: current leading dict.
    """
    # Veri çıkar
    d1h = data.get("data_1h", {})
    whale = d1h.get("whale_acct_ls")
    ls_1h = d1h.get("taker_ls_ratio")
    funding = d1h.get("funding_rate")
    price = d1h.get("current_price", 0)

    # OI_30h hesapla
    oi_ts = data.get("api_open_interest", [])
    oi_30h = None
    if len(oi_ts) >= 2:
        oi_30h = oi_ts[-1][1] - oi_ts[0][1]

    # Whale time series
    whale_ts = data.get("api_whale_account", [])

    # LS series: P59 — api_taker_ls 30-entry 1h zaman serisi (varsa)
    ls_ts_raw = data.get("api_taker_ls", [])
    ls_series = [x[1] for x in ls_ts_raw] if ls_ts_raw else []
    # Fallback: 3-TF snapshot (eski yöntem, sınırlı)
    if not ls_series:
        for tf in ["15m", "1h", "4h"]:
            dtf = data.get(f"data_{tf}", {})
            v = dtf.get("taker_ls_ratio")
            if v:
                ls_series.append(v)
    # ls_series kısa (3 entry) — slope güvenilmez, sadece yön bilgisi

    # ═══ HESAPLA (sessiz) ═══
    d4h = data.get("data_4h", {})
    _4h_p = d4h.get("current_price", 0)
    _4h_ma30 = d4h.get("ma30", 0)
    pct_ma30_4h = ((_4h_p - _4h_ma30) / _4h_ma30 * 100) if _4h_p > 0 and _4h_ma30 > 0 else None
    leading = evaluate_leading(whale, oi_30h, ls_1h, pct_ma30_4h)
    approach_alerts = evaluate_approach(whale, oi_30h, ls_1h, pct_ma30_4h)
    roc = evaluate_rate_of_change(whale, ls_1h, whale_ts, oi_ts, ls_series)

    # ═══ KOMPAKT ÇIKTI ═══
    ts = datetime.now(timezone.utc).strftime("%H:%M UTC")
    icon = "★" if leading["karar"] == "GİR" else "⚠" if leading["karar"] == "GİR_DİKKAT" else "—"

    # Satır 1: Ana sonuç
    wh_s = f"W:{whale:.3f}" if whale else "W:?"
    ls_s = f"LS:{ls_1h:.3f}" if ls_1h else "LS:?"
    oi_s = f"OI:{oi_30h:+.0f}" if oi_30h is not None else "OI:?"
    ma_s = f"P/MA:{pct_ma30_4h:+.1f}%" if pct_ma30_4h is not None else ""
    print()
    print(f"█ {ts} | ${price:,.0f} | {icon} {leading['karar']} {leading['yon']} ({leading['kural']}) | {wh_s} {ls_s} {oi_s} {ma_s}")

    # Satır 2: Trend özeti (tek satır)
    trends = []
    if roc["whale_slope_6h"] is not None:
        trends.append(f"W:{roc['whale_trend']}({roc['whale_slope_6h']:+.4f}/h)")
    if roc["oi_slope_6h"] is not None:
        trends.append(f"OI:{roc['oi_trend']}({roc['oi_slope_6h']:+.0f}/h)")
    if roc["ls_slope"] is not None:
        trends.append(f"LS:{roc['ls_trend']}({roc['ls_slope']:+.4f})")
    if trends:
        print(f"  Trend: {' | '.join(trends)}")

    # Satır 3: Sadece önemli uyarılar (approach YAKIN + ETA ⚡)
    urgent = []
    for a in approach_alerts:
        if a["seviye"] == "YAKIN":
            urgent.append(f"🔴 {a['kural']} {a['param']} YAKIN ({a['uzaklik']:.4f})")
    for sig in roc.get("signals", []):
        if "⚡" in sig:
            urgent.append(sig)
    if urgent:
        for u in urgent:
            print(f"  {u}")

    # Satır 4: Deplasman uyarı (sadece >2.5% ise)
    if pct_ma30_4h is not None and pct_ma30_4h > 2.5:
        tag = "⛔ DEPLASMAN" if pct_ma30_4h > 3.0 else "⚠ DEPLASMAN_YAKIN"
        print(f"  {tag}: 4h%MA30={pct_ma30_4h:+.2f}%")

    # Sinyal değişimi (her zaman göster — kritik)
    if prev_leading and prev_leading.get("kural") != leading.get("kural"):
        print(f"  🔔🔔🔔 SİNYAL DEĞİŞTİ: {prev_leading['kural']} → {leading['kural']} 🔔🔔🔔")
        try:
            import android
            droid = android.Android()
            droid.vibrate(500)
            droid.makeToast(f"Leading: {leading['karar']} {leading['yon']}")
        except:
            pass

    # Bileşik durum — sadece GİRME'de ve yaklaşım varsa
    if leading["karar"] == "GİRME" and not urgent:
        approaching = [a for a in approach_alerts if a["seviye"] == "YAKLAŞIYOR"]
        if approaching:
            print(f"  🟡 {approaching[0]['kural']} yaklaşıyor")

    # GİR/GİR_DİKKAT'ta trend uyumsuzluğu
    if leading["karar"] in ("GİR", "GİR_DİKKAT"):
        if leading["yon"] == "LONG" and roc.get("whale_trend") == "ASAGI":
            print(f"  ⚠ Whale DÜŞÜYOR — sinyal zayıflayabilir")
        if leading["yon"] == "SHORT" and roc.get("oi_trend") == "AZALIYOR":
            print(f"  ⚠ OI DÜŞÜYOR — SHORT_TRAP düşebilir")

    # ─── KARAR MOTORU (DDF entegre) ───
    try:
        import importlib
        import karar_motoru as _km
        importlib.reload(_km)
        _km.run()
    except ImportError:
        print("  ⚠ karar_motoru.py bulunamadi")
    except Exception as _km_exc:
        print(f"  ⚠ karar_motoru hatasi: {_km_exc}")
    return leading


# ═══════════════════════════════════════════════════════════
# ANA DÖNGÜ
# ═══════════════════════════════════════════════════════════

def run_cycle(script_dir):
    """Tek bir monitoring döngüsü: fetch → analiz → rapor."""
    json_path = os.path.join(script_dir, "r_update.json")

    # auto_fetch çalıştır
    fetch_script = os.path.join(script_dir, "auto_fetch.py")
    if os.path.exists(fetch_script):
        print(f"\n  auto_fetch çalıştırılıyor...")
        try:
            subprocess.run(["python3", fetch_script], cwd=script_dir,
                            timeout=300)
        except subprocess.TimeoutExpired:
            print(f"  ⚠ auto_fetch 5dk'da bitmedi — mevcut r_update.json kullanılıyor")
    else:
        print(f"  ⚠ auto_fetch.py bulunamadı — mevcut r_update.json kullanılıyor")

    # JSON oku
    if not os.path.exists(json_path):
        print(f"  ❌ r_update.json bulunamadı: {json_path}")
        return None

    with open(json_path, "r") as f:
        data = json.load(f)

    return data


def main():
    # Argüman parse
    once = "--once" in sys.argv
    interval = DEFAULT_INTERVAL_MIN
    for i, arg in enumerate(sys.argv):
        if arg == "--interval" and i + 1 < len(sys.argv):
            try:
                interval = int(sys.argv[i + 1])
            except ValueError:
                pass

    # Script dir bul
    script_dir = find_script_dir()
    if not script_dir:
        # Fallback: mevcut dizin
        script_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"  ⚠ auto_fetch bulunamadı — mevcut dizin kullanılıyor: {script_dir}")

    print("=" * 60)
    print(f"  AUTO MONITOR — Kompakt (P61)")
    print(f"  Klasör: {script_dir}")
    print(f"  Döngü:  {'TEK SEFER' if once else f'{interval} dakika'}")
    print("=" * 60)

    prev_leading = None
    cycle = 0

    while True:
        cycle += 1
        data = run_cycle(script_dir)

        if data:
            prev_leading = print_monitor_report(data, prev_leading)
        else:
            print("  ❌ Veri alınamadı — sonraki döngüde tekrar denenir")

        if once:
            break

        # Bekle
        print(f"\n  ⏳ {interval}dk sonra tekrar | Ctrl+C çık")
        try:
            time.sleep(interval * 60)
        except KeyboardInterrupt:
            print("\n  Durduruldu.")
            break


if __name__ == "__main__":
    main()
