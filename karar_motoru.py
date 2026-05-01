#!/usr/bin/env python3
"""
karar_motoru.py  v1.0
══════════════════════════════════════════════════════════════════════
Unified Decision Engine — tüm analiz kaynaklarını tek merkezden
çağırır, tek birleşik tablo + tek NET_YON + NET_KARAR üretir.

Kural: Hiçbir modül kendi leading/yön hesabını yapmaz.
       Tüm ağırlıklı konsensüs mantığı bu dosyadadır.

──────────────────────────────────────────────────────────────────────
AĞIRLIK SİSTEMİ
  Normalize edilmiş doğruluk oranları (31 kapalı run, 2026-04-14):

  Kaynak        Ham oran  Normalize ağırlık
  ─────────     ────────  ─────────────────
  leading       %96       0.3609   (25 sinyal, backtest doğrulandı)
  sc            %88       0.3308   (25 sinyal, backtest doğrulandı)
  benzerlik     %82       0.3083   (CG≥85+SC, contamination-clean, n=28)
  multi_coin    —         flag     (backtest yok — teyit flagı)
  scorecard     —         flag     (backtest yok — teyit flagı)

  Toplam normalize: 2.66  →  her oran / 2.66
  Güncelleme: _RAW_ACCURACY'ye değer ekle → ağırlıklar otomatik
  yeniden hesaplanır.

KONSENSÜS EŞİKLERİ (net_margin = |long_score - short_score|)
  < CONSENSUS_MIN_MARGIN (0.10) → NOTR   (çok yakın split)
  < CONSENSUS_DIKKATLI_THR (0.25) → GİR deneliyor ama DİKKATLİ
  Skor senaryoları (referans):
    3/3 aynı yön        → margin 1.0000 → GİR
    2/3 aynı + 1 karşıt → margin 0.33-0.38 → GİR
    1/3 tek yön (NOTR)  → margin 0.3609 → GİR  (leading=0.96 güçlü sinyal)
    1/2 split + 1 NOTR  → margin 0.0301 → NOTR  (alt eşiğin altı)

BAĞIMLILIKLAR
  yon_41.py          (yüklenmiş, 6891 satır, FIX-5/6 aktif)
  benzerlik_analiz_sistemi_fixed.py  (590 satır, CG contamination fix'li)
  multi_coin.py                 (569 satır)
  yon_scorecard.py              (168 satır)
  entry_trigger_v2.py           (568 satır)
  r_update.json                 (tek veri kaynağı)

ENTEGRASYON
  auto_compact.py  → karar_motoru.run() çağır, inline leading kaldır
  auto_monitor.py  → evaluate_leading() kaldır, karar_motoru.run() çağır
══════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# ─── Yol konfigürasyonu ──────────────────────────────────────────────────────
BASE_DIR       = Path(__file__).parent
YON5_PATH             = BASE_DIR / "yon_41.py"
TRIGGER_PATH          = BASE_DIR / "entry_trigger_v2.py"
R_UPDATE_PATH         = BASE_DIR / "r_update.json"
ACCURACY_OVERRIDE_PATH = BASE_DIR / "accuracy_overrides.json"

# ─── Ağırlık sistemi ─────────────────────────────────────────────────────────
# None = flag-only (backtest tamamlanmadı, konsensüs oyuna katılmaz)
#
# OTOMATİK GÜNCELLEME: accuracy_overrides.json dosyasına değer ekle,
#   ağırlıklar bir sonraki çalıştırmada otomatik yeniden hesaplanır.
#   karar_motoru.py dosyasına dokunmak gerekmez.
#   Örnek: { "multi_coin": 0.84, "scorecard": 0.79 }
#   Geçerli aralık: 0.50–1.00  (dışı → uyarı + None korunur)
_RAW_ACCURACY: dict[str, Optional[float]] = {
    "leading":    0.96,   # leading_decision()  24D/1Y/6B=%96 n=25
    "sc":         0.88,   # compute_final_decision()         n=25
}


def _load_accuracy_overrides() -> None:
    """
    accuracy_overrides.json varsa yükle, _RAW_ACCURACY ve WEIGHTS güncelle.
    Sadece None olan alanları doldurur; sabit değerleri (leading, sc, benzerlik) ezmez.
    """
    global _RAW_ACCURACY, WEIGHTS

    if not ACCURACY_OVERRIDE_PATH.exists():
        return

    try:
        overrides: dict = json.loads(
            ACCURACY_OVERRIDE_PATH.read_text(encoding="utf-8")
        )
    except Exception as exc:
        print(f"[KARAR_MOTORU W] accuracy_overrides.json okunamadi: {exc}",
              file=sys.stderr)
        return

    updated: list[str] = []
    for key, val in overrides.items():
        if key not in _RAW_ACCURACY:
            print(f"[KARAR_MOTORU W] accuracy_overrides: bilinmeyen key {key!r} atildi",
                  file=sys.stderr)
            continue
        if _RAW_ACCURACY[key] is not None:
            continue  # sabit deger — ezilemez
        try:
            fval = float(val)
        except (TypeError, ValueError):
            print(f"[KARAR_MOTORU W] accuracy_overrides[{key!r}] gecersiz: {val!r}",
                  file=sys.stderr)
            continue
        if not (0.50 <= fval <= 1.00):
            print(f"[KARAR_MOTORU W] accuracy_overrides[{key!r}]={fval:.4f} "
                  f"aralik disi (0.50-1.00) atildi", file=sys.stderr)
            continue
        _RAW_ACCURACY[key] = fval
        updated.append(f"{key}={fval:.4f}")

    if not updated:
        return

    quantified   = {k: v for k, v in _RAW_ACCURACY.items() if v is not None}
    weight_total = sum(quantified.values())
    WEIGHTS      = {k: v / weight_total for k, v in quantified.items()}
    print(f"[KARAR_MOTORU] override yuklendi: {', '.join(updated)}", file=sys.stderr)
    print(f"[KARAR_MOTORU] yeni agirliklar: "
          + "  ".join(f"{k}={v:.4f}" for k, v in WEIGHTS.items()), file=sys.stderr)


_QUANTIFIED   = {k: v for k, v in _RAW_ACCURACY.items() if v is not None}
_WEIGHT_TOTAL = sum(_QUANTIFIED.values())   # baslangic: 2.66
WEIGHTS: dict[str, float] = {
    k: v / _WEIGHT_TOTAL for k, v in _QUANTIFIED.items()
}
_load_accuracy_overrides()   # override dosyasi varsa WEIGHTS guncellenir

# ─── Konsensüs eşikleri ──────────────────────────────────────────────────────
CONSENSUS_MIN_MARGIN   = 0.10   # altında → NOTR (split çok yakın)
CONSENSUS_DIKKATLI_THR = 0.25   # altında → GİR yerine DİKKATLİ


# ─── SHORT-ONLY MOD (P76) ────────────────────────────────────────────────────
# Backtest sonuçları (n=15, 6 SHORT + 9 LONG):
#   SHORT:     AvgR = +0.500R (sıkı SL=1.5× TP=3.0× ile +1.167R)
#   LONG:      AvgR = +0.111R (aynı parametrelerle başarısız)
#   LONG kök sorun: Stop hunt + stop çok sıkı, MFE/MAE oranı 1.46 (SHORT: 4.34)
# Walk-forward + LOO + duyarlılık testleri SHORT'u daha robust gösterdi.
# SHORT_ONLY_MODE=True iken LONG sinyalleri NOTR'a çevrilir (girilmez).
# Kapatmak için: SHORT_ONLY_MODE=False (çift yönlü moda döner).
SHORT_ONLY_MODE = True


# Gate FIX parametreleri — yon_41 FIX-5 ve FIX-6 eşdeğeri
# r_update.json alanları (doğrulanmış): vol_ratio_1h, ls_opposition,
#   h1_delta, h4_delta, macro_override, data_15m, data_1h, data_4h
FIX5_H1_THRESHOLD = 1.50    # |h1_delta| > bu → ÇOK KÜÇÜK BOYUT
FIX6_VOL_RATIO    = 0.50    # vol_ratio_1h < bu AND (LS karşıtlık + h4 koşulu)
FIX6_LS_OPP_THR  = 0.50    # ls_opposition > bu
FIX6_H4_THRESHOLD = 1.50   # |h4_delta| < bu → BEKLE (düşük hacimde)


# ══════════════════════════════════════════════════════════════════════
# VERİ YAPILARI
# ══════════════════════════════════════════════════════════════════════

@dataclass
class SourceResult:
    name:       str
    direction:  str             # 'LONG' | 'SHORT' | 'NOTR'
    confidence: str             # 'YÜKSEK' | 'ORTA' | 'DÜŞÜK' | '—'
    decision:   str             # 'GİR' | 'DİKKATLİ' | 'GİRME' | '—'
    score_raw:  str             # gösterim için ham skor/metrik
    weight:     Optional[float] # None = flag-only
    error:      Optional[str] = None


@dataclass
class ConsensusResult:
    long_score:      float
    short_score:     float
    notr_count:      int
    net_yon:         str          # 'LONG' | 'SHORT' | 'NOTR'
    net_margin:      float        # |long_score - short_score|
    alignment_flags: dict = field(default_factory=dict)  # multi_coin, scorecard yönleri


@dataclass
class GateResult:
    net_karar:       str          # 'GİR' | 'DİKKATLİ' | 'GİRME'
    net_boyut:       str          # 'NORMAL' | 'KÜÇÜK' | 'ÇOK KÜÇÜK' | 'BEKLE'
    flags:           list = field(default_factory=list)
    override_reason: Optional[str] = None


@dataclass
class KararMotoruOutput:
    timestamp:         str
    net_yon:           str
    net_karar:         str
    net_boyut:         str
    net_giris:         Optional[dict]     # entry_trigger çıktısı, sadece GİR'de
    sources:           list[SourceResult]
    consensus:         ConsensusResult
    gate:              GateResult
    confidence_margin: float


# ══════════════════════════════════════════════════════════════════════
# MODÜL YÜKLEME — exec() tekniği
# ══════════════════════════════════════════════════════════════════════

def _exec_module(path: Path) -> dict:
    """
    Modülü exec() ile yükle, namespace'i döndür.
    __name__ = '__exec__' → if __name__ == '__main__' guard'ları tetiklenmez.
    Benzerlik'in load_yon5 tekniğiyle aynı yaklaşım.
    """
    ns: dict = {"__name__": "__exec__", "__file__": str(path)}
    src = path.read_text(encoding="utf-8")
    exec(compile(src, str(path), "exec"), ns)  # noqa: S102
    return ns


# ══════════════════════════════════════════════════════════════════════
# STAGE 1 — COLLECT
# ══════════════════════════════════════════════════════════════════════

def _collect_yon5(r_data: dict) -> tuple[SourceResult, SourceResult]:
    """
    yon_41'i exec() ile yükle.
    Döndürür: (leading_result, sc_result)

    Doğrulanmış dönüş formatları (2026-04-14):
      - leading_decision(whale_ls, oi_delta_30h, ls_1h, pct_ma30_4h=None)
            → dict: {karar, yon, kural, guven, backtest, neden}
      - compute_scorecard(d15, d1h, d4h, whale_ls=None, oi_data=None)
            → dict: {direction, confidence, size, h15, h1, h4, ...}
      - compute_final_decision(result, d15, d1h, d4h, candle_result=None)
            → dict: {decision, direction, confidence, size, reason, ...}
    """
    try:
        ns = _exec_module(YON5_PATH)

        # r_update.json'dan yon_41 argümanları
        d15 = r_data.get("data_15m", {})
        d1h = r_data.get("data_1h",  {})
        d4h = r_data.get("data_4h",  {})

        # ── Leading decision ──────────────────────────────────────────
        # Signature: leading_decision(whale_ls, oi_delta_30h, ls_1h, pct_ma30_4h=None)
        whale_ls = float(d1h.get("whale_acct_ls",  1.0))
        ls_1h    = float(d1h.get("taker_ls_ratio", 1.0))

        # BUG-A FIX: oi_delta_30h = api_open_interest zaman serisinin
        # tamamının deltası (yon_41 main bloğuyla özdeş hesaplama).
        # d1h["oi_delta"] 1h anlık delta — 30h kümülatif DEĞİL.
        _oi_ts = r_data.get("api_open_interest", [])
        oi_delta_30h: Optional[float] = None
        if len(_oi_ts) >= 2:
            oi_delta_30h = float(_oi_ts[-1][1]) - float(_oi_ts[0][1])

        # BUG-B FIX: pct_ma30_4h displacement filtresi (LONG_ANA_DEPLASMAN).
        # None bırakılırsa ralli tepesi filtresi hiçbir zaman tetiklenmez.
        _4h_price  = float(d4h.get("current_price", 0))
        _4h_ma30   = float(d4h.get("ma30",          0))
        pct_ma30_4h: Optional[float] = None
        if _4h_price > 0 and _4h_ma30 > 0:
            pct_ma30_4h = (_4h_price - _4h_ma30) / _4h_ma30 * 100

        leading_raw = ns["leading_decision"](whale_ls, oi_delta_30h, ls_1h, pct_ma30_4h)

        # leading_decision her zaman dict döndürür; tuple/regex fallback korundu
        if isinstance(leading_raw, dict):
            lead_karar = str(leading_raw.get("karar", "—")).upper()
            lead_yon   = str(leading_raw.get("yon",   "NOTR")).upper()
            lead_kural = str(leading_raw.get("kural", "—"))
        elif isinstance(leading_raw, (tuple, list)) and len(leading_raw) >= 2:
            lead_karar = str(leading_raw[0]).upper()
            lead_yon   = str(leading_raw[1]).upper()
            lead_kural = str(leading_raw[2]) if len(leading_raw) > 2 else "—"
        else:
            m = re.search(
                r"LEADING:\s+\S+\s+(\S+)\s+(\S+)\s+\((\S+)\)",
                str(leading_raw),
            )
            lead_karar = m.group(1).upper() if m else "PARSE_HATASI"
            lead_yon   = m.group(2).upper()  if m else "NOTR"
            lead_kural = m.group(3)          if m else "—"

        # K-3 FIX: GİR_DİKKAT sinyalleri (LONG_ANA_GEÇ 0/5, SHORT_ZAYIF 1/1)
        # konsensüs oyuna katılmaz — accuracy hesabında dışlandıkları için
        # tam ağırlıkla (0.3609) oy kullanmaları ağırlık şişmesine yol açar.
        # score_raw'da gerçek yön+kural görünür (tablo şeffaflığı korunur).
        lead_vote_dir = _norm_dir(lead_yon)
        if "DİKKAT" in _norm_dec(lead_karar):
            lead_vote_dir = "NOTR"   # oy suppression
            lead_kural = f"[OY_BASKILI] {lead_kural} ({lead_yon})"

        leading_result = SourceResult(
            name="leading",
            direction=lead_vote_dir,
            confidence="—",
            decision=_norm_dec(lead_karar),
            score_raw=lead_kural,
            weight=WEIGHTS["leading"],
        )

        # ── Scorecard + final decision ────────────────────────────────
        # Signature: compute_scorecard(d15, d1h, d4h, whale_ls=None, oi_data=None)
        sc_raw = ns["compute_scorecard"](d15, d1h, d4h)

        # h1/h4 FIX-5/FIX-6 için stage_gate'e iletilir
        sc_h1: Optional[float] = float(sc_raw["h1"]) if isinstance(sc_raw, dict) and "h1" in sc_raw else None
        sc_h4: Optional[float] = float(sc_raw["h4"]) if isinstance(sc_raw, dict) and "h4" in sc_raw else None

        # Signature: compute_final_decision(result, d15, d1h, d4h, candle_result=None)
        if "compute_final_decision" in ns:
            final_raw = ns["compute_final_decision"](sc_raw, d15, d1h, d4h)
        else:
            final_raw = sc_raw

        # Doğrulanmış key isimleri: direction / decision / confidence / size
        if isinstance(final_raw, dict):
            sc_yon   = str(final_raw.get("direction",  "NOTR")).upper()
            sc_karar = str(final_raw.get("decision",   "—")).upper()
            sc_conf  = str(final_raw.get("confidence", "—")).upper()
            sc_skor  = str(final_raw.get("size",       "—"))
        else:
            sc_yon, sc_karar, sc_conf, sc_skor = "NOTR", "—", "—", str(final_raw)[:30]

        sc_result = SourceResult(
            name="sc",
            direction=_norm_dir(sc_yon),
            confidence=sc_conf,
            decision=_norm_dec(sc_karar),
            score_raw=sc_skor,
            weight=WEIGHTS["sc"],
        )

        # sc_extras: h1/h4 FIX-5/FIX-6 için stage_gate'e iletilir
        # active_run + hd: forward_tracker için (kapalı run tespiti)
        hd = ns.get("HISTORICAL_DATA", {})
        active_run: Optional[str] = None
        for _lbl, _rd in hd.items():
            if _rd.get("actual") is None:
                active_run = _lbl
                break
        sc_extras = {"h1": sc_h1, "h4": sc_h4, "active_run": active_run, "hd": hd}
        return leading_result, sc_result, sc_extras

    except Exception as exc:  # pylint: disable=broad-except
        _warn(f"yon_41 yükleme hatası: {exc}")
        err = str(exc)
        dummy_l = SourceResult("leading", "NOTR", "—", "GİRME", "HATA",
                               WEIGHTS["leading"], err)
        dummy_s = SourceResult("sc",      "NOTR", "—", "GİRME", "HATA",
                               WEIGHTS["sc"],      err)
        return dummy_l, dummy_s, {"h1": None, "h4": None}


def stage_collect(r_data: dict) -> tuple[list[SourceResult], dict]:
    """Stage 1: Tüm kaynakları çağır, (SourceResult listesi, sc_extras) döndür.
    sc_extras = {"h1": float|None, "h4": float|None} — FIX-5/FIX-6 için."""
    leading_res, sc_res, sc_extras = _collect_yon5(r_data)
    sources = [
        leading_res,
        sc_res,
    ]
    return sources, sc_extras


# ══════════════════════════════════════════════════════════════════════
# STAGE 2 — AGGREGATE
# ══════════════════════════════════════════════════════════════════════

def stage_aggregate(sources: list[SourceResult]) -> None:
    """Stage 2: Unified tabloyu stdout'a yaz."""
    sep = "─" * 72
    print(f"\n{sep}")
    print("  BİRLEŞİK KAYNAK TABLOSU")
    print(sep)
    print(f"  {'KAYNAK':<14} {'YÖN':<8} {'GÜVEN':<10} {'KARAR':<12} "
          f"{'SKOR/METRİK':<22} AĞIRLIK")
    print(f"  {'─'*70}")
    for s in sources:
        w_str  = f"w={s.weight:.4f}" if s.weight is not None else "flag   "
        err_mk = "  ⚠" if s.error else ""
        print(
            f"  {s.name:<14} {s.direction:<8} {s.confidence:<10} "
            f"{s.decision:<12} {s.score_raw:<22} {w_str}{err_mk}"
        )
    print(sep + "\n")


