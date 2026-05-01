#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
karar_zinciri.py — POZİSYON KARARI ZİNCİRİ KEŞFİ (v3 KURU)

NE YAPAR:
  Klasördeki .py dosyalarını içeriklerine göre sınıflandırır,
  bağımlılık grafiğinden çalıştırma sırasını çıkarır,
  öneriyi ekrana yazdırır.

NE YAPMAZ:
  Hiçbir dosyayı ÇALIŞTIRMAZ. Hiçbir dosyayı SİLMEZ veya DEĞİŞTİRMEZ.
  Sıralamayı sen okur, dosyaları manuel çalıştırırsın.

KURALLAR:
  1. Hiçbir dosya adı HARDCODE değil
  2. Roller davranışsal göstergelerden çıkarılır
  3. Sıra bağımlılık grafiğinden çıkarılır
  4. Self-recursion: script kendi __file__'ini taramaz

Kullanım:
    python karar_zinciri.py
    python karar_zinciri.py --klasor /path/to/klasor
"""

import os
import sys
import ast
import re
import argparse
from pathlib import Path
from collections import defaultdict, deque

DEFAULT_FOLDER = "/storage/emulated/0/Download"

# ══════════════════════════════════════════════════════════════
# DAVRANIŞSAL GÖSTERGELER (DOSYA ADI YOK — DAVRANIŞ KANITI)
# ══════════════════════════════════════════════════════════════

GOSTERGELER = {
    # FETCH: HTTP isteği + finansal API endpoint
    "veri_ceker": [
        (r"requests\.(get|post)\s*\([^)]*(binance|coinglass|bybit|okx)", 5),
        (r"urlopen\s*\([^)]*(binance|coinglass)", 5),
        (r"https?://[^\"']*(fapi|api)\.binance", 4),
        (r"https?://[^\"']*coinglass", 4),
        (r"['\"]/?fapi/v1/(klines|openInterest|fundingRate|premiumIndex)", 4),
        (r"['\"]/?api/v3/(klines|ticker)", 3),
    ],
    # JSON IO
    "json_yazar": [
        (r"json\.dump\s*\(", 3),
        (r"with\s+open\s*\([^)]*\.json[^)]*['\"]w", 3),
    ],
    "json_okur": [
        (r"json\.load\s*\(", 3),
        (r"with\s+open\s*\([^)]*\.json[^)]*['\"]r", 2),
    ],
    # PY kaynak yazma (INJECT, RECORD)
    "py_yazar": [
        (r"with\s+open\s*\([^)]*\.py[^)]*['\"]w", 4),
        (r"\.replace\s*\([^)]*\)\s*\.replace", 2),
        (r"\.bak['\"]?\s*[,)]", 2),
    ],
    # Skorlama altyapısı (DECIDE_PRIMARY)
    "skorlar": [
        (r"def\s+score_\w+\s*\(", 3),
        (r"def\s+compute_scorecard\s*\(", 5),
        (r"def\s+leading_decision\s*\(", 5),
        (r"def\s+apply_regime_filter\s*\(", 5),
        (r"REGIME_ADX_THRESHOLD\s*=", 4),
        (r"WEIGHTS\s*=\s*\{[^}]*K\d+", 3),
    ],
    # Konsensüs sabitleri (DECIDE_CONSENSUS)
    "konsensus": [
        (r"CONSENSUS_MIN_MARGIN\s*=", 5),
        (r"CONSENSUS_DIKKATLI_THR\s*=", 5),
        (r"SHORT_ONLY_MODE\s*=", 4),
        (r"DDF_OK", 4),
        (r"FIX5_H1_THRESHOLD|FIX6_VOL_RATIO|FIX6_LS_OPP_THR|FIX6_H4_THRESHOLD", 4),
    ],
    # Seviye hesaplama (LEVELS)
    "seviye_hesaplar": [
        (r"def\s+calc_entry_levels", 5),
        (r"R:R\s*\(TP[12]\)", 4),
        (r"BE\s*TET[Iİ]K|breakeven", 3),
        (r"15m\s*GİRİŞ.*Elder", 3),
        (r"HİBRİT\s*GİRİŞ|HIBRIT\s*GIRIS", 3),
        (r"ATR\s*[xX×]\s*[\d\.]+", 2),
    ],
    # Run kayıt (RECORD)
    "run_kaydeder": [
        (r"RUN_DATA\s*=\s*\{", 5),
        (r"snapshot\s*otomati", 3),
        (r"placeholder\s*['\"]?MM-DD\s*HH:MM", 3),
    ],
    # Sürekli döngü (MONITOR)
    "surekli_calisir": [
        (r"while\s+True\s*:[\s\S]{0,500}time\.sleep\s*\(\s*\d{2,}", 5),
        (r"schedule\.every\s*\(", 4),
        (r"15dk\s*sonra\s*tekrar", 4),
        (r"OTOMATİK\s*MOD|OTOMATIK\s*MOD", 3),
    ],
    # Tarihsel veri sahibi (büyük veri tablosu = DECIDE_PRIMARY çekirdeği)
    "tarihsel_veri": [
        (r"^HISTORICAL_DATA\s*=\s*\{", 6),
    ],
    # Karar yazdırma (çıktı imzası)
    "yazdirir_primary": [
        (r"print\s*\([^)]*KATMAN\s*[08]", 4),
        (r"print\s*\([^)]*pozisyon\s*yok", 4),
        (r"print_regime_filter|print_final_decision", 5),
    ],
    "yazdirir_consensus": [
        (r"print\s*\([^)]*MARGIN\s*[:=]", 3),
        (r"print\s*\([^)]*DDF[_\s]*OK", 3),
        (r"print\s*\([^)]*KARAR\s*MOTORU", 3),
    ],
    "yazdirir_levels": [
        (r"print\s*\([^)]*L[İI]M[İI]T\s*G[İI]R[İI][ŞS]", 3),
        (r"print\s*\([^)]*ENTRY\s*TRIGGER", 3),
    ],
}


def py_dosyalari_bul(klasor, kendi_yolu=None):
    """Klasördeki .py dosyalarını listele. Script kendi __file__'ini hariç tutar."""
    p = Path(klasor)
    if not p.is_dir():
        return []
    kendi_resolved = Path(kendi_yolu).resolve() if kendi_yolu else None
    sonuc = []
    for f in p.iterdir():
        if not (f.is_file() and f.suffix == ".py" and not f.name.startswith(".")):
            continue
        # Self-exclude: script kendisini analiz etmesin
        if kendi_resolved and f.resolve() == kendi_resolved:
            continue
        sonuc.append(f)
    return sorted(sonuc)


