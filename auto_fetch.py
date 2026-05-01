#!/usr/bin/env python3
"""
AUTO FETCH + RUN — Tam otomasyon. Binance + Coinglass API'den veri cek, scorecard calistir.
Pydroid3'te Play. Sifir manuel giris.

P58 DEĞİŞİKLİKLER:
  - fetch_oi: limit=5 → limit=30. api_open_interest zaman serisi (30 entry) JSON'a eklendi.
  - fetch_whale: limit=1 → limit=30. api_whale_account + api_whale_position JSON'a eklendi.
  - fetch_funding_history: YENİ. /fapi/v1/fundingRate limit=10 → api_funding_rate JSON'a eklendi.
  - ETKİ: OI_30h hesaplanabilir → SHORT_TRAP çalışır. VERİ_YETERSİZ kalkar.

KAYNAKLAR:
  Binance Public API (key gerektirmez):
    klines -> price, MA, volume, candles, CVD (futures)
    takerlongshortRatio -> taker buy/sell (TF-spesifik)
    openInterestHist -> OI + delta (TF-spesifik) + 30-entry zaman serisi
    premiumIndex -> funding rate (anlık)
    fundingRate -> funding rate history (son 10)
    topLongShortPositionRatio -> whale + net positions + 30-entry zaman serisi
  Coinglass API (free key):
    aggregated-liquidation-history -> long/short liquidations (K6_LIQ)
    spot-aggregated-cvd-history -> spot CVD (K4_CVD spot bileşeni)
"""

import urllib.request
import json
import time
import os
import sys
import glob
import subprocess
import shutil
from datetime import datetime, timezone

SYMBOL = "BTCUSDT"
BASE = "https://fapi.binance.com"

def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"    x {url.split('?')[0].split('/')[-1]}: {e}")
        return None

def calc_slope(series):
    """Lineer regresyon eğimi (basit). series = [eski, ..., yeni]"""
    n = len(series)
    if n < 2: return 0
    x_mean = (n - 1) / 2
    y_mean = sum(series) / n
    num = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(series))
    den = sum((i - x_mean) ** 2 for i in range(n))
    return num / den if den != 0 else 0

def fetch_klines(interval, limit=35):
    d = fetch(f"{BASE}/fapi/v1/klines?symbol={SYMBOL}&interval={interval}&limit={limit}")
    if not d or len(d) < limit:
        return None
    closes = [float(k[4]) for k in d]
    volumes = [float(k[7]) for k in d]
    taker_buys = [float(k[10]) for k in d]
    price = closes[-1]
    ma5 = round(sum(closes[-5:]) / 5, 2)
    ma10 = round(sum(closes[-10:]) / 10, 2)
    ma30 = round(sum(closes[-30:]) / 30, 2)
    vol = round(volumes[-1])
    vol_ma5 = round(sum(volumes[-5:]) / 5)
    vol_ma10 = round(sum(volumes[-10:]) / 10)
    cvd = round(2 * taker_buys[-1] - volumes[-1])
    curr = d[-1]; prev = d[-2]
    candle = {
        "curr": {"open": float(curr[1]), "high": float(curr[2]), "low": float(curr[3]), "close": float(curr[4])},
        "prev": {"open": float(prev[1]), "high": float(prev[2]), "low": float(prev[3]), "close": float(prev[4])},
    }
    last_closed = d[-2]
    dt = datetime.fromtimestamp(int(last_closed[0]) / 1000, tz=timezone.utc)
    regime_candle = [
        dt.strftime("%m-%d %H:%M"),
        float(last_closed[1]), float(last_closed[2]),
        float(last_closed[3]), float(last_closed[4]),
    ]
    # Global CANDLES tuples: tüm kapalı mumlar (son mum hariç — henüz kapanmamış)
    global_candle_tuples = []
    for k in d[:-1]:  # son mum açık, dahil etme
        kdt = datetime.fromtimestamp(int(k[0]) / 1000, tz=timezone.utc)
        global_candle_tuples.append([
            kdt.strftime("%m-%d %H:%M"),
            round(float(k[1]), 1), round(float(k[2]), 1),
            round(float(k[3]), 1), round(float(k[4]), 1),
        ])
    return {
        "price": price, "ma5": ma5, "ma10": ma10, "ma30": ma30,
        "vol": vol, "vol_ma5": vol_ma5, "vol_ma10": vol_ma10,
        "cvd": cvd, "candle": candle, "regime_candle": regime_candle,
        "global_candles": global_candle_tuples,
        # P52 TREND: klines'tan türetilen trend bilgileri
        "ma5_slope": round(calc_slope([sum(closes[i-5:i])/5 for i in range(max(5,len(closes)-5), len(closes))]), 4),
        "cvd_momentum": round(
            (sum(2*taker_buys[i]-volumes[i] for i in range(-5, 0)) /
             max(abs(sum(2*taker_buys[i]-volumes[i] for i in range(-10, -5))), 1) - 1), 4)
            if len(volumes) >= 10 else 0,
    }

