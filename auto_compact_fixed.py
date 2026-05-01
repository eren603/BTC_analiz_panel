#!/usr/bin/env python3
"""
AUTO COMPACT — Veri çek + scorecard çalıştır + sadece ÖZET göster.
Pydroid3'te Play. 1-2 ekran çıktı, 10+ ekran yerine.

P62 DEĞİŞİKLİKLER:
  - ENTRY TRIGGER V2: 4H→1H→15m üçlü zaman dilimi giriş sistemi.
    1H trend onayı + 15m ATR bazlı giriş seviyeleri + ADX adaptif SL.
    Hibrit giriş: %50 market + %50 limit pullback.
    Pozisyon: bakiye × %1 (sabit $ değil).
    entry_trigger_v2.py aynı klasörde olmalı.

KULLANIM:
  python3 auto_compact.py          → fetch + scorecard + özet
  python3 auto_compact.py --skip   → fetch atla, mevcut verilerle scorecard

AKIŞ:
  auto_fetch.py zaten şu sırayla çalışır:
    1. Binance + Coinglass API'den veri çek → r_update.json
    2. run_updater ile yon_41'e enjekte et
    3. yon_41 scorecard çalıştır
  Bu script auto_fetch'in TÜM çıktısını yakalar,
  sonra sadece özet satırları filtreler.

VERİ KONTROLÜ — auto_fetch şunları çeker:
  Binance (key gereksiz):
    - klines 5m/15m/1h/4h → price, MA5/10/30, volume, CVD, candles
    - takerlongshortRatio → LS ratio (TF-spesifik) + 30-entry 1h zaman serisi
    - openInterestHist → OI + delta + 30-entry zaman serisi
    - topLongShortPositionRatio → whale + net positions + 30-entry zaman serisi
    - premiumIndex → funding rate (anlık)
    - fundingRate → funding history (10 entry)
    - depth → order book imbalance
  Coinglass (CG_KEY):
    - aggregated-liquidation-history → long/short liq (K6_LIQ)
    - spot-aggregated-cvd-history → spot CVD (K4_CVD)
  run_updater enjekte eder:
    - data_5m, data_15m, data_1h, data_4h (dict'ler)
    - candles_data (curr/prev her TF)
    - api_open_interest_live, api_whale_account_live, api_whale_position_live
    - api_funding_rate_live, api_taker_ls_live (list'ler)
    - CANDLES_4H/1H/15M (global candle append)
    - CANDLES_4H_REGIME (yon_41 regime filtresi için)

ÇIKTI (~20 satır, 1-2 ekran):
  - Ham veriler (whale, LS, OI, funding, %MA30)
  - Her scorecard için ÖZET DASHBOARD bloğu
  - Ölçüm karşılaştırması
  - Veri uyarıları (varsa)

GEREKLI DOSYALAR (aynı klasörde):
  auto_fetch.py, run_updater.py, yon_*.py
"""

import subprocess
import os
import sys
import glob
import json
import re
from datetime import datetime, timezone


def find_script_dir():
    """yon_*.py bulunan klasörü bul."""
    search_paths = [
        os.path.dirname(os.path.abspath(__file__)),
        os.getcwd(),
        "/storage/emulated/0/Download",
        "/storage/emulated/0/Downloads",
        "/storage/emulated/0/Documents",
        os.path.expanduser("~"),
    ]
    for p in search_paths:
        if not os.path.isdir(p):
            continue
        if glob.glob(os.path.join(p, "yon_*.py")):
            return p
        try:
            for sub in os.listdir(p):
                sp = os.path.join(p, sub)
                if os.path.isdir(sp) and glob.glob(os.path.join(sp, "yon_*.py")):
                    return sp
        except:
            continue
    return None


