#!/usr/bin/env python3
"""
ENTRY TRIGGER V2 — Üçlü Zaman Dilimi Giriş Sistemi
4H sinyal → 1H onay → 15m giriş

P62 V2 — Araştırma konsensüsü bazlı tam yeniden yazım:
  [1] TF yapısı: 4H→5m (48:1) → 4H→1H→15m (4:1 + 4:1) [Elder Factor of Five]
  [2] ATR SL: sabit 2.0× → ADX adaptif (ADX<25: 2.0×, ADX≥25: 2.5×)
  [3] ATR periyot: 12 (5m) → 14 (15m)
  [4] Pozisyon: sabit $50 → bakiye × %1
  [5] Giriş: %100 limit → %50 market + %50 limit (hibrit)
  [6] Timeout: 180dk → 120dk + fiyat bazlı iptal (ATR×1.5)
  [7] Pullback: ATR×0.5 (korundu)

KAYNAKLAR:
  Elder Triple Screen (Factor of Five), QuantPedia MTF BTC backtest,
  SuperTrend crypto ATR config, Van Tharp position sizing,
  Oxford Bybit/Binance adverse selection study, Alpha decay research

KULLANIM:
  python3 entry_trigger_v2.py LONG             # snapshot
  python3 entry_trigger_v2.py SHORT            # snapshot
  python3 entry_trigger_v2.py LONG monitor     # aktif bekleme
  python3 entry_trigger_v2.py LONG --balance 5000  # bakiye belirt

Pydroid3'te aynı klasörde olmalı: yon_*.py, auto_fetch.py, vs.
"""

import urllib.request
import json
import time
import sys

# ═══════════════════════════════════════
# CONFIG — Araştırma konsensüsü bazlı
# ═══════════════════════════════════════

SYMBOL = "BTCUSDT"

# --- Zaman dilimleri (Elder 4:1 prensibi) ---
TF_SIGNAL = "4h"          # ana yön sinyali
TF_CONFIRM = "1h"         # ara trend onayı
TF_ENTRY = "15m"           # giriş tetikleyici

# --- ATR ayarları (P76 SHORT-ONLY kalibrasyonu) ---
# Backtest (n=6 SHORT, walk-forward + LOO + duyarlılık):
#   SL=1.5× TP=3.0× → AvgR=+1.167R, worst-case WF=+1.000R, LOO±0.43R
#   SL=0.8× TP=3.0× → +1.542R ama fragile (LOO±0.51R, küçük veri overfit)
#   SL=1.5× TP=2.5× → +0.944R (alternatif), SL=2.0× TP=3.0× → +0.833R
# Seçilen: SL=1.5×, TP=3.0× → R:R=2.0, en stabil plato
ATR_PERIOD = 14            # 15m mum (3.5 saat pencere)
ATR_SL_MULT_RANGE = 1.5    # ADX < 25 → ranging (eski 2.0)
ATR_SL_MULT_TREND = 1.5    # ADX ≥ 25 → trending (eski 2.5, SHORT'ta ayrım gereksiz)
ADX_THRESHOLD = 25.0       # adaptif SL eşiği (SHORT-ONLY'de pratik etkisi yok)

# --- Giriş ---
PULLBACK_ZONE = 0.5        # pullback tetik = ATR × bu
HYBRID_MARKET_PCT = 0.50   # %50 market anında
HYBRID_LIMIT_PCT = 0.50    # %50 limit pullback'te

# --- Risk yönetimi ---
RISK_PCT = 0.01            # bakiyenin %1'i per trade
DEFAULT_BALANCE = 5000     # varsayılan bakiye ($)
MAX_RISK_PCT = 0.02        # asla %2'yi aşma

# --- Hedefler (P76 SHORT-ONLY: TP1 genişletildi, R:R=2.0) ---
# Eski: P67 kalibrasyon TP1=2.0× (sabit ATR proxy), backtest yanıltıcıydı.
# Yeni: P76 per-run ATR, MFE/MAE bazlı doğru simülasyon (15 run).
#   TP1=3.0×: SHORT için %83 hit, medyan MFE=$950 (ATR~$270) → TP yakalanır
#   TP2=4.0×: AYNI — stretch hedef, kısmi kâr alma imkânı
TP1_ATR_MULT = 3.0         # TP1 = ATR × 3.0 (eski 2.0)
TP2_ATR_MULT = 4.0         # TP2 = ATR × 4.0 (aynı)
RR_MIN = 0.5               # R:R gate (yeni R:R=2.0 >> 0.5, her zaman geçer)