def fetch_taker_ls(period, limit=5):
    d = fetch(f"{BASE}/futures/data/takerlongshortRatio?symbol={SYMBOL}&period={period}&limit={limit}")
    if not d: return None, [], 0, []
    series = [float(x["buySellRatio"]) for x in d]
    current = series[-1] if series else None
    slope = round(calc_slope(series), 6) if len(series) >= 2 else 0
    # P59: Raw time series (api_taker_ls formatı)
    raw_ts = []
    for x in d:
        ts = int(x["timestamp"]) // 1000
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        raw_ts.append([dt.strftime("%m-%d %H:%M"), round(float(x["buySellRatio"]), 4)])
    return current, series, slope, raw_ts

def fetch_oi(period, limit=30):
    d = fetch(f"{BASE}/futures/data/openInterestHist?symbol={SYMBOL}&period={period}&limit={limit}")
    if d and len(d) >= 2:
        series = [float(x["sumOpenInterest"]) for x in d]
        now = round(series[-1])
        prev = round(series[-2])
        delta = round(now - prev, 1)
        slope = round(calc_slope(series[-5:]), 2) if len(series) >= 3 else delta
        deltas = [series[i] - series[i-1] for i in range(max(1, len(series)-5), len(series))]
        accel = round(calc_slope(deltas), 2) if len(deltas) >= 2 else 0
        # Raw time series for HISTORICAL_DATA (scorecard format)
        raw_ts = []
        for x in d:
            ts = int(x["timestamp"]) // 1000 if "timestamp" in x else int(x.get("t", 0)) // 1000
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            raw_ts.append([dt.strftime("%m-%d %H:%M"), round(float(x["sumOpenInterest"]), 2)])
        return now, delta, series, slope, accel, raw_ts
    return 0, 0, [], 0, 0, []

def fetch_funding():
    d = fetch(f"{BASE}/fapi/v1/premiumIndex?symbol={SYMBOL}")
    return float(d["lastFundingRate"]) if d else None

def fetch_funding_history(limit=10):
    """Funding rate zaman serisi — scorecard api_funding_rate formatı."""
    d = fetch(f"{BASE}/fapi/v1/fundingRate?symbol={SYMBOL}&limit={limit}")
    if not d:
        return []
    raw_ts = []
    for x in d:
        ts = int(x["fundingTime"]) // 1000
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        rate = float(x["fundingRate"])
        mark = float(x.get("markPrice", 0))
        raw_ts.append([dt.strftime("%m-%d %H:%M"), rate, mark])
    return raw_ts