def extract_summary(full_output):
    """auto_fetch çıktısından (scorecard dahil) özet satırları çıkar."""
    lines = full_output.split("\n")
    result = []
    
    # ─── VERİ UYARILARI ───
    for line in lines:
        s = line.strip()
        if "4TF AYNI" in s:
            result.append(f"  ⚠ {s}")
        elif "VERİ EKSİK" in s:
            result.append(f"  ⚠ {s}")
        elif "API BAŞARISIZ" in s:
            result.append(f"  ⚠ {s}")
    
    # ─── HER SCORECARD İÇİN ÖZET DASHBOARD ───
    # Yapı: █ → ÖZET DASHBOARD → █(separator) → içerik → █(bitiş)
    in_dashboard = False
    skip_next_bar = False
    current_file = None
    
    for line in lines:
        s = line.strip()
        
        # Dosya adı tespiti
        if (s.startswith("yon_")) and s.endswith(".py"):
            current_file = s
            continue
        
        # Dashboard başlangıcı
        if "ÖZET DASHBOARD" in s:
            if current_file:
                result.append(f"")
                result.append(f"{'─'*50}")
                result.append(f"  {current_file}")
                result.append(f"{'─'*50}")
                current_file = None
            in_dashboard = True
            skip_next_bar = True  # ÖZET'ten sonraki █ separator, atla
            result.append(f"  {s}")
            continue
        
        # Dashboard içeriği
        if in_dashboard:
            if s.startswith("█"):
                if skip_next_bar:
                    skip_next_bar = False  # separator atlandı, devam
                    continue
                else:
                    in_dashboard = False  # bitiş █
                    continue
            if s:
                result.append(f"  {s}")
        
        # Ölçüm karşılaştırması satırları (her scorecard sonunda)
        if s.startswith("YON (") or s.startswith("YENI ("):
            result.append(f"  {s}")
        
        # Leading detay satırı (Whale: X | OI_30h: Y | LS_1h: Z)
        if s.startswith("Whale:") and "OI_30h:" in s and "LS_1h:" in s:
            result.append(f"  {s}")
    
    # ─── BİTTİ BLOĞU (whale, funding, OI/LS entries) ───
    in_bitti = False
    for line in lines:
        s = line.strip()
        if s == "BITTI":
            in_bitti = True
            continue
        if in_bitti:
            if s.startswith("whale_acct_ls") or s.startswith("funding") or \
               s.startswith("OI_30h") or s.startswith("LS_1h"):
                result.append(f"  {s}")
            if s.startswith("===") or not s:
                in_bitti = False
    
    return result


def get_monitor_line(script_dir):
    """r_update.json'dan temel veri satırı üret."""
    json_path = os.path.join(script_dir, "r_update.json")
    if not os.path.exists(json_path):
        return []
    
    with open(json_path, "r") as f:
        data = json.load(f)
    
    d1h = data.get("data_1h", {})
    d4h = data.get("data_4h", {})
    whale = d1h.get("whale_acct_ls")
    ls_1h = d1h.get("taker_ls_ratio")
    funding = d1h.get("funding_rate")
    price = d1h.get("current_price", 0)
    
    # OI_30h
    oi_ts = data.get("api_open_interest", [])
    oi_30h = (oi_ts[-1][1] - oi_ts[0][1]) if len(oi_ts) >= 2 else None
    
    # 4h%MA30
    _4h_p = d4h.get("current_price", 0)
    _4h_ma30 = d4h.get("ma30", 0)
    pct = ((_4h_p - _4h_ma30) / _4h_ma30 * 100) if _4h_p > 0 and _4h_ma30 > 0 else None
    
    lines = []
    parts = []
    if whale is not None: parts.append(f"W:{whale:.4f}")
    else: parts.append("W:?")
    if ls_1h is not None: parts.append(f"LS:{ls_1h:.4f}")
    else: parts.append("LS:?")
    if oi_30h is not None: parts.append(f"OI:{oi_30h:+,.0f}")
    else: parts.append("OI:?")
    if funding: parts.append(f"F:{funding*3*365*100:+.1f}%APR")
    if pct is not None:
        dep = " ⛔DEP" if pct > 4.0 else " ⚠YAKIN" if pct > 3.5 else ""
        parts.append(f"%MA30:{pct:+.2f}%{dep}")
    
    lines.append(f"  ${price:,.0f} | {' | '.join(parts)}")
    return lines