# --- BE (Break-Even) trailing (P76 YENİ) ---
# MFE fiyat entry'den ATR×BE_TRIGGER_ATR kadar lehimize hareket ettiğinde
# SL'yi entry seviyesine çek. Canlıda Binance üzerinden manuel güncelleme.
# Backtest: R8 (MFE=$1402, MAE=$526, SL tetiklerdi) → BE ile TP'ye ulaştı.
# UYARI: BE mantığı MFE/MAE bazlı simülasyondan çıktı, zaman sırası bilgisi
# yok. Canlıda BE sonrası fiyat TP'ye dönmeyebilir (iyimser tahmin).
BE_TRIGGER_ATR = 1.0       # MFE ≥ ATR×1.0 → SL'yi entry'ye çek

# --- Timeout ---
TIMEOUT_MINUTES = 120      # 120dk (24 × 5m veya 8 × 15m mum)
PRICE_CANCEL_ATR = 1.5     # fiyat ATR×1.5 uzaklaşırsa iptal
CHECK_INTERVAL = 30        # saniye

# ═══════════════════════════════════════
# DATA FETCH
# ═══════════════════════════════════════

def _fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  [HATA] fetch: {e}")
        return None

def fetch_klines(interval="15m", limit=30):
    """Binance'den klines çek."""
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={SYMBOL}&interval={interval}&limit={limit}"
    raw = _fetch(url)
    if not raw:
        return []
    candles = []
    for c in raw:
        candles.append({
            "open_time": c[0],
            "open": float(c[1]),
            "high": float(c[2]),
            "low": float(c[3]),
            "close": float(c[4]),
            "volume": float(c[5]),
        })
    return candles

def fetch_current_price():
    url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={SYMBOL}"
    data = _fetch(url)
    return float(data["price"]) if data else None

# ═══════════════════════════════════════
# HESAPLAMALAR
# ═══════════════════════════════════════

def calc_atr(candles, period=ATR_PERIOD):
    """True Range bazlı ATR."""
    if len(candles) < period + 1:
        return None
    trs = []
    for i in range(1, len(candles)):
        c = candles[i]
        prev_close = candles[i-1]["close"]
        tr = max(
            c["high"] - c["low"],
            abs(c["high"] - prev_close),
            abs(c["low"] - prev_close)
        )
        trs.append(tr)
    if len(trs) < period:
        return None
    return sum(trs[-period:]) / period

def calc_adx(candles, period=14):
    """ADX hesapla (Wilder's smoothing)."""
    if len(candles) < period * 2 + 1:
        return None
    
    plus_dm_list = []
    minus_dm_list = []
    tr_list = []
    
    for i in range(1, len(candles)):
        high = candles[i]["high"]
        low = candles[i]["low"]
        prev_high = candles[i-1]["high"]
        prev_low = candles[i-1]["low"]
        prev_close = candles[i-1]["close"]
        
        plus_dm = max(high - prev_high, 0) if (high - prev_high) > (prev_low - low) else 0
        minus_dm = max(prev_low - low, 0) if (prev_low - low) > (high - prev_high) else 0
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        
        plus_dm_list.append(plus_dm)
        minus_dm_list.append(minus_dm)
        tr_list.append(tr)
    
    if len(tr_list) < period:
        return None
    
    # Wilder's smoothing
    atr_s = sum(tr_list[:period])
    plus_di_s = sum(plus_dm_list[:period])
    minus_di_s = sum(minus_dm_list[:period])
    
    dx_list = []
    for i in range(period, len(tr_list)):
        atr_s = atr_s - (atr_s / period) + tr_list[i]
        plus_di_s = plus_di_s - (plus_di_s / period) + plus_dm_list[i]
        minus_di_s = minus_di_s - (minus_di_s / period) + minus_dm_list[i]
        
        if atr_s == 0:
            continue
        plus_di = 100 * plus_di_s / atr_s
        minus_di = 100 * minus_di_s / atr_s
        
        di_sum = plus_di + minus_di
        if di_sum == 0:
            dx_list.append(0)
        else:
            dx_list.append(100 * abs(plus_di - minus_di) / di_sum)
    
    if len(dx_list) < period:
        return None
    
    adx = sum(dx_list[:period]) / period
    for i in range(period, len(dx_list)):
        adx = (adx * (period - 1) + dx_list[i]) / period
    
    return adx