def fetch_whale(limit=30):
    """topLongShortPositionRatio — whale position ratio time series.
    P59 FIX: net_pos verisini de döndürür (aynı endpoint, duplikat çağrı önlenir).
    Returns: (current, acct_ts, pos_ts, net_pos_data)
      net_pos_data = (nl, ns, nl_series, ns_series, np_slope) — fetch_net_pos uyumlu
    """
    d = fetch(f"{BASE}/futures/data/topLongShortPositionRatio?symbol={SYMBOL}&period=1h&limit={limit}")
    if not d:
        return None, [], [], (0, 0, [], [], 0)
    current = float(d[-1]["longShortRatio"])
    # api_whale_account format: [['MM-DD HH:MM', longShortRatio], ...]
    acct_ts = []
    pos_ts = []
    for x in d:
        ts = int(x["timestamp"]) // 1000
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        label = dt.strftime("%m-%d %H:%M")
        acct_ts.append([label, round(float(x["longShortRatio"]), 4)])
        # longAccount/shortAccount → position ratio = longAccount/shortAccount
        la = float(x.get("longAccount", 0))
        sa = float(x.get("shortAccount", 0))
        pos_ratio = round(la / sa, 4) if sa > 0 else 0
        pos_ts.append([label, pos_ratio])
    # net_pos data (son 5 entry — fetch_net_pos uyumlu)
    last5 = d[-5:] if len(d) >= 5 else d
    nl_series = [float(x["longAccount"]) for x in last5]
    ns_series = [float(x["shortAccount"]) for x in last5]
    np_slope = round(calc_slope(nl_series), 6) if len(nl_series) >= 2 else 0
    net_pos_data = (round(nl_series[-1], 6), round(ns_series[-1], 6),
                    nl_series, ns_series, np_slope)
    return current, acct_ts, pos_ts, net_pos_data

def fetch_net_pos(period):
    """topLongShortPositionRatio -> net_long/net_short.
    P49 FIX: (LSR, -1.0) → (longAccount, shortAccount) her ikisi pozitif.
    P52: limit=5 → trend hesaplama.
    score_net_pos imbalance: (la-sa)/(la+sa) = (LSR-1)/(LSR+1)"""
    d = fetch(f"{BASE}/futures/data/topLongShortPositionRatio?symbol={SYMBOL}&period={period}&limit=5")
    if d:
        nl_series = [float(x["longAccount"]) for x in d]
        ns_series = [float(x["shortAccount"]) for x in d]
        # Trend: net_long eğimi
        np_slope = round(calc_slope(nl_series), 6) if len(nl_series) >= 2 else 0
        return (round(nl_series[-1], 6), round(ns_series[-1], 6),
                nl_series, ns_series, np_slope)
    return 0, 0, [], [], 0