# ══════════════════════════════════════════════════════════════════════
# STAGE 3 — CONSENSUS
# ══════════════════════════════════════════════════════════════════════

def stage_consensus(sources: list[SourceResult]) -> ConsensusResult:
    """
    Stage 3: Ağırlıklı yön oyu.

    Oylama kuralları:
    - weight != None AND direction != 'NOTR' → oy kullanır
    - direction == 'NOTR' → oy kullanmaz (ağırlık sıfır muamele)
    - weight == None (flag-only) → alignment_flags'e kaydedilir, oy vermez
    - error alanı dolu → oy dışı bırakılır

    Normalize ağırlıklar:
      leading=0.3609  sc=0.3308  benzerlik=0.3083
    """
    long_score      = 0.0
    short_score     = 0.0
    notr_count      = 0
    alignment_flags: dict[str, str] = {}

    for src in sources:
        if src.error:
            continue  # hatalı kaynak oya katılmaz

        if src.weight is None:
            # Flag-only: alignment kaydı
            alignment_flags[src.name] = src.direction
            continue

        if src.direction == "LONG":
            long_score += src.weight
        elif src.direction == "SHORT":
            short_score += src.weight
        else:
            notr_count += 1

    margin  = abs(long_score - short_score)
    voted_w = long_score + short_score

    if voted_w == 0 or margin < CONSENSUS_MIN_MARGIN:
        net_yon = "NOTR"
    elif long_score > short_score:
        net_yon = "LONG"
    else:
        net_yon = "SHORT"

    # ─── SHORT-ONLY MOD FİLTRESİ (P76) ───────────────────────────────────
    # LONG sinyali geldiyse NOTR'a çevir. Backtest: LONG AvgR=+0.111R çok zayıf.
    # alignment_flags'e orijinal yön kaydedilir (dashboard'da görünür).
    if SHORT_ONLY_MODE and net_yon == "LONG":
        alignment_flags["SHORT_ONLY_VETO"] = "LONG→NOTR (mod aktif)"
        net_yon = "NOTR"

    return ConsensusResult(
        long_score=round(long_score, 4),
        short_score=round(short_score, 4),
        notr_count=notr_count,
        net_yon=net_yon,
        net_margin=round(margin, 4),
        alignment_flags=alignment_flags,
    )


