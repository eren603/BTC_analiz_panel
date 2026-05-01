#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADD_RUN v2 — yon_41.py'ye yeni run kaydi ekler.
                     +  r_update.json'dan otomatik snapshot pull
                     +  compute_final_decision testi (broken state yakalar)

P78 DEGISIKLIKLER (v1 -> v2):
  [+] r_update.json'dan data_5m/15m/1h/4h + api_open_interest +
      api_taker_ls + whale_acct_ls otomatik kopyalanir
  [+] RUN_DATA'da snapshot alani manuel verilmisse override edilmez
      (manuel > otomatik, atlanmasi loglanir)
  [+] _snapshot_source notu otomatik eklenir (kaynak + mtime)
  [+] Eklendikten sonra compute_final_decision cagrilir,
      KeyError patlamasi anlik yakalanir, yedekten geri alinir
  [+] r_update.json yoksa/bozuksa script DURDURULUR
      (snapshot'siz eklemek = R40 KeyError bug'ini tekrarlamak)

KULLANIM:
  Pydroid3'te calistir. Asagida RUN_DATA dict'ini doldur.
  Sadece manuel alanlari (run_time, entry_price, actual, move, ...) doldur.
  Snapshot alanlari (data_5m/15m/1h/4h vs) OTOMATIK eklenecek.

GUVENLIK ZINCIRI:
  1. yon_41'in yedegi alinir (.bak_addrun)
  2. r_update.json okunur, snapshot cikarilir (yoksa: DUR)
  3. RUN_DATA + snapshot merge (manuel oncelikli)
  4. Yon_5'e insert
  5. Syntax kontrol -> bozuksa yedekten geri al
  6. Import + run sayisi kontrol
  7. YENI: compute_final_decision cagri testi -> KeyError ise yedekten geri al
  8. OK -> _snapshot_source notu eklendi olarak rapor ver