def fetch_liquidations(window_min):
    """Likidasyon — Coinglass API (aggregated, tüm borsalar).
    Binance allForceOrders API key gerektiriyor, Coinglass alternatif.
    window_min: TF dakika cinsinden (15, 60, 240) → interval mapping.
    Returns: (long_liq_usd, short_liq_usd)

    P76 SKIP: Coinglass plan yetersiz (401 hatası) — endpoint atlandı.
    Eski loop: 4 TF × 2 URL × 15s timeout = 120s tasarruf.
    Tekrar aktifleştirmek için: aşağıdaki `return 0, 0` satırını sil."""
    return 0, 0  # P76 — CG 401, skip edildi
    CG_KEY = "aa0a378642f44e709ccb34ccbdea89b1"
    if not CG_KEY:
        return 0, 0
    
    # TF mapping
    if window_min <= 15: interval = "15m"
    elif window_min <= 60: interval = "1h"
    else: interval = "4h"
    
    # v3 ve v4 URL'leri dene
    urls = [
        f"https://open-api-v3.coinglass.com/api/futures/liquidation/aggregated-history?symbol=BTC&interval={interval}&limit=1",
        f"https://open-api-v4.coinglass.com/api/futures/liquidation/aggregated-history?symbol=BTC&interval={interval}&limit=1&exchange_list=Binance",
    ]
    
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0",
                "CG-API-KEY": CG_KEY,
                "accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = json.loads(resp.read())
            
            if str(raw.get("code")) != "0":
                print(f"    ⚠️ CG liq ({url.split('.com')[0].split('-')[-1]}): code={raw.get('code')} msg={raw.get('msg','?')}")
                continue
            
            data = raw.get("data", [])
            if not data:
                continue
            
            # Son periyodu al
            d = data[-1] if isinstance(data, list) else data
            
            # Field adları farklı olabilir — hepsini dene
            long_liq = 0
            short_liq = 0
            for lk in ["longVolUsd", "buyVolUsd", "longLiquidationUsd", "longUsd", "h1LongLiquidationUsd", "longLiquidation"]:
                if lk in d and d[lk]:
                    long_liq = float(d[lk])
                    break
            for sk in ["shortVolUsd", "sellVolUsd", "shortLiquidationUsd", "shortUsd", "h1ShortLiquidationUsd", "shortLiquidation"]:
                if sk in d and d[sk]:
                    short_liq = float(d[sk])
                    break
            
            if long_liq > 0 or short_liq > 0:
                return round(long_liq), round(short_liq)
            
            # Field bulunamadı — debug için raw yazdır
            print(f"    ⚠️ CG liq: veri geldi ama field bulunamadı. Keys: {list(d.keys()) if isinstance(d, dict) else type(d)}")
            print(f"    RAW (ilk 200 char): {str(d)[:200]}")
            return 0, 0
            
        except Exception as e:
            err = str(e)
            if "403" in err or "401" in err:
                print(f"    ⚠️ CG liq: auth hatası ({err[:60]}) — key geçersiz veya plan yetersiz")
            elif "404" in err:
                continue  # sonraki URL'yi dene
            else:
                print(f"    x CG liq: {err[:80]}")
            continue
    
    print(f"    ❌ CG liq: tüm URL'ler başarısız")
    return 0, 0


def fetch_depth():
    """P52: Order book depth imbalance — LEADING gösterge.
    bid_vol / ask_vol: >1 = alıcı baskın, <1 = satıcı baskın.
    Free API, key gerektirmez."""
    d = fetch(f"{BASE}/fapi/v1/depth?symbol={SYMBOL}&limit=20")
    if not d: return 1.0
    try:
        bid_vol = sum(float(b[1]) for b in d.get("bids", []))
        ask_vol = sum(float(a[1]) for a in d.get("asks", []))
        if ask_vol == 0: return 1.0
        return round(bid_vol / ask_vol, 4)
    except:
        return 1.0

def fetch_spot_cvd(interval="1h"):
    """Spot CVD — Coinglass API.
    score_cvd spot_cvd olarak kullanılır. Pozitif=alış baskısı, negatif=satış.
    Returns: float (CVD değeri) veya 0.

    P76 SKIP: Coinglass plan yetersiz (401 hatası) — endpoint atlandı.
    Eski loop: 4 TF × 4 URL × 15s timeout = 240s tasarruf.
    Tekrar aktifleştirmek için: aşağıdaki `return 0` satırını sil."""
    return 0  # P76 — CG 401, skip edildi
    CG_KEY = "aa0a378642f44e709ccb34ccbdea89b1"
    if not CG_KEY:
        return 0
    
    # Pair-specific (Binance BTCUSDT) ve aggregated dene
    urls = [
        f"https://open-api-v3.coinglass.com/api/spot/aggregated-cvd-history?symbol=BTC&interval={interval}&limit=1",
        f"https://open-api-v4.coinglass.com/api/spot/aggregated-cvd-history?symbol=BTC&interval={interval}&limit=1",
        f"https://open-api-v3.coinglass.com/api/spot/cvd-history?exchange=Binance&symbol=BTCUSDT&interval={interval}&limit=1",
        f"https://open-api-v4.coinglass.com/api/spot/cvd-history?exchange=Binance&symbol=BTCUSDT&interval={interval}&limit=1",
    ]
    
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0",
                "CG-API-KEY": CG_KEY,
                "accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = json.loads(resp.read())
            
            if str(raw.get("code")) != "0":
                continue
            
            data = raw.get("data", [])
            if not data:
                continue
            
            d = data[-1] if isinstance(data, list) else data
            
            # CVD field adları
            for ck in ["cvd", "CVD", "cumulativeDelta", "delta", "netDelta", "buyVol", "v"]:
                if ck in d and d[ck] is not None:
                    val = float(d[ck])
                    # buyVol ise delta hesapla (buyVol - sellVol)
                    if ck == "buyVol" and "sellVol" in d:
                        val = float(d["buyVol"]) - float(d["sellVol"])
                    return round(val)
            
            # Field bulunamadı — debug
            print(f"    ⚠️ CG spot_cvd: veri geldi ama field bulunamadı. Keys: {list(d.keys()) if isinstance(d, dict) else type(d)}")
            print(f"    RAW (ilk 200 char): {str(d)[:200]}")
            return 0
            
        except Exception as e:
            err = str(e)
            if "403" in err or "401" in err:
                print(f"    ⚠️ CG spot_cvd: auth hatası — plan yetersiz olabilir")
                return 0
            elif "404" in err:
                continue
            else:
                continue
    
    print(f"    ⚠️ CG spot_cvd: endpoint bulunamadı — 0 olarak devam")
    return 0

