#!/usr/bin/env python3
"""
RUN UPDATER — Regex-based data injection for yon_41.py
Pydroid3 uyumlu: sıfır dış bağımlılık, sadece stdlib.

KULLANIM:
  1) r_update.json dosyasını oluştur (format aşağıda)
  2) Bu scripti çalıştır:
       python3 run_updater.py r_update.json yon_41.py
     (veya parametresiz: glob ile yon_*.py otomatik bulunur)
  3) Güncellenen dosya(lar) aynı yere yazılır (_bak yedek alınır)

JSON FORMAT:
{
  "data_15m": {"current_price": ..., "ma5": ..., ...},
  "data_1h":  {"current_price": ..., ...},
  "data_4h":  {"current_price": ..., ...},
  "candles": {
    "15m": {"curr": {"open":..,"high":..,"low":..,"close":..},
            "prev": {"open":..,"high":..,"low":..,"close":..}},
    "1h":  {"curr": {...}, "prev": {...}},
    "4h":  {"curr": {...}, "prev": {...}}
  },
  "regime_candles": [
    ["04-07 03:00", 70000.0, 70500.0, 69800.0, 70200.0]
  ]
}

NOT:
  - data_15m/1h/4h: Tüm alan adları mevcut dosyadakiyle aynı olmalı.
  - candles: candles_data bloğunun tamamını değiştirir.
  - regime_candles: (opsiyonel, sadece yon_41) CANDLES_4H_REGIME sonuna eklenir.
  - Herhangi bir key JSON'da yoksa → o blok DEĞİŞMEZ.
"""

import json
import re
import sys
import os
import shutil
import glob


def find_work_dir():
    """yon_*.py dosyasını bularak çalışma klasörünü otomatik tespit et."""
    search_paths = [
        os.path.dirname(os.path.abspath(__file__)),          # script'in kendi klasörü
        "/storage/emulated/0",                                # ana depolama
        "/storage/emulated/0/Download",                       # indirilenler
        "/storage/emulated/0/Downloads",                      # indirilenler (alternatif)
        "/storage/emulated/0/Documents",                      # belgeler
        "/data/user/0/ru.iiec.pydroid3/files",               # pydroid3 dahili
        os.path.expanduser("~"),                              # home
    ]
    for p in search_paths:
        if not os.path.isdir(p):
            continue
        hits = glob.glob(os.path.join(p, "yon_*.py"))
        if hits:
            return p
    return None


def replace_or_insert_list(content, var_name, new_list):
    """Top-level list değişkeni değiştir veya yoksa data_15m'den önce ekle."""
    pattern = re.compile(
        r'^(' + re.escape(var_name) + r'\s*=\s*)\[.*\]\s*$',
        re.MULTILINE
    )
    new_line = var_name + ' = ' + json.dumps(new_list, ensure_ascii=False)
    new_content, count = pattern.subn(new_line, content)
    if count >= 1:
        print(f"  ✅ '{var_name}' güncellendi ({len(new_list)} entry)")
        return new_content
    
    # Bulunamadı → data_15m'den hemen önce ekle
    insert_point = re.search(r'^data_15m\s*=', content, re.MULTILINE)
    if insert_point:
        insert_pos = insert_point.start()
        content = content[:insert_pos] + new_line + '\n' + content[insert_pos:]
        print(f"  ✅ '{var_name}' EKLENDİ ({len(new_list)} entry)")
    else:
        print(f"  ⚠️  '{var_name}' eklenemedi — data_15m bulunamadı")
    return content


def replace_data_line(content, var_name, new_dict):
    """data_15m = {...} gibi tek satırlık dict'i değiştirir."""
    # Pattern: satır başında var_name = {....}
    pattern = re.compile(
        r'^(' + re.escape(var_name) + r'\s*=\s*)\{.*\}\s*$',
        re.MULTILINE
    )
    new_line = var_name + ' = ' + json.dumps(new_dict, ensure_ascii=False)
    new_content, count = pattern.subn(new_line, content)
    if count == 0:
        print(f"  ⚠️  '{var_name}' bulunamadı — atlandı")
    elif count > 1:
        print(f"  ⚠️  '{var_name}' birden fazla eşleşme ({count}) — HEPSİ değişti, dosyayı kontrol et!")
    else:
        print(f"  ✅ '{var_name}' güncellendi")
    return new_content


