#!/usr/bin/env python3
"""
============================================================================
  FLOW CARD V4  —  LONG-only paralel kart
  yön_41'in DERIVATİF/whale tabanlı SHORT bakışına paralel,
  LONG fırsatlarını ham AKIŞ verisinden yakalar.

  Backtest (R2-R42, 35 ölçülebilir): 6/6 = %100 LONG, 0 yanlış.
  Kapsam: %17 (seçici, çoğu zaman sessiz — kasıtlı).
  DOWN runlarında %100 sessiz kaldı (11/11 doğru kaçınma).
============================================================================

VERİ KAYNAKLARI
  1. yön_*.py HISTORICAL_DATA    →  3 backtest'li sinyal (A, B, C)
  2. Crypto.com public REST      →  1 anlık leading sinyal (D)
                                    → opsiyonel: erişim varsa
                                    → erişim yoksa graceful skip

============================================================================
SİNYALLER VE FORMÜLLER
============================================================================

A — TAKER L/S TIMEFRAME GAP   (HISTORICAL_DATA, 1h + 4h)
    A = +1  eğer  tls_1h > tls_4h  VE  tls_1h > 1.00  (LONG argümanı)
    A = -1  eğer  tls_1h < tls_4h  VE  tls_1h < 1.00  (LONG'a karşı)
    A =  0  diğer

B — OI DELTA + HACİM ONAYI    (HISTORICAL_DATA, 1h)
    vol_ratio = vol_1h / vol_ma5_1h
    B = +1  eğer  oi_delta > +20  VE  vol_ratio > 1.00
    B = -1  eğer  oi_delta < -20  VE  vol_ratio > 1.00
    B =  0  diğer

C — FUTURES CVD MOMENTUM      (HISTORICAL_DATA, 1h)
    C = +1  eğer  fcvd_1h > +$5M
    C = -1  eğer  fcvd_1h < -$5M
    C =  0  diğer

ÖNEMLİ: Sinyaller -1 alabilir (LONG'a karşı kanıt). Bu kasıtlı:
"LONG'a karşı kanıt" varsa LONG vermeyiz. Final çıktı yine LONG-only.

YEREL KARAR  (A+B+C):
    skor ≥ +2  →  LONG aday  (en az 2 LONG argümanı, karşı argüman yok ya da nötr)
    skor <  2  →  NOTR (sessiz)

D — ANLIK ONAY/BLOK   (Crypto.com REST, anlık)
  Sadece A+B+C ≥ +2 olduğunda devreye girer.
  D1 — Order book imbalance (top 20):
       imb = bid_qty / (bid_qty + ask_qty)
       d1 = +1 (>0.55), -1 (<0.45), 0 arası
  D2 — Tape delta (son 50 trade):
       delta = (buy_vol - sell_vol) / (buy_vol + sell_vol)
       d2 = +1 (>+0.20), -1 (<-0.20), 0 arası
  D = d1 + d2  (-2..+2)

FİNAL:
    A+B+C ≥ 2  AND  D ≥  0   →  ✅ LONG
    A+B+C ≥ 2  AND  D = -1   →  ⚠️ LONG-ŞÜPHELİ
    A+B+C ≥ 2  AND  D = -2   →  🚫 LONG İPTAL
    A+B+C  < 2               →  NOTR  (D bakılmaz)
    D erişilemiyorsa         →  D atlanır, A+B+C kararı uygulanır

============================================================================
KULLANIM
  flow_card.py'yi yön_*.py ile aynı dizine koy. Pydroid Play tuşu.
  urllib stdlib — kütüphane gerekmez. Crypto.com erişimi yoksa atlar.
============================================================================
"""

import sys, os, re, ast, json, urllib.request, urllib.error

# ═══ MANUEL OVERRIDE (opsiyonel) ═══
# Otomatik arama yon_*.py'yi bulamazsa, asagiya tam yolu yaz:
#   ornek: YON_PATH = "/storage/emulated/0/Pydroid3/yon_41.py"
YON_PATH = ""
# ════════════════════════════════════

# ─────────────────────── HISTORICAL_DATA YÜKLEYİCİ ───────────────────────

def load_historical_data(yon_path):
    with open(yon_path, 'r', encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'^HISTORICAL_DATA\s*=\s*(\{)', src, re.M)
    if not m:
        raise RuntimeError("HISTORICAL_DATA bulunamadı")
    start = m.start(1); depth = 0; i = start
    while i < len(src):
        c = src[i]
        if c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return ast.literal_eval(src[start:i+1])
        i += 1
    raise RuntimeError("HISTORICAL_DATA parse edilemedi")

def get_active_run(HD):
    keys = sorted(HD.keys(), key=lambda x: int(x[1:]))
    for k in reversed(keys):
        if HD[k].get('actual') is None:
            return k
    return keys[-1]

# ─────────────────────── SİNYAL A, B, C ───────────────────────