# ══════════════════════════════════════════════════════════════════════
# DDF — DÖNÜŞ/DEVAM FİLTRESİ (6 kriter: K1+K2+K3+K6+K8+K9, eşik=3)
# ══════════════════════════════════════════════════════════════════════
# Backtest (32 run, SC direction, ADIM 4 veri seçimi):
#   Ham: 22 doğru / 4 yanlış → S4=-$10,100
#   Filtre: 22D geçti, 4Y bloke → S4=+$1,100 (fark: +$11,200)
#   PREC/REC/F1 = 1.00/1.00/1.00
# K4, K5, K7 HIÇ YOK — backtest'te hiçbir varyantta seçilmediler.

DDF_ESIK = 3   # >=3 tetiklenirse GİR → GİRME (ADIM 4 veri seçimi)


def _calc_ddf(r_data: dict, direction: str) -> tuple[int, list]:
    """
    DDF: 6 kriter (K1, K2, K3, K6, K8, K9) üzerinden dönüş sinyali tespiti.
    
    Returns:
      (score: int, kriterler: list[tuple[str, bool]])
    
    Kriterler direction'a göre değerlendirilir. Her tetiklenen kriter +1.
    Skor >= DDF_ESIK (3) ise dönüş sinyali kuvvetli → GİR engellenir.
    """
    if direction not in ("LONG", "SHORT"):
        return 0, []

    d1h = r_data.get("data_1h", {})
    d4h = r_data.get("data_4h", {})
    price   = float(d1h.get("current_price", 0) or 0)
    ma30_1h = float(d1h.get("ma30", 0) or 0)
    ma30_4h = float(d4h.get("ma30", 0) or 0)
    ma5_1h  = float(d1h.get("ma5",  0) or 0)
    ma10_1h = float(d1h.get("ma10", 0) or 0)

    # K1: TF çatışması (1h ve 4h MA30'a göre fiyat pozisyonu farklı)
    k1 = False
    if ma30_1h > 0 and ma30_4h > 0 and price > 0:
        k1 = (price > ma30_1h) != (price > ma30_4h)

    # K2: OI eğim tersi
    k2 = False
    oi_list = r_data.get("api_open_interest", [])
    if len(oi_list) >= 2:
        try:
            d30h = float(oi_list[-1][1]) - float(oi_list[0][1])
            s1 = float(d1h.get("oi_slope", 0) or 0)
            s4 = float(d4h.get("oi_slope", 0) or 0)
            if direction == "SHORT":
                k2 = d30h > 0 and s1 < 0 and s4 < 0
            else:
                k2 = d30h < 0 and s1 > 0 and s4 > 0
        except Exception:
            pass

    # K3: Ters trend pozisyonu
    k3 = False
    if ma30_4h > 0 and price > 0:
        pct = (price - ma30_4h) / ma30_4h * 100
        if direction == "SHORT":
            k3 = pct > 0
        else:
            k3 = pct < 0

    # K6: Funding squeeze
    k6 = False
    try:
        fr = float(d1h.get("funding_rate", 0) or 0)
        apr = fr * 3 * 365 * 100
        if direction == "SHORT":
            k6 = apr > 3.0
        else:
            k6 = apr < -3.0
    except Exception:
        pass

    # K8: LS uyumsuzluğu
    k8 = False
    try:
        ls = float(d1h.get("taker_ls_ratio", 1.0) or 1.0)
        if direction == "SHORT":
            k8 = ls > 1.0
        else:
            k8 = ls < 0.85
    except Exception:
        pass

    # K9: 1h MA sıralaması ters
    k9 = False
    if ma5_1h > 0 and ma10_1h > 0 and ma30_1h > 0 and price > 0:
        if direction == "SHORT":
            k9 = price > ma5_1h > ma10_1h > ma30_1h
        else:
            k9 = price < ma5_1h < ma10_1h < ma30_1h

    kriterler = [
        ("K1", bool(k1)),
        ("K2", bool(k2)),
        ("K3", bool(k3)),
        ("K6", bool(k6)),
        ("K8", bool(k8)),
        ("K9", bool(k9)),
    ]
    score = sum(1 for _, v in kriterler if v)
    return score, kriterler