def replace_candles_block(content, new_candles):
    """candles_data = { ... } çok satırlı bloğu değiştirir.
    
    Strateji: İlk 'candles_data = {' satırından başla,
    ardından gelen ilk '}' satırına (yorum olmayan) kadar değiştir.
    Yorum bloğu (# candles_data = {) atlanır.
    """
    # Aktif candles_data bloğunun başlangıcını bul (yorum olmayan)
    pattern = re.compile(
        r'^(candles_data\s*=\s*\{)\s*\n'   # açılış
        r'(.*?)'                             # içerik (lazy)
        r'^\}\s*$',                          # kapanış: satır başında tek }
        re.MULTILINE | re.DOTALL
    )
    
    # Yeni bloğu oluştur
    lines = ['candles_data = {']
    for tf in ['5m', '15m', '1h', '4h']:
        if tf not in new_candles:
            continue
        c = new_candles[tf]
        curr = c.get('curr', {})
        prev = c.get('prev', {})
        lines.append(f'    "{tf}": {{')
        lines.append(f'        "curr": {{"open": {curr["open"]}, "high": {curr["high"]}, "low": {curr["low"]}, "close": {curr["close"]}}},')
        lines.append(f'        "prev": {{"open": {prev["open"]}, "high": {prev["high"]}, "low": {prev["low"]}, "close": {prev["close"]}}},')
        lines.append(f'    }},')
    lines.append('}')
    new_block = '\n'.join(lines)
    
    new_content, count = pattern.subn(new_block, content, count=1)
    if count == 0:
        print("  ⚠️  'candles_data' bloğu bulunamadı — atlandı")
    else:
        print("  ✅ 'candles_data' güncellendi")
    return new_content


def append_regime_candles(content, new_candles_list):
    """CANDLES_4H_REGIME listesinin sonuna yeni mumlar ekler.
    
    Strateji: Son ']' satırını bul (CANDLES_4H_REGIME'in kapanışı),
    onun hemen öncesine yeni tuple satırları ekle.
    """
    if not new_candles_list:
        return content
    
    # CANDLES_4H_REGIME bloğunun kapanış ]'ini bul
    # Bloğun kendisini bulalım
    start_match = re.search(r'^CANDLES_4H_REGIME\s*=\s*\[', content, re.MULTILINE)
    if not start_match:
        print("  ⚠️  'CANDLES_4H_REGIME' bulunamadı — atlandı")
        return content
    
    # start_match'ten sonraki ilk ] satırını bul
    rest = content[start_match.start():]
    bracket_depth = 0
    close_offset = None
    for i, ch in enumerate(rest):
        if ch == '[':
            bracket_depth += 1
        elif ch == ']':
            bracket_depth -= 1
            if bracket_depth == 0:
                close_offset = start_match.start() + i
                break
    
    if close_offset is None:
        print("  ⚠️  'CANDLES_4H_REGIME' kapanış ']' bulunamadı — atlandı")
        return content
    
    # Doğrulama + duplikasyon filtresi
    existing_block = content[start_match.start():close_offset]
    filtered = []
    for idx, c in enumerate(new_candles_list):
        if len(c) < 5:
            print(f"  ❌ regime_candles[{idx}] eksik eleman ({len(c)}/5 gerekli) — atlandı")
            continue
        ts = c[0]
        if f'"{ts}"' in existing_block:
            print(f"  ⚠️  regime mum '{ts}' zaten mevcut — atlandı")
            continue
        filtered.append(c)
    
    if not filtered:
        print(f"  ℹ️  Eklenecek yeni regime mumu yok")
        return content
    
    # Son tuple satırından sonra, ] öncesine ekle
    new_lines = []
    for c in filtered:
        ts, o, h, l, cl = c[0], c[1], c[2], c[3], c[4]
        new_lines.append(f'    ("{ts}", {o}, {h}, {l}, {cl}),')
    
    insert_text = '\n' + '\n'.join(new_lines) + '\n'
    
    new_content = content[:close_offset] + insert_text + content[close_offset:]
    print(f"  ✅ CANDLES_4H_REGIME: {len(filtered)} mum eklendi")
    return new_content