def icerik_oku(path, max_byte=2_000_000):
    try:
        size = path.stat().st_size
        if size > max_byte:
            with open(path, "rb") as f:
                bas = f.read(1_000_000)
                f.seek(-min(200_000, size - 1_000_000), 2)
                son = f.read()
            return (bas + b"\n# ...\n" + son).decode("utf-8", errors="ignore")
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def ana_blok_var_mi(icerik):
    return bool(re.search(r"if\s+__name__\s*==\s*['\"]__main__['\"]", icerik))


def referans_edilen_pyler(icerik, klasor_dosyalari):
    """Bu dosya klasördeki HANGİ .py'yi okuyor/yazıyor (gerçek IO bağlamı)."""
    okunan, yazilan = set(), set()
    for hedef in klasor_dosyalari:
        ad = hedef.name
        if ad not in icerik:
            continue
        for m in re.finditer(re.escape(ad), icerik):
            bas = max(0, m.start() - 80)
            son = min(len(icerik), m.end() + 80)
            baglam = icerik[bas:son]
            if re.search(r"open\s*\([^)]*" + re.escape(ad) + r"[^)]*['\"]w", baglam):
                yazilan.add(ad)
            elif re.search(r"shutil\.copy", baglam):
                yazilan.add(ad)
            elif re.search(r"\.replace\s*\([^)]*" + re.escape(ad), baglam):
                yazilan.add(ad)
            elif re.search(r"open\s*\([^)]*" + re.escape(ad) + r"[^)]*['\"]r", baglam):
                okunan.add(ad)
            elif re.search(r"read_text|json\.load|ast\.parse", baglam):
                okunan.add(ad)
            elif re.search(r"subprocess\.\w+\s*\([^)]*" + re.escape(ad), baglam):
                okunan.add(ad)
            else:
                okunan.add(ad)  # belirsizse okuyucu say (güvenli)
    return okunan, yazilan


def referans_edilen_json(icerik):
    okunan, yazilan = set(), set()
    for m in re.finditer(r"['\"]([\w\-/\.]+\.json)['\"]", icerik):
        ad = os.path.basename(m.group(1))
        bas = max(0, m.start() - 80)
        son = min(len(icerik), m.end() + 80)
        baglam = icerik[bas:son]
        if re.search(r"json\.dump|['\"]w", baglam):
            yazilan.add(ad)
        else:
            okunan.add(ad)
    return okunan, yazilan


