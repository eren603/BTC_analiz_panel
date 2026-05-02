#!/usr/bin/env python3
"""
tek_karar.py  -  TUM KARAR ZINCIRI TEK TIKLA
=============================================

NEDEN: Pydroid'da iki ayri scripti calistirmak yerine tek dosyaya bas.
Eski sistem (karar_motoru) ile yeni sistem (leading_karar v5) cikti
yan yana. Karsilastir, karar ver.

NE YAPAR:
  1. auto_compact_fixed.py'yi calistirir
     (auto_fetch + run_updater + karar_motoru -- eski karar verir)
  2. leading_karar.py'yi calistirir
     (Notion empirik + live overlay -- yeni karar verir)
  3. Iki cikti arka arkaya, scroll edip karsilastir.

KULLANIM:
  python3 tek_karar.py
  (auto_compact_fixed.py ve leading_karar.py ile ayni klasorde olmali)

YORUM REHBERI (cikti scroll sonrasi):
  Iki sistem AYNI YON  -> hizalanma var, guvenle gir
  Iki sistem ZIDDI     -> CELISKI, BEKLE (V4 dersi)
  Bir sistem BEKLE/NOTR + diger GIR -> kucuk pozisyon, dikkatli
"""

import subprocess
import sys
from pathlib import Path


def find_dir():
    """auto_compact_fixed.py + leading_karar.py birlikte bulundugu klasoru bul."""
    candidates = [
        Path(__file__).parent,
        Path.cwd(),
        Path("/storage/emulated/0/Download"),
        Path("/storage/emulated/0/Downloads"),
        Path("/storage/emulated/0"),
    ]
    for d in candidates:
        if not d.is_dir():
            continue
        if (d / "auto_compact_fixed.py").is_file() and (d / "leading_karar.py").is_file():
            return d
    return None


def run_script(script_path, cwd):
    """Subprocess ile calistir, stdout'a aynen aktar."""
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(cwd),
            check=False,
        )
        return result.returncode
    except Exception as e:
        print(f"  HATA: {script_path.name} calismadi: {e}")
        return 1


def main():
    d = find_dir()
    if not d:
        print("HATA: auto_compact_fixed.py + leading_karar.py birlikte bulunamadi.")
        print("Aranan klasorler:")
        for p in [Path(__file__).parent, Path.cwd(),
                  Path("/storage/emulated/0/Download"),
                  Path("/storage/emulated/0/Downloads"),
                  Path("/storage/emulated/0")]:
            mark = "+" if p.is_dir() else "-"
            print(f"  {mark} {p}")
        return 1

    print(f"Klasor: {d}")
    bar = "=" * 78

    # === ASAMA 1: ESKI SISTEM ===
    print()
    print(bar)
    print("  >>> ASAMA 1 / 2 — ESKI SISTEM (auto_fetch + karar_motoru)")
    print(bar)
    rc1 = run_script(d / "auto_compact_fixed.py", d)
    if rc1 != 0:
        print(f"  ⚠ auto_compact_fixed.py exit code {rc1}")

    # === ASAMA 2: YENI SISTEM ===
    print()
    print(bar)
    print("  >>> ASAMA 2 / 2 — YENI SISTEM (leading_karar v5)")
    print(bar)
    rc2 = run_script(d / "leading_karar.py", d)
    if rc2 != 0:
        print(f"  ⚠ leading_karar.py exit code {rc2}")

    # === YORUM REHBERI ===
    print()
    print(bar)
    print("  KARSILASTIRMA REHBERI")
    print(bar)
    print("  Yukarida iki sistem cikti var. Asagidaki tabloyla yorumla:")
    print()
    print("  ESKI sistem            YENI sistem            -> KARAR")
    print("  ---------              ---------              -------")
    print("  GIR LONG               GIR/DIKKATLI LONG      -> GIR LONG (hizali)")
    print("  GIR SHORT              DIKKATLI SHORT         -> KUCUK SHORT (kati esik)")
    print("  GIR LONG               BEKLE/SHORT            -> BEKLE (CELISKI)")
    print("  GIR SHORT              BEKLE/LONG             -> BEKLE (CELISKI -- V4 dersi)")
    print("  BEKLE/NOTR             GIR LONG               -> KUCUK LONG (yeni firsat)")
    print("  Her ikisi BEKLE        Her ikisi BEKLE        -> BEKLE (kararsiz piyasa)")
    print()
    print("  KURAL: CELISKI varsa POZISYON ACMA. Likitide riski yuksek (R41 dersi).")
    print(bar)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
