"""
Android Hızlandırıcı - Pydroid 3 Uyumlu (Root Gerektirmez)

Telefonunuzu hızlandırmak için güvenli, sandbox-içi optimizasyonlar yapar:
  - RAM trim sinyali gönderir (kendi sürecimiz + sistem önerisi)
  - Python/Pydroid önbelleğini ve geçici dosyalarını temizler
  - /sdcard üzerinde junk (thumbnail, .tmp, .log, .cache) tarar/siler
  - Büyük & eski indirilen dosyaları listeler
  - Cihaz bilgilerini (CPU, RAM, depolama, yük) gösterir
  - Android Ayarlar ekranlarını intent ile açar (depolama, pil, geliştirici)
  - İpuçları + hızlı GC

Kullanım: Pydroid 3'te dosyayı aç → Run (▶). Menüden seçim yap.
Not: Scoped Storage (Android 11+) nedeniyle başka uygulamaların önbelleği
silinemez; bu nedenle script güvenli ve görünür alanlara odaklanır.
"""

from __future__ import annotations

import gc
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

# ---------- Renkli çıktı (Pydroid terminali ANSI'yi destekler) ----------
class C:
    R = "\033[0m"
    B = "\033[1m"
    G = "\033[92m"
    Y = "\033[93m"
    RD = "\033[91m"
    CY = "\033[96m"
    M = "\033[95m"
    DIM = "\033[2m"


def cprint(msg: str, color: str = C.R) -> None:
    print(f"{color}{msg}{C.R}")


def header(title: str) -> None:
    bar = "═" * (len(title) + 4)
    cprint(f"\n{bar}", C.CY)
    cprint(f"  {title}", C.B + C.CY)
    cprint(f"{bar}\n", C.CY)


def human_size(num: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if num < 1024.0:
            return f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} PB"


# ---------- Yardımcılar ----------
def run_shell(cmd: list[str], timeout: int = 5) -> tuple[int, str]:
    try:
        out = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return out.returncode, (out.stdout + out.stderr).strip()
    except FileNotFoundError:
        return 127, "komut bulunamadı"
    except subprocess.TimeoutExpired:
        return 124, "zaman aşımı"
    except Exception as e:
        return 1, str(e)