def gostergeleri_skorla(icerik):
    skorlar = {}
    for ad, desenler in GOSTERGELER.items():
        skor = 0
        for desen, agirlik in desenler:
            bulgular = re.findall(desen, icerik, re.IGNORECASE | re.MULTILINE)
            if bulgular:
                skor += agirlik * min(len(bulgular), 3)
        skorlar[ad] = skor
    return skorlar


def dosyalari_analiz_et(dosyalar):
    profiller = {}
    for path in dosyalar:
        icerik = icerik_oku(path)
        if not icerik.strip():
            continue
        py_oku, py_yaz = referans_edilen_pyler(icerik, dosyalar)
        json_oku, json_yaz = referans_edilen_json(icerik)
        profiller[path] = {
            "icerik": icerik,
            "gostergeler": gostergeleri_skorla(icerik),
            "py_okur": py_oku,
            "py_yazar": py_yaz,
            "json_okur": json_oku,
            "json_yazar": json_yaz,
            "ana_blok": ana_blok_var_mi(icerik),
            "boyut": len(icerik),
        }
    return profiller


def rol_belirle(profil):
    """Davranışsal göstergeleri rol skorlarına dönüştür."""
    g = profil["gostergeler"]
    rol_skorlari = {
        "FETCH": g["veri_ceker"] * 1.0 + g["json_yazar"] * 0.5 - g["skorlar"] * 0.5,
        "INJECT": g["json_okur"] * 0.8 + g["py_yazar"] * 1.2 - g["veri_ceker"] * 0.5 - g["skorlar"] * 0.5,
        "DECIDE_PRIMARY": g["skorlar"] * 1.0 + g["tarihsel_veri"] * 1.0 + g["yazdirir_primary"] * 1.2,
        "DECIDE_CONSENSUS": g["konsensus"] * 1.5 + g["yazdirir_consensus"] * 1.0 - g["skorlar"] * 0.3,
        "LEVELS": g["seviye_hesaplar"] * 1.5 + g["yazdirir_levels"] * 1.0 - g["skorlar"] * 0.3,
        "RECORD": g["run_kaydeder"] * 1.5 + g["py_yazar"] * 0.3,
        "MONITOR": g["surekli_calisir"] * 1.5,
    }
    sirali = sorted(rol_skorlari.items(), key=lambda x: -x[1])
    en_iyi, skor = sirali[0]
    fark = skor - (sirali[1][1] if len(sirali) > 1 else 0)
    if skor < 4 or fark < 2:
        return None, skor, fark, rol_skorlari
    return en_iyi, skor, fark, rol_skorlari


def bagimlilik_grafigi_kur(profiller):
    """Yazıcı → okuyucu kenarları (gerçek dosya IO bağımlılığı)."""
    kenarlar = defaultdict(set)
    in_derece = defaultdict(int)

    for yazici, prof_y in profiller.items():
        yazdiklar = {("py", a) for a in prof_y["py_yazar"]} | \
                    {("json", a) for a in prof_y["json_yazar"]}
        if not yazdiklar:
            continue
        for okuyucu, prof_o in profiller.items():
            if yazici == okuyucu:
                continue
            okuduklar = {("py", a) for a in prof_o["py_okur"]} | \
                        {("json", a) for a in prof_o["json_okur"]}
            if yazdiklar & okuduklar and okuyucu not in kenarlar[yazici]:
                kenarlar[yazici].add(okuyucu)
                in_derece[okuyucu] += 1

    return kenarlar, in_derece


def davranis_dalgasi(profil):
    """
    Bir dosyanın hangi 'dalgada' çalışması gerektiğini davranışından çıkar.
    Düşük dalga numarası = önce çalışır.

    Dalga 1 (YAZICI):     Veri üretir, dosya yazar  (FETCH, INJECT, RECORD)
    Dalga 2 (KARAR_TEMEL): Geniş bilgi okuyup birincil karar verir (DECIDE_PRIMARY)
                            Kanıt: çok sayıda skorlama fonksiyonu + tarihsel veri
    Dalga 3 (KARAR_USTU):  Birincil kararı baz alıp konsensüs/eylem üretir
                            Kanıt: konsensüs sabitleri VEYA seviye hesaplama
    Dalga 4 (DÖNGÜ):      Sürekli çalışan
    """
    g = profil["gostergeler"]

    # Dalga 4: Sürekli döngü
    if g["surekli_calisir"] >= 4:
        return 4

    # Dalga 1: Veri yazıcı (FETCH json yazar, INJECT .py yazar, RECORD .py yazar)
    yazma_kaniti = g["json_yazar"] + g["py_yazar"]
    if yazma_kaniti >= 3:
        # Ama eğer aynı dosya geniş skorlama da yapıyorsa, bu YAZICI değil DECIDE_PRIMARY
        if g["skorlar"] >= 8 or g["tarihsel_veri"] >= 4:
            return 2  # büyük tarihsel veri sahibi de "yazma" gibi görünebilir, atla
        return 1

    # Dalga 2: Geniş skorlama + tarihsel veri = yön kararı çekirdeği
    if g["skorlar"] >= 8 or g["tarihsel_veri"] >= 4 or g["yazdirir_primary"] >= 4:
        return 2

    # Dalga 3: Konsensüs sabitleri VEYA seviye hesaplama (üst katman)
    if g["konsensus"] >= 4 or g["seviye_hesaplar"] >= 4 or \
       g["yazdirir_consensus"] >= 3 or g["yazdirir_levels"] >= 3:
        return 3

    # Dalga 3: RUN kayıt da üst katman (karar sonrası)
    if g["run_kaydeder"] >= 4:
        return 3

    # Belirsiz: orta
    return 3