# ══════════════════════════════════════════════════════════════════════
# STAGE 4 — GATE
# ══════════════════════════════════════════════════════════════════════

def stage_gate(
    consensus:  ConsensusResult,
    r_data:     dict,
    sc_extras:  Optional[dict] = None,
) -> GateResult:
    """
    Stage 4: Çatışma tespiti + FIX kuralları.

    Değerlendirme sırası:
    1. Konsensüs yok (NOTR) → erken çıkış
    2. FIX-6: düşük hacim + LS karşıtlık + h4 filtre → BEKLE/GİRME
    3. FIX-5: gecikmeli giriş |h1| eşiği → boyut ayarı
    4. Flag çatışması (multi_coin + scorecard)
    5. Marjin kalitesi → GİR / DİKKATLİ

    sc_extras: {"h1": float|None, "h4": float|None} — compute_scorecard çıktısından.
    NOT: FIX-6 davranışı yon_41'ten kasıtlı olarak ayrışır.
    yon_41: size=COK_KUCUK_BOYUT (pozisyon açılabilir, küçük boyut).
    karar_motoru: return GİRME (koşulsuz blok) — daha muhafazakâr.
    FIX-5 yon_41 implementasyonuyla birebir eşleşir (V9).
    """
    flags: list[str]     = []
    override_reason      = None
    net_boyut            = "NORMAL"
    sc_h1 = (sc_extras or {}).get("h1")
    sc_h4 = (sc_extras or {}).get("h4")

    # ── 1. Konsensüs yok ─────────────────────────────────────────────
    if consensus.net_yon == "NOTR":
        return GateResult(
            "GİRME", "BEKLE",
            ["NOTR_KONSENSÜS"],
            "Ağırlıklı oy eşiğin altında veya split"
        )

    d1h = r_data.get("data_1h", {})

    # ── 2. FIX-6: Düşük hacim + LS karşıtlığı ────────────────────────
    # Yon_5 V9 implementasyonuyla özdeş (satır 1106-1127):
    #   vol_ratio = vol / ((vol_ma5 + vol_ma10) / 2)
    #   ls_opposition = (ls-1.0) if SHORT+ls>1 else (1.0-ls) if LONG+ls<1 else 0
    #   bekle = low_vol AND high_ls AND abs(h4)<1.50
    _vol   = float(d1h.get("volume",     0))
    _vma5  = float(d1h.get("volume_ma5",  0))
    _vma10 = float(d1h.get("volume_ma10", 0))
    # O-1: vol_ma10 yoksa FIX-6 vol_ratio güvenilmez — uyar
    if _vma10 == 0:
        flags.append("FIX6_UYARI  volume_ma10 eksik — vol_ratio yarım average'dan hesaplandı, FIX-6 tetiklenemeyebilir")
    _avg   = (_vma5 + _vma10) / 2.0
    vol_ratio = _vol / _avg if _avg > 0 else 1.0

    # ls_opp consensus.net_yon'a göre hesaplanır (yon_41: sc.direction baz alır).
    # Kasıtlı ayrışma: karar_motoru'nda birleşik konsensüs yönü referanstır.
    # Senaryo: SC=SHORT leading=LONG benz=LONG → consensus=LONG.
    # yon_41 sc.direction=SHORT baz alır → farklı ls_opp. Burada LONG baz → doğru.
    _ls = float(d1h.get("taker_ls_ratio") or 1.0)
    ls_opp = 0.0
    if consensus.net_yon == "SHORT" and _ls > 1.0:
        ls_opp = _ls - 1.0
    elif consensus.net_yon == "LONG" and _ls < 1.0:
        ls_opp = 1.0 - _ls

    h4_abs = abs(sc_h4) if sc_h4 is not None else 99.0  # h4 yoksa FIX-6 tetiklenmez

    if (
        vol_ratio < FIX6_VOL_RATIO
        and ls_opp > FIX6_LS_OPP_THR
        and h4_abs < FIX6_H4_THRESHOLD
    ):
        flags.append(
            f"FIX6_BEKLE  vol={vol_ratio:.2f}<{FIX6_VOL_RATIO}  "
            f"ls_opp={ls_opp:.2f}>{FIX6_LS_OPP_THR}  |h4|={h4_abs:.2f}<{FIX6_H4_THRESHOLD}"
        )
        return GateResult(
            "GİRME", "BEKLE", flags,
            "FIX-6: Düşük hacim + LS karşıtlığı + zayıf 4h"
        )

    # ── 3. FIX-5: Gecikmeli giriş kontrol ────────────────────────────
    # Yon_5 V9: abs(h1) > 1.50 → COK KUCUK BOYUT
    h1_abs = abs(sc_h1) if sc_h1 is not None else 0.0  # h1 yoksa FIX-5 tetiklenmez
    if h1_abs > FIX5_H1_THRESHOLD:
        flags.append(
            f"FIX5_GECİKMELİ_GİRİŞ  |h1|={h1_abs:.2f}>{FIX5_H1_THRESHOLD}"
        )
        net_boyut = "ÇOK KÜÇÜK"


    # ── 5. Marjin kalitesi → net karar ───────────────────────────────
    if consensus.net_margin < CONSENSUS_DIKKATLI_THR:
        flags.append(
            f"DÜŞÜKMARJİN  {consensus.net_margin:.4f} < {CONSENSUS_DIKKATLI_THR}"
        )
        net_karar = "DİKKATLİ"
    elif net_boyut == "ÇOK KÜÇÜK":
        net_karar = "DİKKATLİ"
    else:
        net_karar = "GİR"

    return GateResult(net_karar, net_boyut, flags, override_reason)