def main():
    print("=" * 55)
    print("  AUTO FETCH — Binance + Coinglass API")
    print("  " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    print("=" * 55)

    tf_config = [("5m", "5m", 5), ("15m", "15m", 15), ("1h", "1h", 60), ("4h", "4h", 240)]
    all_data = {}
    all_candles = {}
    all_global_candles = {}
    regime_candles = []
    oi_raw_by_tf = {}

    # Spot CVD (Coinglass) — TF-spesifik
    spot_cvds = {}
    for interval in ["5m", "15m", "1h", "4h"]:
        sc = fetch_spot_cvd(interval)
        spot_cvds[interval] = sc
    sc_ok = any(v != 0 for v in spot_cvds.values())
    if sc_ok:
        print(f"  ✅ spot_cvd (CG): 5m={spot_cvds.get('5m',0):+,} 15m={spot_cvds['15m']:+,} 1h={spot_cvds['1h']:+,} 4h={spot_cvds['4h']:+,}")
    else:
        print(f"  ⚠️ spot_cvd: Coinglass'tan çekilemedi — 0 olarak devam")

    # P52: Order book depth (LEADING)
    depth_imb = fetch_depth()
    print(f"  📊 depth_imbalance: {depth_imb:.4f} ({'ALICI' if depth_imb > 1.2 else 'SATICI' if depth_imb < 0.8 else 'DENGELI'})")

    # P59 FIX: 1h whale + LS 30-entry çağrılarını loop öncesine taşı
    # → topLongShortPositionRatio 1h ve takerlongshortRatio 1h duplikat çağrı önlenir
    print(f"\n  [PRE-FETCH] 1h whale + LS (30 entry)...")
    funding = fetch_funding()
    funding_history = fetch_funding_history(10)
    whale, whale_acct_ts, whale_pos_ts, whale_net_pos_1h = fetch_whale(30)
    _ls_1h_cur, _ls_1h_ser, _ls_1h_slope, ls_1h_ts = fetch_taker_ls("1h", limit=30)
    print(f"  funding={funding}")
    print(f"  whale={whale}")
    print(f"  api_whale_account: {len(whale_acct_ts)} entries")
    print(f"  api_taker_ls: {len(ls_1h_ts)} entries")

    for interval, period, liq_min in tf_config:
        print(f"\n  [{period}] Cekiliyor...")
        kl = fetch_klines(interval)

        # P59 FIX: 1h → pre-fetch'ten türet, 15m/4h → ayrı çağır
        if period == "1h":
            tls = _ls_1h_cur
            ls_series = _ls_1h_ser[-5:] if len(_ls_1h_ser) >= 5 else _ls_1h_ser
            ls_slope = round(calc_slope(ls_series), 6) if len(ls_series) >= 2 else 0
            nl, ns, nl_series, ns_series, np_slope = whale_net_pos_1h
        else:
            tls, ls_series, ls_slope, _ls_raw = fetch_taker_ls(period)
            nl, ns, nl_series, ns_series, np_slope = fetch_net_pos(period)

        oi, oi_d, oi_series, oi_slope, oi_accel, oi_raw_ts = fetch_oi(period)
        ll, sl = fetch_liquidations(liq_min)
        if not kl:
            print(f"  HATA [{period}] Klines basarisiz!")
            return
        all_data[period] = {
            "current_price": kl["price"],
            "ma5": kl["ma5"], "ma10": kl["ma10"], "ma30": kl["ma30"],
            "volume": kl["vol"], "volume_ma5": kl["vol_ma5"], "volume_ma10": kl["vol_ma10"],
            "net_long": nl, "net_short": ns,
            "futures_cvd": kl["cvd"], "spot_cvd": spot_cvds.get(period, 0),
            "taker_ls_ratio": tls if tls is not None else None,  # P59 FIX: None = API failure, 1.0 sessiz default TEHLİKELİ
            "oi": oi, "oi_delta": oi_d,
            "liquidations": {"long": ll, "short": sl},
            # P52 TREND FIELDS
            "ma5_slope": kl.get("ma5_slope", 0),
            "cvd_momentum": kl.get("cvd_momentum", 0),
            "ls_slope": ls_slope,
            "oi_slope": oi_slope,
            "oi_accel": oi_accel,
            "np_slope": np_slope,
            "depth_imbalance": depth_imb,
        }
        all_candles[period] = kl["candle"]
        all_global_candles[period] = kl["global_candles"]
        oi_raw_by_tf[period] = oi_raw_ts
        if period == "4h":
            # P61 FIX: Tüm kapalı 4h mumları regime'e ekle (sadece son mum değil)
            # run_updater dedup yapar, tekrar eklenmez
            for gc in kl["global_candles"]:
                regime_candles.append(gc)
        tag = "OK" if tls is not None else "⚠LS"
        if tls is None:
            print(f"  [⚠LS] [{period}] taker_ls_ratio API BAŞARISIZ — None olarak kaydedildi")
        print(f"  [{tag}] [{period}] ${kl['price']:,.1f} ls={tls if tls is not None else 'None'} oi={oi:,} cvd={kl['cvd']:+,}")
        if ls_slope != 0:
            print(f"         trend: ls_slope={ls_slope:+.6f} oi_slope={oi_slope:+.1f} np_slope={np_slope:+.6f}")

    print(f"\n  [GLOBAL]")
    print(f"  depth_imbalance={depth_imb}")
    print(f"  api_open_interest: {len(oi_raw_by_tf.get('1h', []))} entries")
    print(f"  api_funding_rate: {len(funding_history)} entries")

    # JSON
    output = {"data_5m": all_data["5m"], "data_15m": all_data["15m"], "data_1h": all_data["1h"], "data_4h": all_data["4h"],
              "candles": all_candles,
              "global_candles": all_global_candles}
    # Whale ve funding → data_1h'ye ekle (run_updater enjekte edecek)
    if whale is not None:
        output["data_1h"]["whale_acct_ls"] = whale
    if funding is not None:
        output["data_1h"]["funding_rate"] = funding
    if regime_candles:
        output["regime_candles"] = regime_candles

    # API zaman serileri — HISTORICAL_DATA formatı
    output["api_open_interest"] = oi_raw_by_tf.get("1h", [])
    output["api_whale_account"] = whale_acct_ts
    output["api_whale_position"] = whale_pos_ts
    output["api_funding_rate"] = funding_history
    output["api_taker_ls"] = ls_1h_ts  # P59: LS 1h 30-entry zaman serisi

    json_path = os.path.join(os.getcwd(), "r_update.json")
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2)

    # Ozet
    print(f"\n{'=' * 55}")
    ls5 = all_data["5m"]["taker_ls_ratio"]
    ls15 = all_data["15m"]["taker_ls_ratio"]
    ls1h = all_data["1h"]["taker_ls_ratio"]
    ls4h = all_data["4h"]["taker_ls_ratio"]
    all_ls = [("5m", ls5), ("15m", ls15), ("1h", ls1h), ("4h", ls4h)]
    missing_ls = [tf for tf, v in all_ls if v is None]
    if missing_ls:
        print(f"  ⚠ taker_ls VERİ EKSİK: {', '.join(missing_ls)}")
    else:
        same = abs(ls5-ls15)<0.002 and abs(ls15-ls1h)<0.002 and abs(ls1h-ls4h)<0.002
        if same:
            print(f"  !! taker_ls 4TF AYNI ({ls1h:.4f})")
        else:
            print(f"  OK taker_ls: 5m={ls5:.4f} 15m={ls15:.4f} 1h={ls1h:.4f} 4h={ls4h:.4f}")

    # run_updater + scorecard
    # Pydroid3 uyumlu path arama
    search_paths = [
        os.path.dirname(os.path.abspath(__file__)),
        os.getcwd(),
        "/storage/emulated/0/Download",
        "/storage/emulated/0/Downloads",
        "/storage/emulated/0/Documents",
        os.path.expanduser("~"),
    ]
    
    script_dir = None
    for p in search_paths:
        if not os.path.isdir(p):
            continue
        hits = glob.glob(os.path.join(p, "yon_*.py"))
        if hits:
            script_dir = p
            break
    
    # Alt klasörlerde de ara (Download/27/ gibi)
    if not script_dir:
        for p in search_paths:
            if not os.path.isdir(p):
                continue
            for sub in os.listdir(p):
                sp = os.path.join(p, sub)
                if os.path.isdir(sp) and glob.glob(os.path.join(sp, "yon_*.py")):
                    script_dir = sp
                    break
            if script_dir:
                break
    
    if not script_dir:
        print(f"\n  ❌ yon_*.py hicbir klasorde bulunamadi!")
        print(f"  Aranan: {', '.join(search_paths)}")
        return
    
    print(f"\n  📂 Klasor: {script_dir}")
    
    # JSON'u da oraya kaydet
    json_path2 = os.path.join(script_dir, "r_update.json")
    if os.path.abspath(json_path) != os.path.abspath(json_path2):
        shutil.copy2(json_path, json_path2)
    
    updater = os.path.join(script_dir, "run_updater.py")
    yon_files = sorted(
        glob.glob(os.path.join(script_dir, "yon_*.py")))
    yon_files = [f for f in yon_files if "auto" not in f and "updater" not in f and "fetch" not in f]

    if not yon_files:
        print(f"  yon dosyasi bulunamadi")
        return

    # P76: subprocess → import. PIPE deadlock ve timeout eksikliği elimine.
    # run_updater.update_file() direkt çağrılıyor.
    # yon_41 subprocess'i KALDIRILDI — auto_compact karar_motoru.run() ile zaten çağırıyor.
    if os.path.exists(updater):
        print(f"\n  Veri enjekte ediliyor (import)...")
        try:
            if script_dir not in sys.path:
                sys.path.insert(0, script_dir)
            import importlib
            import run_updater
            importlib.reload(run_updater)
            with open(json_path2, 'r', encoding='utf-8') as f:
                update_data = json.load(f)
            for yf in yon_files:
                if os.path.exists(yf):
                    run_updater.update_file(yf, update_data)
            print(f"  Enjeksiyon tamam.")
        except Exception as _ue:
            print(f"  ⚠ run_updater hatasi: {_ue}")

    print(f"\n{'=' * 55}")
    print(f"  FETCH BITTI")
    print(f"  whale_acct_ls = {whale}")
    print(f"  funding = {funding}")
    print(f"  OI_30h entries = {len(output.get('api_open_interest', []))}")
    print(f"  LS_1h entries = {len(output.get('api_taker_ls', []))}")
    print(f"{'=' * 55}")
    return  # P76: import'tan çağrıldığında temiz çıkış

if __name__ == "__main__":
    main()