def topolojik_sirala(profiller, kenarlar, in_derece):
    """
    Sıralama mantığı:
      1. Her dosyanın 'davranış dalgasını' belirle (1=yazıcı, 2=karar temel, 3=karar üstü, 4=döngü)
      2. Her dalga içinde topo-sort (yazıcı → okuyucu) uygula
      3. Dalgalar sırayla ekle (1, 2, 3, 4)
    """
    dugumler = list(profiller.keys())

    # Dalgalara böl
    dalgalar = defaultdict(list)
    for d in dugumler:
        dalgalar[davranis_dalgasi(profiller[d])].append(d)

    nihai_sira = []
    for dalga_no in sorted(dalgalar.keys()):
        dalga_dugumleri = dalgalar[dalga_no]
        # Bu dalga içinde topo-sort
        derece = {d: 0 for d in dalga_dugumleri}
        for kaynak, hedefler in kenarlar.items():
            if kaynak not in dalga_dugumleri:
                continue
            for h in hedefler:
                if h in dalga_dugumleri:
                    derece[h] = derece.get(h, 0) + 1

        kuyruk = deque([d for d in dalga_dugumleri if derece[d] == 0])
        dalga_sira = []
        while kuyruk:
            adaylar = list(kuyruk)
            kuyruk.clear()
            # Aynı dalga içi tiebreaker: yazıcılık + boyut
            adaylar.sort(key=lambda d: (
                -(len(profiller[d]["json_yazar"]) + len(profiller[d]["py_yazar"])),
                profiller[d]["boyut"],
            ))
            for d in adaylar:
                dalga_sira.append(d)
                for komsu in kenarlar.get(d, []):
                    if komsu in derece:
                        derece[komsu] -= 1
                        if derece[komsu] == 0:
                            kuyruk.append(komsu)

        # Cycle veya bağımsız kalanlar
        for d in dalga_dugumleri:
            if d not in dalga_sira:
                dalga_sira.append(d)

        nihai_sira.extend(dalga_sira)

    return nihai_sira


# ══════════════════════════════════════════════════════════════
# (Çalıştırma + karar fonksiyonları KALDIRILDI — bu sadece keşif scripti)
# ══════════════════════════════════════════════════════════════


def cizgi(k="═", n=72):
    return k * n


def cokul_aday_uyari(rol_atamalari):
    """Aynı role birden fazla dosya atanmışsa uyarı listesi döndür."""
    rol_dosyalari = defaultdict(list)
    for path, rol in rol_atamalari.items():
        if rol:
            rol_dosyalari[rol].append(path)
    uyarilar = []
    for rol, dosyalar in rol_dosyalari.items():
        if len(dosyalar) > 1:
            uyarilar.append((rol, dosyalar))
    return uyarilar