def signal_A(rd):
    d1h = rd.get('data_1h') or {}
    d4h = rd.get('data_4h') or {}
    t1, t4 = d1h.get('taker_ls_ratio'), d4h.get('taker_ls_ratio')
    if t1 is None or t4 is None:
        return 0, "veri eksik"
    if t1 > t4 and t1 > 1.00:
        return +1, f"tls_1h={t1:.3f} > tls_4h={t4:.3f} ve >1.00 → LONG argümanı"
    if t1 < t4 and t1 < 1.00:
        return -1, f"tls_1h={t1:.3f} < tls_4h={t4:.3f} ve <1.00 → LONG'a karşı"
    return 0, f"tls_1h={t1:.3f}, tls_4h={t4:.3f} → nötr"

def signal_B(rd):
    d1h = rd.get('data_1h') or {}
    od, v, vma = d1h.get('oi_delta'), d1h.get('volume'), d1h.get('volume_ma5')
    if od is None or v is None or vma is None or vma == 0:
        return 0, "veri eksik"
    vr = v / vma
    if od >  20 and vr > 1.00:
        return +1, f"oi_delta={od:.1f} > 20 ve vol/ma5={vr:.2f} > 1.00 → LONG argümanı"
    if od < -20 and vr > 1.00:
        return -1, f"oi_delta={od:.1f} < -20 ve vol/ma5={vr:.2f} > 1.00 → LONG'a karşı"
    return 0, f"oi_delta={od:.1f}, vol/ma5={vr:.2f} → nötr"

def signal_C(rd):
    d1h = rd.get('data_1h') or {}
    fc = d1h.get('futures_cvd')
    if fc is None:
        return 0, "veri eksik"
    if fc >  5_000_000:
        return +1, f"fcvd_1h=${fc/1e6:+.1f}M > $5M → LONG argümanı"
    if fc < -5_000_000:
        return -1, f"fcvd_1h=${fc/1e6:+.1f}M < -$5M → LONG'a karşı"
    return 0, f"fcvd_1h=${fc/1e6:+.1f}M → nötr"

# ─────────────────────── SİNYAL D — Crypto.com canlı ───────────────────────

CRYPTO_BOOK_URL   = "https://api.crypto.com/v2/public/get-book?instrument_name=BTC_USDT&depth=20"
CRYPTO_TRADES_URL = "https://api.crypto.com/v2/public/get-trades?instrument_name=BTC_USDT"

def _fetch_json(url, timeout=8):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

def signal_D():
    """(D, info_dict) | (None, neden_str)"""
    try:
        book = _fetch_json(CRYPTO_BOOK_URL)
        bdata = (book.get('result') or {}).get('data') or [{}]
        bdata = bdata[0] if bdata else {}
        bids = bdata.get('bids') or []
        asks = bdata.get('asks') or []
        if not bids or not asks:
            return None, "order book boş"

        # crypto.com formatı: [price, qty, orders] veya {"price","qty"}
        def qty(x):
            if isinstance(x, (list, tuple)):
                return float(x[1])
            return float(x.get('qty', 0))
        bid_qty = sum(qty(x) for x in bids[:20])
        ask_qty = sum(qty(x) for x in asks[:20])
        if bid_qty + ask_qty == 0:
            return None, "order book hacmi sıfır"
        imb = bid_qty / (bid_qty + ask_qty)
        d1 = +1 if imb > 0.55 else (-1 if imb < 0.45 else 0)

        trades = _fetch_json(CRYPTO_TRADES_URL)
        tdata = (trades.get('result') or {}).get('data') or []
        if not tdata:
            return None, "trade akışı boş"

        def side(t):
            return (t.get('s') or t.get('side') or '').lower()
        def tqty(t):
            return float(t.get('q') or t.get('qty') or t.get('quantity') or 0)

        trades50 = tdata[:50]
        buy_vol  = sum(tqty(t) for t in trades50 if side(t) == 'buy')
        sell_vol = sum(tqty(t) for t in trades50 if side(t) == 'sell')
        if buy_vol + sell_vol == 0:
            return None, "trade hacmi sıfır"
        delta = (buy_vol - sell_vol) / (buy_vol + sell_vol)
        d2 = +1 if delta > 0.20 else (-1 if delta < -0.20 else 0)

        return (d1 + d2), {
            'bid_qty': bid_qty, 'ask_qty': ask_qty, 'imb': imb, 'd1': d1,
            'buy_vol': buy_vol, 'sell_vol': sell_vol, 'delta': delta, 'd2': d2,
        }
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
        return None, f"erişim yok: {type(e).__name__}"
    except Exception as e:
        return None, f"hata: {type(e).__name__}: {e}"

# ─────────────────────── ÇIKTI ───────────────────────

def evaluate(rd):
    A, rA = signal_A(rd)
    B, rB = signal_B(rd)
    C, rC = signal_C(rd)
    return {'A':A,'rA':rA,'B':B,'rB':rB,'C':C,'rC':rC,'local':A+B+C}