def append_global_candles(content, global_candles_dict):
    """CANDLES_4H, CANDLES_1H, CANDLES_15M dizilerine yeni mumlar ekler.
    
    global_candles_dict format:
      {"4h": [["MM-DD HH:MM", O, H, L, C], ...],
       "1h": [...], "15m": [...]}
    
    Dedup: timestamp zaten varsa atla.
    """
    if not global_candles_dict:
        return content
    
    tf_map = {"4h": "CANDLES_4H", "1h": "CANDLES_1H", "15m": "CANDLES_15M", "5m": "CANDLES_5M"}
    total_added = 0
    
    for tf_key, var_name in tf_map.items():
        candles = global_candles_dict.get(tf_key)
        if not candles:
            continue
        
        # Değişken bloğunu bul
        pattern = rf'^{var_name}\s*=\s*\['
        start_match = re.search(pattern, content, re.MULTILINE)
        if not start_match:
            print(f"  ⚠️  '{var_name}' bulunamadı — atlandı")
            continue
        
        # Kapanış ]'ini bul (bracket matching)
        rest = content[start_match.start():]
        bracket_depth = 0
        close_offset = None
        for i, ch in enumerate(rest):
            if ch == '[':
                bracket_depth += 1
            elif ch == ']':
                bracket_depth -= 1
                if bracket_depth == 0:
                    close_offset = start_match.start() + i
                    break
        
        if close_offset is None:
            print(f"  ⚠️  '{var_name}' kapanış ']' bulunamadı — atlandı")
            continue
        
        # Mevcut blokta timestamp dedup
        existing_block = content[start_match.start():close_offset]
        filtered = []
        for c in candles:
            if len(c) < 5:
                continue
            ts = c[0]
            if f'"{ts}"' in existing_block:
                continue
            filtered.append(c)
        
        if not filtered:
            continue
        
        # Ekle
        new_lines = []
        for c in filtered:
            ts, o, h, l, cl = c[0], c[1], c[2], c[3], c[4]
            new_lines.append(f'    ("{ts}", {o}, {h}, {l}, {cl}),')
        
        insert_text = '\n' + '\n'.join(new_lines) + '\n'
        content = content[:close_offset] + insert_text + content[close_offset:]
        total_added += len(filtered)
        print(f"  ✅ {var_name}: {len(filtered)} mum eklendi")
    
    if total_added == 0:
        print(f"  ℹ️  Global CANDLES: eklenecek yeni mum yok (tümü mevcut)")
    return content