def calc_ema(candles, period=20):
    """EMA hesapla."""
    if len(candles) < period:
        return None
    mult = 2 / (period + 1)
    ema = sum(c["close"] for c in candles[:period]) / period
    for c in candles[period:]:
        ema = (c["close"] - ema) * mult + ema
    return ema

def calc_ma(candles, period=20):
    """SMA hesapla."""
    if len(candles) < period:
        return None
    return sum(c["close"] for c in candles[-period:]) / period

# ═══════════════════════════════════════
# 1H ONAY KATMANI (Elder 2. Ekran)
# ═══════════════════════════════════════

def check_1h_confirmation(direction):
    """
    1H trend, 4H sinyaliyle uyumlu mu?
    LONG → 1H fiyat > EMA20 + son 3 mum yükselen dip
    SHORT → 1H fiyat < EMA20 + son 3 mum düşen tepe
    Return: {confirmed, price, ema20, trend, detail}
    """
    candles = fetch_klines(interval="1h", limit=30)
    if len(candles) < 21:
        return {"confirmed": None, "detail": "1H veri yetersiz"}
    
    price = candles[-1]["close"]
    ema20 = calc_ema(candles, 20)
    
    # Son 3 mumun trendi
    last3 = candles[-3:]
    higher_lows = last3[1]["low"] > last3[0]["low"] and last3[2]["low"] > last3[1]["low"]
    lower_highs = last3[1]["high"] < last3[0]["high"] and last3[2]["high"] < last3[1]["high"]
    
    if direction == "LONG":
        above_ema = price > ema20
        trend_ok = higher_lows
        confirmed = above_ema  # minimum: EMA üstünde
        strength = "GÜÇLÜ" if (above_ema and trend_ok) else "ZAYIF" if above_ema else "RED"
    else:
        below_ema = price < ema20
        trend_ok = lower_highs
        confirmed = below_ema
        strength = "GÜÇLÜ" if (below_ema and trend_ok) else "ZAYIF" if below_ema else "RED"
    
    return {
        "confirmed": confirmed,
        "price": round(price, 1),
        "ema20": round(ema20, 1),
        "higher_lows": higher_lows,
        "lower_highs": lower_highs,
        "strength": strength,
        "detail": f"{'>' if price > ema20 else '<'} EMA20 | {'HL' if higher_lows else ''} {'LH' if lower_highs else ''}"
    }

# ═══════════════════════════════════════
# 15m GİRİŞ SEVİYELERİ (Elder 3. Ekran)
# ═══════════════════════════════════════

def calc_entry_levels(candles, direction, atr, adx, price):
    """
    15m veriden giriş seviyeleri hesapla.
    ADX bazlı adaptif SL çarpanı.
    P67: TP ATR bazlı (sabit $ yerine).
    """
    recent = candles[-ATR_PERIOD:]
    
    # ADX adaptif SL çarpanı (P76 SHORT-ONLY: her ikisi 1.5×, ayrım kalmadı)
    if adx is not None and adx >= ADX_THRESHOLD:
        sl_mult = ATR_SL_MULT_TREND  # 1.5× (P76)
        regime = "TREND"
    else:
        sl_mult = ATR_SL_MULT_RANGE  # 1.5× (P76)
        regime = "RANGE"
    
    sl_distance = atr * sl_mult
    tp1_distance = atr * TP1_ATR_MULT
    tp2_distance = atr * TP2_ATR_MULT
    
    if direction == "LONG":
        support = min(c["low"] for c in recent)
        trigger = support + atr * PULLBACK_ZONE
        sl = trigger - sl_distance
        tp1 = trigger + tp1_distance
        tp2 = trigger + tp2_distance
        return {
            "direction": "LONG",
            "regime": regime,
            "sl_mult": sl_mult,
            "support": round(support, 1),
            "trigger": round(trigger, 1),
            "sl": round(sl, 1),
            "tp1": round(tp1, 1),
            "tp2": round(tp2, 1),
            "atr": round(atr, 1),
            "adx": round(adx, 1) if adx else None,
            "sl_distance": round(sl_distance, 1),
            "tp1_distance": round(tp1_distance, 1),
            "tp2_distance": round(tp2_distance, 1),
        }
    else:
        resistance = max(c["high"] for c in recent)
        trigger = resistance - atr * PULLBACK_ZONE
        sl = trigger + sl_distance
        tp1 = trigger - tp1_distance
        tp2 = trigger - tp2_distance
        return {
            "direction": "SHORT",
            "regime": regime,
            "sl_mult": sl_mult,
            "resistance": round(resistance, 1),
            "trigger": round(trigger, 1),
            "sl": round(sl, 1),
            "tp1": round(tp1, 1),
            "tp2": round(tp2, 1),
            "atr": round(atr, 1),
            "adx": round(adx, 1) if adx else None,
            "sl_distance": round(sl_distance, 1),
            "tp1_distance": round(tp1_distance, 1),
            "tp2_distance": round(tp2_distance, 1),
        }