ROLLBACK: Herhangi bir adimda hata varsa .bak_addrun'dan otomatik geri yuklenir.
"""
import os
import sys
import re
import shutil
import json
import subprocess
import time
from datetime import datetime

# ============================================================
#  RUN VERILERI — YENI RUN ICIN DOLDURUN, sonra calistirin
#  NOT: data_5m/15m/1h/4h snapshot'lari OTOMATIK eklenir.
#       Sadece manuel alanlari doldurmak yeterli.
# ============================================================
RUN_ID = "R41"

RUN_DATA = {
    # Zaman ve giris
    "run_time": "MM-DD HH:MM",         # Acilis zamani
    "entry_price": 0.0,                # Giris fiyati

    # Sonuc metrikleri (HISTORICAL_DATA standart)
    "actual": "DOWN",                  # "DOWN" / "UP" / "FLAT"
    "move": 0.0,                       # entry -> close fark (signed)
    "mfe_4h": 0.0,                     # max favorable excursion
    "mae_4h": 0.0,                     # max adverse excursion
    "close_price": 0.0,
    "close_time": "MM-DD HH:MM",

    # Override / yon
    "override": None,                  # "manuel_leading_only" vs ya da None
    "override_reason": "",
    "direction_taken": "SHORT",
    "leading_at_entry": "",            # ornek: "GIR SHORT (SHORT_TRAP)"
    "sc_at_entry": "",                 # ornek: "GIRME LONG (COK_KUCUK_BOYUT)"

    # Pozisyon
    "size_btc": 0.0,
    "notional_usd": 0.0,
    "atr_15m": 0.0,
    "sl_target": 0.0,
    "tp1_target": 0.0,
    "tp2_target": 0.0,
    "be_tetik_target": 0.0,

    # Kapanis
    "exit_reason": "",
    "be_triggered": False,
    "be_executed": False,
    "tp1_hit": False,
    "tp2_hit": False,
    "sl_hit": False,

    # PnL
    "gross_pnl_usd": 0.0,
    "result_r": 0.0,

    # Risk profili
    "balance_usd": 0,
    "actual_risk_pct": 0.0,
    "leverage_actual": 0.0,
    "risk_violation": False,
    "risk_violation_note": "",

    # Sistem snapshot (sinyal aninda)
    "system_long_w_at_signal": 0.0,
    "system_short_w_at_signal": 0.0,
    "system_margin_at_signal": 0.0,
    "leading_yon_at_signal": "",
    "leading_karar_at_signal": "",
    "sc_yon_at_signal": "",
    "sc_karar_at_signal": "",

    # OTOMATIK EKLENECEK (DOKUNMA, BOS BIRAK):
    # data_5m, data_15m, data_1h, data_4h,
    # api_open_interest, api_taker_ls, whale_acct_ls,
    # _snapshot_source
}

# Bayraklar
SKIP_FINAL_DECISION_TEST = False  # True yaparsan compute_final_decision testi atlanir
                                   # (debug icin; production'da daima False)
# ============================================================


# =====================================================================
#  YARDIMCI FONKSIYONLAR
# =====================================================================

def find_yon5_path():
    """yon_41.py dosyasini bul."""
    candidates = [
        "/storage/emulated/0/Download/yon_41.py",
        "/storage/emulated/0/Downloads/yon_41.py",
        os.path.join(os.getcwd(), "yon_41.py"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "yon_41.py"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def find_r_update_path():
    """r_update.json dosyasini bul."""
    candidates = [
        "/storage/emulated/0/Download/r_update.json",
        "/storage/emulated/0/Downloads/r_update.json",
        os.path.join(os.getcwd(), "r_update.json"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "r_update.json"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def extract_snapshot_from_r_update(rj_path):
    """
    r_update.json'dan HISTORICAL_DATA'ya eklenecek snapshot'i cikar.

    DONUS: dict (snapshot alanlari)
    HATA: ValueError (eksik/bozuk veri)

    Mantik r40_fix.py ile birebir aynidir (test edilmis pattern).
    """
    with open(rj_path, "r", encoding="utf-8") as f:
        r = json.load(f)

    snapshot = {}

    # 1) Timeframe data'lar (compute_final_decision'in en cok kullandigi)
    for k in ("data_5m", "data_15m", "data_1h", "data_4h"):
        if k not in r:
            raise ValueError(f"r_update.json'da '{k}' YOK. snapshot eksik kalir, durduruluyor.")
        snapshot[k] = r[k]

    # 2) api_open_interest ve api_taker_ls (R39 formatina sadik: ilk + son)
    api_oi = r.get("api_open_interest", [])
    if isinstance(api_oi, list) and len(api_oi) >= 2:
        snapshot["api_open_interest"] = [api_oi[0], api_oi[-1]]
    elif isinstance(api_oi, list) and len(api_oi) == 1:
        snapshot["api_open_interest"] = [api_oi[0], api_oi[0]]
    else:
        snapshot["api_open_interest"] = []

    api_ls = r.get("api_taker_ls", [])
    if isinstance(api_ls, list) and len(api_ls) >= 2:
        snapshot["api_taker_ls"] = [api_ls[0], api_ls[-1]]
    elif isinstance(api_ls, list) and len(api_ls) == 1:
        snapshot["api_taker_ls"] = [api_ls[0], api_ls[0]]
    else:
        snapshot["api_taker_ls"] = []

    # 3) whale_acct_ls (data_1h'tan tek deger)
    snapshot["whale_acct_ls"] = float(r.get("data_1h", {}).get("whale_acct_ls", 0))

    return snapshot


def merge_run_data_with_snapshot(run_data, snapshot, rj_path):
    """
    Manuel RUN_DATA + otomatik snapshot'i birlestirir.

    Kural:
      - RUN_DATA'da zaten varsa (manuel doldurulmus) -> manuel oncelikli, atla
      - RUN_DATA'da yoksa -> snapshot'tan ekle
      - _snapshot_source notu otomatik eklenir

    DONUS: (merged_dict, atlanan_alanlar_listesi)
    """
    merged = dict(run_data)  # kopya
    skipped = []

    for key, value in snapshot.items():
        if key in merged and merged[key] not in (None, "", 0, 0.0, [], {}):
            # Manuel verilmiş, atla
            skipped.append(key)
        else:
            merged[key] = value

    # Snapshot kaynak metadata'si (her zaman taze yazilir)
    rj_mtime = datetime.fromtimestamp(os.path.getmtime(rj_path)).strftime("%Y-%m-%d %H:%M:%S")
    merged["_snapshot_source"] = (
        f"r_update.json @ {rj_mtime} (otomatik, add_run v2)"
    )

    return merged, skipped


def python_repr(v):
    """Bir degeri Python literal string olarak repr eder.
    json.dumps DEGIL — Python literal istiyoruz (True, False, None).
    """
    if isinstance(v, str):
        # Tirnak kacisi ve newline
        return '"' + v.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'
    elif v is None:
        return "None"
    elif v is True:
        return "True"
    elif v is False:
        return "False"
    elif isinstance(v, (int, float)):
        return str(v)
    elif isinstance(v, dict):
        # Dict: JSON formatinda yazilabilir cunku Python dict literal'i de True/False/None disinda JSON ile uyumlu
        return json.dumps(v, ensure_ascii=True, separators=(", ", ": "))
    elif isinstance(v, list):
        return json.dumps(v, ensure_ascii=True, separators=(", ", ": "))
    else:
        return repr(v)


def build_run_block(run_id, merged_data):
    """Yeni run blok'unu Python dict literal stringi olarak hazirlar."""
    lines = [f'    "{run_id}": {{']
    items = list(merged_data.items())
    for idx, (k, v) in enumerate(items):
        comma = "," if idx < len(items) - 1 else ""
        v_repr = python_repr(v)
        lines.append(f'        "{k}": {v_repr}{comma}')
    lines.append("    }")
    return "\n".join(lines)