def update_file(filepath, update_data):
    """Tek dosyayı günceller."""
    print(f"\n{'='*50}")
    print(f"  DOSYA: {os.path.basename(filepath)}")
    print(f"{'='*50}")
    
    # Oku
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_len = len(content)
    
    # 1) data_5m / data_15m / data_1h / data_4h
    for var in ['data_5m', 'data_15m', 'data_1h', 'data_4h']:
        if var in update_data:
            content = replace_data_line(content, var, update_data[var])
    
    # 1b) API zaman serileri — top-level list değişkenler olarak enjekte et
    api_series_vars = {
        'api_open_interest': 'api_open_interest_live',
        'api_whale_account': 'api_whale_account_live',
        'api_whale_position': 'api_whale_position_live',
        'api_funding_rate': 'api_funding_rate_live',
        'api_taker_ls': 'api_taker_ls_live',  # P59: LS 1h 30-entry
    }
    for json_key, var_name in api_series_vars.items():
        if json_key in update_data and update_data[json_key]:
            content = replace_or_insert_list(content, var_name, update_data[json_key])
    
    # 2) candles_data
    if 'candles' in update_data:
        content = replace_candles_block(content, update_data['candles'])
    
    # 3) CANDLES_4H_REGIME (sadece yon_41 dosyalarında)
    if 'regime_candles' in update_data:
        if 'CANDLES_4H_REGIME' in content:
            content = append_regime_candles(content, update_data['regime_candles'])
        else:
            print("  ℹ️  CANDLES_4H_REGIME bu dosyada yok — atlandı (yon_41 only)")
    
    # 4) Global CANDLES_4H/1H/15M append
    if 'global_candles' in update_data:
        content = append_global_candles(content, update_data['global_candles'])
    
    # Yedek al + yaz
    bak_path = filepath + '.bak'
    shutil.copy2(filepath, bak_path)
    print(f"  📁 Yedek: {os.path.basename(bak_path)}")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    new_len = len(content)
    diff = new_len - original_len
    print(f"  📊 Boyut: {original_len:,} → {new_len:,} ({diff:+,} karakter)")
    print(f"  ✅ TAMAMLANDI")


def auto_discover(script_dir):
    """Aynı klasördeki *_update.json ve yon_*.py dosyalarını bul."""
    jsons = sorted([f for f in os.listdir(script_dir) 
                    if f.endswith('_update.json') or f.endswith('_update.JSON')])
    yon4s = []
    yon5s = sorted([f for f in os.listdir(script_dir) if f.startswith('yon_') and f.endswith('.py')])
    targets = yon4s + yon5s
    # run_updater.py kendisini dahil etme
    targets = [f for f in targets if 'updater' not in f.lower()]
    return jsons, targets


def main():
    if len(sys.argv) >= 3:
        # Manuel mod: python3 run_updater.py <json> <dosya1> [dosya2...]
        json_path = sys.argv[1]
        target_files = sys.argv[2:]
    else:
        # Otomatik mod: dosyaları bul
        script_dir = find_work_dir()
        if not script_dir:
            print("❌ yon_*.py hiçbir klasörde bulunamadı!")
            print("   Tüm dosyaları (yon_*.py, *_update.json)")
            print("   run_updater.py ile AYNI klasöre koy.")
            sys.exit(1)
        jsons, targets = auto_discover(script_dir)
        
        if not jsons:
            print("❌ *_update.json bulunamadı!")
            print(f"   Klasör: {script_dir}")
            print(f"   Beklenen: rXX_update.json")
            sys.exit(1)
        if not targets:
            print("❌ yon_*.py bulunamadı!")
            print(f"   Klasör: {script_dir}")
            sys.exit(1)
        
        # En yeni JSON'u kullan (mtime bazlı)
        jsons_full = [os.path.join(script_dir, j) for j in jsons]
        json_path = max(jsons_full, key=os.path.getmtime)
        target_files = [os.path.join(script_dir, t) for t in targets]
        
        print(f"🔍 OTOMATİK MOD")
        print(f"   Klasör: {script_dir}")
        print(f"   JSON:   {os.path.basename(json_path)}")
        print(f"   Hedef:  {', '.join(targets)}")
    
    # JSON oku
    with open(json_path, 'r', encoding='utf-8') as f:
        update_data = json.load(f)
    
    print(f"JSON: {os.path.basename(json_path)}")
    keys = [k for k in update_data.keys()]
    print(f"Güncellenecek: {', '.join(keys)}")
    
    # Her dosyayı güncelle
    for fp in target_files:
        if not os.path.exists(fp):
            print(f"\n  ❌ DOSYA BULUNAMADI: {fp}")
            continue
        update_file(fp, update_data)
    
    print(f"\n{'='*50}")
    print(f"  BİTTİ — {len(target_files)} dosya işlendi")
    print(f"{'='*50}")


if __name__ == '__main__':
    main()