def read_proc(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return ""


def sdcard_root() -> Path:
    for p in ("/sdcard", "/storage/emulated/0", str(Path.home())):
        if os.path.isdir(p) and os.access(p, os.R_OK):
            return Path(p)
    return Path.home()


# ---------- 1) Cihaz bilgisi ----------
def show_device_info() -> None:
    header("CİHAZ DURUMU")

    mem = read_proc("/proc/meminfo")
    fields = {"MemTotal": 0, "MemFree": 0, "MemAvailable": 0, "Cached": 0, "SwapTotal": 0, "SwapFree": 0}
    for line in mem.splitlines():
        for k in fields:
            if line.startswith(k + ":"):
                m = re.search(r"(\d+)", line)
                if m:
                    fields[k] = int(m.group(1)) * 1024
    if fields["MemTotal"]:
        used = fields["MemTotal"] - fields["MemAvailable"]
        pct = used * 100.0 / fields["MemTotal"]
        bar_len = 30
        filled = int(bar_len * pct / 100)
        bar = "█" * filled + "░" * (bar_len - filled)
        col = C.G if pct < 70 else (C.Y if pct < 85 else C.RD)
        cprint(f"RAM   [{bar}] {pct:5.1f}%", col)
        cprint(
            f"      Toplam: {human_size(fields['MemTotal'])}  "
            f"Kullanılan: {human_size(used)}  "
            f"Boşaltılabilir: {human_size(fields['MemAvailable'])}",
            C.DIM,
        )
        if fields["SwapTotal"]:
            sused = fields["SwapTotal"] - fields["SwapFree"]
            cprint(f"SWAP  Kullanılan: {human_size(sused)} / {human_size(fields['SwapTotal'])}", C.DIM)

    load = read_proc("/proc/loadavg").split()
    if load:
        cprint(f"\nCPU yükü (1/5/15dk): {load[0]} / {load[1]} / {load[2]}", C.CY)

    cpuinfo = read_proc("/proc/cpuinfo")
    cores = cpuinfo.count("processor\t:")
    model = ""
    for line in cpuinfo.splitlines():
        if line.lower().startswith("hardware") or line.lower().startswith("model name"):
            model = line.split(":", 1)[-1].strip()
            break
    if cores:
        cprint(f"CPU: {cores} çekirdek  {('· ' + model) if model else ''}", C.CY)

    disk_info = None
    try:
        disk_info = shutil.disk_usage(str(sdcard_root()))
        st = disk_info
        pct = st.used * 100.0 / st.total
        bar_len = 30
        filled = int(bar_len * pct / 100)
        bar = "█" * filled + "░" * (bar_len - filled)
        col = C.G if pct < 80 else (C.Y if pct < 92 else C.RD)
        cprint(f"\nDEPO  [{bar}] {pct:5.1f}%", col)
        cprint(
            f"      Toplam: {human_size(st.total)}  "
            f"Boş: {human_size(st.free)}  "
            f"Kullanılan: {human_size(st.used)}",
            C.DIM,
        )
    except OSError:
        pass

    bat_pct, bat_status = _read_battery()
    if bat_pct:
        cprint(f"\nPil:  %{bat_pct}  ({bat_status or 'bilinmiyor'})", C.M)
    else:
        cprint("\nPil:  bilgi okunamadı (Pydroid sandbox)", C.DIM)

    _print_health_summary(fields, disk_info)


def _print_health_summary(mem: dict, disk) -> None:
    cprint("\n── SAĞLIK ÖZETİ ──", C.B)
    if mem.get("MemTotal"):
        used_pct = (mem["MemTotal"] - mem["MemAvailable"]) * 100.0 / mem["MemTotal"]
        if used_pct < 70:
            cprint("  ✅ RAM: rahat", C.G)
        elif used_pct < 85:
            cprint("  ⚠️  RAM: orta — arka plan uygulamalarını kapat", C.Y)
        else:
            cprint("  🔴 RAM: dolu — yeniden başlat öneriliyor", C.RD)
    if disk:
        try:
            free_gb = disk.free / 1024**3
            if free_gb > 5:
                cprint(f"  ✅ Depolama: {free_gb:.1f} GB boş, ferah", C.G)
            elif free_gb > 2:
                cprint(f"  ⚠️  Depolama: {free_gb:.1f} GB boş — temizle", C.Y)
            else:
                cprint(f"  🔴 Depolama: {free_gb:.1f} GB boş — kritik!", C.RD)
        except Exception:
            pass


def _read_battery() -> tuple[str, str]:
    psu = "/sys/class/power_supply"
    try:
        subs = os.listdir(psu)
    except OSError:
        subs = []
    for sub in subs:
        cap = read_proc(f"{psu}/{sub}/capacity").strip()
        if cap and cap.isdigit():
            return cap, read_proc(f"{psu}/{sub}/status").strip()
    rc, out = run_shell(["dumpsys", "battery"], timeout=4)
    if rc == 0 and out:
        pct = ""
        st = ""
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("level:"):
                pct = line.split(":", 1)[1].strip()
            elif line.startswith("status:"):
                code = line.split(":", 1)[1].strip()
                st = {"2": "Charging", "3": "Discharging", "4": "Not charging", "5": "Full"}.get(code, code)
        if pct:
            return pct, st
    rc, out = run_shell(["sh", "-c", "termux-battery-status"], timeout=3)
    if rc == 0 and "percentage" in out:
        m = re.search(r'"percentage"\s*:\s*(\d+)', out)
        s = re.search(r'"status"\s*:\s*"([^"]+)"', out)
        if m:
            return m.group(1), (s.group(1) if s else "")
    return "", ""


# ---------- 2) RAM trim ----------
def trim_memory() -> None:
    header("RAM TEMİZLEME (memory trim)")

    cprint("Python çöp toplayıcı çalıştırılıyor...", C.Y)
    n = 0
    for _ in range(3):
        n += gc.collect()
    cprint(f"  ✓ {n} obje serbest bırakıldı", C.G)

    pkg = os.environ.get("PYDROID_PKG") or "ru.iiec.pydroid3"
    cprint("\nTRIM_MEMORY sinyali deneniyor (3 yöntem)...", C.Y)
    trim_attempts = [
        ["cmd", "activity", "send-trim-memory", pkg, "COMPLETE"],
        ["am", "send-trim-memory", pkg, "COMPLETE"],
        ["am", "send-trim-memory", pkg, "MODERATE"],
    ]
    trim_ok = False
    for cmd in trim_attempts:
        rc, out = run_shell(cmd)
        if rc == 0 and "Failure" not in out and "Error" not in out:
            cprint(f"  ✓ Başarılı: {' '.join(cmd[:3])}", C.G)
            trim_ok = True
            break
    if not trim_ok:
        cprint("  ⚠  Android 11+ root'suz trim'i engelliyor — atlandı", C.DIM)

    import ctypes
    try:
        ctypes.CDLL("libc.so").malloc_trim(0)
        cprint("  ✓ Native heap fragmanları toplandı", C.G)
    except (OSError, AttributeError):
        pass

    try:
        with open("/proc/sys/vm/drop_caches", "w", encoding="utf-8") as f:
            f.write("3\n")
        cprint("  ✓ Sayfa önbelleği bırakıldı (root)", C.G)
    except (OSError, PermissionError):
        pass

    cprint("\n💡 EN ETKİLİ ADIM:", C.B + C.Y)
    cprint("   Son Kullanılanlar (kare ☐) → 'Tümünü Kapat'", C.Y)
    cprint("   Bu, script'in yapabileceğinden çok daha fazla RAM boşaltır.", C.DIM)


# ---------- 3) Python / Pydroid önbellek temizliği ----------
def clean_python_cache() -> None:
    header("PYTHON & PYDROID ÖNBELLEK TEMİZLİĞİ")

    targets: list[Path] = []
    candidates = [
        Path.home(),
        Path("/sdcard/qpython"),
        Path("/sdcard/Pydroid3"),
        Path("/data/data/ru.iiec.pydroid3/cache"),
        Path("/data/user/0/ru.iiec.pydroid3/cache"),
        Path("/tmp"),
    ]
    for base in candidates:
        if not base.exists() or not os.access(base, os.R_OK):
            continue
        for root, dirs, files in os.walk(base, onerror=lambda e: None):
            for d in list(dirs):
                if d in ("__pycache__", ".pytest_cache", ".mypy_cache"):
                    targets.append(Path(root) / d)
                    dirs.remove(d)
            for fn in files:
                if fn.endswith((".pyc", ".pyo")):
                    targets.append(Path(root) / fn)

    total = 0
    removed = 0
    for t in targets:
        try:
            if t.is_dir():
                size = sum(f.stat().st_size for f in t.rglob("*") if f.is_file())
                shutil.rmtree(t, ignore_errors=True)
            else:
                size = t.stat().st_size
                t.unlink(missing_ok=True)
            total += size
            removed += 1
        except OSError:
            continue

    if removed == 0:
        cprint("  ✓ Silinecek önbellek yok — Pydroid temiz ✨", C.G)
        cprint("  ℹ Diğer uygulamaların önbelleğine Android sandbox erişim vermez.", C.DIM)
        cprint("    Sistem önbelleği için: Ayarlar → Depolama → Önbelleği temizle", C.DIM)
    else:
        cprint(f"  ✓ {removed} öğe silindi  ({human_size(total)} kazanıldı)", C.G)


# ---------- 4) Junk dosya tarayıcı ----------
JUNK_EXT = (".tmp", ".log", ".bak", ".crdownload", ".part", ".dmp", ".trace")
JUNK_DIRS = (".thumbnails", ".cache", "Logs", "log", "tmp", "bugreports", ".trashed")
OLD_DOWNLOAD_EXT = (".apk", ".zip", ".rar", ".7z", ".iso", ".dmg")
OLD_DAYS = 30


def scan_junk(do_delete: bool) -> None:
    header(f"{'JUNK SİL' if do_delete else 'JUNK TARA'}")
    root = sdcard_root()
    cprint(f"Tarama kökü: {root}", C.DIM)
    cprint(f"Eski-büyük arşiv eşiği: {OLD_DAYS} gün, .apk/.zip/.rar...\n", C.DIM)

    now = time.time()
    found: list[tuple[Path, int]] = []
    download_dir = (root / "Download").resolve()

    for r, dirs, files in os.walk(root, onerror=lambda e: None):
        rp = Path(r)
        if any(part.startswith(".") and part not in (".thumbnails", ".cache", ".trashed") for part in rp.parts):
            dirs[:] = []
            continue
        if rp.name in JUNK_DIRS:
            try:
                size = sum(f.stat().st_size for f in rp.rglob("*") if f.is_file())
                if size > 0:
                    found.append((rp, size))
            except OSError:
                pass
            dirs[:] = []
            continue
        in_download = str(rp.resolve()).startswith(str(download_dir))
        for fn in files:
            p = rp / fn
            low = fn.lower()
            try:
                st = p.stat()
            except OSError:
                continue
            if low.endswith(JUNK_EXT):
                found.append((p, st.st_size))
            elif in_download and low.endswith(OLD_DOWNLOAD_EXT):
                age_days = (now - st.st_mtime) / 86400
                if age_days >= OLD_DAYS:
                    found.append((p, st.st_size))

    if not found:
        cprint("  Junk bulunamadı. Telefonun zaten temiz görünüyor ✨", C.G)
        return

    found.sort(key=lambda x: -x[1])
    total = sum(s for _, s in found)
    for p, s in found[:25]:
        cprint(f"  {human_size(s):>10}  {p}", C.DIM)
    if len(found) > 25:
        cprint(f"  ... +{len(found) - 25} öğe daha", C.DIM)
    cprint(f"\nToplam: {len(found)} öğe / {human_size(total)}", C.Y)

    if do_delete:
        ans = input(f"\n{C.RD}Bunları silmek istiyor musun? (evet/hayır): {C.R}").strip().lower()
        if ans in ("e", "evet", "y", "yes"):
            ok = 0
            saved = 0
            for p, s in found:
                try:
                    if p.is_dir():
                        shutil.rmtree(p, ignore_errors=True)
                    else:
                        p.unlink(missing_ok=True)
                    ok += 1
                    saved += s
                except OSError:
                    continue
            cprint(f"  ✓ {ok} öğe silindi ({human_size(saved)} kazanıldı)", C.G)
        else:
            cprint("  İptal edildi.", C.Y)


# ---------- 5) Büyük & eski dosya bulucu ----------
def find_large_old() -> None:
    header("BÜYÜK & ESKİ DOSYALAR")
    root = sdcard_root() / "Download"
    if not root.exists():
        root = sdcard_root()
    cprint(f"Kök: {root}\n", C.DIM)

    now = time.time()
    items: list[tuple[Path, int, float]] = []
    for r, _, files in os.walk(root, onerror=lambda e: None):
        for fn in files:
            p = Path(r) / fn
            try:
                st = p.stat()
            except OSError:
                continue
            if st.st_size >= 25 * 1024 * 1024:
                items.append((p, st.st_size, st.st_mtime))

    if not items:
        cprint("  25MB üzeri dosya yok.", C.G)
        return

    items.sort(key=lambda x: -x[1])
    for p, s, m in items[:20]:
        age_days = (now - m) / 86400
        tag = C.RD if age_days > 60 else (C.Y if age_days > 14 else C.DIM)
        cprint(f"  {human_size(s):>10}  ({age_days:5.0f}g önce)  {p}", tag)
    cprint("\nİpucu: 60+ gündür dokunulmamış büyük dosyaları manuel sil.", C.CY)


# ---------- 6) Ayarlar kısayolları ----------
INTENTS = [
    ("Depolama ayarları", "android.settings.INTERNAL_STORAGE_SETTINGS"),
    ("Pil & güç", "android.settings.BATTERY_SAVER_SETTINGS"),
    ("Pil kullanımı", "android.intent.action.POWER_USAGE_SUMMARY"),
    ("Uygulama listesi", "android.settings.APPLICATION_SETTINGS"),
    ("Geliştirici seçenekleri", "android.settings.APPLICATION_DEVELOPMENT_SETTINGS"),
    ("Bellek ayarı", "android.settings.MEMORY_CARD_SETTINGS"),
]


def open_settings_menu() -> None:
    header("AYARLAR KISAYOLLARI")
    for i, (name, _) in enumerate(INTENTS, 1):
        cprint(f"  {i}) {name}", C.CY)
    cprint("  0) Geri", C.DIM)
    sel = input(f"\n{C.B}Seçim: {C.R}").strip()
    if not sel.isdigit() or int(sel) == 0:
        return
    idx = int(sel) - 1
    if 0 <= idx < len(INTENTS):
        name, action = INTENTS[idx]
        rc, out = run_shell(["am", "start", "-a", action])
        if rc == 0:
            cprint(f"  ✓ '{name}' açılıyor...", C.G)
        else:
            cprint(f"  ⚠  Açılamadı ({rc}): {out[:80]}", C.RD)


# ---------- 7) Hız ipuçları ----------
TIPS = [
    "Geliştirici Seçenekleri'nde Animation/Transition/Animator ölçeklerini 0.5x yap → arayüz hızlanır.",
    "Kullanmadığın uygulamaları arka planda durdur (Ayarlar → Uygulamalar → Pil → Sınırla).",
    "Kullanılmayan büyük uygulamaları kaldır; <2 GB boş alan cihazı yavaşlatır.",
    "Otomatik senkronizasyonu Hesaplar menüsünden gerekmeyen hesaplar için kapat.",
    "Canlı duvar kağıdı ve aşırı widget kullanımı RAM'i sürekli yer; kaldır.",
    "Cihaz 60°C üstüne çıktığında CPU otomatik kısılır → kılıfı çıkar, soğut.",
    "Haftada bir telefonu yeniden başlat; sızıntı yapan süreçleri sıfırlar.",
    "Tarayıcılarda biriken sekmeler RAM yer; kullanılmayanları kapat.",
]


def show_tips() -> None:
    header("HIZ İPUÇLARI")
    for i, t in enumerate(TIPS, 1):
        cprint(f"  {i}. {t}", C.CY)


# ---------- 8) Tek tuş 'tüm optimizasyonları çalıştır' ----------
def run_all() -> None:
    show_device_info()
    trim_memory()
    clean_python_cache()
    scan_junk(do_delete=False)
    cprint("\n→ Junk silmek istersen menüden 5'i seç.", C.Y)


# ---------- Menü ----------
def menu() -> None:
    while True:
        cprint("\n" + "═" * 44, C.M)
        cprint("   ANDROID HIZLANDIRICI  ·  Pydroid 3", C.B + C.M)
        cprint("═" * 44, C.M)
        items = [
            ("1", "Cihaz durumunu göster"),
            ("2", "RAM temizle (trim + GC)"),
            ("3", "Python/Pydroid önbelleğini sil"),
            ("4", "Junk dosyaları TARA"),
            ("5", "Junk dosyaları SİL"),
            ("6", "Büyük & eski dosyaları listele"),
            ("7", "Ayarlar kısayolları"),
            ("8", "Hız ipuçları"),
            ("9", "TÜMÜNÜ çalıştır (önerilen)"),
            ("0", "Çıkış"),
        ]
        for k, v in items:
            cprint(f"  {C.B}{k}{C.R}) {v}", C.CY)
        sel = input(f"\n{C.B}Seçim: {C.R}").strip()

        try:
            if sel == "1":
                show_device_info()
            elif sel == "2":
                trim_memory()
            elif sel == "3":
                clean_python_cache()
            elif sel == "4":
                scan_junk(do_delete=False)
            elif sel == "5":
                scan_junk(do_delete=True)
            elif sel == "6":
                find_large_old()
            elif sel == "7":
                open_settings_menu()
            elif sel == "8":
                show_tips()
            elif sel == "9":
                run_all()
            elif sel == "0":
                cprint("\nHoşça kal! 👋", C.G)
                return
            else:
                cprint("Geçersiz seçim.", C.RD)
        except KeyboardInterrupt:
            cprint("\nİptal edildi.", C.Y)
        except Exception as e:
            cprint(f"Hata: {e}", C.RD)


if __name__ == "__main__":
    if not sys.platform.startswith("linux"):
        cprint("Uyarı: Bu script Android (Linux çekirdeği) için tasarlandı.", C.Y)
    menu()