# ══════════════════════════════════════════════════════════════════════
# ENTRY TRIGGER — koşullu
# ══════════════════════════════════════════════════════════════════════

def _call_entry_trigger(net_yon: str) -> Optional[dict]:
    """
    Sadece net_karar == 'GİR' olduğunda çağrılır.
    Doğrulanmış signature (2026-04-14):
      snapshot(direction, balance=5000, adx_override=None) → dict (levels)
    """
    try:
        ns = _exec_module(TRIGGER_PATH)
        # Doğrulanmış signature (2026-04-14):
        # snapshot(direction, balance=5000, adx_override=None)
        if "snapshot" in ns:
            result = ns["snapshot"](direction=net_yon)
        else:
            # Alternatif giriş noktaları
            for fname in ("run", "get_entry", "trigger"):
                if fname in ns:
                    result = ns[fname](direction=net_yon)
                    break
            else:
                return {"hata": "entry_trigger_v2: giriş noktası bulunamadı"}

        return result if isinstance(result, dict) else {"raw": str(result)}
    except Exception as exc:
        _warn(f"entry_trigger hatası: {exc}")
        return {"hata": str(exc)}


# ══════════════════════════════════════════════════════════════════════
# YARDIMCI FONKSİYONLAR
# ══════════════════════════════════════════════════════════════════════