def find_historical_dict_close(text):
    """HISTORICAL_DATA dict'inin kapanis } pozisyonunu bul.
    DONUS: int (close brace pos) veya None (bulunamadi)
    """
    m = re.search(r"HISTORICAL_DATA\s*=\s*\{", text)
    if not m:
        return None
    depth = 1
    i = m.end()
    while i < len(text) and depth > 0:
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return None


def rollback(yon5_path, bak_path, reason):
    """Yedekten geri yukle ve bilgi ver."""
    print(f"\n  ⚠ ROLLBACK: {reason}")
    print(f"  Yedekten geri yukleniyor: {bak_path}")
    shutil.copy2(bak_path, yon5_path)
    print(f"  Geri yuklendi: {yon5_path}")
    print(f"  ORIGINAL state korundu, sistem etkilenmedi.")


# =====================================================================
#  ANA AKIS
# =====================================================================

def main():
    print("=" * 64)
    print(f"  ADD_RUN v2 — {RUN_ID} ekleniyor (snapshot otomatigi aktif)")
    print("=" * 64)

    # ------ 0) RUN_DATA placeholder validation (Eren doldurmayi unutursa erkenden yakala) ------
    placeholders = []
    if "MM-DD" in str(RUN_DATA.get("run_time", "")):
        placeholders.append("run_time (hala 'MM-DD HH:MM' placeholder)")
    if "MM-DD" in str(RUN_DATA.get("close_time", "")):
        placeholders.append("close_time (hala 'MM-DD HH:MM' placeholder)")
    if RUN_DATA.get("entry_price", 0) == 0.0:
        placeholders.append("entry_price (hala 0.0)")
    if RUN_DATA.get("close_price", 0) == 0.0:
        placeholders.append("close_price (hala 0.0)")
    if placeholders:
        print("  ❌ HATA: RUN_DATA dict'inde doldurulmamis alanlar var:")
        for p in placeholders:
            print(f"     - {p}")
        print("  Once add_run.py'nin ustundeki RUN_DATA bolumunu doldur, sonra calistir.")
        sys.exit(1)

    # ------ 1) Yon_5 dosyasini bul ------
    fp = find_yon5_path()
    if fp is None:
        print("  ❌ HATA: yon_41.py bulunamadi!")
        print("  Aranan: /storage/emulated/0/Download/, mevcut dizin")
        sys.exit(1)
    print(f"  yon_41: {fp}")
    size_before = os.path.getsize(fp)
    print(f"  Boyut (once): {size_before:,} byte")

    # ------ 2) r_update.json bul ve snapshot cikar ------
    rj = find_r_update_path()
    if rj is None:
        print("  ❌ HATA: r_update.json bulunamadi!")
        print("  add_run v2 snapshot pull yapamadan run ekleyemez (R40 KeyError bug riski).")
        print("  Once auto_fetch.py calistirip r_update.json olustur, sonra tekrar dene.")
        sys.exit(1)
    print(f"  r_update.json: {rj}")
    rj_mtime_ts = os.path.getmtime(rj)
    rj_age_min = (time.time() - rj_mtime_ts) / 60.0
    rj_mtime_str = datetime.fromtimestamp(rj_mtime_ts).strftime("%Y-%m-%d %H:%M:%S")
    print(f"  r_update.json mtime: {rj_mtime_str} ({rj_age_min:.1f} dk eski)")
    if rj_age_min > 30:
        print(f"  ⚠ UYARI: r_update.json {rj_age_min:.0f} dakika eski. Snapshot taze degil.")
        print("    Devam ediliyor ama _snapshot_source notu bunu yansitacak.")

    print("\n  [snapshot pull] r_update.json'dan alanlar cikariliyor...")
    try:
        snapshot = extract_snapshot_from_r_update(rj)
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        print(f"  ❌ HATA: snapshot cikarilirken hata: {type(e).__name__}: {e}")
        print("  r_update.json formati bozuk veya eksik. Ekleme YAPILMADI.")
        sys.exit(1)
    for k in ["data_5m", "data_15m", "data_1h", "data_4h"]:
        cp = snapshot[k].get("current_price", "?")
        print(f"    ✓ {k}: current_price={cp}")
    print(f"    ✓ api_open_interest: {len(snapshot['api_open_interest'])} entry")
    print(f"    ✓ api_taker_ls: {len(snapshot['api_taker_ls'])} entry")
    print(f"    ✓ whale_acct_ls: {snapshot['whale_acct_ls']}")

    # ------ 3) RUN_DATA + snapshot merge ------
    print("\n  [merge] manuel RUN_DATA + otomatik snapshot...")
    merged, skipped = merge_run_data_with_snapshot(RUN_DATA, snapshot, rj)
    if skipped:
        print(f"    ⓘ Manuel doldurulmus, atlanan otomatik alanlar: {skipped}")
    print(f"    Final alan sayisi: {len(merged)}")

    # ------ 4) Yedek al ------
    bak = fp + ".bak_addrun"
    shutil.copy2(fp, bak)
    print(f"\n  Yedek: {bak}")

    # ------ 5) Dosyayi oku, HISTORICAL_DATA bul ------
    with open(fp, "r", encoding="utf-8") as f:
        text = f.read()
    closing_brace_pos = find_historical_dict_close(text)
    if closing_brace_pos is None:
        print("  ❌ HATA: HISTORICAL_DATA dict bulunamadi/kapanmadi!")
        sys.exit(1)

    # ------ 6) Run zaten var mi kontrol ------
    dict_content = text[:closing_brace_pos]
    if f'"{RUN_ID}":' in dict_content or f"'{RUN_ID}':" in dict_content:
        print(f"  ❌ HATA: {RUN_ID} HISTORICAL_DATA'da zaten var!")
        print("  Bilincli ust uste yazmak icin once elle sil, sonra calistir.")
        sys.exit(1)

    # ------ 7) Yeni run blogunu hazirla ve insert ------
    new_run_str = build_run_block(RUN_ID, merged)
    insertion = "\n" + new_run_str + ",\n"
    new_text = text[:closing_brace_pos] + insertion + text[closing_brace_pos:]

    with open(fp, "w", encoding="utf-8") as f:
        f.write(new_text)
    size_after = os.path.getsize(fp)
    print(f"  Boyut (sonra): {size_after:,} byte (+{size_after - size_before:,})")

    # ------ 8) Syntax dogrula ------
    print("\n  [test 1/3] Syntax kontrol...")
    result = subprocess.run(
        [sys.executable, "-c",
         f"import py_compile; py_compile.compile({fp!r}, doraise=True)"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  ❌ Syntax hatasi:\n{result.stderr}")
        rollback(fp, bak, "syntax bozuldu")
        sys.exit(1)
    print("    ✓ Syntax temiz")

    # ------ 9) Import + run sayisi dogrula ------
    print("  [test 2/3] Import + run sayisi...")
    verify_code = f"""
import sys, io
sys.path.insert(0, {os.path.dirname(fp)!r})
_o=sys.stdout; sys.stdout=io.StringIO()
import importlib.util
spec=importlib.util.spec_from_file_location('y_test', {fp!r})
y=importlib.util.module_from_spec(spec)
spec.loader.exec_module(y)
sys.stdout=_o
import json as _j
print(_j.dumps({{
    'total': len(y.HISTORICAL_DATA),
    'last_3': sorted(y.HISTORICAL_DATA.keys(), key=lambda x: int(x[1:]))[-3:],
    'new_run_actual': y.HISTORICAL_DATA.get({RUN_ID!r}, {{}}).get('actual'),
    'new_run_entry': y.HISTORICAL_DATA.get({RUN_ID!r}, {{}}).get('entry_price'),
    'new_run_has_data_15m': 'data_15m' in y.HISTORICAL_DATA.get({RUN_ID!r}, {{}}),
}}))
"""
    result2 = subprocess.run(
        [sys.executable, "-c", verify_code],
        capture_output=True, text=True
    )
    if result2.returncode != 0:
        print(f"  ❌ Import hatasi:\n{result2.stderr}")
        rollback(fp, bak, "yon_41 import edilemedi")
        sys.exit(1)
    try:
        info = json.loads(result2.stdout.strip())
    except json.JSONDecodeError:
        print(f"  ❌ Import dogrulamasi parse edilemedi:\n{result2.stdout}")
        rollback(fp, bak, "import dogrulamasi anlasilamadi")
        sys.exit(1)
    print(f"    ✓ Toplam run: {info['total']}")
    print(f"    ✓ Son 3 run: {info['last_3']}")
    print(f"    ✓ {RUN_ID} actual={info['new_run_actual']}, entry={info['new_run_entry']}")
    print(f"    ✓ {RUN_ID} data_15m mevcut: {info['new_run_has_data_15m']}")
    if not info['new_run_has_data_15m']:
        print("  ❌ KRITIK: data_15m eklenmedi! Snapshot pull basarisiz.")
        rollback(fp, bak, "snapshot eklenmemis (data_15m yok)")
        sys.exit(1)

    # ------ 10) compute_final_decision testi (KRITIK — R40 bug yakalar) ------
    if SKIP_FINAL_DECISION_TEST:
        print("  [test 3/3] compute_final_decision testi ATLANDI (bayrak)")
    else:
        print("  [test 3/3] compute_final_decision direkt cagri (broken state yakalar)...")
        cfd_test = f"""
import sys, io, json
sys.path.insert(0, {os.path.dirname(fp)!r})
_o=sys.stdout; sys.stdout=io.StringIO()
import importlib.util
spec=importlib.util.spec_from_file_location('y_cfd', {fp!r})
y=importlib.util.module_from_spec(spec)
spec.loader.exec_module(y)
with open({rj!r}) as f: r = json.load(f)
sys.stdout=_o
try:
    sc = y.compute_scorecard(r['data_15m'], r['data_1h'], r['data_4h'])
    fd = y.compute_final_decision(sc, r['data_15m'], r['data_1h'], r['data_4h'])
    print(json.dumps({{'ok': True, 'decision': fd.get('decision'), 'direction': fd.get('direction')}}))
except Exception as e:
    import traceback
    print(json.dumps({{'ok': False, 'err_type': type(e).__name__, 'err_msg': str(e), 'tb': traceback.format_exc()}}))
"""
        result3 = subprocess.run(
            [sys.executable, "-c", cfd_test],
            capture_output=True, text=True
        )
        try:
            cfd_info = json.loads(result3.stdout.strip())
        except json.JSONDecodeError:
            print(f"  ❌ compute_final_decision testi parse edilemedi:")
            print(f"  STDOUT: {result3.stdout}")
            print(f"  STDERR: {result3.stderr}")
            rollback(fp, bak, "compute_final_decision testi anlasilamadi")
            sys.exit(1)
        if not cfd_info.get('ok'):
            print(f"  ❌ compute_final_decision PATLADI:")
            print(f"     {cfd_info.get('err_type')}: {cfd_info.get('err_msg')}")
            print(f"  Bu cogunlukla yeni run'in snapshot'i eksik/bozuk demek.")
            rollback(fp, bak, "compute_final_decision broken state")
            sys.exit(1)
        print(f"    ✓ compute_final_decision OK: decision={cfd_info.get('decision')}, direction={cfd_info.get('direction')}")

    # ------ 11) BASARI ------
    print()
    print("=" * 64)
    print(f"  {RUN_ID} EKLENDI ✓  (3/3 test gecti)")
    print("=" * 64)
    print(f"  Yedek: {bak}")
    print(f"  Snapshot kaynak: {merged['_snapshot_source']}")
    if skipped:
        print(f"  Manuel atlanan otomatik alanlar: {skipped}")
    print(f"  Geri almak icin: cp {bak} {fp}")
    print()


if __name__ == "__main__":
    main()
