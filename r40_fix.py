#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R40 DUZELTME — eksik data_5m/15m/1h/4h alanlarini ekler.

PROBLEM:
  add_run.py R40'a data_X snapshot'larini eklemedi.
  yon_41'in compute_final_decision fonksiyonu HISTORICAL_DATA tarariyor 
  ve her run'in icinde rd["data_15m"] vs ariyor. R40'da yok -> KeyError.

COZUM:
  R40 acilis snapshot'i yoktu (manuel override'di). En yakin snapshot:
  - 15:58 dashboard'undan once: r_update.json tabanlandi (snapshot YOK)
  - R40 acilis (16:34) ile en yakin auto_compact: 15:58 (sistemin BEKLE dedi)
  - O snapshot artik yok (auto_compact uzerine yazdi)
  
  Pratik cozum: SU AN'KI r_update.json'dan oku (22:26 fetch).
  Bu R40 acilis snapshot'i degil, SONRAKI snapshot. Ama compute_final_decision'in
  patlamasini engeller. KAYIT'TA "snapshot_post_close" not eklenir.

YONTEM:
  1. R40'i bul
  2. data_5m, data_15m, data_1h, data_4h alanlarini ekle (mevcut r_update'ten)
  3. api_open_interest, api_taker_ls alanlarini ekle (cunku R39 var, format tutarli)
  4. Yeni dosya yaz, syntax dogrula
"""
import os, sys, json, re, shutil, subprocess

DOWNLOAD = "/storage/emulated/0/Download"
YON5 = os.path.join(DOWNLOAD, "yon_41.py")
RJ = os.path.join(DOWNLOAD, "r_update.json")

if not os.path.exists(YON5):
    print(f"HATA: {YON5} yok"); sys.exit(1)
if not os.path.exists(RJ):
    print(f"HATA: {RJ} yok"); sys.exit(1)

print("=" * 60)
print("  R40 DUZELTME — eksik data alanlari eklenecek")
print("=" * 60)

# 1) r_update'ten snapshot oku
print("\n[1] r_update.json'dan snapshot okunuyor...")
with open(RJ, "r", encoding="utf-8") as f:
    r = json.load(f)

snapshot = {}
for k in ["data_5m", "data_15m", "data_1h", "data_4h"]:
    if k in r:
        snapshot[k] = r[k]
        print(f"    ✓ {k}: current_price={r[k].get('current_price')}")
    else:
        print(f"    ❌ {k}: r_update.json'da YOK!")
        sys.exit(1)

# api_open_interest ve api_taker_ls (R39 formatindaki gibi 2-eleman list)
api_oi = r.get("api_open_interest", [])
api_ls = r.get("api_taker_ls", [])
if len(api_oi) >= 2:
    snapshot["api_open_interest"] = [api_oi[0], api_oi[-1]]  # ilk + son
    print(f"    ✓ api_open_interest: 2 entry (ilk + son)")
if len(api_ls) >= 2:
    snapshot["api_taker_ls"] = [api_ls[0], api_ls[-1]]
    print(f"    ✓ api_taker_ls: 2 entry")

snapshot["whale_acct_ls"] = float(r.get("data_1h", {}).get("whale_acct_ls", 0))

# 2) yon_41'i oku
print("\n[2] yon_41 dosyasi okunuyor...")
with open(YON5, "r", encoding="utf-8") as f:
    text = f.read()
print(f"    Boyut: {len(text):,} char")

# 3) R40 blok bul
print("\n[3] R40 bloku araniyor...")
m = re.search(r'"R40"\s*:\s*\{', text)
if not m:
    print("    HATA: R40 bulunamadi!")
    sys.exit(1)

# R40'in basi
r40_start = m.start()
# R40'in dict acilis {
brace_open = m.end() - 1
# Matching close brace bul
depth = 1
i = brace_open + 1
while i < len(text) and depth > 0:
    c = text[i]
    if c == "{": depth += 1
    elif c == "}":
        depth -= 1
        if depth == 0: break
    i += 1
r40_close = i  # } pozisyonu
print(f"    R40 bayt: {r40_start} → {r40_close}")
print(f"    R40 boyut: {r40_close - r40_start} char")

# R40 zaten data_15m iceriyor mu?
r40_text = text[r40_start:r40_close+1]
if '"data_15m"' in r40_text:
    print("    ⚠ R40 zaten data_15m iceriyor — duzeltme YAPILMIS.")
    print("    Tekrar calistirmaya gerek yok. Cikiyorum.")
    sys.exit(0)

# 4) Yedek al
print("\n[4] Yedek aliniyor...")
bak = YON5 + ".bak_r40fix"
shutil.copy2(YON5, bak)
print(f"    {bak}")

# 5) R40 icindeki ilk alana ekle (run_time'in oncesine)
# Format: dict acilisindan hemen sonra ekle
# Strateji: brace_open + 1'den sonra "\n" + yeni alanlar + ","
print("\n[5] Yeni alanlar ekleniyor...")
new_fields_lines = []
# R39 formatina sadik: data_5m bir satir, data_15m bir satir, vs.
for k in ["data_5m", "data_15m", "data_1h", "data_4h"]:
    v = snapshot[k]
    # JSON dump (Python dict literal, ASCII)
    v_str = json.dumps(v, ensure_ascii=True)
    new_fields_lines.append(f'        "{k}": {v_str}')

# api alanlarini da ekle (R39'da var)
if "api_open_interest" in snapshot:
    v_str = json.dumps(snapshot["api_open_interest"], ensure_ascii=True)
    new_fields_lines.append(f'        "api_open_interest": {v_str}')
if "api_taker_ls" in snapshot:
    v_str = json.dumps(snapshot["api_taker_ls"], ensure_ascii=True)
    new_fields_lines.append(f'        "api_taker_ls": {v_str}')
new_fields_lines.append(f'        "whale_acct_ls": {snapshot["whale_acct_ls"]}')

# Snapshot kaynak notu
new_fields_lines.append(f'        "_snapshot_source": "r_update.json @ post-close (R40 manuel override icin acilis snapshot mevcut degildi)"')

new_fields_str = ",\n".join(new_fields_lines)
insertion = "\n" + new_fields_str + ","

# R40 dict'in acilisindan ({) hemen sonra ekle
new_text = text[:brace_open + 1] + insertion + text[brace_open + 1:]

# 6) Yaz
print("\n[6] Dosya yaziliyor...")
with open(YON5, "w", encoding="utf-8") as f:
    f.write(new_text)
print(f"    Yeni boyut: {len(new_text):,} char (+{len(new_text) - len(text):,})")

# 7) Syntax kontrol
print("\n[7] Syntax kontrol...")
result = subprocess.run(
    [sys.executable, "-c", f"import py_compile; py_compile.compile({YON5!r}, doraise=True)"],
    capture_output=True, text=True
)
if result.returncode != 0:
    print("    HATA: Syntax bozuk! Yedekten geri yukleniyor...")
    print(result.stderr)
    shutil.copy2(bak, YON5)
    print("    Geri yuklendi.")
    sys.exit(1)
print("    OK syntax temiz.")

# 8) yon_41'i import edip R40'i kontrol
print("\n[8] R40 alanlari dogrulanlyor...")
verify = subprocess.run(
    [sys.executable, "-c", f"""
import sys, io
sys.path.insert(0, {os.path.dirname(YON5)!r})
_o=sys.stdout; sys.stdout=io.StringIO()
import yon_41 as y
sys.stdout=_o
r40 = y.HISTORICAL_DATA.get('R40', {{}})
print('R40 alanlari:', list(r40.keys()))
print('data_15m mevcut:', 'data_15m' in r40)
if 'data_15m' in r40:
    print('data_15m current_price:', r40['data_15m'].get('current_price'))
"""],
    capture_output=True, text=True
)
print(result.stdout if result.stdout else "")
print(verify.stdout)
if verify.returncode != 0:
    print("UYARI:", verify.stderr)

# 9) compute_final_decision testi
print("\n[9] compute_final_decision direkt test...")
verify2 = subprocess.run(
    [sys.executable, "-c", f"""
import sys, io, json
sys.path.insert(0, {os.path.dirname(YON5)!r})
_o=sys.stdout; sys.stdout=io.StringIO()
import yon_41 as y
with open({RJ!r}) as f: r = json.load(f)
sys.stdout=_o
try:
    sc = y.compute_scorecard(r['data_15m'], r['data_1h'], r['data_4h'])
    fd = y.compute_final_decision(sc, r['data_15m'], r['data_1h'], r['data_4h'])
    print('OK: fd.decision=', fd.get('decision'), 'fd.direction=', fd.get('direction'))
except Exception as e:
    print(f'HATA: {{type(e).__name__}}: {{e}}')
    import traceback; traceback.print_exc()
"""],
    capture_output=True, text=True
)
print(verify2.stdout)
if verify2.stderr:
    print("STDERR:", verify2.stderr)

print("\n" + "=" * 60)
print("  R40 DUZELTILDI ✓")
print(f"  Yedek: {bak}")
print("=" * 60)
print("\nSimdi auto_compact_fixed.py'yi tekrar calistir, dashboard temiz cikmali.")