def ana(klasor, kendi_yolu):
    print(cizgi())
    print(f"  KARAR ZİNCİRİ KEŞİF MODU — {klasor}")
    print(f"  (Hiçbir dosya çalıştırılmaz / silinmez / değiştirilmez)")
    print(cizgi())

    dosyalar = py_dosyalari_bul(klasor, kendi_yolu)
    if not dosyalar:
        print("\n  HATA: .py yok.")
        return 1
    print(f"\n[1] {len(dosyalar)} adet .py taranıyor (kendi script hariç)...")

    profiller = dosyalari_analiz_et(dosyalar)

    print(f"\n[2] Davranışsal rol tespiti:")
    rol_atamalari = {}
    for path, prof in profiller.items():
        rol, skor, fark, hepsi = rol_belirle(prof)
        rol_atamalari[path] = rol
        bayrak = "✓" if rol else "?"
        ana_str = "[main]" if prof["ana_blok"] else "      "
        rol_str = rol or "(belirsiz)"
        # Belirsiz olanlar için en yakın 2 rol göster
        ek = ""
        if not rol:
            sirali = sorted(hepsi.items(), key=lambda x: -x[1])[:2]
            ek = f"  [yakın: {sirali[0][0]}={sirali[0][1]:.1f}, {sirali[1][0]}={sirali[1][1]:.1f}]"
        print(f"    {bayrak} {ana_str} {path.name:32s} → {rol_str:20s} (skor {skor:.1f}, fark {fark:+.1f}){ek}")

    # Çoklu aday uyarısı
    uyarilar = cokul_aday_uyari(rol_atamalari)
    if uyarilar:
        print(f"\n[!] AYNI ROLE BİRDEN FAZLA DOSYA — hangisini kullanacağına sen karar ver:")
        for rol, dosyalar in uyarilar:
            print(f"    {rol}:")
            # En büyük skorlu = en iyi aday (ama doğru olmayabilir)
            adaylar = [(p, profiller[p]["boyut"]) for p in dosyalar]
            for p, boyut in sorted(adaylar, key=lambda x: -x[1]):
                print(f"      - {p.name}  ({boyut:,} byte)")

    kenarlar, in_derece = bagimlilik_grafigi_kur(profiller)

    print(f"\n[3] Bağımlılık kenarları (yazıcı → okuyucu):")
    if not kenarlar:
        print(f"    (kenar yok — dosyalar IO ile bağımsız)")
    else:
        # Aynı kaynaktan çok kenar varsa şüpheli — uyarı
        kaynak_sayisi = {}
        for kaynak, hedefler in kenarlar.items():
            kaynak_sayisi[kaynak] = len(hedefler)
        for kaynak, hedefler in kenarlar.items():
            for h in hedefler:
                supheli = " [şüpheli — çok kenar]" if kaynak_sayisi[kaynak] > 5 else ""
                print(f"    {kaynak.name} → {h.name}{supheli}")

    sira_path = topolojik_sirala(profiller, kenarlar, in_derece)
    sira_oneri = [p for p in sira_path
                  if profiller[p]["ana_blok"] and rol_atamalari[p] is not None]

    print(f"\n[4] ÖNERİLEN ÇALIŞTIRMA SIRASI ({len(sira_oneri)} dosya):")
    print(f"    NOT: Sen kararı ver. Yanlış sınıflandırma görürsen atla.")
    print()
    for i, p in enumerate(sira_oneri, 1):
        print(f"    {i}. {p.name:32s} ({rol_atamalari[p]})")

    atlanan = [p for p in sira_path if p not in sira_oneri]
    if atlanan:
        print(f"\n  Sıraya alınmadı ({len(atlanan)}):")
        for p in atlanan:
            sebep = "ana blok yok" if not profiller[p]["ana_blok"] else "rol belirsiz"
            print(f"    - {p.name}  ({sebep})")

    print(f"\n{cizgi('═')}")
    print(f"  ÖNERİLEN ELLE ÇALIŞTIRMA AKIŞI")
    print(cizgi('═'))
    print()
    print(f"  Bu öneri sadece bir başlangıç noktasıdır. Kontrol et, gerekirse düzelt.")
    print(f"  Hatalı atama görürsen o dosyayı listeden çıkar veya sıranı manuel değiştir.")
    print()
    if uyarilar:
        print(f"  ⚠ Çoklu aday uyarıları yukarıda listelendi — sen seç.")
    print()
    print(f"  Pydroid'da:")
    print(f"    1. Yukarıdaki sırada her dosyayı sırayla Play et")
    print(f"    2. Her adımın çıktısına bak:")
    print(f"       - DECIDE_PRIMARY (yön kartı) → NOTR derse: DUR")
    print(f"       - DECIDE_CONSENSUS (karar motoru) → MARGIN/DDF eşik altıysa: DUR")
    print(f"       - LEVELS → seviyeleri al")
    print(f"    3. Pozisyon açtıysan RECORD adımını çalıştır")
    print()
    print(cizgi('═'))
    return 0


def main():
    p = argparse.ArgumentParser(description="Karar zinciri keşif (kuru mod, sadece öneri)")
    p.add_argument("--klasor", default=DEFAULT_FOLDER,
                   help=f"Tarama klasörü (varsayılan: {DEFAULT_FOLDER})")
    args = p.parse_args()
    return ana(args.klasor, kendi_yolu=__file__)


if __name__ == "__main__":
    sys.exit(main())