# ═══════════════════════════════════════
# POZİSYON BOYUTU (%1 equity bazlı)
# ═══════════════════════════════════════

def calc_position(balance, sl_distance, price, tp1_distance=None, tp2_distance=None):
    """
    Risk = bakiye × %1
    Miktar = risk / SL mesafesi
    Hibrit: %50 market + %50 limit
    P67: TP profit ATR bazlı (tp1/tp2_distance parametre olarak alınır)
    """
    risk_dollar = balance * RISK_PCT
    max_risk = balance * MAX_RISK_PCT
    risk_dollar = min(risk_dollar, max_risk)
    
    if sl_distance <= 0:
        return None
    
    total_btc = risk_dollar / sl_distance
    total_usd = total_btc * price
    
    market_btc = total_btc * HYBRID_MARKET_PCT
    limit_btc = total_btc * HYBRID_LIMIT_PCT
    
    _tp1_d = tp1_distance if tp1_distance else sl_distance  # fallback
    _tp2_d = tp2_distance if tp2_distance else sl_distance * 2
    
    return {
        "balance": balance,
        "risk_pct": RISK_PCT * 100,
        "risk_dollar": round(risk_dollar, 2),
        "total_btc": round(total_btc, 4),
        "total_usd": round(total_usd, 0),
        "market_btc": round(market_btc, 4),
        "market_usd": round(market_btc * price, 0),
        "limit_btc": round(limit_btc, 4),
        "limit_usd": round(limit_btc * price, 0),
        "tp1_profit": round(_tp1_d * total_btc, 0),
        "tp2_profit": round(_tp2_d * total_btc, 0),
    }

# ═══════════════════════════════════════
# ANA FONKSİYON: SNAPSHOT
# ═══════════════════════════════════════

