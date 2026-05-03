#!/usr/bin/env python3
"""
snapshot_arsiv.py  -  r_update.json'in zaman damgali kopyasini saklar
=====================================================================

NEDEN: leading_karar.py icin gercek backtest verisi toplamak.
Mevcut r_update.json sadece ANLIK snapshot — gecmise bakilamaz.
Notion Runs database'inde sadece whale_ls + LS_1h + Direction kayitli;
depth/CVD/funding/OI tarihsel YOK. Bu yuzden R40-R42 backtest yapilamadi.

NE YAPAR: Her cagrildiginda mevcut r_update.json'in kopyasini
snapshots/ klasorune yazar. Dosya adi: r_update_YYYYMMDD_HHMMSS.json (UTC).

KULLANIM:
  python3 snapshot_arsiv.py                # snapshot kaydet
  python3 snapshot_arsiv.py --info         # arsiv ozeti
  python3 snapshot_arsiv.py --listele 10   # son 10 kaydi listele

auto_fetch.py icine entegrasyon (opsiyonel):
  main()'in sonuna sun ekle:
      try:
          import snapshot_arsiv
          snapshot_arsiv.archive_now()
      except Exception as _ae:
          print(f"  arsiv hatasi: {_ae}")

DEPOLAMA: ~30KB/snapshot. 15 dk'da bir = 96/gun = ~3MB/gun.
Pydroid'da rahat sigar. Eski snapshot'lar gerekirse manuel silinir.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def find_r_update():
    """r_update.json'u bul."""
    candidates = [
        Path(__file__).parent / "r_update.json",
        Path.cwd() / "r_update.json",
        Path("/storage/emulated/0/Download/r_update.json"),
        Path("/storage/emulated/0/Downloads/r_update.json"),
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def get_archive_dir(base=None):
    """snapshots/ klasoru bul ya da olustur (r_update.json yaninda)."""
    if base is None:
        rj = find_r_update()
        base = rj.parent if rj else Path(__file__).parent
    arch = Path(base) / "snapshots"
    arch.mkdir(exist_ok=True)
    return arch


def archive_now(rj_path=None, dest_dir=None):
    """Mevcut r_update.json'in timestamp'li kopyasini kaydet.

    Returns:
      (saved_path: Path, size_bytes: int) basari
      (None, hata_mesaji: str) hata
    """
    rj = Path(rj_path) if rj_path else find_r_update()
    if not rj or not rj.is_file():
        return None, "r_update.json bulunamadi"

    try:
        with open(rj, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return None, f"r_update.json bozuk: {e}"
    except OSError as e:
        return None, f"r_update.json okunamadi: {e}"

    if dest_dir:
        arch = Path(dest_dir)
        arch.mkdir(parents=True, exist_ok=True)
    else:
        arch = get_archive_dir(rj.parent)

    # Timestamp UTC
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    fname = f"r_update_{ts}.json"
    fpath = arch / fname

    # Ayni saniyede iki cagri olursa _2 _3 ekle
    counter = 1
    while fpath.exists():
        counter += 1
        fname = f"r_update_{ts}_{counter}.json"
        fpath = arch / fname

    # Metadata ekle (kaynak dokunulmaz, kopyaya eklenir)
    data["_archived_at"] = datetime.now(timezone.utc).isoformat()
    try:
        src_mtime = datetime.fromtimestamp(
            rj.stat().st_mtime, tz=timezone.utc
        ).isoformat()
        data["_source_mtime"] = src_mtime
    except OSError:
        pass

    try:
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError as e:
        return None, f"yazma hatasi: {e}"

    return fpath, fpath.stat().st_size


def archive_info():
    """Arsiv klasor ozeti."""
    arch = get_archive_dir()
    files = sorted(arch.glob("r_update_*.json"))
    if not files:
        print(f"  Arsiv bos: {arch}")
        return

    total_size = sum(f.stat().st_size for f in files)
    first = files[0]
    last = files[-1]

    # Time span
    def parse_ts(name):
        # r_update_20260502_193000.json -> "20260502_193000"
        try:
            stem = name.stem.replace("r_update_", "")
            stem = stem.split("_")[0] + "_" + stem.split("_")[1]
            return datetime.strptime(stem, "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)
        except (ValueError, IndexError):
            return None

    t_first = parse_ts(first)
    t_last = parse_ts(last)
    span_str = ""
    if t_first and t_last:
        delta = t_last - t_first
        hours = delta.total_seconds() / 3600
        if hours < 24:
            span_str = f"{hours:.1f} saat"
        else:
            span_str = f"{hours/24:.1f} gun"

    print(f"  Arsiv klasoru     : {arch}")
    print(f"  Snapshot sayisi   : {len(files)}")
    print(f"  Toplam boyut      : {total_size/1024:.1f} KB")
    print(f"  Ilk kayit         : {first.name}")
    print(f"  Son kayit         : {last.name}")
    if span_str:
        print(f"  Zaman araligi     : {span_str}")


def archive_list(n=10):
    """Son N snapshot'i ozetle."""
    arch = get_archive_dir()
    files = sorted(arch.glob("r_update_*.json"), reverse=True)[:n]
    if not files:
        print(f"  Arsiv bos: {arch}")
        return

    print(f"  Son {len(files)} kayit ({arch}):")
    header = f"  {'DOSYA':<32} {'PRICE':>9} {'DEPTH':>6} {'CVD_5m':>14} {'FUND APR':>10}"
    print(header)
    print(f"  {'-'*32} {'-'*9} {'-'*6} {'-'*14} {'-'*10}")

    for f in files:
        try:
            with open(f, encoding="utf-8") as fh:
                d = json.load(fh)
            d1h = d.get("data_1h") or {}
            d5m = d.get("data_5m") or {}
            price = d1h.get("current_price") or d5m.get("current_price", 0)
            depth = d1h.get("depth_imbalance")
            cvd = d5m.get("futures_cvd", 0)
            fr = d1h.get("funding_rate")
            apr = (fr * 3 * 365 * 100) if fr is not None else None

            depth_str = f"{depth:.2f}" if isinstance(depth, (int, float)) else "-"
            apr_str = f"{apr:+.1f}%" if apr is not None else "-"

            print(f"  {f.name:<32} ${price:>7,.0f} {depth_str:>6} "
                  f"{cvd:>+14,.0f} {apr_str:>10}")
        except (json.JSONDecodeError, OSError) as e:
            print(f"  {f.name:<32} HATA: {type(e).__name__}")


def main():
    args = sys.argv[1:]

    if "--info" in args or "--ozet" in args:
        archive_info()
        return 0

    if "--listele" in args or "--list" in args:
        n = 10
        for i, a in enumerate(args):
            if a in ("--listele", "--list") and i + 1 < len(args):
                try:
                    n = int(args[i + 1])
                except (ValueError, IndexError):
                    pass
        archive_list(n)
        return 0

    if "--help" in args or "-h" in args:
        print(__doc__)
        return 0

    # Default: arsivle
    saved, info = archive_now()
    if saved:
        # info burada size_bytes
        all_files = list(saved.parent.glob("r_update_*.json"))
        print(f"  KAYITLI : {saved.name}")
        print(f"  Boyut   : {info:,} byte")
        print(f"  Toplam  : {len(all_files)} snapshot ({saved.parent})")
        return 0
    else:
        # info burada hata_mesaji
        print(f"  HATA: {info}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