def main():
    skip_fetch = "--skip" in sys.argv
    
    script_dir = find_script_dir()
    if not script_dir:
        print("❌ yon_*.py bulunamadı!")
        return
    
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"{'='*55}")
    print(f"  COMPACT — {ts}")
    print(f"{'='*55}")
    
    full_output = ""
    
    if not skip_fetch:
        # P76: subprocess → import. PIPE deadlock elimine.
        # auto_fetch.main() import edilip çağrılıyor, stdout StringIO ile yakalanıyor.
        fetch_path = os.path.join(script_dir, "auto_fetch.py")
        if not os.path.exists(fetch_path):
            print("  ❌ auto_fetch.py bulunamadı")
            return
        
        print("  Çalışıyor...", flush=True)
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        try:
            import io
            import importlib
            import auto_fetch
            importlib.reload(auto_fetch)
            # stdout'u yakala (extract_summary için gerekli) + konsola da ayna
            buf = io.StringIO()
            _orig_stdout = sys.stdout
            class _Tee:
                def __init__(self, *streams): self.streams = streams
                def write(self, data):
                    for s in self.streams:
                        try: s.write(data)
                        except: pass
                def flush(self):
                    for s in self.streams:
                        try: s.flush()
                        except: pass
            sys.stdout = _Tee(_orig_stdout, buf)
            try:
                auto_fetch.main()
            finally:
                sys.stdout = _orig_stdout
            full_output = buf.getvalue()
            print("  ✅ fetch tamam")
        except Exception as _fe:
            print(f"  ❌ auto_fetch hatası: {_fe}")
            import traceback
            traceback.print_exc()
            return
    else:
        # --skip: mevcut verilerle scorecard çalıştır
        print("  --skip: fetch atlandı", end="", flush=True)
        
        updater = os.path.join(script_dir, "run_updater.py")
        json_path = os.path.join(script_dir, "r_update.json")
        yon_files = sorted(
            
            glob.glob(os.path.join(script_dir, "yon_*.py")))
        yon_files = [f for f in yon_files
                     if "auto" not in f and "updater" not in f 
                     and "fetch" not in f and "compact" not in f
                     and "monitor" not in f]
        
        # run_updater
        if os.path.exists(updater) and os.path.exists(json_path) and yon_files:
            subprocess.run(
                ["python3", updater, json_path] + yon_files,
                cwd=script_dir, capture_output=True, text=True, timeout=120
            )
        
        # Scorecards
        for yf in yon_files:
            try:
                r = subprocess.run(
                    ["python3", yf], cwd=script_dir,
                    capture_output=True, text=True, timeout=120
                )
                full_output += f"\n{os.path.basename(yf)}\n{r.stdout}"
            except:
                full_output += f"\n{os.path.basename(yf)}\n  ❌ Timeout\n"
        print(" ✅")
    
    # ─── HAM VERİLER (JSON'dan) ───
    monitor = get_monitor_line(script_dir)
    for ml in monitor:
        print(ml)
    
    # ─── ÖZET (scorecard çıktısından) ───
    summary = extract_summary(full_output)
    for line in summary:
        print(line)
    
    # ─── KARAR MOTORU (DDF entegre) ───
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    try:
        import importlib
        import karar_motoru
        importlib.reload(karar_motoru)
        karar_motoru.run()
    except ImportError as _ke:
        print(f"\n  ⚠ karar_motoru.py bulunamadi: {_ke}")
    except Exception as _km_exc:
        print(f"\n  ⚠ karar_motoru hatasi: {_km_exc}")
    
    print(f"\n{'='*55}")


if __name__ == "__main__":
    main()