def snapshot(direction, balance=DEFAULT_BALANCE, adx_override=None):
    """
    Tam giriş planı: 1H onay + 15m seviyeler + pozisyon + hibrit emir.
    """
    print(f"\n{'='*55}")
    print(f"  ENTRY TRIGGER V2 — {direction}")
    print(f"  4H→1H→15m | Hibrit %50/%50 | %1 Risk")
    print(f"{'='*55}")
    
    # ─── ADIM 1: 1H ONAY (Elder 2. Ekran) ───
    print(f"\n  ── 1H ONAY (Elder 2. Ekran) ──")
    confirm = check_1h_confirmation(direction)
    
    if confirm["confirmed"] is None:
        print(f"  ⚠ {confirm['detail']}")
    elif confirm["confirmed"]:
        icon = "✅" if confirm["strength"] == "GÜÇLÜ" else "🟡"
        print(f"  {icon} 1H ONAY: {confirm['strength']}")
        print(f"    Fiyat ${confirm['price']:,.1f} {confirm['detail']}")
    else:
        print(f"  ❌ 1H RED: {direction} için 1H trend uyumsuz")
        print(f"    Fiyat ${confirm['price']:,.1f} {confirm['detail']}")
        print(f"  → HİBRİT AYAR: %50 market ATLA, sadece %25 limit dene")
        # 1H red durumunda pozisyonu küçült
    
    # ─── ADIM 2: 15m VERİ + ATR + ADX ───
    print(f"\n  ── 15m GİRİŞ (Elder 3. Ekran) ──")
    candles_15m = fetch_klines(interval="15m", limit=ATR_PERIOD + 15)
    if not candles_15m or len(candles_15m) < ATR_PERIOD + 1:
        print(f"  [HATA] 15m veri yetersiz ({len(candles_15m) if candles_15m else 0} mum)")
        return None
    
    price = candles_15m[-1]["close"]
    atr = calc_atr(candles_15m)
    
    # ADX: 4H klines'dan (rejim filtresi ile uyumlu)
    if adx_override is not None:
        adx = adx_override
    else:
        candles_4h = fetch_klines(interval="4h", limit=40)
        adx = calc_adx(candles_4h) if candles_4h and len(candles_4h) >= 29 else None
    
    if atr is None:
        print(f"  [HATA] ATR hesaplanamadı")
        return None
    
    levels = calc_entry_levels(candles_15m, direction, atr, adx, price)
    
    # ─── ÇIKTI ───
    print(f"\n  Anlık fiyat:    ${price:,.1f}")
    print(f"  15m ATR({ATR_PERIOD}):   ${atr:,.1f}")
    print(f"  4H ADX:         {adx:.1f}" if adx else "  4H ADX:         ?")
    print(f"  Rejim:          {levels['regime']} → SL çarpanı: {levels['sl_mult']}×")
    
    if direction == "LONG":
        dist = price - levels["trigger"]
        print(f"\n  ▼ Destek:       ${levels['support']:,.1f}")
    else:
        dist = levels["trigger"] - price
        print(f"\n  ▲ Direnç:       ${levels['resistance']:,.1f}")
    
    print(f"  → LİMİT GİRİŞ: ${levels['trigger']:,.1f}  (ATR×{PULLBACK_ZONE})")
    print(f"  ✗ STOP:         ${levels['sl']:,.1f}  (-${levels['sl_distance']:,.1f}, ATR×{levels['sl_mult']})")
    print(f"  ✓ TP1:          ${levels['tp1']:,.1f}  (+${levels['tp1_distance']:,.1f}, ATR×{TP1_ATR_MULT})")
    print(f"  ✓ TP2:          ${levels['tp2']:,.1f}  (+${levels['tp2_distance']:,.1f}, ATR×{TP2_ATR_MULT})")
    
    # BE (Break-Even) tetik fiyatı — P76 SHORT-ONLY (manuel uyarı)
    # Fiyat bu seviyeye ulaştığında Binance'te SL'yi entry'ye çek
    be_distance = atr * BE_TRIGGER_ATR
    if direction == "LONG":
        be_trigger_price = levels['trigger'] + be_distance
    else:  # SHORT
        be_trigger_price = levels['trigger'] - be_distance
    print(f"  ◎ BE TETİK:     ${be_trigger_price:,.1f}  (MFE=${be_distance:,.1f}, ATR×{BE_TRIGGER_ATR}) → SL'yi entry'ye çek")
    
    # R:R (P67: ATR bazlı — sabit oran)
    rr1 = levels['tp1_distance'] / levels['sl_distance'] if levels['sl_distance'] > 0 else 0
    rr2 = levels['tp2_distance'] / levels['sl_distance'] if levels['sl_distance'] > 0 else 0
    print(f"\n  R:R (TP1): 1:{rr1:.1f}  |  R:R (TP2): 1:{rr2:.1f}")
    
    if rr1 < RR_MIN:
        print(f"  ⚠ UYARI: R:R < {RR_MIN}:1 → GİRME")
        levels["decision"] = "GİRME_RR_KÖTÜ"
        print(f"\n{'='*55}")
        return levels
    
    # ─── ADIM 3: POZİSYON BOYUTU ───
    # 1H red → pozisyon yarıya düş
    effective_balance = balance
    if confirm.get("confirmed") == False:
        effective_balance = balance * 0.5
        print(f"\n  ⚠ 1H RED → pozisyon yarıya: ${effective_balance:,.0f} efektif bakiye")
    
    pos = calc_position(effective_balance, levels['sl_distance'], price,
                        tp1_distance=levels['tp1_distance'], tp2_distance=levels['tp2_distance'])
    if not pos:
        print(f"  [HATA] Pozisyon hesaplanamadı")
        return None
    
    print(f"\n  ── HİBRİT GİRİŞ (50/50) ──")
    print(f"  Bakiye:         ${balance:,.0f}")
    print(f"  Risk:           ${pos['risk_dollar']:,.1f} ({pos['risk_pct']:.0f}%)")
    print(f"  Toplam:         {pos['total_btc']:.4f} BTC (${pos['total_usd']:,.0f})")
    print(f"  ┌─ %50 MARKET:  {pos['market_btc']:.4f} BTC (${pos['market_usd']:,.0f}) → HEMEN")
    print(f"  └─ %50 LİMİT:  {pos['limit_btc']:.4f} BTC (${pos['limit_usd']:,.0f}) → ${levels['trigger']:,.1f}")
    print(f"\n  SL tetiklenirse: -${pos['risk_dollar']:,.1f}")
    print(f"  TP1 ulaşırsa:   +${pos['tp1_profit']:,.0f}")
    print(f"  TP2 ulaşırsa:   +${pos['tp2_profit']:,.0f}")
    
    # ─── ADIM 4: TIMEOUT KURALLARI ───
    cancel_price = price + atr * PRICE_CANCEL_ATR if direction == "SHORT" else price - atr * PRICE_CANCEL_ATR
    print(f"\n  ── TIMEOUT ──")
    print(f"  ⏰ Zaman:       {TIMEOUT_MINUTES}dk (8 × 15m mum)")
    print(f"  💲 Fiyat iptal: ${cancel_price:,.1f} (ATR×{PRICE_CANCEL_ATR} uzaklaşma)")
    print(f"  📊 Sinyal iptal: Yapı veya yön değişirse → hemen iptal")
    
    # ─── KARAR ───
    if abs(dist) < atr * 0.3:
        print(f"\n  ⚡ Fiyat trigger'a YAKIN — limit order şimdi koyulabilir")
        levels["decision"] = "LIMIT_HEMEN"
    else:
        print(f"\n  ⏳ Trigger mesafe: ${abs(dist):,.1f} — pullback bekle")
        levels["decision"] = "PULLBACK_BEKLE"
    
    # Sonuç dict'e ekle
    levels["confirm_1h"] = confirm
    levels["position"] = pos
    levels["cancel_price"] = round(cancel_price, 1)
    levels["timeout_min"] = TIMEOUT_MINUTES
    
    print(f"\n{'='*55}")
    return levels