def print_card(label, rd, ev, D, D_info):
    d1h = rd.get('data_1h') or {}
    print()
    print("="*68)
    print(f"  FLOW CARD V4   {label}   {rd.get('run_time','?')}")
    print("="*68)
    print(f"  Fiyat: ${d1h.get('current_price')}   Actual: {rd.get('actual') or 'AÇIK'}")
    print()
    print(f"  A (Taker L/S gap)   : {ev['A']:+d}  | {ev['rA']}")
    print(f"  B (OI Δ + hacim)    : {ev['B']:+d}  | {ev['rB']}")
    print(f"  C (Futures CVD)     : {ev['C']:+d}  | {ev['rC']}")
    print(f"  ─ Yerel skor A+B+C  : {ev['local']:+d}  (≥+2 → LONG aday)")
    print()

    if D is None:
        print(f"  D (Crypto.com anlık): SKIP — {D_info}")
        if ev['local'] >= 2:
            final, sfx = 'LONG', '  (D atlandı)'
        else:
            final, sfx = 'NOTR', ''
    else:
        info = D_info
        print(f"  D (Crypto.com anlık): {D:+d}")
        print(f"     OB imb={info['imb']:.3f}  bid={info['bid_qty']:.3f}/ask={info['ask_qty']:.3f}  d1={info['d1']:+d}")
        print(f"     Tape  ={info['delta']:+.3f}  buy={info['buy_vol']:.3f}/sell={info['sell_vol']:.3f}  d2={info['d2']:+d}")
        if ev['local'] < 2:
            final, sfx = 'NOTR', ''
        elif D >= 0:
            final, sfx = '✅ LONG', '  (anlık tape onay)'
        elif D == -1:
            final, sfx = '⚠️  LONG-ŞÜPHELİ', '  (anlık tape ters)'
        else:
            final, sfx = '🚫 LONG İPTAL', '  (anlık tape açık ters)'

    print()
    print(f"  ➤ KARAR: {final}{sfx}")
    print("="*68)

def backtest(HD):
    print()
    print("="*68)
    print("  BACKTEST  —  A+B+C kararı (D anlık, geçmişte yok)")
    print("="*68)
    correct = total = 0
    silent_up = silent_down = 0
    keys = sorted(HD.keys(), key=lambda x: int(x[1:]))
    for k in keys:
        rd = HD[k]
        if rd.get('actual') in (None, 'BELIRSIZ'): continue
        ev = evaluate(rd)
        if ev['local'] >= 2:
            total += 1
            ok = (rd['actual'] == 'UP')
            correct += int(ok)
            mark = '✅' if ok else '❌'
            print(f"  {k:>4s} {rd.get('run_time','?'):>11s} skor={ev['local']:+d} LONG actual={rd['actual']} {mark}")
        else:
            if rd['actual'] == 'UP':   silent_up += 1
            else:                       silent_down += 1
    if total:
        print()
        print(f"  LONG sinyalleri: {correct}/{total} = %{correct/total*100:.1f}")
        print(f"  Sessiz UP : {silent_up}  (kaçırılan fırsat)")
        print(f"  Sessiz DOWN: {silent_down}  (doğru kaçınma)")
    print("="*68)

# ─────────────────────── MAIN ───────────────────────

def main():
    yon_path = None

    # 1) Manuel override
    if YON_PATH:
        if os.path.isfile(YON_PATH):
            yon_path = YON_PATH
        else:
            print(f"UYARI: YON_PATH dosyasi yok: {YON_PATH}")
            print("Otomatik aramaya geciliyor...")

    # 2) Otomatik arama
    if not yon_path:
        here = os.path.dirname(os.path.abspath(__file__))
        cwd = os.getcwd()
        candidates = list(dict.fromkeys([
            here, cwd,
            '/storage/emulated/0/Download',
            '/storage/emulated/0/Pydroid3',
            '/storage/emulated/0/Documents',
            '/sdcard/Download',
            '/sdcard/Pydroid3',
            os.path.expanduser('~'),
        ]))

        for d in candidates:
            try:
                if not os.path.isdir(d): continue
                files = sorted(
                    [f for f in os.listdir(d) if f.startswith('yon_') and f.endswith('.py')],
                    reverse=True
                )
                if files:
                    yon_path = os.path.join(d, files[0])
                    break
            except (PermissionError, OSError):
                continue

        if not yon_path:
            print("HATA: yon_*.py bulunamadi. Bakilan klasorler:")
            for d in candidates:
                mark = "+" if os.path.isdir(d) else "-"
                print(f"  {mark} {d}")
            print()
            print("Cozum: yon_41.py'yi flow_card.py ile ayni klasore koy")
            print("       VEYA bu dosyanin basindaki YON_PATH'i doldur.")
            sys.exit(1)

    print(f"yon dosyasi: {yon_path}")
    HD = load_historical_data(yon_path)
    print(f"Yuklendi: {len(HD)} run (R{min(int(k[1:]) for k in HD)}-R{max(int(k[1:]) for k in HD)})")

    label = get_active_run(HD)
    rd = HD[label]
    ev = evaluate(rd)
    D, D_info = signal_D()
    print_card(label, rd, ev, D, D_info)
    backtest(HD)

if __name__ == '__main__':
    main()