def _norm_dir(raw: str) -> str:
    """Ham yön string'ini normalize et."""
    r = raw.strip().upper()
    if r in ("LONG",  "UP",   "AL",  "BUY"):  return "LONG"
    if r in ("SHORT", "DOWN", "SAT", "SELL"): return "SHORT"
    return "NOTR"


def _norm_dec(raw: str) -> str:
    """Ham karar string'ini normalize et."""
    r = raw.strip().upper()
    if "GİRME" in r or "GIRME" in r:          return "GİRME"
    if "DİKKAT" in r or "DIKKAT" in r:        return "DİKKATLİ"
    if "GİR" in r or "GIR" in r:              return "GİR"
    return "—"


def _warn(msg: str) -> None:
    print(f"[KARAR_MOTORU ⚠] {msg}", file=sys.stderr)


def _print_summary(out: KararMotoruOutput) -> None:
    """Sonuç özeti + ağırlık şeffaflığı.
    
    SHORT_ONLY_MODE=True: Dashboard sadece SHORT dilinde konuşur.
      Değer haritası:
        net_yon=SHORT + net_karar=GİR        → SHORT SİNYAL: GİR
        net_yon=SHORT + net_karar=DİKKATLİ   → SHORT SİNYAL: GİR AMA DİKKAT
        net_yon=SHORT + net_karar=GİRME      → SHORT SİNYAL: GİRME
        net_yon=LONG (iç state, filtrelendi) → SHORT SİNYAL: GEÇ
        net_yon=NOTR (margin düşük)          → SHORT SİNYAL: BEKLE
    SHORT_ONLY_MODE=False: Eski çift-yönlü format.
    """
    bar = "═" * 72
    print(bar)
    print(f"  KARAR MOTORU SONUCU  —  {out.timestamp}")
    
    if SHORT_ONLY_MODE:
        # ═══ SHORT DİLİ DASHBOARD ═══
        print("  MOD          :  SHORT-ONLY ✓")
        print(bar)
        
        # SHORT SİNYAL haritası
        # not: out.net_yon'un orijinal değeri "LONG" olmuşsa filtre onu "NOTR"'a
        # çevirdi; LONG'u ayırt etmek için SHORT_ONLY_VETO flag'ine bakıyoruz.
        has_long_pressure = "SHORT_ONLY_VETO" in out.consensus.alignment_flags
        
        if out.net_yon == "SHORT":
            if out.net_karar == "GİR":
                short_sinyal = "GİR"
                aciklama = "SHORT koşulları sağlandı"
            elif out.net_karar == "DİKKATLİ":
                short_sinyal = "GİR AMA DİKKAT"
                aciklama = "SHORT ama margin düşük veya boyut küçük"
            else:  # GİRME
                short_sinyal = "GİRME"
                aciklama = "SHORT yön var ama gate bloke etti"
        elif has_long_pressure:
            # LONG geldi ama filtre NOTR'a çevirdi
            short_sinyal = "GEÇ"
            aciklama = "karşı baskı güçlü (SHORT için uygun zaman değil)"
        else:
            # NOTR (margin düşük, hiçbir yön baskın değil)
            short_sinyal = "BEKLE"
            aciklama = "piyasa kararsız"
        
        print(f"  SHORT SİNYAL :  {short_sinyal}")
        print(f"                  ({aciklama})")
        print(f"  BOYUT        :  {out.net_boyut}")
        print(f"  MARGIN       :  {out.confidence_margin:.4f}"
              f"  (min={CONSENSUS_MIN_MARGIN}  dikkatli<{CONSENSUS_DIKKATLI_THR})")
        print(f"  SHORT BASKI  :  {out.consensus.short_score:.4f}"
              f"  KARŞI BASKI: {out.consensus.long_score:.4f}"
              f"  KARARSIZ: {out.consensus.notr_count}")
        
        if out.gate.flags:
            print("  GATE:")
            for f in out.gate.flags:
                print(f"    ⚠  {f}")
        if out.gate.override_reason:
            print(f"  OVERRIDE     :  {out.gate.override_reason}")
        if out.net_giris:
            print(f"  GİRİŞ (ET)   :  {out.net_giris}")
        print(bar)
    
    else:
        # ═══ ORIJINAL ÇIFT YÖNLÜ DASHBOARD (SHORT_ONLY_MODE=False) ═══
        print(bar)
        print(f"  NET YÖN      :  {out.net_yon}")
        print(f"  NET KARAR    :  {out.net_karar}")
        print(f"  NET BOYUT    :  {out.net_boyut}")
        print(f"  MARGIN       :  {out.confidence_margin:.4f}"
              f"  (min={CONSENSUS_MIN_MARGIN}  dikkatli<{CONSENSUS_DIKKATLI_THR})")
        print(f"  LONG W       :  {out.consensus.long_score:.4f}"
              f"  SHORT W: {out.consensus.short_score:.4f}"
              f"  NOTR: {out.consensus.notr_count}")
        if out.gate.flags:
            print("  GATE:")
            for f in out.gate.flags:
                print(f"    ⚠  {f}")
        if out.gate.override_reason:
            print(f"  OVERRIDE     :  {out.gate.override_reason}")
        if out.net_giris:
            print(f"  GİRİŞ (ET)   :  {out.net_giris}")
        print(bar)
    
    # Ağırlık şeffaflığı — her iki modda da aynı
    print("  Ağırlık sistemi (normalize):")
    for k in ("leading", "sc"):
        acc = _RAW_ACCURACY.get(k)
        if acc is not None and k in WEIGHTS:
            w_val = WEIGHTS[k]
            print(f"    {k:<14}: w={w_val:.4f}  ({acc * 100:.0f}% ham)")
        else:
            print(f"    {k:<14}: flag-only  (accuracy_overrides.json bekleniyor)")
    print(bar + "\n")