# ═══════════════════════════════════════
# MONITOR MODU
# ═══════════════════════════════════════

def monitor(direction, balance=DEFAULT_BALANCE):
    """
    Aktif bekleme: 15m mumları izle, pullback + timeout + fiyat iptal.
    """
    print(f"\n[MONITOR] {direction} giriş bekleniyor (max {TIMEOUT_MINUTES}dk)...")
    
    # İlk snapshot
    levels = snapshot(direction, balance)
    if not levels or levels.get("decision") == "GİRME_RR_KÖTÜ":
        return {"status": "REJECTED"}
    
    trigger = levels["trigger"]
    cancel_price = levels["cancel_price"]
    start_time = time.time()
    
    while True:
        elapsed = (time.time() - start_time) / 60
        
        # Zaman timeout
        if elapsed > TIMEOUT_MINUTES:
            print(f"\n  [TIMEOUT] {TIMEOUT_MINUTES}dk doldu → LİMİT İPTAL")
            return {"status": "TIMEOUT", "elapsed": elapsed}
        
        price = fetch_current_price()
        if price is None:
            time.sleep(CHECK_INTERVAL)
            continue
        
        # Fiyat bazlı iptal
        if direction == "LONG" and price < cancel_price:
            print(f"\n  [FİYAT İPTAL] ${price:,.1f} < ${cancel_price:,.1f} → LİMİT İPTAL")
            return {"status": "PRICE_CANCEL", "price": price}
        if direction == "SHORT" and price > cancel_price:
            print(f"\n  [FİYAT İPTAL] ${price:,.1f} > ${cancel_price:,.1f} → LİMİT İPTAL")
            return {"status": "PRICE_CANCEL", "price": price}
        
        # Pullback tetik
        if direction == "LONG" and price <= trigger:
            print(f"\n  [TETİK] ${price:,.1f} ≤ ${trigger:,.1f} → LİMİT DOLDU!")
            return {"status": "TRIGGERED", "levels": levels, "entry_price": price}
        if direction == "SHORT" and price >= trigger:
            print(f"\n  [TETİK] ${price:,.1f} ≥ ${trigger:,.1f} → LİMİT DOLDU!")
            return {"status": "TRIGGERED", "levels": levels, "entry_price": price}
        
        # Durum raporu (her 2 dakikada)
        if int(elapsed) % 2 == 0 and int(elapsed) > 0:
            dist = abs(price - trigger)
            print(f"  [{int(elapsed):>3d}dk] ${price:,.1f} | trigger ${trigger:,.1f} | mesafe ${dist:,.0f} | iptal ${cancel_price:,.1f}")
        
        time.sleep(CHECK_INTERVAL)

# ═══════════════════════════════════════
# STANDALONE
# ═══════════════════════════════════════

if __name__ == "__main__":
    direction = "LONG"
    mode = "snapshot"
    balance = DEFAULT_BALANCE
    
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg.upper() in ("LONG", "SHORT"):
            direction = arg.upper()
        elif arg.lower() == "monitor":
            mode = "monitor"
        elif arg == "--balance" and i < len(sys.argv) - 1:
            try:
                balance = float(sys.argv[i + 1])
            except:
                pass
    
    if mode == "monitor":
        monitor(direction, balance)
    else:
        snapshot(direction, balance)