# ══════════════════════════════════════════════════════════════════════
# ANA FONKSİYON
# ══════════════════════════════════════════════════════════════════════

def run() -> KararMotoruOutput:
    """
    Karar motorunu çalıştır, KararMotoruOutput döndür.

    Entegrasyon:
      auto_compact.py  → from karar_motoru import run; out = run()
      auto_monitor.py  → aynı; evaluate_leading() kaldırılır
    """
    # r_update.json oku
    try:
        r_data: dict = json.loads(R_UPDATE_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        _warn(f"r_update.json okunamadı: {exc}")
        r_data = {}

    # Stage 1 — Collect
    sources, sc_extras = stage_collect(r_data)

    # Stage 2 — Aggregate (tablo yazdır)
    stage_aggregate(sources)

    # Stage 3 — Consensus
    consensus = stage_consensus(sources)

    # Stage 4 — Gate (sc_extras: h1/h4 FIX-5/FIX-6 için)
    gate = stage_gate(consensus, r_data, sc_extras)

    # Stage 4.5 — DDF (Dönüş/Devam Filtresi): sadece GİR kararında aktif
    # ADIM 4 verisi: K1+K2+K3+K6+K8+K9 eşik=3 → 32 run'da %100 filtre başarısı
    if gate.net_karar == "GİR" and consensus.net_yon in ("LONG", "SHORT"):
        ddf_score, ddf_kriterler = _calc_ddf(r_data, consensus.net_yon)
        tetiklenen = [k for k, v in ddf_kriterler if v]
        if ddf_score >= DDF_ESIK:
            gate.flags.append(
                f"DDF_BLOK  skor={ddf_score}/6 >=eşik={DDF_ESIK}  "
                f"kriterler={tetiklenen}"
            )
            gate.net_karar = "GİRME"
            gate.net_boyut = "BEKLE"
            gate.override_reason = (
                f"DDF: {ddf_score}/6 kriter ters sinyal (dönüş noktası)"
            )
        else:
            gate.flags.append(
                f"DDF_OK    skor={ddf_score}/6 <eşik={DDF_ESIK}  "
                f"kriterler={tetiklenen}"
            )


    # Entry trigger — sadece GİR kararında
    net_giris: Optional[dict] = None
    if gate.net_karar == "GİR":
        net_giris = _call_entry_trigger(consensus.net_yon)

    out = KararMotoruOutput(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        net_yon=consensus.net_yon,
        net_karar=gate.net_karar,
        net_boyut=gate.net_boyut,
        net_giris=net_giris,
        sources=sources,
        consensus=consensus,
        gate=gate,
        confidence_margin=consensus.net_margin,
    )

    _print_summary(out)


    return out


if __name__ == "__main__":
    run()
