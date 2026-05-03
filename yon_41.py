#!/usr/bin/env python3
"""
YON-41 SCORECARD — 7 KATMANLI + IKILI OLCUM + V-RISK + GIRIS KALITESI FILTRELERI

ISIMLENDIRME (P78'de degistirildi):
  Eski konvansiyon: yon_41.py
  Yeni konvansiyon: yon_41.py (versiyon = son R numarasi)
  Run eklemesi → dosya adi ayni kalir (R42 eklendiginde de yon_41.py)
  Yapisal guncelleme → yon_42.py, yon_43.py ...
  Log: yon_log.json

YON-5 DEGISIKLIKLER — P60:
  [YAPISAL] FİYAT DEPLASMANI FİLTRESİ (LONG_ANA ERKEN):
    LONG_ANA ERKEN + 4h%MA30 > 4.0% → GİRME (LONG_ANA_DEPLASMAN).
    P60 eşik=3.0% → P67 eşik=4.0% (grid search: 1/3→3/3 doğru koruma).
    R32 bloke (+4.31%), R33 geçer (+3.50%), R36 geçer (+3.20%). 0 regresyon.

YON-5 DEGISIKLIKLER — P57:
  [YAPISAL] LEADING-PRIMARY KARAR SİSTEMİ:
    Combo P56→P57: Leading sinyal varsa → yön+karar Leading'den. Sinyal yoksa → GİRME.
    Backtest: 18/18=%100, 0 regresyon. COMBO_TABLE dead code.
    Detay: yon_4 P57 changelog'a bak.

YON-5 DEGISIKLIKLER — P55:
  [YAPISAL] LEADING KARAR SİSTEMİ:
    Öncü sinyaller (whale, OI_30h, LS_1h) ile PREDİKTİF giriş kararı.
    SC'den ÖNCE yazdırılır. Kurallar yon_4 ile aynı.
    Backtest: 17/17=%100, kapsam %77.
    Açık konular: WP ratio eklenemedi (yapısal bias), LS SMA veri yok,
    funding kontraryan veri yetersiz. Detay: yon_4 docstring.

YON-5 DEGISIKLIKLER (YON-4'ten):
  [YAPISAL] GÜVEN REFORMU (P47):
    Eski: h1↔h4 aynı işaret → YÜKSEK (büyüklük kontrol yok).
    Yeni: aynı işaret + |4h|<0.50 → DÜŞÜK (zayıf 4h, güven hak etmiyor).
    Backtest (R2-R26, 25 run): 5 run güven etiketi düzeltildi, 0 boyut/yön/karar değişikliği.
    Regresyon: SIFIR.
  [BUGFIX] import re modül seviyesine taşındı (latent UnboundLocalError fix).
  [BUGFIX] K4_CVD spot_cvd=0 fix (P48):
    Eski: spot_cvd=0 → score_cvd base=0 → K4 sinyal ölü (weight=0.9 kayıp).
    Yeni: sc=0 + fc>0 → base=+0.5, sc=0 + fc<0 → base=-0.5.
    Backtest (R2-R26, 25 run): SIFIR regresyon.
  [KATMAN-0] REJİM FİLTRESİ (PRODUCTION):
    ADX(14) < 20.5 → RANGING → NOTR zorla (scorecard ne derse desin).
    Backtest: 500 mum (83 gün, 2026-01-12 → 2026-04-05), R2-R24.
    Sonuç: 4/4 yanlış run engellendi, 0 doğru kayıp, %64 → %90 doğruluk.
    Gap analizi: yanlış max ADX=19.8, doğru min ADX=21.3, gap=1.5 puan.
    Eşik=20.5 (gap ortası), sıfır yanlış engel ile maksimum koruma.
    Ek: 4/6 BELIRSIZ run (R17, R18, R21, R22) da engellenirdi.
    CANDLES_4H_REGIME: 500 mum Binance /fapi/v1/klines verisi gömülü.
    Her yeni run'da CANDLES_4H_REGIME güncellenmeli (yeni mumlar ekle).
  [SKORLAMA] compute_scorecard() DEĞİŞMEDİ — regime filter ayrı katman.
  [ÇIKTI] KATMAN 0 tüm katmanlardan önce yazdırılır.

YON-4 DEGISIKLIKLER — P50:
  [SKORLAMA] K13e OI×PRICE 3×3 MATRİS AKTİF (P50):
    Eski: K13_OI_PRICE_DIV w=0.0 (ölü ağırlık, 2×2 divergence mantığı).
    Yeni: K13_OI_PRICE_DIV w=0.3 (3×3 rejim matrisi, domain + backtest).
    Matris: OI{UP/FLAT/DOWN} × P{UP/FLAT/DOWN} → skor.
      OI↓P↓ → +0.80 (kapitülasyon, %100 backtest)
      OI↑P↑ → +0.50 (trend devam, %75)
      OI↑P↓ → -0.50 (trapped long, %67)
      OI↓P↑ →  0.00 (güvenilmez, %50)
    Magnitude scaling: 0.5 taban + 0.5×mag.
    Backtest (25 run, P49 vs P50): 0 yön değişikliği, 0 doğruluk değişikliği.
    Detay dict: regime, oi_dir, p_dir, base, mag compute_tf'den döndürülür.
    Fingerprint: k13_raw + k13_regime eklendi.
    Kaynak: P49 3×3 matris analizi (14 ölçülebilir run, K13e %71 isabet).
  [SKORLAMA] FİYAT HEDEFLERİ KALDIRILDI (P68):
    P50: Eklendi (sabit $300/$1000). P67: V2 ATR bazlı TP'ye geçti.
    P68: compute_price_targets + print_price_targets kaldırıldı.
    Sebep: Karar mekanizmasına katkı sıfır, V2 calc_entry_levels ile çakışma,
    tüm bilgi başka yerlerde mevcut. TP/SL/R:R → entry_trigger_v2 + auto_compact.

YON-4 DEGISIKLIKLER (YON-3-1'den):
  [YAPISAL] YON-3-1 → YON-4 İSİM YÜKSELTMESİ:
    Heatmap tamamen çıkarıldı — veri toplama, skorlama, gözlem HEPSİ kaldırıldı.
    v3a formülü: SC + M15 + M1h + W (4 bileşen, sabit).
    API sinyal backtest (A/B/C): Whale trend %50, OI %44, funding sinyal yok — hiçbiri eklenmedi.
    Mevcut API verisi toplamaya devam (trending piyasa için).
    Heatmap fonksiyonları kodda kaldı (dead code) ama çağrılmıyor.

YON-3-1 DEGISIKLIKLER (YON-3'ten):
  [SKORLAMA] HEATMAP v3a'DAN ÇIKARILDI:
    Backtest (P41, R18-R23): HT yön doğruluğu 1/5=%20.
    v3a HT dahil: 4/6=%67 | v3a HT hariç: 5/6=%83 → HT net zararlı.
    Cluster S/R doğruluğu: 15/60=%25 (AĞIR dahil %27).
    Regresyon testi (14 ölçülebilir run): 0 regresyon.
    Karar: HT oyu ve HT veto production v3a'dan çıkarıldı.
    v3a formülü: SC + M15 + M1h + W (4 bileşen, eskiden 5).
    Heatmap GÖZLEM MODU'nda — çıktıda GRİ bilgi olarak gösterilir.
    Gemini heatmap veri toplama devam eder (per-run gömme).

YON-2-10 DEGISIKLIKLER (YON-2-9'dan):
  [VERİ] PER-RUN API VERİSİ:
    4 Binance API dataseti per-run HISTORICAL_DATA'ya gömüldü:
    - api_whale_account: topLongShortAccountRatio (saatlik, son 30)
    - api_whale_position: topLongShortPositionRatio (saatlik, son 30)
    - api_open_interest: openInterestHist (saatlik, son 30)
    - api_funding_rate: fundingRate (8h periyot, son 10)
    Format: tuple listesi — ("MM-DD HH:MM", value) veya ("MM-DD HH:MM", rate, markPrice)
    Her yeni run'da Eren API verisini yapıştırır, Claude per-run slice'lar ve gömer.
    NOT: whale_acct_ls (anlık snapshot) KORUNUYOR — API saatlik trend verisi farklı granülerlik.
  [VERİ] HEATMAP GEMİNİ FORMAT (R23+):
    Eski: tek upper/lower per görünüm {"upper": X, "upper_w": Y, "lower": X, "lower_w": Y}
    Yeni: multi-cluster {"clusters": [{"fiyat": X, "yon": "ust/alt", "yogunluk": Y, "genislik": Z}], "bos": [...]}
    Gemini 2.5 Pro screenshot analizi ile çıkarılır — renk, genişlik, boş bölge dahil.
    Backward compat: _heatmap_view_to_old_format() adaptörü R18-R22 eski formatı destekler.
    Production heatmap_signal() ve shadow_heatmap_v2() her iki formatla çalışır.
  [SKORLAMA] DEĞİŞİKLİK YOK — salt veri saklama iyileştirmesi.

YON-2-9 DEGISIKLIKLER (YON-2-8'den):
  [SHADOW] HEATMAP V2 — RESEARCH-BASED GÖZLEM MODU:
    Production skorlamasi DEĞİŞMEDİ — v3a eski heatmap_signal() ile çalışır.
    Shadow: 6 görünüm (perp+spot × 15m/1h/4h) research-based formülle hesaplanır.
    Formül: Exponential decay × ATR-adaptif sigma × TF ağırlığı × perp/spot ağırlığı.
    Kaynak: Bookmap, CME 2025, Glassnode, Rallis 2025 SSRN, Easley et al.
    Parametreler: exp(-d/σ), σ=ATR×1.0, TF: 4h=0.45/1h=0.35/15m=0.20, perp=0.80/spot=0.20.
    Concordance: 2/3 TF uyum kontrolü. Kademeli veto: ≤1.5×ATR AĞIR+ duvar.
    Çıktı: Her run'da shadow vs production karşılaştırma tablosu.
    10 run shadow sonra adoption kararı (K8_WHALE ile aynı süreç).
  [VERİ] R23 heatmap_raw eklendi (6 görünüm verisi).
  [SKORLAMA] DEĞİŞİKLİK YOK — production output yon_2-8 ile birebir aynı.

YON-2-8 DEGISIKLIKLER (YON-2-7'den):
  [VERİ] PER-RUN KLİNES SAKLAMA:
    Eski: Klines sadece global CANDLES_4H/1H/15M dizilerinde saklaniyordu.
    Yeni: Her run giris anindaki klines snapshot'ini HISTORICAL_DATA'da saklar.
    Alanlar: klines_15m, klines_1h, klines_4h (her biri tuple listesi).
    Global diziler KORUNUYOR — MFE/MAE motoru bunlara bagimli.
    Amac: Run bazli tekrar uretilebilirlik (reproducibility).
  [VERİ] HEATMAP RAW (6 GÖRÜNÜM):
    Eski: Tek ozet dict (upper/lower_cluster + weight).
    Yeni: 6 ayrı heatmap gorunumu per-run (perp+spot × 15m/1h/4h).
    Alan: heatmap_raw (6 alt-dict: perp_15m, perp_1h, perp_4h, spot_15m, spot_1h, spot_4h).
    Mevcut heatmap (ozet) KORUNUYOR — v3a scoring buna bagimli.
    heatmap_raw → heatmap otomatik turetme fonksiyonu eklendi.
  [SKORLAMA] DEGİSİKLİK YOK — salt veri saklama iyilestirmesi.

YON-2-7 DEGISIKLIKLER (YON-2-6'dan):
  [KATMAN-8] BİRLEŞİK SİNYAL SİSTEMİ (v3a):
    Eski: Kirmizi/yesil sinyal sayma (7 kaynak)
    Yeni: SC + MUM_15m + MUM_1h + WHALE_v2 oylama + HEATMAP (oy + veto)
    Backtest (15 olculebilir run):
      SC tek basina: 9/13 = %69
      v3a birlestik: 13/15 = %87
    KURTARILAN: R13, R14, R15 (SC yanlis → birlestik dogru)
    KAZANILAN: R7 (SC kacin → birlestik dogru)
    BOZULAN: R16 (SC kacin → birlestik yanlis)
    MUM_4h cikarildi (%53 dogruluk = yazi-tura, zararli).
  [HEATMAP] VERİ ALANI + VETO MEKANİZMASI:
    HISTORICAL_DATA'ya heatmap alanlari eklendi (R18-R22).
    Heatmap veto: SC yonunde ≤$300 mesafede AGIR cluster → GIRME.
    4 run'da 3/3 haklı (üst duvar tuttu, fiyat yukarı gidemedi).
    10 run shadow sonra adoption karari.
  [WHALE_V2] SEVİYELİ SİNYAL:
    Eski: monotonic (<1.0 hep SHORT) → sinyal uretmiyordu.
    Yeni: <0.87 = SHORT(-1), 0.87-0.95 = NOTR(0), >0.95 = LONG(+1).
    6/6 aktif sinyal dogru (%83).
  [MUM_ENTRY] GİRİŞ ANI MUM SİNYALİ:
    CANDLES_15M/1H'den entry anindaki mum pattern'i hesaplanir.
    Renk + close pozisyonu + fitil + engulfing + momentum = skor.
    MUM_15m: %80 (10 aktif), MUM_1h: %71 (14 aktif).

YON-2-6 DEGISIKLIKLER (YON-2-5'ten):
  [KATMAN-8] TF KOMBINASYON SINYALI (Sinyal 7):
    Pencere 34'te 27 kombinasyon (3^3) backtest yapildi, 20 run, $1000 MFE.
    Her TF: LONG/SHORT/NOTR (esik +-0.10). 6/27 kombinasyon gorulen.
    Katman 8 artik mevcut run'in TF kombinasyonunu taniyor ve gecmis
    dogruluk oranini sinyal olarak uretiyor.
    Sonuclar:
      S/L/S: 3/3=%100 YESIL  |  L/L/L: 2/2=%100 YESIL
      S/S/S: 3/5=%60 SARI    |  L/L/S: 1/2=%50 KIRMIZI
      N/L/S: 0/1=%0 KIRMIZI  |  Gorulmemis: SARI uyari
    Simetrik patternler (ters yon) de desteklenir.
    _COMBO_HISTORY dict'i yeni run'larla guncellenecek.
  [PROTOKOL] SINYAL OZETI ZORUNLU FORMAT:
    Her sinyal ozetinde 15m, 1h, 4h + Katman 8 karari yazilir.
    15m veya Katman 8 atlanamaz (T1-C ihlali).
  [BACKTEST] TF KOMBINASYON ANALIZI BELGELENDI:
    27 kombinasyon matrisi, 1h bazli 3x3 tablo, ters yon karsilastirmasi
    docstring'e kaydedildi.

YON-2-5 DEGISIKLIKLER (YON-2-4'ten):
  [OLCUM] ACTUAL DEGERLERI YENIDEN HESAPLANDI:
    Eski: "Eren bir sonraki veri gonderdiginde fiyat nerede?" (tutarsiz zamanlama)
    Yeni: "Fiyat giris yonunde $1000'a ulasti mi? Hangisi once?" ($1000 MFE esigi)
    Metod: CANDLES_15M + CANDLES_1H verisi, entry'den sonraki TUM mumlar.
    Eger fiyat +$1000'a da -$1000'a da ulasmadiysa → BELIRSIZ (piyasa hareket etmedi).
    4 run BELIRSIZ: R17, R18, R19, R20 (ranging market, max hareket <$1000).
    Degisen actual'lar:
      R6:  DOWN → UP   (SHORT icin YANLIS — fiyat once $1000 yukari gitti)
      R11: DOWN → UP   (LONG icin DOGRU — fiyat 7h'de $1000 yukari gitti!)
      R13: UP   → DOWN (LONG icin YANLIS — fiyat $1000 yukariya ulasamadi)
      R14: UP   → DOWN (LONG icin YANLIS — ayni)
      R15: DOWN → UP   (SHORT icin YANLIS — fiyat $1000 yukari gitti)
    R11 NOTU: Onceki "yapisal outlier, duzeltilmez" etiketi YANLISTIR.
      R11 aslinda dogru bir LONG cagrisiydi. 7h'de +$1053 MFE.
    Sonuc: Piyasa hareket ettiginde scorecard dogrulugu: 9/13 = %69
      KUCUK BOYUT: 4/4 = %100 (hareket eden runlarda)
      COK KUCUK BOYUT: 4/7 = %57
  [OLCUM] eval_actual BELIRSIZ DESTEGI:
    actual="BELIRSIZ" → label="BELIRSIZ" (ne BASARILI ne BASARISIZ)
    Post-mortem, WF, Layer 8 bu runlari atlar.

YON-2-4 DEGISIKLIKLER (YON-2-3'ten):
  [KATMAN-7B] BENZERLIK MOTORU — P69: KALDIRILDI.
    LOO backtest: top-1 %63 (iddia %100), majority %59 (baseline %56).
    Bilgi üretmeyen katman kaldırıldı.
  [KATMAN-8] SON KARAR (DİNAMİK):
    Tum katmanlari (Danisma, Benzerlik, Whale, Son Runlar, Guven, Bayraklar)
    tarar ve kirmizi/yesil sinyal sayar.
    3+ kirmizi → GIRME, 2 kirmizi → DIKKATLI, 0-1 kirmizi → GIR.
    PRENSIP: GIRME = pozisyon ACMA. TERS YONE GIR ASLA onerilmez.
    Backtest kaynagi: S2 reverse stratejisi %71 — mevcut %82'den kotu.
  [VERI] whale_acct_ls R2-R21 TAMAMLANDI:
    Tum runlar icin topLongShortPositionRatio verisi gomuldu.
    Kaynak: Binance /futures/data/topLongShortPositionRatio
    (Onceki: topLongShortAccountRatio — degistirildi, tutarlilik icin)

YON-2-3 DEGISIKLIKLER (YON-2-2'den):
  [FIX-7] K12_SPOT_CVD w=0 (OLU AGIRLIK):
    18 run'da max |K12*w| = 0.133. Ort = 0.095.
    Pencere 29 backtest: cikarmak 0 regresyon, 0 degisiklik.
    5. olu agirlik: K2, K7, K13, K17, K12.
    Kod KALDIRILMADI — agirlik 0.
  [SHADOW] K8_WHALE GOZLEM MODU:
    Whale position L/S verisi HISTORICAL_DATA'ya ekleniyor (whale_acct_ls).
    Shadow K8_whale skoru hesaplanip ciktiya yaziliyor.
    Scorecard skorunu DEGISTIRMEZ — gozlem modu.
    10 run sonra (R21-R30) yeterli veri → backtest → adoption karari.
    API kaynak: Binance /futures/data/topLongShortPositionRatio

KATMANLAR:
  KATMAN 1: YON — 1h skoru → LONG/SHORT/NOTR (V-RISK dinamik NOTR bolgesi)
  KATMAN 2: GUVEN — 1h↔4h uyumu + |4h| filtre → YUKSEK/DUSUK
  KATMAN 3: BOYUT — Guven + bayraklar + |4h| + |1h| + BEKLE → NORMAL/KUCUK/COK KUCUK
  KATMAN 4: WF KALITE — Son 3 run MAE/MFE → uyari modu
  KATMAN 5: MUM ANALIZI — anlik+onceki mum → fitil/engulfing/momentum/celiski
  KATMAN 6: SON RUN KARSILASTIRMA — son 3 yonlu run ham metrik tablosu (salt veri)
  KATMAN 7: P69 KALDIRILDI (POST-MORTEM & DANISMA — LOO backtest: profil negatif %0)
  KATMAN 7B: P69 KALDIRILDI (BENZERLIK — LOO backtest: majority %59 = baseline)
  KATMAN 8: SON KARAR — tum katmanlari tarar, GIR/DIKKATLI/GIRME uretir (YON-2-4 YENİ)
IKILI OLCUM: Yon (4h fiyat) + Kalite (MAE/MFE < 0.70)

YON-2 DEGISIKLIKLER (YON-1'den):
  [KATMAN-7] POST-MORTEM & DANISMA MOTORU — P69: KALDIRILDI.
    LOO backtest: Profil≥60% teyit %94, ama negatif taraf %0 doğruluk.
    Meta-skora yanlış sinyal besliyordu. Tüm fonksiyonlar kaldırıldı.

V9 DEGISIKLIKLER (V8'den):
  [FIX-5] |1h| GIRIS KALITESI FILTRESI ("COK GEC"):
    |1h| > 1.50 → COK KUCUK BOYUT
    Mekanizma: Cogu kriter ayni yonde uyumlu = hareket zaten olmus, giris gec.
    Backtest: R10(2.40), R11(1.94), R12(1.71) yakalandi.
    Regresyon: 0 (en yakin BASARILI: R4 |1h|=1.03, gap=0.47)
    False positive: 0
  [FIX-6] BEKLE SINYALI ("HENUZ DEGIL"):
    Kosul: vol_1h < %50 avg VE LS_opposition > 0.50 VE |4h| < 1.50
    Mekanizma: Hacim yok + market ters pozisyonda + makro zayif
    = market maker sweep olasiligi yuksek, girisi ertele.
    Cikti: direction degismez, boyut=COK KUCUK, "BEKLE" flag eklenir.
    Backtest: R17 yakalandi. R15 makro override (|4h|=2.17) ile korundu.
    Regresyon: 0
    False positive: 0
  Kombine: 4/5 GIRIS_KOTU yakalandi, 0 false positive. Kalan: R5 (zayif sinyal).

  [KATMAN-6] SON RUN KARSILASTIRMA (YON-1):
    Son 3 yonlu run'in ham metriklerini mevcut run ile yan yana gosterir.
    Metrikler: vol_ratio, LS_raw, LS_opp, |1h|, |4h|, K6_15m, K6_1h
    Sonuc etiketleri + MAE/MFE oranlari eklenir.
    Salt veri — otomatik UYARI yok (FIX-5/6 ile %100 cakisma nedeniyle kaldirildi).
    Boyutu degistirmez.

YON-1 DEGISIKLIKLER (V9'dan):
  - Dosya: yeni_scorecard_12.py → yon_1.py
  - Versiyon etiketi: V9 → YON-1
  - Log: yeni_scorecard_12_log.json → yon_1_log.json
  - Katman 6 eklendi (salt tablo, UYARI yok)
  - Backtest: R2-R17 tum skorlar, yonler, boyutlar birebir ayni

V8 DEGISIKLIKLER (V7'den):
  [FIX-4] V-RISK DINAMIK NOTR BOLGESI:
    Karsi-sinyal kaynaklari: K6_15m, K6_1h, h15 yon, LIK flag
    Zayif sinyal (|1h| < genisletilmis NOTR) + guclu karsi-sinyal → NOTR
    Formul: effective_notr = 0.10 + min(0.25, counter_score * 0.25 * lik_amp)
    counter_score = max(K6_15m_ters, K6_1h_ters, h15_ters)
    lik_amp = 1.3 if ters yon LIK flag else 1.0
    R2-R16 backtest: SADECE R16 etkilendi (SHORT→NOTR), SIFIR regresyon
    V7: 12/14 dogru (%86), 2 basarisiz
    V8: 12/13 dogru (%92), 1 basarisiz
    R16 V-RISK: K6_15m=+0.928 (ters) + LIK_ters → NOTR ±0.35 → |1h|=0.21 < 0.35 → NOTR

V7 DEGISIKLIKLER (V6'dan):
  [FIX-1] K3_NETPOS GATED WEIGHT (sadece 15m ve 4h):
    1h K3 baseline=+0.767 (R2-R13 ortalamasi). std=0.072.
    15m ve 4h'de: K3_raw baseline'dan > 1*std uzaktaysa → tam agirlik (1.2)
    15m ve 4h'de: K3_raw baseline icindeyse → yarim agirlik (0.6)
    1h EXEMPT: K3 gate 1h'ye UYGULANMIYOR.
    Neden: R7'de K3 gate 1h'yi NOTR→SHORT yaptı, gercek=UP.
    Yanlis yonde tam boyut pozisyon = para kaybi.
    1h K3 bias TANINIYOR ama dokunulmuyor (delta-pozisyon verisi gerekli).
    RISK: R7 regresyonu engellendi ama 1h K3 bias [B] acik konusu olarak kaliyor.
  [FIX-2] OLU AGIRLIK TEMIZLIGI:
    K2_VOL=0 (11 run'da 10'unda notr), K7_OI=0 (%30 dogruluk, zarar veriyor),
    K13_OI_PRICE_DIV=0 (hic tetiklenmedi), K17_CLIMAX=0 (hic tetiklenmedi)
    Drop-one testi: bu 4 kriter cikarildiginda yon dogrulugu DEGISMIYOR
    Kod KALDIRILMADI — agirlik 0, ihtiyac olursa tekrar aktif edilebilir
  [FIX-3] |4h| GIRIS KALITESI FILTRESI:
    |4h| < 0.50 → COK KUCUK BOYUT (R10/R11 pattern: zayif 4h = kotu giris)
    |4h| 0.50-1.00 → min KUCUK BOYUT
    |4h| > 1.00 → mevcut mantik (degisiklik yok)
    Veri: |4h|>1.5 ort MAE/MFE=0.17, |4h|<1.0 ort MAE/MFE=5.33

  [B] ACIK KONU: K3_NETPOS 1h sabit bias hala tam cozulmedi.
    1h K3 her zaman +0.62 ile +0.84 arasi (std=0.072).
    Gated weight bias'i YARILIYOR ama kaldirmiyor.
    Tam cozum: delta-pozisyon verisi (seviye degil degisim) gerekli.
    Her K3 formulunu denedik — R3 LONG→SHORT regresyon riski.
    R3'un dogru LONG cagrisi K3'un pozitif bias'ina BAGIMLI.

  [PROTOKOL] SINYAL OZETI — ZORUNLU 3 SATIR + KATMAN 8
    Pencere 34'te tespit: Claude cikti ozetinde 15m skorunu ve Katman 8
    kararini atladi. 1h tek basina bullish gorundu ama 15m ve 4h bearish —
    resmin yarisi kayboldu. Bu T1-C ihlalidir (filtreleme).
    KURAL: Her sinyal ozeti asagidaki formatta yazilir, ISTISNASIZ:
      15m=X, 1h=Y, 4h=Z | TF celiski: N/3
      Katman 8: GIR/DIKKATLI/GIRME (N kirmizi, N yesil)
    15m veya Katman 8 ASLA atlanamaz. Atlamak = filtreleme = T1-C ihlali.
    GIRME = pozisyon ACMA. Ters yone gir DEGIL (backtest: %71 < mevcut).

  [BACKTEST] TF KOMBİNASYON ANALİZİ (pencere 34, 20 run, $1000 MFE)
    27 kombinasyon (3^3), 6 gorulen, 13 olculen:
      S/S/S: 3/5=%60 SC, %40 ters  (R2✓ R5✓ R6✗ R8✓ R15✗)
      S/L/S: 3/3=%100 SC, %0 ters  (R3✓ R4✓ R9✓) +R19blr +R21blr
      L/L/S: 1/2=%50 SC, %50 ters  (R12✓ R14✗) +R18blr
      L/L/L: 2/2=%100 SC, %0 ters  (R10✓ R11✓)
      N/L/S: 0/1=%0 SC, %100 ters  (R13✗) +R20blr  ← TEK TERS KAZANAN
      S/N/S: olcum yok (R7 kacinildi)
    UYARI TETIKLEYICI: N/L/S (15m=NOTR, 1h=LONG, 4h=SHORT)
      Bu kombinasyonda scorecard %0, ters yon %100 (1 run — sinirli).
      R13: LONG dedi, gercek DOWN. Ayni pattern olusursa UYARI ver.
      Ters pattern (N/S/L) icin de ayni mantik gecerli (simetrik).
"""
import re
import numpy as np
import json, os, hashlib
from datetime import datetime

# Y-2 FIX: Yıl artık dinamik — sabit 2026 yerine çalışma zamanındaki yıl.
# run_time_str formatı "MM-DD HH:MM" (yıl içermiyor). Yıl sınırı geçen
# run'lar için yapısal çözüm HISTORICAL_DATA formatı değişikliği gerektirir;
# şimdilik çalışma zamanı yılı kullanılır.
_TRADE_YEAR: int = datetime.now().year

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(_SCRIPT_DIR, "yon_log.json")  # log shared across yon_* versions

def clamp(val, lo=-1.0, hi=1.0):
    return max(lo, min(hi, val))

# =================== KRITER FONKSIYONLARI ===================

def score_ma(d):
    p = d["current_price"]; m5, m10, m30 = d["ma5"], d["ma10"], d["ma30"]
    checks = sum([p>m5, p>m10, p>m30, m5>m10, m10>m30])
    base = (checks / 5.0) * 2.0 - 1.0
    avg_ma = (m5 + m10 + m30) / 3.0
    dist_pct = abs(p - avg_ma) / avg_ma * 100 if avg_ma > 0 else 0
    df = min(1.0, 0.3 + 0.7 * (dist_pct / 2.0))
    return clamp(base * df), {"checks": checks, "dist_pct": round(dist_pct, 4)}

def score_volume(d):
    """K2_VOL FIX: Dusuk volume = BELIRSIZ (0.0), bearish DEGIL.
    vol<avg -> 0.0 | vol>avg -> pozitif (trend teyidi)
    R7: -0.94 -> 0.0 -> 1h notr bolge -> kayip engellendi
    R3: NOTR -> LONG -> yeni dogru cagri"""
    vol = d["volume"]; avg_ma = (d["volume_ma5"] + d["volume_ma10"]) / 2.0
    if avg_ma == 0: return 0.0, {}
    ratio = vol / avg_ma
    if ratio >= 1.0:
        s = min(1.0, (ratio - 1.0) / 1.0)
    else:
        s = 0.0
    return clamp(s), {"ratio": round(ratio, 4)}

def score_net_pos(d):
    # P49 FIX: nl+ns → nl-ns (imbalance formülü)
    # Eski: net=nl+ns → CG flow verisinde anlamsız (toplam açılış)
    # Yeni: net=nl-ns → doğru imbalance (long-short farkı)
    # CG format: (27000, 1000) → (27000-1000)/28000 = 0.93 (long dominant)
    # API format: (longAccount, shortAccount) → (0.59-0.41)/1.0 = 0.18
    nl, ns = d["net_long"], d["net_short"]
    denom = abs(nl) + abs(ns)
    if denom == 0: return 0.0, {}
    ratio = (nl - ns) / denom
    return clamp(ratio), {"net": round(nl - ns, 2), "ratio": round(ratio, 4)}

def score_cvd(d):
    fc, sc = d["futures_cvd"], d.get("spot_cvd", 0) or 0
    if fc == 0 and sc == 0: return 0.0, {}
    fc_m = float(np.tanh(abs(fc) / 50e6)) if fc != 0 else 0.0
    sc_m = float(np.tanh(abs(sc) / 50000)) if sc != 0 else 0.0
    # P48 FIX: sc=0 → sadece fc magnitude (ikiye bölme yok)
    avg_m = (fc_m + sc_m) / 2.0 if sc != 0 else fc_m
    if fc > 0 and sc > 0: base = +0.8
    elif fc < 0 and sc < 0: base = -0.8
    elif fc > 0 and sc < 0: base = -0.3
    elif fc < 0 and sc > 0: base = +0.3
    # P48 FIX: sc=0 durumunda fc tek başına sinyal üretir
    # base=±0.5: iki CVD uyumundan (±0.8) zayıf, çelişkiden (±0.3) güçlü
    elif sc == 0 and fc > 0: base = +0.5
    elif sc == 0 and fc < 0: base = -0.5
    else: base = 0.0
    return clamp(base * (0.3 + 0.7 * avg_m)), {}

def score_liquidations(d):
    liq = d.get("liquidations", {}); ll = liq.get("long") or 0; ls_ = liq.get("short") or 0
    total = ll + ls_
    if total == 0: return 0.0, {}
    return clamp((ls_ - ll) / total), {"long": ll, "short": ls_}

def score_oi(d):
    oi = d.get("oi", 0); delta = d.get("oi_delta", 0)
    if oi == 0: return 0.0, {}
    return clamp(float(np.tanh((delta / oi * 100) / 1.5))), {}

def score_ls(d):
    r = d.get("taker_ls_ratio")
    if r is None: return 0.0, {"ratio": None}  # P59 FIX: API failure → nötr skor
    return clamp((r - 1.0) / 0.3), {"ratio": r}

def score_spot_cvd(d):
    sc = d.get("spot_cvd", 0) or 0
    if sc == 0: return 0.0, {}
    return clamp(float(np.tanh(sc / 50000.0)) * 0.8), {}

def score_oi_price_div(d, pchg):
    """K13e: OI × Price 3×3 matris — mikro-yapı rejim skorlaması.
    P49 backtest (14 run):
      OI↓P↓ → LONG: 3/3=%100 (kapitülasyon — satış baskısı tükeniyor)
      OI↑P↑ → LONG: 3/4=%75 (trend devam — yeni para giriyor)
      OI↑P↓ → SHORT: 2/3=%67 (trapped long — yeni pozisyon ama fiyat düşüyor)
      OI↓P↑ → NÖTR: 2/4=%50 (güvenilmez — short squeeze veya organik?)
    w=0.3. Tüm TF'lere uygulanır (her TF'nin oi_delta'sı farklı)."""
    oi = d.get("oi", 0); delta = d.get("oi_delta", 0)
    if oi == 0: return 0.0, {}
    oi_pct = (delta / oi) * 100
    # OI trend: >0.3% ↑, <-0.3% ↓, else →
    if oi_pct > 0.3: oi_dir = "UP"
    elif oi_pct < -0.3: oi_dir = "DOWN"
    else: oi_dir = "FLAT"
    # Price trend: pchg >0.3% ↑, <-0.3% ↓, else →
    if pchg > 0.3: p_dir = "UP"
    elif pchg < -0.3: p_dir = "DOWN"
    else: p_dir = "FLAT"
    # 3×3 matris — domain bilgisi + P49 backtest
    _M = {
        ("UP",   "UP"):   +0.50,  # trend devam (%75)
        ("UP",   "FLAT"): +0.15,  # yeni pozisyon, fiyat sabit
        ("UP",   "DOWN"): -0.50,  # trapped long (%67)
        ("FLAT", "UP"):   +0.10,  # hafif bullish
        ("FLAT", "FLAT"):  0.00,  # belirsiz
        ("FLAT", "DOWN"): -0.10,  # hafif bearish
        ("DOWN", "UP"):    0.00,  # güvenilmez (%50)
        ("DOWN", "FLAT"): -0.10,  # pozisyon kapanıyor
        ("DOWN", "DOWN"): +0.80,  # kapitülasyon (%100)
    }
    base = _M.get((oi_dir, p_dir), 0.0)
    # Magnitude: büyük hareket → etki artar (0.5 taban + 0.5 scaling)
    mag = min(1.0, (abs(oi_pct) / 2.0 + abs(pchg) / 2.0) / 2.0)
    score = base * (0.5 + 0.5 * mag)
    regime = f"OI{oi_dir[0]}P{p_dir[0]}"
    return clamp(score), {"oi_dir": oi_dir, "p_dir": p_dir, "oi_pct": round(oi_pct, 3),
        "pchg": round(pchg, 3), "base": base, "mag": round(mag, 3), "regime": regime}

def score_volume_climax(d):
    vol = d["volume"]; avg = (d["volume_ma5"] + d["volume_ma10"]) / 2.0
    if avg == 0: return 0.0, {}
    vr = vol / avg
    if vr < 1.5: return 0.0, {}
    oi = d.get("oi", 0); delta = d.get("oi_delta", 0)
    if oi > 0 and (delta / oi * 100) >= 0: return 0.0, {}
    m30 = d.get("ma30", d["current_price"])
    pc = abs((d["current_price"] - m30) / m30 * 100) if m30 > 0 else 0
    if pc < 0.5: return 0.0, {}
    liq = d.get("liquidations", {}); ll = liq.get("long") or 0; ls_ = liq.get("short") or 0
    tl = ll + ls_
    if tl == 0: return 0.0, {}
    ld = ll/tl*100; sd = ls_/tl*100
    if max(ld, sd) < 55: return 0.0, {}
    strength = min(1.0,(vr-1.5)/1.5)*0.35 + min(1.0,pc/2.0)*0.35 + max(ld,sd)/100*0.30
    raw = +strength if ld > sd else -strength
    return clamp(raw), {"type": "BOTTOM" if raw > 0 else "TOP", "strength": round(strength, 4)}

# =================== P52 TREND SCORE FONKSİYONLARI ===================
# Snapshot (neredeyiz) yerine Trend (nereye gidiyoruz) ölçen göstergeler.
# auto_fetch'ten gelen _slope, _momentum, _accel alanlarını kullanır.
# Veri yoksa (eski format) sessizce 0 döner — backward compat.

def score_ma_slope(d):
    """MA5 eğimi: yükseliyor → LONG, düşüyor → SHORT"""
    slope = d.get("ma5_slope", 0)
    price = d.get("current_price", 1)
    if price == 0 or slope == 0: return 0.0, {}
    normalized = slope / price * 1000
    return clamp(normalized), {"slope": round(slope, 2)}

def score_cvd_momentum(d):
    """CVD momentum: son 5 mum CVD / önceki 5 mum CVD.
    >0 = alış baskısı ARTIYOR → LONG
    <0 = alış baskısı AZALIYOR → SHORT"""
    mom = d.get("cvd_momentum", 0)
    if mom == 0: return 0.0, {}
    return clamp(mom * 2), {"momentum": round(mom, 4)}

def score_ls_trend(d):
    """LS ratio eğimi: artıyor → alıcılar güçleniyor → LONG"""
    slope = d.get("ls_slope", 0)
    if slope == 0: return 0.0, {}
    return clamp(slope / 0.05), {"slope": round(slope, 6)}

def score_oi_trend(d):
    """OI ivmelenmesi: pozisyon açılma HIZLANIYOR mu YAVAŞLIYOR mu?
    Pozitif accel = yeni pozisyon hızlanıyor = momentum devam
    Negatif accel = pozisyon kapanma başladı = dönüş sinyali"""
    accel = d.get("oi_accel", 0)
    oi = d.get("oi", 1)
    if oi == 0 or accel == 0: return 0.0, {}
    return clamp(accel / oi * 100), {"accel": round(accel, 2)}

def score_np_trend(d):
    """Net pozisyon eğimi: long hesaplar ARTIYOR mu AZALIYOR mu?
    Snapshot K3 hep LONG → discriminative=0.14.
    Trend ile "longlar KAPANIYOR" tespiti mümkün."""
    slope = d.get("np_slope", 0)
    if slope == 0: return 0.0, {}
    return clamp(slope / 0.02), {"slope": round(slope, 6)}

def score_depth(d):
    """Order book depth imbalance: bid/ask > 1 → LONG, < 1 → SHORT.
    TEK GERÇEK LEADING gösterge — emirler fiyattan ÖNCE konur."""
    imb = d.get("depth_imbalance", 0)
    if imb == 0: return 0.0, {}
    return clamp((imb - 1.0) / 0.5), {"imbalance": round(imb, 4)}

def score_funding(d):
    """Funding rate — CONTRARIAN gösterge.
    Yüksek pozitif = LONG crowded → SHORT sinyal (reversal riski)
    Yüksek negatif = SHORT crowded → LONG sinyal"""
    fr = d.get("funding_rate")
    if fr is None or fr == 0: return 0.0, {}
    return clamp(-fr / 0.0005), {"rate": round(fr, 6)}

def predict_liq_risk(d):
    nl = d.get("net_long", 0); ns = d.get("net_short", 0); fc = d.get("futures_cvd", 0)
    liq = d.get("liquidations", {}); ll = liq.get("long") or 0; ls_ = liq.get("short") or 0
    sr, lr = 0.0, 0.0
    if nl > 0 and fc < 0 and ls_ > ll * 1.5:
        sr = min(1.0, (nl / 10000) + abs(fc / 1e7) + (ls_ / 100000))
    if ns > 0 and fc > 0 and ll > ls_ * 1.5:
        lr = min(1.0, (ns / 10000) + (fc / 1e7) + (ll / 100000))
    return {"short_liq_risk": round(sr*100, 1), "long_liq_risk": round(lr*100, 1),
            "warning": "SHORT LIK RISKI" if sr > 0.6 else "LONG LIK RISKI" if lr > 0.6 else "YOK"}

# =================== IKILI OLCUM STANDARDI ===================
# YON-2-5: Actual olcumu degisti.
# Eski: 4h sonrasi fiyat giris yonunde mi? (close bazli, tutarsiz)
# Yeni: Fiyat giris yonunde $1000'a ulasti mi? Hangisi once? (MFE bazli, stabil)
# BELIRSIZ: Fiyat ne +$1000 ne -$1000 → piyasa hareket etmedi → olcum yapilmaz.
# 5 etiket: BASARILI, GIRIS_KOTU, YON_YANLIS, BASARISIZ, BELIRSIZ
QUALITY_THRESHOLD = 0.70  # MAE/MFE esigi — 20 run'da revize edilebilir

def eval_actual(direction, actual_dir, mfe_4h, mae_4h):
    """Ikili olcum standardi: yon + giris kalitesi.
    direction: scorecard ciktisi (LONG/SHORT/NOTR)
    actual_dir: gercek hareket (UP/DOWN/None)
    mfe_4h, mae_4h: 4h pencere MFE ve MAE degerleri
    Returns: {"label": str, "dir_ok": bool|None, "quality_ok": bool|None, "ratio": float|None}
    """
    if direction == "NOTR":
        return {"label": "KACINILDI", "dir_ok": None, "quality_ok": None, "ratio": None}
    if actual_dir is None or actual_dir == "?":
        return {"label": "BEKLIYOR", "dir_ok": None, "quality_ok": None, "ratio": None}
    if actual_dir == "BELIRSIZ":
        return {"label": "BELIRSIZ", "dir_ok": None, "quality_ok": None, "ratio": None}

    # Boyut 1: Yon
    dir_ok = (direction == "LONG" and actual_dir == "UP") or \
             (direction == "SHORT" and actual_dir == "DOWN")

    # Boyut 2: Kalite (MAE/MFE orani)
    if mfe_4h is None or mfe_4h <= 0 or mae_4h is None:
        quality_ok = None
        ratio = None
    else:
        ratio = round(mae_4h / mfe_4h, 2)
        quality_ok = ratio < QUALITY_THRESHOLD

    # 4 etiket
    if dir_ok and quality_ok:
        label = "BASARILI"
    elif dir_ok and quality_ok is False:
        label = "GIRIS_KOTU"
    elif dir_ok and quality_ok is None:
        label = "YON_OK_VERI_YOK"
    elif not dir_ok and quality_ok:
        label = "YON_YANLIS"
    elif not dir_ok and quality_ok is False:
        label = "BASARISIZ"
    else:
        label = "YON_X_VERI_YOK"

    return {"label": label, "dir_ok": dir_ok, "quality_ok": quality_ok, "ratio": ratio}

# =================== MUM ANALİZ MOTORU ===================
# Her TF icin anlik + onceki mum → fitil, engulfing, momentum, range, gap
# Veri OPSIYONEL: None ise analiz atlanir

def analyze_candle_pair(curr, prev, tf_label):
    """Tek TF icin anlik + onceki mum analizi.
    curr/prev: {"open": float, "high": float, "low": float, "close": float}
    Returns: dict with flags and metrics, or None if data missing.
    """
    if curr is None:
        return None

    o, h, l, c = curr["open"], curr["high"], curr["low"], curr["close"]
    rng = h - l
    if rng == 0:
        return {"tf": tf_label, "flags": [], "metrics": {"range": 0}}

    # --- Mum tipi ---
    bullish = c > o
    body = abs(c - o)
    body_top = max(c, o)
    body_bot = min(c, o)

    # --- Fitil analizi (rejection) ---
    upper_wick = h - body_top
    lower_wick = body_bot - l
    upper_wick_pct = upper_wick / rng
    lower_wick_pct = lower_wick / rng
    body_pct = body / rng

    # --- Close pozisyonu (0=dip, 1=tepe) ---
    close_pos = (c - l) / rng

    # --- Range (volatilite proxy) ---
    range_pct = (rng / c) * 100

    flags = []
    # Fitil bayraklari
    if upper_wick_pct > 0.60:
        flags.append(f"{tf_label} UST FITIL %{upper_wick_pct*100:.0f} — yukari RED")
    if lower_wick_pct > 0.60:
        flags.append(f"{tf_label} ALT FITIL %{lower_wick_pct*100:.0f} — asagi RED")

    # Close pozisyonu bayraklari
    if close_pos < 0.25:
        flags.append(f"{tf_label} CLOSE DIPTE (%{close_pos*100:.0f}) — satis baskisi")
    elif close_pos > 0.75:
        flags.append(f"{tf_label} CLOSE TEPEDE (%{close_pos*100:.0f}) — alis baskisi")

    # Doji (cok kucuk body)
    if body_pct < 0.10:
        flags.append(f"{tf_label} DOJI — karasizlik")

    metrics = {
        "range": round(rng, 1),
        "range_pct": round(range_pct, 4),
        "body_pct": round(body_pct * 100, 1),
        "upper_wick_pct": round(upper_wick_pct * 100, 1),
        "lower_wick_pct": round(lower_wick_pct * 100, 1),
        "close_pos": round(close_pos * 100, 1),
        "bullish": bullish,
    }

    # --- Onceki mumla karsilastirma ---
    if prev is not None:
        po, ph, pl, pc_ = prev["open"], prev["high"], prev["low"], prev["close"]
        prev_rng = ph - pl
        prev_bullish = pc_ > po
        prev_body_top = max(pc_, po)
        prev_body_bot = min(pc_, po)

        # Engulfing
        if not prev_bullish and bullish and body_bot <= prev_body_bot and body_top >= prev_body_top:
            flags.append(f"{tf_label} BULLISH ENGULFING")
        if prev_bullish and not bullish and body_bot <= prev_body_bot and body_top >= prev_body_top:
            flags.append(f"{tf_label} BEARISH ENGULFING")

        # Momentum (ayni yon devam)
        if prev_bullish and bullish:
            flags.append(f"{tf_label} YUKARI MOMENTUM (2 yesil)")
        elif not prev_bullish and not bullish:
            flags.append(f"{tf_label} ASAGI MOMENTUM (2 kirmizi)")

        # Gap
        gap = o - pc_
        gap_pct = abs(gap / c) * 100
        if gap_pct > 0.10:
            gap_dir = "YUKARI" if gap > 0 else "ASAGI"
            flags.append(f"{tf_label} GAP {gap_dir} ${abs(gap):,.0f} (%{gap_pct:.2f})")

        # Mini ATR (2 mum ortalama range)
        avg_range = (rng + prev_rng) / 2
        avg_range_pct = (avg_range / c) * 100
        metrics["prev_range"] = round(prev_rng, 1)
        metrics["avg_range"] = round(avg_range, 1)
        metrics["avg_range_pct"] = round(avg_range_pct, 4)
        metrics["prev_bullish"] = prev_bullish
        metrics["gap"] = round(gap, 1)

    return {"tf": tf_label, "flags": flags, "metrics": metrics}

def analyze_all_candles(candles_data, direction):
    """3 TF'nin mum analizini birlestir.
    candles_data: {"15m": {"curr": {...}, "prev": {...}}, "1h": ..., "4h": ...} or None
    direction: scorecard ciktisi (LONG/SHORT/NOTR)
    Returns: {"flags": [...], "tf_results": [...], "mae_estimate": float|None}
    """
    if candles_data is None:
        return None

    all_flags = []
    tf_results = []
    ranges = []

    for tf in ["15m", "1h", "4h"]:
        td = candles_data.get(tf)
        if td is None:
            continue
        result = analyze_candle_pair(td.get("curr"), td.get("prev"), tf)
        if result is None:
            continue
        tf_results.append(result)
        all_flags.extend(result["flags"])
        if result["metrics"].get("avg_range"):
            ranges.append((tf, result["metrics"]["avg_range"]))

    # --- Scorecard yonu ile mum celiskisi ---
    conflict_flags = []
    for r in tf_results:
        m = r["metrics"]
        tf = r["tf"]
        if direction == "LONG":
            if m.get("close_pos", 50) < 25:
                conflict_flags.append(f"!! {tf} CLOSE DIPTE ama scorecard LONG")
            if m.get("upper_wick_pct", 0) > 50:
                conflict_flags.append(f"!! {tf} UST FITIL BUYUK ama scorecard LONG")
            if "BEARISH ENGULFING" in " ".join(r["flags"]):
                conflict_flags.append(f"!! {tf} BEARISH ENGULFING ama scorecard LONG")
        elif direction == "SHORT":
            if m.get("close_pos", 50) > 75:
                conflict_flags.append(f"!! {tf} CLOSE TEPEDE ama scorecard SHORT")
            if m.get("lower_wick_pct", 0) > 50:
                conflict_flags.append(f"!! {tf} ALT FITIL BUYUK ama scorecard SHORT")
            if "BULLISH ENGULFING" in " ".join(r["flags"]):
                conflict_flags.append(f"!! {tf} BULLISH ENGULFING ama scorecard SHORT")

    # --- MAE tahmini (1h avg_range bazli) ---
    mae_estimate = None
    for tf, rng in ranges:
        if tf == "1h":
            mae_estimate = round(rng * 1.5, 1)  # 1h range x 1.5 = beklenen max drawdown
            break
    if mae_estimate is None and ranges:
        # 1h yoksa en yakin TF
        mae_estimate = round(ranges[-1][1] * 1.5, 1)

    return {
        "flags": all_flags,
        "conflict_flags": conflict_flags,
        "tf_results": tf_results,
        "mae_estimate": mae_estimate,
    }

def print_candle_analysis(candle_result, direction):
    """Mum analizi ciktisini yazdir."""
    if candle_result is None:
        return

    print(f"\n{'='*70}")
    print(f"  KATMAN 5 — MUM ANALIZİ (anlik + onceki)")
    print(f"{'='*70}")

    for r in candle_result["tf_results"]:
        m = r["metrics"]
        tf = r["tf"]
        color = "YESIL" if m["bullish"] else "KIRMIZI"
        prev_s = ""
        if m.get("prev_bullish") is not None:
            prev_color = "YESIL" if m["prev_bullish"] else "KIRMIZI"
            prev_s = f" | onceki={prev_color}"
        print(f"\n  [{tf}] {color}{prev_s}")
        print(f"    Range: ${m['range']:,.1f} (%{m['range_pct']:.2f})"
              f"  Body: %{m['body_pct']:.0f}"
              f"  UstFitil: %{m['upper_wick_pct']:.0f}"
              f"  AltFitil: %{m['lower_wick_pct']:.0f}"
              f"  Close: %{m['close_pos']:.0f}")
        if m.get("avg_range"):
            print(f"    Mini-ATR (2 mum ort): ${m['avg_range']:,.1f} (%{m['avg_range_pct']:.2f})")
        if m.get("gap") and abs(m["gap"]) > 0:
            print(f"    Gap: ${m['gap']:+,.1f}")
        for f in r["flags"]:
            print(f"    >> {f}")

    # Celiski uyarilari (en onemli kisim)
    if candle_result["conflict_flags"]:
        print(f"\n  {'!'*50}")
        print(f"  SCORECARD <-> MUM CELISKISI:")
        for cf in candle_result["conflict_flags"]:
            print(f"    {cf}")
        print(f"  {'!'*50}")

    # MAE tahmini
    if candle_result["mae_estimate"]:
        print(f"\n  MAE tahmini (1h range x 1.5): ~${candle_result['mae_estimate']:,.0f}")
        print(f"    (Gercek ortalama MAE: tum runlarda hesaplanir)")

# =================== BİRLEŞİK SİNYAL FONKSİYONLARI (YON-2-7) ===================
# v3a backtest: SC + MUM_15m + MUM_1h + WHALE_v2 = %87 (13/15)

def _get_candle_at_entry(candles, run_time_str, candle_hours):
    """Run time'a denk gelen curr + prev mumu bul."""
    if not candles or not run_time_str:
        return None, None
    try:
        rt = _dt.strptime(f"{_TRADE_YEAR}-{run_time_str}", "%Y-%m-%d %H:%M")
    except:
        return None, None
    for i, (ct_str, o, h, l, c) in enumerate(candles):
        ct = _parse_candle_time(ct_str)
        if ct <= rt < ct + _td(hours=candle_hours):
            curr = {"open": o, "high": h, "low": l, "close": c}
            prev = None
            if i > 0:
                prev = {"open": candles[i-1][1], "high": candles[i-1][2],
                         "low": candles[i-1][3], "close": candles[i-1][4]}
            return curr, prev
    return None, None

def candle_entry_signal(curr, prev):
    """Mum verisinden yön sinyali: +1 (LONG), -1 (SHORT), 0 (NÖTR)
    Faktörler: renk, close pozisyonu, fitil, engulfing, momentum."""
    if curr is None:
        return 0, "YOK"
    o, h, l, c = curr["open"], curr["high"], curr["low"], curr["close"]
    rng = h - l
    if rng == 0:
        return 0, "DOJI"
    bullish = c > o
    close_pos = (c - l) / rng
    uw = (h - max(c, o)) / rng
    lw = (min(c, o) - l) / rng
    score = 0
    r = []
    # Renk
    if bullish: score += 1; r.append("G")
    else: score -= 1; r.append("K")
    # Close pozisyonu
    if close_pos > 0.70: score += 1; r.append("CT")
    elif close_pos < 0.30: score -= 1; r.append("CD")
    # Fitil
    if uw > 0.50: score -= 1; r.append("UF")
    if lw > 0.50: score += 1; r.append("AF")
    # Engulfing + momentum (prev ile)
    if prev is not None:
        pb = prev["close"] > prev["open"]
        pbt, pbb = max(prev["close"], prev["open"]), min(prev["close"], prev["open"])
        bt, bb = max(c, o), min(c, o)
        if not pb and bullish and bb <= pbb and bt >= pbt:
            score += 2; r.append("BE")
        if pb and not bullish and bb <= pbb and bt >= pbt:
            score -= 2; r.append("SE")
        if pb and bullish: score += 1; r.append("UM")
        elif not pb and not bullish: score -= 1; r.append("DM")
    sig = 1 if score > 0 else (-1 if score < 0 else 0)
    return sig, "+".join(r)

def get_entry_candle_signals(run_time_str):
    """3 TF için giriş anı mum sinyali (15m, 1h, 4h)."""
    sigs = {}
    for tf, cndls, hrs in [("15m", CANDLES_15M, 0.25), ("1h", CANDLES_1H, 1), ("4h", CANDLES_4H, 4)]:
        curr, prev = _get_candle_at_entry(cndls, run_time_str, hrs)
        sig, reason = candle_entry_signal(curr, prev)
        sigs[tf] = {"sig": sig, "reason": reason}
    return sigs

def whale_signal_v2(whale_ls):
    """Whale L/S → seviyeli sinyal.
    <0.87 = SHORT(-1), 0.87-0.95 = NÖTR(0), >0.95 = LONG(+1).
    Backtest: 5/6 aktif sinyal doğru (%83)."""
    if whale_ls is None:
        return 0, "YOK"
    if whale_ls < 0.87:
        return -1, f"SHORT({whale_ls:.4f})"
    elif whale_ls > 0.95:
        return 1, f"LONG({whale_ls:.4f})"
    else:
        return 0, f"NOTR({whale_ls:.4f})"

# [KALDIRILDI] heatmap_signal() — ölü kod temizliği

# [KALDIRILDI] _heatmap_view_to_old_format() — ölü kod temizliği

# [KALDIRILDI] _heatmap_view_all_clusters() — ölü kod temizliği

# [KALDIRILDI] derive_heatmap_summary() — ölü kod temizliği

# =================== AGIRLIKLAR + HESAPLAMA ===================

# V7: Olu agirliklar sifirlanmis (K2, K7, K13, K17)
# YON-2-3: K12 olu agirlik eklendi (18 run'da etkisiz, 0 regresyon)
# P52 NOT: K3_NETPOS=1.2 korundu. w=0.5 denenip geri alındı —
#   kaskad etki: V9 eşiği, band istatistikleri, meta-skor hepsi bozuldu.
#   K3 düzeltmesi izole değişiklik değil, tam recalibration gerektiriyor.
WEIGHTS = {"K1_MA": 0.0, "K3_NETPOS": 1.2, "K4_CVD": 0.0,
    "K6_LIQ": 0.0, "K7_OI": 0.0, "K8_LS": 1.0,
    "K13_OI_PRICE_DIV": 0.0, "K17_CLIMAX": 0.0,
    # P54 KALİBRASYON (20 run backtest):
    # K1_MA: 1.0→0 (%35 doğru, zararlı) — fingerprint'te kullanılıyor
    # K4_CVD: 0.9→0 (%35 doğru, zararlı, yapısal negatif bias) — fingerprint'te
    # K8_LS: 0.6→1.0 (%70 doğru, güçlendirildi)
    # K13_OI_PRICE_DIV: 0.3→0 (%33 doğru, zararlı) — fingerprint'te
    # P52 TREND KATMANLARI
    "KT_LS_TREND": 0.6, "KT_DEPTH": 0.6, "KT_FUNDING": 0.4,
    # [KALDIRILDI] compute_tf'den çıkarılan w=0 kriterler (sıfır yan etki):
    # K2_VOL (11 run'da 10'unda nötr), K12_SPOT_CVD (ölü ağırlık),
    # KT_MA_SLOPE (LAG, ters çalışıyor), KT_CVD_MOM (w=0),
    # KT_OI_TREND (disc=0.041, bilgi taşımıyor), KT_NP_TREND (disc=0.081, R28 yanlış)
    # Fonksiyon tanımları dosyada duruyor — reaksivasyon için criteria dict'e geri ekle.
}
# P54: NEUTRAL_ZONE 0.10→0.02 (R2 kurtarma, R7 NOTR kalır)
NEUTRAL_ZONE = 0.02

# V7 FIX-1: K3 Gated Weight — baseline'dan uzakliga gore agirlik degisir
K3_BASELINES = {"15m": -0.2840, "1h": +0.7673, "4h": -0.4957}
K3_STDS = {"15m": 0.6926, "1h": 0.0717, "4h": 0.1253}
K3_GATE_THRESHOLD = 1.0   # baseline'dan kac std → tam agirlik
K3_NORMAL_WEIGHT = 0.6    # normal araliktayken agirlik (tam=1.2, yarim=0.6)

def compute_tf(d, tf_label="1h"):
    pchg = ((d["current_price"] - d["ma30"]) / d["ma30"]) * 100 if d["ma30"] > 0 else 0
    criteria = {"K1_MA": score_ma(d), "K3_NETPOS": score_net_pos(d),
        "K4_CVD": score_cvd(d), "K6_LIQ": score_liquidations(d), "K7_OI": score_oi(d),
        "K13_OI_PRICE_DIV": score_oi_price_div(d, pchg), "K17_CLIMAX": score_volume_climax(d),
        # P52 TREND KATMANLARI — veri yoksa sessizce 0 döner
        "KT_LS_TREND": score_ls_trend(d),
        "KT_DEPTH": score_depth(d),
        "KT_FUNDING": score_funding(d),
        # [KALDIRILDI] w=0 + sıfır yan etki: K2_VOL, K12_SPOT_CVD,
        # KT_MA_SLOPE, KT_CVD_MOM, KT_OI_TREND, KT_NP_TREND
    }
    # K8_LS: taker_ls_ratio 3 TF'de ayni deger → sadece 1h'de uygula (3x bias fix)
    if tf_label == "1h":
        criteria["K8_LS"] = score_ls(d)
    total = 0.0; detail = {}
    for k, (raw, det) in criteria.items():
        w = WEIGHTS.get(k, 1.0)
        # V7 FIX-1: K3 gated weight — sadece 15m ve 4h'de
        # 1h EXEMPT: 1h yon belirliyor, K3 gate R7'de regresyon yaratiyordu
        # (NOTR→SHORT, gercek=UP — yanlis yonde tam boyut pozisyon)
        if k == "K3_NETPOS" and tf_label in K3_BASELINES and tf_label != "1h":
            baseline = K3_BASELINES[tf_label]
            std = K3_STDS.get(tf_label, 0.1)
            deviation = abs(raw - baseline)
            if deviation > K3_GATE_THRESHOLD * std:
                w = WEIGHTS["K3_NETPOS"]  # tam agirlik (unusual)
                k3_gate = "FULL"
            else:
                w = K3_NORMAL_WEIGHT      # yarim agirlik (normal)
                k3_gate = "HALF"
            det["k3_gate"] = k3_gate
            det["k3_deviation"] = round(deviation, 4)
            det["k3_baseline"] = baseline
        elif k == "K3_NETPOS" and tf_label == "1h":
            det["k3_gate"] = "EXEMPT"
            det["k3_deviation"] = 0
            det["k3_baseline"] = K3_BASELINES.get("1h", 0)
        final = raw * w; total += final
        detail[k] = {"raw": round(raw, 4), "final": round(final, 4)}
        if k == "K3_NETPOS":
            detail[k].update({kk: det[kk] for kk in det if kk.startswith("k3_")})
        if k == "K13_OI_PRICE_DIV" and det:
            detail[k].update(det)
    return round(total, 4), detail

def compute_scorecard(d15, d1h, d4h, whale_ls=None, oi_data=None):
    h15, det15 = compute_tf(d15, "15m"); h1, det1h = compute_tf(d1h, "1h"); h4, det4h = compute_tf(d4h, "4h")
    
    # === P54 WHALE+OI TRAP ===
    # Fallback: whale_ls auto_fetch tarafından data_1h içine konabilir
    if whale_ls is None and d1h.get("whale_acct_ls"):
        whale_ls = d1h["whale_acct_ls"]
    trap_triggered = False
    trap_info = {}
    if h1 > 0 and whale_ls is not None and oi_data is not None:
        oi_rising = False
        if len(oi_data) >= 2:
            oi_rising = oi_data[-1][1] > oi_data[0][1]
        if whale_ls < 0.86 and oi_rising:
            trap_triggered = True
            trap_penalty = -2.5
            h1_before = h1
            h1 += trap_penalty
            h15 += trap_penalty * 0.5
            h4 += trap_penalty * 0.5
            trap_info = {
                "triggered": True, "whale_ls": whale_ls, "oi_rising": oi_rising,
                "oi_delta": round(oi_data[-1][1] - oi_data[0][1], 1) if len(oi_data) >= 2 else 0,
                "penalty": trap_penalty, "h1_before": round(h1_before, 4), "h1_after": round(h1, 4),
            }
    
    # === V-RISK V3: DİNAMİK NOTR BÖLGESİ ===
    # Karşı-sinyal varsa NOTR bölgesi genişler.
    # Zayıf sinyal + güçlü karşı-sinyal = NOTR (pozisyon açma)
    # Kaynaklar: K6_15m (hızlı), K6_1h (yerleşik), h15 yön, LIK flag
    is_long = h1 > 0
    k6_15m_raw = det15.get("K6_LIQ", {}).get("raw", 0)
    k6_1h_raw = det1h.get("K6_LIQ", {}).get("raw", 0)
    
    # Karşı-sinyal tespiti (15m + 1h)
    k6_15m_ters = (is_long and k6_15m_raw < -0.3) or (not is_long and k6_15m_raw > 0.3)
    k6_1h_ters = (is_long and k6_1h_raw < -0.3) or (not is_long and k6_1h_raw > 0.3)
    h15_ters = (is_long and h15 < -0.10) or (not is_long and h15 > 0.10)
    
    # LIK risk bayrağı (ters yönde) — önceden hesapla
    lik_ters = False
    for tf_dd in [d15, d1h, d4h]:
        lr = predict_liq_risk(tf_dd)
        if is_long and lr["short_liq_risk"] > 60: lik_ters = True
        if not is_long and lr["long_liq_risk"] > 60: lik_ters = True
    
    # NOTR bölgesi genişletme — en güçlü karşı-sinyali kullan
    counter_vals = []
    if k6_15m_ters: counter_vals.append(abs(k6_15m_raw))
    if k6_1h_ters: counter_vals.append(abs(k6_1h_raw))
    if h15_ters: counter_vals.append(abs(h15))
    has_counter = len(counter_vals) > 0
    counter_score = max(counter_vals) if counter_vals else 0
    expansion = 0.0
    if has_counter:
        expansion = counter_score * 0.25
        if lik_ters:
            expansion *= 1.3
        expansion = min(0.25, expansion)  # max genişleme
    effective_notr = NEUTRAL_ZONE + expansion
    
    v_risk_info = {
        "k6_15m_ters": k6_15m_ters, "k6_1h_ters": k6_1h_ters,
        "h15_ters": h15_ters, "lik_ters": lik_ters,
        "counter_score": round(counter_score, 4),
        "expansion": round(expansion, 4),
        "effective_notr": round(effective_notr, 4),
        "original_notr": NEUTRAL_ZONE,
        "triggered": has_counter and abs(h1) < effective_notr and abs(h1) >= NEUTRAL_ZONE,
    }
    
    # Yön belirleme (genişletilmiş NOTR ile)
    if abs(h1) < effective_notr: direction = "NOTR"
    elif h1 > 0: direction = "LONG"
    else: direction = "SHORT"
    
    if direction == "NOTR": confidence, size = "BEKLE", "POZISYON ACMA"
    elif (h1 > 0 and h4 > 0) or (h1 < 0 and h4 < 0):
        if abs(h4) < 0.50:
            confidence, size = "DUSUK", "KUCUK BOYUT"
        else:
            confidence, size = "YUKSEK", "NORMAL BOYUT"
    else: confidence, size = "DUSUK", "KUCUK BOYUT"
    climax = None
    for tf, det in [("15m", det15), ("1h", det1h), ("4h", det4h)]:
        k17 = det.get("K17_CLIMAX", {})
        if abs(k17.get("raw", 0)) > 0.1:
            climax = f"K17 CLIMAX {tf}"
            if confidence != "BEKLE": confidence, size = "DUSUK", "KUCUK BOYUT"
    dirs = [h15 > 0, h1 > 0, h4 > 0]
    contradiction = sum(1 for i in range(3) for j in range(i+1, 3) if dirs[i] != dirs[j])
    if contradiction >= 2 and confidence == "YUKSEK": confidence, size = "ORTA", "KUCUK BOYUT"
    flags = []
    if v_risk_info["triggered"]:
        k6_src = []
        if k6_15m_ters: k6_src.append("K6_15m")
        if k6_1h_ters: k6_src.append("K6_1h")
        if h15_ters: k6_src.append("h15")
        flags.append(f"V-RISK: NOTR ±{effective_notr:.2f} ({'+'.join(k6_src)} ters{' +LIK' if lik_ters else ''})")
    if climax: flags.append(climax)
    if contradiction >= 2: flags.append(f"TF celiski: {contradiction}/3")
    for tf, dd in [("15m", d15), ("1h", d1h), ("4h", d4h)]:
        liq = predict_liq_risk(dd)
        if liq["warning"] != "YOK":
            flags.append(f"{tf} {liq['warning']} (S:{liq['short_liq_risk']}% L:{liq['long_liq_risk']}%)")
    if len(flags) >= 3: size = "COK KUCUK BOYUT"
    # V7 FIX-3: |4h| giris kalitesi filtresi
    if direction != "NOTR":
        abs_h4 = abs(h4)
        if abs_h4 < 0.50:
            size = "COK KUCUK BOYUT"
            flags.append(f"|4h|={abs_h4:.2f} < 0.50 — cok zayif 4h sinyali")
        elif abs_h4 < 1.00 and size == "NORMAL BOYUT":
            size = "KUCUK BOYUT"
            flags.append(f"|4h|={abs_h4:.2f} < 1.00 — zayif 4h sinyali")
    # V9 FIX-5: |1h| giris kalitesi filtresi ("COK GEC")
    # |1h| > 1.50 = cogu kriter uyumlu, hareket zaten olmus
    # R10(2.40), R11(1.94), R12(1.71) yakalandi, 0 regresyon
    if direction != "NOTR":
        abs_h1 = abs(h1)
        if abs_h1 > 1.50:
            size = "COK KUCUK BOYUT"
            flags.append(f"V9-GECIKME: |1h|={abs_h1:.2f} > 1.50 — gecikmiş sinyal riski")
    # V9 FIX-6: BEKLE sinyali ("HENUZ DEGIL")
    # vol_1h < %50 avg + LS yöne karşı > 0.50 + |4h| < 1.50
    # R17 yakalandi, R15 makro override ile korundu, 0 regresyon
    if direction != "NOTR":
        _vol_1h = d1h.get("volume", 0)
        _vol_ma5 = d1h.get("volume_ma5", 0)
        _vol_ma10 = d1h.get("volume_ma10", 0)
        _avg_vol = (_vol_ma5 + _vol_ma10) / 2.0
        _vol_ratio = _vol_1h / _avg_vol if _avg_vol > 0 else 1.0
        _ls = d1h.get("taker_ls_ratio") or 1.0  # P59 FIX: None → nötr
        _ls_opposition = 0.0
        if direction == "SHORT" and _ls > 1.0:
            _ls_opposition = _ls - 1.0
        elif direction == "LONG" and _ls < 1.0:
            _ls_opposition = 1.0 - _ls
        _low_vol = _vol_ratio < 0.50
        _high_ls = _ls_opposition > 0.50
        _weak_macro = abs(h4) < 1.50
        _bekle_flag = _low_vol and _high_ls and _weak_macro
        if _bekle_flag:
            size = "COK KUCUK BOYUT"
            flags.append(f"V9-BEKLE: vol={_vol_ratio:.2f}<0.50 + LS_opp={_ls_opposition:.2f}>0.50 + |4h|={abs(h4):.2f}<1.50 — sweep riski, giris ertele")
    # K8_LS SAME-DATA UYARISI: 3 TF'de ayni taker_ls_ratio → veri TF-spesifik degil
    _ls15 = d15.get("taker_ls_ratio") or 1.0  # P59 FIX: None → nötr
    _ls1h = d1h.get("taker_ls_ratio") or 1.0
    _ls4h = d4h.get("taker_ls_ratio") or 1.0
    if abs(_ls15 - _ls1h) < 0.002 and abs(_ls1h - _ls4h) < 0.002:
        _k8_fin = det1h.get("K8_LS", {}).get("final", 0)
        flags.append(f"K8_LS_AYNI: 3TF={_ls1h:.3f} — katki {_k8_fin:+.3f} yapay, veri TF-spesifik degil")
    # P48: K6_LIQ_FLUSH — 3 TF long liq baskın → tamamlanmış tasfiye, %75 reversal riski
    _k6_15m = det15.get("K6_LIQ", {}).get("raw", 0)
    _k6_1h = det1h.get("K6_LIQ", {}).get("raw", 0)
    _k6_4h = det4h.get("K6_LIQ", {}).get("raw", 0)
    if _k6_15m < -0.30 and _k6_1h < -0.30 and _k6_4h < -0.30 and direction == "SHORT":
        flags.append(f"K6_LIQ_FLUSH: 3TF long liq baskin (15m={_k6_15m:+.2f} 1h={_k6_1h:+.2f} 4h={_k6_4h:+.2f}) — tasfiye tamamlanmis olabilir, %75 reversal riski")
    return {"direction": direction, "confidence": confidence, "size": size,
        "h15": h15, "h1": h1, "h4": h4, "det15": det15, "det1h": det1h, "det4h": det4h,
        "flags": flags, "climax": climax, "contradiction": contradiction, "v_risk": v_risk_info,
        "trap": trap_info}

# =================== LOG SISTEMI ===================

def load_log():
    if not os.path.exists(LOG_FILE): return []
    try:
        with open(LOG_FILE, "r") as f: return json.load(f)
    except: return []

def save_log(runs):
    with open(LOG_FILE, "w") as f: json.dump(runs, f, indent=2, ensure_ascii=False)

def get_data_hash(d15, d1h, d4h):
    c = str(sorted(d15.items())) + str(sorted(d1h.items())) + str(sorted(d4h.items()))
    return hashlib.sha256(c.encode()).hexdigest()[:12]

# [KALDIRILDI] append_run() — ölü kod temizliği

# [KALDIRILDI] _embed_run_to_file() — ölü kod temizliği

# =================== 4H MUM VERİSİ (Binance'ten) ===================
# Kaynak: Binance API /fapi/v1/klines → UTC+3 (Turkiye)
# Eski veri UTC+2 idi (1 saat hatali), API ile duzeltildi
# Eski veride eksik mum vardi (03-26 15:00), API ile tamamlandi

CANDLES_4H = [
    ("03-25 15:00", 71650.3, 71933.3, 70531.4, 70792.4),
    ("03-25 19:00", 70792.4, 71742.2, 70623.4, 70853.2),
    ("03-25 23:00", 70853.3, 71606.0, 70603.0, 71297.5),
    ("03-26 03:00", 71297.5, 71408.1, 70640.0, 70881.9),
    ("03-26 07:00", 70882.0, 70882.0, 69722.6, 70053.8),
    ("03-26 11:00", 70053.8, 70131.5, 69127.2, 69239.3),
    ("03-26 15:00", 69239.3, 69872.2, 68553.4, 69054.8),
    ("03-26 19:00", 69054.9, 69138.8, 68115.8, 68502.7),
    ("03-26 23:00", 68502.7, 69466.6, 68378.5, 68788.0),
    ("03-27 03:00", 68788.1, 69142.7, 68458.5, 68728.8),
    ("03-27 07:00", 68728.8, 68925.0, 68257.2, 68501.7),
    ("03-27 11:00", 68501.8, 68619.9, 66175.4, 66663.2),
    ("03-27 15:00", 66663.3, 66742.2, 65681.5, 66092.0),
    ("03-27 19:00", 66091.9, 66267.4, 65501.0, 66005.4),
    ("03-27 23:00", 66005.5, 66384.0, 65766.1, 66364.2),
    ("03-28 03:00", 66364.1, 66472.4, 65888.0, 66191.8),
    ("03-28 07:00", 66191.8, 66533.9, 66068.3, 66520.8),
    ("03-28 11:00", 66520.9, 66529.4, 66087.3, 66288.5),
    ("03-28 15:00", 66288.4, 67284.0, 66191.7, 66982.3),
    ("03-28 19:00", 66982.4, 67065.0, 66644.0, 66873.0),
    ("03-28 23:00", 66873.0, 66978.0, 66233.6, 66334.8),
    ("03-29 03:00", 66334.8, 67100.0, 66235.6, 66875.7),
    ("03-29 07:00", 66875.7, 66907.5, 66521.4, 66632.5),
    ("03-29 11:00", 66632.4, 66986.8, 66375.5, 66780.8),
    ("03-29 15:00", 66780.8, 66849.0, 66288.1, 66500.0),
    ("03-29 19:00", 66499.9, 66639.0, 66111.0, 66320.2),
    ("03-29 23:00", 66320.3, 66767.9, 64918.2, 65977.9),
    ("03-30 03:00", 65978.0, 67487.7, 65754.2, 67139.8),
    ("03-30 07:00", 67140.0, 67777.0, 67129.3, 67595.9),
    ("03-30 11:00", 67595.9, 67998.0, 67333.3, 67651.5),
    ("03-30 15:00", 67651.5, 68148.4, 67055.0, 67590.2),
    ("03-30 19:00", 67590.2, 67614.9, 66200.1, 66516.0),
    ("03-30 23:00", 66515.9, 66973.5, 66377.1, 66764.4),
    ("03-31 03:00", 66764.4, 68377.0, 66498.9, 67670.8),
    ("03-31 07:00", 67670.8, 67865.7, 67071.9, 67343.8),
    ("03-31 11:00", 67343.9, 67476.9, 65938.0, 66652.4),
    ("03-31 15:00", 66652.4, 67765.8, 66374.4, 66700.0),
    ("03-31 19:00", 66700.0, 68600.0, 66695.9, 67803.0),
    ("03-31 23:00", 67803.0, 68382.9, 67794.8, 68241.5),
    ("04-01 03:00", 68241.4, 68330.0, 67534.9, 68134.0),
    ("04-01 07:00", 68134.0, 69288.0, 67965.0, 68651.9),
    ("04-01 11:00", 68651.9, 68821.5, 68360.0, 68669.9),
    ("04-01 15:00", 68670.0, 68938.8, 67883.7, 68877.0),
    ("04-01 16:00", 68876.9, 69142.6, 67900.4, 68143.8),
    ("04-01 19:00", 68876.9, 69142.6, 67900.4, 68143.8),
    ("04-01 20:00", 68143.7, 68510.6, 67927.0, 68086.5),
    ("04-01 23:00", 68143.7, 68510.6, 67927.0, 68086.5),
    ("04-02 00:00", 68086.4, 68639.1, 66455.9, 66538.4),
    ("04-02 03:00", 68086.4, 68639.1, 66455.9, 66538.4),
    ("04-02 04:00", 66538.4, 66898.5, 66171.8, 66887.9),
    ("04-02 07:00", 66538.4, 66898.5, 66171.8, 66887.9),
    ("04-02 08:00", 66887.8, 66887.9, 66065.1, 66180.6),
    ("04-02 11:00", 66887.8, 66887.9, 66065.1, 66180.6),
    ("04-02 12:00", 66180.6, 67080.0, 65676.1, 66810.6),
    ("04-02 15:00", 66180.6, 67080.0, 65676.1, 66810.6),
    ("04-02 16:00", 66810.6, 67400.0, 66550.0, 66943.2),
    ("04-02 19:00", 66810.6, 67400.0, 66550.0, 66943.2),
    ("04-02 20:00", 66943.2, 67078.9, 66681.3, 66868.5),
    ("04-02 23:00", 66943.2, 67078.9, 66681.3, 66868.5),
    ("04-03 00:00", 66868.6, 66976.2, 66240.0, 66550.0),
    ("04-03 03:00", 66868.6, 66976.2, 66240.0, 66550.0),
    ("04-03 04:00", 66550.1, 67233.3, 66375.1, 67008.8),
    ("04-03 07:00", 66550.1, 67233.3, 66375.1, 67008.8),
    ("04-03 08:00", 67008.8, 67258.0, 66644.0, 66983.4),
    ("04-03 11:00", 67008.8, 67258.0, 66644.0, 66983.4),
    ("04-03 12:00", 66983.5, 67350.0, 66478.5, 66806.1),
    ("04-03 15:00", 66983.5, 67350.0, 66478.5, 66806.1),
    ("04-03 16:00", 66806.0, 67046.1, 66714.1, 66857.0),
    ("04-03 19:00", 66806.0, 67046.1, 66714.1, 66857.0),
    ("04-03 20:00", 66857.0, 66946.3, 66791.8, 66930.0),
    ("04-03 23:00", 66857.0, 66946.3, 66791.8, 66930.0),
    ("04-04 00:00", 66930.0, 66935.3, 66773.3, 66799.1),
    ("04-04 03:00", 66930.0, 66935.3, 66773.3, 66799.1),
    ("04-04 04:00", 66799.1, 67023.7, 66745.5, 66982.0),
    ("04-04 07:00", 66799.1, 67023.7, 66745.5, 66982.0),
    ("04-04 08:00", 66982.1, 67223.8, 66874.5, 67128.9),
    ("04-04 11:00", 66982.1, 67223.8, 66874.5, 67128.9),
    ("04-04 12:00", 67128.9, 67554.5, 67003.7, 67357.3),
    ("04-04 15:00", 67128.9, 67554.5, 67003.7, 67357.3),
    ("04-04 16:00", 67357.4, 67523.8, 67226.4, 67262.7),
    ("04-04 19:00", 67357.4, 67523.8, 67226.4, 67262.7),
    ("04-04 20:00", 67262.8, 67452.7, 67150.6, 67271.0),
    ("04-04 23:00", 67262.8, 67452.7, 67150.6, 67271.0),
    ("04-05 00:00", 67271.1, 67279.2, 66900.0, 67113.5),
    ("04-05 03:00", 67271.1, 67279.2, 66900.0, 67113.5),
    ("04-05 04:00", 67113.4, 67160.0, 66575.5, 66787.4),
    ("04-05 07:00", 67113.4, 67160.0, 66575.5, 66787.4),
    ("04-05 08:00", 66787.4, 67132.8, 66782.1, 66972.7),
    ("04-05 11:00", 66787.4, 67132.8, 66782.1, 66972.7),
    ("04-05 12:00", 66972.7, 67828.6, 66650.0, 67272.2),
    ("04-05 15:00", 66972.7, 67828.6, 66650.0, 67272.2),
    ("04-05 16:00", 67272.2, 67540.0, 67132.2, 67329.1),
    ("04-05 19:00", 67272.2, 67540.0, 67132.2, 67329.1),
    ("04-05 20:00", 67329.1, 69108.0, 67302.4, 68997.9),
    ("04-05 23:00", 67329.1, 69108.0, 67302.4, 68997.9),
    ("04-06 00:00", 68997.9, 69583.0, 68740.2, 69092.4),
    ("04-06 03:00", 68997.9, 69583.0, 68740.2, 69092.4),
    ("04-06 04:00", 69092.3, 69338.2, 68769.6, 69089.7),
    ("04-06 07:00", 69092.3, 69338.2, 68769.6, 69089.7),
    ("04-06 08:00", 69089.8, 70252.9, 69047.7, 69583.6),
    ("04-06 11:00", 69089.8, 69225.0, 69047.7, 69199.9),
    ("04-06 12:00", 69583.5, 69931.9, 69088.0, 69922.5),
    ("04-06 16:00", 69922.4, 70332.5, 69240.0, 69704.8),
    ("04-06 20:00", 69704.8, 69940.0, 68227.5, 68817.9),
    ("04-07 00:00", 68817.9, 69111.8, 68241.9, 68746.3),
    ("04-07 03:00", 69200.0, 69500.0, 69000.0, 69300.0),
    ("04-07 04:00", 68746.4, 68955.6, 68400.6, 68592.1),
    ("04-07 08:00", 68592.0, 69219.0, 68033.0, 68310.8),
    ("04-07 12:00", 68310.7, 68613.8, 67711.0, 68138.4),
    ("04-07 16:00", 68138.5, 69068.6, 68049.9, 68975.9),
    ("04-07 20:00", 68975.9, 72743.4, 68975.9, 71890.2),
    ("04-08 00:00", 71890.2, 72086.4, 71186.0, 71259.6),
    ("04-08 04:00", 71259.7, 71919.0, 71250.0, 71612.0),
    ("04-08 08:00", 71612.1, 71945.0, 71367.0, 71650.2),

    ("04-08 12:00", 71650.2, 72858.5, 70671.6, 71274.8),
    ("04-08 16:00", 71274.9, 71934.5, 70980.0, 71283.0),
    ("04-08 20:00", 71283.0, 71726.7, 70850.9, 71038.1),
    ("04-09 00:00", 71038.2, 71168.0, 70428.0, 70961.2),
    ("04-09 04:00", 70961.2, 71087.8, 70666.0, 70945.0),
    ("04-09 08:00", 70945.0, 71533.0, 70831.9, 71109.9),
    ("04-09 12:00", 71109.9, 72320.0, 70470.2, 72108.0),
    ("04-09 16:00", 72108.0, 72517.9, 71688.8, 72055.9),
    ("04-09 20:00", 72055.8, 73128.0, 71539.9, 71750.4),
    ("04-10 00:00", 71750.4, 72350.0, 71546.0, 71837.3),
    ("04-10 04:00", 71837.3, 72243.6, 71382.1, 71461.2),
    ("04-10 08:00", 71461.2, 72229.0, 71395.0, 72092.7),

    ("04-10 12:00", 72092.8, 73255.7, 71868.5, 72421.0),

    ("04-10 16:00", 72421.1, 73223.4, 72350.0, 73187.3),
    ("04-10 20:00", 73187.4, 73450.0, 72669.1, 72917.4),
    ("04-11 00:00", 72917.4, 73066.2, 72615.0, 72835.1),
    ("04-11 04:00", 72835.1, 72921.5, 72566.4, 72707.7),
    ("04-11 08:00", 72707.8, 72886.0, 72580.0, 72868.2),
    ("04-11 12:00", 72868.2, 72945.0, 72451.9, 72817.3),
    ("04-11 16:00", 72817.3, 73773.4, 72775.3, 73635.9),
    ("04-11 20:00", 73635.9, 73648.8, 72861.2, 73013.4),
    ("04-12 00:00", 73013.4, 73094.4, 71259.0, 71563.6),
    ("04-12 04:00", 71563.6, 71750.0, 71369.7, 71628.1),
    ("04-12 08:00", 71628.2, 71750.0, 71309.7, 71435.0),
    ("04-12 12:00", 71435.0, 71478.0, 70566.5, 70856.2),
    ("04-12 16:00", 70856.1, 71199.0, 70777.0, 71055.2),
    ("04-12 20:00", 71055.2, 71423.9, 70458.2, 70711.1),

    ("04-13 00:00", 70711.2, 71245.0, 70574.0, 70944.8),
    ("04-13 04:00", 70944.8, 71114.9, 70627.9, 70780.0),
    ("04-13 08:00", 70780.1, 70960.3, 70517.3, 70883.9),
    ("04-13 12:00", 70883.9, 72431.0, 70722.3, 71823.6),
    ("04-13 16:00", 71823.6, 73441.7, 71629.5, 73272.2),
    ("04-13 20:00", 73272.1, 74870.0, 72953.3, 74385.0),
    ("04-14 00:00", 74384.9, 74583.1, 73946.9, 74408.8),
    ("04-14 04:00", 74408.8, 74900.0, 74112.2, 74513.4),
    ("04-14 08:00", 74513.3, 74873.5, 74267.2, 74342.4),
    ("04-14 12:00", 74342.4, 76009.0, 74234.0, 75268.1),
    ("04-14 16:00", 75268.1, 75684.9, 73789.7, 74176.4),
    ("04-14 20:00", 74176.5, 74387.7, 73766.8, 74106.9),
    ("04-15 00:00", 74106.9, 74739.2, 74085.0, 74296.8),
    ("04-15 04:00", 74296.8, 74400.0, 73449.0, 73705.1),

    ("04-15 08:00", 73705.2, 74227.5, 73640.1, 74155.1),
    ("04-15 12:00", 74155.0, 74473.5, 73540.0, 73797.5),
    ("04-15 16:00", 73797.5, 75240.0, 73714.9, 74957.8),
    ("04-15 20:00", 74957.7, 75425.6, 74466.5, 74776.2),
    ("04-16 00:00", 74776.3, 75232.7, 74400.0, 74851.9),
    ("04-16 04:00", 74851.9, 75130.0, 74590.3, 74667.7),

    ("04-16 08:00", 74667.7, 74866.9, 74226.2, 74528.4),
    ("04-16 12:00", 74528.4, 74981.1, 73256.8, 74659.5),
    ("04-16 16:00", 74659.5, 75378.1, 73873.5, 75309.4),
    ("04-16 20:00", 75309.5, 75500.0, 74736.5, 75106.8),
    ("04-17 00:00", 75106.8, 75118.4, 74480.0, 74582.8),
    ("04-17 04:00", 74582.8, 75060.4, 74508.2, 75047.4),
    ("04-17 08:00", 75047.4, 76350.0, 74951.6, 75542.2),
    ("04-17 12:00", 75542.1, 77999.9, 75481.8, 77736.2),
    ("04-17 16:00", 77736.2, 78300.0, 76921.9, 77348.8),
    ("04-17 20:00", 77349.2, 77566.0, 76854.2, 77030.6),
    ("04-18 00:00", 77030.6, 77380.0, 76903.2, 76964.3),
    ("04-18 04:00", 76964.4, 77233.6, 76824.1, 76951.0),
    ("04-18 08:00", 76951.0, 77004.2, 75710.6, 76002.0),

    ("04-18 12:00", 76002.0, 76342.7, 75738.0, 76124.8),

    ("04-18 16:00", 76124.8, 76176.6, 75395.9, 75604.2),
    ("04-18 20:00", 75604.2, 75843.3, 75551.0, 75653.8),
    ("04-19 00:00", 75653.8, 75804.0, 75314.0, 75473.0),
    ("04-19 04:00", 75472.9, 75747.3, 74824.3, 75205.6),

    ("04-19 08:00", 75205.7, 75589.2, 74863.6, 75557.4),

    ("04-19 12:00", 75557.5, 76200.0, 75342.3, 75807.6),

    ("04-19 16:00", 75807.7, 75817.7, 74550.0, 74917.9),
    ("04-19 20:00", 74918.0, 74920.2, 73700.2, 73758.4),

    ("04-20 00:00", 73758.4, 74697.6, 73669.0, 74593.9),
    ("04-20 04:00", 74593.9, 75539.3, 74061.2, 74795.5),
    ("04-20 08:00", 74795.5, 75375.1, 74563.2, 75148.7),

    ("04-20 12:00", 75148.8, 75750.0, 74639.5, 75668.1),
    ("04-20 16:00", 75668.1, 76449.8, 75242.5, 76252.5),

    ("04-20 20:00", 76252.5, 76531.0, 75556.2, 75790.1),
    ("04-21 00:00", 75790.1, 76232.3, 75433.1, 75669.1),
    ("04-21 04:00", 75669.1, 76276.6, 75558.8, 76050.0),

    ("04-21 08:00", 76050.0, 76999.0, 76025.0, 76408.3),

    ("04-21 12:00", 76408.3, 76574.3, 75355.2, 75799.9),

    ("04-21 16:00", 75800.0, 76155.0, 74777.9, 74988.6),

    ("04-21 20:00", 74988.7, 76396.2, 74942.2, 76288.2),
    ("04-22 00:00", 76288.3, 77699.0, 76078.6, 77488.3),
    ("04-22 04:00", 77488.4, 78447.5, 77321.7, 77979.8),

    ("04-22 08:00", 77979.7, 78365.8, 77895.3, 78263.2),

    ("04-22 12:00", 78263.2, 79370.0, 78060.0, 79234.3),

    ("04-22 16:00", 79234.3, 79444.0, 78586.7, 78791.3),

    ("04-22 20:00", 78791.3, 78868.9, 78111.6, 78139.8),
    ("04-23 00:00", 78139.7, 78534.9, 77410.7, 77704.3),
    ("04-23 04:00", 77704.3, 78310.1, 77627.4, 78009.1),

    ("04-23 08:00", 78009.1, 78142.2, 76504.6, 77649.9),

    ("04-23 12:00", 77650.0, 78648.0, 77322.8, 78329.2),

    ("04-23 16:00", 78329.3, 78466.8, 76900.1, 77670.5),
    ("04-23 20:00", 77670.4, 78299.0, 77598.4, 78216.8),
    ("04-24 00:00", 78217.4, 78546.0, 77500.0, 77690.1),
    ("04-24 04:00", 77690.1, 78019.2, 77401.5, 77620.5),

    ("04-24 08:00", 77620.5, 78346.1, 77355.8, 78194.8),

    ("04-24 12:00", 78194.9, 78432.9, 77521.0, 78007.3),

    ("04-24 16:00", 78007.3, 78031.9, 77308.0, 77596.1),

    ("04-24 20:00", 77596.0, 77727.0, 77206.8, 77395.4),

    ("04-25 00:00", 77395.3, 77678.0, 77254.7, 77629.0),
    ("04-25 04:00", 77629.0, 77653.2, 77400.0, 77449.9),
    ("04-25 08:00", 77449.9, 77847.0, 77444.0, 77638.7),
    ("04-25 12:00", 77638.7, 77719.1, 77263.0, 77289.3),

    ("04-25 16:00", 77289.3, 77411.8, 77100.0, 77285.6),

    ("04-25 20:00", 77285.7, 77615.7, 77267.3, 77585.0),
    ("04-26 00:00", 77585.0, 77607.7, 77280.0, 77349.3),
    ("04-26 04:00", 77349.3, 78164.7, 77338.4, 78061.5),

    ("04-26 08:00", 78061.5, 78182.8, 77880.0, 78050.0),

    ("04-26 12:00", 78050.0, 78136.5, 77715.0, 78007.9),

    ("04-26 16:00", 78007.9, 78477.9, 77815.0, 78183.1),

    ("04-26 20:00", 78183.2, 78994.8, 77777.0, 78613.5),

    ("04-27 00:00", 78614.4, 79455.0, 78319.1, 79065.1),
    ("04-27 04:00", 79065.1, 79128.1, 77408.6, 77556.7),

    ("04-27 08:00", 77556.7, 77949.9, 77500.0, 77804.3),
    ("04-27 12:00", 77804.3, 78232.0, 76524.0, 76760.0),
    ("04-27 16:00", 76760.0, 76902.7, 76400.0, 76844.4),

    ("04-27 20:00", 76844.3, 77419.7, 76714.8, 77331.2),
    ("04-28 00:00", 77331.2, 77450.0, 76632.4, 76770.6),
    ("04-28 04:00", 76770.6, 77132.4, 76324.1, 76828.4),
    ("04-28 08:00", 76828.3, 76956.0, 76088.0, 76198.8),
    ("04-28 12:00", 76198.9, 76403.7, 75635.6, 76027.8),
    ("04-28 16:00", 76027.7, 76352.0, 75840.3, 76293.6),
    ("04-28 20:00", 76293.5, 76448.0, 76150.0, 76298.1),
    ("04-29 00:00", 76298.2, 77098.8, 76138.7, 76955.7),
    ("04-29 04:00", 76955.7, 77432.1, 76839.8, 77003.8),
    ("04-29 08:00", 77003.8, 77873.2, 76918.5, 77552.5),
    ("04-29 12:00", 77552.5, 77563.6, 75675.2, 75889.1),
    ("04-29 16:00", 75889.1, 76220.0, 74868.0, 75518.5),
    ("04-29 20:00", 75518.4, 76061.2, 75448.0, 75749.9),
    ("04-30 00:00", 75749.9, 76445.0, 75448.9, 75882.1),
    ("04-30 04:00", 75881.6, 76148.0, 75273.5, 76129.9),
    ("04-30 08:00", 76129.9, 76332.6, 75836.0, 76032.9),

    ("04-30 12:00", 76032.9, 76630.3, 76009.8, 76423.0),
    ("04-30 16:00", 76423.0, 76470.5, 76060.4, 76366.7),

    ("04-30 20:00", 76366.7, 76536.2, 76155.1, 76305.4),

    ("05-01 00:00", 76305.4, 77421.2, 76265.4, 77082.6),
    ("05-01 04:00", 77082.6, 77177.1, 76833.7, 77100.0),
    ("05-01 08:00", 77099.9, 77588.4, 77010.5, 77429.5),
    ("05-01 12:00", 77429.6, 78879.9, 77368.2, 78395.4),
    ("05-01 16:00", 78395.4, 78642.0, 78081.5, 78316.9),
    ("05-01 20:00", 78317.0, 78402.9, 77717.7, 78192.0),
    ("05-02 00:00", 78191.9, 78503.9, 78123.0, 78377.7),
    ("05-02 04:00", 78377.7, 78416.8, 77979.3, 78181.6),
    ("05-02 08:00", 78181.6, 78359.2, 78055.7, 78105.7),

    ("05-02 12:00", 78105.7, 78458.2, 78056.0, 78449.8),
    ("05-02 16:00", 78449.8, 78565.9, 78277.0, 78443.8),

    ("05-02 20:00", 78444.1, 79145.0, 78376.0, 78652.9),
]

# =================== 5M MUM VERİSİ (Binance API) ===================
# P59: 5dk zaman dilimi eklendi — giriş zamanlaması mikro-analizi için
CANDLES_5M = [

    ("04-10 10:15", 71780.0, 71780.0, 71750.1, 71780.0),
    ("04-10 10:20", 71780.0, 71780.0, 71678.5, 71699.9),
    ("04-10 10:25", 71699.9, 71741.6, 71658.8, 71696.9),
    ("04-10 10:30", 71697.0, 71729.5, 71691.2, 71724.2),
    ("04-10 10:35", 71724.1, 71748.0, 71688.9, 71738.8),
    ("04-10 10:40", 71738.7, 71788.0, 71729.6, 71768.8),
    ("04-10 10:45", 71768.7, 71800.0, 71739.6, 71800.0),
    ("04-10 10:50", 71800.0, 71910.0, 71793.4, 71860.7),
    ("04-10 10:55", 71860.8, 71900.6, 71860.7, 71872.4),
    ("04-10 11:00", 71872.5, 71997.3, 71861.5, 71959.9),
    ("04-10 11:05", 71960.0, 72073.5, 71925.1, 72070.0),
    ("04-10 11:10", 72070.1, 72133.7, 72022.4, 72085.0),
    ("04-10 11:15", 72085.0, 72160.9, 72058.0, 72117.9),
    ("04-10 11:20", 72117.9, 72194.0, 72105.7, 72143.2),
    ("04-10 11:25", 72143.2, 72175.3, 72102.1, 72175.2),
    ("04-10 11:30", 72175.2, 72195.0, 72091.4, 72117.4),
    ("04-10 11:35", 72117.4, 72229.0, 72117.4, 72200.1),
    ("04-10 11:40", 72200.2, 72221.9, 72139.8, 72145.9),
    ("04-10 11:45", 72145.9, 72214.0, 72077.5, 72197.5),
    ("04-10 11:50", 72197.6, 72202.2, 72117.0, 72117.1),
    ("04-10 11:55", 72117.1, 72118.9, 72054.0, 72092.7),
    ("04-10 12:00", 72092.8, 72148.3, 72053.2, 72148.2),
    ("04-10 12:05", 72148.2, 72182.4, 72085.1, 72101.2),
    ("04-10 12:10", 72101.1, 72101.2, 72044.1, 72050.5),
    ("04-10 12:15", 72050.6, 72147.1, 72034.7, 72145.8),
    ("04-10 12:20", 72145.8, 72294.9, 72046.0, 72086.1),
    ("04-10 12:25", 72086.3, 72178.8, 71960.5, 72134.7),
    ("04-10 12:30", 72134.6, 72467.3, 71999.2, 72295.8),
    ("04-10 12:35", 72295.8, 72295.8, 72150.0, 72253.8),
    ("04-10 12:40", 72253.8, 72393.3, 72247.9, 72277.6),
    ("04-10 12:45", 72277.7, 72372.2, 72234.3, 72372.2),
    ("04-10 12:50", 72372.2, 72372.2, 72156.7, 72171.7),
    ("04-10 12:55", 72171.7, 72236.7, 72155.7, 72225.5),
    ("04-10 13:00", 72225.4, 72225.4, 72150.0, 72163.6),

    ("04-10 14:15", 72667.3, 72812.9, 72590.9, 72722.3),
    ("04-10 14:20", 72722.3, 73031.0, 72722.3, 73024.7),
    ("04-10 14:25", 73024.6, 73050.0, 72839.8, 72933.0),
    ("04-10 14:30", 72933.0, 73100.0, 72927.0, 73032.6),
    ("04-10 14:35", 73032.5, 73123.9, 72969.0, 73020.0),
    ("04-10 14:40", 73020.0, 73041.1, 72660.7, 72819.1),
    ("04-10 14:45", 72819.2, 72888.0, 72649.0, 72681.4),
    ("04-10 14:50", 72681.4, 72925.0, 72681.4, 72793.8),
    ("04-10 14:55", 72793.8, 72888.0, 72716.5, 72870.6),
    ("04-10 15:00", 72870.6, 72970.0, 72851.0, 72865.3),
    ("04-10 15:05", 72865.3, 73064.8, 72784.8, 73049.8),
    ("04-10 15:10", 73049.8, 73084.0, 72977.9, 72978.3),
    ("04-10 15:15", 72978.0, 73005.0, 72881.8, 72981.1),
    ("04-10 15:20", 72981.2, 73255.7, 72943.0, 73220.8),
    ("04-10 15:25", 73220.9, 73220.9, 72700.0, 72740.5),
    ("04-10 15:30", 72740.4, 72806.3, 72634.1, 72667.2),
    ("04-10 15:35", 72667.2, 72693.7, 72618.0, 72688.0),
    ("04-10 15:40", 72687.9, 72709.0, 72537.7, 72703.9),
    ("04-10 15:45", 72703.9, 72723.9, 72479.6, 72531.0),
    ("04-10 15:50", 72531.0, 72572.4, 72451.1, 72461.1),
    ("04-10 15:55", 72461.3, 72483.7, 72309.5, 72421.0),
    ("04-10 16:00", 72421.1, 72518.6, 72350.0, 72482.9),
    ("04-10 16:05", 72482.8, 72561.5, 72432.3, 72514.8),
    ("04-10 16:10", 72515.0, 72676.4, 72515.0, 72661.2),
    ("04-10 16:15", 72661.2, 72798.6, 72625.6, 72700.0),
    ("04-10 16:20", 72700.0, 72720.0, 72522.5, 72717.9),
    ("04-10 16:25", 72718.0, 72730.2, 72636.1, 72730.1),
    ("04-10 16:30", 72730.2, 72750.0, 72528.5, 72748.6),
    ("04-10 16:35", 72748.5, 72767.3, 72662.5, 72676.0),
    ("04-10 16:40", 72676.0, 72683.2, 72600.8, 72683.1),
    ("04-10 16:45", 72683.2, 72760.0, 72663.8, 72729.3),
    ("04-10 16:50", 72729.3, 72925.5, 72729.3, 72859.9),
    ("04-10 16:55", 72860.0, 73024.1, 72856.7, 72954.0),
    ("04-10 17:00", 72954.0, 72964.5, 72820.3, 72841.3),

    ("04-12 22:30", 70636.4, 70749.6, 70458.2, 70720.1),
    ("04-12 22:35", 70720.1, 70900.0, 70707.0, 70834.6),
    ("04-12 22:40", 70834.6, 70896.2, 70750.0, 70784.9),
    ("04-12 22:45", 70784.9, 70868.2, 70750.0, 70750.0),
    ("04-12 22:50", 70749.9, 70854.5, 70749.9, 70810.9),
    ("04-12 22:55", 70811.0, 70905.9, 70787.1, 70875.6),
    ("04-12 23:00", 70875.5, 70882.4, 70682.0, 70753.9),
    ("04-12 23:05", 70753.9, 70802.8, 70700.0, 70719.7),
    ("04-12 23:10", 70719.6, 70757.8, 70588.8, 70588.8),
    ("04-12 23:15", 70588.8, 70676.1, 70561.4, 70664.5),
    ("04-12 23:20", 70664.6, 70664.6, 70583.2, 70587.3),
    ("04-12 23:25", 70587.4, 70731.2, 70587.3, 70684.4),
    ("04-12 23:30", 70684.3, 70684.4, 70533.0, 70550.0),
    ("04-12 23:35", 70550.1, 70632.8, 70550.0, 70601.6),
    ("04-12 23:40", 70601.5, 70707.9, 70565.0, 70702.2),
    ("04-12 23:45", 70702.2, 70709.0, 70552.8, 70565.0),
    ("04-12 23:50", 70565.0, 70750.0, 70564.9, 70696.8),
    ("04-12 23:55", 70696.8, 70762.6, 70677.8, 70711.1),
    ("04-13 00:00", 70711.2, 70719.5, 70574.0, 70657.9),
    ("04-13 00:05", 70658.0, 70861.1, 70657.9, 70860.4),
    ("04-13 00:10", 70860.4, 70887.3, 70778.5, 70884.1),
    ("04-13 00:15", 70884.1, 70893.5, 70796.6, 70815.5),
    ("04-13 00:20", 70815.6, 70896.0, 70802.8, 70886.4),
    ("04-13 00:25", 70886.1, 71062.0, 70851.9, 70935.4),
    ("04-13 00:30", 70935.4, 71050.0, 70907.9, 71044.7),
    ("04-13 00:35", 71044.6, 71082.0, 71004.3, 71004.3),
    ("04-13 00:40", 71004.2, 71093.6, 70970.1, 71023.5),
    ("04-13 00:45", 71023.6, 71129.2, 70978.1, 71094.8),
    ("04-13 00:50", 71094.9, 71225.0, 71067.6, 71157.8),
    ("04-13 00:55", 71157.7, 71164.3, 71080.0, 71130.0),
    ("04-13 01:00", 71129.9, 71176.0, 71066.4, 71131.0),
    ("04-13 01:05", 71131.2, 71150.4, 71070.0, 71090.2),
    ("04-13 01:10", 71090.2, 71193.6, 71075.2, 71099.6),
    ("04-13 01:15", 71099.6, 71110.5, 71030.0, 71066.8),

    ("04-15 08:05", 73733.6, 73804.1, 73715.8, 73715.9),
    ("04-15 08:10", 73715.8, 73826.8, 73681.7, 73815.7),
    ("04-15 08:15", 73815.8, 73844.0, 73800.8, 73830.1),
    ("04-15 08:20", 73830.1, 73914.9, 73830.0, 73914.4),
    ("04-15 08:25", 73914.4, 73963.3, 73911.9, 73959.7),
    ("04-15 08:30", 73959.7, 74120.0, 73931.6, 74098.9),
    ("04-15 08:35", 74098.9, 74130.0, 74059.5, 74064.8),
    ("04-15 08:40", 74064.9, 74104.0, 74045.5, 74060.0),
    ("04-15 08:45", 74059.9, 74063.2, 73991.7, 74019.9),
    ("04-15 08:50", 74019.9, 74154.3, 73996.2, 74122.6),
    ("04-15 08:55", 74122.6, 74139.5, 74070.4, 74070.4),
    ("04-15 09:00", 74070.4, 74143.5, 73987.4, 74007.2),
    ("04-15 09:05", 74007.1, 74050.0, 73968.0, 73976.8),
    ("04-15 09:10", 73976.8, 74033.3, 73920.2, 73989.3),
    ("04-15 09:15", 73989.2, 74047.2, 73981.6, 74047.2),
    ("04-15 09:20", 74047.1, 74047.1, 74004.1, 74004.2),
    ("04-15 09:25", 74004.2, 74010.0, 73886.0, 73914.6),
    ("04-15 09:30", 73914.7, 73977.6, 73888.8, 73888.9),
    ("04-15 09:35", 73888.9, 73954.8, 73886.5, 73887.2),
    ("04-15 09:40", 73887.1, 73950.0, 73868.0, 73929.3),
    ("04-15 09:45", 73929.3, 73945.8, 73889.0, 73914.3),
    ("04-15 09:50", 73914.3, 73940.4, 73884.0, 73936.4),
    ("04-15 09:55", 73936.3, 73998.8, 73925.0, 73968.3),
    ("04-15 10:00", 73968.3, 74038.4, 73941.3, 73970.0),
    ("04-15 10:05", 73969.9, 74142.7, 73960.0, 74090.1),
    ("04-15 10:10", 74090.0, 74125.0, 74059.5, 74071.1),
    ("04-15 10:15", 74071.1, 74075.6, 73950.1, 73962.5),
    ("04-15 10:20", 73962.5, 73982.7, 73898.0, 73943.2),
    ("04-15 10:25", 73943.2, 73977.0, 73840.4, 73865.4),
    ("04-15 10:30", 73865.4, 73879.9, 73760.0, 73796.6),
    ("04-15 10:35", 73796.7, 73831.7, 73750.0, 73805.1),
    ("04-15 10:40", 73805.1, 74017.0, 73805.1, 74017.0),
    ("04-15 10:45", 74017.0, 74222.7, 74017.0, 74049.3),
    ("04-15 10:50", 74049.4, 74077.3, 73959.1, 73959.2),

    ("04-15 10:55", 73959.2, 73959.3, 73777.4, 73825.9),
    ("04-15 11:00", 73825.9, 73919.9, 73825.9, 73864.1),
    ("04-15 11:05", 73864.2, 73966.5, 73838.0, 73949.9),
    ("04-15 11:10", 73949.9, 74056.2, 73948.2, 73987.9),
    ("04-15 11:15", 73987.9, 73987.9, 73907.0, 73907.1),
    ("04-15 11:20", 73907.1, 73944.7, 73881.3, 73936.9),
    ("04-15 11:25", 73937.0, 73975.6, 73920.0, 73920.0),

    ("04-16 06:25", 75004.2, 75020.4, 74972.7, 74979.1),
    ("04-16 06:30", 74979.1, 74997.7, 74922.3, 74950.0),
    ("04-16 06:35", 74950.1, 74981.0, 74935.7, 74966.0),
    ("04-16 06:40", 74966.1, 74966.1, 74801.8, 74907.2),
    ("04-16 06:45", 74907.3, 74969.0, 74865.0, 74962.4),
    ("04-16 06:50", 74962.3, 74999.9, 74922.8, 74948.5),
    ("04-16 06:55", 74948.6, 74992.7, 74921.8, 74985.9),
    ("04-16 07:00", 74985.9, 75039.0, 74935.1, 75018.6),
    ("04-16 07:05", 75018.7, 75018.7, 74901.8, 74940.1),
    ("04-16 07:10", 74940.0, 74940.0, 74847.0, 74872.8),
    ("04-16 07:15", 74872.8, 74905.4, 74854.5, 74883.4),
    ("04-16 07:20", 74883.3, 74888.2, 74856.5, 74859.7),
    ("04-16 07:25", 74859.7, 74869.9, 74808.9, 74863.0),
    ("04-16 07:30", 74863.0, 74869.4, 74806.8, 74850.1),
    ("04-16 07:35", 74850.0, 74853.8, 74800.4, 74830.7),
    ("04-16 07:40", 74830.6, 74852.3, 74800.0, 74821.8),
    ("04-16 07:45", 74821.7, 74824.4, 74673.9, 74726.8),
    ("04-16 07:50", 74726.8, 74730.0, 74590.3, 74615.0),
    ("04-16 07:55", 74615.1, 74675.6, 74600.0, 74667.7),
    ("04-16 08:00", 74667.7, 74711.8, 74563.7, 74583.8),
    ("04-16 08:05", 74583.8, 74619.4, 74488.0, 74496.8),
    ("04-16 08:10", 74496.7, 74541.6, 74466.9, 74490.5),
    ("04-16 08:15", 74490.5, 74620.6, 74473.7, 74589.0),
    ("04-16 08:20", 74589.0, 74696.3, 74578.6, 74636.8),
    ("04-16 08:25", 74636.9, 74659.8, 74560.0, 74647.7),
    ("04-16 08:30", 74647.8, 74696.4, 74619.8, 74670.5),
    ("04-16 08:35", 74670.5, 74677.0, 74603.0, 74620.1),
    ("04-16 08:40", 74620.1, 74657.8, 74514.1, 74638.2),
    ("04-16 08:45", 74638.3, 74706.9, 74623.3, 74679.1),
    ("04-16 08:50", 74679.1, 74682.5, 74625.0, 74651.8),
    ("04-16 08:55", 74651.9, 74678.7, 74605.4, 74634.3),
    ("04-16 09:00", 74634.2, 74710.9, 74592.5, 74698.4),
    ("04-16 09:05", 74698.4, 74698.4, 74633.0, 74690.8),
    ("04-16 09:10", 74690.8, 74720.0, 74657.2, 74704.9),

    ("04-18 10:05", 76344.9, 76398.7, 76214.2, 76214.3),
    ("04-18 10:10", 76214.3, 76288.9, 76166.0, 76250.0),
    ("04-18 10:15", 76249.9, 76334.6, 76249.9, 76329.9),
    ("04-18 10:20", 76330.0, 76354.8, 76235.4, 76296.6),
    ("04-18 10:25", 76296.6, 76314.2, 76244.5, 76287.4),
    ("04-18 10:30", 76287.4, 76287.4, 76179.9, 76221.9),
    ("04-18 10:35", 76221.8, 76247.2, 76182.7, 76244.9),
    ("04-18 10:40", 76244.9, 76273.2, 76183.4, 76189.9),
    ("04-18 10:45", 76189.9, 76258.0, 76132.6, 76200.0),
    ("04-18 10:50", 76200.0, 76204.1, 76091.8, 76117.8),
    ("04-18 10:55", 76117.7, 76150.0, 76091.8, 76150.0),
    ("04-18 11:00", 76150.0, 76150.0, 76020.0, 76073.4),
    ("04-18 11:05", 76073.5, 76078.0, 75870.0, 75932.2),
    ("04-18 11:10", 75932.2, 76021.9, 75871.0, 75905.0),
    ("04-18 11:15", 75905.0, 76039.9, 75883.6, 76011.5),
    ("04-18 11:20", 76011.5, 76061.8, 75977.6, 76033.1),
    ("04-18 11:25", 76033.2, 76034.5, 75997.8, 76034.5),
    ("04-18 11:30", 76034.5, 76135.8, 76023.5, 76080.0),
    ("04-18 11:35", 76080.0, 76080.1, 75778.6, 75779.7),
    ("04-18 11:40", 75779.7, 75840.3, 75710.6, 75803.9),
    ("04-18 11:45", 75804.0, 75874.8, 75750.0, 75806.6),
    ("04-18 11:50", 75806.6, 75973.7, 75791.4, 75943.2),
    ("04-18 11:55", 75943.2, 76065.0, 75901.8, 76002.0),
    ("04-18 12:00", 76002.0, 76194.3, 76000.0, 76189.7),
    ("04-18 12:05", 76189.7, 76191.3, 76108.6, 76136.3),
    ("04-18 12:10", 76136.3, 76177.8, 76089.2, 76161.7),
    ("04-18 12:15", 76161.6, 76277.4, 76148.0, 76176.8),
    ("04-18 12:20", 76176.8, 76177.7, 76085.0, 76152.9),
    ("04-18 12:25", 76152.9, 76157.7, 76100.0, 76100.1),
    ("04-18 12:30", 76100.1, 76181.5, 76070.6, 76135.8),
    ("04-18 12:35", 76135.7, 76137.2, 76011.0, 76011.0),
    ("04-18 12:40", 76011.1, 76144.4, 76000.0, 76140.6),
    ("04-18 12:45", 76140.5, 76209.7, 76138.3, 76204.7),
    ("04-18 12:50", 76204.7, 76220.0, 76184.6, 76184.7),

    ("04-18 15:55", 76083.5, 76158.0, 76083.5, 76124.8),
    ("04-18 16:00", 76124.8, 76124.8, 75983.8, 75990.1),
    ("04-18 16:05", 75990.0, 76087.9, 75990.0, 76087.8),
    ("04-18 16:10", 76087.9, 76176.6, 76087.8, 76144.0),
    ("04-18 16:15", 76144.1, 76144.1, 75584.1, 75932.2),
    ("04-18 16:20", 75932.3, 76075.4, 75863.4, 75993.9),
    ("04-18 16:25", 75993.9, 76093.4, 75980.8, 76041.2),
    ("04-18 16:30", 76041.2, 76088.6, 75941.2, 75991.0),
    ("04-18 16:35", 75991.0, 76050.0, 75990.9, 76009.1),
    ("04-18 16:40", 76009.1, 76009.5, 75940.3, 75943.1),
    ("04-18 16:45", 75943.0, 75976.4, 75870.0, 75890.4),
    ("04-18 16:50", 75890.4, 75890.4, 75807.1, 75863.6),
    ("04-18 16:55", 75863.6, 75915.2, 75843.1, 75897.9),
    ("04-18 17:00", 75897.9, 75897.9, 75812.1, 75852.1),
    ("04-18 17:05", 75852.0, 75856.6, 75750.0, 75823.8),
    ("04-18 17:10", 75823.7, 75930.5, 75724.8, 75781.9),
    ("04-18 17:15", 75781.9, 75843.3, 75781.9, 75832.3),
    ("04-18 17:20", 75832.4, 75837.6, 75741.9, 75800.0),
    ("04-18 17:25", 75800.1, 75843.3, 75761.6, 75809.3),
    ("04-18 17:30", 75809.3, 75843.3, 75806.1, 75843.2),
    ("04-18 17:35", 75843.3, 75843.3, 75828.5, 75835.2),
    ("04-18 17:40", 75835.1, 75842.9, 75822.0, 75829.7),
    ("04-18 17:45", 75829.7, 75843.3, 75829.6, 75841.0),
    ("04-18 17:50", 75841.1, 75843.3, 75827.3, 75831.5),
    ("04-18 17:55", 75831.5, 75831.6, 75783.8, 75783.9),
    ("04-18 18:00", 75783.9, 75783.9, 75629.3, 75728.9),
    ("04-18 18:05", 75728.8, 75805.1, 75665.6, 75793.8),
    ("04-18 18:10", 75793.9, 75795.8, 75748.5, 75756.1),
    ("04-18 18:15", 75756.0, 75756.1, 75550.0, 75576.3),
    ("04-18 18:20", 75576.3, 75655.6, 75552.3, 75588.6),
    ("04-18 18:25", 75588.6, 75650.1, 75555.7, 75618.3),
    ("04-18 18:30", 75618.3, 75638.5, 75501.5, 75599.5),
    ("04-18 18:35", 75599.4, 75625.5, 75481.6, 75524.7),
    ("04-18 18:40", 75524.8, 75541.9, 75395.9, 75528.7),

    ("04-18 18:45", 75528.8, 75697.4, 75503.9, 75620.1),
    ("04-18 18:50", 75620.1, 75647.8, 75498.1, 75499.9),
    ("04-18 18:55", 75499.8, 75612.6, 75490.0, 75603.7),
    ("04-18 19:00", 75603.7, 75695.3, 75574.5, 75665.7),
    ("04-18 19:05", 75665.7, 75724.0, 75634.8, 75696.1),
    ("04-18 19:10", 75696.1, 75760.8, 75689.1, 75705.5),
    ("04-18 19:15", 75705.5, 75761.1, 75700.1, 75700.1),
    ("04-18 19:20", 75700.1, 75700.1, 75569.9, 75590.8),

    ("04-19 05:50", 75554.9, 75555.0, 75500.0, 75514.9),
    ("04-19 05:55", 75514.9, 75518.0, 75490.0, 75505.1),
    ("04-19 06:00", 75505.1, 75505.1, 75411.0, 75416.4),
    ("04-19 06:05", 75416.5, 75479.1, 75354.0, 75393.9),
    ("04-19 06:10", 75393.9, 75430.4, 75350.0, 75350.1),
    ("04-19 06:15", 75350.1, 75354.1, 75234.2, 75336.6),
    ("04-19 06:20", 75336.7, 75404.1, 75323.4, 75400.1),
    ("04-19 06:25", 75400.2, 75402.8, 75364.5, 75364.5),
    ("04-19 06:30", 75364.5, 75435.0, 75364.4, 75425.5),
    ("04-19 06:35", 75425.5, 75445.9, 75404.2, 75411.8),
    ("04-19 06:40", 75411.8, 75419.1, 75380.2, 75387.4),
    ("04-19 06:45", 75387.5, 75390.7, 75358.0, 75371.0),
    ("04-19 06:50", 75371.0, 75390.0, 75359.3, 75360.0),
    ("04-19 06:55", 75360.0, 75360.1, 75315.1, 75359.7),
    ("04-19 07:00", 75359.6, 75363.2, 75262.5, 75317.7),
    ("04-19 07:05", 75317.6, 75329.6, 75168.0, 75192.9),
    ("04-19 07:10", 75192.9, 75250.0, 75185.3, 75194.7),
    ("04-19 07:15", 75194.8, 75194.8, 75057.0, 75071.9),
    ("04-19 07:20", 75072.0, 75099.9, 74824.3, 74950.1),
    ("04-19 07:25", 74950.1, 74995.2, 74921.5, 74930.3),
    ("04-19 07:30", 74930.5, 75050.0, 74930.4, 75011.6),
    ("04-19 07:35", 75011.7, 75064.0, 74959.5, 74993.1),
    ("04-19 07:40", 74993.1, 75188.4, 74993.0, 75134.5),
    ("04-19 07:45", 75134.4, 75165.1, 75115.5, 75122.0),
    ("04-19 07:50", 75122.1, 75222.0, 75095.8, 75191.7),
    ("04-19 07:55", 75191.7, 75250.0, 75181.6, 75205.6),
    ("04-19 08:00", 75205.7, 75219.1, 75130.0, 75142.3),
    ("04-19 08:05", 75142.4, 75188.1, 75130.0, 75157.4),
    ("04-19 08:10", 75157.4, 75240.0, 75157.2, 75220.6),
    ("04-19 08:15", 75220.6, 75250.0, 75179.2, 75190.5),
    ("04-19 08:20", 75190.6, 75193.0, 75141.1, 75154.3),
    ("04-19 08:25", 75154.3, 75175.2, 75090.0, 75090.3),
    ("04-19 08:30", 75090.3, 75119.8, 75024.3, 75100.0),
    ("04-19 08:35", 75100.0, 75213.7, 75094.0, 75160.2),

    ("04-19 08:40", 75160.2, 75211.4, 75153.1, 75186.3),

    ("04-19 08:45", 75186.3, 75216.2, 75165.3, 75210.0),
    ("04-19 08:50", 75210.1, 75230.7, 75130.0, 75216.7),

    ("04-19 09:35", 75067.1, 75100.1, 75001.0, 75014.2),
    ("04-19 09:40", 75014.2, 75061.5, 75013.5, 75020.0),
    ("04-19 09:45", 75020.0, 75020.1, 74863.6, 74963.3),
    ("04-19 09:50", 74963.4, 75000.0, 74914.0, 75000.0),
    ("04-19 09:55", 74999.9, 75000.0, 74927.0, 74974.6),
    ("04-19 10:00", 74974.6, 75051.9, 74888.0, 75000.1),
    ("04-19 10:05", 75000.0, 75000.0, 74921.1, 74955.6),
    ("04-19 10:10", 74955.6, 75010.1, 74940.6, 74994.2),
    ("04-19 10:15", 74994.4, 74994.4, 74951.1, 74971.7),
    ("04-19 10:20", 74971.7, 75049.5, 74967.0, 75007.0),
    ("04-19 10:25", 75007.1, 75081.2, 75007.0, 75044.6),
    ("04-19 10:30", 75044.5, 75064.8, 75027.7, 75061.4),
    ("04-19 10:35", 75061.3, 75061.4, 75025.0, 75025.1),
    ("04-19 10:40", 75025.0, 75058.2, 75010.3, 75050.8),
    ("04-19 10:45", 75050.9, 75091.8, 75007.6, 75091.8),
    ("04-19 10:50", 75091.7, 75179.3, 75090.8, 75161.3),
    ("04-19 10:55", 75161.2, 75199.0, 75141.5, 75175.5),
    ("04-19 11:00", 75175.5, 75210.1, 75170.0, 75183.4),
    ("04-19 11:05", 75183.3, 75400.0, 75171.9, 75395.7),
    ("04-19 11:10", 75395.7, 75418.4, 75270.6, 75383.6),
    ("04-19 11:15", 75383.6, 75513.6, 75357.7, 75367.4),
    ("04-19 11:20", 75367.5, 75389.6, 75295.0, 75351.4),
    ("04-19 11:25", 75351.3, 75390.0, 75304.2, 75331.5),
    ("04-19 11:30", 75331.5, 75419.2, 75329.4, 75373.1),
    ("04-19 11:35", 75373.0, 75430.0, 75360.0, 75413.2),
    ("04-19 11:40", 75413.2, 75490.4, 75413.2, 75472.9),
    ("04-19 11:45", 75473.0, 75505.1, 75450.0, 75500.0),
    ("04-19 11:50", 75500.1, 75589.2, 75477.3, 75555.9),
    ("04-19 11:55", 75555.8, 75574.6, 75513.6, 75557.4),
    ("04-19 12:00", 75557.5, 75600.0, 75509.9, 75591.2),
    ("04-19 12:05", 75591.1, 75631.8, 75520.6, 75615.5),
    ("04-19 12:10", 75615.6, 75647.2, 75452.2, 75636.2),
    ("04-19 12:15", 75636.2, 75665.7, 75590.0, 75622.7),
    ("04-19 12:20", 75622.6, 75622.7, 75528.7, 75530.9),

    ("04-19 12:25", 75530.9, 75531.0, 75455.8, 75474.6),

    ("04-19 12:30", 75474.7, 75500.0, 75444.5, 75499.6),
    ("04-19 12:35", 75499.5, 75499.6, 75426.6, 75427.6),
    ("04-19 12:40", 75427.5, 75477.8, 75386.4, 75457.8),
    ("04-19 12:45", 75457.8, 75477.0, 75417.8, 75433.6),
    ("04-19 12:50", 75433.5, 75525.8, 75433.5, 75504.2),
    ("04-19 12:55", 75504.2, 75642.4, 75504.2, 75529.3),
    ("04-19 13:00", 75529.2, 75638.2, 75505.1, 75637.9),
    ("04-19 13:05", 75638.0, 75741.1, 75616.3, 75729.6),
    ("04-19 13:10", 75729.6, 75732.1, 75616.8, 75719.7),
    ("04-19 13:15", 75719.7, 76045.0, 75679.0, 75989.0),
    ("04-19 13:20", 75988.9, 76200.0, 75877.3, 75996.6),
    ("04-19 13:25", 75996.6, 76091.7, 75958.1, 75999.0),
    ("04-19 13:30", 75999.0, 76066.0, 75913.3, 75963.2),
    ("04-19 13:35", 75963.3, 75998.9, 75883.1, 75985.8),
    ("04-19 13:40", 75985.9, 75995.7, 75930.0, 75988.6),
    ("04-19 13:45", 75988.7, 75988.7, 75824.7, 75886.2),
    ("04-19 13:50", 75886.1, 75928.7, 75857.2, 75874.0),
    ("04-19 13:55", 75874.1, 75900.0, 75808.0, 75877.9),
    ("04-19 14:00", 75878.0, 75974.9, 75688.7, 75758.6),
    ("04-19 14:05", 75758.6, 75760.1, 75625.9, 75649.4),
    ("04-19 14:10", 75649.5, 75760.2, 75642.0, 75748.9),
    ("04-19 14:15", 75749.0, 75865.0, 75710.1, 75809.1),
    ("04-19 14:20", 75809.1, 75865.0, 75754.7, 75844.3),
    ("04-19 14:25", 75844.3, 75987.0, 75844.2, 75916.8),
    ("04-19 14:30", 75916.8, 75944.9, 75740.8, 75812.6),
    ("04-19 14:35", 75812.6, 75888.0, 75770.4, 75888.0),
    ("04-19 14:40", 75888.0, 75944.9, 75888.0, 75935.3),
    ("04-19 14:45", 75935.3, 76100.0, 75893.7, 76040.0),
    ("04-19 14:50", 76040.0, 76087.2, 75923.0, 75923.1),
    ("04-19 14:55", 75923.1, 75996.2, 75911.0, 75971.3),
    ("04-19 15:00", 75971.4, 75978.7, 75821.6, 75970.8),

    ("04-19 15:05", 75970.8, 75970.9, 75838.6, 75886.7),
    ("04-19 15:10", 75886.7, 75997.0, 75886.7, 75960.0),
    ("04-19 15:15", 75960.0, 76116.8, 75951.8, 76025.9),

    ("04-19 15:20", 76025.9, 76043.1, 75834.9, 75937.1),

    ("04-19 15:25", 75937.1, 75949.5, 75885.1, 75917.3),
    ("04-19 15:30", 75917.4, 75943.6, 75638.7, 75670.9),
    ("04-19 15:35", 75671.0, 75712.2, 75342.3, 75600.1),
    ("04-19 15:40", 75600.0, 75696.1, 75554.3, 75676.3),
    ("04-19 15:45", 75676.3, 75809.1, 75643.5, 75801.5),
    ("04-19 15:50", 75801.4, 75833.3, 75671.4, 75803.1),
    ("04-19 15:55", 75803.1, 75840.0, 75746.8, 75807.6),
    ("04-19 16:00", 75807.7, 75817.7, 75642.2, 75800.1),
    ("04-19 16:05", 75800.1, 75805.9, 75620.2, 75653.6),
    ("04-19 16:10", 75653.5, 75690.5, 75562.9, 75624.8),
    ("04-19 16:15", 75624.8, 75720.5, 75550.8, 75562.9),
    ("04-19 16:20", 75562.9, 75608.9, 75505.0, 75579.1),
    ("04-19 16:25", 75579.0, 75681.2, 75510.2, 75526.2),
    ("04-19 16:30", 75526.1, 75666.0, 75478.2, 75630.4),
    ("04-19 16:35", 75630.4, 75650.9, 75568.5, 75580.1),
    ("04-19 16:40", 75580.0, 75600.2, 75460.0, 75522.0),
    ("04-19 16:45", 75522.1, 75599.5, 75495.1, 75564.9),
    ("04-19 16:50", 75564.9, 75593.2, 75300.1, 75354.4),
    ("04-19 16:55", 75354.4, 75445.9, 75255.7, 75345.6),
    ("04-19 17:00", 75345.5, 75348.4, 75080.0, 75107.7),
    ("04-19 17:05", 75107.6, 75193.9, 74938.9, 75087.9),
    ("04-19 17:10", 75087.9, 75223.7, 75059.8, 75220.6),

    ("04-19 17:15", 75220.6, 75264.0, 75171.5, 75249.3),
    ("04-19 17:20", 75249.4, 75337.4, 75129.2, 75149.9),
    ("04-19 17:25", 75149.9, 75238.0, 75107.1, 75228.6),
    ("04-19 17:30", 75228.6, 75323.5, 75072.8, 75102.2),
    ("04-19 17:35", 75102.2, 75170.0, 75033.3, 75170.0),
    ("04-19 17:40", 75170.0, 75184.2, 75081.8, 75140.0),
    ("04-19 17:45", 75140.0, 75176.5, 74999.0, 74999.1),
    ("04-19 17:50", 74999.1, 75002.1, 74560.0, 74758.6),
    ("04-19 17:55", 74758.6, 74829.2, 74709.9, 74742.4),

    ("04-19 18:00", 74742.3, 74851.3, 74616.6, 74658.5),

    ("04-19 18:05", 74658.5, 74845.2, 74647.5, 74834.8),

    ("04-19 22:40", 74078.4, 74140.0, 74063.7, 74102.1),
    ("04-19 22:45", 74102.1, 74130.2, 73978.7, 74005.8),
    ("04-19 22:50", 74005.8, 74143.1, 74005.8, 74101.6),
    ("04-19 22:55", 74101.5, 74166.0, 74005.0, 74005.0),
    ("04-19 23:00", 74005.0, 74018.6, 73780.0, 73880.8),
    ("04-19 23:05", 73880.9, 73937.3, 73815.0, 73917.1),
    ("04-19 23:10", 73917.2, 73997.8, 73884.0, 73987.9),
    ("04-19 23:15", 73987.9, 73987.9, 73750.0, 73892.0),
    ("04-19 23:20", 73892.0, 73909.4, 73754.8, 73823.7),
    ("04-19 23:25", 73823.7, 73896.7, 73801.8, 73847.9),
    ("04-19 23:30", 73847.9, 73926.5, 73767.7, 73828.4),
    ("04-19 23:35", 73828.3, 73922.8, 73779.3, 73836.0),
    ("04-19 23:40", 73835.9, 73864.9, 73788.0, 73862.2),
    ("04-19 23:45", 73862.3, 73899.7, 73800.0, 73876.1),
    ("04-19 23:50", 73876.0, 73948.7, 73847.9, 73883.6),
    ("04-19 23:55", 73883.5, 73883.6, 73746.4, 73758.4),
    ("04-20 00:00", 73758.4, 74200.0, 73669.0, 74029.1),
    ("04-20 00:05", 74029.1, 74084.3, 73768.5, 74022.8),
    ("04-20 00:10", 74022.8, 74098.3, 73992.0, 73994.7),
    ("04-20 00:15", 73994.7, 74150.0, 73994.6, 74090.1),
    ("04-20 00:20", 74090.1, 74205.6, 74075.1, 74205.5),
    ("04-20 00:25", 74205.5, 74239.9, 74149.4, 74186.4),
    ("04-20 00:30", 74186.5, 74229.9, 74142.0, 74170.0),
    ("04-20 00:35", 74170.0, 74180.0, 74100.0, 74113.6),
    ("04-20 00:40", 74113.6, 74171.7, 74112.9, 74130.6),
    ("04-20 00:45", 74130.6, 74227.8, 74120.2, 74196.4),
    ("04-20 00:50", 74196.3, 74322.9, 74196.3, 74252.3),
    ("04-20 00:55", 74252.2, 74300.0, 74220.5, 74228.1),
    ("04-20 01:00", 74228.1, 74321.0, 74202.6, 74245.4),
    ("04-20 01:05", 74245.4, 74319.2, 74190.0, 74241.2),
    ("04-20 01:10", 74241.2, 74322.0, 74214.8, 74321.8),
    ("04-20 01:15", 74321.8, 74328.0, 74227.0, 74248.6),
    ("04-20 01:20", 74248.5, 74248.5, 74167.6, 74192.2),
    ("04-20 01:25", 74192.2, 74265.5, 74192.2, 74253.2),

    ("04-20 12:05", 75146.9, 75305.7, 75146.9, 75261.6),
    ("04-20 12:10", 75261.6, 75359.0, 75261.6, 75305.1),
    ("04-20 12:15", 75305.1, 75416.7, 75249.5, 75408.4),
    ("04-20 12:20", 75408.5, 75633.0, 75408.4, 75472.5),
    ("04-20 12:25", 75472.6, 75500.0, 75358.1, 75368.9),
    ("04-20 12:30", 75369.0, 75420.1, 75313.7, 75348.5),
    ("04-20 12:35", 75348.5, 75400.0, 75149.2, 75210.6),
    ("04-20 12:40", 75210.6, 75210.6, 74939.1, 75169.5),
    ("04-20 12:45", 75169.5, 75289.6, 75169.5, 75269.2),
    ("04-20 12:50", 75269.1, 75343.6, 75248.7, 75277.0),
    ("04-20 12:55", 75277.0, 75280.4, 75180.9, 75245.0),
    ("04-20 13:00", 75245.1, 75268.0, 75111.7, 75162.0),
    ("04-20 13:05", 75162.1, 75320.8, 75077.0, 75241.6),
    ("04-20 13:10", 75241.5, 75272.9, 75163.7, 75182.3),
    ("04-20 13:15", 75182.3, 75233.4, 75024.0, 75073.0),
    ("04-20 13:20", 75073.0, 75086.6, 74951.6, 74970.8),
    ("04-20 13:25", 74970.8, 75165.2, 74955.3, 75155.0),
    ("04-20 13:30", 75155.0, 75243.3, 74811.7, 75242.6),
    ("04-20 13:35", 75242.6, 75392.0, 75171.2, 75206.6),
    ("04-20 13:40", 75206.6, 75230.0, 75075.9, 75184.4),
    ("04-20 13:45", 75184.4, 75285.0, 74988.0, 75057.3),
    ("04-20 13:50", 75057.2, 75100.0, 74932.2, 75007.7),
    ("04-20 13:55", 75007.6, 75252.3, 74972.3, 75232.8),
    ("04-20 14:00", 75232.7, 75232.7, 75055.0, 75154.5),
    ("04-20 14:05", 75154.8, 75274.3, 75015.7, 75164.2),
    ("04-20 14:10", 75164.2, 75210.0, 74990.0, 75037.0),
    ("04-20 14:15", 75037.0, 75265.0, 74997.0, 75260.5),
    ("04-20 14:20", 75260.6, 75550.0, 75245.2, 75484.8),
    ("04-20 14:25", 75484.7, 75734.0, 75388.1, 75531.4),
    ("04-20 14:30", 75531.5, 75648.4, 75432.4, 75486.3),
    ("04-20 14:35", 75486.3, 75528.1, 75380.3, 75420.4),
    ("04-20 14:40", 75420.4, 75420.4, 75154.1, 75291.0),
    ("04-20 14:45", 75291.0, 75372.1, 75177.0, 75367.7),
    ("04-20 14:50", 75367.7, 75405.0, 74942.0, 74982.9),

    ("04-20 17:20", 75811.7, 75813.6, 75670.0, 75702.8),
    ("04-20 17:25", 75702.8, 75712.9, 75644.9, 75668.6),
    ("04-20 17:30", 75668.6, 75695.8, 75553.0, 75610.6),
    ("04-20 17:35", 75610.7, 75769.8, 75574.6, 75713.6),
    ("04-20 17:40", 75713.7, 75800.0, 75684.4, 75707.4),
    ("04-20 17:45", 75707.5, 75892.6, 75642.5, 75887.6),
    ("04-20 17:50", 75887.6, 75975.4, 75749.0, 75837.9),
    ("04-20 17:55", 75837.9, 75907.0, 75762.3, 75853.7),
    ("04-20 18:00", 75853.7, 76277.6, 75853.7, 76039.4),
    ("04-20 18:05", 76039.3, 76282.5, 76024.2, 76254.9),
    ("04-20 18:10", 76255.0, 76278.0, 76144.1, 76237.3),
    ("04-20 18:15", 76237.4, 76280.0, 76185.7, 76216.5),
    ("04-20 18:20", 76216.4, 76250.0, 76098.9, 76114.7),
    ("04-20 18:25", 76114.7, 76151.1, 76038.5, 76065.4),
    ("04-20 18:30", 76065.5, 76100.0, 75968.3, 76099.9),
    ("04-20 18:35", 76099.9, 76105.0, 75942.4, 76018.5),
    ("04-20 18:40", 76018.5, 76250.0, 76018.4, 76125.6),
    ("04-20 18:45", 76125.7, 76167.1, 76050.0, 76136.8),
    ("04-20 18:50", 76136.8, 76439.0, 76136.7, 76371.4),
    ("04-20 18:55", 76371.3, 76418.6, 76302.7, 76388.8),
    ("04-20 19:00", 76389.3, 76442.8, 76255.0, 76381.5),
    ("04-20 19:05", 76381.4, 76449.8, 76318.9, 76408.7),
    ("04-20 19:10", 76408.7, 76445.8, 76261.2, 76299.5),
    ("04-20 19:15", 76299.6, 76299.6, 76156.8, 76185.2),
    ("04-20 19:20", 76185.1, 76223.0, 76130.4, 76150.7),
    ("04-20 19:25", 76150.7, 76177.3, 76130.0, 76159.0),
    ("04-20 19:30", 76159.0, 76217.2, 76105.6, 76181.9),
    ("04-20 19:35", 76181.9, 76200.0, 76161.1, 76200.0),
    ("04-20 19:40", 76199.9, 76200.0, 76166.9, 76200.0),
    ("04-20 19:45", 76199.9, 76200.0, 76165.6, 76200.0),
    ("04-20 19:50", 76200.0, 76200.0, 76168.8, 76199.0),
    ("04-20 19:55", 76199.1, 76285.7, 76186.9, 76252.5),
    ("04-20 20:00", 76252.5, 76252.5, 76072.9, 76199.9),
    ("04-20 20:05", 76200.0, 76253.0, 76081.2, 76204.6),

    ("04-20 20:10", 76204.6, 76324.4, 76204.6, 76292.4),
    ("04-20 20:15", 76292.3, 76366.5, 76262.6, 76353.3),
    ("04-20 20:20", 76353.3, 76531.0, 76336.9, 76400.0),
    ("04-20 20:25", 76400.0, 76430.2, 76248.3, 76273.6),

    ("04-20 20:30", 76273.7, 76273.7, 76161.8, 76199.9),
    ("04-20 20:35", 76199.9, 76200.0, 76168.7, 76200.0),
    ("04-20 20:40", 76200.0, 76200.0, 76199.9, 76200.0),
    ("04-20 20:45", 76199.9, 76283.6, 76199.9, 76221.0),
    ("04-20 20:50", 76221.0, 76230.0, 76220.9, 76229.9),

    ("04-20 20:55", 76230.0, 76230.0, 76229.9, 76229.9),
    ("04-20 21:00", 76230.0, 76323.9, 76177.0, 76199.9),
    ("04-20 21:05", 76200.0, 76280.0, 76089.8, 76099.7),

    ("04-20 21:10", 76099.7, 76099.7, 75798.4, 75956.9),

    ("04-21 08:50", 76618.8, 76624.6, 76500.0, 76500.0),
    ("04-21 08:55", 76500.1, 76500.1, 76404.0, 76462.4),
    ("04-21 09:00", 76462.4, 76565.2, 76337.6, 76360.1),
    ("04-21 09:05", 76360.1, 76400.0, 76304.7, 76371.0),
    ("04-21 09:10", 76371.0, 76447.2, 76364.2, 76433.7),
    ("04-21 09:15", 76433.6, 76492.0, 76433.6, 76470.9),
    ("04-21 09:20", 76470.9, 76489.4, 76365.7, 76366.6),
    ("04-21 09:25", 76366.5, 76370.0, 76138.9, 76204.1),
    ("04-21 09:30", 76204.1, 76249.2, 76149.9, 76150.0),
    ("04-21 09:35", 76150.0, 76235.0, 76103.3, 76233.3),
    ("04-21 09:40", 76233.3, 76285.3, 76226.1, 76266.9),
    ("04-21 09:45", 76267.0, 76287.0, 76200.0, 76251.5),
    ("04-21 09:50", 76251.5, 76313.4, 76230.0, 76268.1),
    ("04-21 09:55", 76268.1, 76349.9, 76268.1, 76324.2),
    ("04-21 10:00", 76324.2, 76383.8, 76306.3, 76380.4),
    ("04-21 10:05", 76380.4, 76467.6, 76346.1, 76425.0),
    ("04-21 10:10", 76425.0, 76425.1, 76349.5, 76394.6),
    ("04-21 10:15", 76394.5, 76496.6, 76325.0, 76431.7),
    ("04-21 10:20", 76431.7, 76533.0, 76388.7, 76522.9),
    ("04-21 10:25", 76522.9, 76525.2, 76458.3, 76468.9),
    ("04-21 10:30", 76468.9, 76500.0, 76445.0, 76483.6),
    ("04-21 10:35", 76483.6, 76510.0, 76476.4, 76488.5),
    ("04-21 10:40", 76488.4, 76565.0, 76421.4, 76521.7),
    ("04-21 10:45", 76521.6, 76699.1, 76503.7, 76685.7),
    ("04-21 10:50", 76685.8, 76844.5, 76685.7, 76791.6),
    ("04-21 10:55", 76791.7, 76833.1, 76699.1, 76702.1),
    ("04-21 11:00", 76702.2, 76716.7, 76613.3, 76645.6),
    ("04-21 11:05", 76645.5, 76665.0, 76550.0, 76599.9),
    ("04-21 11:10", 76600.0, 76607.0, 76281.1, 76357.5),
    ("04-21 11:15", 76357.5, 76472.0, 76291.9, 76472.0),
    ("04-21 11:20", 76472.0, 76689.2, 76454.0, 76640.0),
    ("04-21 11:25", 76639.9, 76640.0, 76563.2, 76629.0),
    ("04-21 11:30", 76629.0, 76650.0, 76533.3, 76533.3),
    ("04-21 11:35", 76533.3, 76582.7, 76507.9, 76564.4),

    ("04-21 11:40", 76564.4, 76572.0, 76420.0, 76437.8),
    ("04-21 11:45", 76437.8, 76444.7, 76400.1, 76409.1),
    ("04-21 11:50", 76409.2, 76458.3, 76400.0, 76402.9),
    ("04-21 11:55", 76402.8, 76447.2, 76360.2, 76408.3),
    ("04-21 12:00", 76408.3, 76455.4, 76299.7, 76352.4),
    ("04-21 12:05", 76352.5, 76430.9, 76332.4, 76397.2),
    ("04-21 12:10", 76397.2, 76397.2, 76207.5, 76212.8),

    ("04-21 12:15", 76212.9, 76290.7, 76200.0, 76282.2),
    ("04-21 12:20", 76282.2, 76324.0, 76250.4, 76266.1),
    ("04-21 12:25", 76266.0, 76349.2, 76266.0, 76335.2),
    ("04-21 12:30", 76335.1, 76482.6, 76270.3, 76464.8),
    ("04-21 12:35", 76464.8, 76491.1, 76047.3, 76076.9),
    ("04-21 12:40", 76076.9, 76113.4, 75631.2, 75783.4),
    ("04-21 12:45", 75783.4, 75873.3, 75689.5, 75726.3),
    ("04-21 12:50", 75726.4, 75925.3, 75723.0, 75906.3),
    ("04-21 12:55", 75906.4, 76025.0, 75906.3, 75972.8),

    ("04-21 13:00", 75972.9, 76043.6, 75862.0, 75882.0),
    ("04-21 13:05", 75882.1, 76011.7, 75854.4, 75956.2),
    ("04-21 13:10", 75956.3, 75985.5, 75916.8, 75947.6),
    ("04-21 13:15", 75947.7, 76028.3, 75923.6, 75987.6),

    ("04-21 13:20", 75987.5, 76020.0, 75951.0, 76015.3),

    ("04-21 16:20", 75929.8, 75934.0, 75811.0, 75862.3),
    ("04-21 16:25", 75862.3, 75950.0, 75820.6, 75828.8),
    ("04-21 16:30", 75828.8, 76056.1, 75801.3, 76056.1),
    ("04-21 16:35", 76056.0, 76155.0, 75950.8, 75999.4),
    ("04-21 16:40", 75999.4, 76075.1, 75826.6, 75853.8),
    ("04-21 16:45", 75853.9, 76012.6, 75853.7, 76007.4),
    ("04-21 16:50", 76007.5, 76007.5, 75880.0, 75885.3),
    ("04-21 16:55", 75885.3, 75899.9, 75705.4, 75739.2),
    ("04-21 17:00", 75739.3, 75788.2, 75677.0, 75709.9),
    ("04-21 17:05", 75710.0, 75710.0, 75517.2, 75611.4),
    ("04-21 17:10", 75611.4, 75611.4, 75400.0, 75507.2),
    ("04-21 17:15", 75507.1, 75516.2, 75047.5, 75064.5),
    ("04-21 17:20", 75064.5, 75340.6, 75017.8, 75269.4),
    ("04-21 17:25", 75269.4, 75358.9, 75169.3, 75291.2),
    ("04-21 17:30", 75291.3, 75341.0, 75236.9, 75299.7),
    ("04-21 17:35", 75299.6, 75726.3, 75237.4, 75568.0),
    ("04-21 17:40", 75568.0, 75875.1, 75549.3, 75725.3),
    ("04-21 17:45", 75725.1, 75755.2, 75594.2, 75678.4),
    ("04-21 17:50", 75678.3, 75801.1, 75568.0, 75578.1),
    ("04-21 17:55", 75578.1, 75578.2, 75463.3, 75516.0),
    ("04-21 18:00", 75515.9, 75607.7, 75479.9, 75535.2),
    ("04-21 18:05", 75535.2, 75600.5, 75511.9, 75558.5),
    ("04-21 18:10", 75558.4, 75573.1, 75452.6, 75550.5),
    ("04-21 18:15", 75550.5, 75639.6, 75402.5, 75431.6),
    ("04-21 18:20", 75431.5, 75485.1, 75370.0, 75418.4),
    ("04-21 18:25", 75418.4, 75456.0, 75330.6, 75431.2),
    ("04-21 18:30", 75431.3, 75566.5, 75431.2, 75543.6),
    ("04-21 18:35", 75543.6, 75549.0, 75430.1, 75500.0),
    ("04-21 18:40", 75499.9, 75513.0, 75427.2, 75489.5),
    ("04-21 18:45", 75489.5, 75522.2, 75356.3, 75361.6),
    ("04-21 18:50", 75361.6, 75516.2, 75273.0, 75470.1),
    ("04-21 18:55", 75470.1, 75609.2, 75425.8, 75563.1),
    ("04-21 19:00", 75563.1, 75713.3, 75563.1, 75695.9),
    ("04-21 19:05", 75695.9, 75760.0, 75656.8, 75656.8),

    ("04-21 19:10", 75656.9, 75734.0, 75526.6, 75571.0),
    ("04-21 19:15", 75571.0, 75660.2, 75500.0, 75575.9),
    ("04-21 19:20", 75576.0, 75837.0, 75576.0, 75799.2),
    ("04-21 19:25", 75799.2, 75900.0, 75722.9, 75741.0),
    ("04-21 19:30", 75741.0, 75750.0, 75526.2, 75529.7),
    ("04-21 19:35", 75529.6, 75529.7, 75142.0, 75216.4),
    ("04-21 19:40", 75216.4, 75221.4, 74777.9, 74824.7),
    ("04-21 19:45", 74824.8, 75000.0, 74781.0, 74973.3),

    ("04-21 19:50", 74973.3, 75065.0, 74866.6, 74918.7),
    ("04-21 19:55", 74918.8, 75008.1, 74907.9, 74988.6),
    ("04-21 20:00", 74988.7, 75138.0, 74952.9, 75069.3),
    ("04-21 20:05", 75069.5, 75399.1, 74942.2, 75327.9),
    ("04-21 20:10", 75327.4, 75600.0, 75267.5, 75534.4),
    ("04-21 20:15", 75534.3, 75591.7, 75400.1, 75471.3),

    ("04-22 07:50", 77966.8, 78025.5, 77939.9, 77960.0),
    ("04-22 07:55", 77960.0, 78040.0, 77949.9, 77979.8),
    ("04-22 08:00", 77979.7, 78128.8, 77979.7, 78022.7),
    ("04-22 08:05", 78022.7, 78100.0, 78015.5, 78068.6),
    ("04-22 08:10", 78068.6, 78140.5, 78055.3, 78109.3),
    ("04-22 08:15", 78109.3, 78127.6, 78071.2, 78097.5),
    ("04-22 08:20", 78097.6, 78186.0, 77991.6, 77997.8),
    ("04-22 08:25", 77997.8, 78050.2, 77930.0, 77931.7),
    ("04-22 08:30", 77931.7, 77995.1, 77916.8, 77935.7),
    ("04-22 08:35", 77935.8, 77979.0, 77914.9, 77936.8),
    ("04-22 08:40", 77936.9, 77973.4, 77895.4, 77897.2),
    ("04-22 08:45", 77897.1, 77956.2, 77895.3, 77923.9),
    ("04-22 08:50", 77924.0, 78031.5, 77923.9, 78014.9),
    ("04-22 08:55", 78014.9, 78037.9, 77969.9, 77970.0),
    ("04-22 09:00", 77970.0, 78026.0, 77912.1, 77955.2),
    ("04-22 09:05", 77955.3, 78040.3, 77914.4, 78024.1),
    ("04-22 09:10", 78024.0, 78061.0, 77990.3, 78004.8),
    ("04-22 09:15", 78004.8, 78025.3, 77920.9, 77948.6),
    ("04-22 09:20", 77948.6, 78002.4, 77943.1, 78000.0),
    ("04-22 09:25", 78000.0, 78127.4, 77992.5, 78119.2),
    ("04-22 09:30", 78119.3, 78127.7, 78045.7, 78067.7),
    ("04-22 09:35", 78067.7, 78089.8, 78013.6, 78078.6),
    ("04-22 09:40", 78078.5, 78152.8, 78078.5, 78108.9),
    ("04-22 09:45", 78108.9, 78108.9, 78051.1, 78073.8),
    ("04-22 09:50", 78073.7, 78087.1, 77950.1, 77962.4),
    ("04-22 09:55", 77962.4, 77992.9, 77935.1, 77959.9),
    ("04-22 10:00", 77959.9, 78021.3, 77908.6, 77939.2),
    ("04-22 10:05", 77939.1, 78000.0, 77912.3, 77918.3),
    ("04-22 10:10", 77918.4, 78000.0, 77917.2, 77999.9),
    ("04-22 10:15", 78000.0, 78007.7, 77934.3, 77983.7),
    ("04-22 10:20", 77983.6, 77997.5, 77935.2, 77952.0),
    ("04-22 10:25", 77952.0, 78037.7, 77941.3, 78027.4),
    ("04-22 10:30", 78027.4, 78151.0, 78025.3, 78133.7),
    ("04-22 10:35", 78133.8, 78146.4, 78070.8, 78110.4),

    ("04-22 10:40", 78110.3, 78128.1, 78075.0, 78087.1),

    ("04-22 10:45", 78087.1, 78100.0, 78059.1, 78080.5),
    ("04-22 10:50", 78080.4, 78121.1, 78054.2, 78079.1),
    ("04-22 10:55", 78079.1, 78132.8, 78040.0, 78117.8),
    ("04-22 11:00", 78117.8, 78254.4, 78117.7, 78186.0),
    ("04-22 11:05", 78186.1, 78250.0, 78054.5, 78085.6),
    ("04-22 11:10", 78085.6, 78170.4, 78068.8, 78114.2),
    ("04-22 11:15", 78114.3, 78207.8, 78114.2, 78169.7),
    ("04-22 11:20", 78169.8, 78215.6, 78169.8, 78186.1),
    ("04-22 11:25", 78186.1, 78280.0, 78180.7, 78280.0),
    ("04-22 11:30", 78280.0, 78298.9, 78225.1, 78278.9),
    ("04-22 11:35", 78278.9, 78365.8, 78122.9, 78191.2),
    ("04-22 11:40", 78191.3, 78220.2, 78139.5, 78178.1),
    ("04-22 11:45", 78178.1, 78289.2, 78178.0, 78271.7),
    ("04-22 11:50", 78271.7, 78280.0, 78209.1, 78242.1),

    ("04-22 11:55", 78242.2, 78266.1, 78202.6, 78263.2),
    ("04-22 12:00", 78263.2, 78381.1, 78208.4, 78277.1),
    ("04-22 12:05", 78277.1, 78289.9, 78183.6, 78289.8),

    ("04-22 12:10", 78289.9, 78424.1, 78283.6, 78380.1),
    ("04-22 12:15", 78380.0, 78490.8, 78251.7, 78307.4),
    ("04-22 12:20", 78307.4, 78330.7, 78186.0, 78198.9),
    ("04-22 12:25", 78198.9, 78249.2, 78105.8, 78142.7),
    ("04-22 12:30", 78142.8, 78200.0, 78060.0, 78181.4),
    ("04-22 12:35", 78181.4, 78205.7, 78134.3, 78160.0),
    ("04-22 12:40", 78160.1, 78240.6, 78145.4, 78151.1),
    ("04-22 12:45", 78151.0, 78298.3, 78137.7, 78139.4),
    ("04-22 12:50", 78139.4, 78208.0, 78137.2, 78202.0),
    ("04-22 12:55", 78202.1, 78260.8, 78180.7, 78196.6),
    ("04-22 13:00", 78196.6, 78263.4, 78120.1, 78253.8),
    ("04-22 13:05", 78253.7, 78413.3, 78188.6, 78220.9),
    ("04-22 13:10", 78220.9, 78335.2, 78203.2, 78335.2),
    ("04-22 13:15", 78335.2, 78460.2, 78306.3, 78408.5),
    ("04-22 13:20", 78408.5, 78462.2, 78335.4, 78428.0),
    ("04-22 13:25", 78428.0, 78431.2, 78360.0, 78426.8),
    ("04-22 13:30", 78426.9, 78654.0, 78294.7, 78397.6),
    ("04-22 13:35", 78397.5, 78453.9, 78232.9, 78397.7),
    ("04-22 13:40", 78397.6, 78605.0, 78374.0, 78564.8),
    ("04-22 13:45", 78564.9, 78734.0, 78466.2, 78600.0),
    ("04-22 13:50", 78599.9, 78738.0, 78521.1, 78702.3),
    ("04-22 13:55", 78702.4, 78799.0, 78665.0, 78794.5),
    ("04-22 14:00", 78794.4, 78859.8, 78722.0, 78830.4),

    ("04-22 14:05", 78830.4, 78838.3, 78639.3, 78777.0),

    ("04-22 14:10", 78777.1, 79052.9, 78777.1, 79018.1),
    ("04-22 14:15", 79018.0, 79037.3, 78722.0, 78755.4),
    ("04-22 14:20", 78755.4, 79142.8, 78720.4, 79033.2),
    ("04-22 14:25", 79033.1, 79085.1, 78940.0, 78958.3),
    ("04-22 14:30", 78958.4, 78992.9, 78511.1, 78690.3),
    ("04-22 14:35", 78690.4, 78820.6, 78643.9, 78820.6),
    ("04-22 14:40", 78820.6, 78914.0, 78640.0, 78655.1),
    ("04-22 14:45", 78655.1, 78864.4, 78645.9, 78851.9),
    ("04-22 14:50", 78851.9, 78987.0, 78822.3, 78917.5),
    ("04-22 14:55", 78917.6, 79056.0, 78825.9, 78996.8),
    ("04-22 15:00", 78996.7, 79070.1, 78846.1, 78883.1),
    ("04-22 15:05", 78883.1, 78976.9, 78811.2, 78916.7),
    ("04-22 15:10", 78916.6, 79095.5, 78884.3, 78916.5),
    ("04-22 15:15", 78916.5, 78990.7, 78848.4, 78944.4),
    ("04-22 15:20", 78944.3, 79040.1, 78890.0, 78951.6),
    ("04-22 15:25", 78951.6, 79100.0, 78800.3, 79028.4),
    ("04-22 15:30", 79028.4, 79271.7, 78966.0, 79053.6),
    ("04-22 15:35", 79053.7, 79250.0, 78973.9, 79223.9),

    ("04-22 15:40", 79223.9, 79293.1, 79155.4, 79240.8),
    ("04-22 15:45", 79240.9, 79299.9, 79191.1, 79239.3),
    ("04-22 15:50", 79239.3, 79364.5, 79176.1, 79364.2),
    ("04-22 15:55", 79364.2, 79370.0, 79223.0, 79234.3),
    ("04-22 16:00", 79234.3, 79399.9, 79229.9, 79381.6),
    ("04-22 16:05", 79381.6, 79444.0, 79236.3, 79238.1),
    ("04-22 16:10", 79238.0, 79239.9, 79099.4, 79157.2),
    ("04-22 16:15", 79157.1, 79166.6, 79050.0, 79083.4),
    ("04-22 16:20", 79083.5, 79138.4, 78901.0, 78952.0),
    ("04-22 16:25", 78952.0, 78970.7, 78838.8, 78888.3),
    ("04-22 16:30", 78888.2, 78993.6, 78809.6, 78940.3),
    ("04-22 16:35", 78940.3, 78987.3, 78892.0, 78920.1),
    ("04-22 16:40", 78920.0, 78920.1, 78732.2, 78778.3),
    ("04-22 16:45", 78778.3, 78814.0, 78695.5, 78803.1),
    ("04-22 16:50", 78803.2, 78819.9, 78670.0, 78670.0),
    ("04-22 16:55", 78670.1, 78740.3, 78586.7, 78705.1),
    ("04-22 17:00", 78705.1, 78880.0, 78705.0, 78844.7),
    ("04-22 17:05", 78844.7, 78891.0, 78788.6, 78891.0),
    ("04-22 17:10", 78891.0, 78998.6, 78883.5, 78937.8),
    ("04-22 17:15", 78937.8, 78966.1, 78715.7, 78799.3),

    ("04-22 17:20", 78799.3, 78818.4, 78667.8, 78685.7),

    ("04-22 17:25", 78685.7, 78875.0, 78660.0, 78797.7),
    ("04-22 17:30", 78797.8, 78858.0, 78726.7, 78764.0),
    ("04-22 17:35", 78763.9, 78822.5, 78718.0, 78796.0),
    ("04-22 17:40", 78796.0, 78854.3, 78760.7, 78774.6),
    ("04-22 17:45", 78774.6, 78894.0, 78666.0, 78845.4),
    ("04-22 17:50", 78845.8, 78961.2, 78818.3, 78955.4),

    ("04-22 17:55", 78955.4, 78959.0, 78853.8, 78869.8),
    ("04-22 18:00", 78869.8, 78956.5, 78869.7, 78879.0),
    ("04-22 18:05", 78879.0, 78897.1, 78783.7, 78887.8),
    ("04-22 18:10", 78887.7, 78959.0, 78840.0, 78919.1),

    ("04-22 18:15", 78919.2, 78949.0, 78883.7, 78928.9),
    ("04-22 18:20", 78928.9, 78959.9, 78843.1, 78955.2),
    ("04-22 18:25", 78955.2, 78955.2, 78863.0, 78863.1),
    ("04-22 18:30", 78863.1, 78920.0, 78811.1, 78854.4),
    ("04-22 18:35", 78854.2, 78942.9, 78854.0, 78922.2),
    ("04-22 18:40", 78922.2, 78978.5, 78920.5, 78920.5),
    ("04-22 18:45", 78920.5, 79088.8, 78917.1, 79068.1),
    ("04-22 18:50", 79068.1, 79129.8, 79026.3, 79035.2),
    ("04-22 18:55", 79035.2, 79035.2, 78942.0, 78989.5),
    ("04-22 19:00", 78989.5, 79014.5, 78689.3, 78741.8),
    ("04-22 19:05", 78741.7, 78800.0, 78654.6, 78720.0),
    ("04-22 19:10", 78719.9, 78810.0, 78719.2, 78810.0),
    ("04-22 19:15", 78810.0, 78900.0, 78781.3, 78882.1),
    ("04-22 19:20", 78882.1, 78940.0, 78872.0, 78938.6),
    ("04-22 19:25", 78938.6, 79020.0, 78935.0, 78979.9),
    ("04-22 19:30", 78979.9, 79009.4, 78858.6, 78880.9),
    ("04-22 19:35", 78880.8, 78880.8, 78733.5, 78815.1),

    ("04-22 19:40", 78815.2, 78823.1, 78770.3, 78805.4),
    ("04-22 19:45", 78805.4, 78840.0, 78754.9, 78836.8),
    ("04-22 19:50", 78836.8, 78868.0, 78716.4, 78839.9),
    ("04-22 19:55", 78840.0, 78910.0, 78766.9, 78791.3),
    ("04-22 20:00", 78791.3, 78868.9, 78757.1, 78849.3),

    ("04-23 05:10", 77980.5, 77980.6, 77926.8, 77940.0),
    ("04-23 05:15", 77940.1, 77953.3, 77869.8, 77953.3),
    ("04-23 05:20", 77953.4, 77974.3, 77891.0, 77893.6),
    ("04-23 05:25", 77893.6, 77893.6, 77838.4, 77854.9),
    ("04-23 05:30", 77854.9, 77859.6, 77724.4, 77800.0),
    ("04-23 05:35", 77799.9, 77846.7, 77732.3, 77752.4),
    ("04-23 05:40", 77752.4, 77832.3, 77746.2, 77828.7),
    ("04-23 05:45", 77828.7, 77956.4, 77824.0, 77942.3),
    ("04-23 05:50", 77942.4, 78093.2, 77931.6, 77931.9),
    ("04-23 05:55", 77932.0, 78021.4, 77932.0, 77991.9),
    ("04-23 06:00", 77992.0, 78095.0, 77992.0, 78076.0),
    ("04-23 06:05", 78076.1, 78236.0, 78076.0, 78184.2),
    ("04-23 06:10", 78184.3, 78227.5, 78137.0, 78156.4),
    ("04-23 06:15", 78156.5, 78218.5, 78128.5, 78128.6),
    ("04-23 06:20", 78128.6, 78310.1, 78113.4, 78262.7),
    ("04-23 06:25", 78262.6, 78296.6, 78228.0, 78238.1),
    ("04-23 06:30", 78238.1, 78300.0, 78227.9, 78228.4),
    ("04-23 06:35", 78228.4, 78228.5, 78172.5, 78177.0),
    ("04-23 06:40", 78177.0, 78188.2, 78100.1, 78134.0),
    ("04-23 06:45", 78133.8, 78137.6, 78052.5, 78052.7),
    ("04-23 06:50", 78052.8, 78200.7, 78052.7, 78155.2),
    ("04-23 06:55", 78155.2, 78180.0, 78120.6, 78167.0),
    ("04-23 07:00", 78167.0, 78210.0, 78097.1, 78148.3),
    ("04-23 07:05", 78148.2, 78210.9, 78114.3, 78126.8),
    ("04-23 07:10", 78126.8, 78191.3, 78079.0, 78096.7),
    ("04-23 07:15", 78096.7, 78118.7, 78068.8, 78102.4),
    ("04-23 07:20", 78102.3, 78148.7, 78077.3, 78120.1),
    ("04-23 07:25", 78120.1, 78151.1, 78087.2, 78112.9),
    ("04-23 07:30", 78113.0, 78135.9, 78077.4, 78119.1),
    ("04-23 07:35", 78119.2, 78128.6, 77991.6, 78080.6),
    ("04-23 07:40", 78080.6, 78110.4, 78040.0, 78056.9),
    ("04-23 07:45", 78057.0, 78084.6, 77970.0, 78082.2),
    ("04-23 07:50", 78082.1, 78117.4, 77925.9, 77952.7),
    ("04-23 07:55", 77952.7, 78009.1, 77952.7, 78009.1),

    ("04-23 10:00", 77613.0, 77678.3, 77580.0, 77580.0),
    ("04-23 10:05", 77580.0, 77580.1, 76504.6, 77263.2),
    ("04-23 10:10", 77263.3, 77265.0, 77116.7, 77166.2),
    ("04-23 10:15", 77166.3, 77297.6, 77154.5, 77264.5),
    ("04-23 10:20", 77264.6, 77350.0, 77243.3, 77275.3),
    ("04-23 10:25", 77275.3, 77350.7, 77275.2, 77345.5),
    ("04-23 10:30", 77345.5, 77400.0, 77300.0, 77364.5),
    ("04-23 10:35", 77364.5, 77405.0, 77313.1, 77386.5),
    ("04-23 10:40", 77386.5, 77387.9, 77330.2, 77333.2),
    ("04-23 10:45", 77333.2, 77437.9, 77314.5, 77323.3),
    ("04-23 10:50", 77323.4, 77352.0, 77273.3, 77273.3),
    ("04-23 10:55", 77273.4, 77385.1, 77238.4, 77362.9),
    ("04-23 11:00", 77363.0, 77460.0, 77363.0, 77458.2),
    ("04-23 11:05", 77458.2, 77458.2, 77365.0, 77405.3),
    ("04-23 11:10", 77405.2, 77425.4, 77321.6, 77350.0),
    ("04-23 11:15", 77350.0, 77426.8, 77343.6, 77399.4),
    ("04-23 11:20", 77399.4, 77452.2, 77399.3, 77450.4),
    ("04-23 11:25", 77450.4, 77459.0, 77384.5, 77425.3),
    ("04-23 11:30", 77425.4, 77450.0, 77341.8, 77346.4),
    ("04-23 11:35", 77346.3, 77532.0, 77346.3, 77483.3),
    ("04-23 11:40", 77483.4, 77554.9, 77469.6, 77546.1),
    ("04-23 11:45", 77546.1, 77660.9, 77546.0, 77560.1),
    ("04-23 11:50", 77560.0, 77661.3, 77555.0, 77661.3),
    ("04-23 11:55", 77661.2, 77709.1, 77630.7, 77649.9),
    ("04-23 12:00", 77650.0, 77758.3, 77649.9, 77719.1),
    ("04-23 12:05", 77719.1, 77837.6, 77700.4, 77714.9),
    ("04-23 12:10", 77714.9, 77760.0, 77656.8, 77669.7),
    ("04-23 12:15", 77669.6, 77687.6, 77600.0, 77629.1),
    ("04-23 12:20", 77629.0, 77702.3, 77555.5, 77702.2),
    ("04-23 12:25", 77702.3, 77729.8, 77659.4, 77726.0),
    ("04-23 12:30", 77726.0, 77772.2, 77666.6, 77710.0),
    ("04-23 12:35", 77710.0, 77750.0, 77697.6, 77733.0),
    ("04-23 12:40", 77732.9, 77829.0, 77700.0, 77708.5),
    ("04-23 12:45", 77708.5, 77783.5, 77460.4, 77632.1),

    ("04-23 12:50", 77632.1, 77693.6, 77553.5, 77648.5),
    ("04-23 12:55", 77648.4, 77827.0, 77648.4, 77826.8),
    ("04-23 13:00", 77826.8, 77875.7, 77728.6, 77775.2),
    ("04-23 13:05", 77775.2, 77789.5, 77710.2, 77764.9),
    ("04-23 13:10", 77765.0, 77777.7, 77587.7, 77614.6),

    ("04-23 13:15", 77614.9, 77676.8, 77556.3, 77630.5),
    ("04-23 13:20", 77630.5, 77662.7, 77610.1, 77634.2),

    ("04-23 13:25", 77634.3, 77642.4, 77525.0, 77546.8),

    ("04-23 13:30", 77546.8, 77630.4, 77488.4, 77570.7),

    ("04-23 14:15", 77483.0, 77561.2, 77444.0, 77449.6),
    ("04-23 14:20", 77449.6, 77724.2, 77434.3, 77691.1),
    ("04-23 14:25", 77691.0, 77920.0, 77666.3, 77690.5),
    ("04-23 14:30", 77690.4, 77873.6, 77690.4, 77780.0),
    ("04-23 14:35", 77779.9, 77942.0, 77745.7, 77791.5),
    ("04-23 14:40", 77791.5, 77879.7, 77727.4, 77856.6),
    ("04-23 14:45", 77856.7, 77962.9, 77812.2, 77812.2),
    ("04-23 14:50", 77812.2, 78043.3, 77801.4, 78000.0),
    ("04-23 14:55", 78000.0, 78176.0, 77999.9, 78132.8),
    ("04-23 15:00", 78132.8, 78150.0, 77952.3, 77968.4),
    ("04-23 15:05", 77968.5, 78035.1, 77929.0, 77966.1),
    ("04-23 15:10", 77966.1, 78097.8, 77966.1, 78062.1),
    ("04-23 15:15", 78062.1, 78446.9, 78021.5, 78359.3),
    ("04-23 15:20", 78359.2, 78648.0, 78333.3, 78534.8),
    ("04-23 15:25", 78534.9, 78534.9, 78335.5, 78343.4),
    ("04-23 15:30", 78343.3, 78461.3, 78258.7, 78453.5),
    ("04-23 15:35", 78453.4, 78510.0, 78379.0, 78509.7),
    ("04-23 15:40", 78509.6, 78559.8, 78425.3, 78439.7),
    ("04-23 15:45", 78439.7, 78439.7, 78202.9, 78331.6),
    ("04-23 15:50", 78331.6, 78333.0, 78221.9, 78243.4),
    ("04-23 15:55", 78243.5, 78386.5, 78232.5, 78329.2),
    ("04-23 16:00", 78329.3, 78406.4, 78276.0, 78282.7),
    ("04-23 16:05", 78282.7, 78466.8, 78260.9, 78352.3),
    ("04-23 16:10", 78352.3, 78404.0, 78241.4, 78253.4),
    ("04-23 16:15", 78253.5, 78367.3, 78242.3, 78367.3),
    ("04-23 16:20", 78367.3, 78371.6, 78182.0, 78342.2),
    ("04-23 16:25", 78342.1, 78394.3, 78244.1, 78244.2),
    ("04-23 16:30", 78244.1, 78379.4, 78213.6, 78369.1),
    ("04-23 16:35", 78369.0, 78410.7, 78270.3, 78270.4),
    ("04-23 16:40", 78270.3, 78319.8, 78247.2, 78273.6),
    ("04-23 16:45", 78273.6, 78316.2, 78247.2, 78274.9),
    ("04-23 16:50", 78274.9, 78314.0, 78045.0, 78053.7),
    ("04-23 16:55", 78053.8, 78113.3, 77965.8, 78049.0),
    ("04-23 17:00", 78049.1, 78137.8, 77837.5, 77870.2),

    ("04-23 17:05", 77870.3, 77886.3, 77638.8, 77684.0),
    ("04-23 17:10", 77684.1, 77879.2, 77621.6, 77792.5),
    ("04-23 17:15", 77792.5, 77804.8, 77492.9, 77581.1),
    ("04-23 17:20", 77581.0, 77687.1, 77504.7, 77600.2),
    ("04-23 17:25", 77600.2, 77797.9, 77524.7, 77542.7),
    ("04-23 17:30", 77542.8, 77647.8, 77445.7, 77617.6),
    ("04-23 17:35", 77617.7, 77691.7, 77110.0, 77210.6),
    ("04-23 17:40", 77210.6, 77210.6, 76904.0, 77141.0),
    ("04-23 17:45", 77141.0, 77324.1, 76900.1, 77251.5),
    ("04-23 17:50", 77251.5, 77748.2, 77184.5, 77614.8),
    ("04-23 17:55", 77614.7, 77770.9, 77562.7, 77715.2),
    ("04-23 18:00", 77715.1, 77974.2, 77690.5, 77743.8),
    ("04-23 18:05", 77743.7, 78075.1, 77683.7, 77912.1),
    ("04-23 18:10", 77912.1, 78100.0, 77907.1, 77915.9),

    ("04-23 18:15", 77915.8, 78027.9, 77827.2, 77850.1),

    ("04-23 18:20", 77850.0, 77934.2, 77784.0, 77875.1),

    ("04-23 18:25", 77875.0, 77891.0, 77814.1, 77860.0),
    ("04-23 18:30", 77860.0, 78009.6, 77859.9, 77932.2),
    ("04-23 18:35", 77932.2, 78079.0, 77923.1, 78017.9),
    ("04-23 18:40", 78017.8, 78050.0, 77953.3, 77982.5),
    ("04-23 18:45", 77982.5, 78009.6, 77823.6, 77823.7),
    ("04-23 18:50", 77823.6, 77872.4, 77742.3, 77843.0),

    ("04-24 06:00", 77911.1, 77945.0, 77863.5, 77880.4),
    ("04-24 06:05", 77880.4, 77898.6, 77850.0, 77887.4),
    ("04-24 06:10", 77887.3, 77908.1, 77850.0, 77901.6),
    ("04-24 06:15", 77901.5, 77920.0, 77866.1, 77920.0),
    ("04-24 06:20", 77920.0, 77920.0, 77835.2, 77845.6),
    ("04-24 06:25", 77845.6, 77845.6, 77761.6, 77793.2),
    ("04-24 06:30", 77793.2, 77808.7, 77722.0, 77803.1),
    ("04-24 06:35", 77803.1, 77811.1, 77704.0, 77783.9),
    ("04-24 06:40", 77783.8, 77852.6, 77770.3, 77770.7),
    ("04-24 06:45", 77770.8, 77816.4, 77751.0, 77816.4),
    ("04-24 06:50", 77816.4, 77875.9, 77806.5, 77829.8),
    ("04-24 06:55", 77829.8, 77830.0, 77734.3, 77741.9),
    ("04-24 07:00", 77742.0, 77762.5, 77718.6, 77747.5),
    ("04-24 07:05", 77747.5, 77814.0, 77747.4, 77769.2),
    ("04-24 07:10", 77769.2, 77799.3, 77707.3, 77713.7),
    ("04-24 07:15", 77713.7, 77736.7, 77647.7, 77652.5),
    ("04-24 07:20", 77652.5, 77666.0, 77609.9, 77615.7),
    ("04-24 07:25", 77615.8, 77680.8, 77601.0, 77680.7),
    ("04-24 07:30", 77680.7, 77700.1, 77610.0, 77610.1),
    ("04-24 07:35", 77610.0, 77627.3, 77576.2, 77624.9),
    ("04-24 07:40", 77624.9, 77638.0, 77594.6, 77608.5),
    ("04-24 07:45", 77608.4, 77686.9, 77608.4, 77675.1),
    ("04-24 07:50", 77675.1, 77704.1, 77621.2, 77621.3),
    ("04-24 07:55", 77621.2, 77644.7, 77500.0, 77620.5),
    ("04-24 08:00", 77620.5, 77642.0, 77530.1, 77541.3),
    ("04-24 08:05", 77541.3, 77633.4, 77531.0, 77602.8),
    ("04-24 08:10", 77602.7, 77666.1, 77589.6, 77653.1),
    ("04-24 08:15", 77653.1, 77855.8, 77653.1, 77801.3),
    ("04-24 08:20", 77801.2, 77987.2, 77761.9, 77875.2),
    ("04-24 08:25", 77875.2, 77880.0, 77812.8, 77819.9),
    ("04-24 08:30", 77819.9, 77820.6, 77736.7, 77744.2),
    ("04-24 08:35", 77744.2, 77779.6, 77711.9, 77770.1),
    ("04-24 08:40", 77770.0, 77786.0, 77688.4, 77703.8),
    ("04-24 08:45", 77703.8, 77825.0, 77703.8, 77819.4),

    ("04-24 08:50", 77819.4, 77850.1, 77777.3, 77819.9),
    ("04-24 08:55", 77819.9, 77820.0, 77733.2, 77744.6),
    ("04-24 09:00", 77744.6, 77773.9, 77640.2, 77653.7),

    ("04-24 09:05", 77653.7, 77653.8, 77355.8, 77400.0),

    ("04-24 09:10", 77399.9, 77477.8, 77376.3, 77477.8),
    ("04-24 09:15", 77477.9, 77573.4, 77448.3, 77530.3),
    ("04-24 09:20", 77530.4, 77535.5, 77430.0, 77459.8),
    ("04-24 09:25", 77459.9, 77492.9, 77421.3, 77458.0),
    ("04-24 09:30", 77457.9, 77500.9, 77373.4, 77457.1),
    ("04-24 09:35", 77457.2, 77536.3, 77457.1, 77500.1),
    ("04-24 09:40", 77500.1, 77551.0, 77500.0, 77551.0),
    ("04-24 09:45", 77550.9, 77551.0, 77474.4, 77474.5),
    ("04-24 09:50", 77474.5, 77545.0, 77446.1, 77537.4),

    ("04-24 09:55", 77537.4, 77540.2, 77485.0, 77497.2),

    ("04-24 10:00", 77497.2, 77497.3, 77415.3, 77467.5),
    ("04-24 10:05", 77467.4, 77476.2, 77410.0, 77476.1),
    ("04-24 10:10", 77476.1, 77500.0, 77430.7, 77480.3),
    ("04-24 10:15", 77480.4, 77562.8, 77480.3, 77530.7),
    ("04-24 10:20", 77530.8, 77627.1, 77530.7, 77621.9),
    ("04-24 10:25", 77621.8, 77718.0, 77621.8, 77642.5),
    ("04-24 10:30", 77642.4, 77649.9, 77588.5, 77605.2),
    ("04-24 10:35", 77605.3, 77666.6, 77595.9, 77610.0),
    ("04-24 10:40", 77610.0, 77637.1, 77578.2, 77613.9),
    ("04-24 10:45", 77613.9, 77712.0, 77572.5, 77640.2),
    ("04-24 10:50", 77640.3, 77680.0, 77624.4, 77680.0),
    ("04-24 10:55", 77679.9, 77765.5, 77679.9, 77715.2),
    ("04-24 11:00", 77715.2, 77993.2, 77715.1, 77924.8),
    ("04-24 11:05", 77924.7, 78278.7, 77900.0, 78081.1),
    ("04-24 11:10", 78081.1, 78199.5, 78081.1, 78179.4),
    ("04-24 11:15", 78179.4, 78189.6, 78065.4, 78074.9),
    ("04-24 11:20", 78075.0, 78290.0, 78065.0, 78218.8),
    ("04-24 11:25", 78218.8, 78298.8, 78150.0, 78293.0),
    ("04-24 11:30", 78293.1, 78346.1, 78228.0, 78326.4),
    ("04-24 11:35", 78326.4, 78326.4, 78165.8, 78236.3),
    ("04-24 11:40", 78236.4, 78286.8, 78229.0, 78257.2),
    ("04-24 11:45", 78257.2, 78257.3, 78150.2, 78189.9),
    ("04-24 11:50", 78190.0, 78209.7, 78159.7, 78166.7),
    ("04-24 11:55", 78166.8, 78220.0, 78125.5, 78194.8),
    ("04-24 12:00", 78194.9, 78273.3, 78170.6, 78170.6),
    ("04-24 12:05", 78170.6, 78226.1, 78137.5, 78176.3),
    ("04-24 12:10", 78176.4, 78289.6, 78176.3, 78273.0),
    ("04-24 12:15", 78273.0, 78295.0, 78180.0, 78231.3),
    ("04-24 12:20", 78231.3, 78309.2, 78158.2, 78294.7),

    ("04-24 12:25", 78294.8, 78294.8, 78198.7, 78231.4),
    ("04-24 12:30", 78231.5, 78237.7, 78141.0, 78167.0),
    ("04-24 12:35", 78167.0, 78216.9, 78117.5, 78163.8),

    ("04-24 12:40", 78163.7, 78245.2, 78137.7, 78151.2),
    ("04-24 12:45", 78151.1, 78239.2, 78087.0, 78098.6),
    ("04-24 12:50", 78098.5, 78100.0, 77963.6, 77996.1),
    ("04-24 12:55", 77996.0, 78239.8, 77996.0, 78233.0),
    ("04-24 13:00", 78233.0, 78378.0, 78224.9, 78324.6),
    ("04-24 13:05", 78324.5, 78383.0, 78305.1, 78340.7),
    ("04-24 13:10", 78340.7, 78432.9, 78300.0, 78315.7),
    ("04-24 13:15", 78315.8, 78360.0, 78238.2, 78359.9),
    ("04-24 13:20", 78360.0, 78360.1, 78185.2, 78210.7),
    ("04-24 13:25", 78210.7, 78210.7, 78100.0, 78126.8),
    ("04-24 13:30", 78126.7, 78255.2, 78000.0, 78207.9),

    ("04-24 13:35", 78207.8, 78250.0, 78063.9, 78210.1),
    ("04-24 13:40", 78210.0, 78241.8, 78060.0, 78143.6),
    ("04-24 13:45", 78143.5, 78207.7, 78000.0, 78062.9),

    ("04-24 15:50", 77908.2, 78050.0, 77903.7, 77954.4),
    ("04-24 15:55", 77954.5, 78024.5, 77921.0, 78007.3),
    ("04-24 16:00", 78007.3, 78031.9, 77887.0, 77937.0),
    ("04-24 16:05", 77937.0, 78008.1, 77795.1, 77832.7),
    ("04-24 16:10", 77832.7, 77925.9, 77750.0, 77750.1),
    ("04-24 16:15", 77750.0, 77754.9, 77644.9, 77681.8),
    ("04-24 16:20", 77681.8, 77712.0, 77600.0, 77706.7),
    ("04-24 16:25", 77706.6, 77726.1, 77638.3, 77683.4),
    ("04-24 16:30", 77683.3, 77847.4, 77683.3, 77832.8),
    ("04-24 16:35", 77832.7, 77875.3, 77726.0, 77746.1),
    ("04-24 16:40", 77746.0, 77760.0, 77543.4, 77668.1),
    ("04-24 16:45", 77668.0, 77708.5, 77580.7, 77594.4),
    ("04-24 16:50", 77594.4, 77692.3, 77593.7, 77692.3),
    ("04-24 16:55", 77692.3, 77751.6, 77621.9, 77732.7),
    ("04-24 17:00", 77732.6, 77732.7, 77620.7, 77647.2),
    ("04-24 17:05", 77647.3, 77668.7, 77565.0, 77615.6),
    ("04-24 17:10", 77615.5, 77734.1, 77615.5, 77722.6),
    ("04-24 17:15", 77722.6, 77722.7, 77589.9, 77600.0),
    ("04-24 17:20", 77600.0, 77603.2, 77550.0, 77582.8),
    ("04-24 17:25", 77582.7, 77680.1, 77555.8, 77637.9),
    ("04-24 17:30", 77637.9, 77678.0, 77414.4, 77455.7),
    ("04-24 17:35", 77455.7, 77567.9, 77449.7, 77475.9),
    ("04-24 17:40", 77476.0, 77580.0, 77475.0, 77563.7),
    ("04-24 17:45", 77563.6, 77614.2, 77520.0, 77572.3),
    ("04-24 17:50", 77572.2, 77792.9, 77572.2, 77715.3),
    ("04-24 17:55", 77715.2, 77778.7, 77599.9, 77644.6),
    ("04-24 18:00", 77644.5, 77681.6, 77585.0, 77629.2),
    ("04-24 18:05", 77629.2, 77629.2, 77559.6, 77584.8),
    ("04-24 18:10", 77584.7, 77639.0, 77488.0, 77496.8),
    ("04-24 18:15", 77496.8, 77496.8, 77308.0, 77375.9),
    ("04-24 18:20", 77375.9, 77477.6, 77367.1, 77466.8),
    ("04-24 18:25", 77466.7, 77512.5, 77444.1, 77461.7),
    ("04-24 18:30", 77461.6, 77575.2, 77444.1, 77541.1),
    ("04-24 18:35", 77541.1, 77601.3, 77510.0, 77510.1),

    ("04-24 18:40", 77510.1, 77555.9, 77479.7, 77544.5),
    ("04-24 18:45", 77544.4, 77584.9, 77517.0, 77521.6),
    ("04-24 18:50", 77521.5, 77564.2, 77508.2, 77549.0),
    ("04-24 18:55", 77548.9, 77598.2, 77526.3, 77579.2),
    ("04-24 19:00", 77579.2, 77711.0, 77579.2, 77608.0),
    ("04-24 19:05", 77608.0, 77632.8, 77532.8, 77563.6),
    ("04-24 19:10", 77563.6, 77575.6, 77535.8, 77566.9),
    ("04-24 19:15", 77567.0, 77636.0, 77566.9, 77596.7),
    ("04-24 19:20", 77596.8, 77619.3, 77520.9, 77520.9),
    ("04-24 19:25", 77521.0, 77547.4, 77485.1, 77533.4),
    ("04-24 19:30", 77533.4, 77608.3, 77515.4, 77577.2),
    ("04-24 19:35", 77577.1, 77606.0, 77522.7, 77588.1),
    ("04-24 19:40", 77588.2, 77615.8, 77573.3, 77579.2),
    ("04-24 19:45", 77579.1, 77588.8, 77539.1, 77542.4),
    ("04-24 19:50", 77542.4, 77578.1, 77503.6, 77573.8),
    ("04-24 19:55", 77573.8, 77609.9, 77547.7, 77596.1),
    ("04-24 20:00", 77596.0, 77612.4, 77490.0, 77538.6),
    ("04-24 20:05", 77538.6, 77563.9, 77511.4, 77532.3),

    ("04-24 20:10", 77532.3, 77608.0, 77525.9, 77600.0),

    ("04-24 20:15", 77600.0, 77619.8, 77509.0, 77529.5),
    ("04-24 20:20", 77529.5, 77566.6, 77470.1, 77475.0),
    ("04-24 20:25", 77474.9, 77521.6, 77412.8, 77492.8),

    ("04-24 20:30", 77492.8, 77543.4, 77492.7, 77526.2),
    ("04-24 20:35", 77526.3, 77630.7, 77526.2, 77617.5),
    ("04-24 20:40", 77617.5, 77623.1, 77581.1, 77590.1),
    ("04-24 20:45", 77590.1, 77634.7, 77590.0, 77613.5),
    ("04-24 20:50", 77613.6, 77633.3, 77600.0, 77625.1),

    ("04-24 20:55", 77625.1, 77727.0, 77625.1, 77688.2),

    ("04-24 21:00", 77688.2, 77698.0, 77655.1, 77697.9),
    ("04-24 21:05", 77698.0, 77718.5, 77660.0, 77667.0),
    ("04-24 21:10", 77667.0, 77696.0, 77546.7, 77546.8),

    ("04-24 21:15", 77546.8, 77596.0, 77530.7, 77595.7),
    ("04-24 21:20", 77595.7, 77595.8, 77539.9, 77595.6),
    ("04-24 21:25", 77595.5, 77618.5, 77561.6, 77582.9),
    ("04-24 21:30", 77582.8, 77593.0, 77528.2, 77569.5),
    ("04-24 21:35", 77569.5, 77577.9, 77507.1, 77550.0),
    ("04-24 21:40", 77550.1, 77595.2, 77516.1, 77520.1),
    ("04-24 21:45", 77520.0, 77550.0, 77506.3, 77538.3),
    ("04-24 21:50", 77538.3, 77547.5, 77511.0, 77532.2),
    ("04-24 21:55", 77532.2, 77554.0, 77490.0, 77490.1),
    ("04-24 22:00", 77490.0, 77558.8, 77465.0, 77517.1),
    ("04-24 22:05", 77517.1, 77555.9, 77500.5, 77500.6),
    ("04-24 22:10", 77500.5, 77566.0, 77500.0, 77562.9),
    ("04-24 22:15", 77562.9, 77562.9, 77536.6, 77562.1),
    ("04-24 22:20", 77562.1, 77579.9, 77533.0, 77542.0),
    ("04-24 22:25", 77542.1, 77542.1, 77500.0, 77500.0),
    ("04-24 22:30", 77500.1, 77500.1, 77415.9, 77419.0),
    ("04-24 22:35", 77419.0, 77449.4, 77206.8, 77261.8),
    ("04-24 22:40", 77261.7, 77316.1, 77230.5, 77241.8),
    ("04-24 22:45", 77241.9, 77340.0, 77241.9, 77288.1),
    ("04-24 22:50", 77288.1, 77343.5, 77278.8, 77280.0),
    ("04-24 22:55", 77280.0, 77317.0, 77280.0, 77294.5),

    ("04-25 00:15", 77378.0, 77397.3, 77306.3, 77324.9),
    ("04-25 00:20", 77324.9, 77347.2, 77315.7, 77315.7),
    ("04-25 00:25", 77315.8, 77327.3, 77254.7, 77271.9),
    ("04-25 00:30", 77271.8, 77320.0, 77266.5, 77309.2),
    ("04-25 00:35", 77309.2, 77354.6, 77304.8, 77354.5),
    ("04-25 00:40", 77354.5, 77382.5, 77329.9, 77336.9),
    ("04-25 00:45", 77336.9, 77382.4, 77336.8, 77371.0),
    ("04-25 00:50", 77371.0, 77376.1, 77364.8, 77375.6),
    ("04-25 00:55", 77375.5, 77420.0, 77375.5, 77419.9),
    ("04-25 01:00", 77420.0, 77450.0, 77398.7, 77411.1),
    ("04-25 01:05", 77411.1, 77412.1, 77392.7, 77408.3),
    ("04-25 01:10", 77408.2, 77487.3, 77408.2, 77471.6),
    ("04-25 01:15", 77471.7, 77502.0, 77462.9, 77479.0),
    ("04-25 01:20", 77478.9, 77479.0, 77425.1, 77448.0),
    ("04-25 01:25", 77448.0, 77457.4, 77419.9, 77441.9),
    ("04-25 01:30", 77441.9, 77500.0, 77441.8, 77500.0),
    ("04-25 01:35", 77499.9, 77511.0, 77483.1, 77499.9),
    ("04-25 01:40", 77499.9, 77515.6, 77490.6, 77515.6),
    ("04-25 01:45", 77515.6, 77579.3, 77515.6, 77545.1),
    ("04-25 01:50", 77545.0, 77547.2, 77499.9, 77510.0),
    ("04-25 01:55", 77510.0, 77510.0, 77490.0, 77490.0),
    ("04-25 02:00", 77490.0, 77516.4, 77450.0, 77459.8),
    ("04-25 02:05", 77459.7, 77539.3, 77459.7, 77508.9),
    ("04-25 02:10", 77509.0, 77588.0, 77502.3, 77502.4),
    ("04-25 02:15", 77502.4, 77531.4, 77485.5, 77524.1),
    ("04-25 02:20", 77524.0, 77545.1, 77507.6, 77545.1),
    ("04-25 02:25", 77545.1, 77606.7, 77545.0, 77589.7),
    ("04-25 02:30", 77589.8, 77608.2, 77573.6, 77583.9),
    ("04-25 02:35", 77583.9, 77584.9, 77568.4, 77583.8),
    ("04-25 02:40", 77583.9, 77583.9, 77571.2, 77578.9),
    ("04-25 02:45", 77578.9, 77578.9, 77565.5, 77576.6),
    ("04-25 02:50", 77576.6, 77587.9, 77576.5, 77580.1),
    ("04-25 02:55", 77580.1, 77592.1, 77549.2, 77567.6),
    ("04-25 03:00", 77567.6, 77600.0, 77551.3, 77599.9),

    ("04-25 14:05", 77600.0, 77635.2, 77589.8, 77615.2),
    ("04-25 14:10", 77615.3, 77655.5, 77600.0, 77655.5),
    ("04-25 14:15", 77655.5, 77665.2, 77620.8, 77625.7),
    ("04-25 14:20", 77625.7, 77652.3, 77621.7, 77628.9),
    ("04-25 14:25", 77628.9, 77704.7, 77628.8, 77686.6),
    ("04-25 14:30", 77686.7, 77704.7, 77677.0, 77677.0),
    ("04-25 14:35", 77677.0, 77700.0, 77666.6, 77700.0),
    ("04-25 14:40", 77699.9, 77707.5, 77683.9, 77689.1),
    ("04-25 14:45", 77689.0, 77713.4, 77686.6, 77694.0),
    ("04-25 14:50", 77693.8, 77693.8, 77616.8, 77641.3),
    ("04-25 14:55", 77641.4, 77641.4, 77603.8, 77618.2),
    ("04-25 15:00", 77618.3, 77628.6, 77600.8, 77622.0),
    ("04-25 15:05", 77622.0, 77639.9, 77613.5, 77620.9),
    ("04-25 15:10", 77620.9, 77632.1, 77610.7, 77631.1),
    ("04-25 15:15", 77631.1, 77644.4, 77631.0, 77636.2),
    ("04-25 15:20", 77636.3, 77666.6, 77636.2, 77666.5),
    ("04-25 15:25", 77666.6, 77686.8, 77658.3, 77665.8),
    ("04-25 15:30", 77665.9, 77670.0, 77644.0, 77669.9),
    ("04-25 15:35", 77669.9, 77691.1, 77653.9, 77653.9),
    ("04-25 15:40", 77653.9, 77658.8, 77621.3, 77621.3),
    ("04-25 15:45", 77621.3, 77621.4, 77455.2, 77458.1),
    ("04-25 15:50", 77458.0, 77487.0, 77263.0, 77283.9),
    ("04-25 15:55", 77283.9, 77364.4, 77265.6, 77289.3),
    ("04-25 16:00", 77289.3, 77381.4, 77251.2, 77365.1),
    ("04-25 16:05", 77365.0, 77407.5, 77314.2, 77369.7),
    ("04-25 16:10", 77369.6, 77411.8, 77322.9, 77407.6),
    ("04-25 16:15", 77407.5, 77411.5, 77376.3, 77376.3),
    ("04-25 16:20", 77376.3, 77392.5, 77368.2, 77377.5),
    ("04-25 16:25", 77377.5, 77385.4, 77282.0, 77355.3),
    ("04-25 16:30", 77355.3, 77380.0, 77274.3, 77335.0),
    ("04-25 16:35", 77334.9, 77385.0, 77100.0, 77230.1),
    ("04-25 16:40", 77230.0, 77348.2, 77220.9, 77327.0),
    ("04-25 16:45", 77327.0, 77371.8, 77300.2, 77352.5),
    ("04-25 16:50", 77352.6, 77371.0, 77340.9, 77350.1),

    ("04-25 16:55", 77350.1, 77375.0, 77333.0, 77364.0),

    ("04-25 17:00", 77364.0, 77378.1, 77321.2, 77343.7),
    ("04-25 17:05", 77343.8, 77343.8, 77319.9, 77329.6),
    ("04-25 17:10", 77329.6, 77329.6, 77305.0, 77312.0),
    ("04-25 17:15", 77312.0, 77312.0, 77256.1, 77284.8),
    ("04-25 17:20", 77284.8, 77379.7, 77278.7, 77335.2),
    ("04-25 17:25", 77335.2, 77367.8, 77270.3, 77284.1),
    ("04-25 17:30", 77284.1, 77295.5, 77211.8, 77241.3),
    ("04-25 17:35", 77241.3, 77297.7, 77241.2, 77294.0),
    ("04-25 17:40", 77294.0, 77301.7, 77267.6, 77267.6),
    ("04-25 17:45", 77267.7, 77270.3, 77215.8, 77215.8),
    ("04-25 17:50", 77215.9, 77218.6, 77192.3, 77192.3),
    ("04-25 17:55", 77192.3, 77225.1, 77162.0, 77213.4),
    ("04-25 18:00", 77213.3, 77293.9, 77174.2, 77258.2),
    ("04-25 18:05", 77258.1, 77258.6, 77224.0, 77249.0),
    ("04-25 18:10", 77249.0, 77266.0, 77237.1, 77245.1),
    ("04-25 18:15", 77245.1, 77256.4, 77244.5, 77244.6),
    ("04-25 18:20", 77244.5, 77260.9, 77220.1, 77250.2),
    ("04-25 18:25", 77250.1, 77287.9, 77250.1, 77285.2),
    ("04-25 18:30", 77285.1, 77353.6, 77285.1, 77323.1),

    ("04-25 18:35", 77323.2, 77353.3, 77306.6, 77310.0),
    ("04-25 18:40", 77310.1, 77322.4, 77270.7, 77270.7),
    ("04-25 18:45", 77270.8, 77327.2, 77269.9, 77269.9),

    ("04-25 18:50", 77269.9, 77292.7, 77256.3, 77256.4),
    ("04-25 18:55", 77256.4, 77290.1, 77246.9, 77256.8),
    ("04-25 19:00", 77256.8, 77276.8, 77245.5, 77264.7),
    ("04-25 19:05", 77264.8, 77275.5, 77235.0, 77262.2),
    ("04-25 19:10", 77261.6, 77300.5, 77252.5, 77290.1),
    ("04-25 19:15", 77290.1, 77303.9, 77276.2, 77303.9),
    ("04-25 19:20", 77303.9, 77312.6, 77278.5, 77311.8),
    ("04-25 19:25", 77311.8, 77311.8, 77208.0, 77218.4),
    ("04-25 19:30", 77218.3, 77225.1, 77185.0, 77200.0),
    ("04-25 19:35", 77200.0, 77220.0, 77185.0, 77185.0),
    ("04-25 19:40", 77185.0, 77205.0, 77153.1, 77153.2),

    ("04-25 19:45", 77153.1, 77205.0, 77153.0, 77200.8),
    ("04-25 19:50", 77200.8, 77254.5, 77200.8, 77248.8),
    ("04-25 19:55", 77248.8, 77301.6, 77248.8, 77285.6),
    ("04-25 20:00", 77285.7, 77323.5, 77269.8, 77275.8),
    ("04-25 20:05", 77275.8, 77310.6, 77267.3, 77310.5),
    ("04-25 20:10", 77310.5, 77360.7, 77310.5, 77316.0),
    ("04-25 20:15", 77316.0, 77352.6, 77306.9, 77341.6),
    ("04-25 20:20", 77341.5, 77402.0, 77341.5, 77381.6),
    ("04-25 20:25", 77381.7, 77389.5, 77349.3, 77389.4),
    ("04-25 20:30", 77389.4, 77391.5, 77360.0, 77369.2),
    ("04-25 20:35", 77369.2, 77385.3, 77359.9, 77369.3),
    ("04-25 20:40", 77369.4, 77378.4, 77360.5, 77360.5),
    ("04-25 20:45", 77360.6, 77376.7, 77360.5, 77373.1),
    ("04-25 20:50", 77373.1, 77396.7, 77363.2, 77396.6),
    ("04-25 20:55", 77396.5, 77450.0, 77396.5, 77439.1),

    ("04-25 21:00", 77439.0, 77499.0, 77426.2, 77470.4),

    ("04-26 05:35", 78041.6, 78050.0, 77976.6, 78024.9),
    ("04-26 05:40", 78024.9, 78036.4, 77995.7, 78012.1),
    ("04-26 05:45", 78012.1, 78023.0, 77953.8, 78008.3),
    ("04-26 05:50", 78008.4, 78011.6, 77963.5, 77970.0),
    ("04-26 05:55", 77970.1, 77979.3, 77939.0, 77949.4),
    ("04-26 06:00", 77949.4, 78008.0, 77949.4, 78007.9),
    ("04-26 06:05", 78007.8, 78007.9, 77957.3, 77957.4),
    ("04-26 06:10", 77957.4, 78000.0, 77957.3, 77980.0),
    ("04-26 06:15", 77980.1, 77984.1, 77888.0, 77899.9),
    ("04-26 06:20", 77899.9, 77922.1, 77886.1, 77890.3),
    ("04-26 06:25", 77890.3, 77950.0, 77886.0, 77911.5),
    ("04-26 06:30", 77911.5, 77923.4, 77894.3, 77901.8),
    ("04-26 06:35", 77901.8, 77948.2, 77885.0, 77948.1),
    ("04-26 06:40", 77948.2, 78012.2, 77948.2, 77975.0),
    ("04-26 06:45", 77974.9, 77975.0, 77889.5, 77889.5),
    ("04-26 06:50", 77889.4, 77953.4, 77851.2, 77934.3),
    ("04-26 06:55", 77934.4, 77970.1, 77920.0, 77963.2),
    ("04-26 07:00", 77963.3, 77987.9, 77952.9, 77953.4),
    ("04-26 07:05", 77953.5, 77977.1, 77948.0, 77948.0),
    ("04-26 07:10", 77948.0, 77971.7, 77947.8, 77967.4),
    ("04-26 07:15", 77967.4, 77990.0, 77947.2, 77962.4),
    ("04-26 07:20", 77962.4, 78000.0, 77962.4, 77979.1),
    ("04-26 07:25", 77979.2, 77979.2, 77948.2, 77957.0),
    ("04-26 07:30", 77957.0, 77960.5, 77920.5, 77935.8),
    ("04-26 07:35", 77935.9, 77945.1, 77920.6, 77929.6),
    ("04-26 07:40", 77929.5, 77944.7, 77928.7, 77935.2),
    ("04-26 07:45", 77935.2, 77950.0, 77935.1, 77950.0),
    ("04-26 07:50", 77950.0, 78034.7, 77949.8, 78014.7),
    ("04-26 07:55", 78014.7, 78085.0, 78012.5, 78061.5),
    ("04-26 08:00", 78061.5, 78085.0, 78045.0, 78075.4),
    ("04-26 08:05", 78075.3, 78095.3, 78026.3, 78039.2),
    ("04-26 08:10", 78039.2, 78039.3, 78001.6, 78031.4),
    ("04-26 08:15", 78031.4, 78039.3, 78000.0, 78000.0),
    ("04-26 08:20", 78000.0, 78005.0, 77973.5, 78004.4),

    ("04-26 09:00", 77989.1, 77989.1, 77933.7, 77953.4),
    ("04-26 09:05", 77953.3, 77982.3, 77926.4, 77939.8),
    ("04-26 09:10", 77939.8, 77973.9, 77939.2, 77973.8),
    ("04-26 09:15", 77973.8, 77979.4, 77950.0, 77950.0),
    ("04-26 09:20", 77950.1, 77985.0, 77950.0, 77985.0),
    ("04-26 09:25", 77985.0, 78020.0, 77965.5, 77972.0),
    ("04-26 09:30", 77971.9, 77972.0, 77917.4, 77926.0),
    ("04-26 09:35", 77925.9, 77935.0, 77900.0, 77910.8),
    ("04-26 09:40", 77910.8, 77944.0, 77880.0, 77932.2),
    ("04-26 09:45", 77932.3, 77932.3, 77904.3, 77925.6),
    ("04-26 09:50", 77925.6, 77966.0, 77925.5, 77952.9),
    ("04-26 09:55", 77952.9, 77971.8, 77952.8, 77971.8),
    ("04-26 10:00", 77971.8, 77971.8, 77914.5, 77931.9),
    ("04-26 10:05", 77931.8, 78017.7, 77931.8, 77992.5),
    ("04-26 10:10", 77992.5, 78012.7, 77986.3, 77993.6),
    ("04-26 10:15", 77993.6, 78005.3, 77972.2, 77990.8),
    ("04-26 10:20", 77990.8, 78000.0, 77979.2, 77979.3),
    ("04-26 10:25", 77979.2, 77991.0, 77964.3, 77972.7),
    ("04-26 10:30", 77972.7, 77972.8, 77952.0, 77969.5),
    ("04-26 10:35", 77969.6, 77973.0, 77957.0, 77957.1),
    ("04-26 10:40", 77957.1, 77973.1, 77932.5, 77945.7),
    ("04-26 10:45", 77945.7, 77967.3, 77935.1, 77936.4),
    ("04-26 10:50", 77936.3, 77950.0, 77923.4, 77941.5),
    ("04-26 10:55", 77941.5, 77963.9, 77941.5, 77961.4),
    ("04-26 11:00", 77961.5, 78028.4, 77961.4, 77990.1),
    ("04-26 11:05", 77990.1, 78027.7, 77990.0, 78016.1),
    ("04-26 11:10", 78016.1, 78050.0, 78006.0, 78006.0),
    ("04-26 11:15", 78006.1, 78012.5, 77985.8, 78005.3),
    ("04-26 11:20", 78005.4, 78074.4, 78001.6, 78069.0),
    ("04-26 11:25", 78069.0, 78114.5, 78063.9, 78092.1),
    ("04-26 11:30", 78092.1, 78104.0, 78022.5, 78056.9),
    ("04-26 11:35", 78056.9, 78056.9, 78024.1, 78032.0),
    ("04-26 11:40", 78032.0, 78046.8, 78031.9, 78031.9),
    ("04-26 11:45", 78032.0, 78050.0, 78005.7, 78049.9),

    ("04-26 11:50", 78050.0, 78085.8, 78049.9, 78063.1),

    ("04-26 11:55", 78063.1, 78089.0, 78050.0, 78050.0),
    ("04-26 12:00", 78050.0, 78063.5, 78016.0, 78016.0),
    ("04-26 12:05", 78016.0, 78030.0, 78005.0, 78005.0),
    ("04-26 12:10", 78005.1, 78005.1, 77932.4, 77933.8),
    ("04-26 12:15", 77933.8, 77947.3, 77920.0, 77942.7),
    ("04-26 12:20", 77942.7, 77980.1, 77941.6, 77956.0),
    ("04-26 12:25", 77956.0, 77972.8, 77918.0, 77935.3),
    ("04-26 12:30", 77935.3, 77938.0, 77925.1, 77930.6),
    ("04-26 12:35", 77930.5, 77947.5, 77930.5, 77947.5),
    ("04-26 12:40", 77947.5, 77947.5, 77900.0, 77900.0),
    ("04-26 12:45", 77900.0, 77900.0, 77715.0, 77798.8),
    ("04-26 12:50", 77798.9, 77840.9, 77783.1, 77800.1),
    ("04-26 12:55", 77800.2, 77816.8, 77763.3, 77795.5),
    ("04-26 13:00", 77795.4, 77812.2, 77742.6, 77803.0),
    ("04-26 13:05", 77803.0, 77863.2, 77767.2, 77854.9),
    ("04-26 13:10", 77854.9, 77893.8, 77839.3, 77859.9),

    ("04-26 13:15", 77860.0, 77899.7, 77819.1, 77849.7),
    ("04-26 13:20", 77849.7, 77855.7, 77806.5, 77806.5),
    ("04-26 13:25", 77806.5, 77834.7, 77769.7, 77834.7),
    ("04-26 13:30", 77834.7, 77945.4, 77825.1, 77921.6),
    ("04-26 13:35", 77921.6, 77944.5, 77880.0, 77944.4),
    ("04-26 13:40", 77944.5, 77953.2, 77902.3, 77950.0),

    ("04-26 13:45", 77950.1, 77953.1, 77887.9, 77901.9),

    ("04-26 14:40", 78033.4, 78087.6, 78000.9, 78016.0),
    ("04-26 14:45", 78016.1, 78016.1, 77950.0, 77981.7),
    ("04-26 14:50", 77981.7, 78115.3, 77981.6, 78100.0),
    ("04-26 14:55", 78100.1, 78120.0, 78050.0, 78053.4),
    ("04-26 15:00", 78053.5, 78091.3, 78050.0, 78062.8),
    ("04-26 15:05", 78062.9, 78079.5, 77989.0, 78045.7),
    ("04-26 15:10", 78045.7, 78063.8, 78038.9, 78053.1),
    ("04-26 15:15", 78053.2, 78088.8, 78053.1, 78067.7),
    ("04-26 15:20", 78067.7, 78075.4, 77912.5, 77957.4),
    ("04-26 15:25", 77957.4, 78058.0, 77957.3, 78058.0),
    ("04-26 15:30", 78057.9, 78073.6, 77981.8, 77993.1),
    ("04-26 15:35", 77993.2, 78030.4, 77993.1, 78030.3),
    ("04-26 15:40", 78030.4, 78030.4, 78000.0, 78005.9),
    ("04-26 15:45", 78005.8, 78006.0, 77952.2, 77973.3),
    ("04-26 15:50", 77973.4, 78014.8, 77973.4, 78009.9),
    ("04-26 15:55", 78009.9, 78010.0, 77983.4, 78007.9),
    ("04-26 16:00", 78007.9, 78028.7, 77965.0, 78012.8),
    ("04-26 16:05", 78012.8, 78026.7, 77968.5, 78007.0),
    ("04-26 16:10", 78006.9, 78012.2, 77973.7, 77973.7),
    ("04-26 16:15", 77973.7, 78000.8, 77973.7, 78000.8),
    ("04-26 16:20", 78000.7, 78007.7, 77988.0, 78007.6),
    ("04-26 16:25", 78007.7, 78013.6, 77990.0, 78011.1),
    ("04-26 16:30", 78011.0, 78055.7, 78000.0, 78044.0),
    ("04-26 16:35", 78044.0, 78051.0, 78000.0, 78012.1),
    ("04-26 16:40", 78012.1, 78012.1, 77960.5, 77960.6),
    ("04-26 16:45", 77960.5, 77995.7, 77902.0, 77992.0),
    ("04-26 16:50", 77992.0, 78000.0, 77984.2, 77991.8),
    ("04-26 16:55", 77991.9, 77991.9, 77890.0, 77890.0),
    ("04-26 17:00", 77890.1, 77932.0, 77815.0, 77932.0),
    ("04-26 17:05", 77932.0, 77977.2, 77920.5, 77966.9),
    ("04-26 17:10", 77966.8, 77986.3, 77957.0, 77976.0),
    ("04-26 17:15", 77976.0, 77990.8, 77973.4, 77975.8),
    ("04-26 17:20", 77975.8, 77990.7, 77938.0, 77972.6),
    ("04-26 17:25", 77972.6, 78009.4, 77972.4, 77975.4),

    ("04-26 17:30", 77975.5, 77975.5, 77896.8, 77942.3),

    ("04-26 17:35", 77942.4, 77965.8, 77930.3, 77938.3),
    ("04-26 17:40", 77938.2, 77991.7, 77938.2, 77979.0),
    ("04-26 17:45", 77979.0, 78026.9, 77962.2, 77984.1),
    ("04-26 17:50", 77984.0, 78012.7, 77983.8, 77983.8),
    ("04-26 17:55", 77983.9, 77995.6, 77969.2, 77976.7),
    ("04-26 18:00", 77976.7, 77997.9, 77961.2, 77961.3),
    ("04-26 18:05", 77961.2, 78050.0, 77945.7, 78041.5),

    ("04-26 18:10", 78041.5, 78125.1, 77978.6, 78063.2),
    ("04-26 18:15", 78063.1, 78326.2, 78040.0, 78161.5),
    ("04-26 18:20", 78161.5, 78205.7, 78146.0, 78180.0),
    ("04-26 18:25", 78180.1, 78180.1, 78120.2, 78138.6),
    ("04-26 18:30", 78138.7, 78171.6, 78096.8, 78096.8),
    ("04-26 18:35", 78096.9, 78150.0, 78096.7, 78117.9),
    ("04-26 18:40", 78118.0, 78195.1, 78111.7, 78170.2),
    ("04-26 18:45", 78170.3, 78232.6, 78142.1, 78209.8),
    ("04-26 18:50", 78209.9, 78229.6, 78199.9, 78225.3),
    ("04-26 18:55", 78225.3, 78260.0, 78190.7, 78238.1),
    ("04-26 19:00", 78238.1, 78270.0, 78130.1, 78170.0),
    ("04-26 19:05", 78170.1, 78273.4, 78155.8, 78260.8),
    ("04-26 19:10", 78260.8, 78400.0, 78258.0, 78359.9),
    ("04-26 19:15", 78359.9, 78477.9, 78301.2, 78361.0),
    ("04-26 19:20", 78361.0, 78374.0, 78175.0, 78175.0),
    ("04-26 19:25", 78175.1, 78210.0, 77967.9, 78159.0),
    ("04-26 19:30", 78158.9, 78187.2, 78050.0, 78109.9),
    ("04-26 19:35", 78109.9, 78168.1, 78004.8, 78053.8),
    ("04-26 19:40", 78053.9, 78161.4, 78053.9, 78141.1),
    ("04-26 19:45", 78141.1, 78190.0, 78134.1, 78190.0),
    ("04-26 19:50", 78190.0, 78235.7, 78189.9, 78228.0),

    ("04-26 19:55", 78228.1, 78250.0, 78175.4, 78183.1),
    ("04-26 20:00", 78183.2, 78208.4, 78154.8, 78205.8),
    ("04-26 20:05", 78205.7, 78225.7, 78192.4, 78213.9),
    ("04-26 20:10", 78213.8, 78213.8, 78142.6, 78142.6),
    ("04-26 20:15", 78142.6, 78166.4, 78120.8, 78128.3),
    ("04-26 20:20", 78128.2, 78170.0, 78107.0, 78169.9),
    ("04-26 20:25", 78170.0, 78200.1, 78169.9, 78185.1),
    ("04-26 20:30", 78185.0, 78355.1, 78185.0, 78309.0),
    ("04-26 20:35", 78309.1, 78348.1, 78219.1, 78219.1),
    ("04-26 20:40", 78219.2, 78263.5, 78207.1, 78245.4),
    ("04-26 20:45", 78245.4, 78312.5, 78224.6, 78239.1),
    ("04-26 20:50", 78239.1, 78250.5, 78205.6, 78205.7),
    ("04-26 20:55", 78205.7, 78205.7, 78135.0, 78150.1),
    ("04-26 21:00", 78150.0, 78229.7, 78139.4, 78229.7),
    ("04-26 21:05", 78229.7, 78243.9, 78213.1, 78213.1),
    ("04-26 21:10", 78213.1, 78247.4, 78198.7, 78198.8),
    ("04-26 21:15", 78198.7, 78226.4, 78180.5, 78208.5),
    ("04-26 21:20", 78208.6, 78235.7, 78202.2, 78216.4),
    ("04-26 21:25", 78216.4, 78234.8, 78139.0, 78151.5),
    ("04-26 21:30", 78151.6, 78151.6, 77912.0, 77989.3),
    ("04-26 21:35", 77989.2, 78073.2, 77933.3, 77995.8),
    ("04-26 21:40", 77995.7, 78002.6, 77915.9, 77950.6),
    ("04-26 21:45", 77950.7, 77958.3, 77815.0, 77911.5),
    ("04-26 21:50", 77911.6, 78554.9, 77777.0, 78525.6),
    ("04-26 21:55", 78525.6, 78994.8, 78299.6, 78369.7),
    ("04-26 22:00", 78369.6, 78544.1, 78307.0, 78367.3),

    ("04-26 22:05", 78367.3, 78538.2, 78343.2, 78486.4),
    ("04-26 22:10", 78486.4, 78529.2, 78428.9, 78521.9),

    ("04-26 22:15", 78521.9, 78821.1, 78507.1, 78705.4),

    ("04-26 22:20", 78705.5, 78736.2, 78604.4, 78627.9),

    ("04-26 22:25", 78628.0, 78645.0, 78459.8, 78484.8),
    ("04-26 22:30", 78484.7, 78484.7, 77915.5, 78012.1),

    ("04-26 22:35", 78012.0, 78156.9, 77956.9, 78124.3),
    ("04-26 22:40", 78124.3, 78255.0, 78104.5, 78241.3),
    ("04-26 22:45", 78241.2, 78398.9, 78222.8, 78359.1),

    ("04-26 22:50", 78359.0, 78359.1, 78262.9, 78321.2),

    ("04-26 22:55", 78321.3, 78325.0, 78250.1, 78274.7),
    ("04-26 23:00", 78274.7, 78359.2, 78215.0, 78272.7),
    ("04-26 23:05", 78272.7, 78324.3, 78234.3, 78276.1),
    ("04-26 23:10", 78276.1, 78361.8, 78276.1, 78314.0),
    ("04-26 23:15", 78313.9, 78365.0, 78223.6, 78245.1),
    ("04-26 23:20", 78245.1, 78424.5, 78245.0, 78354.2),
    ("04-26 23:25", 78354.2, 78409.8, 78106.2, 78109.0),
    ("04-26 23:30", 78109.0, 78391.3, 77988.1, 78297.6),
    ("04-26 23:35", 78297.7, 78442.3, 78244.2, 78403.0),
    ("04-26 23:40", 78403.0, 78569.6, 78393.8, 78560.2),
    ("04-26 23:45", 78560.2, 78870.3, 78550.0, 78719.7),
    ("04-26 23:50", 78719.8, 78773.1, 78603.9, 78617.5),
    ("04-26 23:55", 78617.5, 78628.9, 78574.1, 78613.5),
    ("04-27 00:00", 78614.4, 78842.7, 78599.3, 78759.9),
    ("04-27 00:05", 78759.9, 78799.6, 78673.8, 78676.4),
    ("04-27 00:10", 78676.4, 78696.3, 78520.0, 78542.0),
    ("04-27 00:15", 78542.1, 78589.4, 78497.0, 78575.3),
    ("04-27 00:20", 78575.3, 78604.6, 78500.0, 78505.1),
    ("04-27 00:25", 78505.0, 78505.4, 78319.1, 78443.4),
    ("04-27 00:30", 78443.3, 78470.3, 78356.7, 78444.4),
    ("04-27 00:35", 78444.4, 78628.0, 78424.9, 78627.9),

    ("04-27 00:40", 78628.0, 78788.0, 78627.9, 78774.2),

    ("04-27 07:55", 77647.0, 77671.8, 77556.7, 77556.7),
    ("04-27 08:00", 77556.7, 77669.2, 77541.0, 77666.0),
    ("04-27 08:05", 77666.0, 77685.1, 77566.5, 77570.9),
    ("04-27 08:10", 77570.9, 77605.5, 77562.6, 77590.7),
    ("04-27 08:15", 77590.7, 77646.8, 77590.6, 77613.6),
    ("04-27 08:20", 77613.5, 77628.0, 77550.0, 77609.9),
    ("04-27 08:25", 77609.9, 77614.9, 77517.4, 77524.3),
    ("04-27 08:30", 77524.3, 77568.7, 77500.0, 77566.1),
    ("04-27 08:35", 77566.2, 77625.8, 77550.5, 77588.8),
    ("04-27 08:40", 77588.7, 77588.7, 77533.3, 77575.5),
    ("04-27 08:45", 77575.5, 77726.2, 77575.5, 77691.0),
    ("04-27 08:50", 77691.0, 77766.1, 77672.0, 77718.0),
    ("04-27 08:55", 77718.0, 77775.3, 77718.0, 77763.5),
    ("04-27 09:00", 77763.4, 77785.9, 77740.1, 77777.0),
    ("04-27 09:05", 77777.1, 77817.0, 77750.0, 77750.1),
    ("04-27 09:10", 77750.0, 77810.0, 77740.0, 77810.0),
    ("04-27 09:15", 77810.0, 77810.0, 77718.0, 77718.0),
    ("04-27 09:20", 77718.1, 77735.0, 77661.1, 77661.1),
    ("04-27 09:25", 77661.1, 77750.0, 77657.1, 77739.1),
    ("04-27 09:30", 77739.2, 77945.0, 77719.0, 77882.6),
    ("04-27 09:35", 77882.6, 77910.0, 77815.4, 77864.5),
    ("04-27 09:40", 77864.4, 77928.5, 77844.2, 77907.0),
    ("04-27 09:45", 77907.0, 77931.8, 77850.3, 77864.9),
    ("04-27 09:50", 77864.9, 77945.0, 77856.1, 77944.9),
    ("04-27 09:55", 77945.0, 77949.9, 77856.1, 77856.1),
    ("04-27 10:00", 77856.1, 77903.1, 77806.8, 77819.3),
    ("04-27 10:05", 77819.2, 77819.2, 77756.0, 77789.0),
    ("04-27 10:10", 77789.1, 77798.4, 77764.1, 77771.7),
    ("04-27 10:15", 77771.7, 77796.1, 77756.0, 77792.3),
    ("04-27 10:20", 77792.3, 77792.3, 77750.0, 77754.0),
    ("04-27 10:25", 77754.0, 77768.0, 77740.1, 77768.0),
    ("04-27 10:30", 77768.0, 77799.1, 77756.3, 77788.5),
    ("04-27 10:35", 77788.6, 77830.0, 77788.5, 77830.0),
    ("04-27 10:40", 77830.0, 77886.0, 77822.7, 77832.2),

    ("04-27 10:45", 77832.2, 77833.3, 77801.3, 77804.8),
    ("04-27 10:50", 77804.7, 77859.9, 77801.1, 77814.3),
    ("04-27 10:55", 77814.2, 77824.8, 77806.3, 77806.7),
    ("04-27 11:00", 77806.7, 77842.8, 77750.7, 77750.7),
    ("04-27 11:05", 77750.7, 77790.1, 77710.0, 77710.0),
    ("04-27 11:10", 77710.0, 77745.5, 77700.0, 77738.3),
    ("04-27 11:15", 77738.3, 77762.5, 77705.0, 77760.0),
    ("04-27 11:20", 77760.0, 77814.3, 77750.3, 77801.3),

    ("04-27 11:25", 77801.3, 77854.2, 77791.3, 77815.5),
    ("04-27 11:30", 77815.6, 77848.5, 77791.4, 77799.9),
    ("04-27 11:35", 77800.0, 77805.6, 77737.0, 77754.3),
    ("04-27 11:40", 77754.3, 77781.1, 77753.6, 77768.0),

    ("04-27 11:45", 77768.1, 77770.7, 77750.4, 77761.4),

    ("04-27 19:00", 76790.6, 76835.5, 76761.4, 76768.0),
    ("04-27 19:05", 76768.1, 76773.5, 76691.0, 76756.5),
    ("04-27 19:10", 76756.6, 76858.3, 76735.7, 76836.9),
    ("04-27 19:15", 76836.9, 76863.0, 76764.3, 76764.4),
    ("04-27 19:20", 76764.3, 76789.2, 76718.5, 76718.6),
    ("04-27 19:25", 76718.7, 76726.8, 76584.0, 76584.1),
    ("04-27 19:30", 76584.1, 76612.2, 76400.0, 76547.3),
    ("04-27 19:35", 76547.3, 76620.0, 76502.0, 76556.9),
    ("04-27 19:40", 76556.9, 76750.1, 76556.9, 76741.0),
    ("04-27 19:45", 76740.9, 76810.5, 76720.0, 76760.5),
    ("04-27 19:50", 76760.5, 76820.0, 76760.5, 76806.2),
    ("04-27 19:55", 76806.2, 76844.4, 76762.1, 76844.4),
    ("04-27 20:00", 76844.3, 76914.0, 76780.9, 76903.0),
    ("04-27 20:05", 76903.1, 76967.8, 76856.8, 76873.8),
    ("04-27 20:10", 76873.8, 76897.6, 76845.4, 76856.1),
    ("04-27 20:15", 76856.0, 76923.1, 76856.0, 76900.1),
    ("04-27 20:20", 76900.1, 76948.6, 76863.5, 76948.5),
    ("04-27 20:25", 76948.6, 76962.0, 76901.2, 76952.4),
    ("04-27 20:30", 76952.4, 76976.8, 76936.6, 76964.0),
    ("04-27 20:35", 76964.1, 77037.0, 76956.4, 76958.8),
    ("04-27 20:40", 76958.8, 76970.0, 76910.2, 76942.2),
    ("04-27 20:45", 76942.2, 76949.6, 76893.4, 76920.7),
    ("04-27 20:50", 76920.6, 76950.0, 76899.9, 76920.0),
    ("04-27 20:55", 76920.0, 76963.3, 76898.8, 76915.8),
    ("04-27 21:00", 76915.8, 76915.9, 76854.6, 76873.6),
    ("04-27 21:05", 76873.7, 76881.6, 76830.2, 76881.6),
    ("04-27 21:10", 76881.6, 76881.6, 76783.0, 76844.7),
    ("04-27 21:15", 76844.7, 76904.0, 76820.0, 76821.8),
    ("04-27 21:20", 76821.7, 76863.1, 76806.2, 76815.6),
    ("04-27 21:25", 76815.5, 76892.0, 76806.2, 76867.4),
    ("04-27 21:30", 76867.4, 76907.3, 76867.3, 76907.3),
    ("04-27 21:35", 76907.3, 76944.5, 76884.2, 76887.3),
    ("04-27 21:40", 76887.4, 76917.9, 76830.1, 76857.8),
    ("04-27 21:45", 76857.8, 76871.2, 76797.4, 76871.1),

    ("04-27 21:50", 76871.2, 76909.4, 76800.0, 76801.5),

    ("04-30 09:55", 76111.2, 76111.2, 76062.4, 76062.7),
    ("04-30 10:00", 76062.7, 76125.5, 76054.3, 76112.6),
    ("04-30 10:05", 76112.6, 76136.6, 76071.4, 76110.2),
    ("04-30 10:10", 76110.2, 76114.0, 76004.0, 76014.4),
    ("04-30 10:15", 76014.3, 76046.1, 75984.1, 75984.6),
    ("04-30 10:20", 75984.6, 76030.7, 75976.3, 75976.3),
    ("04-30 10:25", 75976.3, 76000.0, 75943.3, 75952.8),
    ("04-30 10:30", 75952.8, 76079.6, 75952.8, 76022.7),
    ("04-30 10:35", 76022.7, 76088.8, 76009.6, 76045.8),
    ("04-30 10:40", 76045.8, 76049.7, 75980.5, 76016.1),
    ("04-30 10:45", 76016.2, 76043.7, 76000.0, 76000.1),
    ("04-30 10:50", 76000.0, 76029.3, 75967.7, 76016.4),
    ("04-30 10:55", 76016.4, 76018.0, 75980.0, 76001.6),
    ("04-30 11:00", 76001.7, 76066.2, 76001.6, 76066.2),
    ("04-30 11:05", 76066.1, 76181.1, 76046.0, 76146.0),
    ("04-30 11:10", 76145.8, 76233.0, 76117.4, 76117.4),
    ("04-30 11:15", 76117.4, 76160.0, 76107.0, 76115.6),
    ("04-30 11:20", 76115.5, 76127.1, 76060.0, 76060.0),
    ("04-30 11:25", 76060.1, 76084.6, 76055.6, 76075.1),
    ("04-30 11:30", 76075.1, 76087.9, 76002.3, 76057.7),
    ("04-30 11:35", 76057.7, 76100.0, 76028.2, 76028.2),
    ("04-30 11:40", 76028.2, 76028.2, 75858.0, 75893.5),
    ("04-30 11:45", 75893.4, 76050.0, 75836.0, 76046.1),
    ("04-30 11:50", 76046.1, 76068.5, 75965.8, 76000.0),
    ("04-30 11:55", 75999.9, 76038.7, 75992.8, 76032.9),
    ("04-30 12:00", 76032.9, 76118.9, 76009.8, 76076.9),
    ("04-30 12:05", 76077.0, 76140.0, 76057.4, 76078.9),
    ("04-30 12:10", 76079.0, 76111.0, 76052.2, 76109.9),
    ("04-30 12:15", 76110.0, 76200.0, 76101.4, 76199.9),
    ("04-30 12:20", 76199.9, 76333.3, 76186.3, 76315.1),
    ("04-30 12:25", 76315.0, 76315.1, 76278.6, 76298.8),
    ("04-30 12:30", 76298.7, 76375.1, 76284.3, 76307.3),
    ("04-30 12:35", 76307.3, 76307.3, 76280.4, 76290.7),
    ("04-30 12:40", 76290.8, 76302.0, 76199.0, 76199.0),

    ("04-30 12:45", 76199.1, 76285.0, 76199.0, 76270.5),

    ("04-30 12:50", 76270.5, 76370.0, 76257.7, 76275.3),
    ("04-30 12:55", 76275.3, 76284.8, 76251.3, 76259.0),

    ("04-30 13:00", 76259.0, 76320.8, 76256.7, 76280.8),

    ("04-30 17:40", 76133.6, 76133.6, 76100.0, 76126.8),
    ("04-30 17:45", 76126.8, 76200.0, 76125.5, 76174.6),
    ("04-30 17:50", 76174.5, 76225.0, 76145.0, 76220.0),
    ("04-30 17:55", 76219.9, 76268.0, 76209.1, 76209.2),
    ("04-30 18:00", 76209.2, 76340.9, 76206.1, 76297.0),
    ("04-30 18:05", 76297.0, 76297.0, 76231.9, 76267.2),
    ("04-30 18:10", 76267.3, 76267.3, 76210.0, 76230.1),
    ("04-30 18:15", 76230.0, 76438.3, 76229.8, 76376.0),
    ("04-30 18:20", 76376.1, 76396.2, 76351.8, 76364.5),
    ("04-30 18:25", 76364.5, 76364.5, 76240.0, 76249.9),
    ("04-30 18:30", 76250.0, 76299.4, 76166.3, 76225.7),
    ("04-30 18:35", 76225.8, 76281.4, 76225.8, 76277.6),
    ("04-30 18:40", 76277.7, 76382.1, 76268.5, 76357.3),
    ("04-30 18:45", 76357.3, 76393.7, 76321.2, 76381.5),
    ("04-30 18:50", 76381.5, 76440.0, 76352.1, 76352.6),
    ("04-30 18:55", 76352.6, 76352.7, 76309.1, 76309.1),
    ("04-30 19:00", 76309.2, 76339.0, 76264.2, 76291.5),
    ("04-30 19:05", 76291.6, 76389.3, 76291.5, 76387.7),
    ("04-30 19:10", 76387.7, 76456.0, 76385.3, 76413.1),
    ("04-30 19:15", 76413.1, 76416.1, 76390.3, 76392.0),
    ("04-30 19:20", 76392.0, 76455.9, 76379.9, 76455.2),
    ("04-30 19:25", 76455.1, 76466.6, 76424.6, 76432.8),
    ("04-30 19:30", 76432.8, 76470.5, 76428.4, 76436.8),
    ("04-30 19:35", 76436.8, 76470.0, 76383.9, 76456.0),
    ("04-30 19:40", 76455.9, 76455.9, 76368.1, 76402.1),
    ("04-30 19:45", 76402.1, 76427.7, 76363.3, 76400.2),
    ("04-30 19:50", 76400.2, 76415.1, 76355.7, 76373.4),
    ("04-30 19:55", 76373.4, 76412.8, 76334.2, 76366.7),
    ("04-30 20:00", 76366.7, 76393.6, 76340.1, 76357.9),
    ("04-30 20:05", 76357.9, 76383.8, 76305.6, 76369.2),
    ("04-30 20:10", 76369.1, 76433.5, 76350.5, 76406.7),
    ("04-30 20:15", 76406.6, 76420.0, 76273.3, 76358.1),
    ("04-30 20:20", 76358.1, 76525.4, 76357.6, 76420.3),
    ("04-30 20:25", 76420.0, 76430.0, 76399.9, 76429.9),

    ("04-30 20:30", 76429.9, 76462.6, 76399.7, 76442.9),
    ("04-30 20:35", 76442.9, 76482.1, 76442.8, 76482.0),
    ("04-30 20:40", 76482.0, 76500.1, 76454.1, 76473.6),
    ("04-30 20:45", 76473.5, 76536.2, 76463.3, 76515.0),
    ("04-30 20:50", 76515.1, 76515.1, 76485.2, 76499.9),
    ("04-30 20:55", 76499.8, 76500.0, 76444.5, 76451.1),
    ("04-30 21:00", 76451.1, 76481.8, 76438.2, 76481.8),
    ("04-30 21:05", 76481.8, 76495.4, 76405.4, 76405.4),
    ("04-30 21:10", 76405.4, 76454.2, 76405.4, 76453.0),
    ("04-30 21:15", 76453.0, 76453.0, 76395.2, 76395.3),

    ("04-30 22:40", 76266.0, 76292.5, 76261.1, 76292.5),
    ("04-30 22:45", 76292.4, 76292.5, 76255.1, 76288.2),
    ("04-30 22:50", 76288.2, 76335.5, 76220.1, 76220.3),
    ("04-30 22:55", 76220.3, 76229.1, 76155.1, 76197.9),
    ("04-30 23:00", 76198.0, 76231.9, 76173.3, 76217.8),
    ("04-30 23:05", 76217.8, 76288.7, 76194.6, 76194.6),
    ("04-30 23:10", 76194.6, 76262.8, 76186.0, 76261.9),
    ("04-30 23:15", 76261.9, 76295.2, 76250.8, 76268.8),
    ("04-30 23:20", 76268.9, 76288.8, 76245.0, 76285.0),
    ("04-30 23:25", 76284.8, 76299.9, 76253.2, 76299.9),
    ("04-30 23:30", 76299.9, 76347.0, 76282.3, 76282.3),
    ("04-30 23:35", 76282.3, 76315.4, 76281.7, 76304.2),
    ("04-30 23:40", 76304.1, 76310.0, 76277.6, 76285.4),
    ("04-30 23:45", 76285.4, 76306.8, 76261.1, 76306.8),
    ("04-30 23:50", 76306.8, 76339.6, 76306.7, 76312.2),
    ("04-30 23:55", 76312.2, 76342.0, 76275.4, 76305.4),
    ("05-01 00:00", 76305.4, 76444.0, 76265.4, 76442.8),
    ("05-01 00:05", 76442.8, 76472.8, 76402.1, 76457.0),
    ("05-01 00:10", 76457.0, 76460.1, 76403.0, 76428.9),
    ("05-01 00:15", 76428.8, 76533.3, 76428.8, 76461.1),
    ("05-01 00:20", 76461.2, 76475.1, 76422.8, 76447.3),
    ("05-01 00:25", 76447.4, 76480.0, 76447.3, 76479.9),
    ("05-01 00:30", 76479.9, 76517.2, 76435.1, 76443.2),
    ("05-01 00:35", 76443.1, 76467.4, 76410.4, 76423.1),
    ("05-01 00:40", 76423.1, 76493.3, 76423.1, 76488.5),
    ("05-01 00:45", 76488.5, 76557.3, 76448.3, 76448.4),
    ("05-01 00:50", 76448.4, 76455.7, 76402.1, 76414.5),
    ("05-01 00:55", 76414.6, 76423.9, 76353.7, 76415.1),
    ("05-01 01:00", 76415.1, 76440.0, 76400.1, 76423.3),
    ("05-01 01:05", 76423.2, 76538.7, 76423.2, 76516.5),
    ("05-01 01:10", 76516.6, 76549.1, 76489.9, 76515.1),
    ("05-01 01:15", 76515.1, 76586.0, 76515.1, 76569.9),
    ("05-01 01:20", 76569.9, 76586.0, 76521.3, 76526.6),
    ("05-01 01:25", 76526.7, 76526.7, 76484.3, 76495.5),

    ("05-01 01:30", 76495.6, 76530.0, 76482.8, 76527.2),

    ("05-02 10:50", 78230.0, 78230.0, 78210.3, 78217.4),
    ("05-02 10:55", 78217.4, 78225.4, 78205.4, 78205.4),
    ("05-02 11:00", 78205.5, 78205.5, 78124.7, 78146.8),
    ("05-02 11:05", 78146.8, 78164.2, 78145.0, 78161.6),
    ("05-02 11:10", 78161.5, 78161.6, 78120.1, 78135.8),
    ("05-02 11:15", 78135.8, 78157.4, 78132.0, 78149.9),
    ("05-02 11:20", 78149.9, 78199.1, 78149.9, 78193.1),
    ("05-02 11:25", 78193.1, 78197.1, 78171.0, 78171.1),
    ("05-02 11:30", 78171.1, 78176.9, 78136.2, 78136.3),
    ("05-02 11:35", 78136.2, 78136.3, 78108.0, 78119.1),
    ("05-02 11:40", 78119.1, 78134.9, 78082.0, 78134.9),
    ("05-02 11:45", 78134.9, 78135.0, 78055.8, 78059.8),
    ("05-02 11:50", 78059.8, 78100.0, 78055.7, 78059.8),
    ("05-02 11:55", 78059.9, 78111.0, 78059.8, 78105.7),
    ("05-02 12:00", 78105.7, 78105.7, 78069.9, 78090.4),
    ("05-02 12:05", 78090.3, 78127.0, 78056.0, 78066.8),
    ("05-02 12:10", 78066.7, 78111.0, 78058.2, 78097.3),
    ("05-02 12:15", 78097.2, 78100.0, 78097.2, 78100.0),
    ("05-02 12:20", 78100.0, 78125.0, 78099.9, 78125.0),
    ("05-02 12:25", 78124.9, 78232.0, 78124.9, 78208.0),
    ("05-02 12:30", 78208.0, 78220.4, 78154.8, 78197.1),
    ("05-02 12:35", 78197.1, 78197.1, 78158.0, 78158.1),
    ("05-02 12:40", 78158.1, 78193.3, 78148.2, 78187.2),
    ("05-02 12:45", 78187.1, 78187.1, 78155.0, 78170.1),
    ("05-02 12:50", 78170.0, 78181.0, 78135.9, 78150.3),
    ("05-02 12:55", 78150.4, 78169.7, 78150.3, 78169.7),
    ("05-02 13:00", 78169.7, 78297.2, 78169.6, 78271.9),
    ("05-02 13:05", 78271.8, 78295.3, 78245.2, 78270.0),
    ("05-02 13:10", 78270.0, 78403.1, 78269.9, 78350.7),
    ("05-02 13:15", 78350.7, 78350.7, 78284.4, 78284.4),
    ("05-02 13:20", 78284.5, 78308.4, 78263.2, 78267.6),
    ("05-02 13:25", 78267.5, 78277.3, 78262.3, 78262.4),
    ("05-02 13:30", 78262.4, 78275.2, 78262.3, 78275.2),
    ("05-02 13:35", 78275.2, 78275.2, 78266.3, 78271.7),

    ("05-02 13:40", 78271.7, 78327.9, 78271.6, 78326.8),

    ("05-02 13:45", 78326.9, 78327.0, 78303.8, 78303.8),

    ("05-02 17:30", 78385.6, 78436.8, 78385.6, 78426.1),
    ("05-02 17:35", 78426.1, 78453.9, 78426.1, 78432.0),
    ("05-02 17:40", 78432.0, 78432.1, 78387.0, 78387.2),
    ("05-02 17:45", 78387.2, 78401.7, 78363.3, 78363.4),
    ("05-02 17:50", 78363.4, 78363.4, 78328.1, 78362.1),
    ("05-02 17:55", 78362.1, 78362.2, 78362.1, 78362.1),
    ("05-02 18:00", 78362.1, 78362.1, 78302.8, 78306.8),
    ("05-02 18:05", 78306.7, 78314.3, 78299.7, 78301.6),
    ("05-02 18:10", 78301.6, 78309.7, 78283.7, 78286.2),
    ("05-02 18:15", 78286.1, 78348.4, 78277.0, 78334.7),
    ("05-02 18:20", 78334.7, 78362.2, 78329.1, 78329.2),
    ("05-02 18:25", 78329.2, 78360.4, 78329.1, 78360.3),
    ("05-02 18:30", 78360.4, 78432.2, 78360.3, 78406.0),
    ("05-02 18:35", 78405.9, 78415.0, 78378.5, 78381.4),
    ("05-02 18:40", 78381.4, 78396.0, 78370.1, 78379.1),
    ("05-02 18:45", 78379.1, 78414.1, 78379.0, 78407.9),
    ("05-02 18:50", 78407.9, 78459.0, 78407.9, 78443.8),
    ("05-02 18:55", 78443.9, 78450.0, 78432.0, 78432.1),
    ("05-02 19:00", 78432.0, 78433.0, 78412.3, 78420.1),
    ("05-02 19:05", 78420.1, 78429.0, 78408.0, 78429.0),
    ("05-02 19:10", 78429.0, 78477.0, 78428.9, 78437.2),
    ("05-02 19:15", 78437.2, 78447.2, 78414.7, 78417.8),
    ("05-02 19:20", 78417.8, 78422.0, 78404.8, 78421.9),
    ("05-02 19:25", 78421.9, 78431.4, 78420.8, 78420.8),
    ("05-02 19:30", 78420.8, 78429.4, 78407.3, 78429.3),
    ("05-02 19:35", 78429.3, 78429.4, 78421.1, 78425.4),
    ("05-02 19:40", 78425.4, 78486.5, 78425.4, 78460.0),
    ("05-02 19:45", 78460.0, 78460.1, 78448.0, 78451.3),
    ("05-02 19:50", 78451.3, 78451.4, 78429.2, 78429.2),
    ("05-02 19:55", 78429.2, 78443.8, 78416.5, 78443.8),
    ("05-02 20:00", 78444.1, 78449.0, 78408.3, 78414.5),
    ("05-02 20:05", 78414.4, 78418.3, 78407.9, 78416.5),
    ("05-02 20:10", 78416.5, 78416.6, 78394.5, 78394.5),
    ("05-02 20:15", 78394.5, 78396.1, 78385.3, 78392.8),

    ("05-02 20:20", 78392.7, 78400.0, 78392.7, 78395.6),
    ("05-02 20:25", 78395.7, 78395.7, 78383.4, 78395.0),
    ("05-02 20:30", 78394.9, 78413.7, 78394.9, 78408.4),
    ("05-02 20:35", 78408.5, 78440.0, 78408.4, 78440.0),

    ("05-02 20:40", 78439.9, 78439.9, 78388.6, 78400.0),

    ("05-02 21:20", 78445.0, 78448.7, 78429.9, 78436.7),
    ("05-02 21:25", 78436.7, 78458.1, 78429.9, 78455.4),
    ("05-02 21:30", 78455.4, 78515.1, 78455.4, 78505.7),
    ("05-02 21:35", 78505.6, 79145.0, 78491.4, 78863.1),
    ("05-02 21:40", 78863.0, 78869.6, 78718.2, 78767.0),
    ("05-02 21:45", 78767.0, 78880.0, 78729.4, 78749.7),
    ("05-02 21:50", 78749.7, 78777.0, 78675.8, 78678.6),
    ("05-02 21:55", 78678.7, 78736.1, 78678.7, 78689.8),
    ("05-02 22:00", 78689.7, 78773.0, 78624.0, 78676.5),
    ("05-02 22:05", 78676.5, 78748.8, 78664.8, 78709.8),
    ("05-02 22:10", 78709.8, 78746.9, 78699.1, 78745.2),
    ("05-02 22:15", 78745.2, 78745.2, 78637.3, 78649.7),
    ("05-02 22:20", 78649.6, 78701.0, 78580.6, 78597.5),
    ("05-02 22:25", 78597.5, 78605.6, 78569.2, 78590.0),
    ("05-02 22:30", 78589.9, 78680.0, 78588.4, 78679.9),
    ("05-02 22:35", 78680.0, 78717.0, 78620.1, 78620.1),
    ("05-02 22:40", 78620.1, 78668.9, 78610.1, 78619.9),
    ("05-02 22:45", 78620.0, 78680.7, 78619.4, 78680.7),
    ("05-02 22:50", 78680.6, 78809.4, 78663.0, 78767.5),
    ("05-02 22:55", 78767.5, 78838.0, 78767.5, 78793.2),
    ("05-02 23:00", 78793.2, 78793.2, 78696.9, 78714.5),
    ("05-02 23:05", 78714.4, 78714.4, 78650.0, 78679.0),
    ("05-02 23:10", 78679.0, 78735.8, 78666.3, 78697.7),
    ("05-02 23:15", 78697.7, 78727.4, 78688.0, 78695.2),
    ("05-02 23:20", 78695.1, 78734.6, 78684.8, 78715.3),
    ("05-02 23:25", 78715.2, 78774.6, 78715.2, 78766.6),
    ("05-02 23:30", 78766.6, 78784.7, 78743.0, 78743.0),
    ("05-02 23:35", 78743.1, 78754.8, 78670.0, 78670.0),
    ("05-02 23:40", 78670.1, 78680.1, 78653.9, 78653.9),
    ("05-02 23:45", 78653.9, 78676.1, 78622.0, 78639.1),
    ("05-02 23:50", 78639.1, 78662.1, 78588.3, 78651.6),
    ("05-02 23:55", 78651.5, 78653.6, 78619.0, 78652.9),
    ("05-03 00:00", 78652.8, 78740.5, 78652.8, 78675.9),
    ("05-03 00:05", 78675.8, 78675.9, 78555.0, 78575.1),
]

# =================== 15M MUM VERİSİ (Binance API) ===================
# Kaynak: /fapi/v1/klines?symbol=BTCUSDT&interval=15m&limit=200 → UTC+3

CANDLES_15M = [
    ("03-30 04:15", 66371.4, 66634.8, 66289.9, 66565.6),
    ("03-30 04:30", 66565.6, 66700.0, 66495.4, 66634.3),
    ("03-30 04:45", 66634.2, 66806.1, 66570.4, 66624.1),
    ("03-30 05:00", 66624.2, 66841.8, 66538.5, 66813.6),
    ("03-30 05:15", 66813.6, 66875.0, 66650.2, 66720.0),
    ("03-30 05:30", 66720.0, 67021.0, 66560.0, 67021.0),
    ("03-30 05:45", 67021.0, 67487.7, 66974.0, 67087.0),
    ("03-30 06:00", 67087.1, 67117.2, 66934.7, 66980.1),
    ("03-30 06:15", 66980.1, 67264.5, 66966.0, 67208.9),
    ("03-30 06:30", 67208.9, 67254.6, 67103.7, 67168.6),
    ("03-30 06:45", 67168.5, 67288.8, 67086.2, 67139.8),
    ("03-30 07:00", 67140.0, 67466.0, 67129.3, 67389.6),
    ("03-30 07:15", 67389.6, 67625.1, 67339.3, 67414.8),
    ("03-30 07:30", 67414.7, 67529.5, 67350.0, 67386.9),
    ("03-30 07:45", 67386.9, 67620.0, 67384.3, 67579.1),
    ("03-30 08:00", 67579.2, 67777.0, 67542.7, 67608.9),
    ("03-30 08:15", 67609.0, 67699.0, 67549.9, 67623.5),
    ("03-30 08:30", 67623.6, 67671.2, 67412.0, 67463.5),
    ("03-30 08:45", 67463.5, 67529.2, 67404.0, 67459.0),
    ("03-30 09:00", 67459.0, 67550.0, 67378.3, 67409.9),
    ("03-30 09:15", 67409.9, 67430.0, 67238.6, 67288.5),
    ("03-30 09:30", 67288.5, 67369.3, 67250.0, 67333.7),
    ("03-30 09:45", 67333.7, 67394.7, 67264.6, 67273.4),
    ("03-30 10:00", 67273.5, 67430.0, 67180.5, 67349.8),
    ("03-30 10:15", 67349.9, 67402.8, 67262.8, 67301.2),
    ("03-30 10:30", 67301.3, 67399.9, 67255.0, 67283.7),
    ("03-30 10:45", 67283.7, 67612.6, 67267.2, 67595.9),
    ("03-30 11:00", 67595.9, 67888.5, 67574.6, 67865.1),
    ("03-30 11:15", 67865.0, 67880.0, 67688.9, 67727.0),
    ("03-30 11:30", 67727.1, 67920.0, 67690.1, 67725.4),
    ("03-30 11:45", 67725.1, 67784.7, 67623.1, 67634.0),
    ("03-30 12:00", 67633.9, 67667.9, 67538.5, 67550.0),
    ("03-30 12:15", 67549.9, 67629.0, 67467.6, 67485.1),
    ("03-30 12:30", 67485.0, 67537.4, 67427.8, 67527.0),
    ("03-30 12:45", 67527.0, 67564.1, 67426.0, 67466.2),
    ("03-30 13:00", 67466.2, 67470.9, 67365.0, 67411.9),
    ("03-30 13:15", 67411.9, 67465.0, 67383.9, 67391.0),
    ("03-30 13:30", 67391.0, 67410.0, 67333.3, 67409.0),
    ("03-30 13:45", 67409.0, 67498.0, 67390.6, 67463.0),
    ("03-30 14:00", 67463.1, 67565.7, 67459.7, 67559.0),
    ("03-30 14:15", 67559.0, 67998.0, 67508.1, 67655.9),
    ("03-30 14:30", 67655.9, 67719.7, 67475.0, 67565.8),
    ("03-30 14:45", 67565.9, 67709.2, 67550.1, 67651.5),
    ("03-30 15:00", 67651.5, 67846.4, 67627.7, 67808.6),
    ("03-30 15:15", 67808.7, 67950.0, 67762.0, 67827.1),
    ("03-30 15:30", 67827.2, 67929.8, 67775.3, 67847.6),
    ("03-30 15:45", 67847.6, 67914.9, 67799.9, 67859.3),
    ("03-30 16:00", 67859.4, 67932.9, 67800.1, 67870.6),
    ("03-30 16:15", 67870.6, 68148.4, 67835.7, 67838.1),
    ("03-30 16:30", 67838.1, 68008.5, 67660.4, 67673.5),
    ("03-30 16:45", 67673.6, 67800.0, 67378.7, 67490.9),
    ("03-30 17:00", 67490.8, 67724.6, 67420.1, 67641.9),
    ("03-30 17:15", 67641.9, 67666.0, 67200.0, 67279.1),
    ("03-30 17:30", 67279.0, 67375.0, 67063.9, 67099.9),
    ("03-30 17:45", 67100.0, 67843.8, 67055.0, 67762.7),
    ("03-30 18:00", 67762.8, 67875.0, 67523.1, 67527.9),
    ("03-30 18:15", 67528.0, 67591.5, 67373.7, 67494.0),
    ("03-30 18:30", 67493.9, 67871.8, 67430.5, 67724.1),
    ("03-30 18:45", 67724.0, 67766.5, 67558.9, 67590.2),
    ("03-30 19:00", 67590.2, 67614.9, 67310.0, 67414.2),
    ("03-30 19:15", 67414.1, 67448.5, 67253.3, 67320.6),
    ("03-30 19:30", 67320.6, 67481.0, 67280.8, 67345.9),
    ("03-30 19:45", 67345.8, 67413.5, 67188.0, 67333.0),
    ("03-30 20:00", 67332.9, 67443.8, 67140.5, 67159.2),
    ("03-30 20:15", 67159.3, 67167.3, 66617.3, 66787.2),
    ("03-30 20:30", 66787.3, 66937.2, 66729.9, 66927.6),
    ("03-30 20:45", 66927.6, 66975.9, 66757.3, 66805.2),
    ("03-30 21:00", 66805.1, 66899.9, 66671.2, 66794.1),
    ("03-30 21:15", 66794.1, 66831.8, 66548.0, 66670.9),
    ("03-30 21:30", 66670.9, 66794.9, 66544.4, 66711.3),
    ("03-30 21:45", 66711.3, 66765.2, 66456.4, 66620.6),
    ("03-30 22:00", 66620.6, 66640.0, 66262.5, 66398.1),
    ("03-30 22:15", 66398.1, 66427.5, 66200.1, 66278.0),
    ("03-30 22:30", 66278.1, 66374.8, 66213.5, 66305.7),
    ("03-30 22:45", 66305.7, 66556.7, 66256.5, 66516.0),
    ("03-30 23:00", 66515.9, 66662.6, 66488.7, 66561.1),
    ("03-30 23:15", 66561.1, 66641.2, 66512.0, 66620.0),
    ("03-30 23:30", 66620.0, 66647.0, 66510.9, 66628.5),
    ("03-30 23:45", 66628.4, 66640.7, 66576.7, 66614.9),
    ("03-31 00:00", 66614.9, 66777.0, 66550.0, 66749.2),
    ("03-31 00:15", 66749.3, 66963.6, 66737.5, 66822.0),
    ("03-31 00:30", 66822.1, 66973.5, 66782.4, 66900.0),
    ("03-31 00:45", 66900.0, 66928.5, 66757.9, 66770.6),
    ("03-31 01:00", 66770.6, 66971.2, 66668.2, 66740.5),
    ("03-31 01:15", 66740.4, 66869.2, 66696.4, 66785.7),
    ("03-31 01:30", 66785.7, 66831.5, 66710.0, 66800.0),
    ("03-31 01:45", 66800.1, 66813.6, 66650.9, 66746.5),
    ("03-31 02:00", 66746.4, 66752.7, 66377.1, 66517.5),
    ("03-31 02:15", 66517.6, 66690.7, 66485.3, 66672.1),
    ("03-31 02:30", 66672.1, 66741.0, 66626.6, 66729.6),
    ("03-31 02:45", 66729.6, 66769.1, 66675.4, 66764.4),
    ("03-31 03:00", 66764.4, 66792.4, 66525.6, 66614.5),
    ("03-31 03:15", 66615.0, 66790.1, 66498.9, 66779.9),
    ("03-31 03:30", 66780.0, 66922.8, 66731.5, 66912.6),
    ("03-31 03:45", 66912.6, 67276.0, 66906.8, 67172.5),
    ("03-31 04:00", 67172.5, 67257.8, 67004.2, 67194.6),
    ("03-31 04:15", 67194.6, 67850.0, 67194.6, 67743.0),
    ("03-31 04:30", 67743.0, 68377.0, 67697.2, 67893.3),
    ("03-31 04:45", 67893.3, 68020.3, 67776.8, 67896.2),
    ("03-31 05:00", 67896.1, 67943.0, 67726.9, 67883.5),
    ("03-31 05:15", 67883.8, 68072.7, 67880.4, 68007.1),
    ("03-31 05:30", 68007.0, 68029.0, 67802.2, 67948.0),
    ("03-31 05:45", 67947.9, 68058.0, 67865.4, 67911.8),
    ("03-31 06:00", 67911.8, 67974.8, 67763.1, 67878.6),
    ("03-31 06:15", 67878.6, 67937.4, 67767.5, 67807.2),
    ("03-31 06:30", 67807.2, 67892.1, 67610.8, 67695.4),
    ("03-31 06:45", 67695.5, 67730.0, 67610.5, 67670.8),
    ("03-31 07:00", 67670.8, 67758.7, 67548.0, 67630.1),
    ("03-31 07:15", 67630.1, 67865.7, 67441.8, 67562.7),
    ("03-31 07:30", 67562.7, 67628.1, 67485.7, 67565.0),
    ("03-31 07:45", 67565.1, 67652.2, 67480.0, 67510.1),
    ("03-31 08:00", 67510.1, 67588.0, 67360.5, 67389.9),
    ("03-31 08:15", 67389.9, 67630.0, 67356.4, 67592.3),
    ("03-31 08:30", 67592.4, 67691.0, 67530.9, 67643.4),
    ("03-31 08:45", 67643.4, 67756.8, 67623.3, 67648.9),
    ("03-31 09:00", 67649.0, 67679.5, 67431.4, 67446.5),
    ("03-31 09:15", 67446.6, 67482.3, 67300.1, 67383.2),
    ("03-31 09:30", 67383.3, 67457.3, 67307.6, 67379.0),
    ("03-31 09:45", 67379.1, 67505.8, 67379.0, 67465.4),
    ("03-31 10:00", 67465.4, 67497.0, 67200.0, 67267.2),
    ("03-31 10:15", 67267.2, 67296.4, 67071.9, 67260.9),
    ("03-31 10:30", 67260.8, 67350.0, 67179.7, 67299.9),
    ("03-31 10:45", 67299.9, 67410.0, 67281.2, 67343.8),
    ("03-31 11:00", 67343.9, 67476.9, 67208.4, 67324.0),
    ("03-31 11:15", 67323.9, 67420.0, 67250.6, 67280.4),
    ("03-31 11:30", 67280.3, 67281.9, 66777.0, 66818.9),
    ("03-31 11:45", 66818.9, 66911.9, 66655.0, 66745.1),
    ("03-31 12:00", 66745.1, 66891.8, 66550.0, 66669.5),
    ("03-31 12:15", 66669.6, 66686.3, 66321.0, 66403.9),
    ("03-31 12:30", 66403.9, 66499.7, 66368.0, 66477.4),
    ("03-31 12:45", 66477.4, 66487.0, 65938.0, 66099.3),
    ("03-31 13:00", 66099.3, 66371.9, 66067.0, 66342.5),
    ("03-31 13:15", 66342.4, 66432.0, 66313.2, 66350.0),
    ("03-31 13:30", 66350.1, 66398.5, 66188.7, 66247.3),
    ("03-31 13:45", 66247.2, 66442.0, 66214.6, 66329.4),
    ("03-31 14:00", 66329.4, 66572.3, 66205.0, 66543.4),
    ("03-31 14:15", 66543.3, 66850.0, 66500.0, 66610.0),
    ("03-31 14:30", 66610.0, 66805.7, 66603.9, 66696.1),
    ("03-31 14:45", 66696.0, 66696.1, 66534.0, 66652.4),
    ("03-31 15:00", 66652.4, 66766.5, 66535.0, 66541.3),
    ("03-31 15:15", 66541.3, 66799.4, 66480.0, 66764.5),
    ("03-31 15:30", 66764.4, 66909.3, 66692.5, 66872.9),
    ("03-31 15:45", 66872.8, 66888.0, 66615.2, 66623.8),
    ("03-31 16:00", 66623.8, 66818.9, 66623.8, 66792.0),
    ("03-31 16:15", 66792.0, 66932.6, 66719.9, 66773.8),
    ("03-31 16:30", 66773.7, 67166.5, 66691.9, 66937.6),
    ("03-31 16:45", 66937.6, 67375.0, 66937.6, 67255.6),
    ("03-31 17:00", 67255.6, 67500.0, 67078.8, 67300.4),
    ("03-31 17:15", 67300.0, 67765.8, 67285.2, 67692.7),
    ("03-31 17:30", 67692.7, 67712.2, 67047.5, 67184.3),
    ("03-31 17:45", 67184.2, 67184.3, 66374.4, 66555.9),
    ("03-31 18:00", 66556.0, 67262.2, 66555.9, 67210.5),
    ("03-31 18:15", 67210.6, 67255.0, 66864.9, 66920.8),
    ("03-31 18:30", 66920.8, 67127.4, 66841.8, 66906.5),
    ("03-31 18:45", 66906.5, 67019.1, 66666.5, 66700.0),
    ("03-31 19:00", 66700.0, 66970.4, 66695.9, 66893.2),
    ("03-31 19:15", 66893.1, 67165.5, 66881.5, 67056.5),
    ("03-31 19:30", 67056.4, 67985.5, 66916.6, 67742.0),
    ("03-31 19:45", 67742.1, 67888.0, 67457.0, 67632.6),
    ("03-31 20:00", 67632.6, 68532.7, 67532.8, 68432.9),
    ("03-31 20:15", 68432.8, 68600.0, 67951.2, 68002.3),
    ("03-31 20:30", 68002.4, 68091.9, 67573.9, 67683.7),
    ("03-31 20:45", 67683.6, 67749.0, 67357.1, 67493.9),
    ("03-31 21:00", 67493.8, 67764.9, 67488.0, 67739.7),
    ("03-31 21:15", 67739.7, 67929.7, 67594.4, 67744.9),
    ("03-31 21:30", 67744.9, 67855.4, 67601.9, 67789.9),
    ("03-31 21:45", 67789.9, 67912.8, 67700.4, 67814.6),
    ("03-31 22:00", 67814.5, 67985.8, 67802.0, 67952.5),
    ("03-31 22:15", 67952.6, 67996.0, 67810.5, 67840.3),
    ("03-31 22:30", 67840.4, 67901.0, 67671.3, 67800.0),
    ("03-31 22:45", 67799.9, 67934.9, 67694.0, 67803.0),
    ("03-31 23:00", 67803.0, 68177.2, 67794.8, 68109.6),
    ("03-31 23:15", 68109.6, 68135.6, 67902.4, 67967.3),
    ("03-31 23:30", 67967.2, 68099.1, 67911.1, 68017.1),
    ("03-31 23:45", 68017.1, 68234.0, 67985.0, 68227.2),
    ("04-01 00:00", 68227.3, 68227.3, 67911.2, 67977.3),
    ("04-01 00:15", 67977.3, 68030.0, 67840.4, 67995.9),
    ("04-01 00:30", 67995.9, 68138.0, 67991.7, 68130.0),
    ("04-01 00:45", 68130.1, 68382.9, 68119.0, 68234.6),
    ("04-01 01:00", 68234.7, 68306.9, 68013.4, 68172.8),
    ("04-01 01:15", 68172.8, 68254.4, 68057.4, 68080.0),
    ("04-01 01:30", 68080.1, 68214.9, 67919.5, 68140.0),
    ("04-01 01:45", 68140.1, 68183.4, 68057.1, 68141.6),
    ("04-01 02:00", 68141.7, 68250.0, 68050.0, 68183.7),
    ("04-01 02:15", 68183.6, 68332.6, 68141.0, 68224.3),
    ("04-01 02:30", 68224.2, 68332.0, 68200.0, 68271.3),
    ("04-01 02:45", 68271.4, 68297.1, 68173.1, 68241.5),
    ("04-01 03:00", 68241.4, 68241.5, 67975.3, 68004.7),
    ("04-01 03:15", 68004.6, 68177.9, 67863.3, 67964.3),
    ("04-01 03:30", 67964.3, 68031.7, 67808.1, 68031.2),
    ("04-01 03:45", 68031.2, 68305.1, 67989.8, 68288.0),
    ("04-01 04:00", 68288.0, 68330.0, 68106.3, 68223.7),
    ("04-01 04:15", 68223.8, 68223.8, 67976.5, 68006.4),
    ("04-01 04:30", 68006.3, 68054.7, 67755.1, 67915.8),
    ("04-01 04:45", 67915.9, 67920.0, 67707.5, 67746.4),
    ("04-01 05:00", 67746.4, 67873.1, 67662.2, 67803.3),
    ("04-01 05:15", 67803.3, 67881.2, 67556.1, 67603.6),
    ("04-01 05:30", 67603.7, 67691.3, 67534.9, 67617.7),
    ("04-01 05:45", 67617.7, 67705.8, 67558.7, 67623.8),
    ("04-01 06:00", 67623.9, 68086.2, 67623.9, 67957.5),
    ("04-01 13:00", 68608.4, 68632.1, 68370.1, 68545.1),
    ("04-01 14:00", 68545.2, 68702.3, 68471.5, 68669.9),
    ("04-01 15:00", 68670.0, 68773.9, 68220.9, 68363.8),
    ("04-01 16:00", 68364.1, 68650.0, 68128.0, 68183.2),
    ("04-02 01:00", 68324.8, 68324.8, 68104.6, 68184.2),
    ("04-02 01:15", 68184.2, 68230.0, 68032.9, 68149.9),
    ("04-02 01:30", 68149.9, 68284.2, 68101.6, 68209.4),
    ("04-02 01:45", 68209.3, 68227.9, 68040.2, 68088.4),
    ("04-02 02:00", 68088.5, 68220.9, 68088.5, 68162.3),
    ("04-02 02:15", 68162.4, 68162.4, 68050.0, 68088.3),
    ("04-02 02:30", 68088.3, 68146.0, 67952.2, 68072.3),
    ("04-02 02:45", 68072.3, 68142.2, 68024.1, 68086.5),
    ("04-02 03:00", 68086.4, 68199.6, 68013.3, 68177.3),
    ("04-02 03:15", 68177.3, 68244.8, 68100.0, 68179.1),
    ("04-02 03:30", 68179.0, 68494.4, 68166.5, 68494.3),
    ("04-02 03:45", 68494.3, 68639.1, 68391.6, 68565.1),
    ("04-02 04:00", 68565.2, 68565.2, 67598.0, 68105.3),
    ("04-02 04:15", 68105.4, 68109.1, 67223.0, 67538.9),
    ("04-02 04:30", 67538.9, 67545.7, 67090.0, 67135.9),
    ("04-02 04:45", 67135.9, 67364.7, 67000.3, 67316.4),
    ("04-02 05:00", 67316.4, 67316.4, 66807.6, 66824.9),
    ("04-02 05:15", 66824.9, 66982.2, 66729.5, 66863.7),
    ("04-02 05:30", 66863.8, 67016.5, 66590.0, 66677.4),
    ("04-02 05:45", 66677.4, 66912.4, 66656.3, 66821.6),
    ("04-02 06:00", 66821.6, 66931.9, 66702.6, 66719.6),
    ("04-02 06:15", 66719.6, 66865.7, 66601.5, 66831.6),
    ("04-02 06:30", 66831.6, 66850.0, 66455.9, 66571.4),
    ("04-02 06:45", 66571.4, 66617.0, 66464.5, 66538.4),
    ("04-02 07:00", 66538.4, 66617.7, 66469.9, 66501.2),
    ("04-02 07:15", 66501.2, 66592.3, 66337.0, 66386.8),
    ("04-02 07:30", 66386.9, 66420.0, 66171.8, 66255.2),
    ("04-02 07:45", 66255.2, 66363.9, 66234.9, 66300.2),
    ("04-02 08:00", 66300.2, 66478.2, 66270.0, 66349.8),
    ("04-02 08:15", 66349.9, 66450.0, 66315.1, 66449.9),
    ("04-02 08:30", 66449.9, 66593.4, 66362.2, 66553.6),
    ("04-02 08:45", 66553.7, 66628.8, 66440.0, 66558.2),
    ("04-02 09:00", 66558.2, 66591.9, 66530.0, 66547.0),
    ("04-02 09:15", 66547.0, 66798.9, 66540.0, 66612.7),
    ("04-02 09:30", 66612.6, 66666.5, 66506.4, 66519.9),
    ("04-02 09:45", 66519.9, 66661.5, 66519.9, 66652.9),
    ("04-02 10:00", 66653.0, 66681.8, 66521.4, 66545.3),
    ("04-02 10:15", 66545.4, 66680.3, 66545.3, 66647.2),
    ("04-02 10:30", 66647.2, 66860.0, 66644.1, 66824.2),
    ("04-02 10:45", 66824.2, 66898.5, 66821.3, 66887.9),
    ("04-02 11:00", 66887.8, 66887.9, 66681.3, 66743.9),
    ("04-02 11:15", 66743.8, 66749.8, 66555.7, 66645.3),
    ("04-02 11:30", 66645.2, 66705.2, 66462.4, 66475.6),
    ("04-02 11:45", 66475.7, 66529.7, 66372.9, 66418.2),
    ("04-02 12:00", 66418.1, 66454.5, 66256.0, 66394.4),
    ("04-02 12:15", 66394.4, 66487.0, 66330.6, 66444.1),
    ("04-02 12:30", 66444.1, 66487.7, 66360.8, 66400.1),
    ("04-02 12:45", 66400.0, 66441.4, 66332.0, 66428.6),
    ("04-02 13:00", 66428.7, 66471.9, 66188.1, 66231.9),
    ("04-02 13:15", 66231.9, 66354.9, 66191.7, 66337.0),
    ("04-02 13:30", 66337.1, 66464.5, 66322.9, 66440.8),
    ("04-02 14:00", 66424.1, 66449.7, 66223.0, 66253.4),
    ("04-02 14:15", 66253.3, 66438.0, 66065.1, 66415.5),
    ("04-02 14:30", 66415.5, 66447.4, 66283.0, 66297.9),
    ("04-02 14:45", 66297.8, 66360.0, 66138.2, 66180.6),
    ("04-02 15:15", 66139.3, 66150.6, 65919.1, 66115.3),
    ("04-02 15:30", 66115.4, 66186.5, 66069.0, 66179.8),
    ("04-02 15:45", 66179.8, 66209.3, 65962.2, 66014.2),
    ("04-02 16:00", 66014.3, 66130.0, 65919.1, 65969.0),
    ("04-02 16:15", 65969.1, 66158.7, 65850.4, 66110.9),
    ("04-02 16:30", 66110.9, 66209.8, 65676.1, 65826.6),
    ("04-02 16:45", 65826.7, 66250.0, 65800.0, 66227.3),
    ("04-02 17:00", 66227.3, 66400.1, 66123.0, 66357.1),
    ("04-02 17:15", 66357.0, 66458.0, 66158.0, 66222.0),
    ("04-03 01:00", 66910.7, 66990.0, 66864.0, 66869.5),
    ("04-03 01:15", 66869.6, 66965.9, 66782.0, 66875.6),
    ("04-03 01:30", 66875.7, 66975.0, 66875.7, 66947.1),
    ("04-03 01:45", 66947.2, 67008.5, 66885.0, 66954.0),
    ("04-03 02:00", 66954.0, 67070.2, 66892.3, 66919.2),
    ("04-03 02:15", 66919.2, 67001.3, 66893.4, 66906.3),
    ("04-03 02:30", 66906.2, 66930.5, 66852.4, 66852.8),
    ("04-03 02:45", 66852.8, 66874.1, 66820.6, 66868.5),
    ("04-03 03:00", 66868.6, 66976.2, 66745.0, 66839.9),
    ("04-03 03:15", 66839.9, 66936.4, 66763.9, 66793.9),
    ("04-03 03:30", 66794.0, 66884.1, 66733.8, 66773.0),
    ("04-03 03:45", 66773.0, 66773.1, 66671.0, 66761.8),
    ("04-03 04:00", 66761.8, 66808.5, 66696.3, 66797.2),
    ("04-03 04:15", 66797.3, 66868.8, 66707.0, 66834.9),
    ("04-03 04:30", 66834.8, 66881.3, 66450.0, 66540.5),
    ("04-03 04:45", 66540.6, 66600.2, 66457.6, 66599.0),
    ("04-03 05:00", 66599.1, 66599.1, 66375.0, 66479.6),
    ("04-03 05:15", 66479.6, 66726.7, 66413.3, 66424.9),
    ("04-03 05:30", 66424.9, 66485.7, 66240.0, 66309.1),
    ("04-03 05:45", 66309.1, 66517.2, 66282.0, 66504.6),
    ("04-03 06:00", 66504.6, 66640.3, 66461.0, 66623.9),
    ("04-03 06:15", 66623.9, 66698.5, 66572.1, 66602.1),
    ("04-03 06:30", 66602.2, 66677.7, 66492.6, 66565.7),
    ("04-03 06:45", 66565.8, 66608.0, 66515.3, 66550.0),
    ("04-03 07:00", 66550.1, 66625.3, 66525.0, 66603.9),
    ("04-03 07:15", 66603.9, 66666.0, 66505.6, 66505.6),
    ("04-03 07:30", 66505.7, 66578.1, 66468.0, 66548.9),
    ("04-03 07:45", 66548.8, 66648.4, 66533.0, 66578.8),
    ("04-03 08:00", 66578.8, 66641.0, 66554.1, 66554.1),
    ("04-03 08:15", 66554.2, 66561.6, 66375.1, 66549.1),
    ("04-03 08:30", 66549.0, 66789.6, 66549.0, 66740.1),
    ("04-03 08:45", 66740.1, 66740.1, 66478.8, 66574.9),
    ("04-03 09:00", 66574.9, 66635.9, 66523.2, 66635.9),
    ("04-03 09:15", 66635.9, 66665.8, 66567.1, 66594.2),
    ("04-03 09:30", 66594.3, 66748.7, 66550.0, 66706.0),
    ("04-03 09:45", 66706.1, 66770.0, 66680.0, 66762.0),
    ("04-03 10:00", 66762.1, 66879.4, 66716.4, 66785.7),
    ("04-03 10:15", 66785.7, 66916.4, 66764.1, 66913.2),
    ("04-03 10:30", 66913.1, 67233.3, 66882.4, 67043.4),
    ("04-03 10:45", 67043.3, 67095.7, 66971.0, 67008.8),
    ("04-03 11:00", 67008.8, 67258.0, 66993.4, 67137.5),
    ("04-03 11:15", 67137.4, 67188.0, 67012.8, 67023.0),
    ("04-03 11:30", 67023.0, 67090.0, 66864.1, 66900.4),
    ("04-03 11:45", 66900.3, 66978.4, 66867.0, 66935.0),
    ("04-03 12:00", 66935.1, 66976.0, 66850.0, 66866.0),
    ("04-03 12:15", 66866.1, 66893.5, 66714.3, 66790.0),
    ("04-03 12:30", 66790.0, 66888.0, 66757.0, 66868.4),
    ("04-03 12:45", 66868.5, 66874.4, 66772.0, 66828.9),
    ("04-03 13:00", 66828.9, 66828.9, 66736.0, 66791.2),
    ("04-03 13:15", 66791.2, 66847.9, 66727.7, 66727.7),
    ("04-03 13:30", 66727.8, 66765.7, 66644.0, 66749.2),
    ("04-03 13:45", 66749.3, 66871.9, 66749.3, 66845.3),
    ("04-03 14:00", 66845.3, 66888.2, 66790.6, 66823.2),
    ("04-03 14:15", 66823.3, 66927.7, 66807.8, 66904.9),
    ("04-03 14:30", 66904.9, 67041.9, 66880.2, 66965.0),
    ("04-03 14:45", 66965.0, 67009.0, 66911.6, 66983.4),
    ("04-03 15:00", 66983.5, 67018.0, 66890.4, 66978.3),
    ("04-03 15:15", 66978.4, 67110.4, 66910.0, 67087.1),
    ("04-03 15:30", 67087.2, 67350.0, 66751.9, 66837.1),
    ("04-03 15:45", 66836.7, 66868.3, 66605.9, 66690.4),
    ("04-03 16:00", 66690.4, 66707.1, 66525.4, 66645.9),
    ("04-03 16:15", 66645.9, 66705.7, 66564.0, 66649.9),
    ("04-03 16:30", 66650.0, 66651.4, 66546.7, 66574.9),
    ("04-03 16:45", 66574.9, 66663.3, 66478.5, 66644.6),
    ("04-03 17:00", 66644.6, 66776.8, 66600.0, 66752.9),
    ("04-03 17:15", 66752.9, 66968.1, 66688.5, 66878.1),
    ("04-03 17:30", 66878.2, 66910.8, 66773.3, 66775.8),
    ("04-03 17:45", 66775.9, 66953.7, 66775.8, 66900.0),
    ("04-03 18:00", 66899.9, 66999.0, 66876.6, 66931.8),
    ("04-03 18:15", 66931.8, 66931.9, 66828.6, 66899.8),
    ("04-03 18:30", 66899.8, 66956.2, 66804.2, 66828.4),
    ("04-03 18:45", 66828.5, 66853.4, 66778.9, 66806.1),
    ("04-03 19:00", 66806.0, 66890.0, 66800.0, 66881.5),
    ("04-03 19:15", 66881.6, 66965.0, 66843.3, 66959.0),
    ("04-03 19:30", 66958.9, 66979.0, 66896.4, 66944.7),
    ("04-03 19:45", 66944.7, 67046.1, 66911.3, 66972.5),
    ("04-03 20:00", 66972.5, 67040.0, 66920.2, 66920.3),
    ("04-03 20:15", 66920.3, 66936.8, 66714.1, 66844.6),
    ("04-03 20:30", 66844.6, 66923.6, 66822.7, 66860.0),
    ("04-03 20:45", 66860.0, 66869.9, 66773.1, 66811.0),
    ("04-03 21:00", 66811.0, 66838.2, 66746.9, 66807.0),
    ("04-03 21:15", 66807.0, 66899.7, 66788.7, 66850.0),
    ("04-03 21:30", 66850.1, 66890.1, 66805.0, 66826.2),
    ("04-03 21:45", 66826.2, 66826.2, 66767.7, 66783.7),
    ("04-03 22:00", 66783.6, 66822.8, 66746.0, 66752.4),
    ("04-03 22:15", 66752.3, 66827.3, 66751.0, 66765.2),
    ("04-03 22:30", 66765.2, 66829.3, 66740.6, 66821.7),
    ("04-03 22:45", 66821.7, 66882.9, 66818.3, 66857.0),
    ("04-03 23:00", 66857.0, 66877.3, 66816.0, 66869.0),
    ("04-03 23:15", 66869.0, 66878.0, 66839.6, 66847.7),
    ("04-03 23:30", 66847.7, 66888.0, 66821.5, 66856.7),
    ("04-03 23:45", 66856.6, 66877.0, 66800.0, 66800.1),
    ("04-04 00:00", 66800.0, 66900.3, 66791.8, 66878.6),
    ("04-04 00:15", 66878.7, 66900.3, 66840.1, 66860.6),
    ("04-04 00:30", 66860.5, 66900.3, 66848.0, 66900.3),
    ("04-04 00:45", 66900.3, 66946.3, 66869.5, 66929.5),
    ("04-04 01:00", 66929.4, 66943.0, 66813.0, 66839.2),
    ("04-04 01:15", 66839.1, 66902.8, 66839.1, 66885.7),
    ("04-04 01:30", 66885.7, 66930.6, 66872.4, 66901.0),
    ("04-04 01:45", 66901.0, 66907.0, 66818.5, 66860.0),
    ("04-04 02:00", 66859.9, 66880.9, 66823.5, 66844.8),
    ("04-04 02:15", 66844.8, 66858.3, 66804.3, 66828.1),
    ("04-04 02:30", 66828.1, 66893.5, 66800.7, 66841.2),
    ("04-04 02:45", 66841.2, 66930.0, 66840.8, 66930.0),
    ("04-04 03:00", 66930.0, 66935.3, 66860.0, 66873.1),
    ("04-04 03:15", 66873.1, 66935.3, 66860.0, 66885.6),
    ("04-04 03:30", 66885.6, 66930.0, 66875.1, 66905.3),
    ("04-04 03:45", 66905.2, 66905.2, 66855.0, 66863.4),
    ("04-04 04:00", 66863.4, 66895.7, 66819.8, 66819.9),
    ("04-04 04:15", 66819.8, 66848.3, 66811.4, 66811.4),
    ("04-04 04:30", 66811.5, 66837.1, 66795.8, 66798.2),
    ("04-04 04:45", 66798.1, 66822.0, 66798.1, 66820.0),
    ("04-04 05:00", 66820.0, 66891.4, 66791.8, 66816.9),
    ("04-04 05:15", 66817.0, 66817.0, 66781.6, 66804.7),
    ("04-04 05:30", 66804.7, 66859.6, 66799.9, 66800.8),
    ("04-04 05:45", 66800.8, 66816.4, 66773.3, 66814.1),
    ("04-04 06:00", 66814.0, 66875.4, 66814.0, 66867.9),
    ("04-04 06:15", 66867.9, 66867.9, 66818.4, 66824.4),
    ("04-04 06:30", 66824.4, 66829.9, 66806.2, 66816.3),
    ("04-04 06:45", 66816.4, 66838.3, 66798.8, 66799.1),
    ("04-04 07:00", 66799.1, 66821.8, 66770.0, 66773.0),
    ("04-04 07:15", 66773.1, 66835.0, 66745.5, 66834.6),
    ("04-04 07:30", 66834.6, 66837.6, 66818.2, 66831.0),
    ("04-04 07:45", 66830.9, 66840.0, 66817.8, 66833.5),
    ("04-04 08:00", 66833.5, 66866.4, 66826.9, 66830.6),
    ("04-04 08:15", 66830.9, 66878.8, 66817.8, 66849.7),
    ("04-04 08:30", 66849.8, 66908.4, 66844.8, 66868.8),
    ("04-04 08:45", 66868.9, 66894.7, 66862.9, 66871.0),
    ("04-04 09:00", 66871.0, 66934.0, 66871.0, 66926.5),
    ("04-04 09:15", 66926.5, 66940.0, 66876.0, 66920.0),
    ("04-04 09:30", 66920.0, 66925.0, 66886.8, 66924.9),
    ("04-04 09:45", 66925.0, 67023.7, 66924.9, 66981.5),
    ("04-04 10:00", 66981.5, 67004.1, 66955.1, 66973.8),
    ("04-04 10:15", 66973.8, 66983.0, 66904.0, 66928.0),
    ("04-04 10:30", 66928.0, 66970.2, 66927.4, 66934.2),
    ("04-04 10:45", 66934.2, 67019.1, 66919.1, 66982.0),
    ("04-04 11:00", 66982.1, 67020.0, 66957.2, 66968.6),
    ("04-04 11:15", 66968.6, 67025.0, 66964.3, 67017.2),
    ("04-04 11:30", 67017.3, 67017.3, 66928.6, 66943.0),
    ("04-04 11:45", 66943.0, 66945.7, 66874.5, 66907.8),
    ("04-04 12:00", 66907.8, 66957.0, 66882.1, 66948.0),
    ("04-04 12:15", 66948.1, 66958.2, 66910.4, 66944.8),
    ("04-04 12:30", 66944.9, 66953.8, 66927.1, 66928.9),
    ("04-04 12:45", 66929.0, 66954.8, 66928.9, 66952.1),
    ("04-04 13:00", 66952.1, 66993.3, 66880.9, 66880.9),
    ("04-04 13:15", 66880.9, 66923.6, 66880.9, 66906.9),
    ("04-04 13:30", 66906.9, 67039.8, 66894.3, 67008.7),
    ("04-04 13:45", 67008.7, 67150.3, 67001.0, 67139.1),
    ("04-04 14:00", 67139.1, 67223.8, 67111.1, 67134.8),
    ("04-04 14:15", 67134.8, 67134.8, 67068.3, 67092.7),
    ("04-04 14:30", 67092.8, 67125.5, 67050.0, 67111.1),
    ("04-04 14:45", 67111.2, 67128.9, 67069.3, 67128.9),
    ("04-04 15:00", 67128.9, 67152.5, 67048.0, 67084.8),
    ("04-04 15:15", 67084.8, 67110.0, 67070.6, 67075.1),
    ("04-04 15:30", 67075.2, 67096.5, 67025.2, 67028.7),
    ("04-04 15:45", 67028.7, 67083.7, 67028.6, 67062.0),
    ("04-04 16:00", 67061.9, 67071.9, 67044.8, 67071.9),
    ("04-04 16:15", 67071.9, 67103.3, 67058.2, 67076.7),
    ("04-04 16:30", 67076.6, 67245.3, 67061.6, 67210.0),
    ("04-04 16:45", 67209.9, 67211.1, 67144.6, 67170.0),
    ("04-04 17:00", 67170.0, 67193.3, 67160.0, 67164.9),
    ("04-04 17:15", 67165.0, 67178.5, 67160.0, 67160.0),
    ("04-04 17:30", 67160.0, 67160.1, 67003.7, 67068.7),
    ("04-04 17:45", 67068.6, 67180.0, 67068.6, 67177.6),
    ("04-04 18:00", 67177.5, 67554.5, 67145.6, 67351.2),
    ("04-04 18:15", 67351.3, 67445.5, 67263.6, 67297.2),
    ("04-04 18:30", 67297.2, 67323.2, 67242.6, 67302.5),
    ("04-04 18:45", 67302.5, 67359.0, 67267.5, 67357.3),
    ("04-04 19:00", 67357.4, 67369.0, 67292.2, 67310.9),
    ("04-04 19:15", 67310.8, 67459.1, 67292.0, 67410.7),
    ("04-04 19:30", 67410.6, 67487.2, 67350.0, 67487.1),
    ("04-04 19:45", 67487.2, 67500.0, 67319.3, 67335.2),
    ("04-04 20:00", 67335.1, 67346.8, 67249.9, 67346.8),
    ("04-04 20:15", 67346.7, 67386.0, 67318.6, 67362.8),
    ("04-04 20:30", 67362.8, 67372.6, 67289.9, 67289.9),
    ("04-04 20:45", 67290.0, 67314.8, 67283.6, 67302.3),
    ("04-04 21:00", 67302.3, 67314.9, 67252.0, 67304.4),
    ("04-04 21:15", 67304.4, 67350.0, 67300.5, 67300.5),
    ("04-04 21:30", 67300.6, 67300.6, 67256.7, 67256.8),
    ("04-04 21:45", 67256.7, 67296.5, 67226.4, 67265.7),
    ("04-04 22:00", 67265.6, 67472.5, 67265.6, 67468.3),
    ("04-04 22:15", 67468.3, 67523.8, 67331.4, 67332.9),
    ("04-04 22:30", 67332.9, 67343.9, 67245.6, 67274.1),
    ("04-04 22:45", 67274.1, 67298.2, 67245.7, 67262.7),
    ("04-04 23:00", 67262.8, 67262.8, 67150.6, 67200.2),
    ("04-04 23:15", 67200.3, 67245.0, 67200.2, 67237.6),
    ("04-04 23:30", 67237.6, 67269.4, 67220.3, 67234.6),
    ("04-04 23:45", 67234.6, 67264.6, 67230.9, 67230.9),
    ("04-05 02:15", 67325.7, 67331.9, 67272.7, 67272.7),
    ("04-05 02:30", 67272.8, 67296.1, 67229.4, 67291.8),
    ("04-05 02:45", 67291.9, 67295.5, 67214.2, 67271.0),
    ("04-05 03:00", 67271.1, 67279.2, 67205.7, 67223.0),
    ("04-05 03:15", 67222.9, 67247.0, 67196.8, 67230.5),
    ("04-05 03:30", 67230.4, 67240.5, 67200.0, 67218.9),
    ("04-05 03:45", 67218.9, 67235.7, 67131.1, 67177.0),
    ("04-05 04:00", 67177.0, 67200.0, 67082.0, 67158.0),
    ("04-05 04:15", 67158.0, 67158.1, 67095.0, 67101.6),
    ("04-05 04:30", 67101.6, 67102.5, 67045.2, 67060.3),
    ("04-05 04:45", 67060.3, 67088.0, 67051.9, 67060.6),
    ("04-05 05:00", 67060.6, 67060.7, 66900.0, 66970.4),
    ("04-05 05:15", 66970.3, 67132.5, 66955.0, 67100.0),
    ("04-05 05:30", 67100.0, 67149.6, 67085.0, 67105.1),
    ("04-05 05:45", 67105.2, 67154.0, 67099.4, 67144.3),
    ("04-05 06:00", 67144.3, 67166.9, 67123.7, 67159.0),
    ("04-05 06:15", 67159.0, 67159.0, 67100.0, 67124.6),
    ("04-05 06:30", 67124.6, 67124.7, 67058.0, 67110.5),
    ("04-05 06:45", 67110.6, 67114.5, 67091.0, 67113.5),
    ("04-05 07:00", 67113.4, 67113.5, 67034.8, 67056.5),
    ("04-05 07:15", 67056.5, 67159.6, 67049.8, 67157.8),
    ("04-05 07:30", 67157.7, 67160.0, 67103.1, 67103.1),
    ("04-05 07:45", 67103.2, 67118.5, 67051.3, 67066.2),
    ("04-05 08:00", 67066.3, 67127.5, 67062.3, 67080.8),
    ("04-05 08:15", 67080.8, 67097.9, 67010.0, 67049.3),
    ("04-05 08:30", 67049.3, 67072.0, 67026.7, 67059.0),
    ("04-05 08:45", 67059.0, 67072.9, 66822.8, 66905.1),
    ("04-05 09:00", 66905.2, 66918.6, 66587.7, 66620.2),
    ("04-05 09:15", 66620.3, 66754.2, 66575.5, 66729.9),
    ("04-05 09:30", 66729.9, 66831.6, 66729.8, 66792.0),
    ("04-05 09:45", 66792.0, 66830.7, 66767.8, 66771.6),
    ("04-05 10:00", 66771.6, 66887.1, 66771.5, 66868.1),
    ("04-05 10:15", 66868.2, 66881.0, 66767.0, 66786.2),
    ("04-05 10:30", 66786.3, 66786.3, 66685.3, 66734.8),
    ("04-05 10:45", 66734.8, 66794.6, 66703.2, 66787.4),
    ("04-05 11:00", 66787.4, 66850.9, 66782.1, 66826.1),
    ("04-05 11:15", 66826.2, 66873.7, 66820.0, 66833.2),
    ("04-05 11:30", 66833.2, 66862.2, 66800.0, 66819.8),
    ("04-05 11:45", 66819.8, 66910.0, 66819.8, 66892.5),
    ("04-05 12:00", 66892.6, 66954.1, 66862.3, 66892.9),
    ("04-05 12:15", 66892.9, 66996.0, 66890.7, 66973.1),
    ("04-05 12:30", 66973.2, 66990.0, 66935.1, 66986.9),
    ("04-05 12:45", 66986.9, 67020.4, 66975.0, 66996.0),
    ("04-05 13:00", 66996.1, 67000.0, 66928.1, 66934.7),
    ("04-05 13:15", 66934.7, 66959.0, 66928.1, 66958.9),
    ("04-05 13:30", 66958.9, 67132.8, 66950.4, 67054.7),
    ("04-05 13:45", 67054.8, 67054.8, 66979.7, 67012.3),
    ("04-05 14:00", 67012.4, 67052.6, 66999.7, 67018.1),
    ("04-05 14:15", 67018.0, 67054.1, 66960.0, 66975.6),
    ("04-05 14:30", 66975.7, 66985.4, 66934.4, 66954.3),
    ("04-05 14:45", 66972.7, 66972.7, 66873.0, 66882.2),
    ("04-05 15:00", 66882.1, 66908.6, 66858.1, 66858.1),
    ("04-05 15:15", 66858.1, 66863.8, 66666.0, 66716.5),
    ("04-05 15:30", 66716.5, 66773.8, 66650.0, 66751.4),
    ("04-05 15:45", 66751.5, 66829.0, 66725.3, 66726.1),
    ("04-05 16:00", 66726.1, 66830.1, 66673.4, 66676.6),
    ("04-05 16:15", 66676.6, 66832.8, 66666.0, 66802.3),
    ("04-05 16:30", 66802.2, 66892.9, 66802.2, 66863.4),
    ("04-05 16:45", 66863.5, 66940.2, 66820.2, 66849.2),
    ("04-05 17:00", 66849.2, 66885.8, 66783.1, 66879.4),
    ("04-05 17:15", 66879.3, 66938.0, 66858.2, 66910.5),
    ("04-05 17:30", 66910.5, 66916.9, 66871.0, 66892.5),
    ("04-05 17:45", 66892.6, 66939.7, 66792.6, 66906.4),
    ("04-05 18:00", 66906.5, 67521.7, 66906.4, 67478.2),
    ("04-05 18:15", 67478.2, 67828.6, 67271.8, 67410.8),
    ("04-05 18:30", 67410.8, 67428.0, 67240.0, 67272.2),
    ("04-05 18:45", 67272.2, 67366.8, 67241.7, 67269.3),
    ("04-05 19:00", 67269.4, 67359.4, 67269.3, 67287.8),
    ("04-05 19:15", 67287.8, 67381.0, 67230.7, 67291.8),
    ("04-05 19:30", 67291.7, 67291.8, 67170.1, 67194.1),
    ("04-05 19:45", 67291.7, 67291.8, 67170.1, 67203.6),
    ("04-05 23:15", 67352.5, 67477.9, 67344.7, 67450.1),
    ("04-05 23:30", 67450.0, 67681.6, 67436.2, 67524.4),
    ("04-05 23:45", 67524.4, 67647.3, 67511.3, 67636.7),
    ("04-06 00:00", 67636.7, 67636.8, 67390.4, 67499.2),
    ("04-06 00:15", 67499.2, 67518.5, 67377.2, 67453.7),
    ("04-06 00:30", 67453.8, 67499.0, 67394.8, 67469.5),
    ("04-06 00:45", 67469.6, 67672.9, 67446.9, 67519.5),
    ("04-06 01:00", 67519.5, 67771.4, 67439.5, 67500.0),
    ("04-06 01:15", 67500.1, 67575.5, 67313.6, 67406.4),
    ("04-06 01:30", 67406.3, 67968.8, 67384.7, 67937.4),
    ("04-06 01:45", 67937.4, 68347.9, 67929.6, 68313.0),
    ("04-06 02:00", 68313.0, 68580.0, 68232.0, 68577.9),
    ("04-06 02:15", 68577.9, 68950.2, 68571.6, 68772.1),
    ("04-06 02:30", 68772.0, 69108.0, 68761.9, 68923.7),
    ("04-06 02:45", 68923.8, 69027.3, 68869.9, 68997.9),
    ("04-06 03:00", 68997.9, 69583.0, 68997.9, 69205.2),
    ("04-06 03:15", 69205.2, 69319.8, 69050.0, 69150.8),
    ("04-06 03:30", 69150.9, 69415.0, 69074.8, 69282.5),
    ("04-06 03:45", 69282.5, 69313.2, 69030.0, 69051.9),
    ("04-06 04:00", 69051.9, 69103.1, 68810.1, 68816.1),
    ("04-06 04:15", 68816.2, 68960.0, 68803.7, 68950.9),
    ("04-06 04:30", 68950.9, 68950.9, 68765.1, 68772.1),
    ("04-06 04:45", 68772.1, 68847.0, 68761.0, 68782.9),
    ("04-06 05:00", 68782.9, 69300.0, 68740.2, 69089.6),
    ("04-06 05:15", 69089.5, 69282.8, 69071.5, 69198.4),
    ("04-06 05:30", 69198.5, 69386.2, 69155.0, 69186.9),
    ("04-06 05:45", 69187.0, 69276.1, 69174.9, 69183.6),
    ("04-06 06:00", 69183.6, 69223.4, 69074.9, 69099.6),
    ("04-06 06:15", 69099.6, 69177.6, 69030.0, 69151.4),
    ("04-06 06:30", 69151.4, 69206.0, 69037.8, 69092.8),
    ("04-06 06:45", 69092.8, 69117.0, 69026.6, 69092.4),
    ("04-06 07:00", 69092.3, 69172.4, 68966.0, 69039.0),
    ("04-06 07:15", 69039.0, 69044.9, 68943.3, 68971.7),
    ("04-06 07:30", 68971.7, 69188.0, 68967.0, 69147.1),
    ("04-06 07:45", 69147.0, 69180.0, 69093.0, 69107.6),
    ("04-06 08:00", 69107.6, 69150.0, 69082.1, 69129.2),
    ("04-06 08:15", 69129.3, 69188.9, 69052.0, 69139.1),
    ("04-06 08:30", 69139.1, 69214.5, 69132.6, 69189.8),
    ("04-06 08:45", 69189.7, 69209.7, 69118.4, 69167.1),
    ("04-06 09:00", 69167.0, 69338.2, 69063.2, 69276.7),
    ("04-06 09:15", 69276.6, 69276.7, 68769.6, 68813.9),
    ("04-06 09:30", 68813.9, 68948.9, 68805.0, 68904.3),
    ("04-06 09:45", 68904.3, 69079.5, 68895.3, 68958.7),
    ("04-06 10:00", 68958.8, 68966.0, 68800.0, 68873.9),
    ("04-06 10:15", 68873.9, 69078.4, 68873.9, 69048.2),
    ("04-06 10:30", 69048.3, 69117.2, 68945.9, 68955.4),
    ("04-06 10:45", 68955.4, 69190.8, 68922.9, 69089.7),
    ("04-06 11:00", 69089.8, 69197.7, 69047.7, 69144.0),
    ("04-06 11:15", 69144.1, 69225.0, 69090.5, 69199.8),
    ("04-06 11:30", 69199.9, 69199.9, 69175.6, 69175.7),
    ("04-06 20:00", 83100.0, 83150.0, 83050.0, 83120.0),
    ("04-07 00:45", 68749.5, 68872.0, 68703.0, 68738.7),
    ("04-07 01:00", 68738.6, 68738.7, 68500.0, 68554.9),
    ("04-07 01:15", 68554.9, 68878.3, 68554.9, 68692.6),
    ("04-07 01:30", 68692.6, 68773.3, 68547.7, 68599.5),
    ("04-07 01:45", 68599.5, 68615.3, 68291.0, 68363.9),
    ("04-07 02:00", 68363.9, 68467.0, 68241.9, 68390.6),
    ("04-07 02:15", 68390.7, 68549.1, 68380.4, 68543.6),
    ("04-07 02:30", 68543.5, 68684.6, 68467.5, 68586.0),
    ("04-07 02:45", 68586.0, 68663.6, 68518.0, 68640.3),
    ("04-07 03:00", 68640.3, 68720.0, 68586.5, 68645.0),
    ("04-07 03:15", 68645.0, 68768.9, 68622.3, 68745.0),
    ("04-07 03:30", 68745.0, 68780.0, 68696.1, 68764.0),
    ("04-07 03:45", 68763.9, 68767.5, 68704.0, 68746.3),
    ("04-07 04:00", 68746.4, 68755.0, 68592.1, 68637.6),
    ("04-07 04:15", 68637.5, 68652.9, 68510.5, 68572.5),
    ("04-07 04:30", 68572.4, 68846.0, 68572.4, 68822.0),
    ("04-07 04:45", 68822.0, 68955.6, 68794.6, 68819.3),
    ("04-07 05:00", 68819.2, 68831.0, 68756.1, 68770.0),
    ("04-07 05:15", 68770.0, 68805.7, 68648.7, 68670.0),
    ("04-07 05:30", 68669.9, 68720.8, 68604.0, 68614.9),
    ("04-07 05:45", 68614.8, 68661.4, 68577.6, 68627.5),
    ("04-07 06:00", 68627.4, 68635.9, 68450.0, 68490.0),
    ("04-07 06:15", 68489.9, 68557.9, 68400.6, 68539.1),
    ("04-07 06:30", 68539.1, 68552.4, 68450.0, 68524.0),
    ("04-07 06:45", 68523.9, 68579.5, 68468.9, 68540.0),
    ("04-07 07:00", 68539.9, 68546.9, 68470.0, 68526.9),
    ("04-07 07:15", 68526.8, 68630.5, 68470.0, 68546.3),
    ("04-07 07:30", 68546.3, 68677.8, 68546.3, 68645.1),
    ("04-07 07:45", 68645.0, 68650.0, 68569.7, 68592.1),
    ("04-07 08:00", 68592.0, 68813.5, 68570.7, 68697.1),
    ("04-07 08:15", 68697.0, 68830.3, 68626.7, 68725.1),
    ("04-07 08:30", 68725.1, 68921.6, 68725.1, 68886.9),
    ("04-07 08:45", 68886.8, 68963.4, 68859.7, 68907.1),
    ("04-07 09:00", 68907.1, 69218.3, 68900.0, 69070.1),
    ("04-07 09:15", 69070.2, 69120.0, 68958.9, 69025.9),
    ("04-07 09:30", 69026.0, 69219.0, 69013.8, 69146.1),
    ("04-07 09:45", 69146.0, 69167.7, 69077.4, 69109.8),
    ("04-07 10:00", 69109.9, 69170.0, 68776.2, 68877.1),
    ("04-07 10:15", 68877.1, 68976.0, 68627.0, 68704.0),
    ("04-07 10:30", 68703.9, 68745.6, 68405.2, 68440.1),
    ("04-07 10:45", 68440.1, 68451.0, 68151.8, 68196.0),
    ("04-07 11:00", 68196.1, 68313.4, 68033.0, 68309.3),
    ("04-07 11:15", 68309.4, 68383.5, 68222.0, 68336.9),
    ("04-07 11:30", 68336.8, 68430.1, 68250.0, 68375.0),
    ("04-07 11:45", 68374.9, 68400.0, 68284.8, 68310.8),
    ("04-07 12:00", 68310.7, 68444.0, 68039.8, 68243.0),
    ("04-07 12:15", 68243.0, 68433.7, 68168.0, 68396.9),
    ("04-07 12:30", 68396.9, 68442.6, 68251.5, 68293.5),
    ("04-07 12:45", 68293.6, 68579.3, 68207.9, 68367.0),
    ("04-07 13:00", 68366.9, 68613.8, 68343.3, 68600.0),
    ("04-07 13:15", 68600.0, 68608.0, 68430.0, 68455.9),
    ("04-07 13:30", 68455.9, 68571.8, 68260.8, 68309.5),
    ("04-07 13:45", 68309.6, 68438.7, 68168.0, 68208.1),
    ("04-07 14:00", 68208.1, 68232.1, 67780.0, 67865.1),
    ("04-07 14:15", 67865.1, 68141.0, 67741.0, 68127.5),
    ("04-08 04:45", 71573.7, 71644.5, 71506.1, 71528.6),
    ("04-08 05:00", 71528.6, 71643.9, 71516.3, 71633.0),
    ("04-08 05:15", 71633.1, 71750.0, 71590.6, 71680.2),
    ("04-08 05:30", 71680.3, 71734.5, 71625.4, 71668.2),
    ("04-08 05:45", 71668.2, 71797.0, 71607.9, 71701.6),
    ("04-08 06:00", 71701.5, 71828.0, 71539.2, 71772.1),
    ("04-08 06:15", 71772.2, 71919.0, 71702.7, 71821.4),
    ("04-08 06:30", 71821.3, 71829.8, 71726.9, 71779.0),
    ("04-08 06:45", 71779.0, 71790.0, 71679.2, 71697.5),
    ("04-08 07:00", 71697.4, 71770.1, 71600.0, 71729.8),
    ("04-08 07:15", 71729.7, 71873.7, 71670.1, 71780.0),
    ("04-08 07:30", 71780.0, 71780.1, 71586.0, 71618.3),
    ("04-08 07:45", 71618.2, 71620.8, 71551.8, 71612.0),
    ("04-08 08:00", 71612.1, 71790.9, 71612.0, 71681.3),
    ("04-08 08:15", 71681.3, 71780.0, 71658.3, 71724.0),
    ("04-08 08:30", 71724.0, 71808.5, 71615.7, 71705.8),
    ("04-08 08:45", 71705.8, 71776.2, 71669.3, 71776.0),
    ("04-08 09:00", 71776.0, 71945.0, 71775.9, 71790.0),
    ("04-08 09:15", 71790.1, 71850.0, 71650.0, 71650.1),
    ("04-08 09:30", 71650.1, 71719.4, 71560.0, 71560.8),
    ("04-08 09:45", 71560.8, 71683.0, 71555.3, 71655.4),
    ("04-08 10:00", 71655.4, 71782.1, 71554.0, 71575.6),
    ("04-08 10:15", 71575.6, 71651.6, 71560.0, 71615.6),
    ("04-08 10:30", 71615.6, 71624.2, 71415.3, 71519.4),
    ("04-08 10:45", 71519.4, 71550.0, 71439.4, 71445.7),
    ("04-08 11:00", 71445.7, 71636.1, 71415.4, 71604.8),
    ("04-08 11:15", 71604.8, 71640.0, 71492.5, 71620.1),
    ("04-08 11:30", 71620.1, 71623.7, 71367.0, 71481.5),
    ("04-08 11:45", 71481.4, 71687.6, 71448.0, 71650.2),
    ("04-08 12:00", 71650.2, 71824.6, 71645.1, 71805.9),
    ("04-08 12:15", 71805.9, 71820.0, 71542.6, 71733.2),
    ("04-08 12:30", 71733.1, 71935.9, 71700.0, 71906.8),
    ("04-08 12:45", 71906.8, 72169.5, 71858.5, 72023.6),
    ("04-08 13:00", 72023.6, 72800.0, 72023.6, 72590.4),

    ("04-10 04:30", 71835.5, 71881.5, 71781.9, 71872.7),
    ("04-10 04:45", 71872.7, 72199.9, 71856.3, 72088.8),
    ("04-10 05:00", 72088.8, 72137.7, 71973.8, 72030.1),
    ("04-10 05:15", 72030.0, 72243.6, 71986.5, 72189.9),
    ("04-10 05:30", 72189.9, 72234.1, 72110.8, 72126.4),
    ("04-10 05:45", 72126.4, 72190.6, 72054.7, 72098.6),
    ("04-10 06:00", 72098.4, 72154.8, 72025.0, 72109.0),
    ("04-10 06:15", 72109.1, 72109.1, 71907.3, 71932.0),
    ("04-10 06:30", 71932.0, 71982.2, 71834.1, 71908.0),
    ("04-10 06:45", 71908.1, 71962.2, 71759.0, 71778.1),
    ("04-10 07:00", 71778.1, 71821.1, 71675.3, 71684.7),
    ("04-10 07:15", 71684.8, 71750.0, 71667.0, 71692.5),
    ("04-10 07:30", 71692.4, 71763.8, 71618.0, 71633.7),
    ("04-10 07:45", 71633.6, 71666.3, 71382.1, 71461.2),
    ("04-10 08:00", 71461.2, 71645.1, 71395.0, 71577.9),
    ("04-10 08:15", 71577.9, 71666.0, 71484.7, 71611.0),
    ("04-10 08:30", 71611.1, 71730.0, 71583.9, 71672.7),
    ("04-10 08:45", 71672.7, 71681.8, 71460.1, 71571.6),
    ("04-10 09:00", 71571.6, 71665.0, 71555.8, 71664.6),
    ("04-10 09:15", 71664.5, 71818.5, 71649.8, 71730.6),
    ("04-10 09:30", 71730.7, 71840.8, 71715.9, 71774.2),
    ("04-10 09:45", 71774.1, 71800.0, 71701.1, 71746.2),
    ("04-10 10:00", 71746.1, 71780.0, 71674.7, 71779.9),
    ("04-10 10:15", 71780.0, 71780.0, 71658.8, 71696.9),
    ("04-10 10:30", 71697.0, 71788.0, 71688.9, 71768.8),
    ("04-10 10:45", 71768.7, 71910.0, 71739.6, 71872.4),
    ("04-10 11:00", 71872.5, 72133.7, 71861.5, 72085.0),
    ("04-10 11:15", 72085.0, 72194.0, 72058.0, 72175.2),
    ("04-10 11:30", 72175.2, 72229.0, 72091.4, 72145.9),
    ("04-10 11:45", 72145.9, 72214.0, 72054.0, 72092.7),
    ("04-10 12:00", 72092.8, 72182.4, 72044.1, 72050.5),
    ("04-10 12:15", 72050.6, 72294.9, 71960.5, 72134.7),
    ("04-10 12:30", 72134.6, 72467.3, 71999.2, 72277.6),
    ("04-10 12:45", 72277.7, 72372.2, 72155.7, 72225.5),

    ("04-10 13:00", 72225.4, 72236.1, 72150.0, 72175.7),
    ("04-10 13:15", 72175.7, 72260.0, 72118.1, 72260.0),
    ("04-10 13:30", 72260.0, 72381.0, 71868.5, 72034.0),
    ("04-10 13:45", 72033.9, 72340.9, 72019.7, 72284.0),
    ("04-10 14:00", 72283.9, 72735.1, 72209.8, 72667.3),
    ("04-10 14:15", 72667.3, 73050.0, 72590.9, 72933.0),
    ("04-10 14:30", 72933.0, 73123.9, 72660.7, 72819.1),
    ("04-10 14:45", 72819.2, 72925.0, 72649.0, 72870.6),
    ("04-10 15:00", 72870.6, 73084.0, 72784.8, 72978.3),
    ("04-10 15:15", 72978.0, 73255.7, 72700.0, 72740.5),
    ("04-10 15:30", 72740.4, 72806.3, 72537.7, 72703.9),
    ("04-10 15:45", 72703.9, 72723.9, 72309.5, 72421.0),
    ("04-10 16:00", 72421.1, 72676.4, 72350.0, 72661.2),
    ("04-10 16:15", 72661.2, 72798.6, 72522.5, 72730.1),
    ("04-10 16:30", 72730.2, 72767.3, 72528.5, 72683.1),
    ("04-10 16:45", 72683.2, 73024.1, 72663.8, 72954.0),

    ("04-12 16:45", 70838.7, 70898.0, 70777.0, 70890.9),
    ("04-12 17:00", 70890.8, 70968.0, 70856.0, 70856.0),
    ("04-12 17:15", 70855.8, 70968.9, 70853.1, 70955.0),
    ("04-12 17:30", 70955.0, 70983.0, 70910.0, 70977.8),
    ("04-12 17:45", 70977.8, 71188.0, 70889.0, 71099.9),
    ("04-12 18:00", 71100.0, 71138.0, 71010.0, 71136.0),
    ("04-12 18:15", 71135.9, 71177.3, 71022.8, 71047.2),
    ("04-12 18:30", 71047.2, 71160.0, 71047.2, 71076.3),
    ("04-12 18:45", 71076.2, 71120.0, 71064.0, 71092.6),
    ("04-12 19:00", 71092.5, 71199.0, 71090.1, 71100.0),
    ("04-12 19:15", 71100.0, 71130.5, 71083.6, 71125.0),
    ("04-12 19:30", 71125.1, 71130.1, 71042.8, 71071.9),
    ("04-12 19:45", 71072.0, 71090.2, 71034.6, 71055.2),
    ("04-12 20:00", 71055.2, 71073.6, 70953.0, 70982.2),
    ("04-12 20:15", 70982.2, 71040.0, 70920.4, 71024.7),
    ("04-12 20:30", 71024.6, 71417.9, 71024.6, 71284.0),
    ("04-12 20:45", 71284.0, 71348.0, 71186.9, 71302.9),
    ("04-12 21:00", 71302.8, 71423.9, 71110.3, 71179.2),
    ("04-12 21:15", 71179.1, 71286.9, 71179.1, 71268.8),
    ("04-12 21:30", 71268.9, 71319.6, 71184.8, 71277.8),
    ("04-12 21:45", 71277.8, 71334.4, 71172.0, 71331.7),
    ("04-12 22:00", 71331.4, 71332.4, 70661.3, 70922.9),
    ("04-12 22:15", 70922.9, 70953.8, 70522.0, 70636.4),
    ("04-12 22:30", 70636.4, 70900.0, 70458.2, 70784.9),
    ("04-12 22:45", 70784.9, 70905.9, 70749.9, 70875.6),
    ("04-12 23:00", 70875.5, 70882.4, 70588.8, 70588.8),
    ("04-12 23:15", 70588.8, 70731.2, 70561.4, 70684.4),
    ("04-12 23:30", 70684.3, 70707.9, 70533.0, 70702.2),
    ("04-12 23:45", 70702.2, 70762.6, 70552.8, 70711.1),
    ("04-13 00:00", 70711.2, 70887.3, 70574.0, 70884.1),
    ("04-13 00:15", 70884.1, 71062.0, 70796.6, 70935.4),
    ("04-13 00:30", 70935.4, 71093.6, 70907.9, 71023.5),
    ("04-13 00:45", 71023.6, 71225.0, 70978.1, 71130.0),
    ("04-13 01:00", 71129.9, 71193.6, 71066.4, 71099.6),

    ("04-15 02:15", 74494.3, 74550.0, 74298.2, 74311.3),
    ("04-15 02:30", 74311.4, 74318.3, 74142.7, 74240.2),
    ("04-15 02:45", 74240.2, 74321.6, 74149.6, 74280.0),
    ("04-15 03:00", 74280.0, 74286.2, 74171.0, 74181.7),
    ("04-15 03:15", 74181.7, 74338.9, 74123.6, 74250.0),
    ("04-15 03:30", 74250.0, 74300.0, 74162.0, 74197.3),
    ("04-15 03:45", 74197.2, 74333.0, 74181.3, 74296.8),
    ("04-15 04:00", 74296.8, 74400.0, 74295.0, 74302.2),
    ("04-15 04:15", 74302.1, 74363.3, 74255.1, 74273.5),
    ("04-15 04:30", 74273.5, 74368.7, 74225.5, 74296.9),
    ("04-15 04:45", 74296.9, 74310.0, 74211.3, 74290.8),
    ("04-15 05:00", 74290.7, 74390.0, 74154.3, 74160.5),
    ("04-15 05:15", 74160.6, 74199.2, 73960.1, 73975.2),
    ("04-15 05:30", 73975.3, 74000.0, 73822.6, 73916.6),
    ("04-15 05:45", 73916.5, 74010.3, 73862.8, 73983.2),
    ("04-15 06:00", 73983.1, 74015.7, 73888.0, 73909.2),
    ("04-15 06:15", 73909.3, 73988.8, 73874.2, 73882.4),
    ("04-15 06:30", 73882.4, 73973.3, 73859.0, 73969.5),
    ("04-15 06:45", 73969.5, 73986.5, 73822.0, 73851.1),
    ("04-15 07:00", 73851.0, 73987.0, 73788.0, 73872.3),
    ("04-15 07:15", 73872.3, 73872.4, 73550.0, 73676.0),
    ("04-15 07:30", 73676.1, 73681.1, 73530.1, 73562.6),
    ("04-15 07:45", 73562.6, 73752.9, 73449.0, 73705.1),
    ("04-15 08:00", 73705.2, 73826.8, 73640.1, 73815.7),
    ("04-15 08:15", 73815.8, 73963.3, 73800.8, 73959.7),
    ("04-15 08:30", 73959.7, 74130.0, 73931.6, 74060.0),
    ("04-15 08:45", 74059.9, 74154.3, 73991.7, 74070.4),
    ("04-15 09:00", 74070.4, 74143.5, 73920.2, 73989.3),
    ("04-15 09:15", 73989.2, 74047.2, 73886.0, 73914.6),
    ("04-15 09:30", 73914.7, 73977.6, 73868.0, 73929.3),
    ("04-15 09:45", 73929.3, 73998.8, 73884.0, 73968.3),
    ("04-15 10:00", 73968.3, 74142.7, 73941.3, 74071.1),
    ("04-15 10:15", 74071.1, 74075.6, 73840.4, 73865.4),
    ("04-15 10:30", 73865.4, 74017.0, 73750.0, 74017.0),

    ("04-15 10:45", 74017.0, 74222.7, 73777.4, 73825.9),
    ("04-15 11:00", 73825.9, 74056.2, 73825.9, 73987.9),
    ("04-15 11:15", 73987.9, 73987.9, 73881.3, 73920.0),

    ("04-16 00:45", 74727.2, 74812.0, 74647.0, 74772.0),
    ("04-16 01:00", 74772.1, 74772.1, 74415.0, 74530.7),
    ("04-16 01:15", 74530.7, 74650.0, 74478.4, 74569.9),
    ("04-16 01:30", 74569.9, 74665.9, 74531.6, 74646.5),
    ("04-16 01:45", 74646.5, 74676.3, 74520.0, 74612.8),
    ("04-16 02:00", 74612.8, 74720.9, 74556.7, 74631.5),
    ("04-16 02:15", 74631.5, 74888.0, 74569.4, 74855.9),
    ("04-16 02:30", 74855.8, 75199.7, 74855.8, 75150.0),
    ("04-16 02:45", 75150.1, 75232.7, 74763.7, 74840.8),
    ("04-16 03:00", 74840.7, 75096.2, 74830.0, 74906.0),
    ("04-16 03:15", 74906.1, 75123.5, 74906.0, 75000.0),
    ("04-16 03:30", 75000.0, 75012.5, 74907.0, 74932.6),
    ("04-16 03:45", 74932.5, 74946.4, 74825.1, 74851.9),
    ("04-16 04:00", 74851.9, 74974.0, 74800.0, 74900.0),
    ("04-16 04:15", 74900.0, 74935.8, 74839.9, 74886.4),
    ("04-16 04:30", 74886.3, 75130.0, 74830.2, 75058.8),
    ("04-16 04:45", 75058.8, 75058.8, 74675.4, 74899.9),
    ("04-16 05:00", 74900.0, 74970.1, 74855.5, 74876.4),
    ("04-16 05:15", 74876.3, 75075.0, 74852.4, 75027.8),
    ("04-16 05:30", 75027.8, 75100.0, 74968.9, 75016.8),
    ("04-16 05:45", 75016.8, 75031.3, 74966.3, 75006.1),
    ("04-16 06:00", 75006.0, 75079.1, 74961.0, 74973.1),
    ("04-16 06:15", 74973.1, 75045.0, 74961.1, 74979.1),
    ("04-16 06:30", 74979.1, 74997.7, 74801.8, 74907.2),
    ("04-16 06:45", 74907.3, 74999.9, 74865.0, 74985.9),
    ("04-16 07:00", 74985.9, 75039.0, 74847.0, 74872.8),
    ("04-16 07:15", 74872.8, 74905.4, 74808.9, 74863.0),
    ("04-16 07:30", 74863.0, 74869.4, 74800.0, 74821.8),
    ("04-16 07:45", 74821.7, 74824.4, 74590.3, 74667.7),
    ("04-16 08:00", 74667.7, 74711.8, 74466.9, 74490.5),
    ("04-16 08:15", 74490.5, 74696.3, 74473.7, 74647.7),
    ("04-16 08:30", 74647.8, 74696.4, 74514.1, 74638.2),
    ("04-16 08:45", 74638.3, 74706.9, 74605.4, 74634.3),
    ("04-16 09:00", 74634.2, 74720.0, 74592.5, 74704.9),

    ("04-18 04:15", 77031.8, 77031.8, 76888.0, 76943.3),
    ("04-18 04:30", 76943.3, 77037.4, 76824.1, 76939.6),
    ("04-18 04:45", 76939.6, 77131.8, 76939.6, 77065.9),
    ("04-18 05:00", 77065.8, 77233.6, 77063.5, 77159.2),
    ("04-18 05:15", 77159.3, 77177.0, 77091.1, 77108.1),
    ("04-18 05:30", 77108.0, 77150.0, 77063.7, 77107.4),
    ("04-18 05:45", 77107.4, 77107.5, 77073.2, 77085.0),
    ("04-18 06:00", 77085.1, 77177.0, 77053.2, 77123.0),
    ("04-18 06:15", 77122.9, 77142.1, 77008.0, 77041.6),
    ("04-18 06:30", 77041.7, 77100.0, 77035.2, 77097.7),
    ("04-18 06:45", 77097.7, 77118.7, 77059.6, 77078.7),
    ("04-18 07:00", 77078.7, 77086.5, 77020.2, 77028.4),
    ("04-18 07:15", 77028.4, 77064.1, 77000.0, 77049.4),
    ("04-18 07:30", 77049.3, 77054.6, 76925.5, 76996.2),
    ("04-18 07:45", 76996.2, 76996.2, 76826.8, 76951.0),
    ("04-18 08:00", 76951.0, 77004.2, 76744.0, 76761.5),
    ("04-18 08:15", 76761.5, 76820.0, 76584.7, 76644.7),
    ("04-18 08:30", 76644.7, 76729.0, 76460.0, 76515.0),
    ("04-18 08:45", 76515.1, 76755.4, 76500.0, 76695.1),
    ("04-18 09:00", 76695.1, 76695.1, 76400.0, 76501.8),
    ("04-18 09:15", 76501.7, 76543.4, 76357.1, 76538.9),
    ("04-18 09:30", 76538.8, 76630.3, 76513.4, 76589.1),
    ("04-18 09:45", 76589.1, 76663.2, 76487.8, 76557.1),
    ("04-18 10:00", 76557.1, 76557.2, 76166.0, 76250.0),
    ("04-18 10:15", 76249.9, 76354.8, 76235.4, 76287.4),
    ("04-18 10:30", 76287.4, 76287.4, 76179.9, 76189.9),
    ("04-18 10:45", 76189.9, 76258.0, 76091.8, 76150.0),
    ("04-18 11:00", 76150.0, 76150.0, 75870.0, 75905.0),
    ("04-18 11:15", 75905.0, 76061.8, 75883.6, 76034.5),
    ("04-18 11:30", 76034.5, 76135.8, 75710.6, 75803.9),
    ("04-18 11:45", 75804.0, 76065.0, 75750.0, 76002.0),
    ("04-18 12:00", 76002.0, 76194.3, 76000.0, 76161.7),
    ("04-18 12:15", 76161.6, 76277.4, 76085.0, 76100.1),
    ("04-18 12:30", 76100.1, 76181.5, 76000.0, 76140.6),

    ("04-18 12:45", 76140.5, 76243.0, 76138.3, 76168.0),
    ("04-18 13:00", 76168.0, 76176.0, 76090.2, 76119.1),
    ("04-18 13:15", 76119.1, 76175.0, 76012.3, 76046.1),
    ("04-18 13:30", 76046.1, 76059.2, 75738.0, 75908.8),
    ("04-18 13:45", 75908.7, 76145.7, 75860.0, 76080.5),
    ("04-18 14:00", 76080.5, 76135.0, 76034.7, 76132.4),
    ("04-18 14:15", 76132.4, 76150.0, 75924.4, 76101.1),
    ("04-18 14:30", 76101.0, 76268.2, 76101.0, 76152.8),
    ("04-18 14:45", 76152.8, 76223.0, 76123.0, 76211.2),
    ("04-18 15:00", 76211.2, 76342.7, 76085.4, 76177.8),
    ("04-18 15:15", 76177.8, 76237.6, 76100.4, 76164.9),
    ("04-18 15:30", 76164.9, 76195.4, 76086.5, 76086.5),
    ("04-18 15:45", 76086.5, 76158.0, 75931.9, 76124.8),
    ("04-18 16:00", 76124.8, 76176.6, 75983.8, 76144.0),
    ("04-18 16:15", 76144.1, 76144.1, 75584.1, 76041.2),
    ("04-18 16:30", 76041.2, 76088.6, 75940.3, 75943.1),
    ("04-18 16:45", 75943.0, 75976.4, 75807.1, 75897.9),
    ("04-18 17:00", 75897.9, 75930.5, 75724.8, 75781.9),
    ("04-18 17:15", 75781.9, 75843.3, 75741.9, 75809.3),
    ("04-18 17:30", 75809.3, 75843.3, 75806.1, 75829.7),
    ("04-18 17:45", 75829.7, 75843.3, 75783.8, 75783.9),
    ("04-18 18:00", 75783.9, 75805.1, 75629.3, 75756.1),
    ("04-18 18:15", 75756.0, 75756.1, 75550.0, 75618.3),
    ("04-18 18:30", 75618.3, 75638.5, 75395.9, 75528.7),

    ("04-18 18:45", 75528.8, 75697.4, 75490.0, 75603.7),
    ("04-18 19:00", 75603.7, 75760.8, 75574.5, 75705.5),

    ("04-19 00:00", 75653.8, 75804.0, 75640.0, 75734.6),
    ("04-19 00:15", 75734.6, 75734.7, 75519.7, 75570.0),
    ("04-19 00:30", 75570.0, 75605.3, 75506.1, 75536.1),
    ("04-19 00:45", 75536.1, 75648.9, 75530.7, 75627.3),
    ("04-19 01:00", 75627.4, 75757.7, 75574.5, 75636.1),
    ("04-19 01:15", 75636.0, 75636.0, 75500.0, 75500.1),
    ("04-19 01:30", 75500.0, 75544.0, 75408.5, 75512.0),
    ("04-19 01:45", 75512.1, 75605.9, 75512.0, 75577.4),
    ("04-19 02:00", 75577.4, 75604.2, 75538.0, 75592.7),
    ("04-19 02:15", 75592.7, 75650.0, 75353.0, 75449.8),
    ("04-19 02:30", 75449.8, 75692.3, 75400.6, 75606.9),
    ("04-19 02:45", 75606.9, 75647.5, 75450.0, 75450.1),
    ("04-19 03:00", 75450.0, 75505.9, 75314.0, 75496.1),
    ("04-19 03:15", 75496.0, 75523.1, 75418.9, 75485.7),
    ("04-19 03:30", 75485.7, 75582.6, 75444.2, 75564.4),
    ("04-19 03:45", 75564.5, 75607.9, 75465.8, 75473.0),
    ("04-19 04:00", 75472.9, 75700.0, 75471.5, 75657.9),
    ("04-19 04:15", 75657.9, 75747.3, 75619.4, 75640.6),
    ("04-19 04:30", 75640.6, 75640.6, 75371.6, 75499.0),
    ("04-19 04:45", 75499.1, 75675.6, 75457.9, 75623.7),
    ("04-19 05:00", 75623.7, 75650.0, 75481.8, 75506.9),
    ("04-19 05:15", 75506.8, 75509.5, 75466.3, 75509.5),
    ("04-19 05:30", 75509.5, 75629.7, 75509.4, 75554.9),
    ("04-19 05:45", 75555.0, 75555.0, 75490.0, 75505.1),
    ("04-19 06:00", 75505.1, 75505.1, 75350.0, 75350.1),
    ("04-19 06:15", 75350.1, 75404.1, 75234.2, 75364.5),
    ("04-19 06:30", 75364.5, 75445.9, 75364.4, 75387.4),
    ("04-19 06:45", 75387.5, 75390.7, 75315.1, 75359.7),
    ("04-19 07:00", 75359.6, 75363.2, 75168.0, 75194.7),
    ("04-19 07:15", 75194.8, 75194.8, 74824.3, 74930.3),
    ("04-19 07:30", 74930.5, 75188.4, 74930.4, 75134.5),
    ("04-19 07:45", 75134.4, 75250.0, 75095.8, 75205.6),
    ("04-19 08:00", 75205.7, 75240.0, 75130.0, 75220.6),
    ("04-19 08:15", 75220.6, 75250.0, 75090.0, 75090.3),

    ("04-19 08:30", 75090.3, 75213.7, 75024.3, 75186.3),

    ("04-19 08:45", 75186.3, 75230.7, 75130.0, 75220.0),
    ("04-19 09:00", 75220.1, 75232.1, 75125.0, 75131.2),
    ("04-19 09:15", 75131.3, 75150.0, 74901.2, 75048.0),
    ("04-19 09:30", 75048.0, 75126.1, 75001.0, 75020.0),
    ("04-19 09:45", 75020.0, 75020.1, 74863.6, 74974.6),
    ("04-19 10:00", 74974.6, 75051.9, 74888.0, 74994.2),
    ("04-19 10:15", 74994.4, 75081.2, 74951.1, 75044.6),
    ("04-19 10:30", 75044.5, 75064.8, 75010.3, 75050.8),
    ("04-19 10:45", 75050.9, 75199.0, 75007.6, 75175.5),
    ("04-19 11:00", 75175.5, 75418.4, 75170.0, 75383.6),
    ("04-19 11:15", 75383.6, 75513.6, 75295.0, 75331.5),
    ("04-19 11:30", 75331.5, 75490.4, 75329.4, 75472.9),
    ("04-19 11:45", 75473.0, 75589.2, 75450.0, 75557.4),
    ("04-19 12:00", 75557.5, 75647.2, 75452.2, 75636.2),

    ("04-19 12:15", 75636.2, 75665.7, 75455.8, 75474.6),

    ("04-19 12:30", 75474.7, 75500.0, 75386.4, 75457.8),
    ("04-19 12:45", 75457.8, 75642.4, 75417.8, 75529.3),
    ("04-19 13:00", 75529.2, 75741.1, 75505.1, 75719.7),
    ("04-19 13:15", 75719.7, 76200.0, 75679.0, 75999.0),
    ("04-19 13:30", 75999.0, 76066.0, 75883.1, 75988.6),
    ("04-19 13:45", 75988.7, 75988.7, 75808.0, 75877.9),
    ("04-19 14:00", 75878.0, 75974.9, 75625.9, 75748.9),
    ("04-19 14:15", 75749.0, 75987.0, 75710.1, 75916.8),
    ("04-19 14:30", 75916.8, 75944.9, 75740.8, 75935.3),
    ("04-19 14:45", 75935.3, 76100.0, 75893.7, 75971.3),

    ("04-19 15:00", 75971.4, 75997.0, 75821.6, 75960.0),

    ("04-19 15:15", 75960.0, 76116.8, 75834.9, 75917.3),
    ("04-19 15:30", 75917.4, 75943.6, 75342.3, 75676.3),
    ("04-19 15:45", 75676.3, 75840.0, 75643.5, 75807.6),
    ("04-19 16:00", 75807.7, 75817.7, 75562.9, 75624.8),
    ("04-19 16:15", 75624.8, 75720.5, 75505.0, 75526.2),
    ("04-19 16:30", 75526.1, 75666.0, 75460.0, 75522.0),
    ("04-19 16:45", 75522.1, 75599.5, 75255.7, 75345.6),
    ("04-19 17:00", 75345.5, 75348.4, 74938.9, 75220.6),

    ("04-19 17:15", 75220.6, 75337.4, 75107.1, 75228.6),
    ("04-19 17:30", 75228.6, 75323.5, 75033.3, 75140.0),
    ("04-19 17:45", 75140.0, 75176.5, 74560.0, 74742.4),

    ("04-19 18:00", 74742.3, 74876.9, 74616.6, 74799.0),
    ("04-19 18:15", 74798.9, 74837.9, 74550.0, 74772.2),
    ("04-19 18:30", 74772.1, 74781.2, 74610.2, 74669.5),
    ("04-19 18:45", 74669.4, 74766.8, 74568.7, 74736.2),
    ("04-19 19:00", 74736.2, 74947.3, 74736.2, 74906.4),
    ("04-19 19:15", 74906.4, 74988.0, 74803.9, 74908.9),
    ("04-19 19:30", 74908.9, 75043.1, 74888.2, 74922.2),
    ("04-19 19:45", 74922.2, 74990.9, 74852.0, 74917.9),
    ("04-19 20:00", 74918.0, 74920.2, 74657.4, 74768.7),
    ("04-19 20:15", 74768.8, 74768.8, 74599.0, 74720.8),
    ("04-19 20:30", 74720.7, 74831.8, 74413.0, 74490.0),
    ("04-19 20:45", 74490.0, 74695.6, 74375.0, 74591.6),
    ("04-19 21:00", 74591.7, 74705.8, 74526.9, 74650.0),
    ("04-19 21:15", 74650.1, 74736.3, 74533.1, 74707.5),
    ("04-19 21:30", 74707.5, 74776.3, 74681.0, 74701.3),
    ("04-19 21:45", 74701.2, 74760.4, 74304.5, 74379.5),
    ("04-19 22:00", 74379.4, 74379.5, 73750.1, 73986.1),
    ("04-19 22:15", 73986.1, 74034.3, 73700.2, 73912.1),
    ("04-19 22:30", 73912.0, 74143.1, 73884.1, 74102.1),
    ("04-19 22:45", 74102.1, 74166.0, 73978.7, 74005.0),
    ("04-19 23:00", 74005.0, 74018.6, 73780.0, 73987.9),
    ("04-19 23:15", 73987.9, 73987.9, 73750.0, 73847.9),
    ("04-19 23:30", 73847.9, 73926.5, 73767.7, 73862.2),
    ("04-19 23:45", 73862.3, 73948.7, 73746.4, 73758.4),
    ("04-20 00:00", 73758.4, 74200.0, 73669.0, 73994.7),
    ("04-20 00:15", 73994.7, 74239.9, 73994.6, 74186.4),
    ("04-20 00:30", 74186.5, 74229.9, 74100.0, 74130.6),
    ("04-20 00:45", 74130.6, 74322.9, 74120.2, 74228.1),
    ("04-20 01:00", 74228.1, 74322.0, 74190.0, 74321.8),
    ("04-20 01:15", 74321.8, 74328.0, 74167.6, 74253.2),

    ("04-20 06:15", 74265.0, 74370.0, 74206.7, 74300.1),
    ("04-20 06:30", 74300.1, 74860.0, 74300.1, 74739.9),
    ("04-20 06:45", 74740.0, 74799.2, 74612.1, 74751.1),
    ("04-20 07:00", 74751.2, 74829.1, 74650.0, 74761.3),
    ("04-20 07:15", 74761.4, 75539.3, 74681.7, 75175.9),
    ("04-20 07:30", 75175.9, 75209.7, 74802.6, 74898.3),
    ("04-20 07:45", 74898.4, 74977.9, 74618.0, 74795.5),
    ("04-20 08:00", 74795.5, 74837.7, 74614.6, 74791.9),
    ("04-20 08:15", 74792.0, 74970.5, 74665.7, 74783.4),
    ("04-20 08:30", 74783.3, 74900.1, 74710.5, 74790.6),
    ("04-20 08:45", 74790.6, 74829.2, 74563.2, 74691.7),
    ("04-20 09:00", 74691.7, 75042.8, 74660.8, 74996.5),
    ("04-20 09:15", 74996.5, 75120.0, 74950.8, 74989.0),
    ("04-20 09:30", 74989.0, 75165.2, 74934.2, 75120.9),
    ("04-20 09:45", 75120.9, 75200.0, 74980.0, 75028.8),
    ("04-20 10:00", 75028.9, 75330.9, 75028.9, 75301.1),
    ("04-20 10:15", 75301.1, 75375.1, 75215.3, 75265.9),
    ("04-20 10:30", 75266.0, 75266.0, 75108.6, 75136.6),
    ("04-20 10:45", 75136.6, 75157.6, 74964.8, 74993.2),
    ("04-20 11:00", 74993.3, 75150.2, 74907.1, 75132.0),
    ("04-20 11:15", 75132.0, 75237.9, 75012.7, 75123.2),
    ("04-20 11:30", 75123.1, 75243.0, 75032.3, 75175.9),
    ("04-20 11:45", 75175.9, 75238.3, 75105.0, 75148.7),
    ("04-20 12:00", 75148.8, 75359.0, 75031.9, 75305.1),
    ("04-20 12:15", 75305.1, 75633.0, 75249.5, 75368.9),
    ("04-20 12:30", 75369.0, 75420.1, 74939.1, 75169.5),
    ("04-20 12:45", 75169.5, 75343.6, 75169.5, 75245.0),
    ("04-20 13:00", 75245.1, 75320.8, 75077.0, 75182.3),
    ("04-20 13:15", 75182.3, 75233.4, 74951.6, 75155.0),
    ("04-20 13:30", 75155.0, 75392.0, 74811.7, 75184.4),
    ("04-20 13:45", 75184.4, 75285.0, 74932.2, 75232.8),
    ("04-20 14:00", 75232.7, 75274.3, 74990.0, 75037.0),
    ("04-20 14:15", 75037.0, 75734.0, 74997.0, 75531.4),
    ("04-20 14:30", 75531.5, 75648.4, 75154.1, 75291.0),

    ("04-20 14:45", 75291.0, 75405.0, 74873.1, 75000.1),
    ("04-20 15:00", 75000.1, 75045.8, 74639.5, 75024.7),
    ("04-20 15:15", 75024.8, 75750.0, 75003.0, 75708.0),
    ("04-20 15:30", 75708.0, 75708.1, 75468.9, 75541.4),
    ("04-20 15:45", 75541.5, 75699.7, 75490.3, 75668.1),
    ("04-20 16:00", 75668.1, 75676.3, 75360.0, 75376.8),
    ("04-20 16:15", 75376.8, 75483.3, 75280.8, 75318.7),
    ("04-20 16:30", 75318.8, 75533.9, 75260.0, 75443.3),
    ("04-20 16:45", 75443.2, 75525.8, 75250.0, 75300.0),
    ("04-20 17:00", 75300.0, 75645.8, 75242.5, 75595.2),
    ("04-20 17:15", 75595.2, 75839.0, 75551.2, 75668.6),
    ("04-20 17:30", 75668.6, 75800.0, 75553.0, 75707.4),
    ("04-20 17:45", 75707.5, 75975.4, 75642.5, 75853.7),
    ("04-20 18:00", 75853.7, 76282.5, 75853.7, 76237.3),
    ("04-20 18:15", 76237.4, 76280.0, 76038.5, 76065.4),
    ("04-20 18:30", 76065.5, 76250.0, 75942.4, 76125.6),
    ("04-20 18:45", 76125.7, 76439.0, 76050.0, 76388.8),
    ("04-20 19:00", 76389.3, 76449.8, 76255.0, 76299.5),
    ("04-20 19:15", 76299.6, 76299.6, 76130.0, 76159.0),
    ("04-20 19:30", 76159.0, 76217.2, 76105.6, 76200.0),
    ("04-20 19:45", 76199.9, 76285.7, 76165.6, 76252.5),

    ("04-20 20:00", 76252.5, 76324.4, 76072.9, 76292.4),
    ("04-20 20:15", 76292.3, 76531.0, 76248.3, 76273.6),

    ("04-20 20:30", 76273.7, 76273.7, 76161.8, 76200.0),

    ("04-20 20:45", 76199.9, 76283.6, 76199.9, 76229.9),

    ("04-20 21:00", 76230.0, 76323.9, 75798.4, 75956.9),

    ("04-21 03:00", 75540.0, 75594.7, 75433.1, 75520.1),
    ("04-21 03:15", 75520.1, 75623.9, 75453.8, 75589.7),
    ("04-21 03:30", 75589.6, 75674.9, 75447.7, 75514.1),
    ("04-21 03:45", 75514.2, 75680.0, 75508.0, 75669.1),
    ("04-21 04:00", 75669.1, 75737.1, 75569.0, 75569.0),
    ("04-21 04:15", 75569.0, 75678.9, 75558.8, 75593.5),
    ("04-21 04:30", 75593.5, 75696.1, 75581.8, 75682.5),
    ("04-21 04:45", 75682.6, 75790.3, 75639.6, 75768.3),
    ("04-21 05:00", 75768.2, 75939.9, 75758.1, 75857.0),
    ("04-21 05:15", 75856.9, 75947.1, 75785.4, 75859.6),
    ("04-21 05:30", 75859.6, 75859.6, 75780.5, 75802.6),
    ("04-21 05:45", 75802.6, 75802.6, 75732.3, 75760.8),
    ("04-21 06:00", 75760.7, 75772.9, 75680.0, 75738.2),
    ("04-21 06:15", 75738.2, 75760.0, 75658.3, 75714.8),
    ("04-21 06:30", 75714.8, 76088.0, 75714.8, 75955.5),
    ("04-21 06:45", 75955.5, 76000.0, 75922.8, 75930.5),
    ("04-21 07:00", 75930.4, 75943.2, 75770.0, 75911.2),
    ("04-21 07:15", 75911.3, 76276.4, 75887.2, 76139.4),
    ("04-21 07:30", 76139.3, 76272.4, 75981.0, 76154.9),
    ("04-21 07:45", 76155.0, 76276.6, 76043.9, 76050.0),
    ("04-21 08:00", 76050.0, 76179.2, 76025.0, 76091.3),
    ("04-21 08:15", 76091.3, 76341.0, 76074.0, 76302.6),
    ("04-21 08:30", 76302.6, 76460.0, 76203.7, 76411.0),
    ("04-21 08:45", 76411.1, 76999.0, 76376.8, 76462.4),
    ("04-21 09:00", 76462.4, 76565.2, 76304.7, 76433.7),
    ("04-21 09:15", 76433.6, 76492.0, 76138.9, 76204.1),
    ("04-21 09:30", 76204.1, 76285.3, 76103.3, 76266.9),
    ("04-21 09:45", 76267.0, 76349.9, 76200.0, 76324.2),
    ("04-21 10:00", 76324.2, 76467.6, 76306.3, 76394.6),
    ("04-21 10:15", 76394.5, 76533.0, 76325.0, 76468.9),
    ("04-21 10:30", 76468.9, 76565.0, 76421.4, 76521.7),
    ("04-21 10:45", 76521.6, 76844.5, 76503.7, 76702.1),
    ("04-21 11:00", 76702.2, 76716.7, 76281.1, 76357.5),
    ("04-21 11:15", 76357.5, 76689.2, 76291.9, 76629.0),

    ("04-21 11:30", 76629.0, 76650.0, 76420.0, 76437.8),
    ("04-21 11:45", 76437.8, 76458.3, 76360.2, 76408.3),
    ("04-21 12:00", 76408.3, 76455.4, 76207.5, 76212.8),

    ("04-21 12:15", 76212.9, 76349.2, 76200.0, 76335.2),
    ("04-21 12:30", 76335.1, 76491.1, 75631.2, 75783.4),
    ("04-21 12:45", 75783.4, 76025.0, 75689.5, 75972.8),

    ("04-21 13:00", 75972.9, 76043.6, 75854.4, 75947.6),

    ("04-21 13:15", 75947.7, 76095.9, 75923.6, 75986.9),
    ("04-21 13:30", 75986.9, 76144.0, 75688.0, 75961.7),
    ("04-21 13:45", 75961.7, 76014.7, 75722.8, 75859.9),
    ("04-21 14:00", 75860.0, 75885.0, 75650.0, 75794.9),
    ("04-21 14:15", 75795.0, 76305.9, 75795.0, 76075.1),
    ("04-21 14:30", 76075.2, 76574.3, 76065.6, 76425.6),
    ("04-21 14:45", 76425.7, 76439.2, 75571.7, 75628.9),
    ("04-21 15:00", 75628.9, 75818.1, 75355.2, 75731.7),
    ("04-21 15:15", 75731.7, 75950.2, 75554.5, 75653.6),
    ("04-21 15:30", 75653.7, 75785.7, 75485.0, 75659.1),
    ("04-21 15:45", 75659.1, 75800.0, 75580.0, 75799.9),
    ("04-21 16:00", 75800.0, 75970.0, 75779.8, 75924.8),
    ("04-21 16:15", 75924.8, 75950.0, 75799.9, 75828.8),
    ("04-21 16:30", 75828.8, 76155.0, 75801.3, 75853.8),
    ("04-21 16:45", 75853.9, 76012.6, 75705.4, 75739.2),
    ("04-21 17:00", 75739.3, 75788.2, 75400.0, 75507.2),
    ("04-21 17:15", 75507.1, 75516.2, 75017.8, 75291.2),
    ("04-21 17:30", 75291.3, 75875.1, 75236.9, 75725.3),
    ("04-21 17:45", 75725.1, 75801.1, 75463.3, 75516.0),
    ("04-21 18:00", 75515.9, 75607.7, 75452.6, 75550.5),
    ("04-21 18:15", 75550.5, 75639.6, 75330.6, 75431.2),
    ("04-21 18:30", 75431.3, 75566.5, 75427.2, 75489.5),
    ("04-21 18:45", 75489.5, 75609.2, 75273.0, 75563.1),

    ("04-21 19:00", 75563.1, 75760.0, 75526.6, 75571.0),
    ("04-21 19:15", 75571.0, 75900.0, 75500.0, 75741.0),
    ("04-21 19:30", 75741.0, 75750.0, 74777.9, 74824.7),

    ("04-21 19:45", 74824.8, 75065.0, 74781.0, 74988.6),
    ("04-21 20:00", 74988.7, 75600.0, 74942.2, 75534.4),

    ("04-22 02:00", 76267.4, 76850.0, 76183.7, 76696.3),
    ("04-22 02:15", 76696.4, 77234.6, 76696.3, 77195.8),
    ("04-22 02:30", 77195.8, 77318.1, 77033.5, 77211.5),
    ("04-22 02:45", 77211.5, 77613.0, 77104.2, 77568.1),
    ("04-22 03:00", 77568.0, 77699.0, 77417.3, 77571.3),
    ("04-22 03:15", 77571.4, 77575.2, 77376.4, 77488.5),
    ("04-22 03:30", 77488.4, 77547.0, 77366.0, 77544.9),
    ("04-22 03:45", 77544.8, 77596.8, 77460.0, 77488.3),
    ("04-22 04:00", 77488.4, 77590.2, 77428.8, 77449.5),
    ("04-22 04:15", 77449.5, 77481.3, 77321.7, 77470.0),
    ("04-22 04:30", 77469.9, 77670.8, 77434.9, 77520.8),
    ("04-22 04:45", 77520.8, 77550.0, 77405.1, 77475.5),
    ("04-22 05:00", 77475.4, 77555.6, 77406.0, 77503.3),
    ("04-22 05:15", 77503.3, 78447.5, 77484.5, 78226.3),
    ("04-22 05:30", 78226.3, 78335.7, 77970.0, 78097.2),
    ("04-22 05:45", 78097.3, 78200.1, 77928.6, 77954.4),
    ("04-22 06:00", 77954.4, 77982.3, 77873.4, 77918.4),
    ("04-22 06:15", 77918.3, 78008.8, 77883.3, 77939.9),
    ("04-22 06:30", 77939.9, 77982.5, 77860.0, 77935.3),
    ("04-22 06:45", 77935.4, 77990.1, 77890.0, 77971.6),
    ("04-22 07:00", 77971.5, 78098.0, 77931.0, 78064.6),
    ("04-22 07:15", 78064.6, 78070.5, 77774.3, 77855.1),
    ("04-22 07:30", 77855.1, 78034.5, 77805.6, 78032.5),
    ("04-22 07:45", 78032.5, 78080.0, 77939.9, 77979.8),
    ("04-22 08:00", 77979.7, 78140.5, 77979.7, 78109.3),
    ("04-22 08:15", 78109.3, 78186.0, 77930.0, 77931.7),
    ("04-22 08:30", 77931.7, 77995.1, 77895.4, 77897.2),
    ("04-22 08:45", 77897.1, 78037.9, 77895.3, 77970.0),
    ("04-22 09:00", 77970.0, 78061.0, 77912.1, 78004.8),
    ("04-22 09:15", 78004.8, 78127.4, 77920.9, 78119.2),
    ("04-22 09:30", 78119.3, 78152.8, 78013.6, 78108.9),
    ("04-22 09:45", 78108.9, 78108.9, 77935.1, 77959.9),
    ("04-22 10:00", 77959.9, 78021.3, 77908.6, 77999.9),
    ("04-22 10:15", 78000.0, 78037.7, 77934.3, 78027.4),

    ("04-22 10:30", 78027.4, 78151.0, 78025.3, 78087.1),

    ("04-22 10:45", 78087.1, 78132.8, 78040.0, 78117.8),
    ("04-22 11:00", 78117.8, 78254.4, 78054.5, 78114.2),
    ("04-22 11:15", 78114.3, 78280.0, 78114.2, 78280.0),
    ("04-22 11:30", 78280.0, 78365.8, 78122.9, 78178.1),

    ("04-22 11:45", 78178.1, 78289.2, 78178.0, 78263.2),

    ("04-22 12:00", 78263.2, 78424.1, 78183.6, 78380.1),
    ("04-22 12:15", 78380.0, 78490.8, 78105.8, 78142.7),
    ("04-22 12:30", 78142.8, 78240.6, 78060.0, 78151.1),
    ("04-22 12:45", 78151.0, 78298.3, 78137.2, 78196.6),
    ("04-22 13:00", 78196.6, 78413.3, 78120.1, 78335.2),
    ("04-22 13:15", 78335.2, 78462.2, 78306.3, 78426.8),
    ("04-22 13:30", 78426.9, 78654.0, 78232.9, 78564.8),
    ("04-22 13:45", 78564.9, 78799.0, 78466.2, 78794.5),

    ("04-22 14:00", 78794.4, 79052.9, 78639.3, 79018.1),
    ("04-22 14:15", 79018.0, 79142.8, 78720.4, 78958.3),
    ("04-22 14:30", 78958.4, 78992.9, 78511.1, 78655.1),
    ("04-22 14:45", 78655.1, 79056.0, 78645.9, 78996.8),
    ("04-22 15:00", 78996.7, 79095.5, 78811.2, 78916.5),
    ("04-22 15:15", 78916.5, 79100.0, 78800.3, 79028.4),

    ("04-22 15:30", 79028.4, 79293.1, 78966.0, 79240.8),
    ("04-22 15:45", 79240.9, 79370.0, 79176.1, 79234.3),
    ("04-22 16:00", 79234.3, 79444.0, 79099.4, 79157.2),
    ("04-22 16:15", 79157.1, 79166.6, 78838.8, 78888.3),
    ("04-22 16:30", 78888.2, 78993.6, 78732.2, 78778.3),
    ("04-22 16:45", 78778.3, 78819.9, 78586.7, 78705.1),
    ("04-22 17:00", 78705.1, 78998.6, 78705.0, 78937.8),

    ("04-22 17:15", 78937.8, 78966.1, 78660.0, 78797.7),
    ("04-22 17:30", 78797.8, 78858.0, 78718.0, 78774.6),

    ("04-22 17:45", 78774.6, 78961.2, 78666.0, 78869.8),
    ("04-22 18:00", 78869.8, 78959.0, 78783.7, 78919.1),

    ("04-22 18:15", 78919.2, 78959.9, 78843.1, 78863.1),
    ("04-22 18:30", 78863.1, 78978.5, 78811.1, 78920.5),
    ("04-22 18:45", 78920.5, 79129.8, 78917.1, 78989.5),
    ("04-22 19:00", 78989.5, 79014.5, 78654.6, 78810.0),
    ("04-22 19:15", 78810.0, 79020.0, 78781.3, 78979.9),

    ("04-22 19:30", 78979.9, 79009.4, 78733.5, 78805.4),
    ("04-22 19:45", 78805.4, 78910.0, 78716.4, 78791.3),

    ("04-22 23:30", 78294.8, 78295.1, 78160.1, 78212.5),
    ("04-22 23:45", 78212.5, 78272.0, 78111.6, 78139.8),
    ("04-23 00:00", 78139.7, 78366.4, 77839.0, 77839.0),
    ("04-23 00:15", 77839.1, 78459.9, 77526.8, 78406.4),
    ("04-23 00:30", 78406.3, 78534.9, 78260.2, 78384.2),
    ("04-23 00:45", 78384.7, 78416.6, 78221.5, 78389.9),
    ("04-23 01:00", 78390.0, 78445.2, 78187.3, 78229.2),
    ("04-23 01:15", 78229.2, 78244.2, 78015.0, 78047.2),
    ("04-23 01:30", 78047.1, 78356.0, 78026.7, 78251.7),
    ("04-23 01:45", 78251.7, 78398.8, 78179.2, 78311.0),
    ("04-23 02:00", 78310.9, 78320.0, 78119.9, 78120.0),
    ("04-23 02:15", 78120.0, 78177.2, 77939.7, 77993.6),
    ("04-23 02:30", 77993.7, 78079.1, 77715.0, 77829.7),
    ("04-23 02:45", 77829.7, 77986.2, 77723.4, 77897.6),
    ("04-23 03:00", 77897.6, 77991.7, 77680.0, 77680.3),
    ("04-23 03:15", 77680.2, 77706.1, 77588.2, 77649.9),
    ("04-23 03:30", 77649.9, 77683.2, 77410.7, 77591.9),
    ("04-23 03:45", 77591.9, 77723.1, 77486.2, 77704.3),
    ("04-23 04:00", 77704.3, 77846.7, 77627.4, 77814.4),
    ("04-23 04:15", 77814.3, 77902.6, 77696.0, 77757.6),
    ("04-23 04:30", 77757.6, 77879.5, 77757.6, 77828.4),
    ("04-23 04:45", 77828.4, 77912.0, 77788.0, 77871.6),
    ("04-23 05:00", 77871.5, 78000.0, 77851.9, 77940.0),
    ("04-23 05:15", 77940.1, 77974.3, 77838.4, 77854.9),
    ("04-23 05:30", 77854.9, 77859.6, 77724.4, 77828.7),
    ("04-23 05:45", 77828.7, 78093.2, 77824.0, 77991.9),
    ("04-23 06:00", 77992.0, 78236.0, 77992.0, 78156.4),
    ("04-23 06:15", 78156.5, 78310.1, 78113.4, 78238.1),
    ("04-23 06:30", 78238.1, 78300.0, 78100.1, 78134.0),
    ("04-23 06:45", 78133.8, 78200.7, 78052.5, 78167.0),
    ("04-23 07:00", 78167.0, 78210.9, 78079.0, 78096.7),
    ("04-23 07:15", 78096.7, 78151.1, 78068.8, 78112.9),
    ("04-23 07:30", 78113.0, 78135.9, 77991.6, 78056.9),
    ("04-23 07:45", 78057.0, 78117.4, 77925.9, 78009.1),

    ("04-23 08:00", 78009.1, 78142.2, 77866.3, 78074.5),
    ("04-23 08:15", 78074.4, 78088.2, 77920.0, 77941.8),
    ("04-23 08:30", 77941.9, 77947.4, 77680.0, 77704.3),
    ("04-23 08:45", 77704.3, 77866.3, 77691.8, 77822.1),
    ("04-23 09:00", 77822.1, 77830.0, 77400.2, 77541.9),
    ("04-23 09:15", 77541.9, 77683.0, 77465.8, 77590.6),
    ("04-23 09:30", 77590.7, 77729.7, 77590.6, 77688.0),
    ("04-23 09:45", 77688.0, 77723.3, 77500.0, 77613.0),
    ("04-23 10:00", 77613.0, 77678.3, 76504.6, 77166.2),
    ("04-23 10:15", 77166.3, 77350.7, 77154.5, 77345.5),
    ("04-23 10:30", 77345.5, 77405.0, 77300.0, 77333.2),
    ("04-23 10:45", 77333.2, 77437.9, 77238.4, 77362.9),
    ("04-23 11:00", 77363.0, 77460.0, 77321.6, 77350.0),
    ("04-23 11:15", 77350.0, 77459.0, 77343.6, 77425.3),
    ("04-23 11:30", 77425.4, 77554.9, 77341.8, 77546.1),
    ("04-23 11:45", 77546.1, 77709.1, 77546.0, 77649.9),
    ("04-23 12:00", 77650.0, 77837.6, 77649.9, 77669.7),
    ("04-23 12:15", 77669.6, 77729.8, 77555.5, 77726.0),
    ("04-23 12:30", 77726.0, 77829.0, 77666.6, 77708.5),

    ("04-23 12:45", 77708.5, 77827.0, 77460.4, 77826.8),
    ("04-23 13:00", 77826.8, 77875.7, 77587.7, 77614.6),

    ("04-23 13:15", 77614.9, 77676.8, 77525.0, 77546.8),

    ("04-23 13:30", 77546.8, 77649.9, 77475.4, 77495.1),
    ("04-23 13:45", 77495.1, 77626.7, 77322.8, 77486.7),
    ("04-23 14:00", 77486.6, 77621.2, 77378.4, 77483.1),
    ("04-23 14:15", 77483.0, 77920.0, 77434.3, 77690.5),
    ("04-23 14:30", 77690.4, 77942.0, 77690.4, 77856.6),
    ("04-23 14:45", 77856.7, 78176.0, 77801.4, 78132.8),
    ("04-23 15:00", 78132.8, 78150.0, 77929.0, 78062.1),
    ("04-23 15:15", 78062.1, 78648.0, 78021.5, 78343.4),
    ("04-23 15:30", 78343.3, 78559.8, 78258.7, 78439.7),
    ("04-23 15:45", 78439.7, 78439.7, 78202.9, 78329.2),
    ("04-23 16:00", 78329.3, 78466.8, 78241.4, 78253.4),
    ("04-23 16:15", 78253.5, 78394.3, 78182.0, 78244.2),
    ("04-23 16:30", 78244.1, 78410.7, 78213.6, 78273.6),
    ("04-23 16:45", 78273.6, 78316.2, 77965.8, 78049.0),

    ("04-23 17:00", 78049.1, 78137.8, 77621.6, 77792.5),
    ("04-23 17:15", 77792.5, 77804.8, 77492.9, 77542.7),
    ("04-23 17:30", 77542.8, 77691.7, 76904.0, 77141.0),
    ("04-23 17:45", 77141.0, 77770.9, 76900.1, 77715.2),
    ("04-23 18:00", 77715.1, 78100.0, 77683.7, 77915.9),

    ("04-23 18:15", 77915.8, 78027.9, 77784.0, 77860.0),
    ("04-23 18:30", 77860.0, 78079.0, 77859.9, 77982.5),

    ("04-24 00:15", 78260.3, 78432.0, 78207.1, 78365.0),
    ("04-24 00:30", 78365.0, 78459.1, 78323.9, 78336.0),
    ("04-24 00:45", 78336.0, 78435.7, 78274.4, 78376.7),
    ("04-24 01:00", 78376.7, 78380.0, 78003.5, 78115.2),
    ("04-24 01:15", 78115.2, 78135.6, 77951.1, 77987.8),
    ("04-24 01:30", 77987.9, 78102.0, 77901.0, 78000.0),
    ("04-24 01:45", 78000.0, 78399.0, 77983.5, 78369.9),
    ("04-24 02:00", 78369.8, 78546.0, 78250.0, 78349.9),
    ("04-24 02:15", 78349.9, 78357.3, 78192.3, 78215.7),
    ("04-24 02:30", 78215.7, 78365.9, 78206.7, 78365.9),
    ("04-24 02:45", 78365.9, 78395.3, 77986.0, 78074.0),
    ("04-24 03:00", 78074.0, 78134.0, 78023.5, 78090.9),
    ("04-24 03:15", 78090.8, 78090.8, 77591.4, 77697.0),
    ("04-24 03:30", 77697.0, 77700.0, 77500.0, 77600.4),
    ("04-24 03:45", 77600.4, 77700.0, 77585.4, 77690.1),
    ("04-24 04:00", 77690.1, 77699.8, 77632.4, 77681.0),
    ("04-24 04:15", 77681.1, 77814.7, 77555.0, 77560.0),
    ("04-24 04:30", 77560.1, 77629.5, 77413.0, 77604.8),
    ("04-24 04:45", 77604.8, 77714.9, 77553.3, 77620.5),
    ("04-24 05:00", 77620.5, 77650.0, 77503.0, 77518.8),
    ("04-24 05:15", 77518.8, 77612.1, 77401.5, 77598.5),
    ("04-24 05:30", 77598.5, 77720.9, 77598.5, 77667.8),
    ("04-24 05:45", 77667.7, 78019.2, 77667.7, 77911.0),
    ("04-24 06:00", 77911.1, 77945.0, 77850.0, 77901.6),
    ("04-24 06:15", 77901.5, 77920.0, 77761.6, 77793.2),
    ("04-24 06:30", 77793.2, 77852.6, 77704.0, 77770.7),
    ("04-24 06:45", 77770.8, 77875.9, 77734.3, 77741.9),
    ("04-24 07:00", 77742.0, 77814.0, 77707.3, 77713.7),
    ("04-24 07:15", 77713.7, 77736.7, 77601.0, 77680.7),
    ("04-24 07:30", 77680.7, 77700.1, 77576.2, 77608.5),
    ("04-24 07:45", 77608.4, 77704.1, 77500.0, 77620.5),
    ("04-24 08:00", 77620.5, 77666.1, 77530.1, 77653.1),
    ("04-24 08:15", 77653.1, 77987.2, 77653.1, 77819.9),
    ("04-24 08:30", 77819.9, 77820.6, 77688.4, 77703.8),

    ("04-24 08:45", 77703.8, 77850.1, 77703.8, 77744.6),

    ("04-24 09:00", 77744.6, 77773.9, 77355.8, 77477.8),
    ("04-24 09:15", 77477.9, 77573.4, 77421.3, 77458.0),
    ("04-24 09:30", 77457.9, 77551.0, 77373.4, 77551.0),

    ("04-24 09:45", 77550.9, 77551.0, 77446.1, 77497.2),

    ("04-24 10:00", 77497.2, 77500.0, 77410.0, 77480.3),
    ("04-24 10:15", 77480.4, 77718.0, 77480.3, 77642.5),
    ("04-24 10:30", 77642.4, 77666.6, 77578.2, 77613.9),
    ("04-24 10:45", 77613.9, 77765.5, 77572.5, 77715.2),
    ("04-24 11:00", 77715.2, 78278.7, 77715.1, 78179.4),
    ("04-24 11:15", 78179.4, 78298.8, 78065.0, 78293.0),
    ("04-24 11:30", 78293.1, 78346.1, 78165.8, 78257.2),
    ("04-24 11:45", 78257.2, 78257.3, 78125.5, 78194.8),
    ("04-24 12:00", 78194.9, 78289.6, 78137.5, 78273.0),

    ("04-24 12:15", 78273.0, 78309.2, 78158.2, 78231.4),

    ("04-24 12:30", 78231.5, 78245.2, 78117.5, 78151.2),
    ("04-24 12:45", 78151.1, 78239.8, 77963.6, 78233.0),
    ("04-24 13:00", 78233.0, 78432.9, 78224.9, 78315.7),
    ("04-24 13:15", 78315.8, 78360.1, 78100.0, 78126.8),

    ("04-24 13:30", 78126.7, 78255.2, 78000.0, 78143.6),

    ("04-24 13:45", 78143.5, 78207.7, 77870.0, 78050.1),
    ("04-24 14:00", 78050.0, 78060.5, 77748.4, 77832.8),
    ("04-24 14:15", 77832.8, 77980.0, 77639.5, 77663.3),
    ("04-24 14:30", 77663.4, 77974.3, 77639.0, 77927.3),
    ("04-24 14:45", 77927.4, 78027.8, 77828.9, 77986.4),
    ("04-24 15:00", 77986.3, 77994.5, 77521.0, 77686.0),
    ("04-24 15:15", 77686.1, 77840.4, 77640.0, 77781.6),
    ("04-24 15:30", 77781.5, 77976.3, 77673.2, 77944.4),
    ("04-24 15:45", 77944.3, 78199.0, 77875.0, 78007.3),
    ("04-24 16:00", 78007.3, 78031.9, 77750.0, 77750.1),
    ("04-24 16:15", 77750.0, 77754.9, 77600.0, 77683.4),
    ("04-24 16:30", 77683.3, 77875.3, 77543.4, 77668.1),
    ("04-24 16:45", 77668.0, 77751.6, 77580.7, 77732.7),
    ("04-24 17:00", 77732.6, 77734.1, 77565.0, 77722.6),
    ("04-24 17:15", 77722.6, 77722.7, 77550.0, 77637.9),
    ("04-24 17:30", 77637.9, 77678.0, 77414.4, 77563.7),
    ("04-24 17:45", 77563.6, 77792.9, 77520.0, 77644.6),
    ("04-24 18:00", 77644.5, 77681.6, 77488.0, 77496.8),
    ("04-24 18:15", 77496.8, 77512.5, 77308.0, 77461.7),

    ("04-24 18:30", 77461.6, 77601.3, 77444.1, 77544.5),
    ("04-24 18:45", 77544.4, 77598.2, 77508.2, 77579.2),
    ("04-24 19:00", 77579.2, 77711.0, 77532.8, 77566.9),
    ("04-24 19:15", 77567.0, 77636.0, 77485.1, 77533.4),
    ("04-24 19:30", 77533.4, 77615.8, 77515.4, 77579.2),
    ("04-24 19:45", 77579.1, 77609.9, 77503.6, 77596.1),

    ("04-24 20:00", 77596.0, 77612.4, 77490.0, 77600.0),

    ("04-24 20:15", 77600.0, 77619.8, 77412.8, 77492.8),

    ("04-24 20:30", 77492.8, 77630.7, 77492.7, 77590.1),

    ("04-24 20:45", 77590.1, 77727.0, 77590.0, 77688.2),

    ("04-24 21:00", 77688.2, 77718.5, 77546.7, 77546.8),

    ("04-24 21:15", 77546.8, 77618.5, 77530.7, 77582.9),
    ("04-24 21:30", 77582.8, 77595.2, 77507.1, 77520.1),
    ("04-24 21:45", 77520.0, 77554.0, 77490.0, 77490.1),
    ("04-24 22:00", 77490.0, 77566.0, 77465.0, 77562.9),
    ("04-24 22:15", 77562.9, 77579.9, 77500.0, 77500.0),
    ("04-24 22:30", 77500.1, 77500.1, 77206.8, 77241.8),
    ("04-24 22:45", 77241.9, 77343.5, 77241.9, 77294.5),

    ("04-24 23:00", 77294.6, 77365.8, 77291.4, 77344.0),
    ("04-24 23:15", 77344.0, 77386.2, 77288.9, 77368.1),
    ("04-24 23:30", 77368.1, 77439.1, 77349.0, 77396.7),
    ("04-24 23:45", 77396.7, 77412.6, 77371.9, 77395.4),
    ("04-25 00:00", 77395.3, 77459.7, 77370.0, 77377.9),
    ("04-25 00:15", 77378.0, 77397.3, 77254.7, 77271.9),
    ("04-25 00:30", 77271.8, 77382.5, 77266.5, 77336.9),
    ("04-25 00:45", 77336.9, 77420.0, 77336.8, 77419.9),
    ("04-25 01:00", 77420.0, 77487.3, 77392.7, 77471.6),
    ("04-25 01:15", 77471.7, 77502.0, 77419.9, 77441.9),
    ("04-25 01:30", 77441.9, 77515.6, 77441.8, 77515.6),
    ("04-25 01:45", 77515.6, 77579.3, 77490.0, 77490.0),
    ("04-25 02:00", 77490.0, 77588.0, 77450.0, 77502.4),
    ("04-25 02:15", 77502.4, 77606.7, 77485.5, 77589.7),
    ("04-25 02:30", 77589.8, 77608.2, 77568.4, 77578.9),
    ("04-25 02:45", 77578.9, 77592.1, 77549.2, 77567.6),

    ("04-25 08:15", 77513.6, 77537.8, 77489.9, 77526.1),
    ("04-25 08:30", 77526.0, 77615.6, 77526.0, 77597.6),
    ("04-25 08:45", 77597.6, 77603.4, 77571.5, 77603.3),
    ("04-25 09:00", 77603.4, 77626.2, 77560.1, 77582.9),
    ("04-25 09:15", 77582.9, 77594.0, 77536.2, 77538.0),
    ("04-25 09:30", 77538.0, 77722.0, 77538.0, 77684.6),
    ("04-25 09:45", 77684.5, 77736.8, 77668.5, 77672.5),
    ("04-25 10:00", 77672.6, 77760.8, 77672.5, 77721.6),
    ("04-25 10:15", 77721.7, 77800.0, 77716.0, 77776.5),
    ("04-25 10:30", 77776.5, 77847.0, 77722.7, 77766.5),
    ("04-25 10:45", 77766.5, 77786.2, 77734.0, 77749.3),
    ("04-25 11:00", 77749.3, 77749.3, 77689.9, 77689.9),
    ("04-25 11:15", 77689.9, 77709.6, 77585.0, 77626.3),
    ("04-25 11:30", 77626.3, 77642.2, 77582.6, 77593.0),
    ("04-25 11:45", 77593.1, 77651.3, 77564.0, 77638.7),
    ("04-25 12:00", 77638.7, 77673.0, 77580.0, 77644.2),
    ("04-25 12:15", 77644.3, 77667.0, 77555.9, 77561.6),
    ("04-25 12:30", 77561.5, 77572.5, 77500.1, 77517.2),
    ("04-25 12:45", 77517.2, 77545.2, 77502.2, 77518.3),
    ("04-25 13:00", 77518.3, 77615.8, 77518.3, 77603.9),
    ("04-25 13:15", 77603.8, 77604.4, 77564.9, 77577.6),
    ("04-25 13:30", 77577.6, 77638.5, 77560.0, 77638.5),
    ("04-25 13:45", 77638.5, 77676.5, 77611.1, 77650.1),
    ("04-25 14:00", 77650.1, 77719.1, 77589.8, 77655.5),
    ("04-25 14:15", 77655.5, 77704.7, 77620.8, 77686.6),
    ("04-25 14:30", 77686.7, 77707.5, 77666.6, 77689.1),
    ("04-25 14:45", 77689.0, 77713.4, 77603.8, 77618.2),
    ("04-25 15:00", 77618.3, 77639.9, 77600.8, 77631.1),
    ("04-25 15:15", 77631.1, 77686.8, 77631.0, 77665.8),
    ("04-25 15:30", 77665.9, 77691.1, 77621.3, 77621.3),
    ("04-25 15:45", 77621.3, 77621.4, 77263.0, 77289.3),
    ("04-25 16:00", 77289.3, 77411.8, 77251.2, 77407.6),
    ("04-25 16:15", 77407.5, 77411.5, 77282.0, 77355.3),
    ("04-25 16:30", 77355.3, 77385.0, 77100.0, 77327.0),

    ("04-25 16:45", 77327.0, 77375.0, 77300.2, 77364.0),

    ("04-25 17:00", 77364.0, 77378.1, 77305.0, 77312.0),
    ("04-25 17:15", 77312.0, 77379.7, 77256.1, 77284.1),
    ("04-25 17:30", 77284.1, 77301.7, 77211.8, 77267.6),
    ("04-25 17:45", 77267.7, 77270.3, 77162.0, 77213.4),
    ("04-25 18:00", 77213.3, 77293.9, 77174.2, 77245.1),
    ("04-25 18:15", 77245.1, 77287.9, 77220.1, 77285.2),

    ("04-25 18:30", 77285.1, 77353.6, 77270.7, 77270.7),

    ("04-25 18:45", 77270.8, 77327.2, 77246.9, 77256.8),
    ("04-25 19:00", 77256.8, 77300.5, 77235.0, 77290.1),
    ("04-25 19:15", 77290.1, 77312.6, 77208.0, 77218.4),
    ("04-25 19:30", 77218.3, 77225.1, 77153.1, 77153.2),

    ("04-25 19:45", 77153.1, 77301.6, 77153.0, 77285.6),
    ("04-25 20:00", 77285.7, 77360.7, 77267.3, 77316.0),
    ("04-25 20:15", 77316.0, 77402.0, 77306.9, 77389.4),
    ("04-25 20:30", 77389.4, 77391.5, 77359.9, 77360.5),
    ("04-25 20:45", 77360.6, 77450.0, 77360.5, 77439.1),

    ("04-25 23:45", 77559.9, 77585.0, 77553.8, 77585.0),
    ("04-26 00:00", 77585.0, 77607.7, 77472.7, 77513.6),
    ("04-26 00:15", 77513.5, 77513.5, 77425.9, 77432.0),
    ("04-26 00:30", 77432.1, 77514.4, 77401.8, 77509.5),
    ("04-26 00:45", 77509.6, 77557.6, 77412.6, 77457.4),
    ("04-26 01:00", 77457.4, 77490.6, 77440.0, 77463.6),
    ("04-26 01:15", 77463.6, 77531.6, 77449.8, 77459.8),
    ("04-26 01:30", 77459.9, 77523.5, 77455.4, 77518.3),
    ("04-26 01:45", 77518.3, 77518.3, 77395.2, 77417.4),
    ("04-26 02:00", 77417.3, 77530.8, 77410.0, 77530.8),
    ("04-26 02:15", 77530.8, 77553.9, 77480.0, 77518.3),
    ("04-26 02:30", 77518.3, 77547.1, 77480.1, 77482.1),
    ("04-26 02:45", 77482.2, 77482.2, 77434.9, 77480.1),
    ("04-26 03:00", 77480.0, 77487.2, 77440.0, 77487.2),
    ("04-26 03:15", 77487.1, 77500.0, 77370.1, 77384.0),
    ("04-26 03:30", 77384.1, 77386.1, 77280.0, 77341.4),
    ("04-26 03:45", 77341.4, 77386.1, 77321.6, 77349.3),
    ("04-26 04:00", 77349.3, 77455.0, 77338.4, 77432.9),
    ("04-26 04:15", 77432.8, 77456.0, 77422.4, 77430.2),
    ("04-26 04:30", 77430.1, 77488.8, 77379.0, 77472.9),
    ("04-26 04:45", 77472.8, 77777.0, 77472.8, 77727.0),
    ("04-26 05:00", 77727.1, 78119.6, 77670.9, 78089.4),
    ("04-26 05:15", 78089.5, 78164.7, 77979.3, 78060.0),
    ("04-26 05:30", 78060.0, 78156.5, 77976.6, 78012.1),
    ("04-26 05:45", 78012.1, 78023.0, 77939.0, 77949.4),
    ("04-26 06:00", 77949.4, 78008.0, 77949.4, 77980.0),
    ("04-26 06:15", 77980.1, 77984.1, 77886.0, 77911.5),
    ("04-26 06:30", 77911.5, 78012.2, 77885.0, 77975.0),
    ("04-26 06:45", 77974.9, 77975.0, 77851.2, 77963.2),
    ("04-26 07:00", 77963.3, 77987.9, 77947.8, 77967.4),
    ("04-26 07:15", 77967.4, 78000.0, 77947.2, 77957.0),
    ("04-26 07:30", 77957.0, 77960.5, 77920.5, 77935.2),
    ("04-26 07:45", 77935.2, 78085.0, 77935.1, 78061.5),
    ("04-26 08:00", 78061.5, 78095.3, 78001.6, 78031.4),

    ("04-26 08:15", 78031.4, 78050.5, 77973.5, 78042.1),
    ("04-26 08:30", 78042.2, 78182.8, 77981.2, 78005.0),
    ("04-26 08:45", 78005.0, 78017.1, 77982.5, 77989.0),
    ("04-26 09:00", 77989.1, 77989.1, 77926.4, 77973.8),
    ("04-26 09:15", 77973.8, 78020.0, 77950.0, 77972.0),
    ("04-26 09:30", 77971.9, 77972.0, 77880.0, 77932.2),
    ("04-26 09:45", 77932.3, 77971.8, 77904.3, 77971.8),
    ("04-26 10:00", 77971.8, 78017.7, 77914.5, 77993.6),
    ("04-26 10:15", 77993.6, 78005.3, 77964.3, 77972.7),
    ("04-26 10:30", 77972.7, 77973.1, 77932.5, 77945.7),
    ("04-26 10:45", 77945.7, 77967.3, 77923.4, 77961.4),
    ("04-26 11:00", 77961.5, 78050.0, 77961.4, 78006.0),
    ("04-26 11:15", 78006.1, 78114.5, 77985.8, 78092.1),
    ("04-26 11:30", 78092.1, 78104.0, 78022.5, 78031.9),

    ("04-26 11:45", 78032.0, 78089.0, 78005.7, 78050.0),
    ("04-26 12:00", 78050.0, 78063.5, 77932.4, 77933.8),
    ("04-26 12:15", 77933.8, 77980.1, 77918.0, 77935.3),
    ("04-26 12:30", 77935.3, 77947.5, 77900.0, 77900.0),
    ("04-26 12:45", 77900.0, 77900.0, 77715.0, 77795.5),
    ("04-26 13:00", 77795.4, 77893.8, 77742.6, 77859.9),

    ("04-26 13:15", 77860.0, 77899.7, 77769.7, 77834.7),
    ("04-26 13:30", 77834.7, 77953.2, 77825.1, 77950.0),

    ("04-26 13:45", 77950.1, 77953.1, 77871.0, 77940.1),
    ("04-26 14:00", 77940.0, 77940.1, 77840.5, 77917.1),
    ("04-26 14:15", 77917.0, 78136.5, 77891.1, 78022.0),
    ("04-26 14:30", 78022.0, 78087.6, 77970.2, 78016.0),
    ("04-26 14:45", 78016.1, 78120.0, 77950.0, 78053.4),
    ("04-26 15:00", 78053.5, 78091.3, 77989.0, 78053.1),
    ("04-26 15:15", 78053.2, 78088.8, 77912.5, 78058.0),
    ("04-26 15:30", 78057.9, 78073.6, 77981.8, 78005.9),
    ("04-26 15:45", 78005.8, 78014.8, 77952.2, 78007.9),
    ("04-26 16:00", 78007.9, 78028.7, 77965.0, 77973.7),
    ("04-26 16:15", 77973.7, 78013.6, 77973.7, 78011.1),
    ("04-26 16:30", 78011.0, 78055.7, 77960.5, 77960.6),
    ("04-26 16:45", 77960.5, 78000.0, 77890.0, 77890.0),
    ("04-26 17:00", 77890.1, 77986.3, 77815.0, 77976.0),
    ("04-26 17:15", 77976.0, 78009.4, 77938.0, 77975.4),

    ("04-26 17:30", 77975.5, 77991.7, 77896.8, 77979.0),
    ("04-26 17:45", 77979.0, 78026.9, 77962.2, 77976.7),

    ("04-26 18:00", 77976.7, 78125.1, 77945.7, 78063.2),
    ("04-26 18:15", 78063.1, 78326.2, 78040.0, 78138.6),
    ("04-26 18:30", 78138.7, 78195.1, 78096.7, 78170.2),
    ("04-26 18:45", 78170.3, 78260.0, 78142.1, 78238.1),
    ("04-26 19:00", 78238.1, 78400.0, 78130.1, 78359.9),
    ("04-26 19:15", 78359.9, 78477.9, 77967.9, 78159.0),
    ("04-26 19:30", 78158.9, 78187.2, 78004.8, 78141.1),

    ("04-26 19:45", 78141.1, 78250.0, 78134.1, 78183.1),
    ("04-26 20:00", 78183.2, 78225.7, 78142.6, 78142.6),
    ("04-26 20:15", 78142.6, 78200.1, 78107.0, 78185.1),
    ("04-26 20:30", 78185.0, 78355.1, 78185.0, 78245.4),
    ("04-26 20:45", 78245.4, 78312.5, 78135.0, 78150.1),
    ("04-26 21:00", 78150.0, 78247.4, 78139.4, 78198.8),
    ("04-26 21:15", 78198.7, 78235.7, 78139.0, 78151.5),
    ("04-26 21:30", 78151.6, 78151.6, 77912.0, 77950.6),
    ("04-26 21:45", 77950.7, 78994.8, 77777.0, 78369.7),

    ("04-26 22:00", 78369.6, 78544.1, 78307.0, 78521.9),

    ("04-26 22:15", 78521.9, 78821.1, 78459.8, 78484.8),

    ("04-26 22:30", 78484.7, 78484.7, 77915.5, 78241.3),

    ("04-26 22:45", 78241.2, 78398.9, 78222.8, 78274.7),
    ("04-26 23:00", 78274.7, 78361.8, 78215.0, 78314.0),
    ("04-26 23:15", 78313.9, 78424.5, 78106.2, 78109.0),
    ("04-26 23:30", 78109.0, 78569.6, 77988.1, 78560.2),
    ("04-26 23:45", 78560.2, 78870.3, 78550.0, 78613.5),
    ("04-27 00:00", 78614.4, 78842.7, 78520.0, 78542.0),
    ("04-27 00:15", 78542.1, 78604.6, 78319.1, 78443.4),

    ("04-27 00:30", 78443.3, 78788.0, 78356.7, 78774.2),

    ("04-27 02:15", 79142.5, 79224.6, 78984.7, 79085.5),
    ("04-27 02:30", 79085.6, 79218.0, 79000.0, 79027.6),
    ("04-27 02:45", 79027.6, 79163.2, 79019.8, 79082.9),
    ("04-27 03:00", 79082.9, 79212.6, 79032.9, 79168.4),
    ("04-27 03:15", 79168.5, 79229.9, 79126.5, 79199.6),
    ("04-27 03:30", 79199.6, 79273.4, 79124.4, 79199.9),
    ("04-27 03:45", 79199.9, 79216.8, 79032.3, 79065.1),
    ("04-27 04:00", 79065.1, 79092.1, 78957.0, 79014.4),
    ("04-27 04:15", 79014.5, 79084.2, 78959.3, 79084.1),
    ("04-27 04:30", 79084.2, 79128.1, 78978.0, 79030.1),
    ("04-27 04:45", 79030.2, 79046.3, 78830.0, 78882.6),
    ("04-27 05:00", 78882.6, 78904.1, 78311.0, 78351.5),
    ("04-27 05:15", 78351.5, 78366.4, 77753.0, 77780.1),
    ("04-27 05:30", 77780.0, 77822.4, 77503.6, 77750.5),
    ("04-27 05:45", 77750.5, 77826.7, 77686.5, 77730.6),
    ("04-27 06:00", 77730.5, 77767.5, 77610.0, 77683.9),
    ("04-27 06:15", 77684.0, 77834.0, 77642.5, 77677.1),
    ("04-27 06:30", 77677.0, 77677.1, 77408.6, 77568.1),
    ("04-27 06:45", 77568.2, 77699.5, 77560.4, 77657.9),
    ("04-27 07:00", 77657.9, 77692.5, 77512.3, 77599.9),
    ("04-27 07:15", 77599.9, 77698.2, 77521.2, 77647.6),
    ("04-27 07:30", 77647.5, 77647.6, 77534.1, 77634.7),
    ("04-27 07:45", 77634.7, 77696.5, 77556.7, 77556.7),
    ("04-27 08:00", 77556.7, 77685.1, 77541.0, 77590.7),
    ("04-27 08:15", 77590.7, 77646.8, 77517.4, 77524.3),
    ("04-27 08:30", 77524.3, 77625.8, 77500.0, 77575.5),
    ("04-27 08:45", 77575.5, 77775.3, 77575.5, 77763.5),
    ("04-27 09:00", 77763.4, 77817.0, 77740.0, 77810.0),
    ("04-27 09:15", 77810.0, 77810.0, 77657.1, 77739.1),
    ("04-27 09:30", 77739.2, 77945.0, 77719.0, 77907.0),
    ("04-27 09:45", 77907.0, 77949.9, 77850.3, 77856.1),
    ("04-27 10:00", 77856.1, 77903.1, 77756.0, 77771.7),
    ("04-27 10:15", 77771.7, 77796.1, 77740.1, 77768.0),
    ("04-27 10:30", 77768.0, 77886.0, 77756.3, 77832.2),

    ("04-27 10:45", 77832.2, 77859.9, 77801.1, 77806.7),
    ("04-27 11:00", 77806.7, 77842.8, 77700.0, 77738.3),

    ("04-27 11:15", 77738.3, 77854.2, 77705.0, 77815.5),
    ("04-27 11:30", 77815.6, 77848.5, 77737.0, 77768.0),

    ("04-27 13:15", 77662.6, 77750.0, 77594.4, 77668.9),
    ("04-27 13:30", 77668.9, 77930.3, 77581.7, 77800.8),
    ("04-27 13:45", 77800.7, 77813.9, 77516.4, 77700.0),
    ("04-27 14:00", 77700.3, 77880.0, 77627.2, 77812.0),
    ("04-27 14:15", 77812.0, 77881.1, 77780.0, 77836.9),
    ("04-27 14:30", 77836.8, 78179.7, 77799.8, 78136.0),
    ("04-27 14:45", 78136.0, 78232.0, 77744.9, 77776.0),
    ("04-27 15:00", 77775.9, 77796.3, 77222.0, 77337.2),
    ("04-27 15:15", 77337.2, 77337.3, 76524.0, 76823.1),
    ("04-27 15:30", 76823.0, 77063.0, 76785.3, 77020.5),
    ("04-27 15:45", 77020.5, 77024.3, 76683.2, 76760.0),
    ("04-27 16:00", 76760.0, 76819.0, 76611.7, 76743.3),
    ("04-27 16:15", 76743.2, 76829.1, 76688.0, 76710.0),
    ("04-27 16:30", 76709.9, 76784.0, 76560.0, 76563.8),
    ("04-27 16:45", 76563.8, 76663.1, 76509.7, 76587.9),
    ("04-27 17:00", 76587.9, 76766.0, 76585.4, 76666.1),
    ("04-27 17:15", 76666.1, 76868.5, 76600.0, 76793.5),
    ("04-27 17:30", 76793.4, 76902.7, 76722.5, 76830.4),
    ("04-27 17:45", 76830.4, 76866.4, 76664.2, 76702.3),
    ("04-27 18:00", 76702.3, 76779.0, 76632.7, 76715.3),
    ("04-27 18:15", 76715.3, 76820.3, 76623.1, 76657.4),
    ("04-27 18:30", 76657.0, 76736.0, 76636.0, 76727.7),
    ("04-27 18:45", 76727.7, 76858.5, 76691.7, 76790.7),
    ("04-27 19:00", 76790.6, 76858.3, 76691.0, 76836.9),
    ("04-27 19:15", 76836.9, 76863.0, 76584.0, 76584.1),
    ("04-27 19:30", 76584.1, 76750.1, 76400.0, 76741.0),
    ("04-27 19:45", 76740.9, 76844.4, 76720.0, 76844.4),
    ("04-27 20:00", 76844.3, 76967.8, 76780.9, 76856.1),
    ("04-27 20:15", 76856.0, 76962.0, 76856.0, 76952.4),
    ("04-27 20:30", 76952.4, 77037.0, 76910.2, 76942.2),
    ("04-27 20:45", 76942.2, 76963.3, 76893.4, 76915.8),
    ("04-27 21:00", 76915.8, 76915.9, 76783.0, 76844.7),
    ("04-27 21:15", 76844.7, 76904.0, 76806.2, 76867.4),
    ("04-27 21:30", 76867.4, 76944.5, 76830.1, 76857.8),

    ("04-30 04:15", 75748.5, 75761.6, 75625.0, 75637.3),
    ("04-30 04:30", 75637.3, 75650.9, 75363.2, 75385.2),
    ("04-30 04:45", 75385.2, 75502.1, 75385.2, 75458.3),
    ("04-30 05:00", 75458.4, 75596.3, 75435.1, 75574.2),
    ("04-30 05:15", 75574.1, 75593.8, 75273.5, 75389.1),
    ("04-30 05:30", 75389.2, 75721.0, 75389.1, 75675.2),
    ("04-30 05:45", 75675.1, 75708.0, 75562.8, 75569.6),
    ("04-30 06:00", 75569.6, 75652.6, 75540.1, 75563.1),
    ("04-30 06:15", 75562.6, 75661.2, 75562.6, 75641.7),
    ("04-30 06:30", 75641.7, 75835.6, 75641.7, 75710.0),
    ("04-30 06:45", 75710.1, 75760.5, 75668.7, 75720.6),
    ("04-30 07:00", 75720.6, 75810.0, 75684.6, 75774.9),
    ("04-30 07:15", 75774.8, 75864.9, 75742.5, 75852.7),
    ("04-30 07:30", 75852.7, 76047.8, 75852.6, 76045.0),
    ("04-30 07:45", 76045.0, 76148.0, 76021.0, 76129.9),
    ("04-30 08:00", 76129.9, 76180.0, 76036.7, 76054.9),
    ("04-30 08:15", 76054.9, 76132.3, 75987.6, 76045.3),
    ("04-30 08:30", 76045.4, 76107.7, 76012.0, 76104.1),
    ("04-30 08:45", 76104.2, 76116.5, 76020.4, 76025.7),
    ("04-30 09:00", 76025.8, 76076.8, 75989.0, 76050.8),
    ("04-30 09:15", 76050.8, 76197.2, 75973.3, 76196.1),
    ("04-30 09:30", 76196.0, 76332.6, 76035.8, 76042.0),
    ("04-30 09:45", 76042.0, 76168.0, 76035.1, 76062.7),
    ("04-30 10:00", 76062.7, 76136.6, 76004.0, 76014.4),
    ("04-30 10:15", 76014.3, 76046.1, 75943.3, 75952.8),
    ("04-30 10:30", 75952.8, 76088.8, 75952.8, 76016.1),
    ("04-30 10:45", 76016.2, 76043.7, 75967.7, 76001.6),
    ("04-30 11:00", 76001.7, 76233.0, 76001.6, 76117.4),
    ("04-30 11:15", 76117.4, 76160.0, 76055.6, 76075.1),
    ("04-30 11:30", 76075.1, 76100.0, 75858.0, 75893.5),
    ("04-30 11:45", 75893.4, 76068.5, 75836.0, 76032.9),
    ("04-30 12:00", 76032.9, 76140.0, 76009.8, 76109.9),
    ("04-30 12:15", 76110.0, 76333.3, 76101.4, 76298.8),
    ("04-30 12:30", 76298.7, 76375.1, 76199.0, 76199.0),

    ("04-30 12:45", 76199.1, 76370.0, 76199.0, 76259.0),

    ("04-30 13:00", 76259.0, 76320.8, 76221.1, 76270.0),
    ("04-30 13:15", 76269.9, 76300.0, 76111.1, 76147.2),
    ("04-30 13:30", 76147.2, 76599.9, 76066.6, 76586.4),
    ("04-30 13:45", 76586.3, 76630.3, 76357.3, 76370.3),
    ("04-30 14:00", 76370.4, 76546.7, 76226.0, 76317.2),
    ("04-30 14:15", 76317.3, 76326.4, 76044.7, 76310.5),
    ("04-30 14:30", 76310.4, 76519.6, 76161.6, 76296.0),
    ("04-30 14:45", 76296.0, 76433.9, 76227.4, 76256.0),
    ("04-30 15:00", 76256.1, 76410.0, 76116.0, 76394.2),
    ("04-30 15:15", 76394.2, 76468.1, 76326.8, 76468.1),
    ("04-30 15:30", 76468.1, 76614.9, 76326.6, 76430.1),
    ("04-30 15:45", 76430.0, 76497.6, 76283.2, 76423.0),
    ("04-30 16:00", 76423.0, 76446.9, 76315.6, 76440.1),
    ("04-30 16:15", 76440.1, 76440.1, 76251.0, 76322.7),
    ("04-30 16:30", 76322.7, 76384.6, 76280.0, 76305.1),
    ("04-30 16:45", 76305.2, 76340.0, 76181.9, 76220.1),
    ("04-30 17:00", 76220.2, 76294.2, 76169.4, 76178.7),
    ("04-30 17:15", 76178.8, 76178.8, 76060.4, 76110.8),
    ("04-30 17:30", 76110.7, 76230.0, 76100.0, 76126.8),
    ("04-30 17:45", 76126.8, 76268.0, 76125.5, 76209.2),
    ("04-30 18:00", 76209.2, 76340.9, 76206.1, 76230.1),
    ("04-30 18:15", 76230.0, 76438.3, 76229.8, 76249.9),
    ("04-30 18:30", 76250.0, 76382.1, 76166.3, 76357.3),
    ("04-30 18:45", 76357.3, 76440.0, 76309.1, 76309.1),
    ("04-30 19:00", 76309.2, 76456.0, 76264.2, 76413.1),
    ("04-30 19:15", 76413.1, 76466.6, 76379.9, 76432.8),
    ("04-30 19:30", 76432.8, 76470.5, 76368.1, 76402.1),
    ("04-30 19:45", 76402.1, 76427.7, 76334.2, 76366.7),
    ("04-30 20:00", 76366.7, 76433.5, 76305.6, 76406.7),
    ("04-30 20:15", 76406.6, 76525.4, 76273.3, 76429.9),

    ("04-30 20:30", 76429.9, 76500.1, 76399.7, 76473.6),
    ("04-30 20:45", 76473.5, 76536.2, 76444.5, 76451.1),
    ("04-30 21:00", 76451.1, 76495.4, 76405.4, 76453.0),

    ("04-30 21:15", 76453.0, 76453.0, 76274.5, 76299.9),
    ("04-30 21:30", 76299.9, 76416.0, 76299.9, 76344.6),
    ("04-30 21:45", 76344.7, 76344.7, 76186.0, 76202.8),
    ("04-30 22:00", 76202.8, 76330.0, 76191.4, 76321.4),
    ("04-30 22:15", 76321.4, 76409.3, 76315.0, 76395.9),
    ("04-30 22:30", 76395.8, 76408.1, 76224.3, 76292.5),
    ("04-30 22:45", 76292.4, 76335.5, 76155.1, 76197.9),
    ("04-30 23:00", 76198.0, 76288.7, 76173.3, 76261.9),
    ("04-30 23:15", 76261.9, 76299.9, 76245.0, 76299.9),
    ("04-30 23:30", 76299.9, 76347.0, 76277.6, 76285.4),
    ("04-30 23:45", 76285.4, 76342.0, 76261.1, 76305.4),
    ("05-01 00:00", 76305.4, 76472.8, 76265.4, 76428.9),
    ("05-01 00:15", 76428.8, 76533.3, 76422.8, 76479.9),
    ("05-01 00:30", 76479.9, 76517.2, 76410.4, 76488.5),
    ("05-01 00:45", 76488.5, 76557.3, 76353.7, 76415.1),
    ("05-01 01:00", 76415.1, 76549.1, 76400.1, 76515.1),
    ("05-01 01:15", 76515.1, 76586.0, 76484.3, 76495.5),

    ("05-02 05:00", 78137.3, 78149.9, 78000.1, 78048.3),
    ("05-02 05:15", 78048.3, 78090.0, 77979.3, 78067.8),
    ("05-02 05:30", 78067.8, 78170.3, 78067.7, 78150.1),
    ("05-02 05:45", 78150.1, 78219.6, 78140.0, 78140.0),
    ("05-02 06:00", 78140.1, 78245.3, 78136.8, 78143.6),
    ("05-02 06:15", 78143.7, 78180.0, 78099.4, 78099.9),
    ("05-02 06:30", 78099.9, 78193.1, 78099.9, 78189.2),
    ("05-02 06:45", 78189.2, 78322.0, 78189.1, 78278.3),
    ("05-02 07:00", 78278.3, 78304.2, 78257.4, 78274.1),
    ("05-02 07:15", 78274.0, 78300.0, 78262.5, 78275.2),
    ("05-02 07:30", 78275.3, 78290.6, 78174.0, 78190.0),
    ("05-02 07:45", 78190.0, 78224.4, 78156.1, 78181.6),
    ("05-02 08:00", 78181.6, 78223.9, 78113.0, 78218.0),
    ("05-02 08:15", 78218.0, 78247.2, 78193.0, 78239.3),
    ("05-02 08:30", 78239.4, 78305.8, 78239.3, 78282.2),
    ("05-02 08:45", 78282.2, 78318.0, 78246.2, 78272.2),
    ("05-02 09:00", 78272.2, 78290.0, 78250.0, 78262.1),
    ("05-02 09:15", 78262.2, 78303.3, 78262.2, 78268.1),
    ("05-02 09:30", 78268.0, 78359.2, 78168.4, 78262.1),
    ("05-02 09:45", 78262.1, 78280.0, 78246.7, 78252.3),
    ("05-02 10:00", 78252.4, 78273.1, 78240.0, 78250.1),
    ("05-02 10:15", 78250.0, 78264.0, 78187.7, 78211.2),
    ("05-02 10:30", 78211.3, 78228.6, 78175.0, 78210.9),
    ("05-02 10:45", 78210.8, 78236.4, 78190.0, 78205.4),
    ("05-02 11:00", 78205.5, 78205.5, 78120.1, 78135.8),
    ("05-02 11:15", 78135.8, 78199.1, 78132.0, 78171.1),
    ("05-02 11:30", 78171.1, 78176.9, 78082.0, 78134.9),
    ("05-02 11:45", 78134.9, 78135.0, 78055.7, 78105.7),
    ("05-02 12:00", 78105.7, 78127.0, 78056.0, 78097.3),
    ("05-02 12:15", 78097.2, 78232.0, 78097.2, 78208.0),
    ("05-02 12:30", 78208.0, 78220.4, 78148.2, 78187.2),
    ("05-02 12:45", 78187.1, 78187.1, 78135.9, 78169.7),
    ("05-02 13:00", 78169.7, 78403.1, 78169.6, 78350.7),
    ("05-02 13:15", 78350.7, 78350.7, 78262.3, 78262.4),

    ("05-02 13:30", 78262.4, 78327.9, 78262.3, 78326.8),

    ("05-02 13:45", 78326.9, 78363.2, 78280.0, 78332.0),
    ("05-02 14:00", 78331.9, 78359.7, 78275.9, 78276.1),
    ("05-02 14:15", 78276.0, 78458.2, 78271.8, 78386.3),
    ("05-02 14:30", 78386.4, 78432.0, 78338.2, 78364.7),
    ("05-02 14:45", 78364.8, 78452.5, 78358.0, 78380.9),
    ("05-02 15:00", 78380.8, 78447.3, 78380.8, 78397.0),
    ("05-02 15:15", 78396.9, 78399.0, 78320.0, 78336.2),
    ("05-02 15:30", 78336.2, 78410.0, 78331.6, 78397.9),
    ("05-02 15:45", 78398.0, 78450.0, 78372.0, 78449.8),
    ("05-02 16:00", 78449.8, 78550.0, 78416.1, 78498.5),
    ("05-02 16:15", 78498.6, 78565.9, 78464.8, 78468.4),
    ("05-02 16:30", 78468.4, 78468.5, 78390.0, 78390.0),
    ("05-02 16:45", 78390.0, 78464.5, 78390.0, 78419.9),
    ("05-02 17:00", 78419.9, 78420.0, 78376.3, 78398.0),
    ("05-02 17:15", 78397.9, 78418.1, 78374.9, 78385.6),
    ("05-02 17:30", 78385.6, 78453.9, 78385.6, 78387.2),
    ("05-02 17:45", 78387.2, 78401.7, 78328.1, 78362.1),
    ("05-02 18:00", 78362.1, 78362.1, 78283.7, 78286.2),
    ("05-02 18:15", 78286.1, 78362.2, 78277.0, 78360.3),
    ("05-02 18:30", 78360.4, 78432.2, 78360.3, 78379.1),
    ("05-02 18:45", 78379.1, 78459.0, 78379.0, 78432.1),
    ("05-02 19:00", 78432.0, 78477.0, 78408.0, 78437.2),
    ("05-02 19:15", 78437.2, 78447.2, 78404.8, 78420.8),
    ("05-02 19:30", 78420.8, 78486.5, 78407.3, 78460.0),
    ("05-02 19:45", 78460.0, 78460.1, 78416.5, 78443.8),
    ("05-02 20:00", 78444.1, 78449.0, 78394.5, 78394.5),

    ("05-02 20:15", 78394.5, 78400.0, 78383.4, 78395.0),

    ("05-02 20:30", 78394.9, 78440.0, 78388.6, 78400.0),

    ("05-02 20:45", 78399.9, 78421.6, 78376.0, 78415.2),
    ("05-02 21:00", 78415.3, 78483.2, 78408.9, 78408.9),
    ("05-02 21:15", 78408.9, 78458.1, 78401.5, 78455.4),
    ("05-02 21:30", 78455.4, 79145.0, 78455.4, 78767.0),
    ("05-02 21:45", 78767.0, 78880.0, 78675.8, 78689.8),
    ("05-02 22:00", 78689.7, 78773.0, 78624.0, 78745.2),
    ("05-02 22:15", 78745.2, 78745.2, 78569.2, 78590.0),
    ("05-02 22:30", 78589.9, 78717.0, 78588.4, 78619.9),
    ("05-02 22:45", 78620.0, 78838.0, 78619.4, 78793.2),
    ("05-02 23:00", 78793.2, 78793.2, 78650.0, 78697.7),
    ("05-02 23:15", 78697.7, 78774.6, 78684.8, 78766.6),
    ("05-02 23:30", 78766.6, 78784.7, 78653.9, 78653.9),
    ("05-02 23:45", 78653.9, 78676.1, 78588.3, 78652.9),
]

# =================== 1H MUM VERİSİ (Binance API) ===================
# Kaynak: /fapi/v1/klines?symbol=BTCUSDT&interval=1h&limit=168 → UTC+3

CANDLES_1H = [
    ("03-25 07:00", 70689.2, 70949.3, 70659.9, 70938.1),
    ("03-25 08:00", 70938.1, 71319.9, 70900.2, 71080.1),
    ("03-25 09:00", 71080.1, 71233.7, 70928.5, 70962.8),
    ("03-25 10:00", 70962.8, 71233.6, 70850.0, 70900.0),
    ("03-25 11:00", 70899.9, 71478.0, 70752.5, 71209.1),
    ("03-25 12:00", 71209.2, 71376.0, 71058.4, 71301.5),
    ("03-25 13:00", 71301.4, 71600.0, 71250.9, 71462.7),
    ("03-25 14:00", 71462.7, 71999.9, 71425.0, 71650.3),
    ("03-25 15:00", 71650.3, 71933.3, 71085.5, 71685.4),
    ("03-25 16:00", 71685.4, 71931.9, 71473.3, 71546.6),
    ("03-25 17:00", 71546.6, 71666.6, 71190.0, 71203.6),
    ("03-25 18:00", 71203.6, 71282.3, 70531.4, 70792.4),
    ("03-25 19:00", 70792.4, 71742.2, 70671.3, 71290.0),
    ("03-25 20:00", 71290.0, 71361.8, 70676.8, 70752.6),
    ("03-25 21:00", 70752.6, 71121.3, 70623.4, 70786.8),
    ("03-25 22:00", 70786.8, 71082.3, 70741.8, 70853.2),
    ("03-25 23:00", 70853.3, 71028.0, 70603.0, 70970.0),
    ("03-26 00:00", 70970.0, 71149.6, 70889.6, 71000.0),
    ("03-26 01:00", 71000.0, 71606.0, 70907.1, 71330.1),
    ("03-26 02:00", 71330.0, 71412.1, 71143.5, 71297.5),
    ("03-26 03:00", 71297.5, 71408.1, 71088.1, 71265.8),
    ("03-26 04:00", 71265.8, 71341.0, 71116.9, 71212.9),
    ("03-26 05:00", 71212.9, 71257.1, 70640.0, 70855.0),
    ("03-26 06:00", 70855.0, 70944.9, 70650.0, 70881.9),
    ("03-26 07:00", 70882.0, 70882.0, 70680.0, 70737.0),
    ("03-26 08:00", 70737.0, 70767.6, 69906.2, 69988.7),
    ("03-26 09:00", 69988.6, 70126.6, 69815.4, 70057.5),
    ("03-26 10:00", 70057.4, 70140.0, 69722.6, 70053.8),
    ("03-26 11:00", 70053.8, 70095.7, 69769.7, 69985.9),
    ("03-26 12:00", 69986.0, 70131.5, 69366.0, 69537.6),
    ("03-26 13:00", 69537.6, 69693.7, 69417.0, 69480.0),
    ("03-26 14:00", 69480.0, 69620.0, 69127.2, 69239.3),
    ("03-26 15:00", 69239.3, 69428.0, 69187.4, 69395.1),
    ("03-26 16:00", 69395.2, 69872.2, 69158.9, 69617.4),
    ("03-26 17:00", 69615.8, 69800.0, 69217.0, 69450.1),
    ("03-26 18:00", 69450.0, 69472.6, 68553.4, 69054.8),
    ("03-26 19:00", 69054.9, 69054.9, 68797.8, 68904.8),
    ("03-26 20:00", 68904.8, 69138.8, 68325.2, 68456.1),
    ("03-26 21:00", 68456.2, 68581.3, 68115.8, 68457.0),
    ("03-26 22:00", 68457.0, 68657.4, 68317.9, 68502.7),
    ("03-26 23:00", 68502.7, 69466.6, 68378.5, 68973.8),
    ("03-27 00:00", 68973.9, 69213.3, 68849.8, 68885.8),
    ("03-27 01:00", 68885.8, 69000.0, 68542.5, 68862.5),
    ("03-27 02:00", 68862.5, 68968.9, 68600.0, 68788.0),
    ("03-27 03:00", 68788.1, 68942.2, 68458.5, 68746.4),
    ("03-27 04:00", 68746.4, 69033.3, 68654.8, 69016.4),
    ("03-27 05:00", 69016.5, 69142.7, 68815.5, 68870.8),
    ("03-27 06:00", 68870.8, 68888.4, 68621.5, 68728.8),
    ("03-27 07:00", 68728.8, 68764.5, 68257.2, 68540.2),
    ("03-27 08:00", 68540.1, 68830.0, 68453.6, 68588.8),
    ("03-27 09:00", 68588.8, 68811.0, 68530.6, 68621.5),
    ("03-27 10:00", 68621.5, 68925.0, 68416.5, 68501.7),
    ("03-27 11:00", 68501.8, 68619.9, 67560.0, 67876.6),
    ("03-27 12:00", 67876.7, 67912.1, 67500.2, 67651.9),
    ("03-27 13:00", 67652.0, 67737.9, 66257.4, 66456.4),
    ("03-27 14:00", 66456.4, 66810.9, 66175.4, 66663.2),
    ("03-27 15:00", 66663.3, 66742.2, 66388.0, 66579.4),
    ("03-27 16:00", 66579.4, 66699.9, 65950.0, 66153.9),
    ("03-27 17:00", 66153.9, 66375.2, 65681.5, 66162.7),
    ("03-27 18:00", 66162.7, 66615.0, 65930.3, 66092.0),
    ("03-27 19:00", 66091.9, 66149.6, 65731.8, 65945.5),
    ("03-27 20:00", 65945.5, 66267.4, 65550.0, 65604.0),
    ("03-27 21:00", 65604.0, 65939.1, 65501.0, 65804.0),
    ("03-27 22:00", 65804.0, 66119.6, 65666.6, 66005.4),
    ("03-27 23:00", 66005.5, 66125.8, 65766.1, 65983.0),
    ("03-28 00:00", 65983.1, 66148.0, 65972.6, 66040.3),
    ("03-28 01:00", 66040.4, 66053.2, 65874.4, 65981.1),
    ("03-28 02:00", 65981.1, 66384.0, 65931.5, 66364.2),
    ("03-28 03:00", 66364.1, 66472.4, 66239.9, 66389.9),
    ("03-28 04:00", 66389.9, 66389.9, 66006.1, 66137.1),
    ("03-28 05:00", 66137.2, 66214.0, 65888.0, 66020.1),
    ("03-28 06:00", 66020.0, 66217.5, 66020.0, 66191.8),
    ("03-28 07:00", 66191.8, 66274.7, 66068.3, 66243.5),
    ("03-28 08:00", 66243.6, 66349.0, 66169.0, 66310.0),
    ("03-28 09:00", 66310.0, 66460.0, 66270.9, 66358.2),
    ("03-28 10:00", 66358.1, 66533.9, 66341.3, 66520.8),
    ("03-28 11:00", 66520.9, 66529.4, 66352.1, 66374.9),
    ("03-28 12:00", 66374.9, 66374.9, 66203.5, 66270.9),
    ("03-28 13:00", 66271.0, 66379.9, 66087.3, 66184.9),
    ("03-28 14:00", 66184.9, 66325.7, 66162.0, 66288.5),
    ("03-28 15:00", 66288.4, 66498.1, 66191.7, 66416.7),
    ("03-28 16:00", 66416.7, 67148.7, 66363.6, 66813.3),
    ("03-28 17:00", 66813.4, 66942.3, 66631.5, 66716.2),
    ("03-28 18:00", 66716.1, 67284.0, 66678.1, 66982.3),
    ("03-28 19:00", 66982.4, 67065.0, 66821.3, 66894.3),
    ("03-28 20:00", 66894.3, 66965.7, 66644.0, 66808.6),
    ("03-28 21:00", 66808.6, 66920.0, 66801.0, 66871.1),
    ("03-28 22:00", 66871.2, 66916.5, 66764.7, 66873.0),
    ("03-28 23:00", 66873.0, 66978.0, 66868.3, 66885.5),
    ("03-29 00:00", 66885.6, 66890.0, 66526.8, 66644.8),
    ("03-29 01:00", 66644.9, 66758.9, 66562.0, 66729.0),
    ("03-29 02:00", 66729.0, 66729.0, 66233.6, 66334.8),
    ("03-29 03:00", 66334.8, 66468.6, 66235.6, 66444.4),
    ("03-29 04:00", 66444.3, 66585.9, 66344.2, 66536.1),
    ("03-29 05:00", 66536.0, 66820.0, 66500.4, 66773.7),
    ("03-29 06:00", 66773.7, 67100.0, 66724.0, 66875.7),
    ("03-29 07:00", 66875.7, 66907.5, 66683.3, 66701.9),
    ("03-29 08:00", 66701.9, 66799.5, 66565.0, 66741.3),
    ("03-29 09:00", 66741.3, 66845.0, 66601.1, 66704.4),
    ("03-29 10:00", 66704.4, 66720.0, 66521.4, 66632.5),
    ("03-29 11:00", 66632.4, 66743.7, 66560.0, 66689.5),
    ("03-29 12:00", 66689.4, 66740.0, 66500.9, 66600.1),
    ("03-29 13:00", 66600.0, 66600.0, 66375.5, 66473.4),
    ("03-29 14:00", 66473.4, 66986.8, 66473.3, 66780.8),
    ("03-29 15:00", 66780.8, 66844.3, 66668.0, 66818.6),
    ("03-29 16:00", 66818.7, 66849.0, 66483.9, 66546.0),
    ("03-29 17:00", 66546.1, 66764.9, 66420.0, 66556.2),
    ("03-29 18:00", 66556.3, 66695.0, 66288.1, 66500.0),
    ("03-29 19:00", 66499.9, 66639.0, 66400.0, 66467.8),
    ("03-29 20:00", 66467.8, 66518.2, 66111.0, 66356.6),
    ("03-29 21:00", 66356.6, 66524.0, 66291.2, 66397.2),
    ("03-29 22:00", 66397.1, 66453.4, 66282.1, 66320.2),
    ("03-29 23:00", 66320.3, 66767.9, 66312.7, 66578.6),
    ("03-30 00:00", 66578.6, 66734.5, 66477.5, 66678.8),
    ("03-30 01:00", 66678.8, 66686.1, 64918.2, 65820.3),
    ("03-30 02:00", 65820.2, 66350.4, 65819.0, 65977.9),
    ("03-30 03:00", 65978.0, 67043.2, 65754.2, 66251.2),
    ("03-30 04:00", 66251.2, 66806.1, 66251.1, 66624.1),
    ("03-30 05:00", 66624.2, 67487.7, 66538.5, 67087.0),
    ("03-30 06:00", 67087.1, 67288.8, 66934.7, 67139.8),
    ("03-30 07:00", 67140.0, 67625.1, 67129.3, 67579.1),
    ("03-30 08:00", 67579.2, 67777.0, 67404.0, 67459.0),
    ("03-30 09:00", 67459.0, 67550.0, 67238.6, 67273.4),
    ("03-30 10:00", 67273.5, 67612.6, 67180.5, 67595.9),
    ("03-30 11:00", 67595.9, 67920.0, 67574.6, 67634.0),
    ("03-30 12:00", 67633.9, 67667.9, 67426.0, 67466.2),
    ("03-30 13:00", 67466.2, 67498.0, 67333.3, 67463.0),
    ("03-30 14:00", 67463.1, 67998.0, 67459.7, 67651.5),
    ("03-30 15:00", 67651.5, 67950.0, 67627.7, 67859.3),
    ("03-30 16:00", 67859.4, 68148.4, 67378.7, 67490.9),
    ("03-30 17:00", 67490.8, 67843.8, 67055.0, 67762.7),
    ("03-30 18:00", 67762.8, 67875.0, 67373.7, 67590.2),
    ("03-30 19:00", 67590.2, 67614.9, 67188.0, 67333.0),
    ("03-30 20:00", 67332.9, 67443.8, 66617.3, 66805.2),
    ("03-30 21:00", 66805.1, 66899.9, 66456.4, 66620.6),
    ("03-30 22:00", 66620.6, 66640.0, 66200.1, 66516.0),
    ("03-30 23:00", 66515.9, 66662.6, 66488.7, 66614.9),
    ("03-31 00:00", 66614.9, 66973.5, 66550.0, 66770.6),
    ("03-31 01:00", 66770.6, 66971.2, 66650.9, 66746.5),
    ("03-31 02:00", 66746.4, 66769.1, 66377.1, 66764.4),
    ("03-31 03:00", 66764.4, 67276.0, 66498.9, 67172.5),
    ("03-31 04:00", 67172.5, 68377.0, 67004.2, 67896.2),
    ("03-31 05:00", 67896.1, 68072.7, 67726.9, 67911.8),
    ("03-31 06:00", 67911.8, 67974.8, 67610.5, 67670.8),
    ("03-31 07:00", 67670.8, 67865.7, 67441.8, 67510.1),
    ("03-31 08:00", 67510.1, 67756.8, 67356.4, 67648.9),
    ("03-31 09:00", 67649.0, 67679.5, 67300.1, 67465.4),
    ("03-31 10:00", 67465.4, 67497.0, 67071.9, 67343.8),
    ("03-31 11:00", 67343.9, 67476.9, 66655.0, 66745.1),
    ("03-31 12:00", 66745.1, 66891.8, 65938.0, 66099.3),
    ("03-31 13:00", 66099.3, 66442.0, 66067.0, 66329.4),
    ("03-31 14:00", 66329.4, 66850.0, 66205.0, 66652.4),
    ("03-31 15:00", 66652.4, 66909.3, 66480.0, 66623.8),
    ("03-31 16:00", 66623.8, 67375.0, 66623.8, 67255.6),
    ("03-31 17:00", 67255.6, 67765.8, 66374.4, 66555.9),
    ("03-31 18:00", 66556.0, 67262.2, 66555.9, 66700.0),
    ("03-31 19:00", 66700.0, 67985.5, 66695.9, 67632.6),
    ("03-31 20:00", 67632.6, 68600.0, 67357.1, 67493.9),
    ("03-31 21:00", 67493.8, 67929.7, 67488.0, 67814.6),
    ("03-31 22:00", 67814.5, 67996.0, 67671.3, 67803.0),
    ("03-31 23:00", 67803.0, 68234.0, 67794.8, 68227.2),
    ("04-01 00:00", 68227.3, 68382.9, 67840.4, 68234.6),
    ("04-01 01:00", 68234.7, 68306.9, 67919.5, 68141.6),
    ("04-01 02:00", 68141.7, 68332.6, 68050.0, 68241.5),
    ("04-01 03:00", 68241.4, 68305.1, 67808.1, 68288.0),
    ("04-01 04:00", 68288.0, 68330.0, 67707.5, 67746.4),
    ("04-01 05:00", 67746.4, 67881.2, 67534.9, 67623.8),
    ("04-01 06:00", 67623.9, 68214.5, 67623.9, 68134.0),
    ("04-01 07:00", 68134.0, 68450.0, 67965.0, 68272.3),
    ("04-01 08:00", 68272.3, 68732.5, 68114.5, 68418.2),
    ("04-01 09:00", 68418.3, 69220.0, 68418.2, 69069.1),
    ("04-01 10:00", 69069.1, 69288.0, 68631.1, 68651.9),
    ("04-01 11:00", 68651.9, 68821.5, 68425.5, 68630.8),
    ("04-01 12:00", 68630.9, 68702.3, 68360.0, 68608.4),
    ("04-01 13:00", 68608.4, 68632.1, 68370.1, 68545.1),
    ("04-01 14:00", 68545.2, 68702.3, 68471.5, 68669.9),
    ("04-01 15:00", 68670.0, 68773.9, 68220.9, 68363.8),
    ("04-01 16:00", 68364.1, 68650.0, 67883.7, 68091.4),
    ("04-01 17:00", 68091.4, 68657.1, 68020.0, 68559.1),
    ("04-01 18:00", 68559.2, 68938.8, 68380.3, 68877.0),
    ("04-01 19:00", 68876.9, 68961.6, 68570.0, 68781.1),
    ("04-01 20:00", 68781.1, 69142.6, 68212.1, 68239.7),
    ("04-01 21:00", 68239.7, 68313.8, 67900.4, 68054.2),
    ("04-01 22:00", 68054.2, 68269.9, 68000.0, 68143.8),
    ("04-01 23:00", 68143.7, 68217.8, 67927.0, 68159.8),
    ("04-02 00:00", 68159.7, 68510.6, 68136.5, 68324.7),
    ("04-02 01:00", 68324.8, 68324.8, 68032.9, 68088.4),
    ("04-02 02:00", 68088.5, 68220.9, 67952.2, 68086.5),
    ("04-02 03:00", 68086.4, 68639.1, 68013.3, 68565.1),
    ("04-02 04:00", 68565.2, 68565.2, 67000.3, 67316.4),
    ("04-02 05:00", 67316.4, 67316.4, 66590.0, 66821.6),
    ("04-02 06:00", 66821.6, 66931.9, 66455.9, 66538.4),
    ("04-02 07:00", 66538.4, 66617.7, 66171.8, 66300.2),
    ("04-02 08:00", 66300.2, 66628.8, 66270.0, 66558.2),
    ("04-02 09:00", 66558.2, 66798.9, 66506.4, 66652.9),
    ("04-02 10:00", 66653.0, 66898.5, 66521.4, 66887.9),
    ("04-02 11:00", 66887.8, 66887.9, 66372.9, 66418.2),
    ("04-02 12:00", 66418.1, 66487.7, 66256.0, 66428.6),
    ("04-02 13:00", 66428.7, 66471.9, 66188.1, 66424.0),
    ("04-02 14:00", 66424.1, 66449.7, 66065.1, 66180.6),
    ("04-02 15:00", 66180.6, 66215.2, 65919.1, 66014.2),
    ("04-02 16:00", 66014.3, 66250.0, 65676.1, 66227.3),
    ("04-02 17:00", 66227.3, 66873.8, 66123.0, 66765.8),
    ("04-02 18:00", 66822.3, 66960.7, 66596.2, 66810.6),
    ("04-02 19:00", 66810.6, 67234.4, 66707.6, 67050.1),
    ("04-02 20:00", 67050.0, 67400.0, 66622.4, 66641.4),
    ("04-02 21:00", 66641.4, 67044.8, 66550.0, 66941.6),
    ("04-02 22:00", 66941.7, 67082.9, 66827.8, 66943.2),
    ("04-02 23:00", 66943.2, 67078.9, 66755.6, 66906.3),
    ("04-03 00:00", 66906.4, 66993.4, 66681.3, 66910.7),
    ("04-03 01:00", 66910.7, 67008.5, 66782.0, 66954.0),
    ("04-03 02:00", 66954.0, 67070.2, 66820.6, 66868.5),
    ("04-03 03:00", 66868.6, 66976.2, 66671.0, 66761.8),
    ("04-03 04:00", 66761.8, 66881.3, 66450.0, 66599.0),
    ("04-03 05:00", 66599.1, 66726.7, 66240.0, 66504.6),
    ("04-03 06:00", 66504.6, 66698.5, 66461.0, 66550.0),
    ("04-03 07:00", 66550.1, 66666.0, 66468.0, 66578.8),
    ("04-03 08:00", 66578.8, 66789.6, 66375.1, 66574.9),
    ("04-03 09:00", 66574.9, 66770.0, 66523.2, 66762.0),
    ("04-03 10:00", 66762.1, 67233.3, 66716.4, 67008.8),
    ("04-03 11:00", 67008.8, 67258.0, 66864.1, 66935.0),
    ("04-03 12:00", 66935.1, 66976.0, 66714.3, 66828.9),
    ("04-03 13:00", 66828.9, 66871.9, 66644.0, 66845.3),
    ("04-03 14:00", 66845.3, 67041.9, 66790.6, 66983.4),
    ("04-03 15:00", 66983.5, 67350.0, 66605.9, 66690.4),
    ("04-03 16:00", 66690.4, 66707.1, 66478.5, 66644.6),
    ("04-03 17:00", 66644.6, 66968.1, 66600.0, 66900.0),
    ("04-03 18:00", 66899.9, 66999.0, 66778.9, 66806.1),
    ("04-03 19:00", 66806.0, 67046.1, 66800.0, 66972.5),
    ("04-03 20:00", 66972.5, 67040.0, 66714.1, 66811.0),
    ("04-03 21:00", 66811.0, 66899.7, 66746.9, 66783.7),
    ("04-03 22:00", 66783.6, 66882.9, 66740.6, 66857.0),
    ("04-03 23:00", 66857.0, 66888.0, 66800.0, 66800.1),
    ("04-04 00:00", 66800.0, 66946.3, 66791.8, 66929.5),
    ("04-04 01:00", 66929.4, 66943.0, 66813.0, 66860.0),
    ("04-04 02:00", 66859.9, 66930.0, 66800.7, 66930.0),
    ("04-04 03:00", 66930.0, 66935.3, 66838.9, 66863.4),
    ("04-04 04:00", 66863.4, 66895.7, 66795.8, 66820.0),
    ("04-04 05:00", 66820.0, 66891.4, 66773.3, 66814.1),
    ("04-04 06:00", 66814.0, 66875.4, 66798.8, 66799.1),
    ("04-04 07:00", 66799.1, 66840.0, 66745.5, 66833.5),
    ("04-04 08:00", 66833.5, 66908.4, 66817.8, 66871.0),
    ("04-04 09:00", 66871.0, 67023.7, 66871.0, 66981.5),
    ("04-04 10:00", 66981.5, 67019.1, 66904.0, 66982.0),
    ("04-04 11:00", 66982.1, 67025.0, 66874.5, 66907.8),
    ("04-04 12:00", 66907.8, 66958.2, 66882.1, 66952.1),
    ("04-04 13:00", 66952.1, 67150.3, 66880.9, 67139.1),
    ("04-04 14:00", 67139.1, 67223.8, 67050.0, 67128.9),
    ("04-04 15:00", 67128.9, 67152.5, 67025.2, 67062.0),
    ("04-04 16:00", 67061.9, 67245.3, 67044.8, 67170.0),
    ("04-04 17:00", 67170.0, 67193.3, 67003.7, 67177.6),
    ("04-04 18:00", 67177.5, 67554.5, 67145.6, 67357.3),
    ("04-04 19:00", 67357.4, 67500.0, 67292.0, 67335.2),
    ("04-04 20:00", 67335.1, 67386.0, 67249.9, 67302.3),
    ("04-04 21:00", 67302.3, 67350.0, 67226.4, 67265.7),
    ("04-04 22:00", 67265.6, 67523.8, 67245.6, 67262.7),
    ("04-04 23:00", 67262.8, 67269.4, 67150.6, 67240.2),
    ("04-05 00:00", 67240.2, 67452.7, 67180.9, 67325.0),
    ("04-05 01:00", 67325.0, 67438.7, 67305.4, 67368.9),
    ("04-05 02:00", 67368.9, 67371.4, 67214.2, 67271.0),
    ("04-05 03:00", 67271.1, 67279.2, 67131.1, 67177.0),
    ("04-05 04:00", 67177.0, 67200.0, 67045.2, 67060.6),
    ("04-05 05:00", 67060.6, 67154.0, 66900.0, 67144.3),
    ("04-05 06:00", 67144.3, 67166.9, 67058.0, 67113.5),
    ("04-05 07:00", 67113.4, 67160.0, 67034.8, 67066.2),
    ("04-05 08:00", 67066.3, 67127.5, 66822.8, 66905.1),
    ("04-05 09:00", 66905.2, 66918.6, 66575.5, 66771.6),
    ("04-05 10:00", 66771.6, 66887.1, 66685.3, 66787.4),
    ("04-05 11:00", 66787.4, 66910.0, 66782.1, 66892.5),
    ("04-05 12:00", 66892.6, 67020.4, 66862.3, 66996.0),
    ("04-05 13:00", 66996.1, 67132.8, 66928.1, 67012.3),
    ("04-05 14:00", 67012.4, 67054.1, 66934.4, 66972.7),
    ("04-05 15:00", 66972.7, 66972.7, 66650.0, 66751.4),
    ("04-05 16:00", 66751.5, 66892.9, 66666.0, 66863.4),
    ("04-05 17:00", 66863.5, 66940.2, 66783.1, 66892.5),
    ("04-05 18:00", 66892.6, 67828.6, 66792.6, 67272.2),
    ("04-05 19:00", 67272.2, 67381.0, 67132.2, 67178.8),
    ("04-05 20:00", 67178.9, 67376.3, 67150.0, 67342.2),
    ("04-05 21:00", 67342.2, 67428.2, 67246.6, 67381.1),
    ("04-05 22:00", 67381.2, 67540.0, 67250.0, 67329.1),
    ("04-05 23:00", 67329.1, 67681.6, 67302.4, 67636.7),
    ("04-06 00:00", 67636.7, 67672.9, 67377.2, 67519.5),
    ("04-06 01:00", 67519.5, 68347.9, 67313.6, 68313.0),
    ("04-06 02:00", 68313.0, 69108.0, 68232.0, 68997.9),
    ("04-06 03:00", 68997.9, 69583.0, 68997.9, 69051.9),
    ("04-06 04:00", 69051.9, 69103.1, 68761.0, 68782.9),
    ("04-06 05:00", 68782.9, 69386.2, 68740.2, 69183.6),
    ("04-06 06:00", 69183.6, 69223.4, 69026.6, 69092.4),
    ("04-06 07:00", 69092.3, 69188.0, 68943.3, 69107.6),
    ("04-06 08:00", 69107.6, 69214.5, 69052.0, 69167.1),
    ("04-06 09:00", 69167.0, 69338.2, 68769.6, 68958.7),
    ("04-06 10:00", 68958.8, 69190.8, 68800.0, 69089.7),
    ("04-06 11:00", 69089.8, 69225.0, 69047.7, 69191.6),  # ACIK
    # ↑↑↑ YENİ 1H MUMLAR BURAYA EKLE ↑↑↑

    ("04-06 12:00", 69583.5, 69602.4, 69283.0, 69337.3),
    ("04-06 13:00", 69337.4, 69521.4, 69200.1, 69399.8),
    ("04-06 14:00", 69399.7, 69791.3, 69088.0, 69620.0),
    ("04-06 15:00", 69620.0, 69931.9, 69490.0, 69922.5),
    ("04-06 16:00", 69922.4, 70332.5, 69737.6, 69759.2),
    ("04-06 17:00", 69759.2, 69778.4, 69240.0, 69540.6),
    ("04-06 18:00", 69540.6, 69955.3, 69436.4, 69852.9),
    ("04-06 19:00", 69852.8, 69862.2, 69543.8, 69704.8),
    ("04-06 20:00", 69704.8, 69940.0, 69578.0, 69779.4),
    ("04-06 21:00", 69779.5, 69784.3, 69400.0, 69476.5),
    ("04-06 22:00", 69476.5, 69554.2, 68777.0, 68777.1),
    ("04-06 23:00", 68777.0, 68880.1, 68227.5, 68817.9),
    ("04-07 00:00", 68817.9, 69111.8, 68682.7, 68738.7),
    ("04-07 01:00", 68738.6, 68878.3, 68291.0, 68363.9),
    ("04-07 02:00", 68363.9, 68684.6, 68241.9, 68640.3),
    ("04-07 03:00", 68640.3, 68780.0, 68586.5, 68746.3),
    ("04-07 04:00", 68746.4, 68955.6, 68510.5, 68819.3),
    ("04-07 05:00", 68819.2, 68831.0, 68577.6, 68627.5),
    ("04-07 06:00", 68627.4, 68635.9, 68400.6, 68540.0),
    ("04-07 07:00", 68539.9, 68677.8, 68470.0, 68592.1),
    ("04-07 08:00", 68592.0, 68963.4, 68570.7, 68907.1),

    ("04-07 09:00", 68907.1, 69219.0, 68900.0, 69109.8),
    ("04-07 10:00", 69109.9, 69170.0, 68151.8, 68196.0),
    ("04-07 11:00", 68196.1, 68430.1, 68033.0, 68310.8),
    ("04-07 12:00", 68310.7, 68579.3, 68039.8, 68367.0),
    ("04-07 13:00", 68366.9, 68613.8, 68168.0, 68208.1),

    ("04-07 14:00", 68208.1, 68232.1, 67741.0, 67831.0),
    ("04-07 15:00", 67831.1, 68250.0, 67711.0, 68138.4),
    ("04-07 16:00", 68138.5, 68431.8, 68049.9, 68207.2),
    ("04-07 17:00", 68207.2, 68996.0, 68164.5, 68670.0),
    ("04-07 18:00", 68670.1, 68746.7, 68318.1, 68413.7),
    ("04-07 19:00", 68413.7, 69068.6, 68315.3, 68975.9),
    ("04-07 20:00", 68975.9, 69500.0, 68975.9, 69285.2),
    ("04-07 21:00", 69285.3, 70200.0, 69273.3, 69886.7),
    ("04-07 22:00", 69886.7, 71499.9, 69886.6, 71479.9),
    ("04-07 23:00", 71479.9, 72743.4, 71155.0, 71890.2),
    ("04-08 00:00", 71890.2, 72086.4, 71505.2, 71681.9),
    ("04-08 01:00", 71681.9, 71732.6, 71416.9, 71446.5),
    ("04-08 02:00", 71446.5, 71698.0, 71186.0, 71330.0),
    ("04-08 03:00", 71329.9, 71449.9, 71231.3, 71259.6),
    ("04-08 04:00", 71259.7, 71649.8, 71250.0, 71528.6),
    ("04-08 05:00", 71528.6, 71797.0, 71516.3, 71701.6),
    ("04-08 06:00", 71701.5, 71919.0, 71539.2, 71697.5),
    ("04-08 07:00", 71697.4, 71873.7, 71551.8, 71612.0),
    ("04-08 08:00", 71612.1, 71808.5, 71612.0, 71776.0),
    ("04-08 09:00", 71776.0, 71945.0, 71555.3, 71655.4),
    ("04-08 10:00", 71655.4, 71782.1, 71415.3, 71445.7),
    ("04-08 11:00", 71445.7, 71687.6, 71367.0, 71650.2),
    ("04-08 12:00", 71650.2, 72169.5, 71542.6, 72023.6),

    ("04-09 03:00", 71029.6, 71091.9, 70818.0, 70961.2),
    ("04-09 04:00", 70961.2, 70980.5, 70700.0, 70760.1),
    ("04-09 05:00", 70760.1, 71063.0, 70666.0, 70959.7),
    ("04-09 06:00", 70959.6, 71058.6, 70780.1, 70998.8),
    ("04-09 07:00", 70998.8, 71087.8, 70913.5, 70945.0),
    ("04-09 08:00", 70945.0, 71342.0, 70831.9, 71207.6),
    ("04-09 09:00", 71207.5, 71533.0, 71060.9, 71488.7),
    ("04-09 10:00", 71488.7, 71498.9, 71234.7, 71234.7),
    ("04-09 11:00", 71234.7, 71317.0, 71007.8, 71109.9),
    ("04-09 12:00", 71109.9, 71299.6, 70978.8, 71245.0),
    ("04-09 13:00", 71244.9, 71320.0, 70590.0, 70765.2),
    ("04-09 14:00", 70765.2, 71224.5, 70470.2, 71083.5),
    ("04-09 15:00", 71083.4, 72320.0, 70887.8, 72108.0),
    ("04-09 16:00", 72108.0, 72377.4, 71688.8, 72048.0),
    ("04-09 17:00", 72048.1, 72517.9, 72028.2, 72306.9),
    ("04-09 18:00", 72307.0, 72339.0, 71705.0, 71849.3),
    ("04-09 19:00", 71849.3, 72267.3, 71701.3, 72055.9),
    ("04-09 20:00", 72055.8, 72419.8, 71945.0, 72377.6),
    ("04-09 21:00", 72377.6, 72666.6, 72102.5, 72230.1),
    ("04-09 22:00", 72230.2, 73128.0, 71911.1, 71911.2),
    ("04-09 23:00", 71911.1, 71999.0, 71539.9, 71750.4),
    ("04-10 00:00", 71750.4, 71995.8, 71546.0, 71932.3),
    ("04-10 01:00", 71932.3, 72350.0, 71620.6, 72124.0),
    ("04-10 02:00", 72124.0, 72255.0, 71882.3, 71926.3),
    ("04-10 03:00", 71926.2, 71993.0, 71770.5, 71837.3),
    ("04-10 04:00", 71837.3, 72199.9, 71781.9, 72088.8),
    ("04-10 05:00", 72088.8, 72243.6, 71973.8, 72098.6),
    ("04-10 06:00", 72098.4, 72154.8, 71759.0, 71778.1),
    ("04-10 07:00", 71778.1, 71821.1, 71382.1, 71461.2),
    ("04-10 08:00", 71461.2, 71730.0, 71395.0, 71571.6),
    ("04-10 09:00", 71571.6, 71840.8, 71555.8, 71746.2),
    ("04-10 10:00", 71746.1, 71910.0, 71658.8, 71872.4),
    ("04-10 11:00", 71872.5, 72229.0, 71861.5, 72092.7),
    ("04-10 12:00", 72092.8, 72467.3, 71960.5, 72225.5),

    ("04-10 13:00", 72225.4, 72381.0, 71868.5, 72284.0),
    ("04-10 14:00", 72283.9, 73123.9, 72209.8, 72870.6),
    ("04-10 15:00", 72870.6, 73255.7, 72309.5, 72421.0),
    ("04-10 16:00", 72421.1, 73024.1, 72350.0, 72954.0),

    ("04-11 15:00", 72660.8, 72869.9, 72638.8, 72817.3),
    ("04-11 16:00", 72817.3, 73180.0, 72775.3, 72991.3),
    ("04-11 17:00", 72991.3, 73140.8, 72900.1, 73056.2),
    ("04-11 18:00", 73056.2, 73700.0, 72990.2, 73515.9),
    ("04-11 19:00", 73515.9, 73773.4, 73400.4, 73635.9),
    ("04-11 20:00", 73635.9, 73648.8, 73183.5, 73252.9),
    ("04-11 21:00", 73252.8, 73500.0, 73155.0, 73384.7),
    ("04-11 22:00", 73384.7, 73529.0, 73183.4, 73333.3),
    ("04-11 23:00", 73333.3, 73333.4, 72861.2, 73013.4),
    ("04-12 00:00", 73013.4, 73077.6, 72817.4, 73038.8),
    ("04-12 01:00", 73038.7, 73094.4, 71259.0, 71598.7),
    ("04-12 02:00", 71598.7, 72000.0, 71302.0, 71723.7),
    ("04-12 03:00", 71723.7, 71831.8, 71556.3, 71563.6),
    ("04-12 04:00", 71563.6, 71656.3, 71407.7, 71428.7),
    ("04-12 05:00", 71428.7, 71750.0, 71369.7, 71665.1),
    ("04-12 06:00", 71665.0, 71728.0, 71602.0, 71618.9),
    ("04-12 07:00", 71618.8, 71716.2, 71541.4, 71628.1),
    ("04-12 08:00", 71628.2, 71750.0, 71555.0, 71592.3),
    ("04-12 09:00", 71592.4, 71600.0, 71461.7, 71502.4),
    ("04-12 10:00", 71502.3, 71655.2, 71309.7, 71416.1),
    ("04-12 11:00", 71416.1, 71510.0, 71384.3, 71435.0),
    ("04-12 12:00", 71435.0, 71478.0, 71000.0, 71050.1),
    ("04-12 13:00", 71050.0, 71117.2, 70818.7, 70861.5),
    ("04-12 14:00", 70861.4, 71063.8, 70655.6, 70714.3),
    ("04-12 15:00", 70714.3, 70898.0, 70566.5, 70856.2),
    ("04-12 16:00", 70856.1, 70926.7, 70777.0, 70890.9),
    ("04-12 17:00", 70890.8, 71188.0, 70853.1, 71099.9),
    ("04-12 18:00", 71100.0, 71177.3, 71010.0, 71092.6),
    ("04-12 19:00", 71092.5, 71199.0, 71034.6, 71055.2),
    ("04-12 20:00", 71055.2, 71417.9, 70920.4, 71302.9),
    ("04-12 21:00", 71302.8, 71423.9, 71110.3, 71331.7),
    ("04-12 22:00", 71331.4, 71332.4, 70458.2, 70875.6),
    ("04-12 23:00", 70875.5, 70882.4, 70533.0, 70711.1),
    ("04-13 00:00", 70711.2, 71225.0, 70574.0, 71130.0),

    ("04-14 00:00", 74384.9, 74493.4, 74057.7, 74127.9),
    ("04-14 01:00", 74127.9, 74400.0, 73946.9, 74345.5),
    ("04-14 02:00", 74345.5, 74583.1, 74236.1, 74294.4),
    ("04-14 03:00", 74294.5, 74461.9, 74212.8, 74408.8),
    ("04-14 04:00", 74408.8, 74476.1, 74316.9, 74355.5),
    ("04-14 05:00", 74355.5, 74401.8, 74112.2, 74184.5),
    ("04-14 06:00", 74184.5, 74519.9, 74184.5, 74485.0),
    ("04-14 07:00", 74485.1, 74900.0, 74395.6, 74513.4),
    ("04-14 08:00", 74513.3, 74873.5, 74419.1, 74713.9),
    ("04-14 09:00", 74714.0, 74799.5, 74403.1, 74471.9),
    ("04-14 10:00", 74471.9, 74581.7, 74300.0, 74309.8),
    ("04-14 11:00", 74309.8, 74430.0, 74267.2, 74342.4),
    ("04-14 12:00", 74342.4, 74459.6, 74234.0, 74416.7),
    ("04-14 13:00", 74416.7, 75484.0, 74366.0, 75471.2),
    ("04-14 14:00", 75471.1, 76009.0, 74964.7, 74966.3),
    ("04-14 15:00", 74966.3, 75396.9, 74514.1, 75268.1),
    ("04-14 16:00", 75268.1, 75684.9, 74450.0, 74597.1),
    ("04-14 17:00", 74597.2, 74902.7, 74200.2, 74699.9),
    ("04-14 18:00", 74699.9, 74765.0, 73789.7, 74050.0),
    ("04-14 19:00", 74049.9, 74362.8, 73833.5, 74176.4),
    ("04-14 20:00", 74176.5, 74387.7, 73960.0, 74059.0),
    ("04-14 21:00", 74058.9, 74295.7, 73903.8, 74230.3),
    ("04-14 22:00", 74230.3, 74339.4, 73766.8, 73987.5),
    ("04-14 23:00", 73987.6, 74200.1, 73961.3, 74106.9),
    ("04-15 00:00", 74106.9, 74635.0, 74085.0, 74520.3),
    ("04-15 01:00", 74520.3, 74739.2, 74450.8, 74568.3),
    ("04-15 02:00", 74568.3, 74653.4, 74142.7, 74280.0),
    ("04-15 03:00", 74280.0, 74338.9, 74123.6, 74296.8),
    ("04-15 04:00", 74296.8, 74400.0, 74211.3, 74290.8),
    ("04-15 05:00", 74290.7, 74390.0, 73822.6, 73983.2),
    ("04-15 06:00", 73983.1, 74015.7, 73822.0, 73851.1),
    ("04-15 07:00", 73851.0, 73987.0, 73449.0, 73705.1),
    ("04-15 08:00", 73705.2, 74154.3, 73640.1, 74070.4),
    ("04-15 09:00", 74070.4, 74143.5, 73868.0, 73968.3),

    ("04-15 10:00", 73968.3, 74222.7, 73750.0, 73825.9),

    ("04-15 11:00", 73825.9, 74227.5, 73825.9, 74155.1),
    ("04-15 12:00", 74155.0, 74473.5, 74001.1, 74228.7),
    ("04-15 13:00", 74228.8, 74397.0, 73769.5, 74015.8),
    ("04-15 14:00", 74015.9, 74466.0, 73776.5, 74108.8),
    ("04-15 15:00", 74108.8, 74290.0, 73540.0, 73797.5),
    ("04-15 16:00", 73797.5, 74145.2, 73714.9, 73900.4),
    ("04-15 17:00", 73900.3, 74197.1, 73873.8, 74099.1),
    ("04-15 18:00", 74099.0, 74369.2, 74028.0, 74349.1),
    ("04-15 19:00", 74349.1, 75240.0, 74311.9, 74957.8),
    ("04-15 20:00", 74957.7, 74991.5, 74466.5, 74796.8),
    ("04-15 21:00", 74796.7, 74816.0, 74498.6, 74703.0),
    ("04-15 22:00", 74703.1, 75425.6, 74696.0, 74931.3),
    ("04-15 23:00", 74931.3, 74932.1, 74579.0, 74776.2),
    ("04-16 00:00", 74776.3, 74839.0, 74400.0, 74772.0),
    ("04-16 01:00", 74772.1, 74772.1, 74415.0, 74612.8),
    ("04-16 02:00", 74612.8, 75232.7, 74556.7, 74840.8),
    ("04-16 03:00", 74840.7, 75123.5, 74825.1, 74851.9),
    ("04-16 04:00", 74851.9, 75130.0, 74675.4, 74899.9),
    ("04-16 05:00", 74900.0, 75100.0, 74852.4, 75006.1),
    ("04-16 06:00", 75006.0, 75079.1, 74801.8, 74985.9),
    ("04-16 07:00", 74985.9, 75039.0, 74590.3, 74667.7),
    ("04-16 08:00", 74667.7, 74711.8, 74466.9, 74634.3),

    ("04-17 02:00", 74707.7, 74770.0, 74480.0, 74670.6),
    ("04-17 03:00", 74670.5, 74814.1, 74558.9, 74582.8),
    ("04-17 04:00", 74582.8, 74818.1, 74550.0, 74748.4),
    ("04-17 05:00", 74748.3, 74770.5, 74508.2, 74604.8),
    ("04-17 06:00", 74604.8, 74904.2, 74559.7, 74895.1),
    ("04-17 07:00", 74895.2, 75060.4, 74892.7, 75047.4),
    ("04-17 08:00", 75047.4, 75869.0, 74951.6, 75749.8),
    ("04-17 09:00", 75749.8, 76350.0, 75463.2, 75746.0),
    ("04-17 10:00", 75746.1, 75853.7, 75030.2, 75229.7),
    ("04-17 11:00", 75229.6, 75564.7, 75195.7, 75542.2),
    ("04-17 12:00", 75542.1, 76235.4, 75481.8, 76195.6),
    ("04-17 13:00", 76195.7, 77376.3, 76006.7, 77294.3),
    ("04-17 14:00", 77294.2, 77999.9, 76951.1, 77825.1),
    ("04-17 15:00", 77825.1, 77940.0, 77389.0, 77736.2),
    ("04-17 16:00", 77736.2, 78300.0, 77660.0, 77805.1),
    ("04-17 17:00", 77805.1, 77870.0, 77042.0, 77465.3),
    ("04-17 18:00", 77465.3, 77521.3, 77028.4, 77112.1),
    ("04-17 19:00", 77112.0, 77429.8, 76921.9, 77348.8),
    ("04-17 20:00", 77349.2, 77566.0, 77111.0, 77283.7),
    ("04-17 21:00", 77283.7, 77459.0, 77228.6, 77400.1),
    ("04-17 22:00", 77400.0, 77477.1, 77222.1, 77261.8),
    ("04-17 23:00", 77261.9, 77267.0, 76854.2, 77030.6),
    ("04-18 00:00", 77030.6, 77216.2, 76931.0, 77135.1),
    ("04-18 01:00", 77135.2, 77287.9, 77072.7, 77175.9),
    ("04-18 02:00", 77175.9, 77380.0, 77085.6, 77249.5),
    ("04-18 03:00", 77249.6, 77254.3, 76903.2, 76964.3),
    ("04-18 04:00", 76964.4, 77131.8, 76824.1, 77065.9),
    ("04-18 05:00", 77065.8, 77233.6, 77063.5, 77085.0),
    ("04-18 06:00", 77085.1, 77177.0, 77008.0, 77078.7),
    ("04-18 07:00", 77078.7, 77086.5, 76826.8, 76951.0),
    ("04-18 08:00", 76951.0, 77004.2, 76460.0, 76695.1),
    ("04-18 09:00", 76695.1, 76695.1, 76357.1, 76557.1),
    ("04-18 10:00", 76557.1, 76557.2, 76091.8, 76150.0),
    ("04-18 11:00", 76150.0, 76150.0, 75710.6, 76002.0),

    ("04-18 12:00", 76002.0, 76277.4, 76000.0, 76168.0),
    ("04-18 13:00", 76168.0, 76176.0, 75738.0, 76080.5),
    ("04-18 14:00", 76080.5, 76268.2, 75924.4, 76211.2),
    ("04-18 15:00", 76211.2, 76342.7, 75931.9, 76124.8),
    ("04-18 16:00", 76124.8, 76176.6, 75584.1, 75897.9),
    ("04-18 17:00", 75897.9, 75930.5, 75724.8, 75783.9),

    ("04-18 18:00", 75783.9, 75805.1, 75395.9, 75603.7),

    ("04-18 19:00", 75603.7, 75761.1, 75532.3, 75604.2),
    ("04-18 20:00", 75604.2, 75799.9, 75558.6, 75706.1),
    ("04-18 21:00", 75706.1, 75795.0, 75551.0, 75766.5),
    ("04-18 22:00", 75766.4, 75836.9, 75560.0, 75765.5),
    ("04-18 23:00", 75765.5, 75843.3, 75653.4, 75653.8),
    ("04-19 00:00", 75653.8, 75804.0, 75506.1, 75627.3),
    ("04-19 01:00", 75627.4, 75757.7, 75408.5, 75577.4),
    ("04-19 02:00", 75577.4, 75692.3, 75353.0, 75450.1),
    ("04-19 03:00", 75450.0, 75607.9, 75314.0, 75473.0),
    ("04-19 04:00", 75472.9, 75747.3, 75371.6, 75623.7),
    ("04-19 05:00", 75623.7, 75650.0, 75466.3, 75505.1),
    ("04-19 06:00", 75505.1, 75505.1, 75234.2, 75359.7),
    ("04-19 07:00", 75359.6, 75363.2, 74824.3, 75205.6),

    ("04-19 08:00", 75205.7, 75250.0, 75024.3, 75220.0),
    ("04-19 09:00", 75220.1, 75232.1, 74863.6, 74974.6),
    ("04-19 10:00", 74974.6, 75199.0, 74888.0, 75175.5),
    ("04-19 11:00", 75175.5, 75589.2, 75170.0, 75557.4),

    ("04-19 12:00", 75557.5, 75665.7, 75386.4, 75529.3),
    ("04-19 13:00", 75529.2, 76200.0, 75505.1, 75877.9),
    ("04-19 14:00", 75878.0, 76100.0, 75625.9, 75971.3),

    ("04-19 15:00", 75971.4, 76116.8, 75342.3, 75807.6),
    ("04-19 16:00", 75807.7, 75817.7, 75255.7, 75345.6),

    ("04-19 17:00", 75345.5, 75348.4, 74560.0, 74742.4),

    ("04-19 18:00", 74742.3, 74876.9, 74550.0, 74736.2),
    ("04-19 19:00", 74736.2, 75043.1, 74736.2, 74917.9),
    ("04-19 20:00", 74918.0, 74920.2, 74375.0, 74591.6),
    ("04-19 21:00", 74591.7, 74776.3, 74304.5, 74379.5),
    ("04-19 22:00", 74379.4, 74379.5, 73700.2, 74005.0),
    ("04-19 23:00", 74005.0, 74018.6, 73746.4, 73758.4),
    ("04-20 00:00", 73758.4, 74322.9, 73669.0, 74228.1),

    ("04-20 01:00", 74228.1, 74697.6, 74167.6, 74549.4),
    ("04-20 02:00", 74549.5, 74588.3, 74254.9, 74364.5),
    ("04-20 03:00", 74364.5, 74600.0, 74309.8, 74593.9),
    ("04-20 04:00", 74593.9, 74598.1, 74389.1, 74523.7),
    ("04-20 05:00", 74523.7, 74523.7, 74061.2, 74226.5),
    ("04-20 06:00", 74226.5, 74860.0, 74206.7, 74751.1),
    ("04-20 07:00", 74751.2, 75539.3, 74618.0, 74795.5),
    ("04-20 08:00", 74795.5, 74970.5, 74563.2, 74691.7),
    ("04-20 09:00", 74691.7, 75200.0, 74660.8, 75028.8),
    ("04-20 10:00", 75028.9, 75375.1, 74964.8, 74993.2),
    ("04-20 11:00", 74993.3, 75243.0, 74907.1, 75148.7),
    ("04-20 12:00", 75148.8, 75633.0, 74939.1, 75245.0),
    ("04-20 13:00", 75245.1, 75392.0, 74811.7, 75232.8),

    ("04-20 14:00", 75232.7, 75734.0, 74873.1, 75000.1),
    ("04-20 15:00", 75000.1, 75750.0, 74639.5, 75668.1),
    ("04-20 16:00", 75668.1, 75676.3, 75250.0, 75300.0),
    ("04-20 17:00", 75300.0, 75975.4, 75242.5, 75853.7),
    ("04-20 18:00", 75853.7, 76439.0, 75853.7, 76388.8),
    ("04-20 19:00", 76389.3, 76449.8, 76105.6, 76252.5),

    ("04-20 20:00", 76252.5, 76531.0, 76072.9, 76229.9),

    ("04-20 21:00", 76230.0, 76323.9, 75721.7, 75909.5),
    ("04-20 22:00", 75909.4, 76105.4, 75851.1, 75927.7),
    ("04-20 23:00", 75927.7, 75927.7, 75556.2, 75790.1),
    ("04-21 00:00", 75790.1, 76054.0, 75650.0, 76050.0),
    ("04-21 01:00", 76049.9, 76232.3, 75798.6, 75887.0),
    ("04-21 02:00", 75887.1, 75889.9, 75532.0, 75540.0),
    ("04-21 03:00", 75540.0, 75680.0, 75433.1, 75669.1),
    ("04-21 04:00", 75669.1, 75790.3, 75558.8, 75768.3),
    ("04-21 05:00", 75768.2, 75947.1, 75732.3, 75760.8),
    ("04-21 06:00", 75760.7, 76088.0, 75658.3, 75930.5),
    ("04-21 07:00", 75930.4, 76276.6, 75770.0, 76050.0),
    ("04-21 08:00", 76050.0, 76999.0, 76025.0, 76462.4),
    ("04-21 09:00", 76462.4, 76565.2, 76103.3, 76324.2),
    ("04-21 10:00", 76324.2, 76844.5, 76306.3, 76702.1),

    ("04-21 11:00", 76702.2, 76716.7, 76281.1, 76408.3),

    ("04-21 12:00", 76408.3, 76491.1, 75631.2, 75972.8),

    ("04-21 13:00", 75972.9, 76144.0, 75688.0, 75859.9),
    ("04-21 14:00", 75860.0, 76574.3, 75571.7, 75628.9),
    ("04-21 15:00", 75628.9, 75950.2, 75355.2, 75799.9),
    ("04-21 16:00", 75800.0, 76155.0, 75705.4, 75739.2),
    ("04-21 17:00", 75739.3, 75875.1, 75017.8, 75516.0),
    ("04-21 18:00", 75515.9, 75639.6, 75273.0, 75563.1),

    ("04-21 19:00", 75563.1, 75900.0, 74777.9, 74988.6),

    ("04-21 20:00", 74988.7, 75824.8, 74942.2, 75649.4),
    ("04-21 21:00", 75649.3, 75732.5, 75402.9, 75506.4),
    ("04-21 22:00", 75506.4, 75608.6, 75250.0, 75598.6),
    ("04-21 23:00", 75598.6, 76396.2, 75570.3, 76288.2),
    ("04-22 00:00", 76288.3, 76471.2, 76170.0, 76327.1),
    ("04-22 01:00", 76327.1, 76380.0, 76078.6, 76267.3),
    ("04-22 02:00", 76267.4, 77613.0, 76183.7, 77568.1),
    ("04-22 03:00", 77568.0, 77699.0, 77366.0, 77488.3),
    ("04-22 04:00", 77488.4, 77670.8, 77321.7, 77475.5),
    ("04-22 05:00", 77475.4, 78447.5, 77406.0, 77954.4),
    ("04-22 06:00", 77954.4, 78008.8, 77860.0, 77971.6),
    ("04-22 07:00", 77971.5, 78098.0, 77774.3, 77979.8),
    ("04-22 08:00", 77979.7, 78186.0, 77895.3, 77970.0),
    ("04-22 09:00", 77970.0, 78152.8, 77912.1, 77959.9),

    ("04-22 10:00", 77959.9, 78151.0, 77908.6, 78117.8),

    ("04-22 11:00", 78117.8, 78365.8, 78054.5, 78263.2),

    ("04-22 12:00", 78263.2, 78490.8, 78060.0, 78196.6),
    ("04-22 13:00", 78196.6, 78799.0, 78120.1, 78794.5),

    ("04-22 14:00", 78794.4, 79142.8, 78511.1, 78996.8),

    ("04-22 15:00", 78996.7, 79370.0, 78800.3, 79234.3),
    ("04-22 16:00", 79234.3, 79444.0, 78586.7, 78705.1),

    ("04-22 17:00", 78705.1, 78998.6, 78660.0, 78869.8),

    ("04-22 18:00", 78869.8, 79129.8, 78783.7, 78989.5),

    ("04-22 19:00", 78989.5, 79020.0, 78654.6, 78791.3),

    ("04-22 20:00", 78791.3, 78868.9, 78360.0, 78395.8),
    ("04-22 21:00", 78395.8, 78788.3, 78361.4, 78713.8),
    ("04-22 22:00", 78713.9, 78784.0, 78403.2, 78552.1),
    ("04-22 23:00", 78552.1, 78559.2, 78111.6, 78139.8),
    ("04-23 00:00", 78139.7, 78534.9, 77526.8, 78389.9),
    ("04-23 01:00", 78390.0, 78445.2, 78015.0, 78311.0),
    ("04-23 02:00", 78310.9, 78320.0, 77715.0, 77897.6),
    ("04-23 03:00", 77897.6, 77991.7, 77410.7, 77704.3),
    ("04-23 04:00", 77704.3, 77912.0, 77627.4, 77871.6),
    ("04-23 05:00", 77871.5, 78093.2, 77724.4, 77991.9),
    ("04-23 06:00", 77992.0, 78310.1, 77992.0, 78167.0),
    ("04-23 07:00", 78167.0, 78210.9, 77925.9, 78009.1),

    ("04-23 08:00", 78009.1, 78142.2, 77680.0, 77822.1),
    ("04-23 09:00", 77822.1, 77830.0, 77400.2, 77613.0),
    ("04-23 10:00", 77613.0, 77678.3, 76504.6, 77362.9),
    ("04-23 11:00", 77363.0, 77709.1, 77321.6, 77649.9),

    ("04-23 12:00", 77650.0, 77837.6, 77460.4, 77826.8),

    ("04-23 13:00", 77826.8, 77875.7, 77322.8, 77486.7),
    ("04-23 14:00", 77486.6, 78176.0, 77378.4, 78132.8),
    ("04-23 15:00", 78132.8, 78648.0, 77929.0, 78329.2),
    ("04-23 16:00", 78329.3, 78466.8, 77965.8, 78049.0),

    ("04-23 17:00", 78049.1, 78137.8, 76900.1, 77715.2),

    ("04-23 18:00", 77715.1, 78100.0, 77617.8, 77631.7),
    ("04-23 19:00", 77631.5, 77859.9, 77543.4, 77670.5),
    ("04-23 20:00", 77670.4, 78020.0, 77598.4, 77841.3),
    ("04-23 21:00", 77841.3, 78044.2, 77743.3, 77819.6),
    ("04-23 22:00", 77819.5, 78299.0, 77819.5, 78194.2),
    ("04-23 23:00", 78194.1, 78266.0, 77983.5, 78216.8),
    ("04-24 00:00", 78217.4, 78459.1, 78120.0, 78376.7),
    ("04-24 01:00", 78376.7, 78399.0, 77901.0, 78369.9),
    ("04-24 02:00", 78369.8, 78546.0, 77986.0, 78074.0),
    ("04-24 03:00", 78074.0, 78134.0, 77500.0, 77690.1),
    ("04-24 04:00", 77690.1, 77814.7, 77413.0, 77620.5),
    ("04-24 05:00", 77620.5, 78019.2, 77401.5, 77911.0),
    ("04-24 06:00", 77911.1, 77945.0, 77704.0, 77741.9),
    ("04-24 07:00", 77742.0, 77814.0, 77500.0, 77620.5),

    ("04-24 08:00", 77620.5, 77987.2, 77530.1, 77744.6),

    ("04-24 09:00", 77744.6, 77773.9, 77355.8, 77497.2),

    ("04-24 10:00", 77497.2, 77765.5, 77410.0, 77715.2),
    ("04-24 11:00", 77715.2, 78346.1, 77715.1, 78194.8),

    ("04-24 12:00", 78194.9, 78309.2, 77963.6, 78233.0),

    ("04-24 13:00", 78233.0, 78432.9, 77870.0, 78050.1),
    ("04-24 14:00", 78050.0, 78060.5, 77639.0, 77986.4),
    ("04-24 15:00", 77986.3, 78199.0, 77521.0, 78007.3),
    ("04-24 16:00", 78007.3, 78031.9, 77543.4, 77732.7),
    ("04-24 17:00", 77732.6, 77792.9, 77414.4, 77644.6),

    ("04-24 18:00", 77644.5, 77681.6, 77308.0, 77579.2),
    ("04-24 19:00", 77579.2, 77711.0, 77485.1, 77596.1),

    ("04-24 20:00", 77596.0, 77727.0, 77412.8, 77688.2),

    ("04-24 21:00", 77688.2, 77718.5, 77490.0, 77490.1),
    ("04-24 22:00", 77490.0, 77579.9, 77206.8, 77294.5),

    ("04-24 23:00", 77294.6, 77439.1, 77288.9, 77395.4),
    ("04-25 00:00", 77395.3, 77459.7, 77254.7, 77419.9),
    ("04-25 01:00", 77420.0, 77579.3, 77392.7, 77490.0),
    ("04-25 02:00", 77490.0, 77608.2, 77450.0, 77567.6),

    ("04-25 03:00", 77567.6, 77678.0, 77500.0, 77629.0),
    ("04-25 04:00", 77629.0, 77653.2, 77545.0, 77579.5),
    ("04-25 05:00", 77579.5, 77579.5, 77438.1, 77475.8),
    ("04-25 06:00", 77475.8, 77547.0, 77437.0, 77458.8),
    ("04-25 07:00", 77458.9, 77533.2, 77400.0, 77449.9),
    ("04-25 08:00", 77449.9, 77615.6, 77444.0, 77603.3),
    ("04-25 09:00", 77603.4, 77736.8, 77536.2, 77672.5),
    ("04-25 10:00", 77672.6, 77847.0, 77672.5, 77749.3),
    ("04-25 11:00", 77749.3, 77749.3, 77564.0, 77638.7),
    ("04-25 12:00", 77638.7, 77673.0, 77500.1, 77518.3),
    ("04-25 13:00", 77518.3, 77676.5, 77518.3, 77650.1),
    ("04-25 14:00", 77650.1, 77719.1, 77589.8, 77618.2),
    ("04-25 15:00", 77618.3, 77691.1, 77263.0, 77289.3),

    ("04-25 16:00", 77289.3, 77411.8, 77100.0, 77364.0),

    ("04-25 17:00", 77364.0, 77379.7, 77162.0, 77213.4),

    ("04-25 18:00", 77213.3, 77353.6, 77174.2, 77256.8),

    ("04-25 19:00", 77256.8, 77312.6, 77153.0, 77285.6),
    ("04-25 20:00", 77285.7, 77450.0, 77267.3, 77439.1),

    ("04-25 21:00", 77439.0, 77500.0, 77367.0, 77492.9),
    ("04-25 22:00", 77492.9, 77599.9, 77455.4, 77513.2),
    ("04-25 23:00", 77513.3, 77615.7, 77480.9, 77585.0),
    ("04-26 00:00", 77585.0, 77607.7, 77401.8, 77457.4),
    ("04-26 01:00", 77457.4, 77531.6, 77395.2, 77417.4),
    ("04-26 02:00", 77417.3, 77553.9, 77410.0, 77480.1),
    ("04-26 03:00", 77480.0, 77500.0, 77280.0, 77349.3),
    ("04-26 04:00", 77349.3, 77777.0, 77338.4, 77727.0),
    ("04-26 05:00", 77727.1, 78164.7, 77670.9, 77949.4),
    ("04-26 06:00", 77949.4, 78012.2, 77851.2, 77963.2),
    ("04-26 07:00", 77963.3, 78085.0, 77920.5, 78061.5),

    ("04-26 08:00", 78061.5, 78182.8, 77973.5, 77989.0),
    ("04-26 09:00", 77989.1, 78020.0, 77880.0, 77971.8),
    ("04-26 10:00", 77971.8, 78017.7, 77914.5, 77961.4),

    ("04-26 11:00", 77961.5, 78114.5, 77961.4, 78050.0),
    ("04-26 12:00", 78050.0, 78063.5, 77715.0, 77795.5),

    ("04-26 13:00", 77795.4, 77953.2, 77742.6, 77940.1),
    ("04-26 14:00", 77940.0, 78136.5, 77840.5, 78053.4),
    ("04-26 15:00", 78053.5, 78091.3, 77912.5, 78007.9),
    ("04-26 16:00", 78007.9, 78055.7, 77890.0, 77890.0),

    ("04-26 17:00", 77890.1, 78026.9, 77815.0, 77976.7),

    ("04-26 18:00", 77976.7, 78326.2, 77945.7, 78238.1),

    ("04-26 19:00", 78238.1, 78477.9, 77967.9, 78183.1),
    ("04-26 20:00", 78183.2, 78355.1, 78107.0, 78150.1),
    ("04-26 21:00", 78150.0, 78994.8, 77777.0, 78369.7),

    ("04-26 22:00", 78369.6, 78821.1, 77915.5, 78274.7),
    ("04-26 23:00", 78274.7, 78870.3, 77988.1, 78613.5),

    ("04-27 00:00", 78614.4, 79338.0, 78319.1, 79263.7),
    ("04-27 01:00", 79264.1, 79455.0, 78671.8, 79245.3),
    ("04-27 02:00", 79245.3, 79268.8, 78984.7, 79082.9),
    ("04-27 03:00", 79082.9, 79273.4, 79032.3, 79065.1),
    ("04-27 04:00", 79065.1, 79128.1, 78830.0, 78882.6),
    ("04-27 05:00", 78882.6, 78904.1, 77503.6, 77730.6),
    ("04-27 06:00", 77730.5, 77834.0, 77408.6, 77657.9),
    ("04-27 07:00", 77657.9, 77698.2, 77512.3, 77556.7),
    ("04-27 08:00", 77556.7, 77775.3, 77500.0, 77763.5),
    ("04-27 09:00", 77763.4, 77949.9, 77657.1, 77856.1),

    ("04-27 10:00", 77856.1, 77903.1, 77740.1, 77806.7),

    ("04-27 11:00", 77806.7, 77854.2, 77700.0, 77804.3),
    ("04-27 12:00", 77804.3, 77835.7, 77575.0, 77627.4),
    ("04-27 13:00", 77627.3, 77930.3, 77516.4, 77700.0),
    ("04-27 14:00", 77700.3, 78232.0, 77627.2, 77776.0),
    ("04-27 15:00", 77775.9, 77796.3, 76524.0, 76760.0),
    ("04-27 16:00", 76760.0, 76829.1, 76509.7, 76587.9),
    ("04-27 17:00", 76587.9, 76902.7, 76585.4, 76702.3),
    ("04-27 18:00", 76702.3, 76858.5, 76623.1, 76790.7),
    ("04-27 19:00", 76790.6, 76863.0, 76400.0, 76844.4),
    ("04-27 20:00", 76844.3, 77037.0, 76780.9, 76915.8),

    ("04-29 02:00", 76535.0, 76633.3, 76350.8, 76488.1),
    ("04-29 03:00", 76488.0, 77098.8, 76466.5, 76955.7),
    ("04-29 04:00", 76955.7, 77432.1, 76839.8, 77224.2),
    ("04-29 05:00", 77224.1, 77298.9, 77150.0, 77254.7),
    ("04-29 06:00", 77254.7, 77294.4, 76888.0, 76978.5),
    ("04-29 07:00", 76978.5, 77140.0, 76951.0, 77003.8),
    ("04-29 08:00", 77003.8, 77113.6, 76921.2, 76998.5),
    ("04-29 09:00", 76998.4, 77774.0, 76918.5, 77605.5),
    ("04-29 10:00", 77605.4, 77873.2, 77506.8, 77575.3),
    ("04-29 11:00", 77575.3, 77654.7, 77440.0, 77552.5),
    ("04-29 12:00", 77552.5, 77563.6, 76945.1, 77110.0),
    ("04-29 13:00", 77110.0, 77225.7, 76385.0, 76748.7),
    ("04-29 14:00", 76748.6, 76850.0, 76441.5, 76540.3),
    ("04-29 15:00", 76540.2, 76607.5, 75675.2, 75889.1),
    ("04-29 16:00", 75889.1, 76115.4, 75653.0, 75774.7),
    ("04-29 17:00", 75774.7, 76145.8, 75752.5, 76139.6),
    ("04-29 18:00", 76139.3, 76220.0, 74868.0, 75470.1),
    ("04-29 19:00", 75470.1, 75564.0, 75251.6, 75518.5),
    ("04-29 20:00", 75518.4, 75826.7, 75448.0, 75636.0),
    ("04-29 21:00", 75636.1, 76061.2, 75562.3, 75883.1),
    ("04-29 22:00", 75883.1, 75966.0, 75775.7, 75884.5),
    ("04-29 23:00", 75884.5, 75956.8, 75651.3, 75749.9),
    ("04-30 00:00", 75749.9, 76300.0, 75612.2, 76199.1),
    ("04-30 01:00", 76199.1, 76445.0, 76130.1, 76193.9),
    ("04-30 02:00", 76193.9, 76311.8, 75448.9, 75663.6),
    ("04-30 03:00", 75663.5, 75950.0, 75608.6, 75882.1),
    ("04-30 04:00", 75881.6, 75931.7, 75363.2, 75458.3),
    ("04-30 05:00", 75458.4, 75721.0, 75273.5, 75569.6),
    ("04-30 06:00", 75569.6, 75835.6, 75540.1, 75720.6),
    ("04-30 07:00", 75720.6, 76148.0, 75684.6, 76129.9),
    ("04-30 08:00", 76129.9, 76180.0, 75987.6, 76025.7),
    ("04-30 09:00", 76025.8, 76332.6, 75973.3, 76062.7),
    ("04-30 10:00", 76062.7, 76136.6, 75943.3, 76001.6),
    ("04-30 11:00", 76001.7, 76233.0, 75836.0, 76032.9),

    ("04-30 12:00", 76032.9, 76375.1, 76009.8, 76259.0),

    ("04-30 13:00", 76259.0, 76630.3, 76066.6, 76370.3),
    ("04-30 14:00", 76370.4, 76546.7, 76044.7, 76256.0),
    ("04-30 15:00", 76256.1, 76614.9, 76116.0, 76423.0),
    ("04-30 16:00", 76423.0, 76446.9, 76181.9, 76220.1),
    ("04-30 17:00", 76220.2, 76294.2, 76060.4, 76209.2),
    ("04-30 18:00", 76209.2, 76440.0, 76166.3, 76309.1),
    ("04-30 19:00", 76309.2, 76470.5, 76264.2, 76366.7),

    ("04-30 20:00", 76366.7, 76536.2, 76273.3, 76451.1),

    ("04-30 21:00", 76451.1, 76495.4, 76186.0, 76202.8),
    ("04-30 22:00", 76202.8, 76409.3, 76155.1, 76197.9),
    ("04-30 23:00", 76198.0, 76347.0, 76173.3, 76305.4),
    ("05-01 00:00", 76305.4, 76557.3, 76265.4, 76415.1),

    ("05-01 03:00", 76552.8, 77421.2, 76510.0, 77082.6),
    ("05-01 04:00", 77082.6, 77177.1, 76900.0, 76997.4),
    ("05-01 05:00", 76997.3, 77155.0, 76988.0, 77135.3),
    ("05-01 06:00", 77135.3, 77143.5, 76833.7, 76953.9),
    ("05-01 07:00", 76953.8, 77110.0, 76922.4, 77100.0),
    ("05-01 08:00", 77099.9, 77480.0, 77010.5, 77340.0),
    ("05-01 09:00", 77340.1, 77358.5, 77160.0, 77239.3),
    ("05-01 10:00", 77239.3, 77408.7, 77118.1, 77268.9),
    ("05-01 11:00", 77268.9, 77588.4, 77232.4, 77429.5),
    ("05-01 12:00", 77429.6, 78145.3, 77368.2, 77847.2),
    ("05-01 13:00", 77847.2, 78879.9, 77847.1, 78691.3),
    ("05-01 14:00", 78691.3, 78860.0, 78004.1, 78312.9),
    ("05-01 15:00", 78312.8, 78688.0, 78130.0, 78395.4),
    ("05-01 16:00", 78395.4, 78642.0, 78130.0, 78175.4),
    ("05-01 17:00", 78175.4, 78557.4, 78081.5, 78509.2),
    ("05-01 18:00", 78509.3, 78597.9, 78336.1, 78392.1),
    ("05-01 19:00", 78392.1, 78514.2, 78274.0, 78316.9),
    ("05-01 20:00", 78317.0, 78402.9, 77717.7, 77838.2),
    ("05-01 21:00", 77838.1, 78163.8, 77815.0, 78163.8),
    ("05-01 22:00", 78163.8, 78368.3, 78091.8, 78105.9),
    ("05-01 23:00", 78105.9, 78214.5, 77990.9, 78192.0),
    ("05-02 00:00", 78191.9, 78358.7, 78123.0, 78303.3),
    ("05-02 01:00", 78303.3, 78413.4, 78246.5, 78295.8),
    ("05-02 02:00", 78295.8, 78480.0, 78210.3, 78319.2),
    ("05-02 03:00", 78319.3, 78503.9, 78183.4, 78377.7),
    ("05-02 04:00", 78377.7, 78416.8, 78040.0, 78137.4),
    ("05-02 05:00", 78137.3, 78219.6, 77979.3, 78140.0),
    ("05-02 06:00", 78140.1, 78322.0, 78099.4, 78278.3),
    ("05-02 07:00", 78278.3, 78304.2, 78156.1, 78181.6),
    ("05-02 08:00", 78181.6, 78318.0, 78113.0, 78272.2),
    ("05-02 09:00", 78272.2, 78359.2, 78168.4, 78252.3),
    ("05-02 10:00", 78252.4, 78273.1, 78175.0, 78205.4),
    ("05-02 11:00", 78205.5, 78205.5, 78055.7, 78105.7),
    ("05-02 12:00", 78105.7, 78232.0, 78056.0, 78169.7),

    ("05-02 13:00", 78169.7, 78403.1, 78169.6, 78332.0),
    ("05-02 14:00", 78331.9, 78458.2, 78271.8, 78380.9),
    ("05-02 15:00", 78380.8, 78450.0, 78320.0, 78449.8),
    ("05-02 16:00", 78449.8, 78565.9, 78390.0, 78419.9),
    ("05-02 17:00", 78419.9, 78453.9, 78328.1, 78362.1),
    ("05-02 18:00", 78362.1, 78459.0, 78277.0, 78432.1),
    ("05-02 19:00", 78432.0, 78486.5, 78404.8, 78443.8),

    ("05-02 20:00", 78444.1, 78449.0, 78376.0, 78415.2),
    ("05-02 21:00", 78415.3, 79145.0, 78401.5, 78689.8),
    ("05-02 22:00", 78689.7, 78838.0, 78569.2, 78793.2),
    ("05-02 23:00", 78793.2, 78793.2, 78588.3, 78652.9),
]

# =================== MFE/MAE MOTORU ===================

from datetime import datetime as _dt, timedelta as _td

def _parse_candle_time(t):
    return _dt.strptime(f"{_TRADE_YEAR}-{t}", "%Y-%m-%d %H:%M")

def _calc_mfe_mae_from_candles(candles, candle_hours, entry_price, direction, run_time_str, window_hours=24):
    """Genel MFE/MAE hesaplayici — herhangi bir mum listesi icin."""
    if direction == "NOTR" or not run_time_str:
        return {"mfe": 0, "mae": 0, "max_high": 0, "min_low": 0, "candles_used": 0}
    try:
        rt = _dt.strptime(f"{_TRADE_YEAR}-{run_time_str}", "%Y-%m-%d %H:%M")
    except:
        return {"mfe": 0, "mae": 0, "max_high": 0, "min_low": 0, "candles_used": 0}
    window_end = rt + _td(hours=window_hours)
    max_high = entry_price
    min_low = entry_price
    candles_used = 0
    for ct_str, o, h, l, c in candles:
        ct = _parse_candle_time(ct_str)
        ct_end = ct + _td(hours=candle_hours)
        if ct_end <= rt:
            continue
        if ct >= window_end:
            break
        max_high = max(max_high, h)
        min_low = min(min_low, l)
        candles_used += 1
    if direction == "LONG":
        mfe = max_high - entry_price
        mae = entry_price - min_low
    else:
        mfe = entry_price - min_low
        mae = max_high - entry_price
    return {"mfe": round(mfe, 1), "mae": round(mae, 1),
            "max_high": round(max_high, 1), "min_low": round(min_low, 1),
            "candles_used": candles_used}

def calc_mfe_mae(entry_price, direction, run_time_str, window_hours=24):
    """MFE/MAE hesapla — en yuksek cozunurlukten basla: 15m → 1h → 4h.
    Onemli: Daha yuksek cozunurluk sadece pencere basini kapsiyorsa kullanilir.
    Yoksa daha dusuk cozunurlukte fallback yapilir (kismi veri yaniltici)."""
    if direction == "NOTR" or not run_time_str:
        return {"mfe": 0, "mae": 0, "max_high": 0, "min_low": 0, "candles_used": 0}
    try:
        rt = _dt.strptime(f"{_TRADE_YEAR}-{run_time_str}", "%Y-%m-%d %H:%M")
    except:
        return {"mfe": 0, "mae": 0, "max_high": 0, "min_low": 0, "candles_used": 0}

    # 15m dene — ama sadece pencere basini kapsiyorsa
    if CANDLES_15M:
        first_15m = _parse_candle_time(CANDLES_15M[0][0])
        # 15m verisi run_time'dan en fazla 30dk sonra baslamali
        if first_15m <= rt + _td(minutes=30):
            r15 = _calc_mfe_mae_from_candles(CANDLES_15M, 0.25, entry_price, direction, run_time_str, window_hours)
            if r15["candles_used"] > 0:
                return r15

    # 1h dene
    if CANDLES_1H:
        first_1h = _parse_candle_time(CANDLES_1H[0][0])
        if first_1h <= rt + _td(hours=1):
            r1h = _calc_mfe_mae_from_candles(CANDLES_1H, 1, entry_price, direction, run_time_str, window_hours)
            if r1h["candles_used"] > 0:
                return r1h

    # 4h fallback
    return _calc_mfe_mae_from_candles(CANDLES_4H, 4, entry_price, direction, run_time_str, window_hours)

# =================== REGIME DETECTION (ADX-14, 500 mum, 83 gün) ===================
# Backtest: R2-R24, ADX<20.5 → 4/4 yanlış engellendi, 0 doğru kayıp, %64→%90
# Kaynak: Binance /fapi/v1/klines?symbol=BTCUSDT&interval=4h&limit=500
# Tarih: 2026-01-12 → 2026-04-05
REGIME_ADX_THRESHOLD = 20.5  # Gap ortası: yanlış max=19.8, doğru min=21.3

CANDLES_4H_REGIME = [
    ("01-12 12:00", 90573.9, 91637.8, 90066.0, 91618.7),
    ("01-12 16:00", 91618.6, 92299.0, 90966.0, 91821.9),
    ("01-12 20:00", 91821.9, 92017.0, 90870.0, 91252.6),
    ("01-13 00:00", 91252.5, 91524.5, 91011.0, 91380.9),
    ("01-13 04:00", 91380.9, 92258.0, 91316.3, 91908.0),
    ("01-13 08:00", 91908.0, 92676.6, 91850.6, 91962.1),
    ("01-13 12:00", 91962.1, 93408.0, 91700.6, 93407.9),
    ("01-13 16:00", 93407.9, 94189.0, 93009.8, 94179.5),
    ("01-13 20:00", 94179.6, 96863.7, 94011.7, 95375.2),
    ("01-14 00:00", 95375.2, 95670.0, 95082.0, 95665.7),
    ("01-14 04:00", 95665.6, 95755.0, 94413.4, 95166.6),
    ("01-14 08:00", 95166.6, 95288.0, 94700.0, 94763.6),
    ("01-14 12:00", 94763.7, 97100.0, 94643.0, 96691.9),
    ("01-14 16:00", 96691.9, 97733.9, 96180.0, 97221.8),
    ("01-14 20:00", 97221.8, 97932.1, 96666.6, 96907.9),
    ("01-15 00:00", 96908.0, 96960.9, 95733.1, 95943.1),
    ("01-15 04:00", 95943.1, 96744.2, 95909.1, 96601.2),
    ("01-15 08:00", 96601.2, 97155.0, 96243.8, 96548.9),
    ("01-15 12:00", 96548.9, 97100.0, 95403.7, 96717.3),
    ("01-15 16:00", 96717.3, 97047.6, 95080.0, 95469.2),
    ("01-15 20:00", 95469.2, 95837.8, 95089.0, 95567.3),
    ("01-16 00:00", 95567.4, 95825.0, 95279.8, 95319.6),
    ("01-16 04:00", 95319.6, 95790.0, 95111.1, 95608.4),
    ("01-16 08:00", 95608.4, 95805.0, 95210.5, 95382.6),
    ("01-16 12:00", 95382.5, 95763.0, 94234.5, 94537.5),
    ("01-16 16:00", 94537.6, 95191.8, 94454.5, 94961.0),
    ("01-16 20:00", 94961.0, 95550.0, 94630.0, 95503.7),
    ("01-17 00:00", 95503.8, 95536.9, 95136.2, 95324.0),
    ("01-17 04:00", 95324.1, 95346.1, 94999.9, 95061.1),
    ("01-17 08:00", 95061.1, 95287.1, 94977.5, 95283.9),
    ("01-17 12:00", 95283.8, 95621.9, 95152.1, 95529.0),
    ("01-17 16:00", 95529.0, 95529.0, 95165.5, 95258.3),
    ("01-17 20:00", 95258.3, 95373.2, 95000.0, 95107.9),
    ("01-18 00:00", 95107.9, 95200.9, 94819.5, 95155.0),
    ("01-18 04:00", 95155.0, 95236.5, 94980.0, 94989.9),
    ("01-18 08:00", 94989.9, 95257.4, 94980.0, 95133.4),
    ("01-18 12:00", 95133.3, 95326.4, 94850.4, 95067.8),
    ("01-18 16:00", 95067.7, 95485.9, 95024.6, 95335.6),
    ("01-18 20:00", 95335.6, 95490.0, 93550.3, 93614.0),
    ("01-19 00:00", 93614.0, 93614.1, 91800.0, 92656.6),
    ("01-19 04:00", 92656.7, 92810.0, 92344.5, 92787.9),
    ("01-19 08:00", 92787.8, 93312.8, 92635.0, 93136.7),
    ("01-19 12:00", 93136.8, 93188.0, 92660.0, 93013.5),
    ("01-19 16:00", 93013.4, 93379.0, 92888.0, 93066.2),
    ("01-19 20:00", 93066.2, 93312.1, 92116.0, 92589.6),
    ("01-20 00:00", 92589.6, 92845.0, 92200.0, 92397.0),
    ("01-20 04:00", 92396.9, 92440.1, 90723.3, 91136.1),
    ("01-20 08:00", 91136.1, 91415.1, 90622.2, 91185.8),
    ("01-20 12:00", 91185.8, 91344.8, 89819.0, 90644.2),
    ("01-20 16:00", 90644.3, 90944.5, 89250.2, 89694.1),
    ("01-20 20:00", 89694.1, 89824.0, 87787.2, 88390.6),
    ("01-21 00:00", 88390.7, 89568.5, 88218.2, 89396.0),
    ("01-21 04:00", 89395.9, 90088.0, 89045.0, 89171.3),
    ("01-21 08:00", 89171.3, 89449.0, 88614.1, 88757.1),
    ("01-21 12:00", 88757.0, 90599.5, 88109.7, 90237.1),
    ("01-21 16:00", 90237.2, 90427.6, 87205.5, 90321.9),
    ("01-21 20:00", 90321.9, 90349.0, 89317.9, 89411.4),
    ("01-22 00:00", 89411.4, 90327.7, 89411.3, 89857.0),
    ("01-22 04:00", 89856.9, 90170.1, 89750.0, 89772.6),
    ("01-22 08:00", 89772.6, 90123.0, 89701.9, 89909.6),
    ("01-22 12:00", 89909.7, 90309.5, 88465.6, 88953.6),
    ("01-22 16:00", 88953.7, 89882.1, 88630.2, 89732.9),
    ("01-22 20:00", 89732.8, 89908.5, 89095.5, 89518.5),
    ("01-23 00:00", 89518.4, 89948.9, 89400.0, 89886.1),
    ("01-23 04:00", 89886.2, 90050.0, 89358.0, 89497.2),
    ("01-23 08:00", 89497.3, 89590.9, 88823.3, 89171.2),
    ("01-23 12:00", 89171.3, 89847.2, 88530.0, 89711.2),
    ("01-23 16:00", 89711.2, 91195.0, 89438.0, 89938.3),
    ("01-23 20:00", 89938.3, 90124.1, 89163.6, 89558.7),
    ("01-24 00:00", 89558.7, 89893.9, 89383.5, 89738.4),
    ("01-24 04:00", 89738.4, 89820.1, 89530.6, 89581.2),
    ("01-24 08:00", 89581.3, 89659.2, 89539.5, 89548.5),
    ("01-24 12:00", 89548.5, 89554.9, 89131.2, 89235.0),
    ("01-24 16:00", 89234.9, 89425.2, 89116.9, 89286.0),
    ("01-24 20:00", 89286.1, 89444.4, 89155.0, 89180.7),
    ("01-25 00:00", 89180.7, 89281.6, 88800.0, 88920.0),
    ("01-25 04:00", 88920.0, 89057.8, 88600.0, 88630.3),
    ("01-25 08:00", 88630.3, 88727.2, 88084.0, 88531.0),
    ("01-25 12:00", 88530.9, 88947.1, 88306.6, 88406.0),
    ("01-25 16:00", 88406.0, 88410.0, 86100.0, 86459.4),
    ("01-25 20:00", 86459.4, 86966.4, 86021.7, 86628.9),
    ("01-26 00:00", 86628.9, 87922.0, 86463.2, 87233.1),
    ("01-26 04:00", 87233.1, 88059.6, 87188.3, 87968.9),
    ("01-26 08:00", 87969.0, 88367.5, 87556.9, 87810.0),
    ("01-26 12:00", 87810.1, 88834.1, 87278.5, 87609.5),
    ("01-26 16:00", 87609.4, 88496.4, 86960.0, 87965.6),
    ("01-26 20:00", 87965.5, 88637.4, 87506.8, 88300.6),
    ("01-27 00:00", 88300.6, 88880.6, 88157.4, 88744.6),
    ("01-27 04:00", 88744.7, 88983.3, 88239.9, 88287.9),
    ("01-27 08:00", 88288.0, 88365.6, 87707.1, 87947.5),
    ("01-27 12:00", 87947.4, 88418.8, 87530.0, 88000.1),
    ("01-27 16:00", 88000.1, 88836.3, 87265.4, 88378.1),
    ("01-27 20:00", 88378.1, 89499.0, 88335.6, 89197.8),
    ("01-28 00:00", 89197.8, 89454.6, 88932.6, 89079.8),
    ("01-28 04:00", 89079.8, 89366.0, 88786.0, 89106.8),
    ("01-28 08:00", 89106.8, 90122.0, 88831.9, 90036.9),
    ("01-28 12:00", 90036.9, 90444.4, 88852.2, 89444.4),
    ("01-28 16:00", 89444.5, 90592.7, 88974.0, 89363.6),
    ("01-28 20:00", 89363.5, 89880.1, 88829.0, 89261.7),
    ("01-29 00:00", 89261.7, 89316.8, 87650.1, 88003.2),
    ("01-29 04:00", 88003.2, 88394.2, 87863.0, 88310.9),
    ("01-29 08:00", 88310.9, 88461.2, 87711.0, 87795.2),
    ("01-29 12:00", 87795.1, 88133.2, 84335.4, 84898.0),
    ("01-29 16:00", 84897.9, 85596.1, 83338.3, 83979.4),
    ("01-29 20:00", 83979.5, 84699.9, 83785.6, 84604.7),
    ("01-30 00:00", 84604.7, 84697.2, 81000.0, 82640.9),
    ("01-30 04:00", 82640.9, 83300.0, 82021.1, 82770.1),
    ("01-30 08:00", 82770.1, 83280.6, 82108.4, 83104.8),
    ("01-30 12:00", 83104.7, 83779.2, 82328.6, 82850.2),
    ("01-30 16:00", 82850.1, 84599.0, 81832.0, 84200.0),
    ("01-30 20:00", 84199.9, 84487.7, 83501.0, 84211.4),
    ("01-31 00:00", 84211.4, 84239.5, 83775.5, 83987.5),
    ("01-31 04:00", 83987.5, 84110.0, 83368.0, 83514.4),
    ("01-31 08:00", 83514.3, 83598.0, 82530.2, 82983.2),
    ("01-31 12:00", 82983.2, 83115.3, 80754.3, 81268.6),
    ("01-31 16:00", 81268.6, 82200.0, 75500.0, 77707.9),
    ("01-31 20:00", 77707.9, 79200.0, 77037.8, 78706.8),
    ("02-01 00:00", 78706.7, 79396.8, 78245.7, 78826.3),
    ("02-01 04:00", 78826.3, 79094.9, 77899.9, 78320.8),
    ("02-01 08:00", 78320.8, 79194.0, 78099.8, 78712.1),
    ("02-01 12:00", 78712.1, 78732.0, 76752.5, 77563.8),
    ("02-01 16:00", 77563.8, 78421.6, 76950.9, 77142.4),
    ("02-01 20:00", 77142.4, 77753.6, 75644.0, 76931.5),
    ("02-02 00:00", 76931.6, 78111.0, 74555.0, 76256.2),
    ("02-02 04:00", 76256.2, 76930.0, 74853.0, 76612.6),
    ("02-02 08:00", 76612.6, 77937.7, 76576.7, 77716.1),
    ("02-02 12:00", 77716.0, 79311.0, 77515.6, 78800.6),
    ("02-02 16:00", 78800.5, 79248.0, 78234.9, 78299.2),
    ("02-02 20:00", 78299.1, 78935.9, 77843.2, 78692.5),
    ("02-03 00:00", 78692.5, 79163.0, 77566.5, 78710.7),
    ("02-03 04:00", 78710.7, 78967.9, 77900.1, 78749.9),
    ("02-03 08:00", 78750.0, 79049.0, 77900.0, 78040.1),
    ("02-03 12:00", 78040.1, 78425.8, 77000.5, 78094.1),
    ("02-03 16:00", 78094.2, 78101.5, 72889.2, 74893.8),
    ("02-03 20:00", 74893.9, 76920.7, 74541.0, 75732.4),
    ("02-04 00:00", 75732.4, 76952.5, 75420.0, 76661.1),
    ("02-04 04:00", 76661.1, 76809.4, 76072.0, 76478.9),
    ("02-04 08:00", 76478.9, 76568.0, 75629.9, 75987.6),
    ("02-04 12:00", 75987.6, 76245.5, 73756.0, 74107.0),
    ("02-04 16:00", 74107.0, 74211.8, 72101.0, 73895.3),
    ("02-04 20:00", 73895.2, 74141.1, 71838.0, 73137.4),
    ("02-05 00:00", 73137.5, 73316.3, 71111.0, 71198.9),
    ("02-05 04:00", 71199.0, 71600.0, 70085.3, 70716.1),
    ("02-05 08:00", 70716.1, 71944.4, 69862.0, 70279.0),
    ("02-05 12:00", 70279.1, 70848.6, 66666.0, 67451.9),
    ("02-05 16:00", 67452.0, 68667.4, 65160.0, 65237.4),
    ("02-05 20:00", 65237.5, 65678.1, 62233.3, 62868.1),
    ("02-06 00:00", 62868.1, 65969.5, 59800.0, 64138.1),
    ("02-06 04:00", 64138.1, 66783.0, 63924.7, 64811.2),
    ("02-06 08:00", 64811.2, 66773.4, 64438.9, 66586.1),
    ("02-06 12:00", 66586.1, 69157.9, 66072.0, 68577.5),
    ("02-06 16:00", 68577.5, 71451.6, 68348.0, 70675.5),
    ("02-06 20:00", 70675.5, 71714.4, 69764.7, 70544.5),
    ("02-07 00:00", 70544.5, 70899.5, 69674.5, 70887.1),
    ("02-07 04:00", 70887.2, 71690.0, 67250.0, 68050.5),
    ("02-07 08:00", 68050.5, 68797.8, 67550.2, 67935.1),
    ("02-07 12:00", 67935.0, 70000.0, 67870.2, 69122.1),
    ("02-07 16:00", 69122.1, 69887.7, 68478.1, 69341.4),
    ("02-07 20:00", 69341.3, 69688.2, 68734.6, 69254.2),
    ("02-08 00:00", 69254.3, 69666.0, 68843.7, 69064.7),
    ("02-08 04:00", 69064.7, 69693.0, 68928.0, 69665.0),
    ("02-08 08:00", 69665.1, 71199.9, 69467.9, 70954.0),
    ("02-08 12:00", 70954.0, 71524.9, 70653.0, 71152.6),
    ("02-08 16:00", 71152.5, 71480.0, 70220.1, 71381.0),
    ("02-08 20:00", 71381.0, 72300.0, 69913.3, 70288.1),
    ("02-09 00:00", 70288.2, 71434.9, 70013.3, 71269.9),
    ("02-09 04:00", 71269.8, 71320.0, 70251.1, 70393.5),
    ("02-09 08:00", 70393.5, 70583.3, 68373.9, 68899.9),
    ("02-09 12:00", 68900.0, 69843.7, 68271.7, 69528.9),
    ("02-09 16:00", 69528.9, 71041.0, 69050.0, 70912.7),
    ("02-09 20:00", 70912.6, 71085.0, 69776.1, 70110.5),
    ("02-10 00:00", 70110.6, 70499.9, 69155.8, 69473.3),
    ("02-10 04:00", 69473.2, 69886.1, 68633.3, 68882.1),
    ("02-10 08:00", 68882.2, 69376.3, 68406.4, 68489.9),
    ("02-10 12:00", 68489.9, 69554.7, 67883.0, 69251.5),
    ("02-10 16:00", 69251.4, 69957.9, 68555.6, 69031.4),
    ("02-10 20:00", 69031.3, 69116.9, 68322.1, 68805.3),
    ("02-11 00:00", 68805.3, 69262.7, 67951.8, 68143.6),
    ("02-11 04:00", 68143.6, 68288.0, 66511.0, 67000.0),
    ("02-11 08:00", 67000.0, 67094.4, 66342.6, 67023.0),
    ("02-11 12:00", 67022.9, 68821.1, 65718.5, 66489.3),
    ("02-11 16:00", 66489.4, 67831.4, 65834.5, 67547.7),
    ("02-11 20:00", 67547.6, 68315.0, 66757.4, 67054.4),
    ("02-12 00:00", 67054.8, 68021.0, 67016.6, 67550.2),
    ("02-12 04:00", 67550.3, 67659.6, 66640.0, 67181.5),
    ("02-12 08:00", 67181.5, 68265.5, 66860.0, 68031.8),
    ("02-12 12:00", 68031.8, 68385.0, 66958.0, 67107.0),
    ("02-12 16:00", 67107.0, 67221.9, 65081.0, 65760.7),
    ("02-12 20:00", 65760.7, 66460.8, 65177.8, 66243.1),
    ("02-13 00:00", 66243.2, 66778.5, 65833.9, 66519.6),
    ("02-13 04:00", 66519.6, 66650.2, 65964.2, 66183.3),
    ("02-13 08:00", 66183.3, 67196.8, 66159.9, 67137.8),
    ("02-13 12:00", 67137.8, 69289.5, 66823.6, 68652.0),
    ("02-13 16:00", 68652.1, 69473.7, 68500.0, 68904.2),
    ("02-13 20:00", 68904.3, 69055.9, 68639.7, 68821.5),
    ("02-14 00:00", 68821.5, 69118.1, 68736.2, 68947.7),
    ("02-14 04:00", 68947.7, 69318.2, 68689.1, 69182.2),
    ("02-14 08:00", 69182.1, 70557.7, 69174.5, 70464.8),
    ("02-14 12:00", 70464.8, 70499.4, 69163.7, 69754.2),
    ("02-14 16:00", 69754.2, 69903.3, 69259.1, 69849.0),
    ("02-14 20:00", 69848.9, 70230.6, 69600.0, 69795.4),
    ("02-15 00:00", 69795.4, 69967.4, 69212.2, 69926.0),
    ("02-15 04:00", 69925.9, 70907.7, 69925.9, 70784.0),
    ("02-15 08:00", 70784.0, 70938.5, 70114.8, 70268.7),
    ("02-15 12:00", 70268.6, 70391.0, 68741.4, 69068.1),
    ("02-15 16:00", 69068.1, 69074.0, 68029.6, 68263.6),
    ("02-15 20:00", 68263.7, 69049.2, 68100.2, 68796.9),
    ("02-16 00:00", 68796.9, 69033.6, 68112.2, 68392.6),
    ("02-16 04:00", 68392.6, 68869.8, 68183.3, 68552.4),
    ("02-16 08:00", 68552.5, 69029.9, 68300.0, 68769.4),
    ("02-16 12:00", 68769.4, 70110.9, 67250.0, 67505.5),
    ("02-16 16:00", 67505.5, 68221.7, 67475.0, 67883.6),
    ("02-16 20:00", 67883.5, 68962.1, 67788.6, 68862.5),
    ("02-17 00:00", 68862.6, 69228.6, 68350.0, 68443.6),
    ("02-17 04:00", 68443.6, 68681.8, 67854.2, 68353.4),
    ("02-17 08:00", 68353.4, 68445.8, 67655.0, 67824.4),
    ("02-17 12:00", 67824.3, 68350.0, 66588.0, 67363.6),
    ("02-17 16:00", 67363.6, 68220.1, 66824.5, 67766.9),
    ("02-17 20:00", 67766.9, 67897.6, 67355.7, 67475.9),
    ("02-18 00:00", 67475.9, 67683.4, 66850.1, 67590.2),
    ("02-18 04:00", 67590.3, 68190.2, 67456.6, 68078.4),
    ("02-18 08:00", 68078.5, 68438.0, 67037.2, 67345.4),
    ("02-18 12:00", 67345.4, 68336.0, 66666.2, 67671.0),
    ("02-18 16:00", 67671.1, 67684.6, 65826.1, 66138.2),
    ("02-18 20:00", 66138.3, 66528.8, 65993.1, 66422.8),
    ("02-19 00:00", 66422.8, 66975.0, 66301.8, 66950.4),
    ("02-19 04:00", 66950.4, 67299.4, 66651.8, 67180.4),
    ("02-19 08:00", 67180.4, 67180.4, 66431.1, 66468.9),
    ("02-19 12:00", 66468.8, 66723.0, 65595.7, 66362.7),
    ("02-19 16:00", 66362.6, 67174.0, 65863.8, 67022.9),
    ("02-19 20:00", 67022.8, 67147.8, 66618.2, 66974.0),
    ("02-20 00:00", 66973.9, 67490.0, 66912.4, 67327.2),
    ("02-20 04:00", 67327.2, 67999.9, 67079.3, 67794.7),
    ("02-20 08:00", 67794.8, 68283.7, 67250.0, 67290.5),
    ("02-20 12:00", 67290.4, 68099.9, 66408.1, 67547.6),
    ("02-20 16:00", 67547.6, 67998.9, 66915.0, 67616.5),
    ("02-20 20:00", 67616.5, 68220.0, 67486.6, 67979.3),
    ("02-21 00:00", 67979.3, 68079.0, 67488.9, 67637.0),
    ("02-21 04:00", 67636.9, 67899.0, 67555.2, 67821.0),
    ("02-21 08:00", 67821.0, 68280.0, 67776.2, 68060.9),
    ("02-21 12:00", 68061.0, 68687.0, 67882.8, 68571.5),
    ("02-21 16:00", 68571.5, 68632.5, 68066.0, 68516.3),
    ("02-21 20:00", 68516.3, 68568.1, 67860.0, 67933.1),
    ("02-22 00:00", 67933.2, 68198.5, 67763.7, 68010.5),
    ("02-22 04:00", 68010.5, 68204.3, 67850.4, 67973.0),
    ("02-22 08:00", 67973.0, 68220.0, 67877.0, 68183.4),
    ("02-22 12:00", 68183.4, 68205.1, 67275.0, 67659.9),
    ("02-22 16:00", 67660.0, 67712.0, 67150.0, 67402.2),
    ("02-22 20:00", 67402.1, 67728.0, 67324.1, 67613.5),
    ("02-23 00:00", 67613.6, 67655.8, 64232.8, 64894.0),
    ("02-23 04:00", 64894.1, 65980.0, 64628.5, 65915.8),
    ("02-23 08:00", 65915.7, 66574.5, 65534.6, 66170.8),
    ("02-23 12:00", 66170.8, 66490.0, 65500.0, 65633.1),
    ("02-23 16:00", 65633.1, 65701.2, 64050.0, 64273.9),
    ("02-23 20:00", 64273.9, 64989.0, 63860.0, 64625.8),
    ("02-24 00:00", 64625.8, 64980.0, 63303.9, 63570.5),
    ("02-24 04:00", 63570.5, 63606.3, 62655.0, 63155.3),
    ("02-24 08:00", 63155.4, 63432.4, 62900.0, 63192.2),
    ("02-24 12:00", 63192.1, 63993.1, 62401.7, 63933.4),
    ("02-24 16:00", 63933.4, 64719.1, 63664.8, 64405.4),
    ("02-24 20:00", 64405.4, 64566.5, 63769.2, 64031.3),
    ("02-25 00:00", 64031.4, 66283.1, 63876.0, 65361.7),
    ("02-25 04:00", 65361.7, 65627.5, 64720.4, 65001.1),
    ("02-25 08:00", 65001.2, 65674.1, 64929.7, 65396.7),
    ("02-25 12:00", 65396.6, 67548.0, 65280.1, 67362.3),
    ("02-25 16:00", 67362.4, 69531.3, 67354.2, 69005.2),
    ("02-25 20:00", 69005.2, 69999.0, 67557.0, 67952.5),
    ("02-26 00:00", 67952.5, 68666.0, 67690.1, 68187.5),
    ("02-26 04:00", 68187.4, 68850.0, 67780.0, 67800.0),
    ("02-26 08:00", 67800.0, 68689.7, 67750.0, 68025.2),
    ("02-26 12:00", 68025.2, 68270.9, 66730.7, 67353.4),
    ("02-26 16:00", 67353.3, 67888.0, 66462.0, 67550.7),
    ("02-26 20:00", 67550.7, 67790.1, 67114.0, 67448.2),
    ("02-27 00:00", 67448.1, 67670.0, 66841.6, 67557.4),
    ("02-27 04:00", 67557.4, 68188.8, 67417.4, 67644.1),
    ("02-27 08:00", 67644.1, 68127.8, 65923.0, 66094.1),
    ("02-27 12:00", 66094.0, 66320.0, 65626.1, 66072.6),
    ("02-27 16:00", 66072.5, 66095.2, 65080.0, 65365.4),
    ("02-27 20:00", 65365.4, 65921.7, 64875.6, 65836.0),
    ("02-28 00:00", 65836.0, 65994.7, 65681.9, 65763.8),
    ("02-28 04:00", 65763.8, 65786.8, 62979.5, 63788.4),
    ("02-28 08:00", 63787.4, 64267.9, 63313.9, 63810.4),
    ("02-28 12:00", 63810.4, 65335.8, 63782.2, 64800.0),
    ("02-28 16:00", 64800.1, 66642.8, 64635.0, 66318.1),
    ("02-28 20:00", 66318.1, 67735.0, 66150.0, 66937.1),
    ("03-01 00:00", 66937.0, 68189.0, 65812.0, 67474.7),
    ("03-01 04:00", 67474.8, 67582.2, 66757.2, 67113.9),
    ("03-01 08:00", 67114.0, 67275.5, 66160.4, 66439.0),
    ("03-01 12:00", 66439.0, 67333.0, 66100.0, 66810.8),
    ("03-01 16:00", 66810.8, 67083.0, 65681.3, 65926.0),
    ("03-01 20:00", 65925.9, 66888.0, 65011.0, 65750.0),
    ("03-02 00:00", 65749.9, 67082.5, 65726.0, 66787.3),
    ("03-02 04:00", 66787.3, 66966.0, 65509.0, 65981.3),
    ("03-02 08:00", 65981.2, 66707.5, 65612.4, 66329.9),
    ("03-02 12:00", 66329.8, 69588.0, 65234.4, 69089.1),
    ("03-02 16:00", 69089.1, 70100.0, 68519.8, 68928.4),
    ("03-02 20:00", 68928.4, 69500.0, 68529.5, 68801.8),
    ("03-03 00:00", 68801.8, 69221.6, 68142.1, 68349.3),
    ("03-03 04:00", 68349.4, 68561.9, 67759.6, 68138.3),
    ("03-03 08:00", 68138.2, 68281.6, 66270.7, 67000.0),
    ("03-03 12:00", 67000.0, 68000.0, 66080.0, 67692.5),
    ("03-03 16:00", 67692.5, 68972.9, 67440.0, 68395.9),
    ("03-03 20:00", 68395.9, 68821.5, 67778.4, 68295.3),
    ("03-04 00:00", 68295.2, 68887.9, 67350.0, 67700.1),
    ("03-04 04:00", 67700.1, 69676.4, 67421.9, 69464.5),
    ("03-04 08:00", 69464.5, 71887.9, 69100.2, 71082.4),
    ("03-04 12:00", 71082.3, 73436.4, 70559.7, 73339.7),
    ("03-04 16:00", 73339.7, 74046.5, 72467.2, 73580.2),
    ("03-04 20:00", 73580.3, 73678.2, 72273.0, 72641.4),
    ("03-05 00:00", 72641.4, 73295.7, 72300.0, 72469.6),
    ("03-05 04:00", 72469.5, 73060.0, 71740.0, 72025.5),
    ("03-05 08:00", 72025.4, 73539.1, 71716.3, 72879.9),
    ("03-05 12:00", 72880.0, 73032.0, 71136.2, 71611.7),
    ("03-05 16:00", 71611.7, 71620.6, 70612.8, 70875.5),
    ("03-05 20:00", 70875.5, 71530.4, 70737.9, 70854.8),
    ("03-06 00:00", 70854.8, 71387.5, 70339.6, 71045.4),
    ("03-06 04:00", 71045.4, 71168.0, 70100.0, 71026.7),
    ("03-06 08:00", 71026.7, 71035.3, 70164.9, 70185.6),
    ("03-06 12:00", 70185.6, 70328.5, 68121.6, 68468.4),
    ("03-06 16:00", 68468.3, 68759.5, 67712.3, 68101.0),
    ("03-06 20:00", 68100.9, 68406.6, 67731.0, 68083.0),
    ("03-07 00:00", 68083.0, 68524.9, 68018.7, 68063.2),
    ("03-07 04:00", 68063.3, 68130.7, 67411.0, 67809.4),
    ("03-07 08:00", 67809.5, 68215.6, 67675.0, 67975.9),
    ("03-07 12:00", 67976.0, 68061.1, 67568.4, 67844.8),
    ("03-07 16:00", 67844.8, 67913.6, 66850.1, 67042.6),
    ("03-07 20:00", 67042.6, 67445.9, 67028.0, 67232.1),
    ("03-08 00:00", 67232.1, 67459.0, 66720.8, 66974.9),
    ("03-08 04:00", 66974.9, 67430.0, 66508.0, 67277.2),
    ("03-08 08:00", 67277.1, 68171.6, 67121.1, 67490.0),
    ("03-08 12:00", 67490.1, 67623.0, 66730.0, 67174.7),
    ("03-08 16:00", 67174.6, 67459.2, 66707.0, 67299.0),
    ("03-08 20:00", 67299.0, 67496.4, 65569.2, 65934.3),
    ("03-09 00:00", 65934.3, 67646.0, 65770.5, 67165.3),
    ("03-09 04:00", 67165.3, 68038.4, 66833.9, 67504.8),
    ("03-09 08:00", 67504.9, 68441.5, 67301.0, 67723.3),
    ("03-09 12:00", 67723.3, 69449.1, 67714.2, 68832.3),
    ("03-09 16:00", 68832.4, 69498.0, 68200.1, 68951.8),
    ("03-09 20:00", 68951.8, 69100.2, 68333.0, 68394.1),
    ("03-10 00:00", 68394.0, 70555.0, 68345.0, 69391.0),
    ("03-10 04:00", 69391.0, 70500.0, 69391.0, 70374.7),
    ("03-10 08:00", 70374.7, 71272.4, 70332.2, 70570.1),
    ("03-10 12:00", 70570.1, 71748.1, 69184.8, 71296.9),
    ("03-10 16:00", 71296.9, 71665.8, 69688.0, 70005.2),
    ("03-10 20:00", 70005.1, 70375.4, 69388.0, 69901.9),
    ("03-11 00:00", 69901.8, 70139.6, 69455.6, 69517.0),
    ("03-11 04:00", 69517.0, 70249.1, 69329.7, 69622.1),
    ("03-11 08:00", 69622.2, 69750.0, 69098.0, 69144.0),
    ("03-11 12:00", 69144.0, 71060.7, 68932.9, 70186.9),
    ("03-11 16:00", 70187.0, 71286.0, 70093.2, 70600.8),
    ("03-11 20:00", 70600.7, 70931.9, 70078.6, 70150.0),
    ("03-12 00:00", 70150.0, 70314.1, 69180.0, 69402.6),
    ("03-12 04:00", 69402.6, 69818.8, 69150.0, 69782.6),
    ("03-12 08:00", 69782.7, 70756.5, 69540.9, 70388.5),
    ("03-12 12:00", 70388.6, 70625.0, 69303.8, 70282.9),
    ("03-12 16:00", 70282.8, 70530.0, 69725.0, 70393.7),
    ("03-12 20:00", 70393.7, 70727.9, 69974.7, 70480.1),
    ("03-13 00:00", 70480.1, 71979.2, 70342.7, 71366.3),
    ("03-13 04:00", 71366.3, 71649.7, 71150.0, 71585.3),
    ("03-13 08:00", 71585.2, 72547.0, 71347.1, 72189.9),
    ("03-13 12:00", 72189.8, 73870.0, 71700.0, 71800.0),
    ("03-13 16:00", 71800.1, 72215.1, 70811.0, 71148.0),
    ("03-13 20:00", 71148.1, 71452.1, 70510.8, 70895.5),
    ("03-14 00:00", 70895.5, 71141.7, 70436.2, 71034.3),
    ("03-14 04:00", 71034.3, 71272.3, 70256.0, 70565.6),
    ("03-14 08:00", 70565.6, 70745.1, 70350.0, 70705.0),
    ("03-14 12:00", 70705.0, 70914.6, 70444.1, 70554.6),
    ("03-14 16:00", 70554.7, 70707.9, 70455.6, 70664.1),
    ("03-14 20:00", 70664.1, 71221.9, 70607.7, 71174.4),
    ("03-15 00:00", 71174.4, 71599.9, 70815.7, 71314.8),
    ("03-15 04:00", 71314.8, 71750.0, 71277.1, 71420.8),
    ("03-15 08:00", 71420.8, 71897.9, 71420.8, 71800.0),
    ("03-15 12:00", 71800.1, 71800.1, 71220.1, 71444.4),
    ("03-15 16:00", 71444.4, 71971.8, 71275.0, 71515.2),
    ("03-15 20:00", 71515.2, 73199.9, 71396.4, 72778.9),
    ("03-16 00:00", 72778.8, 74307.3, 72235.6, 73539.5),
    ("03-16 04:00", 73539.5, 74444.0, 73345.9, 73427.7),
    ("03-16 08:00", 73427.8, 73856.6, 72841.9, 73515.3),
    ("03-16 12:00", 73515.3, 74481.5, 72926.4, 73240.2),
    ("03-16 16:00", 73240.2, 74399.9, 73122.0, 73928.8),
    ("03-16 20:00", 73928.8, 74880.0, 73819.0, 74846.4),
    ("03-17 00:00", 74846.4, 75998.9, 74231.6, 74424.9),
    ("03-17 04:00", 74424.9, 74652.2, 73723.4, 74212.7),
    ("03-17 08:00", 74212.8, 74418.5, 73512.0, 73997.1),
    ("03-17 12:00", 73997.1, 74856.2, 73330.3, 73878.5),
    ("03-17 16:00", 73878.5, 74763.6, 73826.8, 74460.8),
    ("03-17 20:00", 74460.8, 74777.0, 73829.5, 73872.4),
    ("03-18 00:00", 73872.3, 74633.0, 73492.0, 74414.6),
    ("03-18 04:00", 74414.7, 74455.7, 73636.5, 73840.0),
    ("03-18 08:00", 73840.1, 74246.2, 72731.6, 72906.4),
    ("03-18 12:00", 72906.4, 72947.4, 70821.2, 71436.4),
    ("03-18 16:00", 71436.3, 71980.5, 70858.3, 71030.3),
    ("03-18 20:00", 71030.3, 71438.1, 70456.0, 71202.9),
    ("03-19 00:00", 71202.9, 71598.3, 70858.4, 71180.0),
    ("03-19 04:00", 71180.0, 71180.0, 69421.1, 70145.1),
    ("03-19 08:00", 70145.0, 70535.0, 69860.3, 69926.8),
    ("03-19 12:00", 69926.8, 70144.6, 68750.0, 69372.7),
    ("03-19 16:00", 69372.8, 70563.5, 69065.4, 70233.1),
    ("03-19 20:00", 70233.0, 70655.2, 69677.1, 69887.4),
    ("03-20 00:00", 69887.4, 70777.0, 69801.3, 70696.1),
    ("03-20 04:00", 70696.1, 70944.9, 70161.0, 70811.9),
    ("03-20 08:00", 70812.0, 71342.2, 70175.0, 70439.9),
    ("03-20 12:00", 70440.0, 70647.5, 69450.0, 69829.5),
    ("03-20 16:00", 69829.5, 70161.0, 69350.0, 70141.9),
    ("03-20 20:00", 70141.9, 70888.0, 69701.3, 70472.7),
    ("03-21 00:00", 70472.6, 70803.1, 70403.2, 70638.0),
    ("03-21 04:00", 70637.9, 70849.2, 70582.7, 70687.3),
    ("03-21 08:00", 70687.4, 70721.7, 70455.6, 70618.3),
    ("03-21 12:00", 70618.2, 71077.7, 70420.0, 70599.1),
    ("03-21 16:00", 70599.1, 70620.2, 70163.0, 70365.9),
    ("03-21 20:00", 70365.8, 70482.2, 68511.3, 68881.5),
    ("03-22 00:00", 68881.5, 69555.8, 68189.0, 69307.0),
    ("03-22 04:00", 69307.1, 69493.2, 68846.4, 68884.5),
    ("03-22 08:00", 68884.5, 68950.0, 68030.0, 68177.0),
    ("03-22 12:00", 68177.0, 69000.0, 68153.1, 68814.9),
    ("03-22 16:00", 68814.9, 68852.3, 68108.0, 68170.6),
    ("03-22 20:00", 68170.6, 68470.6, 67300.0, 67830.6),
    ("03-23 00:00", 67830.7, 68555.5, 67400.1, 68045.1),
    ("03-23 04:00", 68045.2, 68872.4, 67456.7, 68306.0),
    ("03-23 08:00", 68305.9, 71468.0, 67880.0, 70097.3),
    ("03-23 12:00", 70097.2, 71789.8, 69644.0, 70112.2),
    ("03-23 16:00", 70112.2, 71232.0, 70100.5, 70647.1),
    ("03-23 20:00", 70647.1, 70976.3, 70370.0, 70865.9),
    ("03-24 00:00", 70866.0, 71080.0, 70232.0, 70512.1),
    ("03-24 04:00", 70512.1, 71377.5, 70075.5, 71255.2),
    ("03-24 08:00", 71255.2, 71339.8, 70812.7, 71116.4),
    ("03-24 12:00", 71116.4, 71144.0, 69467.8, 69837.7),
    ("03-24 16:00", 69837.6, 69979.0, 68884.5, 69342.6),
    ("03-24 20:00", 69342.6, 70800.0, 69257.9, 70523.9),
    ("03-25 00:00", 70524.0, 71028.0, 70375.0, 70689.3),
    ("03-25 04:00", 70689.2, 71319.9, 70659.9, 70900.0),
    ("03-25 08:00", 70899.9, 71999.9, 70752.5, 71650.3),
    ("03-25 12:00", 71650.3, 71933.3, 70531.4, 70792.4),
    ("03-25 16:00", 70792.4, 71742.2, 70623.4, 70853.2),
    ("03-25 20:00", 70853.3, 71606.0, 70603.0, 71297.5),
    ("03-26 00:00", 71297.5, 71408.1, 70640.0, 70881.9),
    ("03-26 04:00", 70882.0, 70882.0, 69722.6, 70053.8),
    ("03-26 08:00", 70053.8, 70131.5, 69127.2, 69239.3),
    ("03-26 12:00", 69239.3, 69872.2, 68553.4, 69054.8),
    ("03-26 16:00", 69054.9, 69138.8, 68115.8, 68502.7),
    ("03-26 20:00", 68502.7, 69466.6, 68378.5, 68788.0),
    ("03-27 00:00", 68788.1, 69142.7, 68458.5, 68728.8),
    ("03-27 04:00", 68728.8, 68925.0, 68257.2, 68501.7),
    ("03-27 08:00", 68501.8, 68619.9, 66175.4, 66663.2),
    ("03-27 12:00", 66663.3, 66742.2, 65681.5, 66092.0),
    ("03-27 16:00", 66091.9, 66267.4, 65501.0, 66005.4),
    ("03-27 20:00", 66005.5, 66384.0, 65766.1, 66364.2),
    ("03-28 00:00", 66364.1, 66472.4, 65888.0, 66191.8),
    ("03-28 04:00", 66191.8, 66533.9, 66068.3, 66520.8),
    ("03-28 08:00", 66520.9, 66529.4, 66087.3, 66288.5),
    ("03-28 12:00", 66288.4, 67284.0, 66191.7, 66982.3),
    ("03-28 16:00", 66982.4, 67065.0, 66644.0, 66873.0),
    ("03-28 20:00", 66873.0, 66978.0, 66233.6, 66334.8),
    ("03-29 00:00", 66334.8, 67100.0, 66235.6, 66875.7),
    ("03-29 04:00", 66875.7, 66907.5, 66521.4, 66632.5),
    ("03-29 08:00", 66632.4, 66986.8, 66375.5, 66780.8),
    ("03-29 12:00", 66780.8, 66849.0, 66288.1, 66500.0),
    ("03-29 16:00", 66499.9, 66639.0, 66111.0, 66320.2),
    ("03-29 20:00", 66320.3, 66767.9, 64918.2, 65977.9),
    ("03-30 00:00", 65978.0, 67487.7, 65754.2, 67139.8),
    ("03-30 04:00", 67140.0, 67777.0, 67129.3, 67595.9),
    ("03-30 08:00", 67595.9, 67998.0, 67333.3, 67651.5),
    ("03-30 12:00", 67651.5, 68148.4, 67055.0, 67590.2),
    ("03-30 16:00", 67590.2, 67614.9, 66200.1, 66516.0),
    ("03-30 20:00", 66515.9, 66973.5, 66377.1, 66764.4),
    ("03-31 00:00", 66764.4, 68377.0, 66498.9, 67670.8),
    ("03-31 04:00", 67670.8, 67865.7, 67071.9, 67343.8),
    ("03-31 08:00", 67343.9, 67476.9, 65938.0, 66652.4),
    ("03-31 12:00", 66652.4, 67765.8, 66374.4, 66700.0),
    ("03-31 16:00", 66700.0, 68600.0, 66695.9, 67803.0),
    ("03-31 20:00", 67803.0, 68382.9, 67794.8, 68241.5),
    ("04-01 00:00", 68241.4, 68330.0, 67534.9, 68134.0),
    ("04-01 04:00", 68134.0, 69288.0, 67965.0, 68651.9),
    ("04-01 08:00", 68651.9, 68821.5, 68360.0, 68669.9),
    ("04-01 12:00", 68670.0, 68938.8, 67883.7, 68877.0),
    ("04-01 16:00", 68876.9, 69142.6, 67900.4, 68143.8),
    ("04-01 20:00", 68143.7, 68510.6, 67927.0, 68086.5),
    ("04-02 00:00", 68086.4, 68639.1, 66455.9, 66538.4),
    ("04-02 04:00", 66538.4, 66898.5, 66171.8, 66887.9),
    ("04-02 08:00", 66887.8, 66887.9, 66065.1, 66180.6),
    ("04-02 12:00", 66180.6, 67080.0, 65676.1, 66810.6),
    ("04-02 16:00", 66810.6, 67400.0, 66550.0, 66943.2),
    ("04-02 20:00", 66943.2, 67078.9, 66681.3, 66868.5),
    ("04-03 00:00", 66868.6, 66976.2, 66240.0, 66550.0),
    ("04-03 04:00", 66550.1, 67233.3, 66375.1, 67008.8),
    ("04-03 08:00", 67008.8, 67258.0, 66644.0, 66983.4),
    ("04-03 12:00", 66983.5, 67350.0, 66478.5, 66806.1),
    ("04-03 16:00", 66806.0, 67046.1, 66714.1, 66857.0),
    ("04-03 20:00", 66857.0, 66946.3, 66791.8, 66930.0),
    ("04-04 00:00", 66930.0, 66935.3, 66773.3, 66799.1),
    ("04-04 04:00", 66799.1, 67023.7, 66745.5, 66982.0),
    ("04-04 08:00", 66982.1, 67223.8, 66874.5, 67128.9),
    ("04-04 12:00", 67128.9, 67554.5, 67003.7, 67357.3),
    ("04-04 16:00", 67357.4, 67523.8, 67226.4, 67262.7),
    ("04-04 20:00", 67262.8, 67452.7, 67150.6, 67271.0),
    ("04-05 00:00", 67271.1, 67279.2, 66900.0, 67113.5),
    ("04-05 04:00", 67113.4, 67160.0, 66575.5, 66787.4),
    ("04-05 08:00", 66787.4, 67132.8, 66782.1, 66972.7),
    ("04-05 12:00", 66972.7, 67828.6, 66650.0, 67272.2),
    ("04-05 16:00", 67272.2, 67540.0, 67132.2, 67329.1),
    ("04-05 20:00", 67329.1, 69108.0, 67302.4, 68997.9),
    ("04-06 00:00", 68997.9, 69583.0, 68740.2, 69092.4),
    ("04-06 04:00", 69092.3, 69338.2, 68769.6, 69089.7),
    ("04-06 08:00", 69089.8, 69225.0, 69047.7, 69199.9),
    ("04-06 15:00", 69583.5, 69931.9, 69088.0, 69922.5),
    ("04-06 19:00", 69922.4, 70332.5, 69240.0, 69719.1),

    ("04-07 04:00", 68746.4, 68955.6, 68400.6, 68592.1),

    ("04-07 08:00", 68592.0, 69219.0, 68033.0, 68310.8),

    ("04-08 08:00", 71612.1, 71945.0, 71367.0, 71650.2),

    ("04-06 12:00", 69583.5, 69931.9, 69088.0, 69922.5),
    ("04-06 16:00", 69922.4, 70332.5, 69240.0, 69704.8),
    ("04-06 20:00", 69704.8, 69940.0, 68227.5, 68817.9),
    ("04-07 00:00", 68817.9, 69111.8, 68241.9, 68746.3),
    ("04-07 12:00", 68310.7, 68613.8, 67711.0, 68138.4),
    ("04-07 16:00", 68138.5, 69068.6, 68049.9, 68975.9),
    ("04-07 20:00", 68975.9, 72743.4, 68975.9, 71890.2),
    ("04-08 00:00", 71890.2, 72086.4, 71186.0, 71259.6),
    ("04-08 04:00", 71259.7, 71919.0, 71250.0, 71612.0),
    ("04-08 12:00", 71650.2, 72858.5, 70671.6, 71274.8),
    ("04-08 16:00", 71274.9, 71934.5, 70980.0, 71283.0),
    ("04-08 20:00", 71283.0, 71726.7, 70850.9, 71038.1),
    ("04-09 00:00", 71038.2, 71168.0, 70428.0, 70961.2),
    ("04-09 04:00", 70961.2, 71087.8, 70666.0, 70945.0),
    ("04-09 08:00", 70945.0, 71533.0, 70831.9, 71109.9),
    ("04-09 12:00", 71109.9, 72320.0, 70470.2, 72108.0),
    ("04-09 16:00", 72108.0, 72517.9, 71688.8, 72055.9),
    ("04-09 20:00", 72055.8, 73128.0, 71539.9, 71750.4),
    ("04-10 00:00", 71750.4, 72350.0, 71546.0, 71837.3),
    ("04-10 04:00", 71837.3, 72243.6, 71382.1, 71461.2),
    ("04-10 08:00", 71461.2, 72229.0, 71395.0, 72092.7),

    ("04-10 12:00", 72092.8, 73255.7, 71868.5, 72421.0),

    ("04-10 16:00", 72421.1, 73223.4, 72350.0, 73187.3),
    ("04-10 20:00", 73187.4, 73450.0, 72669.1, 72917.4),
    ("04-11 00:00", 72917.4, 73066.2, 72615.0, 72835.1),
    ("04-11 04:00", 72835.1, 72921.5, 72566.4, 72707.7),
    ("04-11 08:00", 72707.8, 72886.0, 72580.0, 72868.2),
    ("04-11 12:00", 72868.2, 72945.0, 72451.9, 72817.3),
    ("04-11 16:00", 72817.3, 73773.4, 72775.3, 73635.9),
    ("04-11 20:00", 73635.9, 73648.8, 72861.2, 73013.4),
    ("04-12 00:00", 73013.4, 73094.4, 71259.0, 71563.6),
    ("04-12 04:00", 71563.6, 71750.0, 71369.7, 71628.1),
    ("04-12 08:00", 71628.2, 71750.0, 71309.7, 71435.0),
    ("04-12 12:00", 71435.0, 71478.0, 70566.5, 70856.2),
    ("04-12 16:00", 70856.1, 71199.0, 70777.0, 71055.2),
    ("04-12 20:00", 71055.2, 71423.9, 70458.2, 70711.1),

    ("04-13 00:00", 70711.2, 71245.0, 70574.0, 70944.8),
    ("04-13 04:00", 70944.8, 71114.9, 70627.9, 70780.0),
    ("04-13 08:00", 70780.1, 70960.3, 70517.3, 70883.9),
    ("04-13 12:00", 70883.9, 72431.0, 70722.3, 71823.6),
    ("04-13 16:00", 71823.6, 73441.7, 71629.5, 73272.2),
    ("04-13 20:00", 73272.1, 74870.0, 72953.3, 74385.0),
    ("04-14 00:00", 74384.9, 74583.1, 73946.9, 74408.8),
    ("04-14 04:00", 74408.8, 74900.0, 74112.2, 74513.4),
    ("04-14 08:00", 74513.3, 74873.5, 74267.2, 74342.4),
    ("04-14 12:00", 74342.4, 76009.0, 74234.0, 75268.1),
    ("04-14 16:00", 75268.1, 75684.9, 73789.7, 74176.4),
    ("04-14 20:00", 74176.5, 74387.7, 73766.8, 74106.9),
    ("04-15 00:00", 74106.9, 74739.2, 74085.0, 74296.8),
    ("04-15 04:00", 74296.8, 74400.0, 73449.0, 73705.1),

    ("04-15 08:00", 73705.2, 74227.5, 73640.1, 74155.1),
    ("04-15 12:00", 74155.0, 74473.5, 73540.0, 73797.5),
    ("04-15 16:00", 73797.5, 75240.0, 73714.9, 74957.8),
    ("04-15 20:00", 74957.7, 75425.6, 74466.5, 74776.2),
    ("04-16 00:00", 74776.3, 75232.7, 74400.0, 74851.9),
    ("04-16 04:00", 74851.9, 75130.0, 74590.3, 74667.7),

    ("04-16 08:00", 74667.7, 74866.9, 74226.2, 74528.4),
    ("04-16 12:00", 74528.4, 74981.1, 73256.8, 74659.5),
    ("04-16 16:00", 74659.5, 75378.1, 73873.5, 75309.4),
    ("04-16 20:00", 75309.5, 75500.0, 74736.5, 75106.8),
    ("04-17 00:00", 75106.8, 75118.4, 74480.0, 74582.8),
    ("04-17 04:00", 74582.8, 75060.4, 74508.2, 75047.4),
    ("04-17 08:00", 75047.4, 76350.0, 74951.6, 75542.2),
    ("04-17 12:00", 75542.1, 77999.9, 75481.8, 77736.2),
    ("04-17 16:00", 77736.2, 78300.0, 76921.9, 77348.8),
    ("04-17 20:00", 77349.2, 77566.0, 76854.2, 77030.6),
    ("04-18 00:00", 77030.6, 77380.0, 76903.2, 76964.3),
    ("04-18 04:00", 76964.4, 77233.6, 76824.1, 76951.0),
    ("04-18 08:00", 76951.0, 77004.2, 75710.6, 76002.0),

    ("04-18 12:00", 76002.0, 76342.7, 75738.0, 76124.8),

    ("04-18 16:00", 76124.8, 76176.6, 75395.9, 75604.2),
    ("04-18 20:00", 75604.2, 75843.3, 75551.0, 75653.8),
    ("04-19 00:00", 75653.8, 75804.0, 75314.0, 75473.0),
    ("04-19 04:00", 75472.9, 75747.3, 74824.3, 75205.6),

    ("04-19 08:00", 75205.7, 75589.2, 74863.6, 75557.4),

    ("04-19 12:00", 75557.5, 76200.0, 75342.3, 75807.6),

    ("04-19 16:00", 75807.7, 75817.7, 74550.0, 74917.9),
    ("04-19 20:00", 74918.0, 74920.2, 73700.2, 73758.4),

    ("04-20 00:00", 73758.4, 74697.6, 73669.0, 74593.9),
    ("04-20 04:00", 74593.9, 75539.3, 74061.2, 74795.5),
    ("04-20 08:00", 74795.5, 75375.1, 74563.2, 75148.7),

    ("04-20 12:00", 75148.8, 75750.0, 74639.5, 75668.1),
    ("04-20 16:00", 75668.1, 76449.8, 75242.5, 76252.5),

    ("04-20 20:00", 76252.5, 76531.0, 75556.2, 75790.1),
    ("04-21 00:00", 75790.1, 76232.3, 75433.1, 75669.1),
    ("04-21 04:00", 75669.1, 76276.6, 75558.8, 76050.0),

    ("04-21 08:00", 76050.0, 76999.0, 76025.0, 76408.3),

    ("04-21 12:00", 76408.3, 76574.3, 75355.2, 75799.9),

    ("04-21 16:00", 75800.0, 76155.0, 74777.9, 74988.6),

    ("04-21 20:00", 74988.7, 76396.2, 74942.2, 76288.2),
    ("04-22 00:00", 76288.3, 77699.0, 76078.6, 77488.3),
    ("04-22 04:00", 77488.4, 78447.5, 77321.7, 77979.8),

    ("04-22 08:00", 77979.7, 78365.8, 77895.3, 78263.2),

    ("04-22 12:00", 78263.2, 79370.0, 78060.0, 79234.3),

    ("04-22 16:00", 79234.3, 79444.0, 78586.7, 78791.3),

    ("04-22 20:00", 78791.3, 78868.9, 78111.6, 78139.8),
    ("04-23 00:00", 78139.7, 78534.9, 77410.7, 77704.3),
    ("04-23 04:00", 77704.3, 78310.1, 77627.4, 78009.1),

    ("04-23 08:00", 78009.1, 78142.2, 76504.6, 77649.9),

    ("04-23 12:00", 77650.0, 78648.0, 77322.8, 78329.2),

    ("04-23 16:00", 78329.3, 78466.8, 76900.1, 77670.5),
    ("04-23 20:00", 77670.4, 78299.0, 77598.4, 78216.8),
    ("04-24 00:00", 78217.4, 78546.0, 77500.0, 77690.1),
    ("04-24 04:00", 77690.1, 78019.2, 77401.5, 77620.5),

    ("04-24 08:00", 77620.5, 78346.1, 77355.8, 78194.8),

    ("04-24 12:00", 78194.9, 78432.9, 77521.0, 78007.3),

    ("04-24 16:00", 78007.3, 78031.9, 77308.0, 77596.1),

    ("04-24 20:00", 77596.0, 77727.0, 77206.8, 77395.4),

    ("04-25 00:00", 77395.3, 77678.0, 77254.7, 77629.0),
    ("04-25 04:00", 77629.0, 77653.2, 77400.0, 77449.9),
    ("04-25 08:00", 77449.9, 77847.0, 77444.0, 77638.7),
    ("04-25 12:00", 77638.7, 77719.1, 77263.0, 77289.3),

    ("04-25 16:00", 77289.3, 77411.8, 77100.0, 77285.6),

    ("04-25 20:00", 77285.7, 77615.7, 77267.3, 77585.0),
    ("04-26 00:00", 77585.0, 77607.7, 77280.0, 77349.3),
    ("04-26 04:00", 77349.3, 78164.7, 77338.4, 78061.5),

    ("04-26 08:00", 78061.5, 78182.8, 77880.0, 78050.0),

    ("04-26 12:00", 78050.0, 78136.5, 77715.0, 78007.9),

    ("04-26 16:00", 78007.9, 78477.9, 77815.0, 78183.1),

    ("04-26 20:00", 78183.2, 78994.8, 77777.0, 78613.5),

    ("04-27 00:00", 78614.4, 79455.0, 78319.1, 79065.1),
    ("04-27 04:00", 79065.1, 79128.1, 77408.6, 77556.7),

    ("04-27 08:00", 77556.7, 77949.9, 77500.0, 77804.3),
    ("04-27 12:00", 77804.3, 78232.0, 76524.0, 76760.0),
    ("04-27 16:00", 76760.0, 76902.7, 76400.0, 76844.4),

    ("04-27 20:00", 76844.3, 77419.7, 76714.8, 77331.2),
    ("04-28 00:00", 77331.2, 77450.0, 76632.4, 76770.6),
    ("04-28 04:00", 76770.6, 77132.4, 76324.1, 76828.4),
    ("04-28 08:00", 76828.3, 76956.0, 76088.0, 76198.8),
    ("04-28 12:00", 76198.9, 76403.7, 75635.6, 76027.8),
    ("04-28 16:00", 76027.7, 76352.0, 75840.3, 76293.6),
    ("04-28 20:00", 76293.5, 76448.0, 76150.0, 76298.1),
    ("04-29 00:00", 76298.2, 77098.8, 76138.7, 76955.7),
    ("04-29 04:00", 76955.7, 77432.1, 76839.8, 77003.8),
    ("04-29 08:00", 77003.8, 77873.2, 76918.5, 77552.5),
    ("04-29 12:00", 77552.5, 77563.6, 75675.2, 75889.1),
    ("04-29 16:00", 75889.1, 76220.0, 74868.0, 75518.5),
    ("04-29 20:00", 75518.4, 76061.2, 75448.0, 75749.9),
    ("04-30 00:00", 75749.9, 76445.0, 75448.9, 75882.1),
    ("04-30 04:00", 75881.6, 76148.0, 75273.5, 76129.9),
    ("04-30 08:00", 76129.9, 76332.6, 75836.0, 76032.9),

    ("04-30 12:00", 76032.9, 76630.3, 76009.8, 76423.0),
    ("04-30 16:00", 76423.0, 76470.5, 76060.4, 76366.7),

    ("04-30 20:00", 76366.7, 76536.2, 76155.1, 76305.4),

    ("05-01 00:00", 76305.4, 77421.2, 76265.4, 77082.6),
    ("05-01 04:00", 77082.6, 77177.1, 76833.7, 77100.0),
    ("05-01 08:00", 77099.9, 77588.4, 77010.5, 77429.5),
    ("05-01 12:00", 77429.6, 78879.9, 77368.2, 78395.4),
    ("05-01 16:00", 78395.4, 78642.0, 78081.5, 78316.9),
    ("05-01 20:00", 78317.0, 78402.9, 77717.7, 78192.0),
    ("05-02 00:00", 78191.9, 78503.9, 78123.0, 78377.7),
    ("05-02 04:00", 78377.7, 78416.8, 77979.3, 78181.6),
    ("05-02 08:00", 78181.6, 78359.2, 78055.7, 78105.7),

    ("05-02 12:00", 78105.7, 78458.2, 78056.0, 78449.8),
    ("05-02 16:00", 78449.8, 78565.9, 78277.0, 78443.8),

    ("05-02 20:00", 78444.1, 79145.0, 78376.0, 78652.9),
]

# =================== GECMIS RUN VERILERI R2-R10 ===================

HISTORICAL_DATA = {
    "R2": {
        "data_15m": {"current_price": 66377.3, "ma5": 66385.92, "ma10": 66425.57, "ma30": 66567.79, "volume": 64100000, "volume_ma5": 74200000, "volume_ma10": 75800000, "net_long": 509, "net_short": -19000, "futures_cvd": -19000000, "spot_cvd": -3400, "taker_ls_ratio": 1.5527, "oi": 95800, "oi_delta": 15.1, "liquidations": {"long": None, "short": 6800}},
        "data_1h": {"current_price": 66382.8, "ma5": 66490.58, "ma10": 66581.52, "ma30": 66673.17, "volume": 309800000, "volume_ma5": 283200000, "volume_ma10": 239000000, "net_long": 27000, "net_short": 1000, "futures_cvd": 78400000, "spot_cvd": -4900, "taker_ls_ratio": 0.8274, "oi": 95800, "oi_delta": 310.0, "liquidations": {"long": 385900, "short": 9200}},
        "data_4h": {"current_price": 66388.0, "ma5": 66634.35, "ma10": 66617.09, "ma30": 68264.51, "volume": 500300000, "volume_ma5": 819400000, "volume_ma10": 915700000, "net_long": -24700, "net_short": -22400, "futures_cvd": 4800000, "spot_cvd": -86400, "taker_ls_ratio": 0.8789, "oi": 95800, "oi_delta": 405.3, "liquidations": {"long": 400700, "short": 111000}},
        "actual": 'DOWN', "move": -428,
        "mfe_4h": 1465, "mae_4h": 385,
        "mfe_24h": 1465, "mae_24h": 1766, "max_high_24h": 67487.7, "min_low_24h": 64918.2,
        "run_time": "03-29 21:42",
        "whale_acct_ls": 0.9467,
        "api_whale_account": [['03-29 00:00', 0.9078], ['03-29 01:00', 0.9106], ['03-29 02:00', 0.9107], ['03-29 03:00', 0.9143], ['03-29 04:00', 0.9278], ['03-29 05:00', 0.9291], ['03-29 06:00', 0.9302], ['03-29 07:00', 0.9332], ['03-29 08:00', 0.9434], ['03-29 09:00', 0.9427], ['03-29 10:00', 0.9423]],
        "api_whale_position": [['03-29 00:00', 2.391], ['03-29 01:00', 2.3807], ['03-29 02:00', 2.3727], ['03-29 03:00', 2.4014], ['03-29 04:00', 2.3738], ['03-29 05:00', 2.3523], ['03-29 06:00', 2.3636], ['03-29 07:00', 2.367], ['03-29 08:00', 2.3568], ['03-29 09:00', 2.358], ['03-29 10:00', 2.3434]],
        "api_open_interest": [['03-29 00:00', 93836.99], ['03-29 01:00', 93871.89], ['03-29 02:00', 94087.4], ['03-29 03:00', 94288.16], ['03-29 04:00', 94786.94], ['03-29 05:00', 94555.72], ['03-29 06:00', 94597.18], ['03-29 07:00', 94738.05], ['03-29 08:00', 95254.7], ['03-29 09:00', 95350.31], ['03-29 10:00', 95273.52]],
        "api_funding_rate": [['03-29 00:00', -3.68e-05, 66337.79], ['03-29 08:00', -1.2e-07, 66633.23]],
        "klines_4h": [["03-28 07:00", 66191.8, 66533.9, 66068.3, 66520.8], ["03-28 11:00", 66520.9, 66529.4, 66087.3, 66288.5], ["03-28 15:00", 66288.4, 67284.0, 66191.7, 66982.3], ["03-28 19:00", 66982.4, 67065.0, 66644.0, 66873.0], ["03-28 23:00", 66873.0, 66978.0, 66233.6, 66334.8], ["03-29 03:00", 66334.8, 67100.0, 66235.6, 66875.7], ["03-29 07:00", 66875.7, 66907.5, 66521.4, 66632.5], ["03-29 11:00", 66632.4, 66986.8, 66375.5, 66780.8], ["03-29 15:00", 66780.8, 66849.0, 66288.1, 66500.0], ["03-29 19:00", 66499.9, 66639.0, 66111.0, 66320.2]],
        "klines_1h": [["03-28 16:00", 66416.7, 67148.7, 66363.6, 66813.3], ["03-28 17:00", 66813.4, 66942.3, 66631.5, 66716.2], ["03-28 18:00", 66716.1, 67284.0, 66678.1, 66982.3], ["03-28 19:00", 66982.4, 67065.0, 66821.3, 66894.3], ["03-28 20:00", 66894.3, 66965.7, 66644.0, 66808.6], ["03-28 21:00", 66808.6, 66920.0, 66801.0, 66871.1], ["03-28 22:00", 66871.2, 66916.5, 66764.7, 66873.0], ["03-28 23:00", 66873.0, 66978.0, 66868.3, 66885.5], ["03-29 00:00", 66885.6, 66890.0, 66526.8, 66644.8], ["03-29 01:00", 66644.9, 66758.9, 66562.0, 66729.0], ["03-29 02:00", 66729.0, 66729.0, 66233.6, 66334.8], ["03-29 03:00", 66334.8, 66468.6, 66235.6, 66444.4], ["03-29 04:00", 66444.3, 66585.9, 66344.2, 66536.1], ["03-29 05:00", 66536.0, 66820.0, 66500.4, 66773.7], ["03-29 06:00", 66773.7, 67100.0, 66724.0, 66875.7], ["03-29 07:00", 66875.7, 66907.5, 66683.3, 66701.9], ["03-29 08:00", 66701.9, 66799.5, 66565.0, 66741.3], ["03-29 09:00", 66741.3, 66845.0, 66601.1, 66704.4], ["03-29 10:00", 66704.4, 66720.0, 66521.4, 66632.5], ["03-29 11:00", 66632.4, 66743.7, 66560.0, 66689.5], ["03-29 12:00", 66689.4, 66740.0, 66500.9, 66600.1], ["03-29 13:00", 66600.0, 66600.0, 66375.5, 66473.4], ["03-29 14:00", 66473.4, 66986.8, 66473.3, 66780.8], ["03-29 15:00", 66780.8, 66844.3, 66668.0, 66818.6], ["03-29 16:00", 66818.7, 66849.0, 66483.9, 66546.0], ["03-29 17:00", 66546.1, 66764.9, 66420.0, 66556.2], ["03-29 18:00", 66556.3, 66695.0, 66288.1, 66500.0], ["03-29 19:00", 66499.9, 66639.0, 66400.0, 66467.8], ["03-29 20:00", 66467.8, 66518.2, 66111.0, 66356.6], ["03-29 21:00", 66356.6, 66524.0, 66291.2, 66397.2]]
    },

    "R3": {
        "data_15m": {"current_price": 65972.7, "ma5": 66014.05, "ma10": 66308.27, "ma30": 66385.77, "volume": 298200000, "volume_ma5": 398500000, "volume_ma10": 217400000, "net_long": -1600, "net_short": -17400, "futures_cvd": -28100000, "spot_cvd": -2600, "taker_ls_ratio": 1.0515, "oi": 93900, "oi_delta": -238.2, "liquidations": {"long": 74100, "short": 167500}},
        "data_1h": {"current_price": 65989.1, "ma5": 66275.98, "ma10": 66365.77, "ma30": 66577.16, "volume": 300600000, "volume_ma5": 519200000, "volume_ma10": 390900000, "net_long": 25500, "net_short": 580, "futures_cvd": 74600000, "spot_cvd": -4800, "taker_ls_ratio": 1.0561, "oi": 93900, "oi_delta": -238.2, "liquidations": {"long": 74100, "short": 167500}},
        "data_4h": {"current_price": 65960.0, "ma5": 66438.7, "ma10": 66554.77, "ma30": 68110.29, "volume": 2470000000, "volume_ma5": 1170000000, "volume_ma10": 1130000000, "net_long": -25600, "net_short": -21900, "futures_cvd": -2600000, "spot_cvd": -88000, "taker_ls_ratio": 0.8405, "oi": 96000, "oi_delta": -2400, "liquidations": {"long": 1600000, "short": 555900}},
        "actual": 'UP', "move": 651,
        "mfe_4h": 1499, "mae_4h": 1071,
        "mfe_24h": 2159, "mae_24h": 1071, "max_high_24h": 68148.4, "min_low_24h": 64918.2,
        "run_time": "03-30 02:05",
        "whale_acct_ls": 0.9559,
        "api_whale_account": [['03-29 00:00', 0.9078], ['03-29 01:00', 0.9106], ['03-29 02:00', 0.9107], ['03-29 03:00', 0.9143], ['03-29 04:00', 0.9278], ['03-29 05:00', 0.9291], ['03-29 06:00', 0.9302], ['03-29 07:00', 0.9332], ['03-29 08:00', 0.9434], ['03-29 09:00', 0.9427], ['03-29 10:00', 0.9423], ['03-29 11:00', 0.9419], ['03-29 12:00', 0.9363], ['03-29 13:00', 0.931], ['03-29 14:00', 0.9336]],
        "api_whale_position": [['03-29 00:00', 2.391], ['03-29 01:00', 2.3807], ['03-29 02:00', 2.3727], ['03-29 03:00', 2.4014], ['03-29 04:00', 2.3738], ['03-29 05:00', 2.3523], ['03-29 06:00', 2.3636], ['03-29 07:00', 2.367], ['03-29 08:00', 2.3568], ['03-29 09:00', 2.358], ['03-29 10:00', 2.3434], ['03-29 11:00', 2.3167], ['03-29 12:00', 2.2321], ['03-29 13:00', 2.2258], ['03-29 14:00', 2.1918]],
        "api_open_interest": [['03-29 00:00', 93836.99], ['03-29 01:00', 93871.89], ['03-29 02:00', 94087.4], ['03-29 03:00', 94288.16], ['03-29 04:00', 94786.94], ['03-29 05:00', 94555.72], ['03-29 06:00', 94597.18], ['03-29 07:00', 94738.05], ['03-29 08:00', 95254.7], ['03-29 09:00', 95350.31], ['03-29 10:00', 95273.52], ['03-29 11:00', 95279.6], ['03-29 12:00', 95105.98], ['03-29 13:00', 95361.61], ['03-29 14:00', 95282.19]],
        "api_funding_rate": [['03-29 00:00', -3.68e-05, 66337.79], ['03-29 08:00', -1.2e-07, 66633.23]],
        "klines_4h": [["03-28 11:00", 66520.9, 66529.4, 66087.3, 66288.5], ["03-28 15:00", 66288.4, 67284.0, 66191.7, 66982.3], ["03-28 19:00", 66982.4, 67065.0, 66644.0, 66873.0], ["03-28 23:00", 66873.0, 66978.0, 66233.6, 66334.8], ["03-29 03:00", 66334.8, 67100.0, 66235.6, 66875.7], ["03-29 07:00", 66875.7, 66907.5, 66521.4, 66632.5], ["03-29 11:00", 66632.4, 66986.8, 66375.5, 66780.8], ["03-29 15:00", 66780.8, 66849.0, 66288.1, 66500.0], ["03-29 19:00", 66499.9, 66639.0, 66111.0, 66320.2], ["03-29 23:00", 66320.3, 66767.9, 64918.2, 65977.9]],
        "klines_1h": [["03-28 21:00", 66808.6, 66920.0, 66801.0, 66871.1], ["03-28 22:00", 66871.2, 66916.5, 66764.7, 66873.0], ["03-28 23:00", 66873.0, 66978.0, 66868.3, 66885.5], ["03-29 00:00", 66885.6, 66890.0, 66526.8, 66644.8], ["03-29 01:00", 66644.9, 66758.9, 66562.0, 66729.0], ["03-29 02:00", 66729.0, 66729.0, 66233.6, 66334.8], ["03-29 03:00", 66334.8, 66468.6, 66235.6, 66444.4], ["03-29 04:00", 66444.3, 66585.9, 66344.2, 66536.1], ["03-29 05:00", 66536.0, 66820.0, 66500.4, 66773.7], ["03-29 06:00", 66773.7, 67100.0, 66724.0, 66875.7], ["03-29 07:00", 66875.7, 66907.5, 66683.3, 66701.9], ["03-29 08:00", 66701.9, 66799.5, 66565.0, 66741.3], ["03-29 09:00", 66741.3, 66845.0, 66601.1, 66704.4], ["03-29 10:00", 66704.4, 66720.0, 66521.4, 66632.5], ["03-29 11:00", 66632.4, 66743.7, 66560.0, 66689.5], ["03-29 12:00", 66689.4, 66740.0, 66500.9, 66600.1], ["03-29 13:00", 66600.0, 66600.0, 66375.5, 66473.4], ["03-29 14:00", 66473.4, 66986.8, 66473.3, 66780.8], ["03-29 15:00", 66780.8, 66844.3, 66668.0, 66818.6], ["03-29 16:00", 66818.7, 66849.0, 66483.9, 66546.0], ["03-29 17:00", 66546.1, 66764.9, 66420.0, 66556.2], ["03-29 18:00", 66556.3, 66695.0, 66288.1, 66500.0], ["03-29 19:00", 66499.9, 66639.0, 66400.0, 66467.8], ["03-29 20:00", 66467.8, 66518.2, 66111.0, 66356.6], ["03-29 21:00", 66356.6, 66524.0, 66291.2, 66397.2], ["03-29 22:00", 66397.1, 66453.4, 66282.1, 66320.2], ["03-29 23:00", 66320.3, 66767.9, 66312.7, 66578.6], ["03-30 00:00", 66578.6, 66734.5, 66477.5, 66678.8], ["03-30 01:00", 66678.8, 66686.1, 64918.2, 65820.3], ["03-30 02:00", 65820.2, 66350.4, 65819.0, 65977.9]]
    },

    "R4": {
        "data_15m": {"current_price": 66586.0, "ma5": 66476.55, "ma10": 66300.55, "ma30": 66336.23, "volume": 129300000, "volume_ma5": 126900000, "volume_ma10": 185300000, "net_long": -2300, "net_short": -16300, "futures_cvd": -28400000, "spot_cvd": -2500, "taker_ls_ratio": 1.0716, "oi": 92800, "oi_delta": -256.8, "liquidations": {"long": 17700, "short": 4300}},
        "data_1h": {"current_price": 66578.0, "ma5": 66261.29, "ma10": 66342.67, "ma30": 66546.53, "volume": 490900000, "volume_ma5": 840700000, "volume_ma10": 530600000, "net_long": 24500, "net_short": 1700, "futures_cvd": 76200000, "spot_cvd": -4600, "taker_ls_ratio": 1.0632, "oi": 93100, "oi_delta": -555.9, "liquidations": {"long": 60100, "short": 78700}},
        "data_4h": {"current_price": 66611.0, "ma5": 66438.38, "ma10": 66589.02, "ma30": 67975.01, "volume": 1590000000, "volume_ma5": 1440000000, "volume_ma10": 1260000000, "net_long": -29900, "net_short": -21700, "futures_cvd": -1800000, "spot_cvd": -88400, "taker_ls_ratio": 1.1062, "oi": 94200, "oi_delta": -1700, "liquidations": {"long": 632700, "short": 1200000}},
        "actual": 'UP', "move": 690,
        "mfe_4h": 1199, "mae_4h": 824,
        "mfe_24h": 1799, "mae_24h": 824, "max_high_24h": 68148.4, "min_low_24h": 65754.2,
        "run_time": "03-30 05:01",
        "whale_acct_ls": 0.9529,
        "api_whale_account": [['03-29 00:00', 0.9078], ['03-29 01:00', 0.9106], ['03-29 02:00', 0.9107], ['03-29 03:00', 0.9143], ['03-29 04:00', 0.9278], ['03-29 05:00', 0.9291], ['03-29 06:00', 0.9302], ['03-29 07:00', 0.9332], ['03-29 08:00', 0.9434], ['03-29 09:00', 0.9427], ['03-29 10:00', 0.9423], ['03-29 11:00', 0.9419], ['03-29 12:00', 0.9363], ['03-29 13:00', 0.931], ['03-29 14:00', 0.9336], ['03-29 15:00', 0.9242], ['03-29 16:00', 0.9308], ['03-29 17:00', 0.935], ['03-29 18:00', 0.9467]],
        "api_whale_position": [['03-29 00:00', 2.391], ['03-29 01:00', 2.3807], ['03-29 02:00', 2.3727], ['03-29 03:00', 2.4014], ['03-29 04:00', 2.3738], ['03-29 05:00', 2.3523], ['03-29 06:00', 2.3636], ['03-29 07:00', 2.367], ['03-29 08:00', 2.3568], ['03-29 09:00', 2.358], ['03-29 10:00', 2.3434], ['03-29 11:00', 2.3167], ['03-29 12:00', 2.2321], ['03-29 13:00', 2.2258], ['03-29 14:00', 2.1918], ['03-29 15:00', 2.2362], ['03-29 16:00', 2.2394], ['03-29 17:00', 2.2352], ['03-29 18:00', 2.2185]],
        "api_open_interest": [['03-29 00:00', 93836.99], ['03-29 01:00', 93871.89], ['03-29 02:00', 94087.4], ['03-29 03:00', 94288.16], ['03-29 04:00', 94786.94], ['03-29 05:00', 94555.72], ['03-29 06:00', 94597.18], ['03-29 07:00', 94738.05], ['03-29 08:00', 95254.7], ['03-29 09:00', 95350.31], ['03-29 10:00', 95273.52], ['03-29 11:00', 95279.6], ['03-29 12:00', 95105.98], ['03-29 13:00', 95361.61], ['03-29 14:00', 95282.19], ['03-29 15:00', 95518.23], ['03-29 16:00', 95445.71], ['03-29 17:00', 95541.09], ['03-29 18:00', 95879.2]],
        "api_funding_rate": [['03-29 00:00', -3.68e-05, 66337.79], ['03-29 08:00', -1.2e-07, 66633.23], ['03-29 16:00', 2.677e-05, 66500.0]],
        "klines_4h": [["03-28 15:00", 66288.4, 67284.0, 66191.7, 66982.3], ["03-28 19:00", 66982.4, 67065.0, 66644.0, 66873.0], ["03-28 23:00", 66873.0, 66978.0, 66233.6, 66334.8], ["03-29 03:00", 66334.8, 67100.0, 66235.6, 66875.7], ["03-29 07:00", 66875.7, 66907.5, 66521.4, 66632.5], ["03-29 11:00", 66632.4, 66986.8, 66375.5, 66780.8], ["03-29 15:00", 66780.8, 66849.0, 66288.1, 66500.0], ["03-29 19:00", 66499.9, 66639.0, 66111.0, 66320.2], ["03-29 23:00", 66320.3, 66767.9, 64918.2, 65977.9], ["03-30 03:00", 65978.0, 67487.7, 65754.2, 67139.8]],
        "klines_1h": [["03-29 00:00", 66885.6, 66890.0, 66526.8, 66644.8], ["03-29 01:00", 66644.9, 66758.9, 66562.0, 66729.0], ["03-29 02:00", 66729.0, 66729.0, 66233.6, 66334.8], ["03-29 03:00", 66334.8, 66468.6, 66235.6, 66444.4], ["03-29 04:00", 66444.3, 66585.9, 66344.2, 66536.1], ["03-29 05:00", 66536.0, 66820.0, 66500.4, 66773.7], ["03-29 06:00", 66773.7, 67100.0, 66724.0, 66875.7], ["03-29 07:00", 66875.7, 66907.5, 66683.3, 66701.9], ["03-29 08:00", 66701.9, 66799.5, 66565.0, 66741.3], ["03-29 09:00", 66741.3, 66845.0, 66601.1, 66704.4], ["03-29 10:00", 66704.4, 66720.0, 66521.4, 66632.5], ["03-29 11:00", 66632.4, 66743.7, 66560.0, 66689.5], ["03-29 12:00", 66689.4, 66740.0, 66500.9, 66600.1], ["03-29 13:00", 66600.0, 66600.0, 66375.5, 66473.4], ["03-29 14:00", 66473.4, 66986.8, 66473.3, 66780.8], ["03-29 15:00", 66780.8, 66844.3, 66668.0, 66818.6], ["03-29 16:00", 66818.7, 66849.0, 66483.9, 66546.0], ["03-29 17:00", 66546.1, 66764.9, 66420.0, 66556.2], ["03-29 18:00", 66556.3, 66695.0, 66288.1, 66500.0], ["03-29 19:00", 66499.9, 66639.0, 66400.0, 66467.8], ["03-29 20:00", 66467.8, 66518.2, 66111.0, 66356.6], ["03-29 21:00", 66356.6, 66524.0, 66291.2, 66397.2], ["03-29 22:00", 66397.1, 66453.4, 66282.1, 66320.2], ["03-29 23:00", 66320.3, 66767.9, 66312.7, 66578.6], ["03-30 00:00", 66578.6, 66734.5, 66477.5, 66678.8], ["03-30 01:00", 66678.8, 66686.1, 64918.2, 65820.3], ["03-30 02:00", 65820.2, 66350.4, 65819.0, 65977.9], ["03-30 03:00", 65978.0, 67043.2, 65754.2, 66251.2], ["03-30 04:00", 66251.2, 66806.1, 66251.1, 66624.1], ["03-30 05:00", 66624.2, 67487.7, 66538.5, 67087.0]],
        "klines_15m": [["03-30 04:15", 66371.4, 66634.8, 66289.9, 66565.6], ["03-30 04:30", 66565.6, 66700.0, 66495.4, 66634.3], ["03-30 04:45", 66634.2, 66806.1, 66570.4, 66624.1], ["03-30 05:00", 66624.2, 66841.8, 66538.5, 66813.6]]
    },

    "R5": {
        "data_15m": {"current_price": 67294.1, "ma5": 67450.84, "ma10": 67463.06, "ma30": 66860.34, "volume": 163400000, "volume_ma5": 93400000, "volume_ma10": 118300000, "net_long": -2400, "net_short": -15300, "futures_cvd": -23500000, "spot_cvd": -2400, "taker_ls_ratio": 0.4587, "oi": 92400, "oi_delta": 105.5, "liquidations": {"long": 16400, "short": None}},
        "data_1h": {"current_price": 67276.8, "ma5": 67308.37, "ma10": 66789.41, "ma30": 66664.84, "volume": 216100000, "volume_ma5": 498300000, "volume_ma10": 669800000, "net_long": 24800, "net_short": 3400, "futures_cvd": 76100000, "spot_cvd": -4500, "taker_ls_ratio": 0.5292, "oi": 92400, "oi_delta": 122.0, "liquidations": {"long": 33400, "short": None}},
        "data_4h": {"current_price": 67300.9, "ma5": 66648.02, "ma10": 66673.67, "ma30": 67872.66, "volume": 1190000000, "volume_ma5": 1780000000, "volume_ma10": 1300000000, "net_long": -29000, "net_short": -20200, "futures_cvd": -2700000, "spot_cvd": -88400, "taker_ls_ratio": 0.9776, "oi": 92500, "oi_delta": 44.5, "liquidations": {"long": 54400, "short": 632400}},
        "actual": 'DOWN', "move": -365,
        "mfe_4h": 721, "mae_4h": 148,
        "mfe_24h": 1100, "mae_24h": 1077, "max_high_24h": 68148.4, "min_low_24h": 66200.1,
        "run_time": "03-30 09:27",
        "whale_acct_ls": 0.9328,
        "api_whale_account": [['03-29 04:00', 0.9278], ['03-29 05:00', 0.9291], ['03-29 06:00', 0.9302], ['03-29 07:00', 0.9332], ['03-29 08:00', 0.9434], ['03-29 09:00', 0.9427], ['03-29 10:00', 0.9423], ['03-29 11:00', 0.9419], ['03-29 12:00', 0.9363], ['03-29 13:00', 0.931], ['03-29 14:00', 0.9336], ['03-29 15:00', 0.9242], ['03-29 16:00', 0.9308], ['03-29 17:00', 0.935], ['03-29 18:00', 0.9467], ['03-29 19:00', 0.9468], ['03-29 20:00', 0.9427], ['03-29 21:00', 0.9535], ['03-29 22:00', 0.9569], ['03-29 23:00', 0.9559], ['03-30 00:00', 0.9492], ['03-30 01:00', 0.9516], ['03-30 02:00', 0.9529], ['03-30 03:00', 0.9498], ['03-30 04:00', 0.9463], ['03-30 05:00', 0.9404], ['03-30 06:00', 0.9328], ['03-30 07:00', 0.9256], ['03-30 08:00', 0.9318], ['03-30 09:00', 0.9331]],
        "api_whale_position": [['03-29 04:00', 2.3738], ['03-29 05:00', 2.3523], ['03-29 06:00', 2.3636], ['03-29 07:00', 2.367], ['03-29 08:00', 2.3568], ['03-29 09:00', 2.358], ['03-29 10:00', 2.3434], ['03-29 11:00', 2.3167], ['03-29 12:00', 2.2321], ['03-29 13:00', 2.2258], ['03-29 14:00', 2.1918], ['03-29 15:00', 2.2362], ['03-29 16:00', 2.2394], ['03-29 17:00', 2.2352], ['03-29 18:00', 2.2185], ['03-29 19:00', 2.2165], ['03-29 20:00', 2.2092], ['03-29 21:00', 2.2185], ['03-29 22:00', 2.2248], ['03-29 23:00', 2.2658], ['03-30 00:00', 2.2216], ['03-30 01:00', 2.2862], ['03-30 02:00', 2.2862], ['03-30 03:00', 2.2185], ['03-30 04:00', 2.1949], ['03-30 05:00', 2.1506], ['03-30 06:00', 2.0665], ['03-30 07:00', 2.0057], ['03-30 08:00', 1.9709], ['03-30 09:00', 1.9087]],
        "api_open_interest": [['03-29 04:00', 94786.94], ['03-29 05:00', 94555.72], ['03-29 06:00', 94597.18], ['03-29 07:00', 94738.05], ['03-29 08:00', 95254.7], ['03-29 09:00', 95350.31], ['03-29 10:00', 95273.52], ['03-29 11:00', 95279.6], ['03-29 12:00', 95105.98], ['03-29 13:00', 95361.61], ['03-29 14:00', 95282.19], ['03-29 15:00', 95518.23], ['03-29 16:00', 95445.71], ['03-29 17:00', 95541.09], ['03-29 18:00', 95879.2], ['03-29 19:00', 95856.59], ['03-29 20:00', 96035.42], ['03-29 21:00', 95420.87], ['03-29 22:00', 95570.05], ['03-29 23:00', 93864.43], ['03-30 00:00', 94223.42], ['03-30 01:00', 93116.67], ['03-30 02:00', 92583.43], ['03-30 03:00', 92325.91], ['03-30 04:00', 92468.18], ['03-30 05:00', 92413.32], ['03-30 06:00', 92391.25], ['03-30 07:00', 92285.13], ['03-30 08:00', 91921.01], ['03-30 09:00', 91085.25]],
        "api_funding_rate": [['03-29 00:00', -3.68e-05, 66337.79], ['03-29 08:00', -1.2e-07, 66633.23], ['03-29 16:00', 2.677e-05, 66500.0], ['03-30 00:00', 3e-06, 65973.4], ['03-30 08:00', 4.92e-06, 67596.7]],
        "klines_4h": [["03-28 19:00", 66982.4, 67065.0, 66644.0, 66873.0], ["03-28 23:00", 66873.0, 66978.0, 66233.6, 66334.8], ["03-29 03:00", 66334.8, 67100.0, 66235.6, 66875.7], ["03-29 07:00", 66875.7, 66907.5, 66521.4, 66632.5], ["03-29 11:00", 66632.4, 66986.8, 66375.5, 66780.8], ["03-29 15:00", 66780.8, 66849.0, 66288.1, 66500.0], ["03-29 19:00", 66499.9, 66639.0, 66111.0, 66320.2], ["03-29 23:00", 66320.3, 66767.9, 64918.2, 65977.9], ["03-30 03:00", 65978.0, 67487.7, 65754.2, 67139.8], ["03-30 07:00", 67140.0, 67777.0, 67129.3, 67595.9]],
        "klines_1h": [["03-29 04:00", 66444.3, 66585.9, 66344.2, 66536.1], ["03-29 05:00", 66536.0, 66820.0, 66500.4, 66773.7], ["03-29 06:00", 66773.7, 67100.0, 66724.0, 66875.7], ["03-29 07:00", 66875.7, 66907.5, 66683.3, 66701.9], ["03-29 08:00", 66701.9, 66799.5, 66565.0, 66741.3], ["03-29 09:00", 66741.3, 66845.0, 66601.1, 66704.4], ["03-29 10:00", 66704.4, 66720.0, 66521.4, 66632.5], ["03-29 11:00", 66632.4, 66743.7, 66560.0, 66689.5], ["03-29 12:00", 66689.4, 66740.0, 66500.9, 66600.1], ["03-29 13:00", 66600.0, 66600.0, 66375.5, 66473.4], ["03-29 14:00", 66473.4, 66986.8, 66473.3, 66780.8], ["03-29 15:00", 66780.8, 66844.3, 66668.0, 66818.6], ["03-29 16:00", 66818.7, 66849.0, 66483.9, 66546.0], ["03-29 17:00", 66546.1, 66764.9, 66420.0, 66556.2], ["03-29 18:00", 66556.3, 66695.0, 66288.1, 66500.0], ["03-29 19:00", 66499.9, 66639.0, 66400.0, 66467.8], ["03-29 20:00", 66467.8, 66518.2, 66111.0, 66356.6], ["03-29 21:00", 66356.6, 66524.0, 66291.2, 66397.2], ["03-29 22:00", 66397.1, 66453.4, 66282.1, 66320.2], ["03-29 23:00", 66320.3, 66767.9, 66312.7, 66578.6], ["03-30 00:00", 66578.6, 66734.5, 66477.5, 66678.8], ["03-30 01:00", 66678.8, 66686.1, 64918.2, 65820.3], ["03-30 02:00", 65820.2, 66350.4, 65819.0, 65977.9], ["03-30 03:00", 65978.0, 67043.2, 65754.2, 66251.2], ["03-30 04:00", 66251.2, 66806.1, 66251.1, 66624.1], ["03-30 05:00", 66624.2, 67487.7, 66538.5, 67087.0], ["03-30 06:00", 67087.1, 67288.8, 66934.7, 67139.8], ["03-30 07:00", 67140.0, 67625.1, 67129.3, 67579.1], ["03-30 08:00", 67579.2, 67777.0, 67404.0, 67459.0], ["03-30 09:00", 67459.0, 67550.0, 67238.6, 67273.4]],
        "klines_15m": [["03-30 04:15", 66371.4, 66634.8, 66289.9, 66565.6], ["03-30 04:30", 66565.6, 66700.0, 66495.4, 66634.3], ["03-30 04:45", 66634.2, 66806.1, 66570.4, 66624.1], ["03-30 05:00", 66624.2, 66841.8, 66538.5, 66813.6], ["03-30 05:15", 66813.6, 66875.0, 66650.2, 66720.0], ["03-30 05:30", 66720.0, 67021.0, 66560.0, 67021.0], ["03-30 05:45", 67021.0, 67487.7, 66974.0, 67087.0], ["03-30 06:00", 67087.1, 67117.2, 66934.7, 66980.1], ["03-30 06:15", 66980.1, 67264.5, 66966.0, 67208.9], ["03-30 06:30", 67208.9, 67254.6, 67103.7, 67168.6], ["03-30 06:45", 67168.5, 67288.8, 67086.2, 67139.8], ["03-30 07:00", 67140.0, 67466.0, 67129.3, 67389.6], ["03-30 07:15", 67389.6, 67625.1, 67339.3, 67414.8], ["03-30 07:30", 67414.7, 67529.5, 67350.0, 67386.9], ["03-30 07:45", 67386.9, 67620.0, 67384.3, 67579.1], ["03-30 08:00", 67579.2, 67777.0, 67542.7, 67608.9], ["03-30 08:15", 67609.0, 67699.0, 67549.9, 67623.5], ["03-30 08:30", 67623.6, 67671.2, 67412.0, 67463.5], ["03-30 08:45", 67463.5, 67529.2, 67404.0, 67459.0], ["03-30 09:00", 67459.0, 67550.0, 67378.3, 67409.9], ["03-30 09:15", 67409.9, 67430.0, 67238.6, 67288.5]]
    },

    "R6": {
        "data_15m": {"current_price": 66951.1, "ma5": 67224.39, "ma10": 67387.74, "ma30": 67532.57, "volume": 73700000, "volume_ma5": 90000000, "volume_ma10": 144200000, "net_long": -5100, "net_short": -13900, "futures_cvd": -24700000, "spot_cvd": -2700, "taker_ls_ratio": 0.4483, "oi": 91900, "oi_delta": -529.0, "liquidations": {"long": 101600, "short": None}},
        "data_1h": {"current_price": 66936.4, "ma5": 67422.67, "ma10": 67518.7, "ma30": 66973.85, "volume": 234300000, "volume_ma5": 629100000, "volume_ma10": 521100000, "net_long": 22200, "net_short": 2300, "futures_cvd": 65000000, "spot_cvd": -4600, "taker_ls_ratio": 0.6626, "oi": 92000, "oi_delta": -543.2, "liquidations": {"long": 233000, "short": 5500}},
        "data_4h": {"current_price": 66936.4, "ma5": 67382.73, "ma10": 66912.68, "ma30": 67511.91, "volume": 615400000, "volume_ma5": 1950000000, "volume_ma10": 1600000000, "net_long": -28300, "net_short": -21600, "futures_cvd": -5600000, "spot_cvd": -87800, "taker_ls_ratio": 0.9831, "oi": 91900, "oi_delta": -468.3, "liquidations": {"long": 604200, "short": 34900}},
        "actual": 'UP', "move": 2352,
        "mfe_4h": 736, "mae_4h": 678,
        "mfe_24h": 998, "mae_24h": 1664, "max_high_24h": 68600.0, "min_low_24h": 65938.0,
        "run_time": "03-30 20:20",
        "whale_acct_ls": 0.9235,
        "api_whale_account": [['03-29 08:00', 0.9434], ['03-29 09:00', 0.9427], ['03-29 10:00', 0.9423], ['03-29 11:00', 0.9419], ['03-29 12:00', 0.9363], ['03-29 13:00', 0.931], ['03-29 14:00', 0.9336], ['03-29 15:00', 0.9242], ['03-29 16:00', 0.9308], ['03-29 17:00', 0.935], ['03-29 18:00', 0.9467], ['03-29 19:00', 0.9468], ['03-29 20:00', 0.9427], ['03-29 21:00', 0.9535], ['03-29 22:00', 0.9569], ['03-29 23:00', 0.9559], ['03-30 00:00', 0.9492], ['03-30 01:00', 0.9516], ['03-30 02:00', 0.9529], ['03-30 03:00', 0.9498], ['03-30 04:00', 0.9463], ['03-30 05:00', 0.9404], ['03-30 06:00', 0.9328], ['03-30 07:00', 0.9256], ['03-30 08:00', 0.9318], ['03-30 09:00', 0.9331], ['03-30 10:00', 0.9303], ['03-30 11:00', 0.9314], ['03-30 12:00', 0.9291], ['03-30 13:00', 0.9283]],
        "api_whale_position": [['03-29 08:00', 2.3568], ['03-29 09:00', 2.358], ['03-29 10:00', 2.3434], ['03-29 11:00', 2.3167], ['03-29 12:00', 2.2321], ['03-29 13:00', 2.2258], ['03-29 14:00', 2.1918], ['03-29 15:00', 2.2362], ['03-29 16:00', 2.2394], ['03-29 17:00', 2.2352], ['03-29 18:00', 2.2185], ['03-29 19:00', 2.2165], ['03-29 20:00', 2.2092], ['03-29 21:00', 2.2185], ['03-29 22:00', 2.2248], ['03-29 23:00', 2.2658], ['03-30 00:00', 2.2216], ['03-30 01:00', 2.2862], ['03-30 02:00', 2.2862], ['03-30 03:00', 2.2185], ['03-30 04:00', 2.1949], ['03-30 05:00', 2.1506], ['03-30 06:00', 2.0665], ['03-30 07:00', 2.0057], ['03-30 08:00', 1.9709], ['03-30 09:00', 1.9087], ['03-30 10:00', 1.8531], ['03-30 11:00', 1.8612], ['03-30 12:00', 1.8539], ['03-30 13:00', 1.8121]],
        "api_open_interest": [['03-29 08:00', 95254.7], ['03-29 09:00', 95350.31], ['03-29 10:00', 95273.52], ['03-29 11:00', 95279.6], ['03-29 12:00', 95105.98], ['03-29 13:00', 95361.61], ['03-29 14:00', 95282.19], ['03-29 15:00', 95518.23], ['03-29 16:00', 95445.71], ['03-29 17:00', 95541.09], ['03-29 18:00', 95879.2], ['03-29 19:00', 95856.59], ['03-29 20:00', 96035.42], ['03-29 21:00', 95420.87], ['03-29 22:00', 95570.05], ['03-29 23:00', 93864.43], ['03-30 00:00', 94223.42], ['03-30 01:00', 93116.67], ['03-30 02:00', 92583.43], ['03-30 03:00', 92325.91], ['03-30 04:00', 92468.18], ['03-30 05:00', 92413.32], ['03-30 06:00', 92391.25], ['03-30 07:00', 92285.13], ['03-30 08:00', 91921.01], ['03-30 09:00', 91085.25], ['03-30 10:00', 91402.3], ['03-30 11:00', 91508.39], ['03-30 12:00', 91672.58], ['03-30 13:00', 91850.04]],
        "api_funding_rate": [['03-29 00:00', -3.68e-05, 66337.79], ['03-29 08:00', -1.2e-07, 66633.23], ['03-29 16:00', 2.677e-05, 66500.0], ['03-30 00:00', 3e-06, 65973.4], ['03-30 08:00', 4.92e-06, 67596.7]],
        "klines_4h": [["03-29 07:00", 66875.7, 66907.5, 66521.4, 66632.5], ["03-29 11:00", 66632.4, 66986.8, 66375.5, 66780.8], ["03-29 15:00", 66780.8, 66849.0, 66288.1, 66500.0], ["03-29 19:00", 66499.9, 66639.0, 66111.0, 66320.2], ["03-29 23:00", 66320.3, 66767.9, 64918.2, 65977.9], ["03-30 03:00", 65978.0, 67487.7, 65754.2, 67139.8], ["03-30 07:00", 67140.0, 67777.0, 67129.3, 67595.9], ["03-30 11:00", 67595.9, 67998.0, 67333.3, 67651.5], ["03-30 15:00", 67651.5, 68148.4, 67055.0, 67590.2], ["03-30 19:00", 67590.2, 67614.9, 66200.1, 66516.0]],
        "klines_1h": [["03-29 15:00", 66780.8, 66844.3, 66668.0, 66818.6], ["03-29 16:00", 66818.7, 66849.0, 66483.9, 66546.0], ["03-29 17:00", 66546.1, 66764.9, 66420.0, 66556.2], ["03-29 18:00", 66556.3, 66695.0, 66288.1, 66500.0], ["03-29 19:00", 66499.9, 66639.0, 66400.0, 66467.8], ["03-29 20:00", 66467.8, 66518.2, 66111.0, 66356.6], ["03-29 21:00", 66356.6, 66524.0, 66291.2, 66397.2], ["03-29 22:00", 66397.1, 66453.4, 66282.1, 66320.2], ["03-29 23:00", 66320.3, 66767.9, 66312.7, 66578.6], ["03-30 00:00", 66578.6, 66734.5, 66477.5, 66678.8], ["03-30 01:00", 66678.8, 66686.1, 64918.2, 65820.3], ["03-30 02:00", 65820.2, 66350.4, 65819.0, 65977.9], ["03-30 03:00", 65978.0, 67043.2, 65754.2, 66251.2], ["03-30 04:00", 66251.2, 66806.1, 66251.1, 66624.1], ["03-30 05:00", 66624.2, 67487.7, 66538.5, 67087.0], ["03-30 06:00", 67087.1, 67288.8, 66934.7, 67139.8], ["03-30 07:00", 67140.0, 67625.1, 67129.3, 67579.1], ["03-30 08:00", 67579.2, 67777.0, 67404.0, 67459.0], ["03-30 09:00", 67459.0, 67550.0, 67238.6, 67273.4], ["03-30 10:00", 67273.5, 67612.6, 67180.5, 67595.9], ["03-30 11:00", 67595.9, 67920.0, 67574.6, 67634.0], ["03-30 12:00", 67633.9, 67667.9, 67426.0, 67466.2], ["03-30 13:00", 67466.2, 67498.0, 67333.3, 67463.0], ["03-30 14:00", 67463.1, 67998.0, 67459.7, 67651.5], ["03-30 15:00", 67651.5, 67950.0, 67627.7, 67859.3], ["03-30 16:00", 67859.4, 68148.4, 67378.7, 67490.9], ["03-30 17:00", 67490.8, 67843.8, 67055.0, 67762.7], ["03-30 18:00", 67762.8, 67875.0, 67373.7, 67590.2], ["03-30 19:00", 67590.2, 67614.9, 67188.0, 67333.0], ["03-30 20:00", 67332.9, 67443.8, 66617.3, 66805.2]],
        "klines_15m": [["03-30 08:00", 67579.2, 67777.0, 67542.7, 67608.9], ["03-30 08:15", 67609.0, 67699.0, 67549.9, 67623.5], ["03-30 08:30", 67623.6, 67671.2, 67412.0, 67463.5], ["03-30 08:45", 67463.5, 67529.2, 67404.0, 67459.0], ["03-30 09:00", 67459.0, 67550.0, 67378.3, 67409.9], ["03-30 09:15", 67409.9, 67430.0, 67238.6, 67288.5], ["03-30 09:30", 67288.5, 67369.3, 67250.0, 67333.7], ["03-30 09:45", 67333.7, 67394.7, 67264.6, 67273.4], ["03-30 10:00", 67273.5, 67430.0, 67180.5, 67349.8], ["03-30 10:15", 67349.9, 67402.8, 67262.8, 67301.2], ["03-30 10:30", 67301.3, 67399.9, 67255.0, 67283.7], ["03-30 10:45", 67283.7, 67612.6, 67267.2, 67595.9], ["03-30 11:00", 67595.9, 67888.5, 67574.6, 67865.1], ["03-30 11:15", 67865.0, 67880.0, 67688.9, 67727.0], ["03-30 11:30", 67727.1, 67920.0, 67690.1, 67725.4], ["03-30 11:45", 67725.1, 67784.7, 67623.1, 67634.0], ["03-30 12:00", 67633.9, 67667.9, 67538.5, 67550.0], ["03-30 12:15", 67549.9, 67629.0, 67467.6, 67485.1], ["03-30 12:30", 67485.0, 67537.4, 67427.8, 67527.0], ["03-30 12:45", 67527.0, 67564.1, 67426.0, 67466.2], ["03-30 13:00", 67466.2, 67470.9, 67365.0, 67411.9], ["03-30 13:15", 67411.9, 67465.0, 67383.9, 67391.0], ["03-30 13:30", 67391.0, 67410.0, 67333.3, 67409.0], ["03-30 13:45", 67409.0, 67498.0, 67390.6, 67463.0], ["03-30 14:00", 67463.1, 67565.7, 67459.7, 67559.0], ["03-30 14:15", 67559.0, 67998.0, 67508.1, 67655.9], ["03-30 14:30", 67655.9, 67719.7, 67475.0, 67565.8], ["03-30 14:45", 67565.9, 67709.2, 67550.1, 67651.5], ["03-30 15:00", 67651.5, 67846.4, 67627.7, 67808.6], ["03-30 15:15", 67808.7, 67950.0, 67762.0, 67827.1], ["03-30 15:30", 67827.2, 67929.8, 67775.3, 67847.6], ["03-30 15:45", 67847.6, 67914.9, 67799.9, 67859.3], ["03-30 16:00", 67859.4, 67932.9, 67800.1, 67870.6], ["03-30 16:15", 67870.6, 68148.4, 67835.7, 67838.1], ["03-30 16:30", 67838.1, 68008.5, 67660.4, 67673.5], ["03-30 16:45", 67673.6, 67800.0, 67378.7, 67490.9], ["03-30 17:00", 67490.8, 67724.6, 67420.1, 67641.9], ["03-30 17:15", 67641.9, 67666.0, 67200.0, 67279.1], ["03-30 17:30", 67279.0, 67375.0, 67063.9, 67099.9], ["03-30 17:45", 67100.0, 67843.8, 67055.0, 67762.7], ["03-30 18:00", 67762.8, 67875.0, 67523.1, 67527.9], ["03-30 18:15", 67528.0, 67591.5, 67373.7, 67494.0], ["03-30 18:30", 67493.9, 67871.8, 67430.5, 67724.1], ["03-30 18:45", 67724.0, 67766.5, 67558.9, 67590.2], ["03-30 19:00", 67590.2, 67614.9, 67310.0, 67414.2], ["03-30 19:15", 67414.1, 67448.5, 67253.3, 67320.6], ["03-30 19:30", 67320.6, 67481.0, 67280.8, 67345.9], ["03-30 19:45", 67345.8, 67413.5, 67188.0, 67333.0], ["03-30 20:00", 67332.9, 67443.8, 67140.5, 67159.2], ["03-30 20:15", 67159.3, 67167.3, 66617.3, 66787.2]]
    },

    "R7": {
        "data_15m": {"current_price": 66728.5, "ma5": 66785.09, "ma10": 66736.55, "ma30": 66871.39, "volume": 2000000, "volume_ma5": 40600000, "volume_ma10": 55900000, "net_long": -8100, "net_short": -11700, "futures_cvd": -40400000, "spot_cvd": -2000, "taker_ls_ratio": 0.4237, "oi": 89200, "oi_delta": 0, "liquidations": {"long": None, "short": None}},
        "data_1h": {"current_price": 66728.5, "ma5": 66650.14, "ma10": 67023.26, "ma30": 66981.55, "volume": 111500000, "volume_ma5": 359900000, "volume_ma10": 546100000, "net_long": 16100, "net_short": 4100, "futures_cvd": 39900000, "spot_cvd": -5900, "taker_ls_ratio": 0.9471, "oi": 89200, "oi_delta": 97.8, "liquidations": {"long": 96000, "short": 6800}},
        "data_4h": {"current_price": 66730.0, "ma5": 67216.51, "ma10": 66880.23, "ma30": 67345.59, "volume": 644600000, "volume_ma5": 1840000000, "volume_ma10": 1770000000, "net_long": -31800, "net_short": -20100, "futures_cvd": -22300000, "spot_cvd": -87500, "taker_ls_ratio": 1.151, "oi": 89800, "oi_delta": -419.3, "liquidations": {"long": 97500, "short": 101300}},
        "actual": 'UP', "move": 631,
        "mfe_4h": 0, "mae_4h": 0,
        "mfe_24h": 0, "mae_24h": 0, "max_high_24h": 68600.0, "min_low_24h": 65938.0,
        "run_time": "03-31 01:28",
        "whale_acct_ls": 0.9511,
        "api_whale_account": [['03-29 12:00', 0.9363], ['03-29 13:00', 0.931], ['03-29 14:00', 0.9336], ['03-29 15:00', 0.9242], ['03-29 16:00', 0.9308], ['03-29 17:00', 0.935], ['03-29 18:00', 0.9467], ['03-29 19:00', 0.9468], ['03-29 20:00', 0.9427], ['03-29 21:00', 0.9535], ['03-29 22:00', 0.9569], ['03-29 23:00', 0.9559], ['03-30 00:00', 0.9492], ['03-30 01:00', 0.9516], ['03-30 02:00', 0.9529], ['03-30 03:00', 0.9498], ['03-30 04:00', 0.9463], ['03-30 05:00', 0.9404], ['03-30 06:00', 0.9328], ['03-30 07:00', 0.9256], ['03-30 08:00', 0.9318], ['03-30 09:00', 0.9331], ['03-30 10:00', 0.9303], ['03-30 11:00', 0.9314], ['03-30 12:00', 0.9291], ['03-30 13:00', 0.9283], ['03-30 14:00', 0.9241], ['03-30 15:00', 0.9305], ['03-30 16:00', 0.9209], ['03-30 17:00', 0.9235]],
        "api_whale_position": [['03-29 12:00', 2.2321], ['03-29 13:00', 2.2258], ['03-29 14:00', 2.1918], ['03-29 15:00', 2.2362], ['03-29 16:00', 2.2394], ['03-29 17:00', 2.2352], ['03-29 18:00', 2.2185], ['03-29 19:00', 2.2165], ['03-29 20:00', 2.2092], ['03-29 21:00', 2.2185], ['03-29 22:00', 2.2248], ['03-29 23:00', 2.2658], ['03-30 00:00', 2.2216], ['03-30 01:00', 2.2862], ['03-30 02:00', 2.2862], ['03-30 03:00', 2.2185], ['03-30 04:00', 2.1949], ['03-30 05:00', 2.1506], ['03-30 06:00', 2.0665], ['03-30 07:00', 2.0057], ['03-30 08:00', 1.9709], ['03-30 09:00', 1.9087], ['03-30 10:00', 1.8531], ['03-30 11:00', 1.8612], ['03-30 12:00', 1.8539], ['03-30 13:00', 1.8121], ['03-30 14:00', 1.73], ['03-30 15:00', 1.7465], ['03-30 16:00', 1.7211], ['03-30 17:00', 1.7375]],
        "api_open_interest": [['03-29 12:00', 95105.98], ['03-29 13:00', 95361.61], ['03-29 14:00', 95282.19], ['03-29 15:00', 95518.23], ['03-29 16:00', 95445.71], ['03-29 17:00', 95541.09], ['03-29 18:00', 95879.2], ['03-29 19:00', 95856.59], ['03-29 20:00', 96035.42], ['03-29 21:00', 95420.87], ['03-29 22:00', 95570.05], ['03-29 23:00', 93864.43], ['03-30 00:00', 94223.42], ['03-30 01:00', 93116.67], ['03-30 02:00', 92583.43], ['03-30 03:00', 92325.91], ['03-30 04:00', 92468.18], ['03-30 05:00', 92413.32], ['03-30 06:00', 92391.25], ['03-30 07:00', 92285.13], ['03-30 08:00', 91921.01], ['03-30 09:00', 91085.25], ['03-30 10:00', 91402.3], ['03-30 11:00', 91508.39], ['03-30 12:00', 91672.58], ['03-30 13:00', 91850.04], ['03-30 14:00', 92098.94], ['03-30 15:00', 91665.96], ['03-30 16:00', 91918.91], ['03-30 17:00', 91973.96]],
        "api_funding_rate": [['03-29 00:00', -3.68e-05, 66337.79], ['03-29 08:00', -1.2e-07, 66633.23], ['03-29 16:00', 2.677e-05, 66500.0], ['03-30 00:00', 3e-06, 65973.4], ['03-30 08:00', 4.92e-06, 67596.7], ['03-30 16:00', 7.58e-06, 67595.59]],
        "klines_4h": [["03-29 11:00", 66632.4, 66986.8, 66375.5, 66780.8], ["03-29 15:00", 66780.8, 66849.0, 66288.1, 66500.0], ["03-29 19:00", 66499.9, 66639.0, 66111.0, 66320.2], ["03-29 23:00", 66320.3, 66767.9, 64918.2, 65977.9], ["03-30 03:00", 65978.0, 67487.7, 65754.2, 67139.8], ["03-30 07:00", 67140.0, 67777.0, 67129.3, 67595.9], ["03-30 11:00", 67595.9, 67998.0, 67333.3, 67651.5], ["03-30 15:00", 67651.5, 68148.4, 67055.0, 67590.2], ["03-30 19:00", 67590.2, 67614.9, 66200.1, 66516.0], ["03-30 23:00", 66515.9, 66973.5, 66377.1, 66764.4]],
        "klines_1h": [["03-29 20:00", 66467.8, 66518.2, 66111.0, 66356.6], ["03-29 21:00", 66356.6, 66524.0, 66291.2, 66397.2], ["03-29 22:00", 66397.1, 66453.4, 66282.1, 66320.2], ["03-29 23:00", 66320.3, 66767.9, 66312.7, 66578.6], ["03-30 00:00", 66578.6, 66734.5, 66477.5, 66678.8], ["03-30 01:00", 66678.8, 66686.1, 64918.2, 65820.3], ["03-30 02:00", 65820.2, 66350.4, 65819.0, 65977.9], ["03-30 03:00", 65978.0, 67043.2, 65754.2, 66251.2], ["03-30 04:00", 66251.2, 66806.1, 66251.1, 66624.1], ["03-30 05:00", 66624.2, 67487.7, 66538.5, 67087.0], ["03-30 06:00", 67087.1, 67288.8, 66934.7, 67139.8], ["03-30 07:00", 67140.0, 67625.1, 67129.3, 67579.1], ["03-30 08:00", 67579.2, 67777.0, 67404.0, 67459.0], ["03-30 09:00", 67459.0, 67550.0, 67238.6, 67273.4], ["03-30 10:00", 67273.5, 67612.6, 67180.5, 67595.9], ["03-30 11:00", 67595.9, 67920.0, 67574.6, 67634.0], ["03-30 12:00", 67633.9, 67667.9, 67426.0, 67466.2], ["03-30 13:00", 67466.2, 67498.0, 67333.3, 67463.0], ["03-30 14:00", 67463.1, 67998.0, 67459.7, 67651.5], ["03-30 15:00", 67651.5, 67950.0, 67627.7, 67859.3], ["03-30 16:00", 67859.4, 68148.4, 67378.7, 67490.9], ["03-30 17:00", 67490.8, 67843.8, 67055.0, 67762.7], ["03-30 18:00", 67762.8, 67875.0, 67373.7, 67590.2], ["03-30 19:00", 67590.2, 67614.9, 67188.0, 67333.0], ["03-30 20:00", 67332.9, 67443.8, 66617.3, 66805.2], ["03-30 21:00", 66805.1, 66899.9, 66456.4, 66620.6], ["03-30 22:00", 66620.6, 66640.0, 66200.1, 66516.0], ["03-30 23:00", 66515.9, 66662.6, 66488.7, 66614.9], ["03-31 00:00", 66614.9, 66973.5, 66550.0, 66770.6], ["03-31 01:00", 66770.6, 66971.2, 66650.9, 66746.5]],
        "klines_15m": [["03-30 13:00", 67466.2, 67470.9, 67365.0, 67411.9], ["03-30 13:15", 67411.9, 67465.0, 67383.9, 67391.0], ["03-30 13:30", 67391.0, 67410.0, 67333.3, 67409.0], ["03-30 13:45", 67409.0, 67498.0, 67390.6, 67463.0], ["03-30 14:00", 67463.1, 67565.7, 67459.7, 67559.0], ["03-30 14:15", 67559.0, 67998.0, 67508.1, 67655.9], ["03-30 14:30", 67655.9, 67719.7, 67475.0, 67565.8], ["03-30 14:45", 67565.9, 67709.2, 67550.1, 67651.5], ["03-30 15:00", 67651.5, 67846.4, 67627.7, 67808.6], ["03-30 15:15", 67808.7, 67950.0, 67762.0, 67827.1], ["03-30 15:30", 67827.2, 67929.8, 67775.3, 67847.6], ["03-30 15:45", 67847.6, 67914.9, 67799.9, 67859.3], ["03-30 16:00", 67859.4, 67932.9, 67800.1, 67870.6], ["03-30 16:15", 67870.6, 68148.4, 67835.7, 67838.1], ["03-30 16:30", 67838.1, 68008.5, 67660.4, 67673.5], ["03-30 16:45", 67673.6, 67800.0, 67378.7, 67490.9], ["03-30 17:00", 67490.8, 67724.6, 67420.1, 67641.9], ["03-30 17:15", 67641.9, 67666.0, 67200.0, 67279.1], ["03-30 17:30", 67279.0, 67375.0, 67063.9, 67099.9], ["03-30 17:45", 67100.0, 67843.8, 67055.0, 67762.7], ["03-30 18:00", 67762.8, 67875.0, 67523.1, 67527.9], ["03-30 18:15", 67528.0, 67591.5, 67373.7, 67494.0], ["03-30 18:30", 67493.9, 67871.8, 67430.5, 67724.1], ["03-30 18:45", 67724.0, 67766.5, 67558.9, 67590.2], ["03-30 19:00", 67590.2, 67614.9, 67310.0, 67414.2], ["03-30 19:15", 67414.1, 67448.5, 67253.3, 67320.6], ["03-30 19:30", 67320.6, 67481.0, 67280.8, 67345.9], ["03-30 19:45", 67345.8, 67413.5, 67188.0, 67333.0], ["03-30 20:00", 67332.9, 67443.8, 67140.5, 67159.2], ["03-30 20:15", 67159.3, 67167.3, 66617.3, 66787.2], ["03-30 20:30", 66787.3, 66937.2, 66729.9, 66927.6], ["03-30 20:45", 66927.6, 66975.9, 66757.3, 66805.2], ["03-30 21:00", 66805.1, 66899.9, 66671.2, 66794.1], ["03-30 21:15", 66794.1, 66831.8, 66548.0, 66670.9], ["03-30 21:30", 66670.9, 66794.9, 66544.4, 66711.3], ["03-30 21:45", 66711.3, 66765.2, 66456.4, 66620.6], ["03-30 22:00", 66620.6, 66640.0, 66262.5, 66398.1], ["03-30 22:15", 66398.1, 66427.5, 66200.1, 66278.0], ["03-30 22:30", 66278.1, 66374.8, 66213.5, 66305.7], ["03-30 22:45", 66305.7, 66556.7, 66256.5, 66516.0], ["03-30 23:00", 66515.9, 66662.6, 66488.7, 66561.1], ["03-30 23:15", 66561.1, 66641.2, 66512.0, 66620.0], ["03-30 23:30", 66620.0, 66647.0, 66510.9, 66628.5], ["03-30 23:45", 66628.4, 66640.7, 66576.7, 66614.9], ["03-31 00:00", 66614.9, 66777.0, 66550.0, 66749.2], ["03-31 00:15", 66749.3, 66963.6, 66737.5, 66822.0], ["03-31 00:30", 66822.1, 66973.5, 66782.4, 66900.0], ["03-31 00:45", 66900.0, 66928.5, 66757.9, 66770.6], ["03-31 01:00", 66770.6, 66971.2, 66668.2, 66740.5], ["03-31 01:15", 66740.4, 66869.2, 66696.4, 66785.7]]
    },

    "R8": {
        "data_15m": {"current_price": 67342.5, "ma5": 67493.8, "ma10": 67509.65, "ma30": 67464.18, "volume": 37900000, "volume_ma5": 76800000, "volume_ma10": 83800000, "net_long": -5800, "net_short": -13000, "futures_cvd": -39300000, "spot_cvd": -3000, "taker_ls_ratio": 1.0142, "oi": 90100, "oi_delta": 95.9, "liquidations": {"long": None, "short": None}},
        "data_1h": {"current_price": 67340.0, "ma5": 67616.85, "ma10": 67343.45, "ma30": 67300.02, "volume": 225000000, "volume_ma5": 313900000, "volume_ma10": 447400000, "net_long": 17500, "net_short": 3900, "futures_cvd": 37000000, "spot_cvd": -5600, "taker_ls_ratio": 0.8121, "oi": 90100, "oi_delta": 118.6, "liquidations": {"long": 105700, "short": 676}},
        "data_4h": {"current_price": 67360.8, "ma5": 67181.44, "ma10": 67059.3, "ma30": 67150.48, "volume": 949200000, "volume_ma5": 1970000000, "volume_ma10": 1980000000, "net_long": -26700, "net_short": -21400, "futures_cvd": -18900000, "spot_cvd": -84300, "taker_ls_ratio": 0.9346, "oi": 90600, "oi_delta": -342.9, "liquidations": {"long": 203300, "short": 205400}},
        "actual": 'DOWN', "move": -1002,
        "mfe_4h": 1402, "mae_4h": 526,
        "mfe_24h": 1402, "mae_24h": 1260, "max_high_24h": 68600.0, "min_low_24h": 65938.0,
        "run_time": "03-31 09:36",
        "whale_acct_ls": 0.898,
        "api_whale_account": [['03-29 16:00', 0.9308], ['03-29 17:00', 0.935], ['03-29 18:00', 0.9467], ['03-29 19:00', 0.9468], ['03-29 20:00', 0.9427], ['03-29 21:00', 0.9535], ['03-29 22:00', 0.9569], ['03-29 23:00', 0.9559], ['03-30 00:00', 0.9492], ['03-30 01:00', 0.9516], ['03-30 02:00', 0.9529], ['03-30 03:00', 0.9498], ['03-30 04:00', 0.9463], ['03-30 05:00', 0.9404], ['03-30 06:00', 0.9328], ['03-30 07:00', 0.9256], ['03-30 08:00', 0.9318], ['03-30 09:00', 0.9331], ['03-30 10:00', 0.9303], ['03-30 11:00', 0.9314], ['03-30 12:00', 0.9291], ['03-30 13:00', 0.9283], ['03-30 14:00', 0.9241], ['03-30 15:00', 0.9305], ['03-30 16:00', 0.9209], ['03-30 17:00', 0.9235], ['03-30 18:00', 0.9479], ['03-30 19:00', 0.9319], ['03-30 20:00', 0.9355], ['03-30 21:00', 0.9348]],
        "api_whale_position": [['03-29 16:00', 2.2394], ['03-29 17:00', 2.2352], ['03-29 18:00', 2.2185], ['03-29 19:00', 2.2165], ['03-29 20:00', 2.2092], ['03-29 21:00', 2.2185], ['03-29 22:00', 2.2248], ['03-29 23:00', 2.2658], ['03-30 00:00', 2.2216], ['03-30 01:00', 2.2862], ['03-30 02:00', 2.2862], ['03-30 03:00', 2.2185], ['03-30 04:00', 2.1949], ['03-30 05:00', 2.1506], ['03-30 06:00', 2.0665], ['03-30 07:00', 2.0057], ['03-30 08:00', 1.9709], ['03-30 09:00', 1.9087], ['03-30 10:00', 1.8531], ['03-30 11:00', 1.8612], ['03-30 12:00', 1.8539], ['03-30 13:00', 1.8121], ['03-30 14:00', 1.73], ['03-30 15:00', 1.7465], ['03-30 16:00', 1.7211], ['03-30 17:00', 1.7375], ['03-30 18:00', 1.8353], ['03-30 19:00', 1.876], ['03-30 20:00', 1.9472], ['03-30 21:00', 1.9656]],
        "api_open_interest": [['03-29 16:00', 95445.71], ['03-29 17:00', 95541.09], ['03-29 18:00', 95879.2], ['03-29 19:00', 95856.59], ['03-29 20:00', 96035.42], ['03-29 21:00', 95420.87], ['03-29 22:00', 95570.05], ['03-29 23:00', 93864.43], ['03-30 00:00', 94223.42], ['03-30 01:00', 93116.67], ['03-30 02:00', 92583.43], ['03-30 03:00', 92325.91], ['03-30 04:00', 92468.18], ['03-30 05:00', 92413.32], ['03-30 06:00', 92391.25], ['03-30 07:00', 92285.13], ['03-30 08:00', 91921.01], ['03-30 09:00', 91085.25], ['03-30 10:00', 91402.3], ['03-30 11:00', 91508.39], ['03-30 12:00', 91672.58], ['03-30 13:00', 91850.04], ['03-30 14:00', 92098.94], ['03-30 15:00', 91665.96], ['03-30 16:00', 91918.91], ['03-30 17:00', 91973.96], ['03-30 18:00', 91316.51], ['03-30 19:00', 90205.02], ['03-30 20:00', 89691.53], ['03-30 21:00', 89449.5]],
        "api_funding_rate": [['03-29 00:00', -3.68e-05, 66337.79], ['03-29 08:00', -1.2e-07, 66633.23], ['03-29 16:00', 2.677e-05, 66500.0], ['03-30 00:00', 3e-06, 65973.4], ['03-30 08:00', 4.92e-06, 67596.7], ['03-30 16:00', 7.58e-06, 67595.59]],
        "klines_4h": [["03-29 19:00", 66499.9, 66639.0, 66111.0, 66320.2], ["03-29 23:00", 66320.3, 66767.9, 64918.2, 65977.9], ["03-30 03:00", 65978.0, 67487.7, 65754.2, 67139.8], ["03-30 07:00", 67140.0, 67777.0, 67129.3, 67595.9], ["03-30 11:00", 67595.9, 67998.0, 67333.3, 67651.5], ["03-30 15:00", 67651.5, 68148.4, 67055.0, 67590.2], ["03-30 19:00", 67590.2, 67614.9, 66200.1, 66516.0], ["03-30 23:00", 66515.9, 66973.5, 66377.1, 66764.4], ["03-31 03:00", 66764.4, 68377.0, 66498.9, 67670.8], ["03-31 07:00", 67670.8, 67865.7, 67071.9, 67343.8]],
        "klines_1h": [["03-30 04:00", 66251.2, 66806.1, 66251.1, 66624.1], ["03-30 05:00", 66624.2, 67487.7, 66538.5, 67087.0], ["03-30 06:00", 67087.1, 67288.8, 66934.7, 67139.8], ["03-30 07:00", 67140.0, 67625.1, 67129.3, 67579.1], ["03-30 08:00", 67579.2, 67777.0, 67404.0, 67459.0], ["03-30 09:00", 67459.0, 67550.0, 67238.6, 67273.4], ["03-30 10:00", 67273.5, 67612.6, 67180.5, 67595.9], ["03-30 11:00", 67595.9, 67920.0, 67574.6, 67634.0], ["03-30 12:00", 67633.9, 67667.9, 67426.0, 67466.2], ["03-30 13:00", 67466.2, 67498.0, 67333.3, 67463.0], ["03-30 14:00", 67463.1, 67998.0, 67459.7, 67651.5], ["03-30 15:00", 67651.5, 67950.0, 67627.7, 67859.3], ["03-30 16:00", 67859.4, 68148.4, 67378.7, 67490.9], ["03-30 17:00", 67490.8, 67843.8, 67055.0, 67762.7], ["03-30 18:00", 67762.8, 67875.0, 67373.7, 67590.2], ["03-30 19:00", 67590.2, 67614.9, 67188.0, 67333.0], ["03-30 20:00", 67332.9, 67443.8, 66617.3, 66805.2], ["03-30 21:00", 66805.1, 66899.9, 66456.4, 66620.6], ["03-30 22:00", 66620.6, 66640.0, 66200.1, 66516.0], ["03-30 23:00", 66515.9, 66662.6, 66488.7, 66614.9], ["03-31 00:00", 66614.9, 66973.5, 66550.0, 66770.6], ["03-31 01:00", 66770.6, 66971.2, 66650.9, 66746.5], ["03-31 02:00", 66746.4, 66769.1, 66377.1, 66764.4], ["03-31 03:00", 66764.4, 67276.0, 66498.9, 67172.5], ["03-31 04:00", 67172.5, 68377.0, 67004.2, 67896.2], ["03-31 05:00", 67896.1, 68072.7, 67726.9, 67911.8], ["03-31 06:00", 67911.8, 67974.8, 67610.5, 67670.8], ["03-31 07:00", 67670.8, 67865.7, 67441.8, 67510.1], ["03-31 08:00", 67510.1, 67756.8, 67356.4, 67648.9], ["03-31 09:00", 67649.0, 67679.5, 67300.1, 67465.4]],
        "klines_15m": [["03-30 21:15", 66794.1, 66831.8, 66548.0, 66670.9], ["03-30 21:30", 66670.9, 66794.9, 66544.4, 66711.3], ["03-30 21:45", 66711.3, 66765.2, 66456.4, 66620.6], ["03-30 22:00", 66620.6, 66640.0, 66262.5, 66398.1], ["03-30 22:15", 66398.1, 66427.5, 66200.1, 66278.0], ["03-30 22:30", 66278.1, 66374.8, 66213.5, 66305.7], ["03-30 22:45", 66305.7, 66556.7, 66256.5, 66516.0], ["03-30 23:00", 66515.9, 66662.6, 66488.7, 66561.1], ["03-30 23:15", 66561.1, 66641.2, 66512.0, 66620.0], ["03-30 23:30", 66620.0, 66647.0, 66510.9, 66628.5], ["03-30 23:45", 66628.4, 66640.7, 66576.7, 66614.9], ["03-31 00:00", 66614.9, 66777.0, 66550.0, 66749.2], ["03-31 00:15", 66749.3, 66963.6, 66737.5, 66822.0], ["03-31 00:30", 66822.1, 66973.5, 66782.4, 66900.0], ["03-31 00:45", 66900.0, 66928.5, 66757.9, 66770.6], ["03-31 01:00", 66770.6, 66971.2, 66668.2, 66740.5], ["03-31 01:15", 66740.4, 66869.2, 66696.4, 66785.7], ["03-31 01:30", 66785.7, 66831.5, 66710.0, 66800.0], ["03-31 01:45", 66800.1, 66813.6, 66650.9, 66746.5], ["03-31 02:00", 66746.4, 66752.7, 66377.1, 66517.5], ["03-31 02:15", 66517.6, 66690.7, 66485.3, 66672.1], ["03-31 02:30", 66672.1, 66741.0, 66626.6, 66729.6], ["03-31 02:45", 66729.6, 66769.1, 66675.4, 66764.4], ["03-31 03:00", 66764.4, 66792.4, 66525.6, 66614.5], ["03-31 03:15", 66615.0, 66790.1, 66498.9, 66779.9], ["03-31 03:30", 66780.0, 66922.8, 66731.5, 66912.6], ["03-31 03:45", 66912.6, 67276.0, 66906.8, 67172.5], ["03-31 04:00", 67172.5, 67257.8, 67004.2, 67194.6], ["03-31 04:15", 67194.6, 67850.0, 67194.6, 67743.0], ["03-31 04:30", 67743.0, 68377.0, 67697.2, 67893.3], ["03-31 04:45", 67893.3, 68020.3, 67776.8, 67896.2], ["03-31 05:00", 67896.1, 67943.0, 67726.9, 67883.5], ["03-31 05:15", 67883.8, 68072.7, 67880.4, 68007.1], ["03-31 05:30", 68007.0, 68029.0, 67802.2, 67948.0], ["03-31 05:45", 67947.9, 68058.0, 67865.4, 67911.8], ["03-31 06:00", 67911.8, 67974.8, 67763.1, 67878.6], ["03-31 06:15", 67878.6, 67937.4, 67767.5, 67807.2], ["03-31 06:30", 67807.2, 67892.1, 67610.8, 67695.4], ["03-31 06:45", 67695.5, 67730.0, 67610.5, 67670.8], ["03-31 07:00", 67670.8, 67758.7, 67548.0, 67630.1], ["03-31 07:15", 67630.1, 67865.7, 67441.8, 67562.7], ["03-31 07:30", 67562.7, 67628.1, 67485.7, 67565.0], ["03-31 07:45", 67565.1, 67652.2, 67480.0, 67510.1], ["03-31 08:00", 67510.1, 67588.0, 67360.5, 67389.9], ["03-31 08:15", 67389.9, 67630.0, 67356.4, 67592.3], ["03-31 08:30", 67592.4, 67691.0, 67530.9, 67643.4], ["03-31 08:45", 67643.4, 67756.8, 67623.3, 67648.9], ["03-31 09:00", 67649.0, 67679.5, 67431.4, 67446.5], ["03-31 09:15", 67446.6, 67482.3, 67300.1, 67383.2], ["03-31 09:30", 67383.3, 67457.3, 67307.6, 67379.0]]
    },

    "R9": {
        "data_15m": {"current_price": 66387.6, "ma5": 66287.24, "ma10": 66454.28, "ma30": 67130.41, "volume": 56200000, "volume_ma5": 178300000, "volume_ma10": 215000000, "net_long": -4700, "net_short": -13900, "futures_cvd": -39600000, "spot_cvd": -3300, "taker_ls_ratio": 2.1797, "oi": 90800, "oi_delta": 35.9, "liquidations": {"long": 1700, "short": 7600}},
        "data_1h": {"current_price": 66380.7, "ma5": 66805.33, "ma10": 67266.45, "ma30": 67241.8, "volume": 552400000, "volume_ma5": 607600000, "volume_ma10": 583500000, "net_long": 15800, "net_short": 826, "futures_cvd": 26600000, "spot_cvd": -8300, "taker_ls_ratio": 1.1387, "oi": 90800, "oi_delta": 228.9, "liquidations": {"long": 6000, "short": 28400}},
        "data_4h": {"current_price": 66358.6, "ma5": 66931.91, "ma10": 67061.44, "ma30": 67053.9, "volume": 2290000000, "volume_ma5": 1950000000, "volume_ma10": 2190000000, "net_long": -29000, "net_short": -21600, "futures_cvd": -19800000, "spot_cvd": -85200, "taker_ls_ratio": 0.898, "oi": 90800, "oi_delta": 78.4, "liquidations": {"long": 2300000, "short": 79400}},
        "actual": 'UP', "move": 1406,
        "mfe_4h": 1385, "mae_4h": 443,
        "mfe_24h": 2219, "mae_24h": 443, "max_high_24h": 68600.0, "min_low_24h": 65938.0,
        "run_time": "03-31 13:51",
        "whale_acct_ls": 0.9315,
        "api_whale_account": [['03-29 20:00', 0.9427], ['03-29 21:00', 0.9535], ['03-29 22:00', 0.9569], ['03-29 23:00', 0.9559], ['03-30 00:00', 0.9492], ['03-30 01:00', 0.9516], ['03-30 02:00', 0.9529], ['03-30 03:00', 0.9498], ['03-30 04:00', 0.9463], ['03-30 05:00', 0.9404], ['03-30 06:00', 0.9328], ['03-30 07:00', 0.9256], ['03-30 08:00', 0.9318], ['03-30 09:00', 0.9331], ['03-30 10:00', 0.9303], ['03-30 11:00', 0.9314], ['03-30 12:00', 0.9291], ['03-30 13:00', 0.9283], ['03-30 14:00', 0.9241], ['03-30 15:00', 0.9305], ['03-30 16:00', 0.9209], ['03-30 17:00', 0.9235], ['03-30 18:00', 0.9479], ['03-30 19:00', 0.9319], ['03-30 20:00', 0.9355], ['03-30 21:00', 0.9348], ['03-30 22:00', 0.9511], ['03-30 23:00', 0.9425], ['03-31 00:00', 0.9364], ['03-31 01:00', 0.9215]],
        "api_whale_position": [['03-29 20:00', 2.2092], ['03-29 21:00', 2.2185], ['03-29 22:00', 2.2248], ['03-29 23:00', 2.2658], ['03-30 00:00', 2.2216], ['03-30 01:00', 2.2862], ['03-30 02:00', 2.2862], ['03-30 03:00', 2.2185], ['03-30 04:00', 2.1949], ['03-30 05:00', 2.1506], ['03-30 06:00', 2.0665], ['03-30 07:00', 2.0057], ['03-30 08:00', 1.9709], ['03-30 09:00', 1.9087], ['03-30 10:00', 1.8531], ['03-30 11:00', 1.8612], ['03-30 12:00', 1.8539], ['03-30 13:00', 1.8121], ['03-30 14:00', 1.73], ['03-30 15:00', 1.7465], ['03-30 16:00', 1.7211], ['03-30 17:00', 1.7375], ['03-30 18:00', 1.8353], ['03-30 19:00', 1.876], ['03-30 20:00', 1.9472], ['03-30 21:00', 1.9656], ['03-30 22:00', 1.9735], ['03-30 23:00', 1.978], ['03-31 00:00', 2.0048], ['03-31 01:00', 2.0637]],
        "api_open_interest": [['03-29 20:00', 96035.42], ['03-29 21:00', 95420.87], ['03-29 22:00', 95570.05], ['03-29 23:00', 93864.43], ['03-30 00:00', 94223.42], ['03-30 01:00', 93116.67], ['03-30 02:00', 92583.43], ['03-30 03:00', 92325.91], ['03-30 04:00', 92468.18], ['03-30 05:00', 92413.32], ['03-30 06:00', 92391.25], ['03-30 07:00', 92285.13], ['03-30 08:00', 91921.01], ['03-30 09:00', 91085.25], ['03-30 10:00', 91402.3], ['03-30 11:00', 91508.39], ['03-30 12:00', 91672.58], ['03-30 13:00', 91850.04], ['03-30 14:00', 92098.94], ['03-30 15:00', 91665.96], ['03-30 16:00', 91918.91], ['03-30 17:00', 91973.96], ['03-30 18:00', 91316.51], ['03-30 19:00', 90205.02], ['03-30 20:00', 89691.53], ['03-30 21:00', 89449.5], ['03-30 22:00', 89241.14], ['03-30 23:00', 89140.5], ['03-31 00:00', 89941.69], ['03-31 01:00', 89815.59]],
        "api_funding_rate": [['03-29 00:00', -3.68e-05, 66337.79], ['03-29 08:00', -1.2e-07, 66633.23], ['03-29 16:00', 2.677e-05, 66500.0], ['03-30 00:00', 3e-06, 65973.4], ['03-30 08:00', 4.92e-06, 67596.7], ['03-30 16:00', 7.58e-06, 67595.59], ['03-31 00:00', 1.16e-06, 66764.4]],
        "klines_4h": [["03-29 23:00", 66320.3, 66767.9, 64918.2, 65977.9], ["03-30 03:00", 65978.0, 67487.7, 65754.2, 67139.8], ["03-30 07:00", 67140.0, 67777.0, 67129.3, 67595.9], ["03-30 11:00", 67595.9, 67998.0, 67333.3, 67651.5], ["03-30 15:00", 67651.5, 68148.4, 67055.0, 67590.2], ["03-30 19:00", 67590.2, 67614.9, 66200.1, 66516.0], ["03-30 23:00", 66515.9, 66973.5, 66377.1, 66764.4], ["03-31 03:00", 66764.4, 68377.0, 66498.9, 67670.8], ["03-31 07:00", 67670.8, 67865.7, 67071.9, 67343.8], ["03-31 11:00", 67343.9, 67476.9, 65938.0, 66652.4]],
        "klines_1h": [["03-30 08:00", 67579.2, 67777.0, 67404.0, 67459.0], ["03-30 09:00", 67459.0, 67550.0, 67238.6, 67273.4], ["03-30 10:00", 67273.5, 67612.6, 67180.5, 67595.9], ["03-30 11:00", 67595.9, 67920.0, 67574.6, 67634.0], ["03-30 12:00", 67633.9, 67667.9, 67426.0, 67466.2], ["03-30 13:00", 67466.2, 67498.0, 67333.3, 67463.0], ["03-30 14:00", 67463.1, 67998.0, 67459.7, 67651.5], ["03-30 15:00", 67651.5, 67950.0, 67627.7, 67859.3], ["03-30 16:00", 67859.4, 68148.4, 67378.7, 67490.9], ["03-30 17:00", 67490.8, 67843.8, 67055.0, 67762.7], ["03-30 18:00", 67762.8, 67875.0, 67373.7, 67590.2], ["03-30 19:00", 67590.2, 67614.9, 67188.0, 67333.0], ["03-30 20:00", 67332.9, 67443.8, 66617.3, 66805.2], ["03-30 21:00", 66805.1, 66899.9, 66456.4, 66620.6], ["03-30 22:00", 66620.6, 66640.0, 66200.1, 66516.0], ["03-30 23:00", 66515.9, 66662.6, 66488.7, 66614.9], ["03-31 00:00", 66614.9, 66973.5, 66550.0, 66770.6], ["03-31 01:00", 66770.6, 66971.2, 66650.9, 66746.5], ["03-31 02:00", 66746.4, 66769.1, 66377.1, 66764.4], ["03-31 03:00", 66764.4, 67276.0, 66498.9, 67172.5], ["03-31 04:00", 67172.5, 68377.0, 67004.2, 67896.2], ["03-31 05:00", 67896.1, 68072.7, 67726.9, 67911.8], ["03-31 06:00", 67911.8, 67974.8, 67610.5, 67670.8], ["03-31 07:00", 67670.8, 67865.7, 67441.8, 67510.1], ["03-31 08:00", 67510.1, 67756.8, 67356.4, 67648.9], ["03-31 09:00", 67649.0, 67679.5, 67300.1, 67465.4], ["03-31 10:00", 67465.4, 67497.0, 67071.9, 67343.8], ["03-31 11:00", 67343.9, 67476.9, 66655.0, 66745.1], ["03-31 12:00", 66745.1, 66891.8, 65938.0, 66099.3], ["03-31 13:00", 66099.3, 66442.0, 66067.0, 66329.4]],
        "klines_15m": [["03-31 01:30", 66785.7, 66831.5, 66710.0, 66800.0], ["03-31 01:45", 66800.1, 66813.6, 66650.9, 66746.5], ["03-31 02:00", 66746.4, 66752.7, 66377.1, 66517.5], ["03-31 02:15", 66517.6, 66690.7, 66485.3, 66672.1], ["03-31 02:30", 66672.1, 66741.0, 66626.6, 66729.6], ["03-31 02:45", 66729.6, 66769.1, 66675.4, 66764.4], ["03-31 03:00", 66764.4, 66792.4, 66525.6, 66614.5], ["03-31 03:15", 66615.0, 66790.1, 66498.9, 66779.9], ["03-31 03:30", 66780.0, 66922.8, 66731.5, 66912.6], ["03-31 03:45", 66912.6, 67276.0, 66906.8, 67172.5], ["03-31 04:00", 67172.5, 67257.8, 67004.2, 67194.6], ["03-31 04:15", 67194.6, 67850.0, 67194.6, 67743.0], ["03-31 04:30", 67743.0, 68377.0, 67697.2, 67893.3], ["03-31 04:45", 67893.3, 68020.3, 67776.8, 67896.2], ["03-31 05:00", 67896.1, 67943.0, 67726.9, 67883.5], ["03-31 05:15", 67883.8, 68072.7, 67880.4, 68007.1], ["03-31 05:30", 68007.0, 68029.0, 67802.2, 67948.0], ["03-31 05:45", 67947.9, 68058.0, 67865.4, 67911.8], ["03-31 06:00", 67911.8, 67974.8, 67763.1, 67878.6], ["03-31 06:15", 67878.6, 67937.4, 67767.5, 67807.2], ["03-31 06:30", 67807.2, 67892.1, 67610.8, 67695.4], ["03-31 06:45", 67695.5, 67730.0, 67610.5, 67670.8], ["03-31 07:00", 67670.8, 67758.7, 67548.0, 67630.1], ["03-31 07:15", 67630.1, 67865.7, 67441.8, 67562.7], ["03-31 07:30", 67562.7, 67628.1, 67485.7, 67565.0], ["03-31 07:45", 67565.1, 67652.2, 67480.0, 67510.1], ["03-31 08:00", 67510.1, 67588.0, 67360.5, 67389.9], ["03-31 08:15", 67389.9, 67630.0, 67356.4, 67592.3], ["03-31 08:30", 67592.4, 67691.0, 67530.9, 67643.4], ["03-31 08:45", 67643.4, 67756.8, 67623.3, 67648.9], ["03-31 09:00", 67649.0, 67679.5, 67431.4, 67446.5], ["03-31 09:15", 67446.6, 67482.3, 67300.1, 67383.2], ["03-31 09:30", 67383.3, 67457.3, 67307.6, 67379.0], ["03-31 09:45", 67379.1, 67505.8, 67379.0, 67465.4], ["03-31 10:00", 67465.4, 67497.0, 67200.0, 67267.2], ["03-31 10:15", 67267.2, 67296.4, 67071.9, 67260.9], ["03-31 10:30", 67260.8, 67350.0, 67179.7, 67299.9], ["03-31 10:45", 67299.9, 67410.0, 67281.2, 67343.8], ["03-31 11:00", 67343.9, 67476.9, 67208.4, 67324.0], ["03-31 11:15", 67323.9, 67420.0, 67250.6, 67280.4], ["03-31 11:30", 67280.3, 67281.9, 66777.0, 66818.9], ["03-31 11:45", 66818.9, 66911.9, 66655.0, 66745.1], ["03-31 12:00", 66745.1, 66891.8, 66550.0, 66669.5], ["03-31 12:15", 66669.6, 66686.3, 66321.0, 66403.9], ["03-31 12:30", 66403.9, 66499.7, 66368.0, 66477.4], ["03-31 12:45", 66477.4, 66487.0, 65938.0, 66099.3], ["03-31 13:00", 66099.3, 66371.9, 66067.0, 66342.5], ["03-31 13:15", 66342.4, 66432.0, 66313.2, 66350.0], ["03-31 13:30", 66350.1, 66398.5, 66188.7, 66247.3], ["03-31 13:45", 66247.2, 66442.0, 66214.6, 66329.4]]
    },

    "R10": {
        "data_15m": {"current_price": 68081.9, "ma5": 67883.22, "ma10": 67799.85, "ma30": 67410.41, "volume": 80200000, "volume_ma5": 77400000, "volume_ma10": 113900000, "net_long": -2400, "net_short": 7100, "futures_cvd": -35900000, "spot_cvd": -1200, "taker_ls_ratio": 1.4541, "oi": 89200, "oi_delta": -73.3, "liquidations": {"long": 0, "short": 317300}},
        "data_1h": {"current_price": 68081.9, "ma5": 67750.06, "ma10": 67253.81, "ma30": 67136.45, "volume": 80500000, "volume_ma5": 832200000, "volume_ma10": 894100000, "net_long": 21000, "net_short": -4500, "futures_cvd": 35000000, "spot_cvd": -5800, "taker_ls_ratio": 1.4522, "oi": 89200, "oi_delta": -72.0, "liquidations": {"long": 0, "short": 318100}},
        "data_4h": {"current_price": 68081.9, "ma5": 67303.15, "ma10": 67271.27, "ma30": 66936.12, "volume": 81100000, "volume_ma5": 2550000000, "volume_ma10": 2330000000, "net_long": -25200, "net_short": 12100, "futures_cvd": -16000000, "spot_cvd": -82500, "taker_ls_ratio": 1.4559, "oi": 89200, "oi_delta": -72.0, "liquidations": {"long": 0, "short": 318100}},
        "actual": 'UP', "move": 162,
        "mfe_4h": 518, "mae_4h": 1386,
        "mfe_24h": 518, "mae_24h": 1386, "max_high_24h": 68600.0, "min_low_24h": 66696.0,
        "run_time": "03-31 21:00",
        "whale_acct_ls": 0.8748,
        "api_whale_account": [['03-30 05:00', 0.9404], ['03-30 06:00', 0.9328], ['03-30 07:00', 0.9256], ['03-30 08:00', 0.9318], ['03-30 09:00', 0.9331], ['03-30 10:00', 0.9303], ['03-30 11:00', 0.9314], ['03-30 12:00', 0.9291], ['03-30 13:00', 0.9283], ['03-30 14:00', 0.9241], ['03-30 15:00', 0.9305], ['03-30 16:00', 0.9209], ['03-30 17:00', 0.9235], ['03-30 18:00', 0.9479], ['03-30 19:00', 0.9319], ['03-30 20:00', 0.9355], ['03-30 21:00', 0.9348], ['03-30 22:00', 0.9511], ['03-30 23:00', 0.9425], ['03-31 00:00', 0.9364], ['03-31 01:00', 0.9215], ['03-31 02:00', 0.8922], ['03-31 03:00', 0.8971], ['03-31 04:00', 0.8933], ['03-31 05:00', 0.89], ['03-31 06:00', 0.898], ['03-31 07:00', 0.8898], ['03-31 08:00', 0.8931], ['03-31 09:00', 0.9149], ['03-31 10:00', 0.9315]],
        "api_whale_position": [['03-30 05:00', 2.1506], ['03-30 06:00', 2.0665], ['03-30 07:00', 2.0057], ['03-30 08:00', 1.9709], ['03-30 09:00', 1.9087], ['03-30 10:00', 1.8531], ['03-30 11:00', 1.8612], ['03-30 12:00', 1.8539], ['03-30 13:00', 1.8121], ['03-30 14:00', 1.73], ['03-30 15:00', 1.7465], ['03-30 16:00', 1.7211], ['03-30 17:00', 1.7375], ['03-30 18:00', 1.8353], ['03-30 19:00', 1.876], ['03-30 20:00', 1.9472], ['03-30 21:00', 1.9656], ['03-30 22:00', 1.9735], ['03-30 23:00', 1.978], ['03-31 00:00', 2.0048], ['03-31 01:00', 2.0637], ['03-31 02:00', 1.9647], ['03-31 03:00', 1.8662], ['03-31 04:00', 1.8329], ['03-31 05:00', 1.8417], ['03-31 06:00', 1.8678], ['03-31 07:00', 1.8868], ['03-31 08:00', 1.9155], ['03-31 09:00', 2.0157], ['03-31 10:00', 2.1636]],
        "api_open_interest": [['03-30 05:00', 92413.32], ['03-30 06:00', 92391.25], ['03-30 07:00', 92285.13], ['03-30 08:00', 91921.01], ['03-30 09:00', 91085.25], ['03-30 10:00', 91402.3], ['03-30 11:00', 91508.39], ['03-30 12:00', 91672.58], ['03-30 13:00', 91850.04], ['03-30 14:00', 92098.94], ['03-30 15:00', 91665.96], ['03-30 16:00', 91918.91], ['03-30 17:00', 91973.96], ['03-30 18:00', 91316.51], ['03-30 19:00', 90205.02], ['03-30 20:00', 89691.53], ['03-30 21:00', 89449.5], ['03-30 22:00', 89241.14], ['03-30 23:00', 89140.5], ['03-31 00:00', 89941.69], ['03-31 01:00', 89815.59], ['03-31 02:00', 90079.72], ['03-31 03:00', 90411.65], ['03-31 04:00', 90575.06], ['03-31 05:00', 90614.34], ['03-31 06:00', 90113.58], ['03-31 07:00', 90359.31], ['03-31 08:00', 90709.16], ['03-31 09:00', 90618.96], ['03-31 10:00', 90565.44]],
        "api_funding_rate": [['03-29 00:00', -3.68e-05, 66337.79], ['03-29 08:00', -1.2e-07, 66633.23], ['03-29 16:00', 2.677e-05, 66500.0], ['03-30 00:00', 3e-06, 65973.4], ['03-30 08:00', 4.92e-06, 67596.7], ['03-30 16:00', 7.58e-06, 67595.59], ['03-31 00:00', 1.16e-06, 66764.4], ['03-31 08:00', -1.921e-05, 67343.9]],
        "klines_4h": [["03-30 07:00", 67140.0, 67777.0, 67129.3, 67595.9], ["03-30 11:00", 67595.9, 67998.0, 67333.3, 67651.5], ["03-30 15:00", 67651.5, 68148.4, 67055.0, 67590.2], ["03-30 19:00", 67590.2, 67614.9, 66200.1, 66516.0], ["03-30 23:00", 66515.9, 66973.5, 66377.1, 66764.4], ["03-31 03:00", 66764.4, 68377.0, 66498.9, 67670.8], ["03-31 07:00", 67670.8, 67865.7, 67071.9, 67343.8], ["03-31 11:00", 67343.9, 67476.9, 65938.0, 66652.4], ["03-31 15:00", 66652.4, 67765.8, 66374.4, 66700.0], ["03-31 19:00", 66700.0, 68600.0, 66695.9, 67803.0]],
        "klines_1h": [["03-30 16:00", 67859.4, 68148.4, 67378.7, 67490.9], ["03-30 17:00", 67490.8, 67843.8, 67055.0, 67762.7], ["03-30 18:00", 67762.8, 67875.0, 67373.7, 67590.2], ["03-30 19:00", 67590.2, 67614.9, 67188.0, 67333.0], ["03-30 20:00", 67332.9, 67443.8, 66617.3, 66805.2], ["03-30 21:00", 66805.1, 66899.9, 66456.4, 66620.6], ["03-30 22:00", 66620.6, 66640.0, 66200.1, 66516.0], ["03-30 23:00", 66515.9, 66662.6, 66488.7, 66614.9], ["03-31 00:00", 66614.9, 66973.5, 66550.0, 66770.6], ["03-31 01:00", 66770.6, 66971.2, 66650.9, 66746.5], ["03-31 02:00", 66746.4, 66769.1, 66377.1, 66764.4], ["03-31 03:00", 66764.4, 67276.0, 66498.9, 67172.5], ["03-31 04:00", 67172.5, 68377.0, 67004.2, 67896.2], ["03-31 05:00", 67896.1, 68072.7, 67726.9, 67911.8], ["03-31 06:00", 67911.8, 67974.8, 67610.5, 67670.8], ["03-31 07:00", 67670.8, 67865.7, 67441.8, 67510.1], ["03-31 08:00", 67510.1, 67756.8, 67356.4, 67648.9], ["03-31 09:00", 67649.0, 67679.5, 67300.1, 67465.4], ["03-31 10:00", 67465.4, 67497.0, 67071.9, 67343.8], ["03-31 11:00", 67343.9, 67476.9, 66655.0, 66745.1], ["03-31 12:00", 66745.1, 66891.8, 65938.0, 66099.3], ["03-31 13:00", 66099.3, 66442.0, 66067.0, 66329.4], ["03-31 14:00", 66329.4, 66850.0, 66205.0, 66652.4], ["03-31 15:00", 66652.4, 66909.3, 66480.0, 66623.8], ["03-31 16:00", 66623.8, 67375.0, 66623.8, 67255.6], ["03-31 17:00", 67255.6, 67765.8, 66374.4, 66555.9], ["03-31 18:00", 66556.0, 67262.2, 66555.9, 66700.0], ["03-31 19:00", 66700.0, 67985.5, 66695.9, 67632.6], ["03-31 20:00", 67632.6, 68600.0, 67357.1, 67493.9], ["03-31 21:00", 67493.8, 67929.7, 67488.0, 67814.6]],
        "klines_15m": [["03-31 08:45", 67643.4, 67756.8, 67623.3, 67648.9], ["03-31 09:00", 67649.0, 67679.5, 67431.4, 67446.5], ["03-31 09:15", 67446.6, 67482.3, 67300.1, 67383.2], ["03-31 09:30", 67383.3, 67457.3, 67307.6, 67379.0], ["03-31 09:45", 67379.1, 67505.8, 67379.0, 67465.4], ["03-31 10:00", 67465.4, 67497.0, 67200.0, 67267.2], ["03-31 10:15", 67267.2, 67296.4, 67071.9, 67260.9], ["03-31 10:30", 67260.8, 67350.0, 67179.7, 67299.9], ["03-31 10:45", 67299.9, 67410.0, 67281.2, 67343.8], ["03-31 11:00", 67343.9, 67476.9, 67208.4, 67324.0], ["03-31 11:15", 67323.9, 67420.0, 67250.6, 67280.4], ["03-31 11:30", 67280.3, 67281.9, 66777.0, 66818.9], ["03-31 11:45", 66818.9, 66911.9, 66655.0, 66745.1], ["03-31 12:00", 66745.1, 66891.8, 66550.0, 66669.5], ["03-31 12:15", 66669.6, 66686.3, 66321.0, 66403.9], ["03-31 12:30", 66403.9, 66499.7, 66368.0, 66477.4], ["03-31 12:45", 66477.4, 66487.0, 65938.0, 66099.3], ["03-31 13:00", 66099.3, 66371.9, 66067.0, 66342.5], ["03-31 13:15", 66342.4, 66432.0, 66313.2, 66350.0], ["03-31 13:30", 66350.1, 66398.5, 66188.7, 66247.3], ["03-31 13:45", 66247.2, 66442.0, 66214.6, 66329.4], ["03-31 14:00", 66329.4, 66572.3, 66205.0, 66543.4], ["03-31 14:15", 66543.3, 66850.0, 66500.0, 66610.0], ["03-31 14:30", 66610.0, 66805.7, 66603.9, 66696.1], ["03-31 14:45", 66696.0, 66696.1, 66534.0, 66652.4], ["03-31 15:00", 66652.4, 66766.5, 66535.0, 66541.3], ["03-31 15:15", 66541.3, 66799.4, 66480.0, 66764.5], ["03-31 15:30", 66764.4, 66909.3, 66692.5, 66872.9], ["03-31 15:45", 66872.8, 66888.0, 66615.2, 66623.8], ["03-31 16:00", 66623.8, 66818.9, 66623.8, 66792.0], ["03-31 16:15", 66792.0, 66932.6, 66719.9, 66773.8], ["03-31 16:30", 66773.7, 67166.5, 66691.9, 66937.6], ["03-31 16:45", 66937.6, 67375.0, 66937.6, 67255.6], ["03-31 17:00", 67255.6, 67500.0, 67078.8, 67300.4], ["03-31 17:15", 67300.0, 67765.8, 67285.2, 67692.7], ["03-31 17:30", 67692.7, 67712.2, 67047.5, 67184.3], ["03-31 17:45", 67184.2, 67184.3, 66374.4, 66555.9], ["03-31 18:00", 66556.0, 67262.2, 66555.9, 67210.5], ["03-31 18:15", 67210.6, 67255.0, 66864.9, 66920.8], ["03-31 18:30", 66920.8, 67127.4, 66841.8, 66906.5], ["03-31 18:45", 66906.5, 67019.1, 66666.5, 66700.0], ["03-31 19:00", 66700.0, 66970.4, 66695.9, 66893.2], ["03-31 19:15", 66893.1, 67165.5, 66881.5, 67056.5], ["03-31 19:30", 67056.4, 67985.5, 66916.6, 67742.0], ["03-31 19:45", 67742.1, 67888.0, 67457.0, 67632.6], ["03-31 20:00", 67632.6, 68532.7, 67532.8, 68432.9], ["03-31 20:15", 68432.8, 68600.0, 67951.2, 68002.3], ["03-31 20:30", 68002.4, 68091.9, 67573.9, 67683.7], ["03-31 20:45", 67683.6, 67749.0, 67357.1, 67493.9], ["03-31 21:00", 67493.8, 67764.9, 67488.0, 67739.7]]
    },

    "R11": {
        "data_15m": {"current_price": 68226.0, "ma5": 68210.48, "ma10": 68181.55, "ma30": 67986.65, "volume": 23000000, "volume_ma5": 46800000, "volume_ma10": 58600000, "net_long": -1300, "net_short": 6300, "futures_cvd": -35800000, "spot_cvd": -514, "taker_ls_ratio": 1.632, "oi": 89200, "oi_delta": 25.5, "liquidations": {"long": 478, "short": 1000}},
        "data_1h": {"current_price": 68234.7, "ma5": 68128.22, "ma10": 67683.82, "ma30": 67239.89, "volume": 200800000, "volume_ma5": 280400000, "volume_ma10": 790400000, "net_long": 21200, "net_short": -5000, "futures_cvd": 34600000, "spot_cvd": -6300, "taker_ls_ratio": 1.632, "oi": 89200, "oi_delta": 63.0, "liquidations": {"long": 76700, "short": 198500}},
        "data_4h": {"current_price": 68238.1, "ma5": 67348.29, "ma10": 67293.85, "ma30": 66943.65, "volume": 1090000000, "volume_ma5": 2750000000, "volume_ma10": 2430000000, "net_long": -25200, "net_short": 12100, "futures_cvd": -18100000, "spot_cvd": -82700, "taker_ls_ratio": 1.632, "oi": 89200, "oi_delta": 28.8, "liquidations": {"long": 299500, "short": 767100}},
        "actual": 'UP', "move": 1053,
        "run_time": "04-01 02:50",
        "whale_acct_ls": 0.8714,
        "api_whale_account": [['03-30 12:00', 0.9291], ['03-30 13:00', 0.9283], ['03-30 14:00', 0.9241], ['03-30 15:00', 0.9305], ['03-30 16:00', 0.9209], ['03-30 17:00', 0.9235], ['03-30 18:00', 0.9479], ['03-30 19:00', 0.9319], ['03-30 20:00', 0.9355], ['03-30 21:00', 0.9348], ['03-30 22:00', 0.9511], ['03-30 23:00', 0.9425], ['03-31 00:00', 0.9364], ['03-31 01:00', 0.9215], ['03-31 02:00', 0.8922], ['03-31 03:00', 0.8971], ['03-31 04:00', 0.8933], ['03-31 05:00', 0.89], ['03-31 06:00', 0.898], ['03-31 07:00', 0.8898], ['03-31 08:00', 0.8931], ['03-31 09:00', 0.9149], ['03-31 10:00', 0.9315], ['03-31 11:00', 0.9375], ['03-31 12:00', 0.9508], ['03-31 13:00', 0.9432], ['03-31 14:00', 0.8967], ['03-31 15:00', 0.8852], ['03-31 16:00', 0.8674], ['03-31 17:00', 0.8653]],
        "api_whale_position": [['03-30 12:00', 1.8539], ['03-30 13:00', 1.8121], ['03-30 14:00', 1.73], ['03-30 15:00', 1.7465], ['03-30 16:00', 1.7211], ['03-30 17:00', 1.7375], ['03-30 18:00', 1.8353], ['03-30 19:00', 1.876], ['03-30 20:00', 1.9472], ['03-30 21:00', 1.9656], ['03-30 22:00', 1.9735], ['03-30 23:00', 1.978], ['03-31 00:00', 2.0048], ['03-31 01:00', 2.0637], ['03-31 02:00', 1.9647], ['03-31 03:00', 1.8662], ['03-31 04:00', 1.8329], ['03-31 05:00', 1.8417], ['03-31 06:00', 1.8678], ['03-31 07:00', 1.8868], ['03-31 08:00', 1.9155], ['03-31 09:00', 2.0157], ['03-31 10:00', 2.1636], ['03-31 11:00', 2.2321], ['03-31 12:00', 2.2436], ['03-31 13:00', 2.1939], ['03-31 14:00', 2.1556], ['03-31 15:00', 2.1172], ['03-31 16:00', 2.0276], ['03-31 17:00', 1.963]],
        "api_open_interest": [['03-30 12:00', 91672.58], ['03-30 13:00', 91850.04], ['03-30 14:00', 92098.94], ['03-30 15:00', 91665.96], ['03-30 16:00', 91918.91], ['03-30 17:00', 91973.96], ['03-30 18:00', 91316.51], ['03-30 19:00', 90205.02], ['03-30 20:00', 89691.53], ['03-30 21:00', 89449.5], ['03-30 22:00', 89241.14], ['03-30 23:00', 89140.5], ['03-31 00:00', 89941.69], ['03-31 01:00', 89815.59], ['03-31 02:00', 90079.72], ['03-31 03:00', 90411.65], ['03-31 04:00', 90575.06], ['03-31 05:00', 90614.34], ['03-31 06:00', 90113.58], ['03-31 07:00', 90359.31], ['03-31 08:00', 90709.16], ['03-31 09:00', 90618.96], ['03-31 10:00', 90565.44], ['03-31 11:00', 90783.49], ['03-31 12:00', 91274.53], ['03-31 13:00', 91149.98], ['03-31 14:00', 91315.98], ['03-31 15:00', 91202.41], ['03-31 16:00', 91570.9], ['03-31 17:00', 91156.68]],
        "api_funding_rate": [['03-29 00:00', -3.68e-05, 66337.79], ['03-29 08:00', -1.2e-07, 66633.23], ['03-29 16:00', 2.677e-05, 66500.0], ['03-30 00:00', 3e-06, 65973.4], ['03-30 08:00', 4.92e-06, 67596.7], ['03-30 16:00', 7.58e-06, 67595.59], ['03-31 00:00', 1.16e-06, 66764.4], ['03-31 08:00', -1.921e-05, 67343.9], ['03-31 16:00', -2.763e-05, 66700.0]],
        "klines_4h": [["03-30 11:00", 67595.9, 67998.0, 67333.3, 67651.5], ["03-30 15:00", 67651.5, 68148.4, 67055.0, 67590.2], ["03-30 19:00", 67590.2, 67614.9, 66200.1, 66516.0], ["03-30 23:00", 66515.9, 66973.5, 66377.1, 66764.4], ["03-31 03:00", 66764.4, 68377.0, 66498.9, 67670.8], ["03-31 07:00", 67670.8, 67865.7, 67071.9, 67343.8], ["03-31 11:00", 67343.9, 67476.9, 65938.0, 66652.4], ["03-31 15:00", 66652.4, 67765.8, 66374.4, 66700.0], ["03-31 19:00", 66700.0, 68600.0, 66695.9, 67803.0], ["03-31 23:00", 67803.0, 68382.9, 67794.8, 68241.5]],
        "klines_1h": [["03-30 21:00", 66805.1, 66899.9, 66456.4, 66620.6], ["03-30 22:00", 66620.6, 66640.0, 66200.1, 66516.0], ["03-30 23:00", 66515.9, 66662.6, 66488.7, 66614.9], ["03-31 00:00", 66614.9, 66973.5, 66550.0, 66770.6], ["03-31 01:00", 66770.6, 66971.2, 66650.9, 66746.5], ["03-31 02:00", 66746.4, 66769.1, 66377.1, 66764.4], ["03-31 03:00", 66764.4, 67276.0, 66498.9, 67172.5], ["03-31 04:00", 67172.5, 68377.0, 67004.2, 67896.2], ["03-31 05:00", 67896.1, 68072.7, 67726.9, 67911.8], ["03-31 06:00", 67911.8, 67974.8, 67610.5, 67670.8], ["03-31 07:00", 67670.8, 67865.7, 67441.8, 67510.1], ["03-31 08:00", 67510.1, 67756.8, 67356.4, 67648.9], ["03-31 09:00", 67649.0, 67679.5, 67300.1, 67465.4], ["03-31 10:00", 67465.4, 67497.0, 67071.9, 67343.8], ["03-31 11:00", 67343.9, 67476.9, 66655.0, 66745.1], ["03-31 12:00", 66745.1, 66891.8, 65938.0, 66099.3], ["03-31 13:00", 66099.3, 66442.0, 66067.0, 66329.4], ["03-31 14:00", 66329.4, 66850.0, 66205.0, 66652.4], ["03-31 15:00", 66652.4, 66909.3, 66480.0, 66623.8], ["03-31 16:00", 66623.8, 67375.0, 66623.8, 67255.6], ["03-31 17:00", 67255.6, 67765.8, 66374.4, 66555.9], ["03-31 18:00", 66556.0, 67262.2, 66555.9, 66700.0], ["03-31 19:00", 66700.0, 67985.5, 66695.9, 67632.6], ["03-31 20:00", 67632.6, 68600.0, 67357.1, 67493.9], ["03-31 21:00", 67493.8, 67929.7, 67488.0, 67814.6], ["03-31 22:00", 67814.5, 67996.0, 67671.3, 67803.0], ["03-31 23:00", 67803.0, 68234.0, 67794.8, 68227.2], ["04-01 00:00", 68227.3, 68382.9, 67840.4, 68234.6], ["04-01 01:00", 68234.7, 68306.9, 67919.5, 68141.6], ["04-01 02:00", 68141.7, 68332.6, 68050.0, 68241.5]],
        "klines_15m": [["03-31 14:30", 66610.0, 66805.7, 66603.9, 66696.1], ["03-31 14:45", 66696.0, 66696.1, 66534.0, 66652.4], ["03-31 15:00", 66652.4, 66766.5, 66535.0, 66541.3], ["03-31 15:15", 66541.3, 66799.4, 66480.0, 66764.5], ["03-31 15:30", 66764.4, 66909.3, 66692.5, 66872.9], ["03-31 15:45", 66872.8, 66888.0, 66615.2, 66623.8], ["03-31 16:00", 66623.8, 66818.9, 66623.8, 66792.0], ["03-31 16:15", 66792.0, 66932.6, 66719.9, 66773.8], ["03-31 16:30", 66773.7, 67166.5, 66691.9, 66937.6], ["03-31 16:45", 66937.6, 67375.0, 66937.6, 67255.6], ["03-31 17:00", 67255.6, 67500.0, 67078.8, 67300.4], ["03-31 17:15", 67300.0, 67765.8, 67285.2, 67692.7], ["03-31 17:30", 67692.7, 67712.2, 67047.5, 67184.3], ["03-31 17:45", 67184.2, 67184.3, 66374.4, 66555.9], ["03-31 18:00", 66556.0, 67262.2, 66555.9, 67210.5], ["03-31 18:15", 67210.6, 67255.0, 66864.9, 66920.8], ["03-31 18:30", 66920.8, 67127.4, 66841.8, 66906.5], ["03-31 18:45", 66906.5, 67019.1, 66666.5, 66700.0], ["03-31 19:00", 66700.0, 66970.4, 66695.9, 66893.2], ["03-31 19:15", 66893.1, 67165.5, 66881.5, 67056.5], ["03-31 19:30", 67056.4, 67985.5, 66916.6, 67742.0], ["03-31 19:45", 67742.1, 67888.0, 67457.0, 67632.6], ["03-31 20:00", 67632.6, 68532.7, 67532.8, 68432.9], ["03-31 20:15", 68432.8, 68600.0, 67951.2, 68002.3], ["03-31 20:30", 68002.4, 68091.9, 67573.9, 67683.7], ["03-31 20:45", 67683.6, 67749.0, 67357.1, 67493.9], ["03-31 21:00", 67493.8, 67764.9, 67488.0, 67739.7], ["03-31 21:15", 67739.7, 67929.7, 67594.4, 67744.9], ["03-31 21:30", 67744.9, 67855.4, 67601.9, 67789.9], ["03-31 21:45", 67789.9, 67912.8, 67700.4, 67814.6], ["03-31 22:00", 67814.5, 67985.8, 67802.0, 67952.5], ["03-31 22:15", 67952.6, 67996.0, 67810.5, 67840.3], ["03-31 22:30", 67840.4, 67901.0, 67671.3, 67800.0], ["03-31 22:45", 67799.9, 67934.9, 67694.0, 67803.0], ["03-31 23:00", 67803.0, 68177.2, 67794.8, 68109.6], ["03-31 23:15", 68109.6, 68135.6, 67902.4, 67967.3], ["03-31 23:30", 67967.2, 68099.1, 67911.1, 68017.1], ["03-31 23:45", 68017.1, 68234.0, 67985.0, 68227.2], ["04-01 00:00", 68227.3, 68227.3, 67911.2, 67977.3], ["04-01 00:15", 67977.3, 68030.0, 67840.4, 67995.9], ["04-01 00:30", 67995.9, 68138.0, 67991.7, 68130.0], ["04-01 00:45", 68130.1, 68382.9, 68119.0, 68234.6], ["04-01 01:00", 68234.7, 68306.9, 68013.4, 68172.8], ["04-01 01:15", 68172.8, 68254.4, 68057.4, 68080.0], ["04-01 01:30", 68080.1, 68214.9, 67919.5, 68140.0], ["04-01 01:45", 68140.1, 68183.4, 68057.1, 68141.6], ["04-01 02:00", 68141.7, 68250.0, 68050.0, 68183.7], ["04-01 02:15", 68183.6, 68332.6, 68141.0, 68224.3], ["04-01 02:30", 68224.2, 68332.0, 68200.0, 68271.3], ["04-01 02:45", 68271.4, 68297.1, 68173.1, 68241.5]]
    },

    "R12": {
        "data_15m": {"current_price": 67893.0, "ma5": 67737.73, "ma10": 67837.62, "ma30": 68025.95, "volume": 41100000, "volume_ma5": 76800000, "volume_ma10": 86000000, "net_long": -1800, "net_short": 6500, "futures_cvd": -42100000, "spot_cvd": -655, "taker_ls_ratio": 1.592, "oi": 89800, "oi_delta": 60.6, "liquidations": {"long": 2400, "short": 3700}},
        "data_1h": {"current_price": 67893.0, "ma5": 67958.52, "ma10": 68001.36, "ma30": 67407.74, "volume": 166500000, "volume_ma5": 296500000, "volume_ma10": 313600000, "net_long": 20200, "net_short": -3400, "futures_cvd": 30100000, "spot_cvd": -6800, "taker_ls_ratio": 1.592, "oi": 89900, "oi_delta": -96.2, "liquidations": {"long": 2400, "short": 166600}},
        "data_4h": {"current_price": 67890.0, "ma5": 67458.2, "ma10": 67318.22, "ma30": 66915.8, "volume": 1260000000, "volume_ma5": 2710000000, "volume_ma10": 2390000000, "net_long": -24200, "net_short": 13000, "futures_cvd": -15300000, "spot_cvd": -81400, "taker_ls_ratio": 1.592, "oi": 89200, "oi_delta": 669.5, "liquidations": {"long": 956200, "short": 436500}},
        "actual": 'UP', "move": 307,
        "run_time": "04-01 03:43",
        "whale_acct_ls": 0.8683,
        "api_whale_account": [['03-30 17:00', 0.9235], ['03-30 18:00', 0.9479], ['03-30 19:00', 0.9319], ['03-30 20:00', 0.9355], ['03-30 21:00', 0.9348], ['03-30 22:00', 0.9511], ['03-30 23:00', 0.9425], ['03-31 00:00', 0.9364], ['03-31 01:00', 0.9215], ['03-31 02:00', 0.8922], ['03-31 03:00', 0.8971], ['03-31 04:00', 0.8933], ['03-31 05:00', 0.89], ['03-31 06:00', 0.898], ['03-31 07:00', 0.8898], ['03-31 08:00', 0.8931], ['03-31 09:00', 0.9149], ['03-31 10:00', 0.9315], ['03-31 11:00', 0.9375], ['03-31 12:00', 0.9508], ['03-31 13:00', 0.9432], ['03-31 14:00', 0.8967], ['03-31 15:00', 0.8852], ['03-31 16:00', 0.8674], ['03-31 17:00', 0.8653], ['03-31 18:00', 0.8748], ['03-31 19:00', 0.8762], ['03-31 20:00', 0.8776], ['03-31 21:00', 0.8745], ['03-31 22:00', 0.8747]],
        "api_whale_position": [['03-30 17:00', 1.7375], ['03-30 18:00', 1.8353], ['03-30 19:00', 1.876], ['03-30 20:00', 1.9472], ['03-30 21:00', 1.9656], ['03-30 22:00', 1.9735], ['03-30 23:00', 1.978], ['03-31 00:00', 2.0048], ['03-31 01:00', 2.0637], ['03-31 02:00', 1.9647], ['03-31 03:00', 1.8662], ['03-31 04:00', 1.8329], ['03-31 05:00', 1.8417], ['03-31 06:00', 1.8678], ['03-31 07:00', 1.8868], ['03-31 08:00', 1.9155], ['03-31 09:00', 2.0157], ['03-31 10:00', 2.1636], ['03-31 11:00', 2.2321], ['03-31 12:00', 2.2436], ['03-31 13:00', 2.1939], ['03-31 14:00', 2.1556], ['03-31 15:00', 2.1172], ['03-31 16:00', 2.0276], ['03-31 17:00', 1.963], ['03-31 18:00', 1.8612], ['03-31 19:00', 1.8588], ['03-31 20:00', 1.8305], ['03-31 21:00', 1.7747], ['03-31 22:00', 1.7412]],
        "api_open_interest": [['03-30 17:00', 91973.96], ['03-30 18:00', 91316.51], ['03-30 19:00', 90205.02], ['03-30 20:00', 89691.53], ['03-30 21:00', 89449.5], ['03-30 22:00', 89241.14], ['03-30 23:00', 89140.5], ['03-31 00:00', 89941.69], ['03-31 01:00', 89815.59], ['03-31 02:00', 90079.72], ['03-31 03:00', 90411.65], ['03-31 04:00', 90575.06], ['03-31 05:00', 90614.34], ['03-31 06:00', 90113.58], ['03-31 07:00', 90359.31], ['03-31 08:00', 90709.16], ['03-31 09:00', 90618.96], ['03-31 10:00', 90565.44], ['03-31 11:00', 90783.49], ['03-31 12:00', 91274.53], ['03-31 13:00', 91149.98], ['03-31 14:00', 91315.98], ['03-31 15:00', 91202.41], ['03-31 16:00', 91570.9], ['03-31 17:00', 91156.68], ['03-31 18:00', 89453.29], ['03-31 19:00', 89342.53], ['03-31 20:00', 89165.95], ['03-31 21:00', 89005.65], ['03-31 22:00', 88746.48]],
        "api_funding_rate": [['03-29 00:00', -3.68e-05, 66337.79], ['03-29 08:00', -1.2e-07, 66633.23], ['03-29 16:00', 2.677e-05, 66500.0], ['03-30 00:00', 3e-06, 65973.4], ['03-30 08:00', 4.92e-06, 67596.7], ['03-30 16:00', 7.58e-06, 67595.59], ['03-31 00:00', 1.16e-06, 66764.4], ['03-31 08:00', -1.921e-05, 67343.9], ['03-31 16:00', -2.763e-05, 66700.0]],
        "klines_4h": [["03-30 15:00", 67651.5, 68148.4, 67055.0, 67590.2], ["03-30 19:00", 67590.2, 67614.9, 66200.1, 66516.0], ["03-30 23:00", 66515.9, 66973.5, 66377.1, 66764.4], ["03-31 03:00", 66764.4, 68377.0, 66498.9, 67670.8], ["03-31 07:00", 67670.8, 67865.7, 67071.9, 67343.8], ["03-31 11:00", 67343.9, 67476.9, 65938.0, 66652.4], ["03-31 15:00", 66652.4, 67765.8, 66374.4, 66700.0], ["03-31 19:00", 66700.0, 68600.0, 66695.9, 67803.0], ["03-31 23:00", 67803.0, 68382.9, 67794.8, 68241.5], ["04-01 03:00", 68241.4, 68330.0, 67534.9, 68134.0]],
        "klines_1h": [["03-30 22:00", 66620.6, 66640.0, 66200.1, 66516.0], ["03-30 23:00", 66515.9, 66662.6, 66488.7, 66614.9], ["03-31 00:00", 66614.9, 66973.5, 66550.0, 66770.6], ["03-31 01:00", 66770.6, 66971.2, 66650.9, 66746.5], ["03-31 02:00", 66746.4, 66769.1, 66377.1, 66764.4], ["03-31 03:00", 66764.4, 67276.0, 66498.9, 67172.5], ["03-31 04:00", 67172.5, 68377.0, 67004.2, 67896.2], ["03-31 05:00", 67896.1, 68072.7, 67726.9, 67911.8], ["03-31 06:00", 67911.8, 67974.8, 67610.5, 67670.8], ["03-31 07:00", 67670.8, 67865.7, 67441.8, 67510.1], ["03-31 08:00", 67510.1, 67756.8, 67356.4, 67648.9], ["03-31 09:00", 67649.0, 67679.5, 67300.1, 67465.4], ["03-31 10:00", 67465.4, 67497.0, 67071.9, 67343.8], ["03-31 11:00", 67343.9, 67476.9, 66655.0, 66745.1], ["03-31 12:00", 66745.1, 66891.8, 65938.0, 66099.3], ["03-31 13:00", 66099.3, 66442.0, 66067.0, 66329.4], ["03-31 14:00", 66329.4, 66850.0, 66205.0, 66652.4], ["03-31 15:00", 66652.4, 66909.3, 66480.0, 66623.8], ["03-31 16:00", 66623.8, 67375.0, 66623.8, 67255.6], ["03-31 17:00", 67255.6, 67765.8, 66374.4, 66555.9], ["03-31 18:00", 66556.0, 67262.2, 66555.9, 66700.0], ["03-31 19:00", 66700.0, 67985.5, 66695.9, 67632.6], ["03-31 20:00", 67632.6, 68600.0, 67357.1, 67493.9], ["03-31 21:00", 67493.8, 67929.7, 67488.0, 67814.6], ["03-31 22:00", 67814.5, 67996.0, 67671.3, 67803.0], ["03-31 23:00", 67803.0, 68234.0, 67794.8, 68227.2], ["04-01 00:00", 68227.3, 68382.9, 67840.4, 68234.6], ["04-01 01:00", 68234.7, 68306.9, 67919.5, 68141.6], ["04-01 02:00", 68141.7, 68332.6, 68050.0, 68241.5], ["04-01 03:00", 68241.4, 68305.1, 67808.1, 68288.0]],
        "klines_15m": [["03-31 15:15", 66541.3, 66799.4, 66480.0, 66764.5], ["03-31 15:30", 66764.4, 66909.3, 66692.5, 66872.9], ["03-31 15:45", 66872.8, 66888.0, 66615.2, 66623.8], ["03-31 16:00", 66623.8, 66818.9, 66623.8, 66792.0], ["03-31 16:15", 66792.0, 66932.6, 66719.9, 66773.8], ["03-31 16:30", 66773.7, 67166.5, 66691.9, 66937.6], ["03-31 16:45", 66937.6, 67375.0, 66937.6, 67255.6], ["03-31 17:00", 67255.6, 67500.0, 67078.8, 67300.4], ["03-31 17:15", 67300.0, 67765.8, 67285.2, 67692.7], ["03-31 17:30", 67692.7, 67712.2, 67047.5, 67184.3], ["03-31 17:45", 67184.2, 67184.3, 66374.4, 66555.9], ["03-31 18:00", 66556.0, 67262.2, 66555.9, 67210.5], ["03-31 18:15", 67210.6, 67255.0, 66864.9, 66920.8], ["03-31 18:30", 66920.8, 67127.4, 66841.8, 66906.5], ["03-31 18:45", 66906.5, 67019.1, 66666.5, 66700.0], ["03-31 19:00", 66700.0, 66970.4, 66695.9, 66893.2], ["03-31 19:15", 66893.1, 67165.5, 66881.5, 67056.5], ["03-31 19:30", 67056.4, 67985.5, 66916.6, 67742.0], ["03-31 19:45", 67742.1, 67888.0, 67457.0, 67632.6], ["03-31 20:00", 67632.6, 68532.7, 67532.8, 68432.9], ["03-31 20:15", 68432.8, 68600.0, 67951.2, 68002.3], ["03-31 20:30", 68002.4, 68091.9, 67573.9, 67683.7], ["03-31 20:45", 67683.6, 67749.0, 67357.1, 67493.9], ["03-31 21:00", 67493.8, 67764.9, 67488.0, 67739.7], ["03-31 21:15", 67739.7, 67929.7, 67594.4, 67744.9], ["03-31 21:30", 67744.9, 67855.4, 67601.9, 67789.9], ["03-31 21:45", 67789.9, 67912.8, 67700.4, 67814.6], ["03-31 22:00", 67814.5, 67985.8, 67802.0, 67952.5], ["03-31 22:15", 67952.6, 67996.0, 67810.5, 67840.3], ["03-31 22:30", 67840.4, 67901.0, 67671.3, 67800.0], ["03-31 22:45", 67799.9, 67934.9, 67694.0, 67803.0], ["03-31 23:00", 67803.0, 68177.2, 67794.8, 68109.6], ["03-31 23:15", 68109.6, 68135.6, 67902.4, 67967.3], ["03-31 23:30", 67967.2, 68099.1, 67911.1, 68017.1], ["03-31 23:45", 68017.1, 68234.0, 67985.0, 68227.2], ["04-01 00:00", 68227.3, 68227.3, 67911.2, 67977.3], ["04-01 00:15", 67977.3, 68030.0, 67840.4, 67995.9], ["04-01 00:30", 67995.9, 68138.0, 67991.7, 68130.0], ["04-01 00:45", 68130.1, 68382.9, 68119.0, 68234.6], ["04-01 01:00", 68234.7, 68306.9, 68013.4, 68172.8], ["04-01 01:15", 68172.8, 68254.4, 68057.4, 68080.0], ["04-01 01:30", 68080.1, 68214.9, 67919.5, 68140.0], ["04-01 01:45", 68140.1, 68183.4, 68057.1, 68141.6], ["04-01 02:00", 68141.7, 68250.0, 68050.0, 68183.7], ["04-01 02:15", 68183.6, 68332.6, 68141.0, 68224.3], ["04-01 02:30", 68224.2, 68332.0, 68200.0, 68271.3], ["04-01 02:45", 68271.4, 68297.1, 68173.1, 68241.5], ["04-01 03:00", 68241.4, 68241.5, 67975.3, 68004.7], ["04-01 03:15", 68004.6, 68177.9, 67863.3, 67964.3], ["04-01 03:30", 67964.3, 68031.7, 67808.1, 68031.2]]
    },

    "R13": {
        "data_15m": {"current_price": 68492.0, "ma5": 68511.23, "ma10": 68560.51, "ma30": 68510.36, "volume": 42300000, "volume_ma5": 60500000, "volume_ma10": 98200000, "net_long": -30, "net_short": 5500, "futures_cvd": -32100000, "spot_cvd": -460, "taker_ls_ratio": 1.401, "oi": 91300, "oi_delta": -12.9, "liquidations": {"long": 137, "short": 0}},
        "data_1h": {"current_price": 68492.0, "ma5": 68691.27, "ma10": 68365.09, "ma30": 67698.27, "volume": 81300000, "volume_ma5": 531400000, "volume_ma10": 472400000, "net_long": 21200, "net_short": -3100, "futures_cvd": 31600000, "spot_cvd": -7000, "taker_ls_ratio": 1.401, "oi": 91200, "oi_delta": 31.9, "liquidations": {"long": 274, "short": 0}},
        "data_4h": {"current_price": 68492.0, "ma5": 68267.58, "ma10": 67647.9, "ma30": 66990.62, "volume": 982400000, "volume_ma5": 2060000000, "volume_ma10": 2260000000, "net_long": -25200, "net_short": 13900, "futures_cvd": -6300000, "spot_cvd": -80600, "taker_ls_ratio": 1.401, "oi": 91200, "oi_delta": 1.08, "liquidations": {"long": 209300, "short": 64900}},
        "actual": 'DOWN', "move": -2816,
        "run_time": "04-01 10:45",
        "whale_acct_ls": 0.8528,
        "api_whale_account": [['03-31 00:00', 0.9364], ['03-31 01:00', 0.9215], ['03-31 02:00', 0.8922], ['03-31 03:00', 0.8971], ['03-31 04:00', 0.8933], ['03-31 05:00', 0.89], ['03-31 06:00', 0.898], ['03-31 07:00', 0.8898], ['03-31 08:00', 0.8931], ['03-31 09:00', 0.9149], ['03-31 10:00', 0.9315], ['03-31 11:00', 0.9375], ['03-31 12:00', 0.9508], ['03-31 13:00', 0.9432], ['03-31 14:00', 0.8967], ['03-31 15:00', 0.8852], ['03-31 16:00', 0.8674], ['03-31 17:00', 0.8653], ['03-31 18:00', 0.8748], ['03-31 19:00', 0.8762], ['03-31 20:00', 0.8776], ['03-31 21:00', 0.8745], ['03-31 22:00', 0.8747], ['03-31 23:00', 0.8714], ['04-01 00:00', 0.8683], ['04-01 01:00', 0.8667], ['04-01 02:00', 0.8547], ['04-01 03:00', 0.8666], ['04-01 04:00', 0.8705], ['04-01 05:00', 0.8621]],
        "api_whale_position": [['03-31 00:00', 2.0048], ['03-31 01:00', 2.0637], ['03-31 02:00', 1.9647], ['03-31 03:00', 1.8662], ['03-31 04:00', 1.8329], ['03-31 05:00', 1.8417], ['03-31 06:00', 1.8678], ['03-31 07:00', 1.8868], ['03-31 08:00', 1.9155], ['03-31 09:00', 2.0157], ['03-31 10:00', 2.1636], ['03-31 11:00', 2.2321], ['03-31 12:00', 2.2436], ['03-31 13:00', 2.1939], ['03-31 14:00', 2.1556], ['03-31 15:00', 2.1172], ['03-31 16:00', 2.0276], ['03-31 17:00', 1.963], ['03-31 18:00', 1.8612], ['03-31 19:00', 1.8588], ['03-31 20:00', 1.8305], ['03-31 21:00', 1.7747], ['03-31 22:00', 1.7412], ['03-31 23:00', 1.7108], ['04-01 00:00', 1.6824], ['04-01 01:00', 1.649], ['04-01 02:00', 1.635], ['04-01 03:00', 1.7064], ['04-01 04:00', 1.6911], ['04-01 05:00', 1.6476]],
        "api_open_interest": [['03-31 00:00', 89941.69], ['03-31 01:00', 89815.59], ['03-31 02:00', 90079.72], ['03-31 03:00', 90411.65], ['03-31 04:00', 90575.06], ['03-31 05:00', 90614.34], ['03-31 06:00', 90113.58], ['03-31 07:00', 90359.31], ['03-31 08:00', 90709.16], ['03-31 09:00', 90618.96], ['03-31 10:00', 90565.44], ['03-31 11:00', 90783.49], ['03-31 12:00', 91274.53], ['03-31 13:00', 91149.98], ['03-31 14:00', 91315.98], ['03-31 15:00', 91202.41], ['03-31 16:00', 91570.9], ['03-31 17:00', 91156.68], ['03-31 18:00', 89453.29], ['03-31 19:00', 89342.53], ['03-31 20:00', 89165.95], ['03-31 21:00', 89005.65], ['03-31 22:00', 88746.48], ['03-31 23:00', 89128.25], ['04-01 00:00', 89212.45], ['04-01 01:00', 89555.26], ['04-01 02:00', 90026.03], ['04-01 03:00', 89978.67], ['04-01 04:00', 90147.71], ['04-01 05:00', 90562.41]],
        "api_funding_rate": [['03-29 00:00', -3.68e-05, 66337.79], ['03-29 08:00', -1.2e-07, 66633.23], ['03-29 16:00', 2.677e-05, 66500.0], ['03-30 00:00', 3e-06, 65973.4], ['03-30 08:00', 4.92e-06, 67596.7], ['03-30 16:00', 7.58e-06, 67595.59], ['03-31 00:00', 1.16e-06, 66764.4], ['03-31 08:00', -1.921e-05, 67343.9], ['03-31 16:00', -2.763e-05, 66700.0], ['04-01 00:00', -3.449e-05, 68243.3]],
        "klines_4h": [["03-30 19:00", 67590.2, 67614.9, 66200.1, 66516.0], ["03-30 23:00", 66515.9, 66973.5, 66377.1, 66764.4], ["03-31 03:00", 66764.4, 68377.0, 66498.9, 67670.8], ["03-31 07:00", 67670.8, 67865.7, 67071.9, 67343.8], ["03-31 11:00", 67343.9, 67476.9, 65938.0, 66652.4], ["03-31 15:00", 66652.4, 67765.8, 66374.4, 66700.0], ["03-31 19:00", 66700.0, 68600.0, 66695.9, 67803.0], ["03-31 23:00", 67803.0, 68382.9, 67794.8, 68241.5], ["04-01 03:00", 68241.4, 68330.0, 67534.9, 68134.0], ["04-01 07:00", 68134.0, 69288.0, 67965.0, 68651.9]],
        "klines_1h": [["03-31 05:00", 67896.1, 68072.7, 67726.9, 67911.8], ["03-31 06:00", 67911.8, 67974.8, 67610.5, 67670.8], ["03-31 07:00", 67670.8, 67865.7, 67441.8, 67510.1], ["03-31 08:00", 67510.1, 67756.8, 67356.4, 67648.9], ["03-31 09:00", 67649.0, 67679.5, 67300.1, 67465.4], ["03-31 10:00", 67465.4, 67497.0, 67071.9, 67343.8], ["03-31 11:00", 67343.9, 67476.9, 66655.0, 66745.1], ["03-31 12:00", 66745.1, 66891.8, 65938.0, 66099.3], ["03-31 13:00", 66099.3, 66442.0, 66067.0, 66329.4], ["03-31 14:00", 66329.4, 66850.0, 66205.0, 66652.4], ["03-31 15:00", 66652.4, 66909.3, 66480.0, 66623.8], ["03-31 16:00", 66623.8, 67375.0, 66623.8, 67255.6], ["03-31 17:00", 67255.6, 67765.8, 66374.4, 66555.9], ["03-31 18:00", 66556.0, 67262.2, 66555.9, 66700.0], ["03-31 19:00", 66700.0, 67985.5, 66695.9, 67632.6], ["03-31 20:00", 67632.6, 68600.0, 67357.1, 67493.9], ["03-31 21:00", 67493.8, 67929.7, 67488.0, 67814.6], ["03-31 22:00", 67814.5, 67996.0, 67671.3, 67803.0], ["03-31 23:00", 67803.0, 68234.0, 67794.8, 68227.2], ["04-01 00:00", 68227.3, 68382.9, 67840.4, 68234.6], ["04-01 01:00", 68234.7, 68306.9, 67919.5, 68141.6], ["04-01 02:00", 68141.7, 68332.6, 68050.0, 68241.5], ["04-01 03:00", 68241.4, 68305.1, 67808.1, 68288.0], ["04-01 04:00", 68288.0, 68330.0, 67707.5, 67746.4], ["04-01 05:00", 67746.4, 67881.2, 67534.9, 67623.8], ["04-01 06:00", 67623.9, 68214.5, 67623.9, 68134.0], ["04-01 07:00", 68134.0, 68450.0, 67965.0, 68272.3], ["04-01 08:00", 68272.3, 68732.5, 68114.5, 68418.2], ["04-01 09:00", 68418.3, 69220.0, 68418.2, 69069.1], ["04-01 10:00", 69069.1, 69288.0, 68631.1, 68651.9]],
        "klines_15m": [["03-31 17:45", 67184.2, 67184.3, 66374.4, 66555.9], ["03-31 18:00", 66556.0, 67262.2, 66555.9, 67210.5], ["03-31 18:15", 67210.6, 67255.0, 66864.9, 66920.8], ["03-31 18:30", 66920.8, 67127.4, 66841.8, 66906.5], ["03-31 18:45", 66906.5, 67019.1, 66666.5, 66700.0], ["03-31 19:00", 66700.0, 66970.4, 66695.9, 66893.2], ["03-31 19:15", 66893.1, 67165.5, 66881.5, 67056.5], ["03-31 19:30", 67056.4, 67985.5, 66916.6, 67742.0], ["03-31 19:45", 67742.1, 67888.0, 67457.0, 67632.6], ["03-31 20:00", 67632.6, 68532.7, 67532.8, 68432.9], ["03-31 20:15", 68432.8, 68600.0, 67951.2, 68002.3], ["03-31 20:30", 68002.4, 68091.9, 67573.9, 67683.7], ["03-31 20:45", 67683.6, 67749.0, 67357.1, 67493.9], ["03-31 21:00", 67493.8, 67764.9, 67488.0, 67739.7], ["03-31 21:15", 67739.7, 67929.7, 67594.4, 67744.9], ["03-31 21:30", 67744.9, 67855.4, 67601.9, 67789.9], ["03-31 21:45", 67789.9, 67912.8, 67700.4, 67814.6], ["03-31 22:00", 67814.5, 67985.8, 67802.0, 67952.5], ["03-31 22:15", 67952.6, 67996.0, 67810.5, 67840.3], ["03-31 22:30", 67840.4, 67901.0, 67671.3, 67800.0], ["03-31 22:45", 67799.9, 67934.9, 67694.0, 67803.0], ["03-31 23:00", 67803.0, 68177.2, 67794.8, 68109.6], ["03-31 23:15", 68109.6, 68135.6, 67902.4, 67967.3], ["03-31 23:30", 67967.2, 68099.1, 67911.1, 68017.1], ["03-31 23:45", 68017.1, 68234.0, 67985.0, 68227.2], ["04-01 00:00", 68227.3, 68227.3, 67911.2, 67977.3], ["04-01 00:15", 67977.3, 68030.0, 67840.4, 67995.9], ["04-01 00:30", 67995.9, 68138.0, 67991.7, 68130.0], ["04-01 00:45", 68130.1, 68382.9, 68119.0, 68234.6], ["04-01 01:00", 68234.7, 68306.9, 68013.4, 68172.8], ["04-01 01:15", 68172.8, 68254.4, 68057.4, 68080.0], ["04-01 01:30", 68080.1, 68214.9, 67919.5, 68140.0], ["04-01 01:45", 68140.1, 68183.4, 68057.1, 68141.6], ["04-01 02:00", 68141.7, 68250.0, 68050.0, 68183.7], ["04-01 02:15", 68183.6, 68332.6, 68141.0, 68224.3], ["04-01 02:30", 68224.2, 68332.0, 68200.0, 68271.3], ["04-01 02:45", 68271.4, 68297.1, 68173.1, 68241.5], ["04-01 03:00", 68241.4, 68241.5, 67975.3, 68004.7], ["04-01 03:15", 68004.6, 68177.9, 67863.3, 67964.3], ["04-01 03:30", 67964.3, 68031.7, 67808.1, 68031.2], ["04-01 03:45", 68031.2, 68305.1, 67989.8, 68288.0], ["04-01 04:00", 68288.0, 68330.0, 68106.3, 68223.7], ["04-01 04:15", 68223.8, 68223.8, 67976.5, 68006.4], ["04-01 04:30", 68006.3, 68054.7, 67755.1, 67915.8], ["04-01 04:45", 67915.9, 67920.0, 67707.5, 67746.4], ["04-01 05:00", 67746.4, 67873.1, 67662.2, 67803.3], ["04-01 05:15", 67803.3, 67881.2, 67556.1, 67603.6], ["04-01 05:30", 67603.7, 67691.3, 67534.9, 67617.7], ["04-01 05:45", 67617.7, 67705.8, 67558.7, 67623.8], ["04-01 06:00", 67623.9, 68086.2, 67623.9, 67957.5]]
    },

    "R14": {
        "data_15m": {"current_price": 68334.6, "ma5": 68448.66, "ma10": 68501.77, "ma30": 68627.95, "volume": 127500000, "volume_ma5": 176400000, "volume_ma10": 121000000, "net_long": 214.2, "net_short": 3000, "futures_cvd": -27500000, "spot_cvd": 324.1, "taker_ls_ratio": 1.429, "oi": 90800, "oi_delta": -66.8, "liquidations": {"long": 39200, "short": 134200}},
        "data_1h": {"current_price": 68327.4, "ma5": 68502.92, "ma10": 68555.68, "ma30": 67796.66, "volume": 429800000, "volume_ma5": 371200000, "volume_ma10": 511600000, "net_long": 18600, "net_short": -3200, "futures_cvd": 30100000, "spot_cvd": -7600, "taker_ls_ratio": 1.429, "oi": 90900, "oi_delta": -149.7, "liquidations": {"long": 303100, "short": 187300}},
        "data_4h": {"current_price": 68359.1, "ma5": 68413.54, "ma10": 67824.18, "ma30": 67071.91, "volume": 1070000000, "volume_ma5": 1530000000, "volume_ma10": 2290000000, "net_long": -26000, "net_short": 11200, "futures_cvd": 5800000, "spot_cvd": -79800, "taker_ls_ratio": 1.434, "oi": 91200, "oi_delta": -499.3, "liquidations": {"long": 976800, "short": 213200}},
        "actual": 'DOWN', "move": -2651,
        "run_time": "04-01 16:39",
        "whale_acct_ls": 0.8513,
        "api_whale_account": [['03-31 06:00', 0.898], ['03-31 07:00', 0.8898], ['03-31 08:00', 0.8931], ['03-31 09:00', 0.9149], ['03-31 10:00', 0.9315], ['03-31 11:00', 0.9375], ['03-31 12:00', 0.9508], ['03-31 13:00', 0.9432], ['03-31 14:00', 0.8967], ['03-31 15:00', 0.8852], ['03-31 16:00', 0.8674], ['03-31 17:00', 0.8653], ['03-31 18:00', 0.8748], ['03-31 19:00', 0.8762], ['03-31 20:00', 0.8776], ['03-31 21:00', 0.8745], ['03-31 22:00', 0.8747], ['03-31 23:00', 0.8714], ['04-01 00:00', 0.8683], ['04-01 01:00', 0.8667], ['04-01 02:00', 0.8547], ['04-01 03:00', 0.8666], ['04-01 04:00', 0.8705], ['04-01 05:00', 0.8621], ['04-01 06:00', 0.8581], ['04-01 07:00', 0.8528], ['04-01 08:00', 0.8502], ['04-01 09:00', 0.8428], ['04-01 10:00', 0.842], ['04-01 11:00', 0.8442]],
        "api_whale_position": [['03-31 06:00', 1.8678], ['03-31 07:00', 1.8868], ['03-31 08:00', 1.9155], ['03-31 09:00', 2.0157], ['03-31 10:00', 2.1636], ['03-31 11:00', 2.2321], ['03-31 12:00', 2.2436], ['03-31 13:00', 2.1939], ['03-31 14:00', 2.1556], ['03-31 15:00', 2.1172], ['03-31 16:00', 2.0276], ['03-31 17:00', 1.963], ['03-31 18:00', 1.8612], ['03-31 19:00', 1.8588], ['03-31 20:00', 1.8305], ['03-31 21:00', 1.7747], ['03-31 22:00', 1.7412], ['03-31 23:00', 1.7108], ['04-01 00:00', 1.6824], ['04-01 01:00', 1.649], ['04-01 02:00', 1.635], ['04-01 03:00', 1.7064], ['04-01 04:00', 1.6911], ['04-01 05:00', 1.6476], ['04-01 06:00', 1.5934], ['04-01 07:00', 1.4814], ['04-01 08:00', 1.4085], ['04-01 09:00', 1.4576], ['04-01 10:00', 1.4637], ['04-01 11:00', 1.4576]],
        "api_open_interest": [['03-31 06:00', 90113.58], ['03-31 07:00', 90359.31], ['03-31 08:00', 90709.16], ['03-31 09:00', 90618.96], ['03-31 10:00', 90565.44], ['03-31 11:00', 90783.49], ['03-31 12:00', 91274.53], ['03-31 13:00', 91149.98], ['03-31 14:00', 91315.98], ['03-31 15:00', 91202.41], ['03-31 16:00', 91570.9], ['03-31 17:00', 91156.68], ['03-31 18:00', 89453.29], ['03-31 19:00', 89342.53], ['03-31 20:00', 89165.95], ['03-31 21:00', 89005.65], ['03-31 22:00', 88746.48], ['03-31 23:00', 89128.25], ['04-01 00:00', 89212.45], ['04-01 01:00', 89555.26], ['04-01 02:00', 90026.03], ['04-01 03:00', 89978.67], ['04-01 04:00', 90147.71], ['04-01 05:00', 90562.41], ['04-01 06:00', 90503.71], ['04-01 07:00', 90916.1], ['04-01 08:00', 91248.89], ['04-01 09:00', 90807.26], ['04-01 10:00', 91215.04], ['04-01 11:00', 91225.25]],
        "api_funding_rate": [['03-29 08:00', -1.2e-07, 66633.23], ['03-29 16:00', 2.677e-05, 66500.0], ['03-30 00:00', 3e-06, 65973.4], ['03-30 08:00', 4.92e-06, 67596.7], ['03-30 16:00', 7.58e-06, 67595.59], ['03-31 00:00', 1.16e-06, 66764.4], ['03-31 08:00', -1.921e-05, 67343.9], ['03-31 16:00', -2.763e-05, 66700.0], ['04-01 00:00', -3.449e-05, 68243.3], ['04-01 08:00', -4.61e-06, 68668.6]],
        "klines_4h": [["03-31 03:00", 66764.4, 68377.0, 66498.9, 67670.8], ["03-31 07:00", 67670.8, 67865.7, 67071.9, 67343.8], ["03-31 11:00", 67343.9, 67476.9, 65938.0, 66652.4], ["03-31 15:00", 66652.4, 67765.8, 66374.4, 66700.0], ["03-31 19:00", 66700.0, 68600.0, 66695.9, 67803.0], ["03-31 23:00", 67803.0, 68382.9, 67794.8, 68241.5], ["04-01 03:00", 68241.4, 68330.0, 67534.9, 68134.0], ["04-01 07:00", 68134.0, 69288.0, 67965.0, 68651.9], ["04-01 11:00", 68651.9, 68821.5, 68360.0, 68669.9], ["04-01 15:00", 68670.0, 68938.8, 67883.7, 68877.0]],
        "klines_1h": [["03-31 11:00", 67343.9, 67476.9, 66655.0, 66745.1], ["03-31 12:00", 66745.1, 66891.8, 65938.0, 66099.3], ["03-31 13:00", 66099.3, 66442.0, 66067.0, 66329.4], ["03-31 14:00", 66329.4, 66850.0, 66205.0, 66652.4], ["03-31 15:00", 66652.4, 66909.3, 66480.0, 66623.8], ["03-31 16:00", 66623.8, 67375.0, 66623.8, 67255.6], ["03-31 17:00", 67255.6, 67765.8, 66374.4, 66555.9], ["03-31 18:00", 66556.0, 67262.2, 66555.9, 66700.0], ["03-31 19:00", 66700.0, 67985.5, 66695.9, 67632.6], ["03-31 20:00", 67632.6, 68600.0, 67357.1, 67493.9], ["03-31 21:00", 67493.8, 67929.7, 67488.0, 67814.6], ["03-31 22:00", 67814.5, 67996.0, 67671.3, 67803.0], ["03-31 23:00", 67803.0, 68234.0, 67794.8, 68227.2], ["04-01 00:00", 68227.3, 68382.9, 67840.4, 68234.6], ["04-01 01:00", 68234.7, 68306.9, 67919.5, 68141.6], ["04-01 02:00", 68141.7, 68332.6, 68050.0, 68241.5], ["04-01 03:00", 68241.4, 68305.1, 67808.1, 68288.0], ["04-01 04:00", 68288.0, 68330.0, 67707.5, 67746.4], ["04-01 05:00", 67746.4, 67881.2, 67534.9, 67623.8], ["04-01 06:00", 67623.9, 68214.5, 67623.9, 68134.0], ["04-01 07:00", 68134.0, 68450.0, 67965.0, 68272.3], ["04-01 08:00", 68272.3, 68732.5, 68114.5, 68418.2], ["04-01 09:00", 68418.3, 69220.0, 68418.2, 69069.1], ["04-01 10:00", 69069.1, 69288.0, 68631.1, 68651.9], ["04-01 11:00", 68651.9, 68821.5, 68425.5, 68630.8], ["04-01 12:00", 68630.9, 68702.3, 68360.0, 68608.4], ["04-01 13:00", 68608.4, 68632.1, 68370.1, 68545.1], ["04-01 14:00", 68545.2, 68702.3, 68471.5, 68669.9], ["04-01 15:00", 68670.0, 68773.9, 68220.9, 68363.8], ["04-01 16:00", 68364.1, 68650.0, 67883.7, 68091.4]],
        "klines_15m": [["03-31 18:45", 66906.5, 67019.1, 66666.5, 66700.0], ["03-31 19:00", 66700.0, 66970.4, 66695.9, 66893.2], ["03-31 19:15", 66893.1, 67165.5, 66881.5, 67056.5], ["03-31 19:30", 67056.4, 67985.5, 66916.6, 67742.0], ["03-31 19:45", 67742.1, 67888.0, 67457.0, 67632.6], ["03-31 20:00", 67632.6, 68532.7, 67532.8, 68432.9], ["03-31 20:15", 68432.8, 68600.0, 67951.2, 68002.3], ["03-31 20:30", 68002.4, 68091.9, 67573.9, 67683.7], ["03-31 20:45", 67683.6, 67749.0, 67357.1, 67493.9], ["03-31 21:00", 67493.8, 67764.9, 67488.0, 67739.7], ["03-31 21:15", 67739.7, 67929.7, 67594.4, 67744.9], ["03-31 21:30", 67744.9, 67855.4, 67601.9, 67789.9], ["03-31 21:45", 67789.9, 67912.8, 67700.4, 67814.6], ["03-31 22:00", 67814.5, 67985.8, 67802.0, 67952.5], ["03-31 22:15", 67952.6, 67996.0, 67810.5, 67840.3], ["03-31 22:30", 67840.4, 67901.0, 67671.3, 67800.0], ["03-31 22:45", 67799.9, 67934.9, 67694.0, 67803.0], ["03-31 23:00", 67803.0, 68177.2, 67794.8, 68109.6], ["03-31 23:15", 68109.6, 68135.6, 67902.4, 67967.3], ["03-31 23:30", 67967.2, 68099.1, 67911.1, 68017.1], ["03-31 23:45", 68017.1, 68234.0, 67985.0, 68227.2], ["04-01 00:00", 68227.3, 68227.3, 67911.2, 67977.3], ["04-01 00:15", 67977.3, 68030.0, 67840.4, 67995.9], ["04-01 00:30", 67995.9, 68138.0, 67991.7, 68130.0], ["04-01 00:45", 68130.1, 68382.9, 68119.0, 68234.6], ["04-01 01:00", 68234.7, 68306.9, 68013.4, 68172.8], ["04-01 01:15", 68172.8, 68254.4, 68057.4, 68080.0], ["04-01 01:30", 68080.1, 68214.9, 67919.5, 68140.0], ["04-01 01:45", 68140.1, 68183.4, 68057.1, 68141.6], ["04-01 02:00", 68141.7, 68250.0, 68050.0, 68183.7], ["04-01 02:15", 68183.6, 68332.6, 68141.0, 68224.3], ["04-01 02:30", 68224.2, 68332.0, 68200.0, 68271.3], ["04-01 02:45", 68271.4, 68297.1, 68173.1, 68241.5], ["04-01 03:00", 68241.4, 68241.5, 67975.3, 68004.7], ["04-01 03:15", 68004.6, 68177.9, 67863.3, 67964.3], ["04-01 03:30", 67964.3, 68031.7, 67808.1, 68031.2], ["04-01 03:45", 68031.2, 68305.1, 67989.8, 68288.0], ["04-01 04:00", 68288.0, 68330.0, 68106.3, 68223.7], ["04-01 04:15", 68223.8, 68223.8, 67976.5, 68006.4], ["04-01 04:30", 68006.3, 68054.7, 67755.1, 67915.8], ["04-01 04:45", 67915.9, 67920.0, 67707.5, 67746.4], ["04-01 05:00", 67746.4, 67873.1, 67662.2, 67803.3], ["04-01 05:15", 67803.3, 67881.2, 67556.1, 67603.6], ["04-01 05:30", 67603.7, 67691.3, 67534.9, 67617.7], ["04-01 05:45", 67617.7, 67705.8, 67558.7, 67623.8], ["04-01 06:00", 67623.9, 68086.2, 67623.9, 67957.5], ["04-01 13:00", 68608.4, 68632.1, 68370.1, 68545.1], ["04-01 14:00", 68545.2, 68702.3, 68471.5, 68669.9], ["04-01 15:00", 68670.0, 68773.9, 68220.9, 68363.8], ["04-01 16:00", 68364.1, 68650.0, 68128.0, 68183.2]]
    },

    "R15": {
        "data_15m": {"current_price": 66297.2, "ma5": 66360.45, "ma10": 66447.55, "ma30": 66524.59, "volume": 45400000, "volume_ma5": 67100000, "volume_ma10": 82000000, "net_long": -3700, "net_short": -9500, "futures_cvd": -19600000, "spot_cvd": 1100, "taker_ls_ratio": 2.117, "oi": 88600, "oi_delta": 58.9, "liquidations": {"long": 40700, "short": 132.6}},
        "data_1h": {"current_price": 66303.1, "ma5": 66538.12, "ma10": 66622.55, "ma30": 67838.45, "volume": 154100000, "volume_ma5": 303600000, "volume_ma10": 559800000, "net_long": 14800, "net_short": -4600, "futures_cvd": 20000000, "spot_cvd": -6100, "taker_ls_ratio": 2.117, "oi": 88500, "oi_delta": 144.8, "liquidations": {"long": 116900, "short": 331.8}},
        "data_4h": {"current_price": 66313.1, "ma5": 67197.34, "ma10": 67857.74, "ma30": 67243.08, "volume": 820600000, "volume_ma5": 1710000000, "volume_ma10": 1780000000, "net_long": -31100, "net_short": 12200, "futures_cvd": 20600000, "spot_cvd": -79500, "taker_ls_ratio": 2.117, "oi": 88000, "oi_delta": 649.7, "liquidations": {"long": 1200000, "short": 182600}},
        "actual": 'UP', "move": 1097,
        "run_time": "04-02 13:22",
        "whale_acct_ls": 0.9394,
        "api_whale_account": [['03-31 20:00', 0.8776], ['03-31 21:00', 0.8745], ['03-31 22:00', 0.8747], ['03-31 23:00', 0.8714], ['04-01 00:00', 0.8683], ['04-01 01:00', 0.8667], ['04-01 02:00', 0.8547], ['04-01 03:00', 0.8666], ['04-01 04:00', 0.8705], ['04-01 05:00', 0.8621], ['04-01 06:00', 0.8581], ['04-01 07:00', 0.8528], ['04-01 08:00', 0.8502], ['04-01 09:00', 0.8428], ['04-01 10:00', 0.842], ['04-01 11:00', 0.8442], ['04-01 12:00', 0.8419], ['04-01 13:00', 0.8513], ['04-01 14:00', 0.874], ['04-01 15:00', 0.8689], ['04-01 16:00', 0.8627], ['04-01 17:00', 0.8611], ['04-01 18:00', 0.8707], ['04-01 19:00', 0.8872], ['04-01 20:00', 0.8859], ['04-01 21:00', 0.8855], ['04-01 22:00', 0.8844], ['04-01 23:00', 0.8881], ['04-02 00:00', 0.8882], ['04-02 01:00', 0.8857]],
        "api_whale_position": [['03-31 20:00', 1.8305], ['03-31 21:00', 1.7747], ['03-31 22:00', 1.7412], ['03-31 23:00', 1.7108], ['04-01 00:00', 1.6824], ['04-01 01:00', 1.649], ['04-01 02:00', 1.635], ['04-01 03:00', 1.7064], ['04-01 04:00', 1.6911], ['04-01 05:00', 1.6476], ['04-01 06:00', 1.5934], ['04-01 07:00', 1.4814], ['04-01 08:00', 1.4085], ['04-01 09:00', 1.4576], ['04-01 10:00', 1.4637], ['04-01 11:00', 1.4576], ['04-01 12:00', 1.49], ['04-01 13:00', 1.4975], ['04-01 14:00', 1.5316], ['04-01 15:00', 1.5202], ['04-01 16:00', 1.5164], ['04-01 17:00', 1.5006], ['04-01 18:00', 1.5063], ['04-01 19:00', 1.5733], ['04-01 20:00', 1.5867], ['04-01 21:00', 1.5961], ['04-01 22:00', 1.6035], ['04-01 23:00', 1.6089], ['04-02 00:00', 1.6254], ['04-02 01:00', 1.6406]],
        "api_open_interest": [['03-31 20:00', 89165.95], ['03-31 21:00', 89005.65], ['03-31 22:00', 88746.48], ['03-31 23:00', 89128.25], ['04-01 00:00', 89212.45], ['04-01 01:00', 89555.26], ['04-01 02:00', 90026.03], ['04-01 03:00', 89978.67], ['04-01 04:00', 90147.71], ['04-01 05:00', 90562.41], ['04-01 06:00', 90503.71], ['04-01 07:00', 90916.1], ['04-01 08:00', 91248.89], ['04-01 09:00', 90807.26], ['04-01 10:00', 91215.04], ['04-01 11:00', 91225.25], ['04-01 12:00', 91252.05], ['04-01 13:00', 90900.72], ['04-01 14:00', 90512.38], ['04-01 15:00', 90383.74], ['04-01 16:00', 90660.0], ['04-01 17:00', 90588.67], ['04-01 18:00', 90313.76], ['04-01 19:00', 89938.96], ['04-01 20:00', 89762.35], ['04-01 21:00', 89610.66], ['04-01 22:00', 89270.46], ['04-01 23:00', 89309.85], ['04-02 00:00', 89176.97], ['04-02 01:00', 89056.04]],
        "api_funding_rate": [['03-30 00:00', 3e-06, 65973.4], ['03-30 08:00', 4.92e-06, 67596.7], ['03-30 16:00', 7.58e-06, 67595.59], ['03-31 00:00', 1.16e-06, 66764.4], ['03-31 08:00', -1.921e-05, 67343.9], ['03-31 16:00', -2.763e-05, 66700.0], ['04-01 00:00', -3.449e-05, 68243.3], ['04-01 08:00', -4.61e-06, 68668.6], ['04-01 16:00', 5.77e-06, 68876.82], ['04-02 00:00', 3.521e-05, 68086.5]],
        "klines_4h": [["03-31 23:00", 67803.0, 68382.9, 67794.8, 68241.5], ["04-01 03:00", 68241.4, 68330.0, 67534.9, 68134.0], ["04-01 07:00", 68134.0, 69288.0, 67965.0, 68651.9], ["04-01 11:00", 68651.9, 68821.5, 68360.0, 68669.9], ["04-01 15:00", 68670.0, 68938.8, 67883.7, 68877.0], ["04-01 19:00", 68876.9, 69142.6, 67900.4, 68143.8], ["04-01 23:00", 68143.7, 68510.6, 67927.0, 68086.5], ["04-02 03:00", 68086.4, 68639.1, 66455.9, 66538.4], ["04-02 07:00", 66538.4, 66898.5, 66171.8, 66887.9], ["04-02 11:00", 66887.8, 66887.9, 66065.1, 66180.6]],
        "klines_1h": [["04-01 08:00", 68272.3, 68732.5, 68114.5, 68418.2], ["04-01 09:00", 68418.3, 69220.0, 68418.2, 69069.1], ["04-01 10:00", 69069.1, 69288.0, 68631.1, 68651.9], ["04-01 11:00", 68651.9, 68821.5, 68425.5, 68630.8], ["04-01 12:00", 68630.9, 68702.3, 68360.0, 68608.4], ["04-01 13:00", 68608.4, 68632.1, 68370.1, 68545.1], ["04-01 14:00", 68545.2, 68702.3, 68471.5, 68669.9], ["04-01 15:00", 68670.0, 68773.9, 68220.9, 68363.8], ["04-01 16:00", 68364.1, 68650.0, 67883.7, 68091.4], ["04-01 17:00", 68091.4, 68657.1, 68020.0, 68559.1], ["04-01 18:00", 68559.2, 68938.8, 68380.3, 68877.0], ["04-01 19:00", 68876.9, 68961.6, 68570.0, 68781.1], ["04-01 20:00", 68781.1, 69142.6, 68212.1, 68239.7], ["04-01 21:00", 68239.7, 68313.8, 67900.4, 68054.2], ["04-01 22:00", 68054.2, 68269.9, 68000.0, 68143.8], ["04-01 23:00", 68143.7, 68217.8, 67927.0, 68159.8], ["04-02 00:00", 68159.7, 68510.6, 68136.5, 68324.7], ["04-02 01:00", 68324.8, 68324.8, 68032.9, 68088.4], ["04-02 02:00", 68088.5, 68220.9, 67952.2, 68086.5], ["04-02 03:00", 68086.4, 68639.1, 68013.3, 68565.1], ["04-02 04:00", 68565.2, 68565.2, 67000.3, 67316.4], ["04-02 05:00", 67316.4, 67316.4, 66590.0, 66821.6], ["04-02 06:00", 66821.6, 66931.9, 66455.9, 66538.4], ["04-02 07:00", 66538.4, 66617.7, 66171.8, 66300.2], ["04-02 08:00", 66300.2, 66628.8, 66270.0, 66558.2], ["04-02 09:00", 66558.2, 66798.9, 66506.4, 66652.9], ["04-02 10:00", 66653.0, 66898.5, 66521.4, 66887.9], ["04-02 11:00", 66887.8, 66887.9, 66372.9, 66418.2], ["04-02 12:00", 66418.1, 66487.7, 66256.0, 66428.6], ["04-02 13:00", 66428.7, 66471.9, 66188.1, 66424.0]],
        "klines_15m": [["04-02 01:00", 68324.8, 68324.8, 68104.6, 68184.2], ["04-02 01:15", 68184.2, 68230.0, 68032.9, 68149.9], ["04-02 01:30", 68149.9, 68284.2, 68101.6, 68209.4], ["04-02 01:45", 68209.3, 68227.9, 68040.2, 68088.4], ["04-02 02:00", 68088.5, 68220.9, 68088.5, 68162.3], ["04-02 02:15", 68162.4, 68162.4, 68050.0, 68088.3], ["04-02 02:30", 68088.3, 68146.0, 67952.2, 68072.3], ["04-02 02:45", 68072.3, 68142.2, 68024.1, 68086.5], ["04-02 03:00", 68086.4, 68199.6, 68013.3, 68177.3], ["04-02 03:15", 68177.3, 68244.8, 68100.0, 68179.1], ["04-02 03:30", 68179.0, 68494.4, 68166.5, 68494.3], ["04-02 03:45", 68494.3, 68639.1, 68391.6, 68565.1], ["04-02 04:00", 68565.2, 68565.2, 67598.0, 68105.3], ["04-02 04:15", 68105.4, 68109.1, 67223.0, 67538.9], ["04-02 04:30", 67538.9, 67545.7, 67090.0, 67135.9], ["04-02 04:45", 67135.9, 67364.7, 67000.3, 67316.4], ["04-02 05:00", 67316.4, 67316.4, 66807.6, 66824.9], ["04-02 05:15", 66824.9, 66982.2, 66729.5, 66863.7], ["04-02 05:30", 66863.8, 67016.5, 66590.0, 66677.4], ["04-02 05:45", 66677.4, 66912.4, 66656.3, 66821.6], ["04-02 06:00", 66821.6, 66931.9, 66702.6, 66719.6], ["04-02 06:15", 66719.6, 66865.7, 66601.5, 66831.6], ["04-02 06:30", 66831.6, 66850.0, 66455.9, 66571.4], ["04-02 06:45", 66571.4, 66617.0, 66464.5, 66538.4], ["04-02 07:00", 66538.4, 66617.7, 66469.9, 66501.2], ["04-02 07:15", 66501.2, 66592.3, 66337.0, 66386.8], ["04-02 07:30", 66386.9, 66420.0, 66171.8, 66255.2], ["04-02 07:45", 66255.2, 66363.9, 66234.9, 66300.2], ["04-02 08:00", 66300.2, 66478.2, 66270.0, 66349.8], ["04-02 08:15", 66349.9, 66450.0, 66315.1, 66449.9], ["04-02 08:30", 66449.9, 66593.4, 66362.2, 66553.6], ["04-02 08:45", 66553.7, 66628.8, 66440.0, 66558.2], ["04-02 09:00", 66558.2, 66591.9, 66530.0, 66547.0], ["04-02 09:15", 66547.0, 66798.9, 66540.0, 66612.7], ["04-02 09:30", 66612.6, 66666.5, 66506.4, 66519.9], ["04-02 09:45", 66519.9, 66661.5, 66519.9, 66652.9], ["04-02 10:00", 66653.0, 66681.8, 66521.4, 66545.3], ["04-02 10:15", 66545.4, 66680.3, 66545.3, 66647.2], ["04-02 10:30", 66647.2, 66860.0, 66644.1, 66824.2], ["04-02 10:45", 66824.2, 66898.5, 66821.3, 66887.9], ["04-02 11:00", 66887.8, 66887.9, 66681.3, 66743.9], ["04-02 11:15", 66743.8, 66749.8, 66555.7, 66645.3], ["04-02 11:30", 66645.2, 66705.2, 66462.4, 66475.6], ["04-02 11:45", 66475.7, 66529.7, 66372.9, 66418.2], ["04-02 12:00", 66418.1, 66454.5, 66256.0, 66394.4], ["04-02 12:15", 66394.4, 66487.0, 66330.6, 66444.1], ["04-02 12:30", 66444.1, 66487.7, 66360.8, 66400.1], ["04-02 12:45", 66400.0, 66441.4, 66332.0, 66428.6], ["04-02 13:00", 66428.7, 66471.9, 66188.1, 66231.9], ["04-02 13:15", 66231.9, 66354.9, 66191.7, 66337.0]]
    },

    "R16": {
        "data_15m": {"current_price": 66080.1, "ma5": 66140.3, "ma10": 66252.42, "ma30": 66446.34, "volume": 39400000, "volume_ma5": 129600000, "volume_ma10": 104000000, "net_long": -4100, "net_short": -8600, "futures_cvd": -23300000, "spot_cvd": 484.0, "taker_ls_ratio": 2.148, "oi": 89000, "oi_delta": 40.1, "liquidations": {"long": 396.7, "short": 10700}},
        "data_1h": {"current_price": 66079.9, "ma5": 66306.27, "ma10": 66446.89, "ma30": 67668.26, "volume": 561400000, "volume_ma5": 375300000, "volume_ma10": 399700000, "net_long": 14300, "net_short": -5500, "futures_cvd": 17600000, "spot_cvd": -6500, "taker_ls_ratio": 2.148, "oi": 88700, "oi_delta": 336.0, "liquidations": {"long": 247900, "short": 40200}},
        "data_4h": {"current_price": 66054.9, "ma5": 66751.73, "ma10": 67625.2, "ma30": 67207.53, "volume": 562600000, "volume_ma5": 1550000000, "volume_ma10": 1770000000, "net_long": 31200, "net_short": 13000, "futures_cvd": 19300000, "spot_cvd": -79000, "taker_ls_ratio": 2.148, "oi": 88700, "oi_delta": 346.0, "liquidations": {"long": 247900, "short": 40200}},
        "actual": 'UP', "move": 747,
        "run_time": "04-02 15:52",
        "whale_acct_ls": 0.9471,
        "api_whale_account": [['04-01 02:00', 0.8547], ['04-01 03:00', 0.8666], ['04-01 04:00', 0.8705], ['04-01 05:00', 0.8621], ['04-01 06:00', 0.8581], ['04-01 07:00', 0.8528], ['04-01 08:00', 0.8502], ['04-01 09:00', 0.8428], ['04-01 10:00', 0.842], ['04-01 11:00', 0.8442], ['04-01 12:00', 0.8419], ['04-01 13:00', 0.8513], ['04-01 14:00', 0.874], ['04-01 15:00', 0.8689], ['04-01 16:00', 0.8627], ['04-01 17:00', 0.8611], ['04-01 18:00', 0.8707], ['04-01 19:00', 0.8872], ['04-01 20:00', 0.8859], ['04-01 21:00', 0.8855], ['04-01 22:00', 0.8844], ['04-01 23:00', 0.8881], ['04-02 00:00', 0.8882], ['04-02 01:00', 0.8857], ['04-02 02:00', 0.8798], ['04-02 03:00', 0.8841], ['04-02 04:00', 0.8938], ['04-02 05:00', 0.9113], ['04-02 06:00', 0.9279], ['04-02 07:00', 0.934]],
        "api_whale_position": [['04-01 02:00', 1.635], ['04-01 03:00', 1.7064], ['04-01 04:00', 1.6911], ['04-01 05:00', 1.6476], ['04-01 06:00', 1.5934], ['04-01 07:00', 1.4814], ['04-01 08:00', 1.4085], ['04-01 09:00', 1.4576], ['04-01 10:00', 1.4637], ['04-01 11:00', 1.4576], ['04-01 12:00', 1.49], ['04-01 13:00', 1.4975], ['04-01 14:00', 1.5316], ['04-01 15:00', 1.5202], ['04-01 16:00', 1.5164], ['04-01 17:00', 1.5006], ['04-01 18:00', 1.5063], ['04-01 19:00', 1.5733], ['04-01 20:00', 1.5867], ['04-01 21:00', 1.5961], ['04-01 22:00', 1.6035], ['04-01 23:00', 1.6089], ['04-02 00:00', 1.6254], ['04-02 01:00', 1.6406], ['04-02 02:00', 1.8019], ['04-02 03:00', 1.8994], ['04-02 04:00', 1.9851], ['04-02 05:00', 2.0864], ['04-02 06:00', 2.1786], ['04-02 07:00', 2.2062]],
        "api_open_interest": [['04-01 02:00', 90026.03], ['04-01 03:00', 89978.67], ['04-01 04:00', 90147.71], ['04-01 05:00', 90562.41], ['04-01 06:00', 90503.71], ['04-01 07:00', 90916.1], ['04-01 08:00', 91248.89], ['04-01 09:00', 90807.26], ['04-01 10:00', 91215.04], ['04-01 11:00', 91225.25], ['04-01 12:00', 91252.05], ['04-01 13:00', 90900.72], ['04-01 14:00', 90512.38], ['04-01 15:00', 90383.74], ['04-01 16:00', 90660.0], ['04-01 17:00', 90588.67], ['04-01 18:00', 90313.76], ['04-01 19:00', 89938.96], ['04-01 20:00', 89762.35], ['04-01 21:00', 89610.66], ['04-01 22:00', 89270.46], ['04-01 23:00', 89309.85], ['04-02 00:00', 89176.97], ['04-02 01:00', 89056.04], ['04-02 02:00', 88403.32], ['04-02 03:00', 88327.27], ['04-02 04:00', 88498.17], ['04-02 05:00', 88597.96], ['04-02 06:00', 88211.37], ['04-02 07:00', 88012.93]],
        "api_funding_rate": [['03-30 00:00', 3e-06, 65973.4], ['03-30 08:00', 4.92e-06, 67596.7], ['03-30 16:00', 7.58e-06, 67595.59], ['03-31 00:00', 1.16e-06, 66764.4], ['03-31 08:00', -1.921e-05, 67343.9], ['03-31 16:00', -2.763e-05, 66700.0], ['04-01 00:00', -3.449e-05, 68243.3], ['04-01 08:00', -4.61e-06, 68668.6], ['04-01 16:00', 5.77e-06, 68876.82], ['04-02 00:00', 3.521e-05, 68086.5]],
        "klines_4h": [["04-01 03:00", 68241.4, 68330.0, 67534.9, 68134.0], ["04-01 07:00", 68134.0, 69288.0, 67965.0, 68651.9], ["04-01 11:00", 68651.9, 68821.5, 68360.0, 68669.9], ["04-01 15:00", 68670.0, 68938.8, 67883.7, 68877.0], ["04-01 19:00", 68876.9, 69142.6, 67900.4, 68143.8], ["04-01 23:00", 68143.7, 68510.6, 67927.0, 68086.5], ["04-02 03:00", 68086.4, 68639.1, 66455.9, 66538.4], ["04-02 07:00", 66538.4, 66898.5, 66171.8, 66887.9], ["04-02 11:00", 66887.8, 66887.9, 66065.1, 66180.6], ["04-02 15:00", 66180.6, 67080.0, 65676.1, 66810.6]],
        "klines_1h": [["04-01 10:00", 69069.1, 69288.0, 68631.1, 68651.9], ["04-01 11:00", 68651.9, 68821.5, 68425.5, 68630.8], ["04-01 12:00", 68630.9, 68702.3, 68360.0, 68608.4], ["04-01 13:00", 68608.4, 68632.1, 68370.1, 68545.1], ["04-01 14:00", 68545.2, 68702.3, 68471.5, 68669.9], ["04-01 15:00", 68670.0, 68773.9, 68220.9, 68363.8], ["04-01 16:00", 68364.1, 68650.0, 67883.7, 68091.4], ["04-01 17:00", 68091.4, 68657.1, 68020.0, 68559.1], ["04-01 18:00", 68559.2, 68938.8, 68380.3, 68877.0], ["04-01 19:00", 68876.9, 68961.6, 68570.0, 68781.1], ["04-01 20:00", 68781.1, 69142.6, 68212.1, 68239.7], ["04-01 21:00", 68239.7, 68313.8, 67900.4, 68054.2], ["04-01 22:00", 68054.2, 68269.9, 68000.0, 68143.8], ["04-01 23:00", 68143.7, 68217.8, 67927.0, 68159.8], ["04-02 00:00", 68159.7, 68510.6, 68136.5, 68324.7], ["04-02 01:00", 68324.8, 68324.8, 68032.9, 68088.4], ["04-02 02:00", 68088.5, 68220.9, 67952.2, 68086.5], ["04-02 03:00", 68086.4, 68639.1, 68013.3, 68565.1], ["04-02 04:00", 68565.2, 68565.2, 67000.3, 67316.4], ["04-02 05:00", 67316.4, 67316.4, 66590.0, 66821.6], ["04-02 06:00", 66821.6, 66931.9, 66455.9, 66538.4], ["04-02 07:00", 66538.4, 66617.7, 66171.8, 66300.2], ["04-02 08:00", 66300.2, 66628.8, 66270.0, 66558.2], ["04-02 09:00", 66558.2, 66798.9, 66506.4, 66652.9], ["04-02 10:00", 66653.0, 66898.5, 66521.4, 66887.9], ["04-02 11:00", 66887.8, 66887.9, 66372.9, 66418.2], ["04-02 12:00", 66418.1, 66487.7, 66256.0, 66428.6], ["04-02 13:00", 66428.7, 66471.9, 66188.1, 66424.0], ["04-02 14:00", 66424.1, 66449.7, 66065.1, 66180.6], ["04-02 15:00", 66180.6, 66215.2, 65919.1, 66014.2]],
        "klines_15m": [["04-02 03:00", 68086.4, 68199.6, 68013.3, 68177.3], ["04-02 03:15", 68177.3, 68244.8, 68100.0, 68179.1], ["04-02 03:30", 68179.0, 68494.4, 68166.5, 68494.3], ["04-02 03:45", 68494.3, 68639.1, 68391.6, 68565.1], ["04-02 04:00", 68565.2, 68565.2, 67598.0, 68105.3], ["04-02 04:15", 68105.4, 68109.1, 67223.0, 67538.9], ["04-02 04:30", 67538.9, 67545.7, 67090.0, 67135.9], ["04-02 04:45", 67135.9, 67364.7, 67000.3, 67316.4], ["04-02 05:00", 67316.4, 67316.4, 66807.6, 66824.9], ["04-02 05:15", 66824.9, 66982.2, 66729.5, 66863.7], ["04-02 05:30", 66863.8, 67016.5, 66590.0, 66677.4], ["04-02 05:45", 66677.4, 66912.4, 66656.3, 66821.6], ["04-02 06:00", 66821.6, 66931.9, 66702.6, 66719.6], ["04-02 06:15", 66719.6, 66865.7, 66601.5, 66831.6], ["04-02 06:30", 66831.6, 66850.0, 66455.9, 66571.4], ["04-02 06:45", 66571.4, 66617.0, 66464.5, 66538.4], ["04-02 07:00", 66538.4, 66617.7, 66469.9, 66501.2], ["04-02 07:15", 66501.2, 66592.3, 66337.0, 66386.8], ["04-02 07:30", 66386.9, 66420.0, 66171.8, 66255.2], ["04-02 07:45", 66255.2, 66363.9, 66234.9, 66300.2], ["04-02 08:00", 66300.2, 66478.2, 66270.0, 66349.8], ["04-02 08:15", 66349.9, 66450.0, 66315.1, 66449.9], ["04-02 08:30", 66449.9, 66593.4, 66362.2, 66553.6], ["04-02 08:45", 66553.7, 66628.8, 66440.0, 66558.2], ["04-02 09:00", 66558.2, 66591.9, 66530.0, 66547.0], ["04-02 09:15", 66547.0, 66798.9, 66540.0, 66612.7], ["04-02 09:30", 66612.6, 66666.5, 66506.4, 66519.9], ["04-02 09:45", 66519.9, 66661.5, 66519.9, 66652.9], ["04-02 10:00", 66653.0, 66681.8, 66521.4, 66545.3], ["04-02 10:15", 66545.4, 66680.3, 66545.3, 66647.2], ["04-02 10:30", 66647.2, 66860.0, 66644.1, 66824.2], ["04-02 10:45", 66824.2, 66898.5, 66821.3, 66887.9], ["04-02 11:00", 66887.8, 66887.9, 66681.3, 66743.9], ["04-02 11:15", 66743.8, 66749.8, 66555.7, 66645.3], ["04-02 11:30", 66645.2, 66705.2, 66462.4, 66475.6], ["04-02 11:45", 66475.7, 66529.7, 66372.9, 66418.2], ["04-02 12:00", 66418.1, 66454.5, 66256.0, 66394.4], ["04-02 12:15", 66394.4, 66487.0, 66330.6, 66444.1], ["04-02 12:30", 66444.1, 66487.7, 66360.8, 66400.1], ["04-02 12:45", 66400.0, 66441.4, 66332.0, 66428.6], ["04-02 13:00", 66428.7, 66471.9, 66188.1, 66231.9], ["04-02 13:15", 66231.9, 66354.9, 66191.7, 66337.0], ["04-02 13:30", 66337.1, 66464.5, 66322.9, 66440.8], ["04-02 14:00", 66424.1, 66449.7, 66223.0, 66253.4], ["04-02 14:15", 66253.3, 66438.0, 66065.1, 66415.5], ["04-02 14:30", 66415.5, 66447.4, 66283.0, 66297.9], ["04-02 14:45", 66297.8, 66360.0, 66138.2, 66180.6], ["04-02 15:15", 66139.3, 66150.6, 65919.1, 66115.3], ["04-02 15:30", 66115.4, 66186.5, 66069.0, 66179.8], ["04-02 15:45", 66179.8, 66209.3, 65962.2, 66014.2]]
    },

    # ═══════════════════════════════════════════════════════════════
    # R17 — KAPSAMLI KAYIT
    # ═══════════════════════════════════════════════════════════════
    # GİRİŞ: SHORT $66,776.8 @ 04-03 13:23 | NORMAL BOYUT | YÜKSEK güven
    # SONUÇ: DOWN -$24 → GİRİŞ_KÖTÜ (yön doğru, zamanlama kötü)
    # MFE4h: +$298 (dip $66,478.5 @ 16:45) | MAE4h: -$573 (tepe $67,350.0 @ 15:30)
    # MAE/MFE: 1.92 | 15m mum: 17 adet (13:15→17:15)
    # ───────────────────────────────────────────────────────────────
    # SCORECARD ÇIKTISI:
    #   15m = -1.3285 (K6_LIQ -0.60, K3 -0.34, K4_CVD -0.32)
    #   1h  = -1.0676 (K3 -0.93, K6_LIQ -0.48, K4_CVD -0.32, K8_LS +0.60, K1_MA +0.19)
    #   4h  = -1.1134 (K12_SPOT -0.74, K3 -0.31, K1_MA -0.20, K4_CVD -0.20, K6_LIQ +0.33)
    #   V-RISK: tetiklenmedi (tüm karşı-sinyal kaynakları aynı yön)
    # ───────────────────────────────────────────────────────────────
    # VERİ NOTU: 4h ma30=0 — Gemini chart'ta MA30 çizgisi görünmemiş.
    #   Kapanış Gemini'da ma30=67268.27 (gerçek değer). Tahmini ~67130 (R13-R16 trendi).
    #   Etki: 4h K1_MA -0.20→-0.27 (fark 0.07). Yön/güven/boyut DEĞİŞMİYOR.
    #   İlk kez oluştu (R2-R16 hepsi normal). Gelecek runlarda Gemini chart zoom kontrol.
    # ───────────────────────────────────────────────────────────────
    # GİRİŞ HEATMAP (04-03 13:23):
    #   15m@33: fiyat ~$66,792. Üstte 67,200-67,400 yoğun likidite duvarı.
    #   15m@106: fiyat ~$66,750. 66,240 alt, 67,200-67,400 üst kümeler.
    #   1h@54: fiyat ~$66,775. 68,000+ ağır direnç. 66,000 destek.
    #   1h@234: fiyat ~$66,760. 68,000-68,500 kalın mor çizgiler. 65,676 dip.
    #   4h@52: fiyat ~$66,787. 69,000-71,000 ağır katmanlar.
    #   4h@464: fiyat ~$66,754. 68,000-69,000 yoğun. 65,000 altı boş.
    # ───────────────────────────────────────────────────────────────
    # KAPANIŞ HEATMAP (04-03 17:16-17:17):
    #   15m@33: fiyat ~$66,756. $67,370 spike izi. 66,282 alt.
    #   15m@106: fiyat ~$66,725. 66,400-66,600 destek kümesi (çalıştı).
    #     67,200-67,400 direnç (spike bölgesi). Kırmızı/mor yoğun.
    #   1h@54: fiyat ~$66,757. 65,712-69,171 range.
    #   1h@234: fiyat ~$66,738. 68,000-68,500 kalın mor direnç.
    #   4h@52: fiyat ~$66,755. Makro yapı değişmemiş.
    #   4h@464: fiyat ~$66,739. 64,918-71,408 geniş range.
    # ───────────────────────────────────────────────────────────────
    # GİRİŞ GEMİNİ (04-03 ~13:23):
    #   15m: p=66776.8 ma5=66809.77 ma10=66891.02 ma30=66745.14
    #     vol=18M vol_ma5=37.4M vol_ma10=55.5M net_long=-4600 net_short=-3800
    #     cvd=-22.8M spot=-210.6 funding=-0.0005 liq_L=801.5 liq_S=0
    #     oi=90400 oi_delta=-18.7 ls=1.803
    #   1h: p=66776.8 ma5=66862.30 ma10=66711.88 ma30=66684.05
    #     vol=52.2M vol_ma5=221.9M vol_ma10=248.7M net_long=375 net_short=-2900
    #     cvd=-12.6M spot=-8400 funding=-0.0005 liq_L=3500 liq_S=400.7
    #     oi=90300 oi_delta=70.8 ls=1.803
    #   4h: p=66777.4 ma5=66829.67 ma10=67254.38 ma30=0
    #     vol=556.6M vol_ma5=1050M vol_ma10=1600M net_long=-29100 net_short=17200
    #     cvd=16.5M spot=-81100 funding=-0.0005 liq_L=50600 liq_S=177200
    #     oi=90200 oi_delta=219.6 ls=1.803
    # ───────────────────────────────────────────────────────────────
    # KAPANIŞ GEMİNİ (04-03 ~17:17):
    #   15m: p=66730.1 ma5=66670.55 ma10=66759.66 ma30=66849.49
    #     vol=6.1M vol_ma5=80.7M vol_ma10=112.3M net_long=-5300 net_short=-4400
    #     cvd=-20M spot=-187.9 funding=+0.0005 liq_L=0 liq_S=0
    #     oi=90500 oi_delta=4.72 ls=1.802
    #   1h: p=66726.1 ma5=66777.30 ma10=66799.61 ma30=66703.78
    #     vol=106.9M vol_ma5=289.7M vol_ma10=273.6M net_long=5900 net_short=4700
    #     cvd=-14.5M spot=-6400 funding=+0.0005 liq_L=2100 liq_S=21300
    #     oi=90500 oi_delta=30.7 ls=1.802
    #   4h: p=66710.9 ma5=66824.45 ma10=66749.18 ma30=67268.27
    #     vol=1120M vol_ma5=931.5M vol_ma10=1660M net_long=-29400 net_short=17000
    #     cvd=16.9M spot=-80800 funding=+0.0005 liq_L=206600 liq_S=126600
    #     oi=90100 oi_delta=431.7 ls=1.802
    # ───────────────────────────────────────────────────────────────
    # GİRİŞ API GÖZLEM (6. set — 04-03 ~13:00):
    #   Whale: 0.4700 long (düşüş trendi: ATH 0.4941 @ R16 bounce'dan)
    #   Retail: 0.6432 long (düşüş trendi: ATH 0.6870 @ R16 bounce'dan)
    #   Gap: ~0.17 (geniş)
    #   Funding: son ödeme -0.000006 @ 04-03 11:00
    #   OI: ~90,200
    # ───────────────────────────────────────────────────────────────
    # KAPANIŞ API GÖZLEM (7. set — 04-03 ~17:00):
    #   Whale: 0.4711 long (girişten minimal değişim +0.0011)
    #   Retail: 0.6418 long (girişten hafif düşüş -0.0014, 16:00'da 0.6382 dip)
    #   Gap: ~0.17 (değişmedi)
    #   Funding: değişmedi (sonraki ödeme henüz olmadı)
    #   OI: 90,463 (girişten +263 hafif artış)
    # ───────────────────────────────────────────────────────────────
    # POST-MORTEM:
    #   15:30'da $67,350 spike (+$573 MAE) — heatmap'te 67,200-67,400 likidite
    #   duvarı görülüyordu. Market maker likiditeyi süpürdü, sonra düşüş geldi.
    #   Scorecard yönü doğru buldu ama "süpürme öncesi gir" zamanlaması yok.
    #   $67,300'den girilseydi: MFE=$822, MAE=$50 → BAŞARILI olurdu.
    #   Bu R5 (ratio 6.68) ve R10 (ratio 1.97) ile aynı pattern: yön doğru,
    #   giriş zamanlaması heatmap bilgisiyle iyileştirilebilir.
    # ═══════════════════════════════════════════════════════════════

    "R17": {
        "data_15m": {"current_price": 66776.8, "ma5": 66809.77, "ma10": 66891.02, "ma30": 66745.14, "volume": 18000000, "volume_ma5": 37400000, "volume_ma10": 55500000, "net_long": -4600, "net_short": -3800, "futures_cvd": -22800000, "spot_cvd": -210.6, "taker_ls_ratio": 1.803, "oi": 90400, "oi_delta": -18.7, "liquidations": {"long": 801.5, "short": 0}},
        "data_1h": {"current_price": 66776.8, "ma5": 66862.3, "ma10": 66711.88, "ma30": 66684.05, "volume": 52200000, "volume_ma5": 221900000, "volume_ma10": 248700000, "net_long": 375.0, "net_short": -2900, "futures_cvd": -12600000, "spot_cvd": -8400, "taker_ls_ratio": 1.803, "oi": 90300, "oi_delta": 70.8, "liquidations": {"long": 3500, "short": 400.7}},
        "data_4h": {"current_price": 66777.4, "ma5": 66829.67, "ma10": 67254.38, "ma30": 0, "volume": 556600000, "volume_ma5": 1050000000, "volume_ma10": 1600000000, "net_long": -29100, "net_short": 17200, "futures_cvd": 16500000, "spot_cvd": -81100, "taker_ls_ratio": 1.803, "oi": 90200, "oi_delta": 219.6, "liquidations": {"long": 50600, "short": 177200}},
        "actual": 'BELIRSIZ', "move": None,
        "run_time": "04-03 13:23",
        "whale_acct_ls": 0.8868,
        "api_whale_account": [['04-02 00:00', 0.8882], ['04-02 01:00', 0.8857], ['04-02 02:00', 0.8798], ['04-02 03:00', 0.8841], ['04-02 04:00', 0.8938], ['04-02 05:00', 0.9113], ['04-02 06:00', 0.9279], ['04-02 07:00', 0.934], ['04-02 08:00', 0.9329], ['04-02 09:00', 0.9348], ['04-02 10:00', 0.9394], ['04-02 11:00', 0.9419], ['04-02 12:00', 0.9471], ['04-02 13:00', 0.9706], ['04-02 14:00', 0.9768], ['04-02 15:00', 0.9537], ['04-02 16:00', 0.9316], ['04-02 17:00', 0.9063], ['04-02 18:00', 0.8813], ['04-02 19:00', 0.8749], ['04-02 20:00', 0.8802], ['04-02 21:00', 0.8807], ['04-02 22:00', 0.88], ['04-02 23:00', 0.8826], ['04-03 00:00', 0.88], ['04-03 01:00', 0.8856], ['04-03 02:00', 0.8851], ['04-03 03:00', 0.8928], ['04-03 04:00', 0.9016], ['04-03 05:00', 0.9039]],
        "api_whale_position": [['04-02 00:00', 1.6254], ['04-02 01:00', 1.6406], ['04-02 02:00', 1.8019], ['04-02 03:00', 1.8994], ['04-02 04:00', 1.9851], ['04-02 05:00', 2.0864], ['04-02 06:00', 2.1786], ['04-02 07:00', 2.2062], ['04-02 08:00', 2.2175], ['04-02 09:00', 2.1888], ['04-02 10:00', 2.23], ['04-02 11:00', 2.2626], ['04-02 12:00', 2.2584], ['04-02 13:00', 2.2852], ['04-02 14:00', 2.3456], ['04-02 15:00', 2.2082], ['04-02 16:00', 2.1506], ['04-02 17:00', 2.0656], ['04-02 18:00', 1.9815], ['04-02 19:00', 1.9878], ['04-02 20:00', 1.9656], ['04-02 21:00', 1.9577], ['04-02 22:00', 1.9533], ['04-02 23:00', 1.9446], ['04-03 00:00', 1.9231], ['04-03 01:00', 1.9019], ['04-03 02:00', 1.896], ['04-03 03:00', 1.9283], ['04-03 04:00', 1.93], ['04-03 05:00', 1.9377]],
        "api_open_interest": [['04-02 00:00', 89176.97], ['04-02 01:00', 89056.04], ['04-02 02:00', 88403.32], ['04-02 03:00', 88327.27], ['04-02 04:00', 88498.17], ['04-02 05:00', 88597.96], ['04-02 06:00', 88211.37], ['04-02 07:00', 88012.93], ['04-02 08:00', 88010.92], ['04-02 09:00', 88389.57], ['04-02 10:00', 88518.74], ['04-02 11:00', 88727.73], ['04-02 12:00', 88721.21], ['04-02 13:00', 89113.05], ['04-02 14:00', 89821.35], ['04-02 15:00', 89858.13], ['04-02 16:00', 90567.53], ['04-02 17:00', 91244.66], ['04-02 18:00', 90813.61], ['04-02 19:00', 90353.51], ['04-02 20:00', 90256.23], ['04-02 21:00', 90142.26], ['04-02 22:00', 90149.0], ['04-02 23:00', 90167.25], ['04-03 00:00', 90119.34], ['04-03 01:00', 90456.75], ['04-03 02:00', 90492.64], ['04-03 03:00', 90701.42], ['04-03 04:00', 90854.84], ['04-03 05:00', 90898.03]],
        "api_funding_rate": [['03-31 00:00', 1.16e-06, 66764.4], ['03-31 08:00', -1.921e-05, 67343.9], ['03-31 16:00', -2.763e-05, 66700.0], ['04-01 00:00', -3.449e-05, 68243.3], ['04-01 08:00', -4.61e-06, 68668.6], ['04-01 16:00', 5.77e-06, 68876.82], ['04-02 00:00', 3.521e-05, 68086.5], ['04-02 08:00', 8.45e-06, 66888.21], ['04-02 16:00', -7.398e-05, 66819.54], ['04-03 00:00', -8.31e-06, 66869.74]],
        "klines_4h": [["04-01 23:00", 68143.7, 68510.6, 67927.0, 68086.5], ["04-02 03:00", 68086.4, 68639.1, 66455.9, 66538.4], ["04-02 07:00", 66538.4, 66898.5, 66171.8, 66887.9], ["04-02 11:00", 66887.8, 66887.9, 66065.1, 66180.6], ["04-02 15:00", 66180.6, 67080.0, 65676.1, 66810.6], ["04-02 19:00", 66810.6, 67400.0, 66550.0, 66943.2], ["04-02 23:00", 66943.2, 67078.9, 66681.3, 66868.5], ["04-03 03:00", 66868.6, 66976.2, 66240.0, 66550.0], ["04-03 07:00", 66550.1, 67233.3, 66375.1, 67008.8], ["04-03 11:00", 67008.8, 67258.0, 66644.0, 66983.4]],
        "klines_1h": [["04-02 08:00", 66300.2, 66628.8, 66270.0, 66558.2], ["04-02 09:00", 66558.2, 66798.9, 66506.4, 66652.9], ["04-02 10:00", 66653.0, 66898.5, 66521.4, 66887.9], ["04-02 11:00", 66887.8, 66887.9, 66372.9, 66418.2], ["04-02 12:00", 66418.1, 66487.7, 66256.0, 66428.6], ["04-02 13:00", 66428.7, 66471.9, 66188.1, 66424.0], ["04-02 14:00", 66424.1, 66449.7, 66065.1, 66180.6], ["04-02 15:00", 66180.6, 66215.2, 65919.1, 66014.2], ["04-02 16:00", 66014.3, 66250.0, 65676.1, 66227.3], ["04-02 17:00", 66227.3, 66873.8, 66123.0, 66765.8], ["04-02 18:00", 66822.3, 66960.7, 66596.2, 66810.6], ["04-02 19:00", 66810.6, 67234.4, 66707.6, 67050.1], ["04-02 20:00", 67050.0, 67400.0, 66622.4, 66641.4], ["04-02 21:00", 66641.4, 67044.8, 66550.0, 66941.6], ["04-02 22:00", 66941.7, 67082.9, 66827.8, 66943.2], ["04-02 23:00", 66943.2, 67078.9, 66755.6, 66906.3], ["04-03 00:00", 66906.4, 66993.4, 66681.3, 66910.7], ["04-03 01:00", 66910.7, 67008.5, 66782.0, 66954.0], ["04-03 02:00", 66954.0, 67070.2, 66820.6, 66868.5], ["04-03 03:00", 66868.6, 66976.2, 66671.0, 66761.8], ["04-03 04:00", 66761.8, 66881.3, 66450.0, 66599.0], ["04-03 05:00", 66599.1, 66726.7, 66240.0, 66504.6], ["04-03 06:00", 66504.6, 66698.5, 66461.0, 66550.0], ["04-03 07:00", 66550.1, 66666.0, 66468.0, 66578.8], ["04-03 08:00", 66578.8, 66789.6, 66375.1, 66574.9], ["04-03 09:00", 66574.9, 66770.0, 66523.2, 66762.0], ["04-03 10:00", 66762.1, 67233.3, 66716.4, 67008.8], ["04-03 11:00", 67008.8, 67258.0, 66864.1, 66935.0], ["04-03 12:00", 66935.1, 66976.0, 66714.3, 66828.9], ["04-03 13:00", 66828.9, 66871.9, 66644.0, 66845.3]],
        "klines_15m": [["04-03 01:00", 66910.7, 66990.0, 66864.0, 66869.5], ["04-03 01:15", 66869.6, 66965.9, 66782.0, 66875.6], ["04-03 01:30", 66875.7, 66975.0, 66875.7, 66947.1], ["04-03 01:45", 66947.2, 67008.5, 66885.0, 66954.0], ["04-03 02:00", 66954.0, 67070.2, 66892.3, 66919.2], ["04-03 02:15", 66919.2, 67001.3, 66893.4, 66906.3], ["04-03 02:30", 66906.2, 66930.5, 66852.4, 66852.8], ["04-03 02:45", 66852.8, 66874.1, 66820.6, 66868.5], ["04-03 03:00", 66868.6, 66976.2, 66745.0, 66839.9], ["04-03 03:15", 66839.9, 66936.4, 66763.9, 66793.9], ["04-03 03:30", 66794.0, 66884.1, 66733.8, 66773.0], ["04-03 03:45", 66773.0, 66773.1, 66671.0, 66761.8], ["04-03 04:00", 66761.8, 66808.5, 66696.3, 66797.2], ["04-03 04:15", 66797.3, 66868.8, 66707.0, 66834.9], ["04-03 04:30", 66834.8, 66881.3, 66450.0, 66540.5], ["04-03 04:45", 66540.6, 66600.2, 66457.6, 66599.0], ["04-03 05:00", 66599.1, 66599.1, 66375.0, 66479.6], ["04-03 05:15", 66479.6, 66726.7, 66413.3, 66424.9], ["04-03 05:30", 66424.9, 66485.7, 66240.0, 66309.1], ["04-03 05:45", 66309.1, 66517.2, 66282.0, 66504.6], ["04-03 06:00", 66504.6, 66640.3, 66461.0, 66623.9], ["04-03 06:15", 66623.9, 66698.5, 66572.1, 66602.1], ["04-03 06:30", 66602.2, 66677.7, 66492.6, 66565.7], ["04-03 06:45", 66565.8, 66608.0, 66515.3, 66550.0], ["04-03 07:00", 66550.1, 66625.3, 66525.0, 66603.9], ["04-03 07:15", 66603.9, 66666.0, 66505.6, 66505.6], ["04-03 07:30", 66505.7, 66578.1, 66468.0, 66548.9], ["04-03 07:45", 66548.8, 66648.4, 66533.0, 66578.8], ["04-03 08:00", 66578.8, 66641.0, 66554.1, 66554.1], ["04-03 08:15", 66554.2, 66561.6, 66375.1, 66549.1], ["04-03 08:30", 66549.0, 66789.6, 66549.0, 66740.1], ["04-03 08:45", 66740.1, 66740.1, 66478.8, 66574.9], ["04-03 09:00", 66574.9, 66635.9, 66523.2, 66635.9], ["04-03 09:15", 66635.9, 66665.8, 66567.1, 66594.2], ["04-03 09:30", 66594.3, 66748.7, 66550.0, 66706.0], ["04-03 09:45", 66706.1, 66770.0, 66680.0, 66762.0], ["04-03 10:00", 66762.1, 66879.4, 66716.4, 66785.7], ["04-03 10:15", 66785.7, 66916.4, 66764.1, 66913.2], ["04-03 10:30", 66913.1, 67233.3, 66882.4, 67043.4], ["04-03 10:45", 67043.3, 67095.7, 66971.0, 67008.8], ["04-03 11:00", 67008.8, 67258.0, 66993.4, 67137.5], ["04-03 11:15", 67137.4, 67188.0, 67012.8, 67023.0], ["04-03 11:30", 67023.0, 67090.0, 66864.1, 66900.4], ["04-03 11:45", 66900.3, 66978.4, 66867.0, 66935.0], ["04-03 12:00", 66935.1, 66976.0, 66850.0, 66866.0], ["04-03 12:15", 66866.1, 66893.5, 66714.3, 66790.0], ["04-03 12:30", 66790.0, 66888.0, 66757.0, 66868.4], ["04-03 12:45", 66868.5, 66874.4, 66772.0, 66828.9], ["04-03 13:00", 66828.9, 66828.9, 66736.0, 66791.2], ["04-03 13:15", 66791.2, 66847.9, 66727.7, 66727.7]]
    },

    "R18": {
        "data_15m": {"current_price": 66993.6, "ma5": 66916.78, "ma10": 66892.23, "ma30": 66838.43, "volume": 46200000, "volume_ma5": 36200000, "volume_ma10": 43500000, "net_long": -4700, "net_short": -4600, "futures_cvd": -19900000, "spot_cvd": 144.0, "taker_ls_ratio": 1.74, "oi": 90500, "oi_delta": -39.2, "liquidations": {"long": 0, "short": 8400}},
        "data_1h": {"current_price": 66992.3, "ma5": 66806.69, "ma10": 66863.48, "ma30": 66741.22, "volume": 140300000, "volume_ma5": 326800000, "volume_ma10": 288500000, "net_long": 6000, "net_short": 5000, "futures_cvd": -18000000, "spot_cvd": -6000, "taker_ls_ratio": 1.74, "oi": 90500, "oi_delta": -27.3, "liquidations": {"long": 11600, "short": 16300}},
        "data_4h": {"current_price": 66967.6, "ma5": 66863.98, "ma10": 66801.08, "ma30": 67293.15, "volume": 141100000, "volume_ma5": 916500000, "volume_ma10": 1370000000, "net_long": -29200, "net_short": 17500, "futures_cvd": 18600000, "spot_cvd": -80900, "taker_ls_ratio": 1.74, "oi": 90500, "oi_delta": -25.2, "liquidations": {"long": 11600, "short": 16300}},
        "actual": 'BELIRSIZ', "move": None,
        "run_time": "04-03 19:54",
        "whale_acct_ls": 0.8832,
        "api_whale_account": [['04-02 14:00', 0.9768], ['04-02 15:00', 0.9537], ['04-02 16:00', 0.9316], ['04-02 17:00', 0.9063], ['04-02 18:00', 0.8813], ['04-02 19:00', 0.8749], ['04-02 20:00', 0.8802], ['04-02 21:00', 0.8807], ['04-02 22:00', 0.88], ['04-02 23:00', 0.8826], ['04-03 00:00', 0.88], ['04-03 01:00', 0.8856], ['04-03 02:00', 0.8851], ['04-03 03:00', 0.8928], ['04-03 04:00', 0.9016], ['04-03 05:00', 0.9039], ['04-03 06:00', 0.9062], ['04-03 07:00', 0.907], ['04-03 08:00', 0.8996], ['04-03 09:00', 0.8906], ['04-03 10:00', 0.8868], ['04-03 11:00', 0.8871], ['04-03 12:00', 0.8836], ['04-03 13:00', 0.8793], ['04-03 14:00', 0.8908], ['04-03 15:00', 0.8901], ['04-03 16:00', 0.8832], ['04-03 17:00', 0.8795], ['04-03 18:00', 0.8821], ['04-03 19:00', 0.8829]],
        "api_whale_position": [['04-02 14:00', 2.3456], ['04-02 15:00', 2.2082], ['04-02 16:00', 2.1506], ['04-02 17:00', 2.0656], ['04-02 18:00', 1.9815], ['04-02 19:00', 1.9878], ['04-02 20:00', 1.9656], ['04-02 21:00', 1.9577], ['04-02 22:00', 1.9533], ['04-02 23:00', 1.9446], ['04-03 00:00', 1.9231], ['04-03 01:00', 1.9019], ['04-03 02:00', 1.896], ['04-03 03:00', 1.9283], ['04-03 04:00', 1.93], ['04-03 05:00', 1.9377], ['04-03 06:00', 1.963], ['04-03 07:00', 1.978], ['04-03 08:00', 1.9248], ['04-03 09:00', 1.8555], ['04-03 10:00', 1.8678], ['04-03 11:00', 1.8885], ['04-03 12:00', 1.8986], ['04-03 13:00', 1.8265], ['04-03 14:00', 1.8653], ['04-03 15:00', 1.8523], ['04-03 16:00', 1.8161], ['04-03 17:00', 1.8011], ['04-03 18:00', 1.7941], ['04-03 19:00', 1.7949]],
        "api_open_interest": [['04-02 14:00', 89821.35], ['04-02 15:00', 89858.13], ['04-02 16:00', 90567.53], ['04-02 17:00', 91244.66], ['04-02 18:00', 90813.61], ['04-02 19:00', 90353.51], ['04-02 20:00', 90256.23], ['04-02 21:00', 90142.26], ['04-02 22:00', 90149.0], ['04-02 23:00', 90167.25], ['04-03 00:00', 90119.34], ['04-03 01:00', 90456.75], ['04-03 02:00', 90492.64], ['04-03 03:00', 90701.42], ['04-03 04:00', 90854.84], ['04-03 05:00', 90898.03], ['04-03 06:00', 90609.22], ['04-03 07:00', 90567.7], ['04-03 08:00', 90159.28], ['04-03 09:00', 90350.39], ['04-03 10:00', 90305.06], ['04-03 11:00', 90209.61], ['04-03 12:00', 90069.5], ['04-03 13:00', 90115.95], ['04-03 14:00', 90463.49], ['04-03 15:00', 90456.13], ['04-03 16:00', 90476.57], ['04-03 17:00', 90450.32], ['04-03 18:00', 90415.2], ['04-03 19:00', 90344.98]],
        "api_funding_rate": [['03-31 16:00', -2.763e-05, 66700.0], ['04-01 00:00', -3.449e-05, 68243.3], ['04-01 08:00', -4.61e-06, 68668.6], ['04-01 16:00', 5.77e-06, 68876.82], ['04-02 00:00', 3.521e-05, 68086.5], ['04-02 08:00', 8.45e-06, 66888.21], ['04-02 16:00', -7.398e-05, 66819.54], ['04-03 00:00', -8.31e-06, 66869.74], ['04-03 08:00', -5.99e-06, 67008.7], ['04-03 16:00', 3.51e-06, 66809.34]],
        "klines_4h": [["04-02 07:00", 66538.4, 66898.5, 66171.8, 66887.9], ["04-02 11:00", 66887.8, 66887.9, 66065.1, 66180.6], ["04-02 15:00", 66180.6, 67080.0, 65676.1, 66810.6], ["04-02 19:00", 66810.6, 67400.0, 66550.0, 66943.2], ["04-02 23:00", 66943.2, 67078.9, 66681.3, 66868.5], ["04-03 03:00", 66868.6, 66976.2, 66240.0, 66550.0], ["04-03 07:00", 66550.1, 67233.3, 66375.1, 67008.8], ["04-03 11:00", 67008.8, 67258.0, 66644.0, 66983.4], ["04-03 15:00", 66983.5, 67350.0, 66478.5, 66806.1], ["04-03 19:00", 66806.0, 67046.1, 66714.1, 66857.0]],
        "klines_1h": [["04-02 14:00", 66424.1, 66449.7, 66065.1, 66180.6], ["04-02 15:00", 66180.6, 66215.2, 65919.1, 66014.2], ["04-02 16:00", 66014.3, 66250.0, 65676.1, 66227.3], ["04-02 17:00", 66227.3, 66873.8, 66123.0, 66765.8], ["04-02 18:00", 66822.3, 66960.7, 66596.2, 66810.6], ["04-02 19:00", 66810.6, 67234.4, 66707.6, 67050.1], ["04-02 20:00", 67050.0, 67400.0, 66622.4, 66641.4], ["04-02 21:00", 66641.4, 67044.8, 66550.0, 66941.6], ["04-02 22:00", 66941.7, 67082.9, 66827.8, 66943.2], ["04-02 23:00", 66943.2, 67078.9, 66755.6, 66906.3], ["04-03 00:00", 66906.4, 66993.4, 66681.3, 66910.7], ["04-03 01:00", 66910.7, 67008.5, 66782.0, 66954.0], ["04-03 02:00", 66954.0, 67070.2, 66820.6, 66868.5], ["04-03 03:00", 66868.6, 66976.2, 66671.0, 66761.8], ["04-03 04:00", 66761.8, 66881.3, 66450.0, 66599.0], ["04-03 05:00", 66599.1, 66726.7, 66240.0, 66504.6], ["04-03 06:00", 66504.6, 66698.5, 66461.0, 66550.0], ["04-03 07:00", 66550.1, 66666.0, 66468.0, 66578.8], ["04-03 08:00", 66578.8, 66789.6, 66375.1, 66574.9], ["04-03 09:00", 66574.9, 66770.0, 66523.2, 66762.0], ["04-03 10:00", 66762.1, 67233.3, 66716.4, 67008.8], ["04-03 11:00", 67008.8, 67258.0, 66864.1, 66935.0], ["04-03 12:00", 66935.1, 66976.0, 66714.3, 66828.9], ["04-03 13:00", 66828.9, 66871.9, 66644.0, 66845.3], ["04-03 14:00", 66845.3, 67041.9, 66790.6, 66983.4], ["04-03 15:00", 66983.5, 67350.0, 66605.9, 66690.4], ["04-03 16:00", 66690.4, 66707.1, 66478.5, 66644.6], ["04-03 17:00", 66644.6, 66968.1, 66600.0, 66900.0], ["04-03 18:00", 66899.9, 66999.0, 66778.9, 66806.1], ["04-03 19:00", 66806.0, 67046.1, 66800.0, 66972.5]],
        "klines_15m": [["04-03 07:30", 66505.7, 66578.1, 66468.0, 66548.9], ["04-03 07:45", 66548.8, 66648.4, 66533.0, 66578.8], ["04-03 08:00", 66578.8, 66641.0, 66554.1, 66554.1], ["04-03 08:15", 66554.2, 66561.6, 66375.1, 66549.1], ["04-03 08:30", 66549.0, 66789.6, 66549.0, 66740.1], ["04-03 08:45", 66740.1, 66740.1, 66478.8, 66574.9], ["04-03 09:00", 66574.9, 66635.9, 66523.2, 66635.9], ["04-03 09:15", 66635.9, 66665.8, 66567.1, 66594.2], ["04-03 09:30", 66594.3, 66748.7, 66550.0, 66706.0], ["04-03 09:45", 66706.1, 66770.0, 66680.0, 66762.0], ["04-03 10:00", 66762.1, 66879.4, 66716.4, 66785.7], ["04-03 10:15", 66785.7, 66916.4, 66764.1, 66913.2], ["04-03 10:30", 66913.1, 67233.3, 66882.4, 67043.4], ["04-03 10:45", 67043.3, 67095.7, 66971.0, 67008.8], ["04-03 11:00", 67008.8, 67258.0, 66993.4, 67137.5], ["04-03 11:15", 67137.4, 67188.0, 67012.8, 67023.0], ["04-03 11:30", 67023.0, 67090.0, 66864.1, 66900.4], ["04-03 11:45", 66900.3, 66978.4, 66867.0, 66935.0], ["04-03 12:00", 66935.1, 66976.0, 66850.0, 66866.0], ["04-03 12:15", 66866.1, 66893.5, 66714.3, 66790.0], ["04-03 12:30", 66790.0, 66888.0, 66757.0, 66868.4], ["04-03 12:45", 66868.5, 66874.4, 66772.0, 66828.9], ["04-03 13:00", 66828.9, 66828.9, 66736.0, 66791.2], ["04-03 13:15", 66791.2, 66847.9, 66727.7, 66727.7], ["04-03 13:30", 66727.8, 66765.7, 66644.0, 66749.2], ["04-03 13:45", 66749.3, 66871.9, 66749.3, 66845.3], ["04-03 14:00", 66845.3, 66888.2, 66790.6, 66823.2], ["04-03 14:15", 66823.3, 66927.7, 66807.8, 66904.9], ["04-03 14:30", 66904.9, 67041.9, 66880.2, 66965.0], ["04-03 14:45", 66965.0, 67009.0, 66911.6, 66983.4], ["04-03 15:00", 66983.5, 67018.0, 66890.4, 66978.3], ["04-03 15:15", 66978.4, 67110.4, 66910.0, 67087.1], ["04-03 15:30", 67087.2, 67350.0, 66751.9, 66837.1], ["04-03 15:45", 66836.7, 66868.3, 66605.9, 66690.4], ["04-03 16:00", 66690.4, 66707.1, 66525.4, 66645.9], ["04-03 16:15", 66645.9, 66705.7, 66564.0, 66649.9], ["04-03 16:30", 66650.0, 66651.4, 66546.7, 66574.9], ["04-03 16:45", 66574.9, 66663.3, 66478.5, 66644.6], ["04-03 17:00", 66644.6, 66776.8, 66600.0, 66752.9], ["04-03 17:15", 66752.9, 66968.1, 66688.5, 66878.1], ["04-03 17:30", 66878.2, 66910.8, 66773.3, 66775.8], ["04-03 17:45", 66775.9, 66953.7, 66775.8, 66900.0], ["04-03 18:00", 66899.9, 66999.0, 66876.6, 66931.8], ["04-03 18:15", 66931.8, 66931.9, 66828.6, 66899.8], ["04-03 18:30", 66899.8, 66956.2, 66804.2, 66828.4], ["04-03 18:45", 66828.5, 66853.4, 66778.9, 66806.1], ["04-03 19:00", 66806.0, 66890.0, 66800.0, 66881.5], ["04-03 19:15", 66881.6, 66965.0, 66843.3, 66959.0], ["04-03 19:30", 66958.9, 66979.0, 66896.4, 66944.7], ["04-03 19:45", 66944.7, 67046.1, 66911.3, 66972.5]]
    },

    "R19": {
        "data_15m": {"current_price": 66874.4, "ma5": 66861.8, "ma10": 66825.77, "ma30": 66836.83, "volume": 2500000, "volume_ma5": 12300000, "volume_ma10": 15000000, "net_long": -4900, "net_short": -5500, "futures_cvd": -16600000, "spot_cvd": -148.8, "taker_ls_ratio": 1.737, "oi": 90200, "oi_delta": -2.8594, "liquidations": {"long": 0, "short": 0}},
        "data_1h": {"current_price": 66874.4, "ma5": 66859.7, "ma10": 66832.3, "ma30": 66809.95, "volume": 40900000, "volume_ma5": 114100000, "volume_ma10": 224800000, "net_long": 8400, "net_short": 6200, "futures_cvd": -10900000, "spot_cvd": -5100, "taker_ls_ratio": 1.737, "oi": 90200, "oi_delta": 1.2578, "liquidations": {"long": 109000, "short": 6300}},
        "data_4h": {"current_price": 66870.7, "ma5": 66905.95, "ma10": 66788.34, "ma30": 67319.16, "volume": 41100000, "volume_ma5": 760000000, "volume_ma10": 1250000000, "net_long": -29300, "net_short": 16900, "futures_cvd": 19400000, "spot_cvd": -81100, "taker_ls_ratio": 1.737, "oi": 90200, "oi_delta": 1.3047, "liquidations": {"long": 109000, "short": 6300}},
        "actual": 'BELIRSIZ', "move": None,
        "mfe_4h": 72, "mae_4h": 83,
        "run_time": "04-03 21:04",
        "whale_acct_ls": 0.8821,
        "api_whale_account": [['04-02 18:00', 0.8813], ['04-02 19:00', 0.8749], ['04-02 20:00', 0.8802], ['04-02 21:00', 0.8807], ['04-02 22:00', 0.88], ['04-02 23:00', 0.8826], ['04-03 00:00', 0.88], ['04-03 01:00', 0.8856], ['04-03 02:00', 0.8851], ['04-03 03:00', 0.8928], ['04-03 04:00', 0.9016], ['04-03 05:00', 0.9039], ['04-03 06:00', 0.9062], ['04-03 07:00', 0.907], ['04-03 08:00', 0.8996], ['04-03 09:00', 0.8906], ['04-03 10:00', 0.8868], ['04-03 11:00', 0.8871], ['04-03 12:00', 0.8836], ['04-03 13:00', 0.8793], ['04-03 14:00', 0.8908], ['04-03 15:00', 0.8901], ['04-03 16:00', 0.8832], ['04-03 17:00', 0.8795], ['04-03 18:00', 0.8821], ['04-03 19:00', 0.8829], ['04-03 20:00', 0.8827], ['04-03 21:00', 0.8817], ['04-03 22:00', 0.8727], ['04-03 23:00', 0.8712]],
        "api_whale_position": [['04-02 18:00', 1.9815], ['04-02 19:00', 1.9878], ['04-02 20:00', 1.9656], ['04-02 21:00', 1.9577], ['04-02 22:00', 1.9533], ['04-02 23:00', 1.9446], ['04-03 00:00', 1.9231], ['04-03 01:00', 1.9019], ['04-03 02:00', 1.896], ['04-03 03:00', 1.9283], ['04-03 04:00', 1.93], ['04-03 05:00', 1.9377], ['04-03 06:00', 1.963], ['04-03 07:00', 1.978], ['04-03 08:00', 1.9248], ['04-03 09:00', 1.8555], ['04-03 10:00', 1.8678], ['04-03 11:00', 1.8885], ['04-03 12:00', 1.8986], ['04-03 13:00', 1.8265], ['04-03 14:00', 1.8653], ['04-03 15:00', 1.8523], ['04-03 16:00', 1.8161], ['04-03 17:00', 1.8011], ['04-03 18:00', 1.7941], ['04-03 19:00', 1.7949], ['04-03 20:00', 1.8161], ['04-03 21:00', 1.8161], ['04-03 22:00', 1.8193], ['04-03 23:00', 1.8145]],
        "api_open_interest": [['04-02 18:00', 90813.61], ['04-02 19:00', 90353.51], ['04-02 20:00', 90256.23], ['04-02 21:00', 90142.26], ['04-02 22:00', 90149.0], ['04-02 23:00', 90167.25], ['04-03 00:00', 90119.34], ['04-03 01:00', 90456.75], ['04-03 02:00', 90492.64], ['04-03 03:00', 90701.42], ['04-03 04:00', 90854.84], ['04-03 05:00', 90898.03], ['04-03 06:00', 90609.22], ['04-03 07:00', 90567.7], ['04-03 08:00', 90159.28], ['04-03 09:00', 90350.39], ['04-03 10:00', 90305.06], ['04-03 11:00', 90209.61], ['04-03 12:00', 90069.5], ['04-03 13:00', 90115.95], ['04-03 14:00', 90463.49], ['04-03 15:00', 90456.13], ['04-03 16:00', 90476.57], ['04-03 17:00', 90450.32], ['04-03 18:00', 90415.2], ['04-03 19:00', 90344.98], ['04-03 20:00', 90245.53], ['04-03 21:00', 90244.79], ['04-03 22:00', 90316.0], ['04-03 23:00', 90346.16]],
        "api_funding_rate": [['03-31 16:00', -2.763e-05, 66700.0], ['04-01 00:00', -3.449e-05, 68243.3], ['04-01 08:00', -4.61e-06, 68668.6], ['04-01 16:00', 5.77e-06, 68876.82], ['04-02 00:00', 3.521e-05, 68086.5], ['04-02 08:00', 8.45e-06, 66888.21], ['04-02 16:00', -7.398e-05, 66819.54], ['04-03 00:00', -8.31e-06, 66869.74], ['04-03 08:00', -5.99e-06, 67008.7], ['04-03 16:00', 3.51e-06, 66809.34]],
        "klines_4h": [["04-02 07:00", 66538.4, 66898.5, 66171.8, 66887.9], ["04-02 11:00", 66887.8, 66887.9, 66065.1, 66180.6], ["04-02 15:00", 66180.6, 67080.0, 65676.1, 66810.6], ["04-02 19:00", 66810.6, 67400.0, 66550.0, 66943.2], ["04-02 23:00", 66943.2, 67078.9, 66681.3, 66868.5], ["04-03 03:00", 66868.6, 66976.2, 66240.0, 66550.0], ["04-03 07:00", 66550.1, 67233.3, 66375.1, 67008.8], ["04-03 11:00", 67008.8, 67258.0, 66644.0, 66983.4], ["04-03 15:00", 66983.5, 67350.0, 66478.5, 66806.1], ["04-03 19:00", 66806.0, 67046.1, 66714.1, 66857.0]],
        "klines_1h": [["04-02 16:00", 66014.3, 66250.0, 65676.1, 66227.3], ["04-02 17:00", 66227.3, 66873.8, 66123.0, 66765.8], ["04-02 18:00", 66822.3, 66960.7, 66596.2, 66810.6], ["04-02 19:00", 66810.6, 67234.4, 66707.6, 67050.1], ["04-02 20:00", 67050.0, 67400.0, 66622.4, 66641.4], ["04-02 21:00", 66641.4, 67044.8, 66550.0, 66941.6], ["04-02 22:00", 66941.7, 67082.9, 66827.8, 66943.2], ["04-02 23:00", 66943.2, 67078.9, 66755.6, 66906.3], ["04-03 00:00", 66906.4, 66993.4, 66681.3, 66910.7], ["04-03 01:00", 66910.7, 67008.5, 66782.0, 66954.0], ["04-03 02:00", 66954.0, 67070.2, 66820.6, 66868.5], ["04-03 03:00", 66868.6, 66976.2, 66671.0, 66761.8], ["04-03 04:00", 66761.8, 66881.3, 66450.0, 66599.0], ["04-03 05:00", 66599.1, 66726.7, 66240.0, 66504.6], ["04-03 06:00", 66504.6, 66698.5, 66461.0, 66550.0], ["04-03 07:00", 66550.1, 66666.0, 66468.0, 66578.8], ["04-03 08:00", 66578.8, 66789.6, 66375.1, 66574.9], ["04-03 09:00", 66574.9, 66770.0, 66523.2, 66762.0], ["04-03 10:00", 66762.1, 67233.3, 66716.4, 67008.8], ["04-03 11:00", 67008.8, 67258.0, 66864.1, 66935.0], ["04-03 12:00", 66935.1, 66976.0, 66714.3, 66828.9], ["04-03 13:00", 66828.9, 66871.9, 66644.0, 66845.3], ["04-03 14:00", 66845.3, 67041.9, 66790.6, 66983.4], ["04-03 15:00", 66983.5, 67350.0, 66605.9, 66690.4], ["04-03 16:00", 66690.4, 66707.1, 66478.5, 66644.6], ["04-03 17:00", 66644.6, 66968.1, 66600.0, 66900.0], ["04-03 18:00", 66899.9, 66999.0, 66778.9, 66806.1], ["04-03 19:00", 66806.0, 67046.1, 66800.0, 66972.5], ["04-03 20:00", 66972.5, 67040.0, 66714.1, 66811.0], ["04-03 21:00", 66811.0, 66899.7, 66746.9, 66783.7]],
        "klines_15m": [["04-03 08:45", 66740.1, 66740.1, 66478.8, 66574.9], ["04-03 09:00", 66574.9, 66635.9, 66523.2, 66635.9], ["04-03 09:15", 66635.9, 66665.8, 66567.1, 66594.2], ["04-03 09:30", 66594.3, 66748.7, 66550.0, 66706.0], ["04-03 09:45", 66706.1, 66770.0, 66680.0, 66762.0], ["04-03 10:00", 66762.1, 66879.4, 66716.4, 66785.7], ["04-03 10:15", 66785.7, 66916.4, 66764.1, 66913.2], ["04-03 10:30", 66913.1, 67233.3, 66882.4, 67043.4], ["04-03 10:45", 67043.3, 67095.7, 66971.0, 67008.8], ["04-03 11:00", 67008.8, 67258.0, 66993.4, 67137.5], ["04-03 11:15", 67137.4, 67188.0, 67012.8, 67023.0], ["04-03 11:30", 67023.0, 67090.0, 66864.1, 66900.4], ["04-03 11:45", 66900.3, 66978.4, 66867.0, 66935.0], ["04-03 12:00", 66935.1, 66976.0, 66850.0, 66866.0], ["04-03 12:15", 66866.1, 66893.5, 66714.3, 66790.0], ["04-03 12:30", 66790.0, 66888.0, 66757.0, 66868.4], ["04-03 12:45", 66868.5, 66874.4, 66772.0, 66828.9], ["04-03 13:00", 66828.9, 66828.9, 66736.0, 66791.2], ["04-03 13:15", 66791.2, 66847.9, 66727.7, 66727.7], ["04-03 13:30", 66727.8, 66765.7, 66644.0, 66749.2], ["04-03 13:45", 66749.3, 66871.9, 66749.3, 66845.3], ["04-03 14:00", 66845.3, 66888.2, 66790.6, 66823.2], ["04-03 14:15", 66823.3, 66927.7, 66807.8, 66904.9], ["04-03 14:30", 66904.9, 67041.9, 66880.2, 66965.0], ["04-03 14:45", 66965.0, 67009.0, 66911.6, 66983.4], ["04-03 15:00", 66983.5, 67018.0, 66890.4, 66978.3], ["04-03 15:15", 66978.4, 67110.4, 66910.0, 67087.1], ["04-03 15:30", 67087.2, 67350.0, 66751.9, 66837.1], ["04-03 15:45", 66836.7, 66868.3, 66605.9, 66690.4], ["04-03 16:00", 66690.4, 66707.1, 66525.4, 66645.9], ["04-03 16:15", 66645.9, 66705.7, 66564.0, 66649.9], ["04-03 16:30", 66650.0, 66651.4, 66546.7, 66574.9], ["04-03 16:45", 66574.9, 66663.3, 66478.5, 66644.6], ["04-03 17:00", 66644.6, 66776.8, 66600.0, 66752.9], ["04-03 17:15", 66752.9, 66968.1, 66688.5, 66878.1], ["04-03 17:30", 66878.2, 66910.8, 66773.3, 66775.8], ["04-03 17:45", 66775.9, 66953.7, 66775.8, 66900.0], ["04-03 18:00", 66899.9, 66999.0, 66876.6, 66931.8], ["04-03 18:15", 66931.8, 66931.9, 66828.6, 66899.8], ["04-03 18:30", 66899.8, 66956.2, 66804.2, 66828.4], ["04-03 18:45", 66828.5, 66853.4, 66778.9, 66806.1], ["04-03 19:00", 66806.0, 66890.0, 66800.0, 66881.5], ["04-03 19:15", 66881.6, 66965.0, 66843.3, 66959.0], ["04-03 19:30", 66958.9, 66979.0, 66896.4, 66944.7], ["04-03 19:45", 66944.7, 67046.1, 66911.3, 66972.5], ["04-03 20:00", 66972.5, 67040.0, 66920.2, 66920.3], ["04-03 20:15", 66920.3, 66936.8, 66714.1, 66844.6], ["04-03 20:30", 66844.6, 66923.6, 66822.7, 66860.0], ["04-03 20:45", 66860.0, 66869.9, 66773.1, 66811.0], ["04-03 21:00", 66811.0, 66838.2, 66746.9, 66807.0]]
    },

    "R20": {
        "data_15m": {"current_price": 66907.7, "ma5": 66857.04, "ma10": 66874.03, "ma30": 66855.72, "volume": 14900000, "volume_ma5": 18600000, "volume_ma10": 21300000, "net_long": -4600, "net_short": -6600, "futures_cvd": -14200000, "spot_cvd": 203.8, "taker_ls_ratio": 1.734, "oi": 90300, "oi_delta": -5.4922, "liquidations": {"long": 0, "short": 0}},
        "data_1h": {"current_price": 66907.6, "ma5": 66870.84, "ma10": 66862.76, "ma30": 66813.97, "volume": 74200000, "volume_ma5": 79700000, "volume_ma10": 133000000, "net_long": 7900, "net_short": 5900, "futures_cvd": -10000000, "spot_cvd": -5100, "taker_ls_ratio": 1.734, "oi": 90300, "oi_delta": -59.3, "liquidations": {"long": 23700, "short": 22300}},
        "data_4h": {"current_price": 66907.6, "ma5": 66912.59, "ma10": 66791.67, "ma30": 67320.27, "volume": 316600000, "volume_ma5": 815100000, "volume_ma10": 1280000000, "net_long": -29300, "net_short": 16900, "futures_cvd": 20600000, "spot_cvd": -80900, "taker_ls_ratio": 1.734, "oi": 90200, "oi_delta": 43.6, "liquidations": {"long": 158200, "short": 52800}},
        "actual": 'BELIRSIZ', "move": None,
        "mfe_4h": 39, "mae_4h": 116,
        "run_time": "04-04 00:07",
        "whale_acct_ls": 0.8817,
        "api_whale_account": [['04-02 21:00', 0.8807], ['04-02 22:00', 0.88], ['04-02 23:00', 0.8826], ['04-03 00:00', 0.88], ['04-03 01:00', 0.8856], ['04-03 02:00', 0.8851], ['04-03 03:00', 0.8928], ['04-03 04:00', 0.9016], ['04-03 05:00', 0.9039], ['04-03 06:00', 0.9062], ['04-03 07:00', 0.907], ['04-03 08:00', 0.8996], ['04-03 09:00', 0.8906], ['04-03 10:00', 0.8868], ['04-03 11:00', 0.8871], ['04-03 12:00', 0.8836], ['04-03 13:00', 0.8793], ['04-03 14:00', 0.8908], ['04-03 15:00', 0.8901], ['04-03 16:00', 0.8832], ['04-03 17:00', 0.8795], ['04-03 18:00', 0.8821], ['04-03 19:00', 0.8829], ['04-03 20:00', 0.8827], ['04-03 21:00', 0.8817], ['04-03 22:00', 0.8727], ['04-03 23:00', 0.8712], ['04-04 00:00', 0.8727], ['04-04 01:00', 0.8722], ['04-04 02:00', 0.8721]],
        "api_whale_position": [['04-02 21:00', 1.9577], ['04-02 22:00', 1.9533], ['04-02 23:00', 1.9446], ['04-03 00:00', 1.9231], ['04-03 01:00', 1.9019], ['04-03 02:00', 1.896], ['04-03 03:00', 1.9283], ['04-03 04:00', 1.93], ['04-03 05:00', 1.9377], ['04-03 06:00', 1.963], ['04-03 07:00', 1.978], ['04-03 08:00', 1.9248], ['04-03 09:00', 1.8555], ['04-03 10:00', 1.8678], ['04-03 11:00', 1.8885], ['04-03 12:00', 1.8986], ['04-03 13:00', 1.8265], ['04-03 14:00', 1.8653], ['04-03 15:00', 1.8523], ['04-03 16:00', 1.8161], ['04-03 17:00', 1.8011], ['04-03 18:00', 1.7941], ['04-03 19:00', 1.7949], ['04-03 20:00', 1.8161], ['04-03 21:00', 1.8161], ['04-03 22:00', 1.8193], ['04-03 23:00', 1.8145], ['04-04 00:00', 1.8129], ['04-04 01:00', 1.8137], ['04-04 02:00', 1.8129]],
        "api_open_interest": [['04-02 21:00', 90142.26], ['04-02 22:00', 90149.0], ['04-02 23:00', 90167.25], ['04-03 00:00', 90119.34], ['04-03 01:00', 90456.75], ['04-03 02:00', 90492.64], ['04-03 03:00', 90701.42], ['04-03 04:00', 90854.84], ['04-03 05:00', 90898.03], ['04-03 06:00', 90609.22], ['04-03 07:00', 90567.7], ['04-03 08:00', 90159.28], ['04-03 09:00', 90350.39], ['04-03 10:00', 90305.06], ['04-03 11:00', 90209.61], ['04-03 12:00', 90069.5], ['04-03 13:00', 90115.95], ['04-03 14:00', 90463.49], ['04-03 15:00', 90456.13], ['04-03 16:00', 90476.57], ['04-03 17:00', 90450.32], ['04-03 18:00', 90415.2], ['04-03 19:00', 90344.98], ['04-03 20:00', 90245.53], ['04-03 21:00', 90244.79], ['04-03 22:00', 90316.0], ['04-03 23:00', 90346.16], ['04-04 00:00', 90276.77], ['04-04 01:00', 90404.57], ['04-04 02:00', 90435.17]],
        "api_funding_rate": [['04-01 00:00', -3.449e-05, 68243.3], ['04-01 08:00', -4.61e-06, 68668.6], ['04-01 16:00', 5.77e-06, 68876.82], ['04-02 00:00', 3.521e-05, 68086.5], ['04-02 08:00', 8.45e-06, 66888.21], ['04-02 16:00', -7.398e-05, 66819.54], ['04-03 00:00', -8.31e-06, 66869.74], ['04-03 08:00', -5.99e-06, 67008.7], ['04-03 16:00', 3.51e-06, 66809.34], ['04-04 00:00', 3.761e-05, 66930.0]],
        "klines_4h": [["04-02 11:00", 66887.8, 66887.9, 66065.1, 66180.6], ["04-02 15:00", 66180.6, 67080.0, 65676.1, 66810.6], ["04-02 19:00", 66810.6, 67400.0, 66550.0, 66943.2], ["04-02 23:00", 66943.2, 67078.9, 66681.3, 66868.5], ["04-03 03:00", 66868.6, 66976.2, 66240.0, 66550.0], ["04-03 07:00", 66550.1, 67233.3, 66375.1, 67008.8], ["04-03 11:00", 67008.8, 67258.0, 66644.0, 66983.4], ["04-03 15:00", 66983.5, 67350.0, 66478.5, 66806.1], ["04-03 19:00", 66806.0, 67046.1, 66714.1, 66857.0], ["04-03 23:00", 66857.0, 66946.3, 66791.8, 66930.0]],
        "klines_1h": [["04-02 19:00", 66810.6, 67234.4, 66707.6, 67050.1], ["04-02 20:00", 67050.0, 67400.0, 66622.4, 66641.4], ["04-02 21:00", 66641.4, 67044.8, 66550.0, 66941.6], ["04-02 22:00", 66941.7, 67082.9, 66827.8, 66943.2], ["04-02 23:00", 66943.2, 67078.9, 66755.6, 66906.3], ["04-03 00:00", 66906.4, 66993.4, 66681.3, 66910.7], ["04-03 01:00", 66910.7, 67008.5, 66782.0, 66954.0], ["04-03 02:00", 66954.0, 67070.2, 66820.6, 66868.5], ["04-03 03:00", 66868.6, 66976.2, 66671.0, 66761.8], ["04-03 04:00", 66761.8, 66881.3, 66450.0, 66599.0], ["04-03 05:00", 66599.1, 66726.7, 66240.0, 66504.6], ["04-03 06:00", 66504.6, 66698.5, 66461.0, 66550.0], ["04-03 07:00", 66550.1, 66666.0, 66468.0, 66578.8], ["04-03 08:00", 66578.8, 66789.6, 66375.1, 66574.9], ["04-03 09:00", 66574.9, 66770.0, 66523.2, 66762.0], ["04-03 10:00", 66762.1, 67233.3, 66716.4, 67008.8], ["04-03 11:00", 67008.8, 67258.0, 66864.1, 66935.0], ["04-03 12:00", 66935.1, 66976.0, 66714.3, 66828.9], ["04-03 13:00", 66828.9, 66871.9, 66644.0, 66845.3], ["04-03 14:00", 66845.3, 67041.9, 66790.6, 66983.4], ["04-03 15:00", 66983.5, 67350.0, 66605.9, 66690.4], ["04-03 16:00", 66690.4, 66707.1, 66478.5, 66644.6], ["04-03 17:00", 66644.6, 66968.1, 66600.0, 66900.0], ["04-03 18:00", 66899.9, 66999.0, 66778.9, 66806.1], ["04-03 19:00", 66806.0, 67046.1, 66800.0, 66972.5], ["04-03 20:00", 66972.5, 67040.0, 66714.1, 66811.0], ["04-03 21:00", 66811.0, 66899.7, 66746.9, 66783.7], ["04-03 22:00", 66783.6, 66882.9, 66740.6, 66857.0], ["04-03 23:00", 66857.0, 66888.0, 66800.0, 66800.1], ["04-04 00:00", 66800.0, 66946.3, 66791.8, 66929.5]],
        "klines_15m": [["04-03 11:45", 66900.3, 66978.4, 66867.0, 66935.0], ["04-03 12:00", 66935.1, 66976.0, 66850.0, 66866.0], ["04-03 12:15", 66866.1, 66893.5, 66714.3, 66790.0], ["04-03 12:30", 66790.0, 66888.0, 66757.0, 66868.4], ["04-03 12:45", 66868.5, 66874.4, 66772.0, 66828.9], ["04-03 13:00", 66828.9, 66828.9, 66736.0, 66791.2], ["04-03 13:15", 66791.2, 66847.9, 66727.7, 66727.7], ["04-03 13:30", 66727.8, 66765.7, 66644.0, 66749.2], ["04-03 13:45", 66749.3, 66871.9, 66749.3, 66845.3], ["04-03 14:00", 66845.3, 66888.2, 66790.6, 66823.2], ["04-03 14:15", 66823.3, 66927.7, 66807.8, 66904.9], ["04-03 14:30", 66904.9, 67041.9, 66880.2, 66965.0], ["04-03 14:45", 66965.0, 67009.0, 66911.6, 66983.4], ["04-03 15:00", 66983.5, 67018.0, 66890.4, 66978.3], ["04-03 15:15", 66978.4, 67110.4, 66910.0, 67087.1], ["04-03 15:30", 67087.2, 67350.0, 66751.9, 66837.1], ["04-03 15:45", 66836.7, 66868.3, 66605.9, 66690.4], ["04-03 16:00", 66690.4, 66707.1, 66525.4, 66645.9], ["04-03 16:15", 66645.9, 66705.7, 66564.0, 66649.9], ["04-03 16:30", 66650.0, 66651.4, 66546.7, 66574.9], ["04-03 16:45", 66574.9, 66663.3, 66478.5, 66644.6], ["04-03 17:00", 66644.6, 66776.8, 66600.0, 66752.9], ["04-03 17:15", 66752.9, 66968.1, 66688.5, 66878.1], ["04-03 17:30", 66878.2, 66910.8, 66773.3, 66775.8], ["04-03 17:45", 66775.9, 66953.7, 66775.8, 66900.0], ["04-03 18:00", 66899.9, 66999.0, 66876.6, 66931.8], ["04-03 18:15", 66931.8, 66931.9, 66828.6, 66899.8], ["04-03 18:30", 66899.8, 66956.2, 66804.2, 66828.4], ["04-03 18:45", 66828.5, 66853.4, 66778.9, 66806.1], ["04-03 19:00", 66806.0, 66890.0, 66800.0, 66881.5], ["04-03 19:15", 66881.6, 66965.0, 66843.3, 66959.0], ["04-03 19:30", 66958.9, 66979.0, 66896.4, 66944.7], ["04-03 19:45", 66944.7, 67046.1, 66911.3, 66972.5], ["04-03 20:00", 66972.5, 67040.0, 66920.2, 66920.3], ["04-03 20:15", 66920.3, 66936.8, 66714.1, 66844.6], ["04-03 20:30", 66844.6, 66923.6, 66822.7, 66860.0], ["04-03 20:45", 66860.0, 66869.9, 66773.1, 66811.0], ["04-03 21:00", 66811.0, 66838.2, 66746.9, 66807.0], ["04-03 21:15", 66807.0, 66899.7, 66788.7, 66850.0], ["04-03 21:30", 66850.1, 66890.1, 66805.0, 66826.2], ["04-03 21:45", 66826.2, 66826.2, 66767.7, 66783.7], ["04-03 22:00", 66783.6, 66822.8, 66746.0, 66752.4], ["04-03 22:15", 66752.3, 66827.3, 66751.0, 66765.2], ["04-03 22:30", 66765.2, 66829.3, 66740.6, 66821.7], ["04-03 22:45", 66821.7, 66882.9, 66818.3, 66857.0], ["04-03 23:00", 66857.0, 66877.3, 66816.0, 66869.0], ["04-03 23:15", 66869.0, 66878.0, 66839.6, 66847.7], ["04-03 23:30", 66847.7, 66888.0, 66821.5, 66856.7], ["04-03 23:45", 66856.6, 66877.0, 66800.0, 66800.1], ["04-04 00:00", 66800.0, 66900.3, 66791.8, 66878.6]]
    },

    "R21": {
        "data_15m": {"current_price": 67082.4, "ma5": 67097.14, "ma10": 67076.76, "ma30": 66980.34, "volume": 5400000, "volume_ma5": 23700000, "volume_ma10": 39000000, "net_long": -92.3, "net_short": -3400, "futures_cvd": -12400000, "spot_cvd": 603.0, "taker_ls_ratio": 1.647, "oi": 90500, "oi_delta": 7.4453, "liquidations": {"long": 0, "short": 0}},
        "data_1h": {"current_price": 67082.5, "ma5": 67042.06, "ma10": 66967.75, "ma30": 66892.05, "volume": 62500000, "volume_ma5": 119700000, "volume_ma10": 104800000, "net_long": 8500, "net_short": 4100, "futures_cvd": -6800000, "spot_cvd": -4100, "taker_ls_ratio": 1.647, "oi": 90500, "oi_delta": 58.7, "liquidations": {"long": 2800, "short": 5200}},
        "data_4h": {"current_price": 67082.4, "ma5": 66984.48, "ma10": 66912.84, "ma30": 67254.95, "volume": 63800000, "volume_ma5": 316800000, "volume_ma10": 655600000, "net_long": -27900, "net_short": 16500, "futures_cvd": 21200000, "spot_cvd": -80800, "taker_ls_ratio": 1.647, "oi": 90500, "oi_delta": 58.7, "liquidations": {"long": 2800, "short": 5200}},
        "actual": 'BELIRSIZ', "move": None,
        "mfe_4h": 472, "mae_4h": 79,
        "run_time": "04-04 15:33",
        "whale_acct_ls": 0.8713,
        "api_whale_account": [['04-03 03:00', 0.8928], ['04-03 04:00', 0.9016], ['04-03 05:00', 0.9039], ['04-03 06:00', 0.9062], ['04-03 07:00', 0.907], ['04-03 08:00', 0.8996], ['04-03 09:00', 0.8906], ['04-03 10:00', 0.8868], ['04-03 11:00', 0.8871], ['04-03 12:00', 0.8836], ['04-03 13:00', 0.8793], ['04-03 14:00', 0.8908], ['04-03 15:00', 0.8901], ['04-03 16:00', 0.8832], ['04-03 17:00', 0.8795], ['04-03 18:00', 0.8821], ['04-03 19:00', 0.8829], ['04-03 20:00', 0.8827], ['04-03 21:00', 0.8817], ['04-03 22:00', 0.8727], ['04-03 23:00', 0.8712], ['04-04 00:00', 0.8727], ['04-04 01:00', 0.8722], ['04-04 02:00', 0.8721], ['04-04 03:00', 0.8741], ['04-04 04:00', 0.8751], ['04-04 05:00', 0.8753], ['04-04 06:00', 0.8736], ['04-04 07:00', 0.8735], ['04-04 08:00', 0.874]],
        "api_whale_position": [['04-03 03:00', 1.9283], ['04-03 04:00', 1.93], ['04-03 05:00', 1.9377], ['04-03 06:00', 1.963], ['04-03 07:00', 1.978], ['04-03 08:00', 1.9248], ['04-03 09:00', 1.8555], ['04-03 10:00', 1.8678], ['04-03 11:00', 1.8885], ['04-03 12:00', 1.8986], ['04-03 13:00', 1.8265], ['04-03 14:00', 1.8653], ['04-03 15:00', 1.8523], ['04-03 16:00', 1.8161], ['04-03 17:00', 1.8011], ['04-03 18:00', 1.7941], ['04-03 19:00', 1.7949], ['04-03 20:00', 1.8161], ['04-03 21:00', 1.8161], ['04-03 22:00', 1.8193], ['04-03 23:00', 1.8145], ['04-04 00:00', 1.8129], ['04-04 01:00', 1.8137], ['04-04 02:00', 1.8129], ['04-04 03:00', 1.8019], ['04-04 04:00', 1.805], ['04-04 05:00', 1.8058], ['04-04 06:00', 1.809], ['04-04 07:00', 1.7964], ['04-04 08:00', 1.7678]],
        "api_open_interest": [['04-03 03:00', 90701.42], ['04-03 04:00', 90854.84], ['04-03 05:00', 90898.03], ['04-03 06:00', 90609.22], ['04-03 07:00', 90567.7], ['04-03 08:00', 90159.28], ['04-03 09:00', 90350.39], ['04-03 10:00', 90305.06], ['04-03 11:00', 90209.61], ['04-03 12:00', 90069.5], ['04-03 13:00', 90115.95], ['04-03 14:00', 90463.49], ['04-03 15:00', 90456.13], ['04-03 16:00', 90476.57], ['04-03 17:00', 90450.32], ['04-03 18:00', 90415.2], ['04-03 19:00', 90344.98], ['04-03 20:00', 90245.53], ['04-03 21:00', 90244.79], ['04-03 22:00', 90316.0], ['04-03 23:00', 90346.16], ['04-04 00:00', 90276.77], ['04-04 01:00', 90404.57], ['04-04 02:00', 90435.17], ['04-04 03:00', 90444.29], ['04-04 04:00', 90396.92], ['04-04 05:00', 90382.03], ['04-04 06:00', 90388.65], ['04-04 07:00', 90109.42], ['04-04 08:00', 90175.64]],
        "api_funding_rate": [['04-01 08:00', -4.61e-06, 68668.6], ['04-01 16:00', 5.77e-06, 68876.82], ['04-02 00:00', 3.521e-05, 68086.5], ['04-02 08:00', 8.45e-06, 66888.21], ['04-02 16:00', -7.398e-05, 66819.54], ['04-03 00:00', -8.31e-06, 66869.74], ['04-03 08:00', -5.99e-06, 67008.7], ['04-03 16:00', 3.51e-06, 66809.34], ['04-04 00:00', 3.761e-05, 66930.0], ['04-04 08:00', 4.115e-05, 66983.97]],
        "klines_4h": [["04-03 03:00", 66868.6, 66976.2, 66240.0, 66550.0], ["04-03 07:00", 66550.1, 67233.3, 66375.1, 67008.8], ["04-03 11:00", 67008.8, 67258.0, 66644.0, 66983.4], ["04-03 15:00", 66983.5, 67350.0, 66478.5, 66806.1], ["04-03 19:00", 66806.0, 67046.1, 66714.1, 66857.0], ["04-03 23:00", 66857.0, 66946.3, 66791.8, 66930.0], ["04-04 03:00", 66930.0, 66935.3, 66773.3, 66799.1], ["04-04 07:00", 66799.1, 67023.7, 66745.5, 66982.0], ["04-04 11:00", 66982.1, 67223.8, 66874.5, 67128.9], ["04-04 15:00", 67128.9, 67554.5, 67003.7, 67357.3]],
        "klines_1h": [["04-03 10:00", 66762.1, 67233.3, 66716.4, 67008.8], ["04-03 11:00", 67008.8, 67258.0, 66864.1, 66935.0], ["04-03 12:00", 66935.1, 66976.0, 66714.3, 66828.9], ["04-03 13:00", 66828.9, 66871.9, 66644.0, 66845.3], ["04-03 14:00", 66845.3, 67041.9, 66790.6, 66983.4], ["04-03 15:00", 66983.5, 67350.0, 66605.9, 66690.4], ["04-03 16:00", 66690.4, 66707.1, 66478.5, 66644.6], ["04-03 17:00", 66644.6, 66968.1, 66600.0, 66900.0], ["04-03 18:00", 66899.9, 66999.0, 66778.9, 66806.1], ["04-03 19:00", 66806.0, 67046.1, 66800.0, 66972.5], ["04-03 20:00", 66972.5, 67040.0, 66714.1, 66811.0], ["04-03 21:00", 66811.0, 66899.7, 66746.9, 66783.7], ["04-03 22:00", 66783.6, 66882.9, 66740.6, 66857.0], ["04-03 23:00", 66857.0, 66888.0, 66800.0, 66800.1], ["04-04 00:00", 66800.0, 66946.3, 66791.8, 66929.5], ["04-04 01:00", 66929.4, 66943.0, 66813.0, 66860.0], ["04-04 02:00", 66859.9, 66930.0, 66800.7, 66930.0], ["04-04 03:00", 66930.0, 66935.3, 66838.9, 66863.4], ["04-04 04:00", 66863.4, 66895.7, 66795.8, 66820.0], ["04-04 05:00", 66820.0, 66891.4, 66773.3, 66814.1], ["04-04 06:00", 66814.0, 66875.4, 66798.8, 66799.1], ["04-04 07:00", 66799.1, 66840.0, 66745.5, 66833.5], ["04-04 08:00", 66833.5, 66908.4, 66817.8, 66871.0], ["04-04 09:00", 66871.0, 67023.7, 66871.0, 66981.5], ["04-04 10:00", 66981.5, 67019.1, 66904.0, 66982.0], ["04-04 11:00", 66982.1, 67025.0, 66874.5, 66907.8], ["04-04 12:00", 66907.8, 66958.2, 66882.1, 66952.1], ["04-04 13:00", 66952.1, 67150.3, 66880.9, 67139.1], ["04-04 14:00", 67139.1, 67223.8, 67050.0, 67128.9], ["04-04 15:00", 67128.9, 67152.5, 67025.2, 67062.0]],
        "klines_15m": [["04-04 03:15", 66873.1, 66935.3, 66860.0, 66885.6], ["04-04 03:30", 66885.6, 66930.0, 66875.1, 66905.3], ["04-04 03:45", 66905.2, 66905.2, 66855.0, 66863.4], ["04-04 04:00", 66863.4, 66895.7, 66819.8, 66819.9], ["04-04 04:15", 66819.8, 66848.3, 66811.4, 66811.4], ["04-04 04:30", 66811.5, 66837.1, 66795.8, 66798.2], ["04-04 04:45", 66798.1, 66822.0, 66798.1, 66820.0], ["04-04 05:00", 66820.0, 66891.4, 66791.8, 66816.9], ["04-04 05:15", 66817.0, 66817.0, 66781.6, 66804.7], ["04-04 05:30", 66804.7, 66859.6, 66799.9, 66800.8], ["04-04 05:45", 66800.8, 66816.4, 66773.3, 66814.1], ["04-04 06:00", 66814.0, 66875.4, 66814.0, 66867.9], ["04-04 06:15", 66867.9, 66867.9, 66818.4, 66824.4], ["04-04 06:30", 66824.4, 66829.9, 66806.2, 66816.3], ["04-04 06:45", 66816.4, 66838.3, 66798.8, 66799.1], ["04-04 07:00", 66799.1, 66821.8, 66770.0, 66773.0], ["04-04 07:15", 66773.1, 66835.0, 66745.5, 66834.6], ["04-04 07:30", 66834.6, 66837.6, 66818.2, 66831.0], ["04-04 07:45", 66830.9, 66840.0, 66817.8, 66833.5], ["04-04 08:00", 66833.5, 66866.4, 66826.9, 66830.6], ["04-04 08:15", 66830.9, 66878.8, 66817.8, 66849.7], ["04-04 08:30", 66849.8, 66908.4, 66844.8, 66868.8], ["04-04 08:45", 66868.9, 66894.7, 66862.9, 66871.0], ["04-04 09:00", 66871.0, 66934.0, 66871.0, 66926.5], ["04-04 09:15", 66926.5, 66940.0, 66876.0, 66920.0], ["04-04 09:30", 66920.0, 66925.0, 66886.8, 66924.9], ["04-04 09:45", 66925.0, 67023.7, 66924.9, 66981.5], ["04-04 10:00", 66981.5, 67004.1, 66955.1, 66973.8], ["04-04 10:15", 66973.8, 66983.0, 66904.0, 66928.0], ["04-04 10:30", 66928.0, 66970.2, 66927.4, 66934.2], ["04-04 10:45", 66934.2, 67019.1, 66919.1, 66982.0], ["04-04 11:00", 66982.1, 67020.0, 66957.2, 66968.6], ["04-04 11:15", 66968.6, 67025.0, 66964.3, 67017.2], ["04-04 11:30", 67017.3, 67017.3, 66928.6, 66943.0], ["04-04 11:45", 66943.0, 66945.7, 66874.5, 66907.8], ["04-04 12:00", 66907.8, 66957.0, 66882.1, 66948.0], ["04-04 12:15", 66948.1, 66958.2, 66910.4, 66944.8], ["04-04 12:30", 66944.9, 66953.8, 66927.1, 66928.9], ["04-04 12:45", 66929.0, 66954.8, 66928.9, 66952.1], ["04-04 13:00", 66952.1, 66993.3, 66880.9, 66880.9], ["04-04 13:15", 66880.9, 66923.6, 66880.9, 66906.9], ["04-04 13:30", 66906.9, 67039.8, 66894.3, 67008.7], ["04-04 13:45", 67008.7, 67150.3, 67001.0, 67139.1], ["04-04 14:00", 67139.1, 67223.8, 67111.1, 67134.8], ["04-04 14:15", 67134.8, 67134.8, 67068.3, 67092.7], ["04-04 14:30", 67092.8, 67125.5, 67050.0, 67111.1], ["04-04 14:45", 67111.2, 67128.9, 67069.3, 67128.9], ["04-04 15:00", 67128.9, 67152.5, 67048.0, 67084.8], ["04-04 15:15", 67084.8, 67110.0, 67070.6, 67075.1], ["04-04 15:30", 67075.2, 67096.5, 67025.2, 67028.7]]
    },

    "R22": {
        "data_15m": {"current_price": 67290.0, "ma5": 67325.47, "ma10": 67348.27, "ma30": 67203.27, "volume": 302000, "volume_ma5": 55700000, "volume_ma10": 58700000, "net_long": 1000, "net_short": -696.2, "futures_cvd": -14100000, "spot_cvd": 504.7, "taker_ls_ratio": 1.587, "oi": 92400, "oi_delta": 0, "liquidations": {"long": 0, "short": 0}},
        "data_1h": {"current_price": 67290.0, "ma5": 67266.01, "ma10": 67152.02, "ma30": 66949.0, "volume": 116600000, "volume_ma5": 299200000, "volume_ma10": 213000000, "net_long": 10400, "net_short": 6600, "futures_cvd": -6400000, "spot_cvd": -3800, "taker_ls_ratio": 1.587, "oi": 92400, "oi_delta": -337.6, "liquidations": {"long": 14900, "short": 13600}},
        "data_4h": {"current_price": 67290.0, "ma5": 67111.44, "ma10": 67014.27, "ma30": 67289.81, "volume": 493300000, "volume_ma5": 559100000, "volume_ma10": 687400000, "net_long": -26700, "net_short": 17000, "futures_cvd": 24800000, "spot_cvd": -80500, "taker_ls_ratio": 1.587, "oi": 91700, "oi_delta": 291.2, "liquidations": {"long": 53700, "short": 132000}},
        "actual": 'BELIRSIZ', "move": None,
        "mfe_4h": 234, "mae_4h": 139,
        "run_time": "04-04 20:44",
        "whale_acct_ls": 0.8507,
        "api_whale_account": [['04-03 15:00', 0.8901], ['04-03 16:00', 0.8832], ['04-03 17:00', 0.8795], ['04-03 18:00', 0.8821], ['04-03 19:00', 0.8829], ['04-03 20:00', 0.8827], ['04-03 21:00', 0.8817], ['04-03 22:00', 0.8727], ['04-03 23:00', 0.8712], ['04-04 00:00', 0.8727], ['04-04 01:00', 0.8722], ['04-04 02:00', 0.8721], ['04-04 03:00', 0.8741], ['04-04 04:00', 0.8751], ['04-04 05:00', 0.8753], ['04-04 06:00', 0.8736], ['04-04 07:00', 0.8735], ['04-04 08:00', 0.874], ['04-04 09:00', 0.8713], ['04-04 10:00', 0.8711], ['04-04 11:00', 0.8727], ['04-04 12:00', 0.8713], ['04-04 13:00', 0.8713], ['04-04 14:00', 0.8755], ['04-04 15:00', 0.8611], ['04-04 16:00', 0.872], ['04-04 17:00', 0.8507], ['04-04 18:00', 0.848], ['04-04 19:00', 0.8492], ['04-04 20:00', 0.8483]],
        "api_whale_position": [['04-03 15:00', 1.8523], ['04-03 16:00', 1.8161], ['04-03 17:00', 1.8011], ['04-03 18:00', 1.7941], ['04-03 19:00', 1.7949], ['04-03 20:00', 1.8161], ['04-03 21:00', 1.8161], ['04-03 22:00', 1.8193], ['04-03 23:00', 1.8145], ['04-04 00:00', 1.8129], ['04-04 01:00', 1.8137], ['04-04 02:00', 1.8129], ['04-04 03:00', 1.8019], ['04-04 04:00', 1.805], ['04-04 05:00', 1.8058], ['04-04 06:00', 1.809], ['04-04 07:00', 1.7964], ['04-04 08:00', 1.7678], ['04-04 09:00', 1.7609], ['04-04 10:00', 1.7579], ['04-04 11:00', 1.7563], ['04-04 12:00', 1.7203], ['04-04 13:00', 1.7093], ['04-04 14:00', 1.7093], ['04-04 15:00', 1.6961], ['04-04 16:00', 1.6567], ['04-04 17:00', 1.6483], ['04-04 18:00', 1.6344], ['04-04 19:00', 1.6274], ['04-04 20:00', 1.6254]],
        "api_open_interest": [['04-03 15:00', 90456.13], ['04-03 16:00', 90476.57], ['04-03 17:00', 90450.32], ['04-03 18:00', 90415.2], ['04-03 19:00', 90344.98], ['04-03 20:00', 90245.53], ['04-03 21:00', 90244.79], ['04-03 22:00', 90316.0], ['04-03 23:00', 90346.16], ['04-04 00:00', 90276.77], ['04-04 01:00', 90404.57], ['04-04 02:00', 90435.17], ['04-04 03:00', 90444.29], ['04-04 04:00', 90396.92], ['04-04 05:00', 90382.03], ['04-04 06:00', 90388.65], ['04-04 07:00', 90109.42], ['04-04 08:00', 90175.64], ['04-04 09:00', 90138.02], ['04-04 10:00', 90166.14], ['04-04 11:00', 90309.75], ['04-04 12:00', 90483.65], ['04-04 13:00', 90612.71], ['04-04 14:00', 90541.96], ['04-04 15:00', 91554.05], ['04-04 16:00', 91724.81], ['04-04 17:00', 92353.46], ['04-04 18:00', 92006.22], ['04-04 19:00', 91995.9], ['04-04 20:00', 91896.59]],
        "api_funding_rate": [['04-01 16:00', 5.77e-06, 68876.82], ['04-02 00:00', 3.521e-05, 68086.5], ['04-02 08:00', 8.45e-06, 66888.21], ['04-02 16:00', -7.398e-05, 66819.54], ['04-03 00:00', -8.31e-06, 66869.74], ['04-03 08:00', -5.99e-06, 67008.7], ['04-03 16:00', 3.51e-06, 66809.34], ['04-04 00:00', 3.761e-05, 66930.0], ['04-04 08:00', 4.115e-05, 66983.97], ['04-04 16:00', 1.651e-05, 67357.3]],
        "klines_4h": [["04-03 07:00", 66550.1, 67233.3, 66375.1, 67008.8], ["04-03 11:00", 67008.8, 67258.0, 66644.0, 66983.4], ["04-03 15:00", 66983.5, 67350.0, 66478.5, 66806.1], ["04-03 19:00", 66806.0, 67046.1, 66714.1, 66857.0], ["04-03 23:00", 66857.0, 66946.3, 66791.8, 66930.0], ["04-04 03:00", 66930.0, 66935.3, 66773.3, 66799.1], ["04-04 07:00", 66799.1, 67023.7, 66745.5, 66982.0], ["04-04 11:00", 66982.1, 67223.8, 66874.5, 67128.9], ["04-04 15:00", 67128.9, 67554.5, 67003.7, 67357.3], ["04-04 19:00", 67357.4, 67523.8, 67226.4, 67262.7]],
        "klines_1h": [["04-03 15:00", 66983.5, 67350.0, 66605.9, 66690.4], ["04-03 16:00", 66690.4, 66707.1, 66478.5, 66644.6], ["04-03 17:00", 66644.6, 66968.1, 66600.0, 66900.0], ["04-03 18:00", 66899.9, 66999.0, 66778.9, 66806.1], ["04-03 19:00", 66806.0, 67046.1, 66800.0, 66972.5], ["04-03 20:00", 66972.5, 67040.0, 66714.1, 66811.0], ["04-03 21:00", 66811.0, 66899.7, 66746.9, 66783.7], ["04-03 22:00", 66783.6, 66882.9, 66740.6, 66857.0], ["04-03 23:00", 66857.0, 66888.0, 66800.0, 66800.1], ["04-04 00:00", 66800.0, 66946.3, 66791.8, 66929.5], ["04-04 01:00", 66929.4, 66943.0, 66813.0, 66860.0], ["04-04 02:00", 66859.9, 66930.0, 66800.7, 66930.0], ["04-04 03:00", 66930.0, 66935.3, 66838.9, 66863.4], ["04-04 04:00", 66863.4, 66895.7, 66795.8, 66820.0], ["04-04 05:00", 66820.0, 66891.4, 66773.3, 66814.1], ["04-04 06:00", 66814.0, 66875.4, 66798.8, 66799.1], ["04-04 07:00", 66799.1, 66840.0, 66745.5, 66833.5], ["04-04 08:00", 66833.5, 66908.4, 66817.8, 66871.0], ["04-04 09:00", 66871.0, 67023.7, 66871.0, 66981.5], ["04-04 10:00", 66981.5, 67019.1, 66904.0, 66982.0], ["04-04 11:00", 66982.1, 67025.0, 66874.5, 66907.8], ["04-04 12:00", 66907.8, 66958.2, 66882.1, 66952.1], ["04-04 13:00", 66952.1, 67150.3, 66880.9, 67139.1], ["04-04 14:00", 67139.1, 67223.8, 67050.0, 67128.9], ["04-04 15:00", 67128.9, 67152.5, 67025.2, 67062.0], ["04-04 16:00", 67061.9, 67245.3, 67044.8, 67170.0], ["04-04 17:00", 67170.0, 67193.3, 67003.7, 67177.6], ["04-04 18:00", 67177.5, 67554.5, 67145.6, 67357.3], ["04-04 19:00", 67357.4, 67500.0, 67292.0, 67335.2], ["04-04 20:00", 67335.1, 67386.0, 67249.9, 67302.3]],
        "klines_15m": [["04-04 08:15", 66830.9, 66878.8, 66817.8, 66849.7], ["04-04 08:30", 66849.8, 66908.4, 66844.8, 66868.8], ["04-04 08:45", 66868.9, 66894.7, 66862.9, 66871.0], ["04-04 09:00", 66871.0, 66934.0, 66871.0, 66926.5], ["04-04 09:15", 66926.5, 66940.0, 66876.0, 66920.0], ["04-04 09:30", 66920.0, 66925.0, 66886.8, 66924.9], ["04-04 09:45", 66925.0, 67023.7, 66924.9, 66981.5], ["04-04 10:00", 66981.5, 67004.1, 66955.1, 66973.8], ["04-04 10:15", 66973.8, 66983.0, 66904.0, 66928.0], ["04-04 10:30", 66928.0, 66970.2, 66927.4, 66934.2], ["04-04 10:45", 66934.2, 67019.1, 66919.1, 66982.0], ["04-04 11:00", 66982.1, 67020.0, 66957.2, 66968.6], ["04-04 11:15", 66968.6, 67025.0, 66964.3, 67017.2], ["04-04 11:30", 67017.3, 67017.3, 66928.6, 66943.0], ["04-04 11:45", 66943.0, 66945.7, 66874.5, 66907.8], ["04-04 12:00", 66907.8, 66957.0, 66882.1, 66948.0], ["04-04 12:15", 66948.1, 66958.2, 66910.4, 66944.8], ["04-04 12:30", 66944.9, 66953.8, 66927.1, 66928.9], ["04-04 12:45", 66929.0, 66954.8, 66928.9, 66952.1], ["04-04 13:00", 66952.1, 66993.3, 66880.9, 66880.9], ["04-04 13:15", 66880.9, 66923.6, 66880.9, 66906.9], ["04-04 13:30", 66906.9, 67039.8, 66894.3, 67008.7], ["04-04 13:45", 67008.7, 67150.3, 67001.0, 67139.1], ["04-04 14:00", 67139.1, 67223.8, 67111.1, 67134.8], ["04-04 14:15", 67134.8, 67134.8, 67068.3, 67092.7], ["04-04 14:30", 67092.8, 67125.5, 67050.0, 67111.1], ["04-04 14:45", 67111.2, 67128.9, 67069.3, 67128.9], ["04-04 15:00", 67128.9, 67152.5, 67048.0, 67084.8], ["04-04 15:15", 67084.8, 67110.0, 67070.6, 67075.1], ["04-04 15:30", 67075.2, 67096.5, 67025.2, 67028.7], ["04-04 15:45", 67028.7, 67083.7, 67028.6, 67062.0], ["04-04 16:00", 67061.9, 67071.9, 67044.8, 67071.9], ["04-04 16:15", 67071.9, 67103.3, 67058.2, 67076.7], ["04-04 16:30", 67076.6, 67245.3, 67061.6, 67210.0], ["04-04 16:45", 67209.9, 67211.1, 67144.6, 67170.0], ["04-04 17:00", 67170.0, 67193.3, 67160.0, 67164.9], ["04-04 17:15", 67165.0, 67178.5, 67160.0, 67160.0], ["04-04 17:30", 67160.0, 67160.1, 67003.7, 67068.7], ["04-04 17:45", 67068.6, 67180.0, 67068.6, 67177.6], ["04-04 18:00", 67177.5, 67554.5, 67145.6, 67351.2], ["04-04 18:15", 67351.3, 67445.5, 67263.6, 67297.2], ["04-04 18:30", 67297.2, 67323.2, 67242.6, 67302.5], ["04-04 18:45", 67302.5, 67359.0, 67267.5, 67357.3], ["04-04 19:00", 67357.4, 67369.0, 67292.2, 67310.9], ["04-04 19:15", 67310.8, 67459.1, 67292.0, 67410.7], ["04-04 19:30", 67410.6, 67487.2, 67350.0, 67487.1], ["04-04 19:45", 67487.2, 67500.0, 67319.3, 67335.2], ["04-04 20:00", 67335.1, 67346.8, 67249.9, 67346.8], ["04-04 20:15", 67346.7, 67386.0, 67318.6, 67362.8], ["04-04 20:30", 67362.8, 67372.6, 67289.9, 67289.9]]
    },

    "R23": {
        "data_15m": {"current_price": 67227.4, "ma5": 67232.55, "ma10": 67276.02, "ma30": 67281.98, "volume": 5900000, "volume_ma5": 22800000, "volume_ma10": 27300000, "net_long": 910.2, "net_short": -1200, "futures_cvd": -10700000, "spot_cvd": 849.6, "taker_ls_ratio": 1.565, "oi": 91800, "oi_delta": -4.4219, "liquidations": {"long": 0, "short": 0}},
        "data_1h": {"current_price": 67227.4, "ma5": 67278.62, "ma10": 67228.9, "ma30": 67000.1, "volume": 94500000, "volume_ma5": 169500000, "volume_ma10": 213400000, "net_long": 10000, "net_short": 6600, "futures_cvd": -6000000, "spot_cvd": -3900, "taker_ls_ratio": 1.565, "oi": 91900, "oi_delta": -130.5, "liquidations": {"long": 183300, "short": 3000}},
        "data_4h": {"current_price": 67227.3, "ma5": 67191.66, "ma10": 67033.41, "ma30": 67304.21, "volume": 94600000, "volume_ma5": 57700000, "volume_ma10": 632800000, "net_long": -27000, "net_short": 16800, "futures_cvd": 25000000, "spot_cvd": -80900, "taker_ls_ratio": 1.565, "oi": 91900, "oi_delta": -130.8, "liquidations": {"long": 183300, "short": 3000}},
        "actual": "DOWN", "move": -750,
        "run_time": "04-04 23:52",
        "whale_acct_ls": 0.8483,
        "api_whale_account": [['04-03 18:00', 0.8821], ['04-03 19:00', 0.8829], ['04-03 20:00', 0.8827], ['04-03 21:00', 0.8817], ['04-03 22:00', 0.8727], ['04-03 23:00', 0.8712], ['04-04 00:00', 0.8727], ['04-04 01:00', 0.8722], ['04-04 02:00', 0.8721], ['04-04 03:00', 0.8741], ['04-04 04:00', 0.8751], ['04-04 05:00', 0.8753], ['04-04 06:00', 0.8736], ['04-04 07:00', 0.8735], ['04-04 08:00', 0.874], ['04-04 09:00', 0.8713], ['04-04 10:00', 0.8711], ['04-04 11:00', 0.8727], ['04-04 12:00', 0.8713], ['04-04 13:00', 0.8713], ['04-04 14:00', 0.8755], ['04-04 15:00', 0.8611], ['04-04 16:00', 0.872], ['04-04 17:00', 0.8507], ['04-04 18:00', 0.848], ['04-04 19:00', 0.8492], ['04-04 20:00', 0.8483], ['04-04 21:00', 0.8466], ['04-04 22:00', 0.852], ['04-04 23:00', 0.8508]],
        "api_whale_position": [['04-03 18:00', 1.7941], ['04-03 19:00', 1.7949], ['04-03 20:00', 1.8161], ['04-03 21:00', 1.8161], ['04-03 22:00', 1.8193], ['04-03 23:00', 1.8145], ['04-04 00:00', 1.8129], ['04-04 01:00', 1.8137], ['04-04 02:00', 1.8129], ['04-04 03:00', 1.8019], ['04-04 04:00', 1.805], ['04-04 05:00', 1.8058], ['04-04 06:00', 1.809], ['04-04 07:00', 1.7964], ['04-04 08:00', 1.7678], ['04-04 09:00', 1.7609], ['04-04 10:00', 1.7579], ['04-04 11:00', 1.7563], ['04-04 12:00', 1.7203], ['04-04 13:00', 1.7093], ['04-04 14:00', 1.7093], ['04-04 15:00', 1.6961], ['04-04 16:00', 1.6567], ['04-04 17:00', 1.6483], ['04-04 18:00', 1.6344], ['04-04 19:00', 1.6274], ['04-04 20:00', 1.6254], ['04-04 21:00', 1.624], ['04-04 22:00', 1.6185], ['04-04 23:00', 1.6164]],
        "api_open_interest": [['04-03 18:00', 90415.2], ['04-03 19:00', 90344.98], ['04-03 20:00', 90245.53], ['04-03 21:00', 90244.79], ['04-03 22:00', 90316.0], ['04-03 23:00', 90346.16], ['04-04 00:00', 90276.77], ['04-04 01:00', 90404.57], ['04-04 02:00', 90435.17], ['04-04 03:00', 90444.29], ['04-04 04:00', 90396.92], ['04-04 05:00', 90382.03], ['04-04 06:00', 90388.65], ['04-04 07:00', 90109.42], ['04-04 08:00', 90175.64], ['04-04 09:00', 90138.02], ['04-04 10:00', 90166.14], ['04-04 11:00', 90309.75], ['04-04 12:00', 90483.65], ['04-04 13:00', 90612.71], ['04-04 14:00', 90541.96], ['04-04 15:00', 91554.05], ['04-04 16:00', 91724.81], ['04-04 17:00', 92353.46], ['04-04 18:00', 92006.22], ['04-04 19:00', 91995.9], ['04-04 20:00', 91896.59], ['04-04 21:00', 91754.32], ['04-04 22:00', 91540.33], ['04-04 23:00', 91493.24]],
        "api_funding_rate": [['04-01 16:00', 5.77e-06, 68876.82], ['04-02 00:00', 3.521e-05, 68086.5], ['04-02 08:00', 8.45e-06, 66888.21], ['04-02 16:00', -7.398e-05, 66819.54], ['04-03 00:00', -8.31e-06, 66869.74], ['04-03 08:00', -5.99e-06, 67008.7], ['04-03 16:00', 3.51e-06, 66809.34], ['04-04 00:00', 3.761e-05, 66930.0], ['04-04 08:00', 4.115e-05, 66983.97], ['04-04 16:00', 1.651e-05, 67357.3]],
        "klines_4h": [["04-03 11:00", 67008.8, 67258.0, 66644.0, 66983.4], ["04-03 15:00", 66983.5, 67350.0, 66478.5, 66806.1], ["04-03 19:00", 66806.0, 67046.1, 66714.1, 66857.0], ["04-03 23:00", 66857.0, 66946.3, 66791.8, 66930.0], ["04-04 03:00", 66930.0, 66935.3, 66773.3, 66799.1], ["04-04 07:00", 66799.1, 67023.7, 66745.5, 66982.0], ["04-04 11:00", 66982.1, 67223.8, 66874.5, 67128.9], ["04-04 15:00", 67128.9, 67554.5, 67003.7, 67357.3], ["04-04 19:00", 67357.4, 67523.8, 67226.4, 67262.7], ["04-04 23:00", 67262.8, 67269.4, 67150.6, 67244.4]],
        "klines_1h": [["04-03 18:00", 66899.9, 66999.0, 66778.9, 66806.1], ["04-03 19:00", 66806.0, 67046.1, 66800.0, 66972.5], ["04-03 20:00", 66972.5, 67040.0, 66714.1, 66811.0], ["04-03 21:00", 66811.0, 66899.7, 66746.9, 66783.7], ["04-03 22:00", 66783.6, 66882.9, 66740.6, 66857.0], ["04-03 23:00", 66857.0, 66888.0, 66800.0, 66800.1], ["04-04 00:00", 66800.0, 66946.3, 66791.8, 66929.5], ["04-04 01:00", 66929.4, 66943.0, 66813.0, 66860.0], ["04-04 02:00", 66859.9, 66930.0, 66800.7, 66930.0], ["04-04 03:00", 66930.0, 66935.3, 66838.9, 66863.4], ["04-04 04:00", 66863.4, 66895.7, 66795.8, 66820.0], ["04-04 05:00", 66820.0, 66891.4, 66773.3, 66814.1], ["04-04 06:00", 66814.0, 66875.4, 66798.8, 66799.1], ["04-04 07:00", 66799.1, 66840.0, 66745.5, 66833.5], ["04-04 08:00", 66833.5, 66908.4, 66817.8, 66871.0], ["04-04 09:00", 66871.0, 67023.7, 66871.0, 66981.5], ["04-04 10:00", 66981.5, 67019.1, 66904.0, 66982.0], ["04-04 11:00", 66982.1, 67025.0, 66874.5, 66907.8], ["04-04 12:00", 66907.8, 66958.2, 66882.1, 66952.1], ["04-04 13:00", 66952.1, 67150.3, 66880.9, 67139.1], ["04-04 14:00", 67139.1, 67223.8, 67050.0, 67128.9], ["04-04 15:00", 67128.9, 67152.5, 67025.2, 67062.0], ["04-04 16:00", 67061.9, 67245.3, 67044.8, 67170.0], ["04-04 17:00", 67170.0, 67193.3, 67003.7, 67177.6], ["04-04 18:00", 67177.5, 67554.5, 67145.6, 67357.3], ["04-04 19:00", 67357.4, 67500.0, 67292.0, 67335.2], ["04-04 20:00", 67335.1, 67386.0, 67249.9, 67302.3], ["04-04 21:00", 67302.3, 67350.0, 67226.4, 67265.7], ["04-04 22:00", 67265.6, 67523.8, 67245.6, 67262.7], ["04-04 23:00", 67262.8, 67269.4, 67150.6, 67237.2]],
        "klines_15m": [["04-04 11:30", 67017.3, 67017.3, 66928.6, 66943.0], ["04-04 11:45", 66943.0, 66945.7, 66874.5, 66907.8], ["04-04 12:00", 66907.8, 66957.0, 66882.1, 66948.0], ["04-04 12:15", 66948.1, 66958.2, 66910.4, 66944.8], ["04-04 12:30", 66944.9, 66953.8, 66927.1, 66928.9], ["04-04 12:45", 66929.0, 66954.8, 66928.9, 66952.1], ["04-04 13:00", 66952.1, 66993.3, 66880.9, 66880.9], ["04-04 13:15", 66880.9, 66923.6, 66880.9, 66906.9], ["04-04 13:30", 66906.9, 67039.8, 66894.3, 67008.7], ["04-04 13:45", 67008.7, 67150.3, 67001.0, 67139.1], ["04-04 14:00", 67139.1, 67223.8, 67111.1, 67134.8], ["04-04 14:15", 67134.8, 67134.8, 67068.3, 67092.7], ["04-04 14:30", 67092.8, 67125.5, 67050.0, 67111.1], ["04-04 14:45", 67111.2, 67128.9, 67069.3, 67128.9], ["04-04 15:00", 67128.9, 67152.5, 67048.0, 67084.8], ["04-04 15:15", 67084.8, 67110.0, 67070.6, 67075.1], ["04-04 15:30", 67075.2, 67096.5, 67025.2, 67028.7], ["04-04 15:45", 67028.7, 67083.7, 67028.6, 67062.0], ["04-04 16:00", 67061.9, 67071.9, 67044.8, 67071.9], ["04-04 16:15", 67071.9, 67103.3, 67058.2, 67076.7], ["04-04 16:30", 67076.6, 67245.3, 67061.6, 67210.0], ["04-04 16:45", 67209.9, 67211.1, 67144.6, 67170.0], ["04-04 17:00", 67170.0, 67193.3, 67160.0, 67164.9], ["04-04 17:15", 67165.0, 67178.5, 67160.0, 67160.0], ["04-04 17:30", 67160.0, 67160.1, 67003.7, 67068.7], ["04-04 17:45", 67068.6, 67180.0, 67068.6, 67177.6], ["04-04 18:00", 67177.5, 67554.5, 67145.6, 67351.2], ["04-04 18:15", 67351.3, 67445.5, 67263.6, 67297.2], ["04-04 18:30", 67297.2, 67323.2, 67242.6, 67302.5], ["04-04 18:45", 67302.5, 67359.0, 67267.5, 67357.3], ["04-04 19:00", 67357.4, 67369.0, 67292.2, 67310.9], ["04-04 19:15", 67310.8, 67459.1, 67292.0, 67410.7], ["04-04 19:30", 67410.6, 67487.2, 67350.0, 67487.1], ["04-04 19:45", 67487.2, 67500.0, 67319.3, 67335.2], ["04-04 20:00", 67335.1, 67346.8, 67249.9, 67346.8], ["04-04 20:15", 67346.7, 67386.0, 67318.6, 67362.8], ["04-04 20:30", 67362.8, 67372.6, 67289.9, 67289.9], ["04-04 20:45", 67290.0, 67314.8, 67283.6, 67302.3], ["04-04 21:00", 67302.3, 67314.9, 67252.0, 67304.4], ["04-04 21:15", 67304.4, 67350.0, 67300.5, 67300.5], ["04-04 21:30", 67300.6, 67300.6, 67256.7, 67256.8], ["04-04 21:45", 67256.7, 67296.5, 67226.4, 67265.7], ["04-04 22:00", 67265.6, 67472.5, 67265.6, 67468.3], ["04-04 22:15", 67468.3, 67523.8, 67331.4, 67332.9], ["04-04 22:30", 67332.9, 67343.9, 67245.6, 67274.1], ["04-04 22:45", 67274.1, 67298.2, 67245.7, 67262.7], ["04-04 23:00", 67262.8, 67262.8, 67150.6, 67200.2], ["04-04 23:15", 67200.3, 67245.0, 67200.2, 67237.6], ["04-04 23:30", 67237.6, 67269.4, 67220.3, 67234.6], ["04-04 23:45", 67234.6, 67264.6, 67230.9, 67230.9]]
    },

    "R24": {
        "data_15m": {"current_price": 66961.0, "ma5": 67004.71, "ma10": 66987.34, "ma30": 66921.61, "volume": 16200000, "volume_ma5": 30500000, "volume_ma10": 28700000, "net_long": -153.9, "net_short": -592.0, "futures_cvd": 4000000, "spot_cvd": 1200, "taker_ls_ratio": 1.572, "oi": 89900, "oi_delta": 8.3984, "liquidations": {"long": 0, "short": 0}},
        "data_1h": {"current_price": 66961.0, "ma5": 66929.84, "ma10": 66964.98, "ma30": 67103.89, "volume": 65500000, "volume_ma5": 126500000, "volume_ma10": 162700000, "net_long": 8200, "net_short": 6500, "futures_cvd": -5500000, "spot_cvd": -3900, "taker_ls_ratio": 1.572, "oi": 89900, "oi_delta": 39.5, "liquidations": {"long": 737.4, "short": 0}},
        "data_4h": {"current_price": 66965.7, "ma5": 67080.02, "ma10": 67059.73, "ma30": 67278.8, "volume": 440400000, "volume_ma5": 588600000, "volume_ma10": 556500000, "net_long": -27200, "net_short": 16000, "futures_cvd": 28200000, "spot_cvd": -81900, "taker_ls_ratio": 1.572, "oi": 89800, "oi_delta": 66.0, "liquidations": {"long": 2100, "short": 76000}},
        "actual": "UP", "move": 2622,
        "run_time": "04-05 14:37",
        "whale_acct_ls": 0.8529,
        "api_whale_account": [["04-04 09:00", 0.8736], ["04-04 10:00", 0.8735], ["04-04 11:00", 0.874], ["04-04 12:00", 0.8713], ["04-04 13:00", 0.8711], ["04-04 14:00", 0.8727], ["04-04 15:00", 0.8713], ["04-04 16:00", 0.8713], ["04-04 17:00", 0.8755], ["04-04 18:00", 0.8611], ["04-04 19:00", 0.872], ["04-04 20:00", 0.8507], ["04-04 21:00", 0.848], ["04-04 22:00", 0.8492], ["04-04 23:00", 0.8483], ["04-05 00:00", 0.8466], ["04-05 01:00", 0.852], ["04-05 02:00", 0.8508], ["04-05 03:00", 0.849], ["04-05 04:00", 0.8467], ["04-05 05:00", 0.8519], ["04-05 06:00", 0.8581], ["04-05 07:00", 0.8576], ["04-05 08:00", 0.858], ["04-05 09:00", 0.8553], ["04-05 10:00", 0.8491], ["04-05 11:00", 0.8546], ["04-05 12:00", 0.8555], ["04-05 13:00", 0.8528], ["04-05 14:00", 0.8529]],
        "api_whale_position": [["04-04 09:00", 1.7285], ["04-04 10:00", 1.7226], ["04-04 11:00", 1.6998], ["04-04 12:00", 1.6882], ["04-04 13:00", 1.6838], ["04-04 14:00", 1.6932], ["04-04 15:00", 1.6525], ["04-04 16:00", 1.6385], ["04-04 17:00", 1.6385], ["04-04 18:00", 1.6219], ["04-04 19:00", 1.6076], ["04-04 20:00", 1.5994], ["04-04 21:00", 1.5813], ["04-04 22:00", 1.5694], ["04-04 23:00", 1.57], ["04-05 00:00", 1.5641], ["04-05 01:00", 1.5628], ["04-05 02:00", 1.5602], ["04-05 03:00", 1.551], ["04-05 04:00", 1.5549], ["04-05 05:00", 1.5439], ["04-05 06:00", 1.5615], ["04-05 07:00", 1.5575], ["04-05 08:00", 1.5562], ["04-05 09:00", 1.5536], ["04-05 10:00", 1.5967], ["04-05 11:00", 1.5907], ["04-05 12:00", 1.5994], ["04-05 13:00", 1.592], ["04-05 14:00", 1.5813]],
        "api_open_interest": [["04-04 09:00", 90388.652], ["04-04 10:00", 90109.418], ["04-04 11:00", 90175.644], ["04-04 12:00", 90138.018], ["04-04 13:00", 90166.136], ["04-04 14:00", 90309.753], ["04-04 15:00", 90483.649], ["04-04 16:00", 90612.712], ["04-04 17:00", 90541.957], ["04-04 18:00", 91554.052], ["04-04 19:00", 91724.811], ["04-04 20:00", 92353.457], ["04-04 21:00", 92006.221], ["04-04 22:00", 91995.904], ["04-04 23:00", 91896.585], ["04-05 00:00", 91754.324], ["04-05 01:00", 91540.327], ["04-05 02:00", 91493.237], ["04-05 03:00", 91402.972], ["04-05 04:00", 91389.739], ["04-05 05:00", 91380.3], ["04-05 06:00", 91286.249], ["04-05 07:00", 91326.964], ["04-05 08:00", 91416.432], ["04-05 09:00", 91202.121], ["04-05 10:00", 89986.007], ["04-05 11:00", 89846.134], ["04-05 12:00", 89888.518], ["04-05 13:00", 89839.739], ["04-05 14:00", 89872.635]],
        "api_funding_rate": [["04-02 11:00", 8.45e-06, 66888.20861594], ["04-02 19:00", -7.398e-05, 66819.54021739], ["04-03 03:00", -8.31e-06, 66869.74346667], ["04-03 11:00", -5.99e-06, 67008.7], ["04-03 19:00", 3.51e-06, 66809.33805072], ["04-04 03:00", 3.761e-05, 66930.0], ["04-04 11:00", 4.115e-05, 66983.97256934], ["04-04 19:00", 1.651e-05, 67357.3], ["04-05 03:00", 2.407e-05, 67271.0], ["04-05 11:00", 3.812e-05, 66787.4]],
        "klines_4h": [["04-03 15:00", 66983.5, 67350.0, 66478.5, 66806.1], ["04-03 19:00", 66806.0, 67046.1, 66714.1, 66857.0], ["04-03 23:00", 66857.0, 66946.3, 66791.8, 66930.0], ["04-04 03:00", 66930.0, 66935.3, 66773.3, 66799.1], ["04-04 07:00", 66799.1, 67023.7, 66745.5, 66982.0], ["04-04 11:00", 66982.1, 67223.8, 66874.5, 67128.9], ["04-04 15:00", 67128.9, 67554.5, 67003.7, 67357.3], ["04-04 19:00", 67357.4, 67523.8, 67226.4, 67262.7], ["04-04 23:00", 67262.8, 67452.7, 67150.6, 67271.0], ["04-05 03:00", 67271.1, 67279.2, 66900.0, 67113.5], ["04-05 07:00", 67113.4, 67160.0, 66575.5, 66787.4], ["04-05 11:00", 66787.4, 67132.8, 66782.1, 66949.7]],
        "klines_1h": [["04-04 09:00", 66871.0, 67023.7, 66871.0, 66981.5], ["04-04 10:00", 66981.5, 67019.1, 66904.0, 66982.0], ["04-04 11:00", 66982.1, 67025.0, 66874.5, 66907.8], ["04-04 12:00", 66907.8, 66958.2, 66882.1, 66952.1], ["04-04 13:00", 66952.1, 67150.3, 66880.9, 67139.1], ["04-04 14:00", 67139.1, 67223.8, 67050.0, 67128.9], ["04-04 15:00", 67128.9, 67152.5, 67025.2, 67062.0], ["04-04 16:00", 67061.9, 67245.3, 67044.8, 67170.0], ["04-04 17:00", 67170.0, 67193.3, 67003.7, 67177.6], ["04-04 18:00", 67177.5, 67554.5, 67145.6, 67357.3], ["04-04 19:00", 67357.4, 67500.0, 67292.0, 67335.2], ["04-04 20:00", 67335.1, 67386.0, 67249.9, 67302.3], ["04-04 21:00", 67302.3, 67350.0, 67226.4, 67265.7], ["04-04 22:00", 67265.6, 67523.8, 67245.6, 67262.7], ["04-04 23:00", 67262.8, 67269.4, 67150.6, 67240.2], ["04-05 00:00", 67240.2, 67452.7, 67180.9, 67325.0], ["04-05 01:00", 67325.0, 67438.7, 67305.4, 67368.9], ["04-05 02:00", 67368.9, 67371.4, 67214.2, 67271.0], ["04-05 03:00", 67271.1, 67279.2, 67131.1, 67177.0], ["04-05 04:00", 67177.0, 67200.0, 67045.2, 67060.6], ["04-05 05:00", 67060.6, 67154.0, 66900.0, 67144.3], ["04-05 06:00", 67144.3, 67166.9, 67058.0, 67113.5], ["04-05 07:00", 67113.4, 67160.0, 67034.8, 67066.2], ["04-05 08:00", 67066.3, 67127.5, 66822.8, 66905.1], ["04-05 09:00", 66905.2, 66918.6, 66575.5, 66771.6], ["04-05 10:00", 66771.6, 66887.1, 66685.3, 66787.4], ["04-05 11:00", 66787.4, 66910.0, 66782.1, 66892.5], ["04-05 12:00", 66892.6, 67020.4, 66862.3, 66996.0], ["04-05 13:00", 66996.1, 67132.8, 66928.1, 67012.3], ["04-05 14:00", 67012.4, 67054.1, 66934.4, 66951.1]],
    },

    "R25": {
        "data_15m": {"current_price": 67203.6, "ma5": 67264.96, "ma10": 67190.95, "ma30": 66993.05, "volume": 33700000, "volume_ma5": 60000000, "volume_ma10": 142800000, "net_long": 1300, "net_short": -3800, "futures_cvd": 13200000, "spot_cvd": 2400, "taker_ls_ratio": 1.585, "oi": 90000, "oi_delta": 52.4, "liquidations": {"long": 11800, "short": 0}},
        "data_1h": {"current_price": 67190.8, "ma5": 66994.08, "ma10": 66963.11, "ma30": 67104.53, "volume": 212100000, "volume_ma5": 412700000, "volume_ma10": 271800000, "net_long": 8600, "net_short": 6400, "futures_cvd": -1400000, "spot_cvd": -4400, "taker_ls_ratio": 1.585, "oi": 89800, "oi_delta": 319.5, "liquidations": {"long": 17500, "short": 2500}},
        "data_4h": {"current_price": 67177.0, "ma5": 67065.73, "ma10": 67133.05, "ma30": 67277.50, "volume": 212500000, "volume_ma5": 783700000, "volume_ma10": 707000000, "net_long": -25900, "net_short": 14500, "futures_cvd": 31200000, "spot_cvd": -81700, "taker_ls_ratio": 1.585, "oi": 89800, "oi_delta": 314.3, "liquidations": {"long": 17500, "short": 2500}},
        "actual": "UP", "move": 2392,
        "run_time": "04-05 20:00",
        "whale_acct_ls": 1.5833,
        "api_whale_account": [["04-04 14:00", 1.7563], ["04-04 15:00", 1.7203], ["04-04 16:00", 1.7093], ["04-04 17:00", 1.7093], ["04-04 18:00", 1.6961], ["04-04 19:00", 1.6567], ["04-04 20:00", 1.6483], ["04-04 21:00", 1.6344], ["04-04 22:00", 1.6274], ["04-04 23:00", 1.6254], ["04-05 00:00", 1.6240], ["04-05 01:00", 1.6185], ["04-05 02:00", 1.6164], ["04-05 03:00", 1.6103], ["04-05 04:00", 1.6096], ["04-05 05:00", 1.6082], ["04-05 06:00", 1.6371], ["04-05 07:00", 1.6357], ["04-05 08:00", 1.6357], ["04-05 09:00", 1.6378], ["04-05 10:00", 1.6947], ["04-05 11:00", 1.6932], ["04-05 12:00", 1.6991], ["04-05 13:00", 1.6889], ["04-05 14:00", 1.6788], ["04-05 15:00", 1.6702], ["04-05 16:00", 1.6998], ["04-05 17:00", 1.7352], ["04-05 18:00", 1.7360], ["04-05 19:00", 1.6695]],
        "api_whale_position": [["04-04 14:00", 1.6932], ["04-04 15:00", 1.6525], ["04-04 16:00", 1.6385], ["04-04 17:00", 1.6385], ["04-04 18:00", 1.6219], ["04-04 19:00", 1.6076], ["04-04 20:00", 1.5994], ["04-04 21:00", 1.5813], ["04-04 22:00", 1.5694], ["04-04 23:00", 1.5700], ["04-05 00:00", 1.5641], ["04-05 01:00", 1.5628], ["04-05 02:00", 1.5602], ["04-05 03:00", 1.5510], ["04-05 04:00", 1.5549], ["04-05 05:00", 1.5439], ["04-05 06:00", 1.5615], ["04-05 07:00", 1.5575], ["04-05 08:00", 1.5562], ["04-05 09:00", 1.5536], ["04-05 10:00", 1.5967], ["04-05 11:00", 1.5907], ["04-05 12:00", 1.5994], ["04-05 13:00", 1.5920], ["04-05 14:00", 1.5813], ["04-05 15:00", 1.5667], ["04-05 16:00", 1.5913], ["04-05 17:00", 1.6254], ["04-05 18:00", 1.6281], ["04-05 19:00", 1.5833]],
        "api_open_interest": [["04-04 14:00", 90309.753], ["04-04 15:00", 90483.649], ["04-04 16:00", 90612.712], ["04-04 17:00", 90541.957], ["04-04 18:00", 91554.052], ["04-04 19:00", 91724.811], ["04-04 20:00", 92353.457], ["04-04 21:00", 92006.221], ["04-04 22:00", 91995.904], ["04-04 23:00", 91896.585], ["04-05 00:00", 91754.324], ["04-05 01:00", 91540.327], ["04-05 02:00", 91493.237], ["04-05 03:00", 91402.972], ["04-05 04:00", 91389.739], ["04-05 05:00", 91380.300], ["04-05 06:00", 91286.249], ["04-05 07:00", 91326.964], ["04-05 08:00", 91416.432], ["04-05 09:00", 91202.121], ["04-05 10:00", 89986.007], ["04-05 11:00", 89846.134], ["04-05 12:00", 89888.518], ["04-05 13:00", 89839.739], ["04-05 14:00", 89872.635], ["04-05 15:00", 89969.389], ["04-05 16:00", 89961.692], ["04-05 17:00", 90058.913], ["04-05 18:00", 90143.795], ["04-05 19:00", 89758.696]],
        "api_funding_rate": [["04-02 19:00", -7.398e-05, 66819.54021739], ["04-03 03:00", -8.31e-06, 66869.74346667], ["04-03 11:00", -5.99e-06, 67008.7], ["04-03 19:00", 3.51e-06, 66809.33805072], ["04-04 03:00", 3.761e-05, 66930.0], ["04-04 11:00", 4.115e-05, 66983.97256934], ["04-04 19:00", 1.651e-05, 67357.3], ["04-05 03:00", 2.407e-05, 67271.0], ["04-05 11:00", 3.812e-05, 66787.4], ["04-05 19:00", 1.889e-05, 67278.50018741]],
        "klines_4h": [["04-04 07:00", 66799.1, 67023.7, 66745.5, 66982.0], ["04-04 11:00", 66982.1, 67223.8, 66874.5, 67128.9], ["04-04 15:00", 67128.9, 67554.5, 67003.7, 67357.3], ["04-04 19:00", 67357.4, 67523.8, 67226.4, 67262.7], ["04-04 23:00", 67262.8, 67452.7, 67150.6, 67271.0], ["04-05 03:00", 67271.1, 67279.2, 66900.0, 67113.5], ["04-05 07:00", 67113.4, 67160.0, 66575.5, 66787.4], ["04-05 11:00", 66787.4, 67132.8, 66782.1, 66972.7], ["04-05 15:00", 66972.7, 67828.6, 66650.0, 67272.2], ["04-05 19:00", 67272.2, 67381.0, 67201.2, 67201.2]],
    },

    "R26": {
        "data_15m": {"current_price": 69229.9, "ma5": 69119.42, "ma10": 69019.62, "ma30": 69065.43, "volume": 11400000, "volume_ma5": 78100000, "volume_ma10": 84800000, "net_long": 6700, "net_short": 2500, "futures_cvd": 26400000, "spot_cvd": 1800, "taker_ls_ratio": 1.068, "oi": 94500, "oi_delta": 30.9, "liquidations": {"long": 138.4, "short": 0}},
        "data_1h": {"current_price": 69239.3, "ma5": 69112.20, "ma10": 69096.96, "ma30": 67788.91, "volume": 157000000, "volume_ma5": 262900000, "volume_ma10": 469300000, "net_long": 3000, "net_short": 10600, "futures_cvd": -7500000, "spot_cvd": -5100, "taker_ls_ratio": 1.068, "oi": 94200, "oi_delta": 348.2, "liquidations": {"long": 36900, "short": 52100}},
        "data_4h": {"current_price": 69230.1, "ma5": 68748.91, "ma10": 67915.98, "ma30": 67372.37, "volume": 157700000, "volume_ma5": 1370000000, "volume_ma10": 1090000000, "net_long": -15700, "net_short": 18600, "futures_cvd": 45200000, "spot_cvd": -81700, "taker_ls_ratio": 1.068, "oi": 94200, "oi_delta": 349.2, "liquidations": {"long": 36900, "short": 52100}},
        "actual": "UP", "move": 1093,
        "run_time": "04-06 12:00",
        "whale_acct_ls": 1.0734,
        "api_whale_account": [["04-05 06:00", 0.8581], ["04-05 07:00", 0.8576], ["04-05 08:00", 0.8580], ["04-05 09:00", 0.8553], ["04-05 10:00", 0.8491], ["04-05 11:00", 0.8546], ["04-05 12:00", 0.8555], ["04-05 13:00", 0.8528], ["04-05 14:00", 0.8529], ["04-05 15:00", 0.8540], ["04-05 16:00", 0.8557], ["04-05 17:00", 0.8559], ["04-05 18:00", 0.8516], ["04-05 19:00", 0.8565], ["04-05 20:00", 0.8506], ["04-05 21:00", 0.8476], ["04-05 22:00", 0.8513], ["04-05 23:00", 0.8536], ["04-06 00:00", 0.8652], ["04-06 01:00", 0.8706], ["04-06 02:00", 0.8853], ["04-06 03:00", 0.8819], ["04-06 04:00", 0.8781], ["04-06 05:00", 0.8749], ["04-06 06:00", 0.8778], ["04-06 07:00", 0.8743], ["04-06 08:00", 0.8771], ["04-06 09:00", 0.8768], ["04-06 10:00", 0.8763], ["04-06 11:00", 0.8952]],
        "api_whale_position": [["04-05 06:00", 1.5615], ["04-05 07:00", 1.5575], ["04-05 08:00", 1.5562], ["04-05 09:00", 1.5536], ["04-05 10:00", 1.5967], ["04-05 11:00", 1.5907], ["04-05 12:00", 1.5994], ["04-05 13:00", 1.5920], ["04-05 14:00", 1.5813], ["04-05 15:00", 1.5667], ["04-05 16:00", 1.5913], ["04-05 17:00", 1.6254], ["04-05 18:00", 1.6281], ["04-05 19:00", 1.5833], ["04-05 20:00", 1.5873], ["04-05 21:00", 1.5780], ["04-05 22:00", 1.5727], ["04-05 23:00", 1.5641], ["04-06 00:00", 1.5562], ["04-06 01:00", 1.5452], ["04-06 02:00", 1.4907], ["04-06 03:00", 1.3068], ["04-06 04:00", 1.2262], ["04-06 05:00", 1.1668], ["04-06 06:00", 1.1459], ["04-06 07:00", 1.1110], ["04-06 08:00", 1.0929], ["04-06 09:00", 1.0872], ["04-06 10:00", 1.0846], ["04-06 11:00", 1.0734]],
        "api_open_interest": [["04-05 06:00", 91286.249], ["04-05 07:00", 91326.964], ["04-05 08:00", 91416.432], ["04-05 09:00", 91202.121], ["04-05 10:00", 89986.007], ["04-05 11:00", 89846.134], ["04-05 12:00", 89888.518], ["04-05 13:00", 89839.739], ["04-05 14:00", 89872.635], ["04-05 15:00", 89969.389], ["04-05 16:00", 89961.692], ["04-05 17:00", 90058.913], ["04-05 18:00", 90143.795], ["04-05 19:00", 89758.696], ["04-05 20:00", 90037.459], ["04-05 21:00", 90095.581], ["04-05 22:00", 90145.588], ["04-05 23:00", 90199.031], ["04-06 00:00", 89940.642], ["04-06 01:00", 89632.776], ["04-06 02:00", 90072.929], ["04-06 03:00", 91034.347], ["04-06 04:00", 91483.957], ["04-06 05:00", 91669.248], ["04-06 06:00", 92064.476], ["04-06 07:00", 92698.032], ["04-06 08:00", 93147.432], ["04-06 09:00", 93323.513], ["04-06 10:00", 93179.738], ["04-06 11:00", 94186.889]],
        "api_funding_rate": [["04-03 11:00", -5.99e-06, 67008.7], ["04-03 19:00", 3.51e-06, 66809.33805072], ["04-04 03:00", 3.761e-05, 66930.0], ["04-04 11:00", 4.115e-05, 66983.97256934], ["04-04 19:00", 1.651e-05, 67357.3], ["04-05 03:00", 2.407e-05, 67271.0], ["04-05 11:00", 3.812e-05, 66787.4], ["04-05 19:00", 1.889e-05, 67278.50018741], ["04-06 03:00", 7.073e-05, 68997.4], ["04-06 11:00", 5.544e-05, 69087.63507246]],
        "klines_4h": [["04-04 23:00", 67262.8, 67452.7, 67150.6, 67271.0], ["04-05 03:00", 67271.1, 67279.2, 66900.0, 67113.5], ["04-05 07:00", 67113.4, 67160.0, 66575.5, 66787.4], ["04-05 11:00", 66787.4, 67132.8, 66782.1, 66972.7], ["04-05 15:00", 66972.7, 67828.6, 66650.0, 67272.2], ["04-05 19:00", 67272.2, 67540.0, 67132.2, 67329.1], ["04-05 23:00", 67329.1, 69108.0, 67302.4, 68997.9], ["04-06 03:00", 68997.9, 69583.0, 68740.2, 69092.4], ["04-06 07:00", 69092.3, 69338.2, 68769.6, 69089.7], ["04-06 11:00", 69089.8, 69225.0, 69047.7, 69199.9]],
        "klines_1h": [["04-05 06:00", 67144.3, 67166.9, 67058.0, 67113.5], ["04-05 07:00", 67113.4, 67160.0, 67034.8, 67066.2], ["04-05 08:00", 67066.3, 67127.5, 66822.8, 66905.1], ["04-05 09:00", 66905.2, 66918.6, 66575.5, 66771.6], ["04-05 10:00", 66771.6, 66887.1, 66685.3, 66787.4], ["04-05 11:00", 66787.4, 66910.0, 66782.1, 66892.5], ["04-05 12:00", 66892.6, 67020.4, 66862.3, 66996.0], ["04-05 13:00", 66996.1, 67132.8, 66928.1, 67012.3], ["04-05 14:00", 67012.4, 67054.1, 66934.4, 66972.7], ["04-05 15:00", 66972.7, 66972.7, 66650.0, 66751.4], ["04-05 16:00", 66751.5, 66892.9, 66666.0, 66863.4], ["04-05 17:00", 66863.5, 66940.2, 66783.1, 66892.5], ["04-05 18:00", 66892.6, 67828.6, 66792.6, 67272.2], ["04-05 19:00", 67272.2, 67381.0, 67132.2, 67178.8], ["04-05 20:00", 67178.9, 67376.3, 67150.0, 67342.2], ["04-05 21:00", 67342.2, 67428.2, 67246.6, 67381.1], ["04-05 22:00", 67381.2, 67540.0, 67250.0, 67329.1], ["04-05 23:00", 67329.1, 67681.6, 67302.4, 67636.7], ["04-06 00:00", 67636.7, 67672.9, 67377.2, 67519.5], ["04-06 01:00", 67519.5, 68347.9, 67313.6, 68313.0], ["04-06 02:00", 68313.0, 69108.0, 68232.0, 68997.9], ["04-06 03:00", 68997.9, 69583.0, 68997.9, 69051.9], ["04-06 04:00", 69051.9, 69103.1, 68761.0, 68782.9], ["04-06 05:00", 68782.9, 69386.2, 68740.2, 69183.6], ["04-06 06:00", 69183.6, 69223.4, 69026.6, 69092.4], ["04-06 07:00", 69092.3, 69188.0, 68943.3, 69107.6], ["04-06 08:00", 69107.6, 69214.5, 69052.0, 69167.1], ["04-06 09:00", 69167.0, 69338.2, 68769.6, 68958.7], ["04-06 10:00", 68958.8, 69190.8, 68800.0, 69089.7], ["04-06 11:00", 69089.8, 69225.0, 69047.7, 69191.6]],
    },

    "R27": {
        "data_15m": {"current_price": 69680.1, "ma5": 69701.07, "ma10": 69658.42, "ma30": 69593.29, "volume": 8500000, "volume_ma5": 72200000, "volume_ma10": 144500000, "net_long": 7400, "net_short": 1800, "futures_cvd": 26200000, "spot_cvd": 3900, "taker_ls_ratio": 1.038, "oi": 95100, "oi_delta": -12.7, "liquidations": {"long": 0, "short": 0}},
        "data_1h": {"current_price": 69679.8, "ma5": 69703.15, "ma10": 69627.51, "ma30": 68687.58, "volume": 311900000, "volume_ma5": 628500000, "volume_ma10": 584200000, "net_long": 1400, "net_short": 11200, "futures_cvd": -2800000, "spot_cvd": -4400, "taker_ls_ratio": 1.038, "oi": 95100, "oi_delta": -32.4, "liquidations": {"long": 139.4, "short": 47200}},
        "data_4h": {"current_price": 69695.7, "ma5": 69472.87, "ma10": 68472.18, "ma30": 67469.89, "volume": 1730000000, "volume_ma5": 1890000000, "volume_ma10": 1610000000, "net_long": -14400, "net_short": 15600, "futures_cvd": 55600000, "spot_cvd": -79300, "taker_ls_ratio": 1.038, "oi": 94100, "oi_delta": 1000, "liquidations": {"long": 12600000, "short": 412700}},
        "actual": "DOWN", "move": -963, "mfe_4h": 963, "mae_4h": 0,
        "run_time": "04-06 17:00",
    },

    "R28": {
        "_note": "P54: Score data placeholder — MFE/MAE P53'ten.",
        "data_15m": {"current_price": 69083.0, "ma5": 69100.0, "ma10": 69150.0, "ma30": 69200.0, "volume": 50000000, "volume_ma5": 60000000, "volume_ma10": 70000000, "net_long": 0, "net_short": 0, "futures_cvd": 0, "spot_cvd": 0, "taker_ls_ratio": 1.0, "oi": 91000, "oi_delta": 0, "liquidations": {"long": 0, "short": 0}},
        "data_1h": {"current_price": 69083.0, "ma5": 69100.0, "ma10": 69150.0, "ma30": 69200.0, "volume": 200000000, "volume_ma5": 250000000, "volume_ma10": 300000000, "net_long": 0, "net_short": 0, "futures_cvd": 0, "spot_cvd": 0, "taker_ls_ratio": 1.0, "oi": 91000, "oi_delta": 0, "liquidations": {"long": 0, "short": 0}},
        "data_4h": {"current_price": 69083.0, "ma5": 69100.0, "ma10": 69150.0, "ma30": 69200.0, "volume": 800000000, "volume_ma5": 900000000, "volume_ma10": 1000000000, "net_long": 0, "net_short": 0, "futures_cvd": 0, "spot_cvd": 0, "taker_ls_ratio": 1.0, "oi": 91000, "oi_delta": 0, "liquidations": {"long": 0, "short": 0}},
        "actual": "DOWN", "move": -963,
        "mfe_4h": 135, "mae_4h": 182,
        "run_time": "04-07 06:00",
    },

    "R29": {
        "_note": "P54: Score data placeholder. MFE/MAE screenshot TAHMİN. SC=SHORT, Eren override LONG.",
        "data_15m": {"current_price": 68024.0, "ma5": 68050.0, "ma10": 68100.0, "ma30": 68200.0, "volume": 40000000, "volume_ma5": 50000000, "volume_ma10": 60000000, "net_long": 0, "net_short": 0, "futures_cvd": 0, "spot_cvd": 0, "taker_ls_ratio": 1.0, "oi": 90000, "oi_delta": 0, "liquidations": {"long": 0, "short": 0}},
        "data_1h": {"current_price": 68024.0, "ma5": 68050.0, "ma10": 68100.0, "ma30": 68200.0, "volume": 180000000, "volume_ma5": 200000000, "volume_ma10": 250000000, "net_long": 0, "net_short": 0, "futures_cvd": 0, "spot_cvd": 0, "taker_ls_ratio": 1.0, "oi": 90000, "oi_delta": 0, "liquidations": {"long": 0, "short": 0}},
        "data_4h": {"current_price": 68024.0, "ma5": 68050.0, "ma10": 68100.0, "ma30": 68200.0, "volume": 700000000, "volume_ma5": 800000000, "volume_ma10": 900000000, "net_long": 0, "net_short": 0, "futures_cvd": 0, "spot_cvd": 0, "taker_ls_ratio": 1.0, "oi": 90000, "oi_delta": 0, "liquidations": {"long": 0, "short": 0}},
        "actual": "UP", "move": 659,
        "mfe_4h": 313, "mae_4h": 972,
        "run_time": "04-07 14:36",
    },

    "R30": {
        "_note": "P55→P56: Leading=GİR LONG (LONG_ANA), SC=LONG GİRME (V9 gecikme). Eren leading'e güvendi. +$2970.",
        "data_15m": {"current_price": 67997.9, "ma5": 68101.62, "ma10": 68262.14, "ma30": 68525.51, "volume": 21917077, "volume_ma5": 211940547, "volume_ma10": 168479602, "net_long": 0.4925, "net_short": 0.5075, "futures_cvd": -2384232, "spot_cvd": 0, "taker_ls_ratio": 1.0682, "oi": 89572, "oi_delta": -167, "liquidations": {"long": 0, "short": 0}, "ma5_slope": -57.634, "cvd_momentum": -4.6989, "ls_slope": 0.12676, "oi_slope": -180.12, "oi_accel": -63.14, "np_slope": 0.00213, "depth_imbalance": 1.3644},
        "data_1h": {"current_price": 68023.8, "ma5": 68221.14, "ma10": 68488.22, "ma30": 69040.03, "volume": 788815993, "volume_ma5": 675666882, "volume_ma10": 467201378, "net_long": 0.4853, "net_short": 0.5147, "futures_cvd": -61208807, "spot_cvd": 0, "taker_ls_ratio": 0.8577, "oi": 90199, "oi_delta": -716, "liquidations": {"long": 0, "short": 0}, "ma5_slope": -72.478, "cvd_momentum": -3.1782, "ls_slope": -0.03662, "oi_slope": -339.68, "oi_accel": -219.94, "np_slope": 0.00299, "depth_imbalance": 1.3644, "whale_acct_ls": 0.9428, "funding_rate": 5.479e-05},
        "data_4h": {"current_price": 68017.2, "ma5": 68496.86, "ma10": 68987.73, "ma30": 67736.6, "volume": 1898560049, "volume_ma5": 1668626870, "volume_ma10": 1806897047, "net_long": 0.474, "net_short": 0.526, "futures_cvd": -97949225, "spot_cvd": 0, "taker_ls_ratio": 1.0247, "oi": 91058, "oi_delta": -6, "liquidations": {"long": 0, "short": 0}, "ma5_slope": -155.542, "cvd_momentum": -2.692, "ls_slope": 0.03155, "oi_slope": -804.43, "oi_accel": 996.97, "np_slope": 0.00112, "depth_imbalance": 1.3644},
        "actual": "UP", "move": 2970,
        "whale_acct_ls": 0.9428,
        "run_time": "04-07 23:30",
    },

    "R31": {
        "actual": "UP",
        "run_time": "04-08 13:00",
        "data_15m": {"current_price": 72412.5, "ma5": 72133.3, "ma10": 71882.9, "ma30": 71744.63, "volume": 315662936, "volume_ma5": 393894946, "volume_ma10": 252579043, "net_long": 0.4974, "net_short": 0.5026, "futures_cvd": -39237570, "spot_cvd": 0, "taker_ls_ratio": 1.6186, "oi": 94763, "oi_delta": 3434, "liquidations": {"long": 0, "short": 0}, "ma5_slope": 92.472, "cvd_momentum": 0.6442, "ls_slope": -0.41961, "oi_slope": 760.06, "oi_accel": 402.58, "np_slope": 0.00115, "depth_imbalance": 1.4898},
        "data_1h": {"current_price": 72421.1, "ma5": 71839.2, "ma10": 71751.17, "ma30": 70236.89, "volume": 1428700806, "volume_ma5": 600269922, "volume_ma10": 444337637, "net_long": 0.4901, "net_short": 0.5099, "futures_cvd": 223560881, "spot_cvd": 0, "taker_ls_ratio": 1.7124, "oi": 91329, "oi_delta": 1729, "liquidations": {"long": 0, "short": 0}, "ma5_slope": 3.344, "cvd_momentum": 10.5324, "ls_slope": 0.16618, "oi_slope": 555.18, "oi_accel": 300.81, "np_slope": -0.00019, "depth_imbalance": 1.4898, "whale_acct_ls": 0.9611, "funding_rate": 4.95e-05},
        "data_4h": {"current_price": 72439.6, "ma5": 71770.32, "ma10": 70161.51, "ma30": 68629.56, "volume": 2189882432, "volume_ma5": 2674208648, "volume_ma10": 2254298569, "net_long": 0.4892, "net_short": 0.5108, "futures_cvd": 423031995, "spot_cvd": 0, "taker_ls_ratio": 1.0292, "oi": 89600, "oi_delta": 977, "liquidations": {"long": 0, "short": 0}, "ma5_slope": 624.35, "cvd_momentum": 15.3658, "ls_slope": -0.04239, "oi_slope": 238.94, "oi_accel": 467.9, "np_slope": -0.00118, "depth_imbalance": 1.4898},
        "whale_acct_ls": 0.9611,
        "api_open_interest": [["04-07 08:00", 91063.57], ["04-07 09:00", 91448.53], ["04-07 10:00", 91510.05], ["04-07 11:00", 91690.58], ["04-07 12:00", 91057.85], ["04-07 13:00", 90915.29], ["04-07 14:00", 90199.31], ["04-07 15:00", 89469.57], ["04-07 16:00", 89372.13], ["04-07 17:00", 89353.15], ["04-07 18:00", 89148.66], ["04-07 19:00", 88639.87], ["04-07 20:00", 88720.45], ["04-07 21:00", 88229.53], ["04-07 22:00", 88418.88], ["04-07 23:00", 88229.13], ["04-08 00:00", 87992.19], ["04-08 01:00", 88067.31], ["04-08 02:00", 88347.5], ["04-08 03:00", 88018.75], ["04-08 04:00", 87928.6], ["04-08 05:00", 87921.12], ["04-08 06:00", 88178.07], ["04-08 07:00", 88391.84], ["04-08 08:00", 88623.24], ["04-08 09:00", 88859.2], ["04-08 10:00", 88988.39], ["04-08 11:00", 89450.1], ["04-08 12:00", 89599.62], ["04-08 13:00", 91329.48]],
        "api_whale_account": [["04-07 08:00", 0.8954], ["04-07 09:00", 0.9016], ["04-07 10:00", 0.8992], ["04-07 11:00", 0.8865], ["04-07 12:00", 0.9013], ["04-07 13:00", 0.9093], ["04-07 14:00", 0.9428], ["04-07 15:00", 0.9733], ["04-07 16:00", 0.9856], ["04-07 17:00", 0.9829], ["04-07 18:00", 0.9788], ["04-07 19:00", 0.985], ["04-07 20:00", 0.9864], ["04-07 21:00", 0.9724], ["04-07 22:00", 0.9538], ["04-07 23:00", 0.9389], ["04-08 00:00", 0.943], ["04-08 01:00", 0.9581], ["04-08 02:00", 0.9536], ["04-08 03:00", 0.976], ["04-08 04:00", 0.9752], ["04-08 05:00", 0.9733], ["04-08 06:00", 0.9627], ["04-08 07:00", 0.9535], ["04-08 08:00", 0.9544], ["04-08 09:00", 0.9631], ["04-08 10:00", 0.9613], ["04-08 11:00", 0.9643], ["04-08 12:00", 0.9578], ["04-08 13:00", 0.9611]],
        "api_whale_position": [["04-07 08:00", 0.8954], ["04-07 09:00", 0.9015], ["04-07 10:00", 0.8993], ["04-07 11:00", 0.8864], ["04-07 12:00", 0.9011], ["04-07 13:00", 0.9091], ["04-07 14:00", 0.9429], ["04-07 15:00", 0.9732], ["04-07 16:00", 0.9857], ["04-07 17:00", 0.9829], ["04-07 18:00", 0.979], ["04-07 19:00", 0.9849], ["04-07 20:00", 0.9865], ["04-07 21:00", 0.9724], ["04-07 22:00", 0.9539], ["04-07 23:00", 0.9387], ["04-08 00:00", 0.9429], ["04-08 01:00", 0.9581], ["04-08 02:00", 0.9535], ["04-08 03:00", 0.9759], ["04-08 04:00", 0.9751], ["04-08 05:00", 0.9732], ["04-08 06:00", 0.9627], ["04-08 07:00", 0.9535], ["04-08 08:00", 0.9543], ["04-08 09:00", 0.9631], ["04-08 10:00", 0.9612], ["04-08 11:00", 0.9643], ["04-08 12:00", 0.9577], ["04-08 13:00", 0.9612]],
        "api_funding_rate": [["04-05 08:00", 3.812e-05, 66787.4], ["04-05 16:00", 1.889e-05, 67278.50018741], ["04-06 00:00", 7.073e-05, 68997.4], ["04-06 08:00", 5.544e-05, 69087.63507246], ["04-06 16:00", 4.23e-06, 69925.85927536], ["04-07 00:00", -3.15e-06, 68822.2], ["04-07 08:00", 3.703e-05, 68594.77686657], ["04-07 16:00", 7.393e-05, 68141.01094203], ["04-08 00:00", 6.02e-05, 71907.34283333], ["04-08 08:00", 1.563e-05, 71612.1]]
    },

    "R32": {
        "_note": "P60: LONG_ANA ERKEN (LS=1.01). Sinyal YANLIŞ + giriş zamanlaması KÖTÜ. Fiyat $66.6k→$72.9k rallisinin tepesinde LONG. 4h%MA30=+4.31% → P60 DEPLASMAN filtresi bu run'ı bloklar. MFE≈+174, MAE≈-1332.",
        "data_15m": {"current_price": 71610.5, "ma5": 72011.98, "ma10": 71786.22, "ma30": 71720.93, "volume": 0, "volume_ma5": 0, "volume_ma10": 0, "net_long": 0, "net_short": 0, "futures_cvd": 21951868, "spot_cvd": 0, "taker_ls_ratio": 1.3759, "oi": 92221, "oi_delta": 0, "liquidations": {"long": 0, "short": 0}, "ma5_slope": 0, "cvd_momentum": 0, "ls_slope": 0.0694, "oi_slope": -31.4, "oi_accel": 0, "np_slope": -0.00085, "depth_imbalance": 2.5981},
        "data_1h": {"current_price": 71610.5, "ma5": 71710.18, "ma10": 71635.02, "ma30": 70109.26, "volume": 0, "volume_ma5": 0, "volume_ma10": 0, "net_long": 0, "net_short": 0, "futures_cvd": 20314803, "spot_cvd": 0, "taker_ls_ratio": 1.0094, "oi": 92221, "oi_delta": -52, "liquidations": {"long": 0, "short": 0}, "ma5_slope": 0, "cvd_momentum": 0, "ls_slope": -0.13746, "oi_slope": -50.7, "oi_accel": 0, "np_slope": 0.00552, "depth_imbalance": 2.5981, "whale_acct_ls": 1.0448, "funding_rate": 3.466e-05},
        "data_4h": {"current_price": 71606.6, "ma5": 71077.58, "ma10": 69847.55, "ma30": 68796.68, "volume": 0, "volume_ma5": 0, "volume_ma10": 0, "net_long": 0, "net_short": 0, "futures_cvd": 20100412, "spot_cvd": 0, "taker_ls_ratio": 1.0703, "oi": 92273, "oi_delta": 0, "liquidations": {"long": 0, "short": 0}, "ma5_slope": 0, "cvd_momentum": 0, "ls_slope": -0.04389, "oi_slope": 1023.2, "oi_accel": 0, "np_slope": 0.00543, "depth_imbalance": 2.5981},
        "actual": "DOWN",
        "whale_acct_ls": 1.0448,
        "run_time": "04-08 14:00",
    },
    "R33": {
        "data_15m": {"current_price": 72027.8, "ma5": 71912.0, "ma10": 72084.78, "ma30": 71587.2, "volume": 21228364, "volume_ma5": 88257047, "volume_ma10": 157790907, "net_long": 0.5092, "net_short": 0.4908, "futures_cvd": 18541747, "spot_cvd": 0, "taker_ls_ratio": 1.1677, "oi": 93150, "oi_delta": -118, "liquidations": {"long": 0, "short": 0}, "ma5_slope": -96.19, "cvd_momentum": 3.6448, "ls_slope": 0.09556, "oi_slope": -60.68, "oi_accel": -2.32, "np_slope": 0.00053, "depth_imbalance": 7.334},
        "data_1h": {"current_price": 72027.8, "ma5": 72068.0, "ma10": 71577.83, "ma30": 71287.87, "volume": 160492235, "volume_ma5": 887266433, "volume_ma10": 655685928, "net_long": 0.5096, "net_short": 0.4904, "futures_cvd": 50647486, "spot_cvd": 0, "taker_ls_ratio": 1.0027, "oi": 93268, "oi_delta": -249, "liquidations": {"long": 0, "short": 0}, "ma5_slope": 198.296, "cvd_momentum": 1.7618, "ls_slope": -0.04016, "oi_slope": 751.53, "oi_accel": -26.08, "np_slope": -0.00189, "depth_imbalance": 7.334, "whale_acct_ls": 1.0393, "funding_rate": -9.71e-06},
        "data_4h": {"current_price": 72033.5, "ma5": 71431.52, "ma10": 71401.57, "ma30": 69596.12, "volume": 2565009372, "volume_ma5": 1931542742, "volume_ma10": 2087487302, "net_long": 0.5142, "net_short": 0.4858, "futures_cvd": 5138888, "spot_cvd": 0, "taker_ls_ratio": 1.0936, "oi": 92216, "oi_delta": 767, "liquidations": {"long": 0, "short": 0}, "ma5_slope": -45.238, "cvd_momentum": -0.5886, "ls_slope": 0.01756, "oi_slope": 227.65, "oi_accel": 160.59, "np_slope": 0.00094, "depth_imbalance": 7.334},
        "actual": "UP",
        "close_price": 71600.1,
        "close_time": "04-10 08:25",
        "mfe_short": 645.7,
        "mae_short": 1100.2,
        "mfe_long": 1100.2,
        "mae_long": 645.7,
        "eval_manual_short": "YANLIS (MAE=$1100 > MFE=$646)",
        "eval_sc_long": "BASARILI (MFE=$1100, MAE/MFE=0.59)",
        "deplasman_eval": "YANLIS_KORUMA (SC LONG doğruydu, filtre engelledi)",
        "run_time": "04-09 19:27",
        "whale_acct_ls": 1.0393,
        "api_open_interest": [["04-09 15:00", 90161.07], ["04-09 16:00", 92216.21], ["04-09 17:00", 93103.01], ["04-09 18:00", 93516.85], ["04-09 19:00", 93268.38]],
        "manual_override": "SHORT — Eren manuel karar. Sistem GİRME (LONG_ANA_DEPLASMAN)",
        "leading_at_entry": "GİRME (LONG_ANA_DEPLASMAN)",
        "entry_price": 72027.8,
        "cg_observations": {
            "5m": {"price": 71805.3, "vol": "8.9M", "vol_ma5": "49.4M", "note": "tepede konsolidasyon, vol çok düşük"},
            "15m": {"price": 71850.0, "vol": "46M", "vol_ma5": "141.7M", "note": "72518 tepe reddi, toparlanma zayıf"},
            "1h": {"price": 71833.2, "vol": "391M", "vol_ma5": "980.5M", "note": "72858→70428 düşüş, vol düşük"},
            "4h": {"price": 71833.0, "vol": "2.3B", "vol_ma5": "1.88B", "note": "ralli tepesi, net_long negatif"}
        }
    },
    "R34": {
        "data_5m": {
                "current_price": 71738.8,
                "ma5": 71750.82,
                "ma10": 71682.42,
                "ma30": 71637.21,
                "volume": 5702764,
                "volume_ma5": 24112714,
                "volume_ma10": 22170007,
                "net_long": 0.5122,
                "net_short": 0.4878,
                "futures_cvd": -525204,
                "spot_cvd": 0,
                "taker_ls_ratio": 1.1725,
                "oi": 93746,
                "oi_delta": 10,
                "liquidations": {
                        "long": 0,
                        "short": 0
                },
                "ma5_slope": 29.21,
                "cvd_momentum": 0.1957,
                "ls_slope": -0.06451,
                "oi_slope": -29.05,
                "oi_accel": 6.21,
                "np_slope": -0.00017,
                "depth_imbalance": 2.0017
        },
        "data_15m": {
                "current_price": 71738.8,
                "ma5": 71675.66,
                "ma10": 71635.46,
                "ma30": 71845.13,
                "volume": 28318885,
                "volume_ma5": 71403119,
                "volume_ma10": 97754177,
                "net_long": 0.5122,
                "net_short": 0.4878,
                "futures_cvd": 1446455,
                "spot_cvd": 0,
                "taker_ls_ratio": 1.2912,
                "oi": 93736,
                "oi_delta": -124,
                "liquidations": {
                        "long": 0,
                        "short": 0
                },
                "ma5_slope": 13.794,
                "cvd_momentum": -1.2407,
                "ls_slope": 0.03708,
                "oi_slope": 12.31,
                "oi_accel": -20.68,
                "np_slope": -0.00041,
                "depth_imbalance": 2.0017
        },
        "data_1h": {
                "current_price": 71738.8,
                "ma5": 71729.66,
                "ma10": 71855.7,
                "ma30": 71633.09,
                "volume": 167736262,
                "volume_ma5": 305012484,
                "volume_ma10": 331053614,
                "net_long": 0.5125,
                "net_short": 0.4875,
                "futures_cvd": 17308886,
                "spot_cvd": 0,
                "taker_ls_ratio": 1.0205,
                "oi": 93867,
                "oi_delta": -5,
                "liquidations": {
                        "long": 0,
                        "short": 0
                },
                "ma5_slope": -52.636,
                "cvd_momentum": -2.1015,
                "ls_slope": -0.06296,
                "oi_slope": -126.92,
                "oi_accel": -45.72,
                "np_slope": 0.00122,
                "depth_imbalance": 2.0017,
                "whale_acct_ls": 1.0511,
                "funding_rate": 3.694e-05
        },
        "data_4h": {
                "current_price": 71738.8,
                "ma5": 71768.72,
                "ma10": 71500.58,
                "ma30": 70218.31,
                "volume": 564336999,
                "volume_ma5": 1761706609,
                "volume_ma10": 1688202587,
                "net_long": 0.5125,
                "net_short": 0.4875,
                "futures_cvd": 20871551,
                "spot_cvd": 0,
                "taker_ls_ratio": 0.8129,
                "oi": 93872,
                "oi_delta": -460,
                "liquidations": {
                        "long": 0,
                        "short": 0
                },
                "ma5_slope": 155.654,
                "cvd_momentum": 0.8145,
                "ls_slope": -0.0435,
                "oi_slope": 442.49,
                "oi_accel": -209.75,
                "np_slope": -0.00078,
                "depth_imbalance": 2.0017
        },
        "actual": "UP",
        "close_price": 72300.6,
        "close_time": "04-10 12:48",
        "move": 490.7,
        "mfe_4h": 657.4,
        "mae_4h": 151.1,
        "mfe_short": 151.1,
        "mae_short": 657.4,
        "run_high": 72467.3,
        "run_low": 71658.8,
        "eval_leading": "DOĞRU (GİR LONG → actual UP, MFE=$657)",
        "eval_sc_entry": "SHORT GİRME → yanlış olurdu",
        "eval_sc_close": "LONG GİR (meta=+2.5) → doğru",
        "run_time": "04-10 09:38",
        "whale_acct_ls": 1.0511,
        "entry_price": 71809.9,
        "api_open_interest": [
                [
                        "04-09 04:00",
                        91644.5
                ],
                [
                        "04-09 05:00",
                        91254.14
                ],
                [
                        "04-09 06:00",
                        91144.87
                ],
                [
                        "04-09 07:00",
                        91345.86
                ],
                [
                        "04-09 08:00",
                        91389.49
                ],
                [
                        "04-09 09:00",
                        91328.71
                ],
                [
                        "04-09 10:00",
                        91309.1
                ],
                [
                        "04-09 11:00",
                        91264.25
                ],
                [
                        "04-09 12:00",
                        91449.1
                ],
                [
                        "04-09 13:00",
                        91472.76
                ],
                [
                        "04-09 14:00",
                        91099.77
                ],
                [
                        "04-09 15:00",
                        90161.07
                ],
                [
                        "04-09 16:00",
                        92216.21
                ],
                [
                        "04-09 17:00",
                        93103.01
                ],
                [
                        "04-09 18:00",
                        93516.85
                ],
                [
                        "04-09 19:00",
                        93268.38
                ],
                [
                        "04-09 20:00",
                        93219.42
                ],
                [
                        "04-09 21:00",
                        93518.13
                ],
                [
                        "04-09 22:00",
                        93396.27
                ],
                [
                        "04-09 23:00",
                        94022.45
                ],
                [
                        "04-10 00:00",
                        92972.17
                ],
                [
                        "04-10 01:00",
                        93063.16
                ],
                [
                        "04-10 02:00",
                        94201.63
                ],
                [
                        "04-10 03:00",
                        94484.15
                ],
                [
                        "04-10 04:00",
                        94332.33
                ],
                [
                        "04-10 05:00",
                        94321.53
                ],
                [
                        "04-10 06:00",
                        94231.79
                ],
                [
                        "04-10 07:00",
                        94429.81
                ],
                [
                        "04-10 08:00",
                        93872.21
                ],
                [
                        "04-10 09:00",
                        93866.73
                ]
        ],
        "api_whale_account": [
                [
                        "04-09 04:00",
                        1.0568
                ],
                [
                        "04-09 05:00",
                        1.0653
                ],
                [
                        "04-09 06:00",
                        1.0763
                ],
                [
                        "04-09 07:00",
                        1.0761
                ],
                [
                        "04-09 08:00",
                        1.0737
                ],
                [
                        "04-09 09:00",
                        1.0655
                ],
                [
                        "04-09 10:00",
                        1.0564
                ],
                [
                        "04-09 11:00",
                        1.0537
                ],
                [
                        "04-09 12:00",
                        1.0532
                ],
                [
                        "04-09 13:00",
                        1.0499
                ],
                [
                        "04-09 14:00",
                        1.0705
                ],
                [
                        "04-09 15:00",
                        1.063
                ],
                [
                        "04-09 16:00",
                        1.0583
                ],
                [
                        "04-09 17:00",
                        1.0472
                ],
                [
                        "04-09 18:00",
                        1.0271
                ],
                [
                        "04-09 19:00",
                        1.0393
                ],
                [
                        "04-09 20:00",
                        1.0505
                ],
                [
                        "04-09 21:00",
                        1.0498
                ],
                [
                        "04-09 22:00",
                        1.0511
                ],
                [
                        "04-09 23:00",
                        1.0611
                ],
                [
                        "04-10 00:00",
                        1.0428
                ],
                [
                        "04-10 01:00",
                        1.0393
                ],
                [
                        "04-10 02:00",
                        1.0212
                ],
                [
                        "04-10 03:00",
                        1.0276
                ],
                [
                        "04-10 04:00",
                        1.0323
                ],
                [
                        "04-10 05:00",
                        1.0352
                ],
                [
                        "04-10 06:00",
                        1.0328
                ],
                [
                        "04-10 07:00",
                        1.0351
                ],
                [
                        "04-10 08:00",
                        1.0511
                ],
                [
                        "04-10 09:00",
                        1.0511
                ]
        ],
        "api_whale_position": [
                [
                        "04-09 04:00",
                        1.0568
                ],
                [
                        "04-09 05:00",
                        1.0653
                ],
                [
                        "04-09 06:00",
                        1.0764
                ],
                [
                        "04-09 07:00",
                        1.076
                ],
                [
                        "04-09 08:00",
                        1.0738
                ],
                [
                        "04-09 09:00",
                        1.0657
                ],
                [
                        "04-09 10:00",
                        1.0563
                ],
                [
                        "04-09 11:00",
                        1.0538
                ],
                [
                        "04-09 12:00",
                        1.0534
                ],
                [
                        "04-09 13:00",
                        1.05
                ],
                [
                        "04-09 14:00",
                        1.0704
                ],
                [
                        "04-09 15:00",
                        1.0631
                ],
                [
                        "04-09 16:00",
                        1.0585
                ],
                [
                        "04-09 17:00",
                        1.0471
                ],
                [
                        "04-09 18:00",
                        1.0272
                ],
                [
                        "04-09 19:00",
                        1.0392
                ],
                [
                        "04-09 20:00",
                        1.0504
                ],
                [
                        "04-09 21:00",
                        1.0496
                ],
                [
                        "04-09 22:00",
                        1.0513
                ],
                [
                        "04-09 23:00",
                        1.061
                ],
                [
                        "04-10 00:00",
                        1.0429
                ],
                [
                        "04-10 01:00",
                        1.0392
                ],
                [
                        "04-10 02:00",
                        1.021
                ],
                [
                        "04-10 03:00",
                        1.0276
                ],
                [
                        "04-10 04:00",
                        1.0321
                ],
                [
                        "04-10 05:00",
                        1.035
                ],
                [
                        "04-10 06:00",
                        1.0329
                ],
                [
                        "04-10 07:00",
                        1.035
                ],
                [
                        "04-10 08:00",
                        1.0513
                ],
                [
                        "04-10 09:00",
                        1.0513
                ]
        ],
        "api_funding_rate": [
                [
                        "04-07 08:00",
                        3.703e-05,
                        68594.77686657
                ],
                [
                        "04-07 16:00",
                        7.393e-05,
                        68141.01094203
                ],
                [
                        "04-08 00:00",
                        6.02e-05,
                        71907.34283333
                ],
                [
                        "04-08 08:00",
                        1.563e-05,
                        71612.1
                ],
                [
                        "04-08 16:00",
                        4.048e-05,
                        71275.77918841
                ],
                [
                        "04-09 00:00",
                        -1.47e-06,
                        71038.1
                ],
                [
                        "04-09 08:00",
                        5.239e-05,
                        70945.0
                ],
                [
                        "04-09 16:00",
                        -1.986e-05,
                        72108.0
                ],
                [
                        "04-10 00:00",
                        4.11e-06,
                        71755.54984058
                ],
                [
                        "04-10 08:00",
                        2.458e-05,
                        71461.2
                ]
        ],
        "api_taker_ls": [
                [
                        "04-09 03:00",
                        0.9558
                ],
                [
                        "04-09 04:00",
                        0.6205
                ],
                [
                        "04-09 05:00",
                        1.3009
                ],
                [
                        "04-09 06:00",
                        1.0292
                ],
                [
                        "04-09 07:00",
                        1.0927
                ],
                [
                        "04-09 08:00",
                        1.2607
                ],
                [
                        "04-09 09:00",
                        1.1796
                ],
                [
                        "04-09 10:00",
                        0.8508
                ],
                [
                        "04-09 11:00",
                        0.8201
                ],
                [
                        "04-09 12:00",
                        1.0043
                ],
                [
                        "04-09 13:00",
                        0.794
                ],
                [
                        "04-09 14:00",
                        1.1418
                ],
                [
                        "04-09 15:00",
                        1.216
                ],
                [
                        "04-09 16:00",
                        0.8375
                ],
                [
                        "04-09 17:00",
                        1.0926
                ],
                [
                        "04-09 18:00",
                        1.0027
                ],
                [
                        "04-09 19:00",
                        1.1359
                ],
                [
                        "04-09 20:00",
                        1.1709
                ],
                [
                        "04-09 21:00",
                        1.0779
                ],
                [
                        "04-09 22:00",
                        1.3418
                ],
                [
                        "04-09 23:00",
                        1.2461
                ],
                [
                        "04-10 00:00",
                        1.1487
                ],
                [
                        "04-10 01:00",
                        1.3351
                ],
                [
                        "04-10 02:00",
                        0.951
                ],
                [
                        "04-10 03:00",
                        0.8339
                ],
                [
                        "04-10 04:00",
                        1.1345
                ],
                [
                        "04-10 05:00",
                        1.033
                ],
                [
                        "04-10 06:00",
                        0.8207
                ],
                [
                        "04-10 07:00",
                        0.6314
                ],
                [
                        "04-10 08:00",
                        1.0205
                ]
        ],
        "leading_at_entry": "GİR LONG (LONG_ANA)",
        "sc_at_entry": "SHORT GİRME (meta=-5.0)",
        "entry_trigger": {
                "direction": "LONG",
                "destek": 71460.1,
                "giris_trigger": 71503.5,
                "stop_loss": 71329.9,
                "tp1": 71803.5,
                "tp2": 72503.5,
                "atr_5m": 86.8,
                "sl_distance": 173.6,
                "rr_tp1": 1.7,
                "rr_tp2": 5.8,
                "pozisyon_btc": 0.288,
                "risk_dollar": 50
        },
        "cg_observations": {
                "5m": {
                        "price": 71810.0,
                        "high": 72350.0,
                        "low": 71382.1,
                        "vol": "23.3M",
                        "vol_ma5": "27.5M",
                        "vol_ma10": "23.9M",
                        "net_long": "4.1K",
                        "net_short": "-1.2K",
                        "fs_ratio": 11.7,
                        "note": "72350→71382 düşüş sonrası konsolidasyon, vol düşük"
                },
                "15m": {
                        "price": 71819.2,
                        "high": 73128.0,
                        "low": 70470.2,
                        "vol": "46.5M",
                        "vol_ma5": "74.9M",
                        "vol_ma10": "99.5M",
                        "net_long": "17.6K",
                        "net_short": "-13.0K",
                        "fs_ratio": 12.0,
                        "note": "73128 tepe, 70470 dip, geri çekilme konsolidasyona döndü"
                }
        },
        "compact_summary": {
                "rejim": "TRENDING (ADX=32.7)",
                "v3a": "+1 → LONG",
                "mum": "2 çelişki",
                "danisma": "3 uyarı",
                "tf": "15m=+0.06 1h=-0.93 4h=-0.89 → SHORT",
                "flags": "TF celiski: 2/3",
                "pct_ma30": "+2.26%"
        }
},
    "R35": {
        "data_5m": {
                "current_price": 72298.1,
                "ma5": 72252.0,
                "ma10": 72179.18,
                "ma30": 72045.85,
                "volume": 23518681,
                "volume_ma5": 121971926,
                "volume_ma10": 81707711,
                "net_long": 0.5136,
                "net_short": 0.4864,
                "futures_cvd": -1850076,
                "spot_cvd": 0,
                "taker_ls_ratio": 0.6653,
                "oi": 93676,
                "oi_delta": 76,
                "liquidations": {
                        "long": 0,
                        "short": 0
                },
                "ma5_slope": 28.606,
                "cvd_momentum": 12.0576,
                "ls_slope": -0.06544,
                "oi_slope": 133.23,
                "oi_accel": -0.76,
                "np_slope": 0.00093,
                "depth_imbalance": 0.9421
        },
        "data_15m": {
                "current_price": 72298.1,
                "ma5": 72170.72,
                "ma10": 72090.09,
                "ma30": 71871.69,
                "volume": 23569723,
                "volume_ma5": 183454527,
                "volume_ma10": 145341004,
                "net_long": 0.5136,
                "net_short": 0.4864,
                "futures_cvd": -1850943,
                "spot_cvd": 0,
                "taker_ls_ratio": 1.2398,
                "oi": 93676,
                "oi_delta": 397,
                "liquidations": {
                        "long": 0,
                        "short": 0
                },
                "ma5_slope": 30.72,
                "cvd_momentum": -0.5635,
                "ls_slope": 0.1378,
                "oi_slope": 106.49,
                "oi_accel": 53.03,
                "np_slope": 6e-05,
                "depth_imbalance": 0.9421
        },
        "data_1h": {
                "current_price": 72300.6,
                "ma5": 71916.7,
                "ma10": 71884.75,
                "ma30": 71751.57,
                "volume": 817372956,
                "volume_ma5": 438129132,
                "volume_ma10": 359270093,
                "net_long": 0.5121,
                "net_short": 0.4879,
                "futures_cvd": 37854842,
                "spot_cvd": 0,
                "taker_ls_ratio": 0.9878,
                "oi": 93176,
                "oi_delta": -177,
                "liquidations": {
                        "long": 0,
                        "short": 0
                },
                "ma5_slope": -32.172,
                "cvd_momentum": -0.4027,
                "ls_slope": 0.09016,
                "oi_slope": -190.56,
                "oi_accel": 45.79,
                "np_slope": -0.0001,
                "depth_imbalance": 0.9421,
                "whale_acct_ls": 1.0495,
                "funding_rate": 7.64e-06
        },
        "data_4h": {
                "current_price": 72314.3,
                "ma5": 71891.18,
                "ma10": 71663.59,
                "ma30": 70398.17,
                "volume": 817769994,
                "volume_ma5": 1483141576,
                "volume_ma10": 1752794308,
                "net_long": 0.5121,
                "net_short": 0.4879,
                "futures_cvd": 38248699,
                "spot_cvd": 0,
                "taker_ls_ratio": 1.0706,
                "oi": 93176,
                "oi_delta": -696,
                "liquidations": {
                        "long": 0,
                        "short": 0
                },
                "ma5_slope": 105.572,
                "cvd_momentum": 2.4082,
                "ls_slope": -0.02825,
                "oi_slope": 81.39,
                "oi_accel": -361.1,
                "np_slope": 0.00016,
                "depth_imbalance": 0.9421
        },
        "actual": None,
        "run_time": "04-10 12:48",
        "whale_acct_ls": 1.0495,
        "entry_price": 72300.6,
        "api_open_interest": [
                [
                        "04-09 07:00",
                        91345.86
                ],
                [
                        "04-09 08:00",
                        91389.49
                ],
                [
                        "04-09 09:00",
                        91328.71
                ],
                [
                        "04-09 10:00",
                        91309.1
                ],
                [
                        "04-09 11:00",
                        91264.25
                ],
                [
                        "04-09 12:00",
                        91449.1
                ],
                [
                        "04-09 13:00",
                        91472.76
                ],
                [
                        "04-09 14:00",
                        91099.77
                ],
                [
                        "04-09 15:00",
                        90161.07
                ],
                [
                        "04-09 16:00",
                        92216.21
                ],
                [
                        "04-09 17:00",
                        93103.01
                ],
                [
                        "04-09 18:00",
                        93516.85
                ],
                [
                        "04-09 19:00",
                        93268.38
                ],
                [
                        "04-09 20:00",
                        93219.42
                ],
                [
                        "04-09 21:00",
                        93518.13
                ],
                [
                        "04-09 22:00",
                        93396.27
                ],
                [
                        "04-09 23:00",
                        94022.45
                ],
                [
                        "04-10 00:00",
                        92972.17
                ],
                [
                        "04-10 01:00",
                        93063.16
                ],
                [
                        "04-10 02:00",
                        94201.63
                ],
                [
                        "04-10 03:00",
                        94484.15
                ],
                [
                        "04-10 04:00",
                        94332.33
                ],
                [
                        "04-10 05:00",
                        94321.53
                ],
                [
                        "04-10 06:00",
                        94231.79
                ],
                [
                        "04-10 07:00",
                        94429.81
                ],
                [
                        "04-10 08:00",
                        93872.21
                ],
                [
                        "04-10 09:00",
                        93866.73
                ],
                [
                        "04-10 10:00",
                        93662.63
                ],
                [
                        "04-10 11:00",
                        93352.83
                ],
                [
                        "04-10 12:00",
                        93176.34
                ]
        ],
        "api_whale_account": [
                [
                        "04-09 07:00",
                        1.0761
                ],
                [
                        "04-09 08:00",
                        1.0737
                ],
                [
                        "04-09 09:00",
                        1.0655
                ],
                [
                        "04-09 10:00",
                        1.0564
                ],
                [
                        "04-09 11:00",
                        1.0537
                ],
                [
                        "04-09 12:00",
                        1.0532
                ],
                [
                        "04-09 13:00",
                        1.0499
                ],
                [
                        "04-09 14:00",
                        1.0705
                ],
                [
                        "04-09 15:00",
                        1.063
                ],
                [
                        "04-09 16:00",
                        1.0583
                ],
                [
                        "04-09 17:00",
                        1.0472
                ],
                [
                        "04-09 18:00",
                        1.0271
                ],
                [
                        "04-09 19:00",
                        1.0393
                ],
                [
                        "04-09 20:00",
                        1.0505
                ],
                [
                        "04-09 21:00",
                        1.0498
                ],
                [
                        "04-09 22:00",
                        1.0511
                ],
                [
                        "04-09 23:00",
                        1.0611
                ],
                [
                        "04-10 00:00",
                        1.0428
                ],
                [
                        "04-10 01:00",
                        1.0393
                ],
                [
                        "04-10 02:00",
                        1.0212
                ],
                [
                        "04-10 03:00",
                        1.0276
                ],
                [
                        "04-10 04:00",
                        1.0323
                ],
                [
                        "04-10 05:00",
                        1.0352
                ],
                [
                        "04-10 06:00",
                        1.0328
                ],
                [
                        "04-10 07:00",
                        1.0351
                ],
                [
                        "04-10 08:00",
                        1.0511
                ],
                [
                        "04-10 09:00",
                        1.0511
                ],
                [
                        "04-10 10:00",
                        1.0525
                ],
                [
                        "04-10 11:00",
                        1.0503
                ],
                [
                        "04-10 12:00",
                        1.0495
                ]
        ],
        "api_whale_position": [
                [
                        "04-09 07:00",
                        1.076
                ],
                [
                        "04-09 08:00",
                        1.0738
                ],
                [
                        "04-09 09:00",
                        1.0657
                ],
                [
                        "04-09 10:00",
                        1.0563
                ],
                [
                        "04-09 11:00",
                        1.0538
                ],
                [
                        "04-09 12:00",
                        1.0534
                ],
                [
                        "04-09 13:00",
                        1.05
                ],
                [
                        "04-09 14:00",
                        1.0704
                ],
                [
                        "04-09 15:00",
                        1.0631
                ],
                [
                        "04-09 16:00",
                        1.0585
                ],
                [
                        "04-09 17:00",
                        1.0471
                ],
                [
                        "04-09 18:00",
                        1.0272
                ],
                [
                        "04-09 19:00",
                        1.0392
                ],
                [
                        "04-09 20:00",
                        1.0504
                ],
                [
                        "04-09 21:00",
                        1.0496
                ],
                [
                        "04-09 22:00",
                        1.0513
                ],
                [
                        "04-09 23:00",
                        1.061
                ],
                [
                        "04-10 00:00",
                        1.0429
                ],
                [
                        "04-10 01:00",
                        1.0392
                ],
                [
                        "04-10 02:00",
                        1.021
                ],
                [
                        "04-10 03:00",
                        1.0276
                ],
                [
                        "04-10 04:00",
                        1.0321
                ],
                [
                        "04-10 05:00",
                        1.035
                ],
                [
                        "04-10 06:00",
                        1.0329
                ],
                [
                        "04-10 07:00",
                        1.035
                ],
                [
                        "04-10 08:00",
                        1.0513
                ],
                [
                        "04-10 09:00",
                        1.0513
                ],
                [
                        "04-10 10:00",
                        1.0525
                ],
                [
                        "04-10 11:00",
                        1.0504
                ],
                [
                        "04-10 12:00",
                        1.0496
                ]
        ],
        "api_funding_rate": [
                [
                        "04-07 08:00",
                        3.703e-05,
                        68594.77686657
                ],
                [
                        "04-07 16:00",
                        7.393e-05,
                        68141.01094203
                ],
                [
                        "04-08 00:00",
                        6.02e-05,
                        71907.34283333
                ],
                [
                        "04-08 08:00",
                        1.563e-05,
                        71612.1
                ],
                [
                        "04-08 16:00",
                        4.048e-05,
                        71275.77918841
                ],
                [
                        "04-09 00:00",
                        -1.47e-06,
                        71038.1
                ],
                [
                        "04-09 08:00",
                        5.239e-05,
                        70945.0
                ],
                [
                        "04-09 16:00",
                        -1.986e-05,
                        72108.0
                ],
                [
                        "04-10 00:00",
                        4.11e-06,
                        71755.54984058
                ],
                [
                        "04-10 08:00",
                        2.458e-05,
                        71461.2
                ]
        ],
        "api_taker_ls": [
                [
                        "04-09 06:00",
                        1.0292
                ],
                [
                        "04-09 07:00",
                        1.0927
                ],
                [
                        "04-09 08:00",
                        1.2607
                ],
                [
                        "04-09 09:00",
                        1.1796
                ],
                [
                        "04-09 10:00",
                        0.8508
                ],
                [
                        "04-09 11:00",
                        0.8201
                ],
                [
                        "04-09 12:00",
                        1.0043
                ],
                [
                        "04-09 13:00",
                        0.794
                ],
                [
                        "04-09 14:00",
                        1.1418
                ],
                [
                        "04-09 15:00",
                        1.216
                ],
                [
                        "04-09 16:00",
                        0.8375
                ],
                [
                        "04-09 17:00",
                        1.0926
                ],
                [
                        "04-09 18:00",
                        1.0027
                ],
                [
                        "04-09 19:00",
                        1.1359
                ],
                [
                        "04-09 20:00",
                        1.1709
                ],
                [
                        "04-09 21:00",
                        1.0779
                ],
                [
                        "04-09 22:00",
                        1.3418
                ],
                [
                        "04-09 23:00",
                        1.2461
                ],
                [
                        "04-10 00:00",
                        1.1487
                ],
                [
                        "04-10 01:00",
                        1.3351
                ],
                [
                        "04-10 02:00",
                        0.951
                ],
                [
                        "04-10 03:00",
                        0.8339
                ],
                [
                        "04-10 04:00",
                        1.1345
                ],
                [
                        "04-10 05:00",
                        1.033
                ],
                [
                        "04-10 06:00",
                        0.8207
                ],
                [
                        "04-10 07:00",
                        0.6314
                ],
                [
                        "04-10 08:00",
                        1.0205
                ],
                [
                        "04-10 09:00",
                        1.2077
                ],
                [
                        "04-10 10:00",
                        1.2093
                ],
                [
                        "04-10 11:00",
                        0.9878
                ]
        ],
        "leading_at_entry": "GİR LONG (LONG_ANA)",
        "sc_at_entry": "LONG GİR (meta=+0.5)",
        "cg_observations": {
                "5m": {
                        "price": 72350.0,
                        "high": 72467.3,
                        "low": 71382.1,
                        "vol": "28.3M",
                        "vol_ma5": "122.9M",
                        "vol_ma10": "82.2M",
                        "net_long": "5.2K",
                        "net_short": "-1.6K",
                        "fs_ratio": 10.1,
                        "note": "71382 dipten 72467 tepeye toparlanma, vol yükseldi"
                },
                "15m": {
                        "price": 72371.2,
                        "high": 73128.0,
                        "low": 70470.2,
                        "vol": "29.3M",
                        "vol_ma5": "180.7M",
                        "vol_ma10": "143.9M",
                        "net_long": "19.7K",
                        "net_short": "-12.2K",
                        "fs_ratio": 10.0,
                        "note": "73128→70470→72467 V-recovery, net_long güçlü"
                }
        },
        "compact_summary": {
                "rejim": "TRENDING (ADX=33.5)",
                "v3a": "+2 → LONG",
                "mum": "1 çelişki",
                "danisma": "3 uyarı",
                "tf": "15m=+0.98 1h=+0.64 4h=+0.29 → LONG",
                "flags": "|4h|=0.29 < 0.50 — cok zayif 4h sinyali",
                "pct_ma30": "+2.55%"
        },
        "actual": "UP",
        "close_price": 72970.1,
        "close_time": "04-10 16:48",
        "move": 669.5,
        "mfe_4h": 823.3,
        "mae_4h": 432.1,
        "mfe_short": 432.1,
        "mae_short": 823.3,
        "run_high": 73123.9,
        "run_low": 71868.5,
        "eval_leading": "DOĞRU (GİR LONG → actual UP, MFE=$823)",
        "eval_sc_entry": "LONG GİR (meta=+4.0) → doğru",
        "run_time": "04-10 12:48",
        "whale_acct_ls": 1.0495,
},
    "R36": {
        "data_5m": {
                "current_price": 72824.3,
                "ma5": 72841.76,
                "ma10": 72776.45,
                "ma30": 72753.21,
                "volume": 11223156,
                "volume_ma5": 43151216,
                "volume_ma10": 42087198,
                "net_long": 0.5096,
                "net_short": 0.4904,
                "futures_cvd": -513343,
                "spot_cvd": 0,
                "taker_ls_ratio": 1.2501,
                "oi": 96546,
                "oi_delta": -66,
                "liquidations": {"long": 0, "short": 0},
                "ma5_slope": 27.18,
                "cvd_momentum": -0.4024,
                "ls_slope": 0.16538,
                "oi_slope": -7.33,
                "oi_accel": -10.65,
                "np_slope": -0.00049,
                "depth_imbalance": 1.0156
        },
        "data_15m": {
                "current_price": 72824.2,
                "ma5": 72770.52,
                "ma10": 72756.69,
                "ma30": 72359.71,
                "volume": 60181415,
                "volume_ma5": 130810524,
                "volume_ma10": 189182921,
                "net_long": 0.5104,
                "net_short": 0.4896,
                "futures_cvd": -16568722,
                "spot_cvd": 0,
                "taker_ls_ratio": 1.4807,
                "oi": 96612,
                "oi_delta": 20,
                "liquidations": {"long": 0, "short": 0},
                "ma5_slope": -16.708,
                "cvd_momentum": -0.3471,
                "ls_slope": 0.08506,
                "oi_slope": -80.9,
                "oi_accel": 56.83,
                "np_slope": 0.00014,
                "depth_imbalance": 1.0156
        },
        "data_1h": {
                "current_price": 72833.0,
                "ma5": 72672.52,
                "ma10": 72287.1,
                "ma30": 71994.96,
                "volume": 60323937,
                "volume_ma5": 797147556,
                "volume_ma10": 623328934,
                "net_long": 0.5104,
                "net_short": 0.4896,
                "futures_cvd": -16536310,
                "spot_cvd": 0,
                "taker_ls_ratio": 1.152,
                "oi": 96612,
                "oi_delta": -316,
                "liquidations": {"long": 0, "short": 0},
                "ma5_slope": 163.328,
                "cvd_momentum": 0.4522,
                "ls_slope": 0.01904,
                "oi_slope": 843.96,
                "oi_accel": -215.04,
                "np_slope": -0.00095,
                "depth_imbalance": 1.0156,
                "whale_acct_ls": 1.0423,
                "funding_rate": -3.091e-05
        },
        "data_4h": {
                "current_price": 72833.0,
                "ma5": 72129.04,
                "ma10": 71861.44,
                "ma30": 70585.19,
                "volume": 654195143,
                "volume_ma5": 1796034918,
                "volume_ma10": 2006935580,
                "net_long": 0.5102,
                "net_short": 0.4898,
                "futures_cvd": 25462508,
                "spot_cvd": 0,
                "taker_ls_ratio": 1.049,
                "oi": 96928,
                "oi_delta": 3752,
                "liquidations": {"long": 0, "short": 0},
                "ma5_slope": 70.456,
                "cvd_momentum": -0.6838,
                "ls_slope": -0.04442,
                "oi_slope": 675.51,
                "oi_accel": 594.12,
                "np_slope": 0.00036,
                "depth_imbalance": 1.0156
        },
        "actual": "UP",
        "close_price": 72962.3,
        "close_time": "04-11 17:14",
        "move": 129.3,
        "mfe_4h": 617.0,
        "mae_4h": 83.0,
        "mfe_short": 83.0,
        "mae_short": 617.0,
        "run_high": 73450.0,
        "run_low": 72451.9,
        "eval_leading": "GİRME (LONG_ANA_DEPLASMAN) — pozisyon açılmadı, SC LONG doğruydu",
        "eval_sc_entry": "LONG GİR (meta=+0.5) → doğru",
        "deplasman_eval": "YANLIS_KORUMA (SC LONG doğruydu, DEPLASMAN engelledi, %MA30=+3.2%)",
        "run_time": "04-10 17:06",
        "whale_acct_ls": 1.0423,
        "entry_price": 72833.0,
        "leading_at_entry": "GİRME (LONG_ANA_DEPLASMAN)",
        "api_open_interest": [["04-10 17:00", 5163]],
        "api_taker_ls": [["04-10 17:00", 1.1520]]
},
    "R37": {
        "data_5m": {"current_price": 70815.3, "ma5": 70939.46, "ma10": 71081.83, "ma30": 71131.35, "volume": 26008928, "volume_ma5": 106044920, "volume_ma10": 57682671, "net_long": 0.5085, "net_short": 0.4915, "futures_cvd": 442791, "spot_cvd": 0, "taker_ls_ratio": 2.3473, "oi": 91452, "oi_delta": -11, "liquidations": {"long": 0, "short": 0}, "ma5_slope": -61.218, "cvd_momentum": -25.2307, "ls_slope": 0.22954, "oi_slope": 107.49, "oi_accel": -13.54, "np_slope": 0.00244, "depth_imbalance": 0.7304},
        "data_15m": {"current_price": 70802.6, "ma5": 71120.76, "ma10": 71137.68, "ma30": 71021.72, "volume": 27899531, "volume_ma5": 121478170, "volume_ma10": 105777641, "net_long": 0.5085, "net_short": 0.4915, "futures_cvd": 566549, "spot_cvd": 0, "taker_ls_ratio": 0.7397, "oi": 91452, "oi_delta": 302, "liquidations": {"long": 0, "short": 0}, "ma5_slope": 14.312, "cvd_momentum": -2.1421, "ls_slope": -0.12358, "oi_slope": 75.5, "oi_accel": 101.62, "np_slope": 0.00156, "depth_imbalance": 0.7304},
        "data_1h": {"current_price": 70812.0, "ma5": 71118.88, "ma10": 71001.72, "ma30": 71815.7, "volume": 510145423, "volume_ma5": 278984242, "volume_ma10": 372761637, "net_long": 0.5, "net_short": 0.5, "futures_cvd": -70576782, "spot_cvd": 0, "taker_ls_ratio": 1.1781, "oi": 91150, "oi_delta": -116, "liquidations": {"long": 0, "short": 0}, "ma5_slope": 74.132, "cvd_momentum": -1.3109, "ls_slope": -0.06968, "oi_slope": -142.85, "oi_accel": 5.74, "np_slope": 0.00074, "depth_imbalance": 0.7304, "whale_acct_ls": 1.0001, "funding_rate": -2.971e-05},
        "data_4h": {"current_price": 70811.9, "ma5": 71157.28, "ma10": 71968.48, "ma30": 71873.09, "volume": 1057889275, "volume_ma5": 1169287290, "volume_ma10": 1320090973, "net_long": 0.4998, "net_short": 0.5002, "futures_cvd": -6453496, "spot_cvd": 0, "taker_ls_ratio": 1.1729, "oi": 91624, "oi_delta": -378, "liquidations": {"long": 0, "short": 0}, "ma5_slope": -377.652, "cvd_momentum": -2.9727, "ls_slope": 0.01817, "oi_slope": -1216.17, "oi_accel": 252.5, "np_slope": 0.0044, "depth_imbalance": 0.7304},
        "actual": "DOWN",
        "close_price": 70812.0,
        "close_time": "04-12 22:17",
        "move": -691.0,
        "mfe_4h": 937,
        "mae_4h": 13,
        "mfe_short": 937,
        "mae_short": 13,
        "mfe_long": 13,
        "mae_long": 937,
        "run_high": 71516.0,
        "run_low": 70566.0,
        "eval_leading": "SİNYAL_YOK → LONG_ANA (YANLIŞ)",
        "eval_sc_entry": "SHORT GİR → doğru",
        "run_time": "04-12 09:53",
        "whale_acct_ls": 1.0001,
        "entry_price": 71503.0,
        "leading_at_entry": "GİRME (SİNYAL_YOK)",
        "api_open_interest": [["04-11 17:00", 98102.1], ["04-12 22:00", 91149.68]],
        "api_taker_ls": [["04-11 16:00", 1.3387], ["04-12 21:00", 1.1781]]
},
    "R38": {
        "data_5m": {"current_price": 71054.2, "ma5": 71088.36, "ma10": 71085.22, "ma30": 70854.58, "volume": 20159262, "volume_ma5": 20990650, "volume_ma10": 24269273, "net_long": 0.5106, "net_short": 0.4894, "futures_cvd": -2667725, "spot_cvd": 0, "taker_ls_ratio": 0.7383, "oi": 90622, "oi_delta": -21, "liquidations": {"long": 0, "short": 0}, "ma5_slope": 5.718, "cvd_momentum": -2.0108, "ls_slope": -0.02977, "oi_slope": -7.94, "oi_accel": -8.42, "np_slope": -5e-05, "depth_imbalance": 42.1867},
        "data_15m": {"current_price": 71056.7, "ma5": 71049.04, "ma10": 70881.58, "ma30": 71013.04, "volume": 43268624, "volume_ma5": 72785646, "volume_ma10": 73582625, "net_long": 0.5106, "net_short": 0.4894, "futures_cvd": -6455785, "spot_cvd": 0, "taker_ls_ratio": 0.6362, "oi": 90643, "oi_delta": -10, "liquidations": {"long": 0, "short": 0}, "ma5_slope": 75.418, "cvd_momentum": -0.2606, "ls_slope": -0.09386, "oi_slope": -57.93, "oi_accel": -4.31, "np_slope": -0.00075, "depth_imbalance": 42.1867},
        "data_1h": {"current_price": 71054.2, "ma5": 71020.52, "ma10": 71054.41, "ma30": 71574.06, "volume": 105474488, "volume_ma5": 368952697, "volume_ma10": 302765883, "net_long": 0.5108, "net_short": 0.4892, "futures_cvd": -20144794, "spot_cvd": 0, "taker_ls_ratio": 1.3225, "oi": 90653, "oi_delta": -118, "liquidations": {"long": 0, "short": 0}, "ma5_slope": -15.724, "cvd_momentum": -1.346, "ls_slope": -0.00651, "oi_slope": -160.56, "oi_accel": 63.61, "np_slope": 0.00283, "depth_imbalance": 42.1867, "whale_acct_ls": 1.0441, "funding_rate": 3.24e-06},
        "data_4h": {"current_price": 71051.2, "ma5": 71021.74, "ma10": 71776.7, "ma30": 71862.78, "volume": 483470357, "volume_ma5": 1227590278, "volume_ma10": 1376269118, "net_long": 0.5117, "net_short": 0.4883, "futures_cvd": 32477730, "spot_cvd": 0, "taker_ls_ratio": 0.9735, "oi": 90771, "oi_delta": -853, "liquidations": {"long": 0, "short": 0}, "ma5_slope": -373.666, "cvd_momentum": -3.3949, "ls_slope": 0.03125, "oi_slope": -1200.72, "oi_accel": 15.44, "np_slope": 0.00671, "depth_imbalance": 42.1867},
        "actual": "UP",
        "close_price": 73000.0,
        "close_time": "04-15 13:07",
        "move": 2.74,
        "run_time": "04-13 01:24",
        "whale_acct_ls": 1.0441,
        "entry_price": 71054.2,
        "leading_at_entry": "GİR_DİKKAT LONG (LONG_ANA_GEÇ)",
        "api_open_interest": [["04-11 20:00", 98391.9], ["04-13 01:00", 90652.68]],
        "api_taker_ls": [["04-11 19:00", 1.1547], ["04-13 00:00", 1.3225]]
},
    "R39": {
        "data_5m": {"current_price": 73965.6, "ma5": 73943.5, "ma10": 73936.59, "ma30": 73944.78, "volume": 5899842, "volume_ma5": 14495591, "volume_ma10": 27560159, "net_long": 0.473, "net_short": 0.527, "futures_cvd": 3455768, "spot_cvd": 0, "taker_ls_ratio": 2.3305, "oi": 97539, "oi_delta": -36, "liquidations": {"long": 0, "short": 0}, "ma5_slope": 3.314, "cvd_momentum": 5.3179, "ls_slope": 0.03822, "oi_slope": -15.37, "oi_accel": -15.57, "np_slope": -8e-05, "depth_imbalance": 0.3699},
        "data_15m": {"current_price": 73961.6, "ma5": 73942.48, "ma10": 73946.11, "ma30": 73956.04, "volume": 5974767, "volume_ma5": 75236320, "volume_ma10": 64903901, "net_long": 0.4732, "net_short": 0.5268, "futures_cvd": 3441789, "spot_cvd": 0, "taker_ls_ratio": 1.5041, "oi": 97546, "oi_delta": -44, "liquidations": {"long": 0, "short": 0}, "ma5_slope": -6.976, "cvd_momentum": 2.9104, "ls_slope": 0.10674, "oi_slope": -2.42, "oi_accel": -4.73, "np_slope": 0.00042, "depth_imbalance": 0.3699},
        "data_1h": {"current_price": 73961.6, "ma5": 73906.26, "ma10": 74023.32, "ma30": 74339.59, "volume": 119305909, "volume_ma5": 354276383, "volume_ma10": 297066162, "net_long": 0.4728, "net_short": 0.5272, "futures_cvd": 24831535, "spot_cvd": 0, "taker_ls_ratio": 0.9729, "oi": 97565, "oi_delta": -42, "liquidations": {"long": 0, "short": 0}, "ma5_slope": -62.222, "cvd_momentum": -0.5143, "ls_slope": 0.03538, "oi_slope": -368.15, "oi_accel": 64.92, "np_slope": 0.0012, "depth_imbalance": 0.3699, "whale_acct_ls": 0.897, "funding_rate": -3.019e-05},
        "data_4h": {"current_price": 73961.6, "ma5": 74049.36, "ma10": 74316.45, "ma30": 72817.38, "volume": 1097644368, "volume_ma5": 1580620077, "volume_ma10": 2197651883, "net_long": 0.4716, "net_short": 0.5284, "futures_cvd": 53547165, "spot_cvd": 0, "taker_ls_ratio": 0.8799, "oi": 98146, "oi_delta": -762, "liquidations": {"long": 0, "short": 0}, "ma5_slope": -64.946, "cvd_momentum": -1.0112, "ls_slope": -0.03908, "oi_slope": -652.23, "oi_accel": -1166.17, "np_slope": 0.00217, "depth_imbalance": 0.3699},
        "actual": "UP",
        "close_price": None,
        "close_time": None,
        "move": None,
        "run_time": "04-15 11:31",
        "whale_acct_ls": 0.897,
        "entry_price": 73992.0,
        "leading_at_entry": "GİR SHORT (SHORT_TRAP)",
        "api_open_interest": [["04-14 06:00", 94455.11], ["04-15 11:00", 97565.39]],
        "api_taker_ls": [["04-14 05:00", 0.9776], ["04-15 10:00", 0.9729]]
},

    "R40": {
        "data_5m": {"current_price": 75631.8, "ma5": 75664.86, "ma10": 75624.24, "ma30": 75709.75, "volume": 2194845, "volume_ma5": 15778320, "volume_ma10": 38722226, "net_long": 0.4485, "net_short": 0.5515, "futures_cvd": 1208157, "spot_cvd": 0, "taker_ls_ratio": 1.0797, "oi": 98912, "oi_delta": -6, "liquidations": {"long": 0, "short": 0}, "ma5_slope": 23.316, "cvd_momentum": 5.5779, "ls_slope": -0.07765, "oi_slope": -26.31, "oi_accel": -0.9, "np_slope": -4e-05, "depth_imbalance": 1.8524},
        "data_15m": {"current_price": 75634.6, "ma5": 75618.16, "ma10": 75705.17, "ma30": 75965.14, "volume": 34069012, "volume_ma5": 131534125, "volume_ma10": 102900803, "net_long": 0.4489, "net_short": 0.5511, "futures_cvd": -2794440, "spot_cvd": 0, "taker_ls_ratio": 1.124, "oi": 98924, "oi_delta": -77, "liquidations": {"long": 0, "short": 0}, "ma5_slope": -40.076, "cvd_momentum": -3.7662, "ls_slope": 0.15114, "oi_slope": -131.77, "oi_accel": 66.83, "np_slope": 0.00126, "depth_imbalance": 1.8524},
        "data_1h": {"current_price": 75634.5, "ma5": 75808.96, "ma10": 75965.65, "ma30": 76796.1, "volume": 113184964, "volume_ma5": 384977572, "volume_ma10": 454080417, "net_long": 0.4481, "net_short": 0.5519, "futures_cvd": 1898149, "spot_cvd": 0, "taker_ls_ratio": 0.7869, "oi": 99001, "oi_delta": -679, "liquidations": {"long": 0, "short": 0}, "ma5_slope": -49.372, "cvd_momentum": -5.5811, "ls_slope": -0.15791, "oi_slope": -727.12, "oi_accel": -129.72, "np_slope": -0.00178, "depth_imbalance": 1.8524, "whale_acct_ls": 0.8119, "funding_rate": -8.465e-05},
        "data_4h": {"current_price": 75634.5, "ma5": 76335.32, "ma10": 76438.18, "ma30": 75165.93, "volume": 1680268604, "volume_ma5": 1494119013, "volume_ma10": 2481557519, "net_long": 0.4524, "net_short": 0.5476, "futures_cvd": -210786447, "spot_cvd": 0, "taker_ls_ratio": 1.184, "oi": 101310, "oi_delta": -1363, "liquidations": {"long": 0, "short": 0}, "ma5_slope": 8.192, "cvd_momentum": -1.6289, "ls_slope": -0.00508, "oi_slope": -1478.95, "oi_accel": -365.56, "np_slope": 0.00248, "depth_imbalance": 1.8524},
        "api_open_interest": [["04-17 14:00", 103336.74], ["04-18 19:00", 99000.96]],
        "api_taker_ls": [["04-17 13:00", 1.0587], ["04-18 18:00", 0.7869]],
        "whale_acct_ls": 0.8119,
        "_snapshot_source": "r_update.json @ post-close (R40 manuel override icin acilis snapshot mevcut degildi)",
        "run_time": "04-18 16:34",
        "entry_price": 75980.2,
        "actual": "DOWN",
        "move": -584.3,
        "mfe_4h": 584.3,
        "mae_4h": 269.8,
        "close_price": 75395.9,
        "close_time": "04-18 21:43",
        "override": "manuel_leading_only",
        "override_reason": "Sistem BEKLE; leading SHORT/GIR + sc LONG/GIRME (margin 0.0435 < 0.10)",
        "direction_taken": "SHORT",
        "leading_at_entry": "GIR SHORT (SHORT_TRAP) — manuel_override",
        "sc_at_entry": "GIRME LONG (COK_KUCUK_BOYUT)",
        "size_btc": 0.25,
        "notional_usd": 18995.05,
        "atr_15m": 224.5,
        "sl_target": 76316.9,
        "tp1_target": 75306.7,
        "tp2_target": 75082.2,
        "be_tetik_target": 75755.7,
        "exit_reason": "MANUEL_DIP",
        "be_triggered": True,
        "be_executed": True,
        "tp1_hit": False,
        "tp2_hit": False,
        "sl_hit": False,
        "gross_pnl_usd": 146.08,
        "result_r": 1.74,
        "balance_usd": 2000,
        "actual_risk_pct": 4.21,
        "leverage_actual": 9.5,
        "risk_violation": True,
        "risk_violation_note": "5K bakiye varsayim ile 0.250 BTC alindi, gercek 2K bakiye. Hedef %1, gercek %4.2.",
        "system_long_w_at_signal": 0.4783,
        "system_short_w_at_signal": 0.5217,
        "system_margin_at_signal": 0.0435,
        "leading_yon_at_signal": "SHORT",
        "leading_karar_at_signal": "GIR",
        "sc_yon_at_signal": "LONG",
        "sc_karar_at_signal": "GIRME"
    },

    "R41": {
        "run_time": "04-19 12:30",
        "entry_price": 75000.0,
        "actual": "UP",
        "move": 600.0,
        "mfe_4h": 665.7,
        "mae_4h": 136.4,
        "close_price": 75600.0,
        "close_time": "04-19 15:22",
        "override": "counter_signal",
        "override_reason": "Sistem SHORT DIKKATLI COK KUCUK (FIX5 gecikmeli giris); Eren CVD divergence + taker_ls flip + funding premium + OI short-cover gorerek LONG counter-play acti. Kapanista sistem kendisi SHORT GEC konumuna geldi (sc=LONG dondu), tez dogrulandi.",
        "direction_taken": "LONG",
        "leading_at_entry": "DIKKATLI NOTR (SHORT_ZAYIF, guven ORTA, Whale 0.78<0.90, LS 0.77<0.85)",
        "sc_at_entry": "GIRME SHORT (COK_KUCUK_BOYUT, meta+0.5, FIX5_GECIKMELI_GIRIS |h1|=1.81>1.5)",
        "size_btc": 0.0,
        "notional_usd": 0.0,
        "atr_15m": 151.9,
        "sl_target": 0.0,
        "tp1_target": 0.0,
        "tp2_target": 0.0,
        "be_tetik_target": 0.0,
        "exit_reason": "MANUEL (piyasa LONG dondu, +$600 de Eren kapatti)",
        "be_triggered": False,
        "be_executed": False,
        "tp1_hit": False,
        "tp2_hit": False,
        "sl_hit": False,
        "gross_pnl_usd": 0.0,
        "result_r": 0.0,
        "balance_usd": 2100,
        "actual_risk_pct": 0.0,
        "leverage_actual": 0.0,
        "risk_violation": False,
        "risk_violation_note": "Boyut/PnL detayi alinmadi (cok ufak counter-play etiketi). Ana kayit degeri: sistem snapshot + fiyat hareketi + counter-signal pattern.",
        "system_long_w_at_signal": 0.0,
        "system_short_w_at_signal": 0.4783,
        "system_margin_at_signal": 0.4783,
        "leading_yon_at_signal": "NOTR",
        "leading_karar_at_signal": "DIKKATLI (SHORT_ZAYIF, guven ORTA)",
        "sc_yon_at_signal": "SHORT",
        "sc_karar_at_signal": "GIRME (COK_KUCUK_BOYUT, meta+0.5)",
        "data_5m": {"current_price": 75449.2, "ma5": 75542.72, "ma10": 75553.36, "ma30": 75311.49, "volume": 13869979, "volume_ma5": 40190570, "volume_ma10": 37499989, "net_long": 0.4385, "net_short": 0.5615, "futures_cvd": -2078146, "spot_cvd": 0, "taker_ls_ratio": 0.7006, "oi": 97383, "oi_delta": -11, "liquidations": {"long": 0, "short": 0}, "ma5_slope": 3.202, "cvd_momentum": -1.4406, "ls_slope": -0.18786, "oi_slope": -53.08, "oi_accel": 3.22, "np_slope": 1e-05, "depth_imbalance": 0.2464},
        "data_15m": {"current_price": 75460.7, "ma5": 75520.36, "ma10": 75358.78, "ma30": 75265.64, "volume": 14218944, "volume_ma5": 84821106, "volume_ma10": 85475319, "net_long": 0.4385, "net_short": 0.5615, "futures_cvd": -1804339, "spot_cvd": 0, "taker_ls_ratio": 1.0806, "oi": 97383, "oi_delta": -161, "liquidations": {"long": 0, "short": 0}, "ma5_slope": 78.81, "cvd_momentum": -0.531, "ls_slope": -0.08899, "oi_slope": 0.62, "oi_accel": -32.83, "np_slope": -0.00014, "depth_imbalance": 0.2464},
        "data_1h": {"current_price": 75460.8, "ma5": 75277.66, "ma10": 75355.54, "ma30": 75764.38, "volume": 273483591, "volume_ma5": 270762748, "volume_ma10": 291917267, "net_long": 0.4389, "net_short": 0.5611, "futures_cvd": 2495322, "spot_cvd": 0, "taker_ls_ratio": 1.4494, "oi": 97525, "oi_delta": 110, "liquidations": {"long": 0, "short": 0}, "ma5_slope": -60.934, "cvd_momentum": 0.5065, "ls_slope": 0.14897, "oi_slope": 78.76, "oi_accel": -13.86, "np_slope": 0.00038, "depth_imbalance": 0.2464, "whale_acct_ls": 0.7821, "funding_rate": -9.202e-05},
        "data_4h": {"current_price": 75460.8, "ma5": 75470.12, "ma10": 75899.69, "ma30": 75312.68, "volume": 273645907, "volume_ma5": 816604267, "volume_ma10": 1161602966, "net_long": 0.4389, "net_short": 0.5611, "futures_cvd": 2470042, "spot_cvd": 0, "taker_ls_ratio": 1.1894, "oi": 97525, "oi_delta": 372, "liquidations": {"long": 0, "short": 0}, "ma5_slope": -211.58, "cvd_momentum": -0.9012, "ls_slope": 0.05114, "oi_slope": -383.51, "oi_accel": 574.22, "np_slope": -0.00301, "depth_imbalance": 0.2464},
        "api_open_interest": [["04-18 07:00", 106361.26], ["04-19 12:00", 97524.64]],
        "api_taker_ls": [["04-18 06:00", 0.9334], ["04-19 11:00", 1.4494]],
        "whale_acct_ls": 0.7821,
        "_snapshot_source": "r_update.json @ 2026-04-19 15:33:29 (otomatik, add_run v2)"
    },

    "R42": {
        "run_time": "04-20 18:03",
        "entry_price": 74800.0,
        "actual": "UP",
        "move": 900.0,
        "mfe_4h": 1731.0,
        "mae_4h": 0.0,
        "close_price": 75700.0,
        "close_time": "04-20 18:57",
        "override": "counter_signal",
        "override_reason": "Sistem SHORT-ONLY mod LONG sinyalini NOTR'a cevirdi (sc=LONG w=0.4783 meta=0 GUVEN=YUKSEK). Eren TF split (4h/1h LONG 1.04/1.07), depth_imbalance 0.44->5.32 ALICI flip, rejim TRANSITION (ADX=23.3), funding hafif SHORT crowding (-3e-5), OI_30h azalis (-3533) gorerek LONG counter-play acti. SL yazilmadi - manuel izleme. R41'den farkli: CVD tum TF negatif, whale 0.77 bear.",
        "direction_taken": "LONG",
        "leading_at_entry": "NOTR GIRME SINYAL_YOK (hicbir kural tetiklenmedi)",
        "sc_at_entry": "LONG GIR KUCUK_BOYUT (meta=0.0 GUVEN=YUKSEK)",
        "size_btc": 0.1,
        "notional_usd": 7480.0,
        "atr_15m": 228.6,
        "sl_target": 0.0,
        "tp1_target": 76000.0,
        "tp2_target": 0.0,
        "be_tetik_target": 0.0,
        "exit_reason": "Manuel kapatma (+$900 kar, flow alirim baskisi devam ediyor diye)",
        "be_triggered": False,
        "be_executed": False,
        "tp1_hit": False,
        "tp2_hit": False,
        "sl_hit": False,
        "gross_pnl_usd": 90.0,
        "result_r": 1.125,
        "balance_usd": 2100,
        "actual_risk_pct": 0.0,
        "leverage_actual": 3.56,
        "risk_violation": True,
        "risk_violation_note": "SL YAZILMADI (manuel izleme karari). Counter-play 0.1 BTC ($7,480 notional) R41 'cok ufak' etiketinden agresif. Mental SL $74,000 (-$80, %3.8 bakiye). TP otomatik $76,000.",
        "system_long_w_at_signal": 0.4783,
        "system_short_w_at_signal": 0.0,
        "system_margin_at_signal": 0.4783,
        "leading_yon_at_signal": "NOTR",
        "leading_karar_at_signal": "GIRME (SINYAL_YOK, hicbir kural tetiklenmedi)",
        "sc_yon_at_signal": "LONG",
        "sc_karar_at_signal": "GIR KUCUK_BOYUT (meta=0.0 GUVEN=YUKSEK)",
        "data_5m": {"current_price": 74959.9, "ma5": 75204.38, "ma10": 75282.19, "ma30": 75212.55, "volume": 95669267, "volume_ma5": 84221563, "volume_ma10": 82545270, "net_long": 0.4379, "net_short": 0.5621, "futures_cvd": -16740861, "spot_cvd": 0, "taker_ls_ratio": 0.5718, "oi": 95409, "oi_delta": 65, "liquidations": {"long": 0, "short": 0}, "ma5_slope": -11.8, "cvd_momentum": -5.7418, "ls_slope": -0.02713, "oi_slope": 0.14, "oi_accel": -23.24, "np_slope": 0.00025, "depth_imbalance": 5.3204},
        "data_15m": {"current_price": 74929.2, "ma5": 75204.28, "ma10": 75195.76, "ma30": 75093.16, "volume": 312900482, "volume_ma5": 215978288, "volume_ma10": 185149010, "net_long": 0.4364, "net_short": 0.5636, "futures_cvd": -68781690, "spot_cvd": 0, "taker_ls_ratio": 0.8251, "oi": 95321, "oi_delta": 120, "liquidations": {"long": 0, "short": 0}, "ma5_slope": 16.438, "cvd_momentum": -2.5513, "ls_slope": -0.02308, "oi_slope": 98.57, "oi_accel": 15.13, "np_slope": -0.00014, "depth_imbalance": 5.3204},
        "data_1h": {"current_price": 74967.8, "ma5": 75117.5, "ma10": 74908.11, "ma30": 74890.36, "volume": 919413517, "volume_ma5": 548732677, "volume_ma10": 528413223, "net_long": 0.4366, "net_short": 0.5634, "futures_cvd": -53431984, "spot_cvd": 0, "taker_ls_ratio": 1.0721, "oi": 94985, "oi_delta": 449, "liquidations": {"long": 0, "short": 0}, "ma5_slope": 103.138, "cvd_momentum": -1.4546, "ls_slope": -0.04092, "oi_slope": -35.42, "oi_accel": 76.5, "np_slope": -0.00061, "depth_imbalance": 5.3204, "whale_acct_ls": 0.7751, "funding_rate": -3.03e-05},
        "data_4h": {"current_price": 74967.8, "ma5": 74652.86, "ma10": 75022.58, "ma30": 75455.72, "volume": 2178303562, "volume_ma5": 1867809798, "volume_ma10": 1669353899, "net_long": 0.4374, "net_short": 0.5626, "futures_cvd": -15625499, "spot_cvd": 0, "taker_ls_ratio": 1.044, "oi": 94744, "oi_delta": -415, "liquidations": {"long": 0, "short": 0}, "ma5_slope": -177.356, "cvd_momentum": -2.6484, "ls_slope": 0.0455, "oi_slope": -527.23, "oi_accel": 138.17, "np_slope": 0.00092, "depth_imbalance": 5.3204},
        "api_open_interest": [["04-19 09:00", 97371.68], ["04-20 14:00", 94985.03]],
        "api_taker_ls": [["04-19 08:00", 1.0757], ["04-20 13:00", 1.0721]],
        "whale_acct_ls": 0.7751,
        "_snapshot_source": "r_update.json @ 2026-04-20 17:59:18 (otomatik, add_run v2) | P82 FIX: mfe_4h 0.0->1731.0, mae_4h 0.0 korundu (CANDLES_15M backfill, 13 mum, entry=74800, max_high=76531, min_low=74800)"
    },
}

# =================== CIKTI ===================

def _get_stored_mfe_mae(rd, direction, window_hours=4):
    """Kapali run icin saklanan MFE/MAE degerlerini don.
    Eski run'larda mfe_4h formatı tutarsız olabilir (R2-R29 ters perspektif).
    Güvenli kullanım: (1) direction-specific alanlar (mfe_long/mfe_short), VEYA
    (2) yeni format göstergeleri (entry_price veya mfe_short) ile mfe_4h/mae_4h.
    P82 FIX: entry_price koşulu eklendi — R40/R41 artık Branch 2'de yakalaniyor."""
    if rd.get("actual") is None or rd.get("actual") == "?":
        return None
    # 1) Direction-specific fields (en güvenli — R33 tarzı)
    if direction == "LONG" and "mfe_long" in rd and rd["mfe_long"] is not None:
        return {"mfe": rd["mfe_long"], "mae": rd.get("mae_long", 0),
                "max_high": 0, "min_low": 0, "candles_used": 99}
    if direction == "SHORT" and "mfe_short" in rd and rd["mfe_short"] is not None:
        return {"mfe": rd["mfe_short"], "mae": rd.get("mae_short", 0),
                "max_high": 0, "min_low": 0, "candles_used": 99}
    # 2) mfe_4h — yeni format göstergeleri varsa güvenilir
    #    (R33+ entry_price VEYA R33-R37 mfe_short; eski R2-R29 ters perspektif riski var)
    if "mfe_4h" in rd and "mae_4h" in rd and window_hours <= 4:
        yeni_format = ("entry_price" in rd or "mfe_short" in rd)
        if yeni_format and (rd["mfe_4h"] > 0 or rd["mae_4h"] > 0):
            return {"mfe": rd["mfe_4h"], "mae": rd["mae_4h"],
                    "max_high": 0, "min_low": 0, "candles_used": 99}
    return None

def _get_mfe_mae_for_run(rd, direction, run_time, window_hours=4):
    """Post-mortem icin stabil MFE/MAE.
    Kapali run: stored values → 1h klines → 4h klines.
    Acik run: normal cascade (15m→1h→4h)."""
    p = rd["data_1h"]["current_price"]
    if rd.get("actual") is not None and rd.get("actual") != "?":
        # 1) Stored values (kapanista hesaplandi — en dogru)
        stored = _get_stored_mfe_mae(rd, direction, window_hours)
        if stored is not None:
            return stored
        # 2) 1h klines (15m'den stabil)
        if CANDLES_1H:
            first_1h = _parse_candle_time(CANDLES_1H[0][0])
            rt_dt = _dt.strptime(f"{_TRADE_YEAR}-{run_time}", "%Y-%m-%d %H:%M") if run_time else None
            if rt_dt and first_1h <= rt_dt + _td(hours=1):
                r1h = _calc_mfe_mae_from_candles(CANDLES_1H, 1, p, direction, run_time, window_hours)
                if r1h["candles_used"] > 0:
                    return r1h
        # 3) 4h fallback
        r4h = _calc_mfe_mae_from_candles(CANDLES_4H, 4, p, direction, run_time, window_hours)
        if r4h["candles_used"] > 0:
            return r4h
    # Acik run: normal cascade
    return calc_mfe_mae(p, direction, run_time, window_hours=window_hours)

def get_active_run():
    """Aktif run numarasini hesapla.
    HISTORICAL_DATA'daki en yuksek numarali actual=None entry = aktif run.
    Hepsi doluysa → max + 1 (sonraki run)."""
    candidates = [int(k[1:]) for k, v in HISTORICAL_DATA.items() if v.get("actual") is None]
    if candidates:
        return max(candidates)
    return max((int(k[1:]) for k in HISTORICAL_DATA), default=0) + 1

def print_scores_and_direction(result, price):
    d = result
    _run = get_active_run()
    print(f"\n{'X'*70}")
    print(f"  YON-5 | RUN-{_run} — ${price:,.1f}")
    print(f"{'X'*70}")
    for tf, label, det, total in [("15m","15m",d["det15"],d["h15"]),("1h","1h <-- YON",d["det1h"],d["h1"]),("4h","4h",d["det4h"],d["h4"])]:
        print(f"\n  -- {label} TOPLAM: {total:+.4f} --")
        for k, v in sorted(det.items(), key=lambda x: x[1]["final"]):
            raw = v["raw"]; final = v["final"]
            icon = "[+]" if raw > 0.05 else ("[-]" if raw < -0.05 else "[ ]")
            k3_info = ""
            if k == "K3_NETPOS" and "k3_gate" in v:
                k3_info = f"  gate={v['k3_gate']} dev={v.get('k3_deviation',0):.4f}"
            print(f"    {icon} {k:<20s} raw={raw:+.3f} final={final:+.4f}{k3_info}")
    print(f"\n{'='*70}")
    print(f"  KATMAN 1 — YON:    {d['direction']}")
    print(f"    1h = {d['h1']:+.4f}  (notr: +/-{NEUTRAL_ZONE})")
    print(f"  KATMAN 2 — GUVEN:  {d['confidence']}")
    h14 = "AYNI YON" if d["h1"] * d["h4"] > 0 else "TERS YON"
    h14_detail = h14
    if h14 == "AYNI YON" and abs(d["h4"]) < 0.50:
        h14_detail = f"AYNI YON ama |4h|={abs(d['h4']):.2f} < 0.50 — zayif"
    print(f"    4h = {d['h4']:+.4f}  ({h14_detail})")
    if d["climax"]: print(f"    ! {d['climax']}")
    if d["contradiction"] >= 2: print(f"    ! TF celiski: {d['contradiction']}/3")
    print(f"  KATMAN 3 — BOYUT:  {d['size']}")
    for f in d["flags"]: print(f"    >> {f}")
    print(f"\n  +{'='*50}+")
    print(f"  | {d['direction']} {d['size']:<42s}|")
    print(f"  | 1h={d['h1']:+.4f}  4h={d['h4']:+.4f}  Guven={d['confidence']:<8s}  |")
    print(f"  +{'='*50}+")
    
    # P54 TRAP DISPLAY
    _trap = d.get("trap", {})
    if _trap.get("triggered"):
        print(f"\n  ⚠️ WHALE+OI TRAP TETİKLENDİ!")
        print(f"    whale_acct_ls={_trap['whale_ls']:.4f} (< 0.86) + OI yükseliyor (+{_trap['oi_delta']:.0f})")
        print(f"    h1: {_trap['h1_before']:+.4f} → {_trap['h1_after']:+.4f} (penaltı: {_trap['penalty']})")
        print(f"    Akıllı para SHORT, retail LONG → dağıtım tuzağı")

    # =================== SHADOW K8_WHALE (GOZLEM MODU) ===================
    # Whale account L/S verisi varsa shadow skor hesapla
    # Scorecard skorunu DEGISTIRMEZ — sadece bilgi
    _active_label = f"R{_run}"
    _whale_ls = HISTORICAL_DATA.get(_active_label, {}).get("whale_acct_ls")
    if _whale_ls is not None:
        _run_data = HISTORICAL_DATA[_active_label]
        _taker_ls = _run_data["data_1h"].get("taker_ls_ratio", 1.0)
        _k8_taker = clamp((_taker_ls - 1.0) / 0.3)
        _k8_whale = clamp((_whale_ls - 1.0) / 0.3)
        _k8_taker_contrib = _k8_taker * WEIGHTS["K8_LS"]
        _k8_whale_contrib = _k8_whale * WEIGHTS["K8_LS"]
        _h1_with_whale = d["h1"] - _k8_taker_contrib + _k8_whale_contrib
        _divergence = abs(_taker_ls - _whale_ls)
        _div_flag = "CELISIK" if (_taker_ls > 1.0 and _whale_ls < 1.0) or (_taker_ls < 1.0 and _whale_ls > 1.0) else "UYUMLU"
        print(f"\n  --- SHADOW K8_WHALE (GOZLEM — SKORU DEGISTIRMEZ) ---")
        print(f"    Taker LS:  {_taker_ls:.3f} → K8={_k8_taker:+.3f} × {WEIGHTS['K8_LS']} = {_k8_taker_contrib:+.3f}")
        print(f"    Whale LS:  {_whale_ls:.4f} → K8={_k8_whale:+.3f} × {WEIGHTS['K8_LS']} = {_k8_whale_contrib:+.3f}")
        print(f"    Divergence: {_divergence:.3f} ({_div_flag})")
        print(f"    1h MEVCUT:      {d['h1']:+.4f} (taker K8 ile)")
        print(f"    1h WHALE ILE:   {_h1_with_whale:+.4f} (shadow)")
        _shadow_dir = "LONG" if _h1_with_whale > 0.10 else ("SHORT" if _h1_with_whale < -0.10 else "NOTR")
        if _shadow_dir != d["direction"]:
            print(f"    !! YON FARKI: mevcut={d['direction']} shadow={_shadow_dir}")
        print(f"  --- (adoption: 10 run gozlem sonrasi) ---")

def print_wf_quality(result):
    """KATMAN 4 — Walk-Forward giriş kalitesi (Uyarı Modu)."""
    d = result

    # =================== KATMAN 4 — WALK-FORWARD BOYUT UYARISI ===================
    # Son N run'in MFE/MAE oranina bakarak giris kalitesini degerlendir
    # UYARI MODU: Boyutu degistirmez, sadece bilgilendirir (20 run'a kadar)
    wf_window = 3  # Son kac run'a bak
    wf_ratios = []
    wf_details = []
    # Once historical run'lardan topla (NOTR haric)
    for rlabel in sorted(HISTORICAL_DATA.keys(), key=lambda x: int(x[1:])):
        rd = HISTORICAL_DATA[rlabel]
        rr = compute_scorecard(rd["data_15m"], rd["data_1h"], rd["data_4h"], whale_ls=rd.get("whale_acct_ls"), oi_data=rd.get("api_open_interest", []))
        if rr["direction"] == "NOTR":
            continue
        rt = rd.get("run_time", "")
        m4 = _get_mfe_mae_for_run(rd, rr["direction"], rt, window_hours=4)
        if m4["candles_used"] > 0 and m4["mfe"] > 0:
            ratio = m4["mae"] / m4["mfe"]
            wf_ratios.append(ratio)
            wf_details.append({"label": rlabel, "ratio": ratio, "mfe": m4["mfe"], "mae": m4["mae"]})
    # Sonra log run'lardan topla
    for lr in load_log():
        if lr["direction"] == "NOTR":
            continue
        rt = lr.get("run_time", lr.get("timestamp", ""))
        m4 = calc_mfe_mae(lr["price"], lr["direction"], rt, window_hours=4)
        if m4["candles_used"] > 0 and m4["mfe"] > 0:
            ratio = m4["mae"] / m4["mfe"]
            wf_ratios.append(ratio)
            wf_details.append({"label": lr["label"], "ratio": ratio, "mfe": m4["mfe"], "mae": m4["mae"]})

    print(f"\n{'='*70}")
    print(f"  KATMAN 4 — WALK-FORWARD GIRIS KALITESI (UYARI MODU)")
    print(f"{'='*70}")

    if len(wf_ratios) < wf_window:
        print(f"  Yetersiz veri: {len(wf_ratios)} run (min {wf_window} gerekli)")
        wf_suggested = None
    else:
        # Son N run'in ortalamasi
        last_n = wf_details[-wf_window:]
        avg_ratio = sum(r["ratio"] for r in last_n) / len(last_n)
        # Kalite siniflandirmasi
        if avg_ratio < 0.4:
            quality = "COK IYI"
            wf_suggested = "NORMAL BOYUT"
        elif avg_ratio < 0.7:
            quality = "IYI"
            wf_suggested = "NORMAL BOYUT"
        elif avg_ratio < 1.0:
            quality = "ORTA"
            wf_suggested = "KUCUK BOYUT"
        else:
            quality = "KOTU"
            wf_suggested = "COK KUCUK BOYUT"

        print(f"  Son {wf_window} run (4h pencere):")
        for r in last_n:
            q = "iyi" if r["ratio"] < 0.5 else ("orta" if r["ratio"] < 1.0 else "kotu")
            print(f"    {r['label']:<5s} MFE={r['mfe']:>+7.0f}  MAE={r['mae']:>-7.0f}  oran={r['ratio']:.2f} ({q})")
        print(f"  Ortalama MAE/MFE: {avg_ratio:.2f} → Kalite: {quality}")
        print(f"  WF onerisi: {wf_suggested}")

        # Mevcut boyutla karsilastir
        if d['direction'] != "NOTR":
            if wf_suggested != d['size']:
                print(f"  !! UYARI: Scorecard '{d['size']}' diyor, WF '{wf_suggested}' oneriyor")
            else:
                print(f"  OK: Scorecard ve WF ayni boyutta")

        # Tum run'larin ozet istatistikleri
        all_mfes = [r["mfe"] for r in wf_details]
        all_maes = [r["mae"] for r in wf_details]
        all_ratios = [r["ratio"] for r in wf_details]
        print(f"\n  Tum runlar ({len(wf_details)} adet):")
        print(f"    Ort MFE: ${sum(all_mfes)/len(all_mfes):,.0f}  Ort MAE: ${sum(all_maes)/len(all_maes):,.0f}")
        print(f"    Ort MAE/MFE: {sum(all_ratios)/len(all_ratios):.2f}")
        print(f"    En iyi:  {min(wf_details, key=lambda x: x['ratio'])['label']} ({min(all_ratios):.2f})")
        print(f"    En kotu: {max(wf_details, key=lambda x: x['ratio'])['label']} ({max(all_ratios):.2f})")
    print(f"  [!] Bu katman UYARI MODU'nda — boyutu degistirmiyor (20 run'a kadar)")


def print_historical_table():
    """Geçmiş runlar tablosu + ölçüm karşılaştırması."""
    # Gecmis run tablosu — IKILI OLCUM STANDARDI
    print(f"\n{'='*110}")
    print(f"  GECMIS RUNLAR — IKILI OLCUM (Yon: 4h fiyat | Kalite: MAE/MFE < {QUALITY_THRESHOLD})")
    print(f"{'='*110}")
    print(f"  {'Run':<4s} {'Fiyat':>8s} {'1h':>8s} {'Yon':>6s} {'Guven':>7s} {'Gercek':>6s} {'MFE4h':>7s} {'MAE4h':>7s} {'Oran':>6s} {'SONUC':<16s} {'MFE24h':>7s} {'MAE24h':>7s} {'Mum':>4s}")
    print(f"  {'-'*108}")

    # Sayaclar
    _eval_counts = {"BASARILI": 0, "GIRIS_KOTU": 0, "YON_YANLIS": 0, "BASARISIZ": 0,
                    "KACINILDI": 0, "BEKLIYOR": 0, "YON_OK_VERI_YOK": 0, "YON_X_VERI_YOK": 0}
    _old_ok = 0; _old_total = 0

    for rlabel in sorted(HISTORICAL_DATA.keys(), key=lambda x: int(x[1:])):
        rd = HISTORICAL_DATA[rlabel]
        rr = compute_scorecard(rd["data_15m"], rd["data_1h"], rd["data_4h"], whale_ls=rd.get("whale_acct_ls"), oi_data=rd.get("api_open_interest", []))
        act = rd.get("actual") or "?"
        p = rd["data_1h"]["current_price"]
        rt = rd.get("run_time", "")
        m4 = _get_mfe_mae_for_run(rd, rr["direction"], rt, window_hours=4)
        m24 = _get_mfe_mae_for_run(rd, rr["direction"], rt, window_hours=24)

        # Ikili degerlendirme
        mfe4 = m4["mfe"] if m4["candles_used"] > 0 else None
        mae4 = m4["mae"] if m4["candles_used"] > 0 else None
        ev = eval_actual(rr["direction"], act, mfe4, mae4)
        _eval_counts[ev["label"]] = _eval_counts.get(ev["label"], 0) + 1

        # Eski sistem karsilastirma
        if rr["direction"] != "NOTR" and act not in ("?", None, "BELIRSIZ"):
            _old_total += 1
            if (rr["direction"]=="LONG" and act=="UP") or (rr["direction"]=="SHORT" and act=="DOWN"):
                _old_ok += 1

        # Satir yazdir
        ratio_s = f"{ev['ratio']:.2f}" if ev["ratio"] is not None else "---"
        if rr["direction"] == "NOTR":
            print(f"  {rlabel:<4s} ${p:>7,.0f} {rr['h1']:>+8.4f} {'NOTR':>6s} {rr['confidence']:>7s} {'---':>6s} {'---':>7s} {'---':>7s} {'---':>6s} {'KACINILDI':<16s} {'---':>7s} {'---':>7s} {'---':>4s}")
        elif m4["candles_used"] == 0:
            print(f"  {rlabel:<4s} ${p:>7,.0f} {rr['h1']:>+8.4f} {rr['direction']:>6s} {rr['confidence']:>7s} {act:>6s} {'?':>7s} {'?':>7s} {'---':>6s} {ev['label']:<16s} {'?':>7s} {'?':>7s} {'0':>4s}")
        else:
            mfe4s = f"+{int(m4['mfe'])}"; mae4s = f"-{int(m4['mae'])}"
            mfe24s = f"+{int(m24['mfe'])}"; mae24s = f"-{int(m24['mae'])}"
            print(f"  {rlabel:<4s} ${p:>7,.0f} {rr['h1']:>+8.4f} {rr['direction']:>6s} {rr['confidence']:>7s} {act:>6s} {mfe4s:>7s} {mae4s:>7s} {ratio_s:>6s} {ev['label']:<16s} {mfe24s:>7s} {mae24s:>7s} {m24['candles_used']:>4d}")

    # Log runs
    for lr in load_log():
        act = lr.get("actual_dir") or "?"
        rt = lr.get("run_time", lr.get("timestamp", ""))
        m4 = calc_mfe_mae(lr["price"], lr["direction"], rt, window_hours=4)
        m24 = calc_mfe_mae(lr["price"], lr["direction"], rt, window_hours=24)

        mfe4 = m4["mfe"] if m4["candles_used"] > 0 else None
        mae4 = m4["mae"] if m4["candles_used"] > 0 else None
        ev = eval_actual(lr["direction"], act, mfe4, mae4)
        _eval_counts[ev["label"]] = _eval_counts.get(ev["label"], 0) + 1

        if lr["direction"] != "NOTR" and act not in ("?", None, "BELIRSIZ"):
            _old_total += 1
            if (lr["direction"]=="LONG" and act=="UP") or (lr["direction"]=="SHORT" and act=="DOWN"):
                _old_ok += 1

        ratio_s = f"{ev['ratio']:.2f}" if ev["ratio"] is not None else "---"
        if lr["direction"] == "NOTR" or m4["candles_used"] == 0:
            mfe4s = mae4s = mfe24s = mae24s = "?"
            mc = "0"
        else:
            mfe4s = f"+{int(m4['mfe'])}"; mae4s = f"-{int(m4['mae'])}"
            mfe24s = f"+{int(m24['mfe'])}"; mae24s = f"-{int(m24['mae'])}"
            mc = str(m24["candles_used"])
        print(f"  {lr['label']:<4s} ${lr['price']:>7,.0f} {lr['h1']:>+8.4f} {lr['direction']:>6s} {lr['confidence']:>7s} {act:>6s} {mfe4s:>7s} {mae4s:>7s} {ratio_s:>6s} {ev['label']:<16s} {mfe24s:>7s} {mae24s:>7s} {mc:>4s} [L]")

    # Ozet — eski vs yeni karsilastirma
    print(f"\n  {'='*60}")
    print(f"  OLCUM KARSILASTIRMASI")
    print(f"  {'='*60}")
    print(f"  YON ($1000 MFE ilk yon): {_old_ok}/{_old_total} dogru ({_old_ok/_old_total*100:.0f}%)" if _old_total > 0 else "  YON: veri yok")
    _new_ok = _eval_counts.get("BASARILI", 0)
    _new_total = _new_ok + _eval_counts.get("GIRIS_KOTU", 0) + _eval_counts.get("YON_YANLIS", 0) + _eval_counts.get("BASARISIZ", 0)
    print(f"  YENI (yon+kalite): {_new_ok}/{_new_total} basarili ({_new_ok/_new_total*100:.0f}%)" if _new_total > 0 else "  YENI: veri yok")
    print(f"    BASARILI:    {_eval_counts.get('BASARILI', 0)}")
    print(f"    GIRIS_KOTU:  {_eval_counts.get('GIRIS_KOTU', 0)}")
    print(f"    YON_YANLIS:  {_eval_counts.get('YON_YANLIS', 0)}")
    print(f"    BASARISIZ:   {_eval_counts.get('BASARISIZ', 0)}")
    print(f"    BELIRSIZ:    {_eval_counts.get('BELIRSIZ', 0)}")
    print(f"    KACINILDI:   {_eval_counts.get('KACINILDI', 0)}")
    print(f"    BEKLIYOR:    {_eval_counts.get('BEKLIYOR', 0)}")
    print(f"  Kalite esigi: MAE/MFE < {QUALITY_THRESHOLD} (20 run'da revize edilecek)")

# =================== KATMAN 6 — SON RUN KARSILASTIRMA ===================
# Son 3 yonlu run'in (NOTR haric, actual olan) ham metriklerini mevcut run
# ile yan yana gosterir. Salt veri — otomatik UYARI yok.
# Backtest sonucu: Binary flag sistemi FIX-3/5/6 esikleriyle %100 cakisiyordu
# (0 ozgun katki, %33 FP). Tablo ham metrikleri gosterir, karar Eren'in.
# 20 run'da surekli benzerlik skoruna (continuous distance) gecilebilir.

def extract_run_metrics(d15, d1h, d4h, direction, h1, h4):
    """Bir run'in ham verisinden karsilastirma metriklerini cikar."""
    vol = d1h.get("volume", 0)
    vol_ma5 = d1h.get("volume_ma5", 0)
    vol_ma10 = d1h.get("volume_ma10", 0)
    avg_vol = (vol_ma5 + vol_ma10) / 2.0
    vol_ratio = vol / avg_vol if avg_vol > 0 else 1.0

    ls = d1h.get("taker_ls_ratio", 1.0)
    ls_opp = 0.0
    if direction == "SHORT" and ls > 1.0:
        ls_opp = ls - 1.0
    elif direction == "LONG" and ls < 1.0:
        ls_opp = 1.0 - ls

    k6_15m_raw = score_liquidations(d15)[0]
    k6_1h_raw = score_liquidations(d1h)[0]

    return {
        "vol_ratio": round(vol_ratio, 3),
        "ls_raw": round(ls, 3),
        "ls_opp": round(ls_opp, 3),
        "abs_h1": round(abs(h1), 4),
        "abs_h4": round(abs(h4), 4),
        "direction": direction,
        "k6_15m": round(k6_15m_raw, 3),
        "k6_1h": round(k6_1h_raw, 3),
    }

def print_recent_comparison(current_result, d15, d1h, d4h):
    """KATMAN 6: Son 3 yonlu run ile mevcut run — salt metrik tablosu.
    Otomatik UYARI yok. Veriyi goster, karar Eren'in."""

    d = current_result
    _run = get_active_run()
    print(f"\n{'='*70}")
    print(f"  KATMAN 6 — SON RUN KARSILASTIRMA | RUN-{_run}")
    print(f"{'='*70}")

    if d["direction"] == "NOTR":
        print(f"  NOTR sinyal — karsilastirma uygulanmaz")
        return

    if d1h.get("current_price", 0) == 0:
        print(f"  Veri girilmemis (price=0) — karsilastirma atlanir")
        return

    curr = extract_run_metrics(d15, d1h, d4h, d["direction"], d["h1"], d["h4"])

    # Son 3 yonlu run'i bul (actual != None, direction != NOTR)
    recent = []
    for rlabel in sorted(HISTORICAL_DATA.keys(), key=lambda x: int(x[1:]), reverse=True):
        rd = HISTORICAL_DATA[rlabel]
        if rd.get("actual") is None or rd.get("actual") == "?" or rd.get("actual") == "BELIRSIZ":
            continue
        rr = compute_scorecard(rd["data_15m"], rd["data_1h"], rd["data_4h"], whale_ls=rd.get("whale_acct_ls"), oi_data=rd.get("api_open_interest", []))
        if rr["direction"] == "NOTR":
            continue
        rt = rd.get("run_time", "")
        m4 = _get_mfe_mae_for_run(rd, rr["direction"], rt, window_hours=4)
        ev = eval_actual(rr["direction"], rd["actual"], m4["mfe"], m4["mae"])
        rm = extract_run_metrics(rd["data_15m"], rd["data_1h"], rd["data_4h"],
                                  rr["direction"], rr["h1"], rr["h4"])
        rm["outcome"] = ev["label"]
        rm["label"] = rlabel
        rm["mae_mfe"] = ev["ratio"]
        recent.append(rm)
        if len(recent) >= 3:
            break

    if len(recent) == 0:
        print(f"  Karsilastirma icin yeterli gecmis run yok")
        return

    # --- TABLO: Yan yana metrik karsilastirmasi ---
    labels = ["MEVCUT"] + [r["label"] for r in recent]
    all_m = [curr] + recent

    print(f"\n  {'Metrik':<14s}", end="")
    for lbl in labels:
        print(f" {lbl:>12s}", end="")
    print()
    print(f"  {'-'*14}", end="")
    for _ in labels:
        print(f" {'-'*12}", end="")
    print()

    rows = [
        ("Yon",       lambda m: m["direction"]),
        ("vol_ratio", lambda m: f"{m['vol_ratio']:.3f}"),
        ("LS_raw",    lambda m: f"{m['ls_raw']:.3f}"),
        ("LS_opp",    lambda m: f"{m['ls_opp']:.3f}"),
        ("|1h|",      lambda m: f"{m['abs_h1']:.4f}"),
        ("|4h|",      lambda m: f"{m['abs_h4']:.4f}"),
        ("K6_15m",    lambda m: f"{m['k6_15m']:+.3f}"),
        ("K6_1h",     lambda m: f"{m['k6_1h']:+.3f}"),
    ]
    for name, fn in rows:
        print(f"  {name:<14s}", end="")
        for m in all_m:
            print(f" {fn(m):>12s}", end="")
        print()

    # Sonuc + MAE/MFE (sadece gecmis runlar)
    print(f"\n  {'Sonuc:':<14s}")
    for r in recent:
        ratio_s = f"MAE/MFE={r['mae_mfe']:.2f}" if r["mae_mfe"] is not None else "MAE/MFE=---"
        print(f"    {r['label']:<7s}: {r['outcome']:<14s} ({ratio_s})")

# =================== KATMAN 7 + 7B KALDIRILDI (P69) ===================
# P69: Katman 7 (POST-MORTEM & DANIŞMA) ve Katman 7B (BENZERLİK MOTORU) kaldırıldı.
# Sebep: LOO backtest — K7B top-1 %63 (docstring iddiası %100), majority %59
# (baseline %56 ile eşdeğer). K7 profil negatif tarafı %0 doğruluk.
# Her iki katman meta-skora yanlış sinyal besliyordu.
# Kaldırılan fonksiyonlar: generate_postmortem, generate_all_postmortems,
# consult_postmortems, print_postmortem, print_consultation, print_all_postmortems,
# SIMILARITY_WEIGHTS, _extract_similarity_profile, find_similar_runs, print_similarity.

# =================== KATMAN 8 — SON KARAR (DİNAMİK) ===================
# Tum katmanlari tarar, kirmizi/yesil sinyal sayar, nihai oneri uretir.
# Scorecard skorunu DEGISTIRMEZ — karar destek katmani.
# PRENSIP: GIRME = pozisyon ACMA. TERS YONE GIR DEMEK DEGILDIR.
# Backtest kaynagi: S2 reverse stratejisi %71 — mevcut %82'den kotu.
# Ters yon onerisi ASLA uretilmez.

def compute_meta_score(result, signals, candle_result):
    """P51+P52: Tüm katman sinyallerini tek sayıya indir → binary GİR/GİRME.
    Pozitif = GİR, Sıfır veya negatif = GİRME. Eşik: > 0 (P52: strict).
    
    P52 değişiklikler (Ç9 — 26 run backtest):
      1. tf_uyum +1.5 → +1.0 (R6/R7 false positive azaltma)
      2. profil_zero -2.0 → P69: KALDIRILDI (K7 removed)
      3. Eşik >= 0 → > 0 (R14 boundary fix)
      Sonuç: GİR 6/6 = %100 (önceki: 6/9 = %67), FP: 0 (önceki: 3)
      R6/R7/R14 düzeltildi, R3/R4 korundu.
    
    Backtest (P51 orijinal, R2-R16):
      v2 ağırlıklar: GİR 8 run → 6 doğru (%75) vs eski FD %73.
      Bilinen false positive: R6 (k6_flush yetersiz), R7 (weak_h1 yetersiz).
    
    Bileşenler ve ağırlıklar:
      POZİTİF: v3a uyum (+1-3), TF 3'lü uyum (+1.0), güven YÜKSEK (+1.0),
               temiz flagler (+0.5), combo %100 (+1.0),
               son run başarılı (+0.5)
      NEGATİF: v3a ters (-1-3), V9-gecikme (-4.0),
               weak |h1| (-1.0), K6 flush (-1.5),
               son run başarısız (-1.0), çok flag (-1.0),
               combo kötü (-0.5),
               K8_LS aynı (-0.5), güven DÜŞÜK (-0.5),
               mum çelişki (-0.5/çelişki)
    """
    direction = result["direction"]
    if direction == "NOTR":
        return -99.0, {"reason": "NOTR"}, "BEKLE"
    
    score = 0.0
    breakdown = {}
    
    # ── 1. v3a OYLAMA ──
    v3a_total = 0
    for color, source, desc in signals:
        if source == "V3A_OYLAMA":
            # Parse v3a total from desc: "... = +2 → LONG"
            m = re.search(r'=\s*([+-]?\d+)\s*→', desc)
            if m:
                v3a_total = int(m.group(1))
            break
    
    v3a_aligned = (v3a_total > 0 and direction == "LONG") or \
                  (v3a_total < 0 and direction == "SHORT")
    v3a_contra = (v3a_total > 0 and direction == "SHORT") or \
                 (v3a_total < 0 and direction == "LONG")
    
    if v3a_aligned:
        pts = min(3.0, abs(v3a_total) * 1.0)
        score += pts
        breakdown["v3a_aligned"] = f"+{pts:.1f} (v3a={v3a_total:+d})"
    elif v3a_contra:
        pts = -min(3.0, abs(v3a_total) * 1.0)
        score += pts
        breakdown["v3a_contra"] = f"{pts:.1f} (v3a={v3a_total:+d})"
    elif v3a_total == 0:
        breakdown["v3a_neutral"] = "+0.0 (v3a=0)"
    
    # ── 2. TF UYUM ──
    signs_pos = [result["h15"] > 0.1, result["h1"] > 0.1, result["h4"] > 0.1]
    signs_neg = [result["h15"] < -0.1, result["h1"] < -0.1, result["h4"] < -0.1]
    if all(signs_pos) or all(signs_neg):
        score += 1.0
        breakdown["tf_uyum"] = "+1.0 (3TF aynı yön)"
    
    # ── 3. GÜVEN ──
    if result["confidence"] == "YUKSEK":
        score += 1.0
        breakdown["guven"] = "+1.0 (YÜKSEK)"
    elif result["confidence"] == "DUSUK":
        score -= 0.5
        breakdown["guven"] = "-0.5 (DÜŞÜK)"
    
    # ── 4. FLAG TEMİZLİĞİ ──
    flag_count = len(result.get("flags", []))
    if flag_count <= 1:
        score += 0.5
        breakdown["flags"] = f"+0.5 ({flag_count} flag)"
    elif flag_count >= 4:
        score -= 1.0
        breakdown["flags"] = f"-1.0 ({flag_count} flag)"
    
    # ── 5. V9-GECİKME ──
    has_v9 = any("V9-GECIKME" in f for f in result.get("flags", []))
    if has_v9:
        score -= 4.0
        breakdown["v9_gecikme"] = "-4.0 (|1h| > 1.50)"
    
    # ── 5b. ZAYIF |h1| ──
    abs_h1 = abs(result["h1"])
    if abs_h1 < 0.30:
        score -= 1.0
        breakdown["weak_h1"] = f"-1.0 (|h1|={abs_h1:.2f} < 0.30)"
    
    # ── 6. SİNYAL BAZLI SKORLAR ──
    for color, source, desc in signals:
        if source == "V3A_OYLAMA":
            continue
        
        # P69: DANISMA_1H_BAND ve BENZERLIK kaldırıldı (K7+K7B removed)
        if source == "SON_RUNLAR":
            if color == "KIRMIZI":
                score -= 1.0
                breakdown["son_run_fail"] = "-1.0"
            elif color == "YESIL":
                score += 0.5
                breakdown["son_run_ok"] = "+0.5"
        
        elif source == "TF_COMBO":
            if color == "KIRMIZI":
                score -= 0.5
                breakdown["combo_bad"] = "-0.5"
            elif color == "YESIL":
                score += 1.0
                breakdown["combo_good"] = "+1.0"
        
        elif source == "K8_LS_AYNI":
            score -= 0.5
            breakdown["k8_ayni"] = "-0.5"
        
        elif source == "K6_LIQ_FLUSH":
            score -= 1.5
            breakdown["k6_flush"] = "-1.5"
    
    # ── 7. MUM ÇELİŞKİSİ ──
    if candle_result and candle_result.get("conflict_flags"):
        n_conf = len(candle_result["conflict_flags"])
        pts = -0.5 * min(n_conf, 2)
        score += pts
        breakdown["mum_celiski"] = f"{pts:.1f} ({n_conf} çelişki)"
    
    # ── 8. PROFİL BAŞARI ORANI — P69: KALDIRILDI (K7 removed) ──
    
    # ── 9. TREND CONTRA PENALTİSİ (P52) ──
    # LS_TREND SC yönüne zıtsa → momentum dönüyor sinyali.
    # LS_TREND disc=0.752 — en güçlü trend göstergesi.
    # Backtest: mevcut GİR runların HİÇBİRİNİ etkilemiyor (sıfır regresyon).
    # ls_slope auto_fetch'ten gelir; yoksa 0 → tetiklenmez (backward compat).
    det1h = result.get("det1h", {})
    kt_ls = det1h.get("KT_LS_TREND", {})
    kt_ls_raw = kt_ls.get("raw", 0) if isinstance(kt_ls, dict) else 0
    if kt_ls_raw != 0:
        sc_long = direction == "LONG"
        sc_short = direction == "SHORT"
        if (sc_long and kt_ls_raw < -0.5) or (sc_short and kt_ls_raw > 0.5):
            score -= 1.5
            breakdown["ls_contra"] = f"-1.5 (LS trend={kt_ls_raw:+.2f} vs SC={direction})"
    
    score = round(score, 2)
    decision = "GIR" if score > 0 else "GIRME"
    return score, breakdown, decision

def compute_final_decision(result, d15, d1h, d4h, candle_result=None):
    """Tum katmanlari tarayarak dinamik GIR/DIKKATLI/GIRME karari uret.
    P51: Meta-skor entegrasyonu — tüm sinyaller tek sayıya indirilir.
    Returns: dict with decision, signals, meta_score, reasoning
    """
    direction = result["direction"]
    if direction == "NOTR":
        return {"decision": "BEKLE", "reason": "NOTR sinyal — pozisyon yok",
                "red": 0, "green": 0, "signals": []}
    
    signals = []  # (renk, kaynak, aciklama)
    
    # --- P69: KATMAN 7 DANISMA ve KATMAN 7B BENZERLIK KALDIRILDI ---
    # LOO backtest: K7B %63 top-1 (baseline %56), K7 profil negatif %0.
    
    # --- 3. WHALE SHADOW: Divergence ---
    # P49: data_1h öncelikli (auto_fetch enjekte eder), HISTORICAL_DATA fallback
    whale_ls = d1h.get("whale_acct_ls")
    if whale_ls is None:
        for label in sorted(HISTORICAL_DATA.keys(), key=lambda x: int(x[1:]), reverse=True):
            rd = HISTORICAL_DATA[label]
            if rd.get("actual") is None:
                whale_ls = rd.get("whale_acct_ls")
                break
    
    if whale_ls is not None:
        # Whale monotonic kontrolu: tum runlarda hep ayni yonde mi?
        # Hep ayni yondeyse → bilgi degil, gurultu. Sinyal URETME.
        whale_vals = [rd.get("whale_acct_ls") for rd in HISTORICAL_DATA.values()
                      if rd.get("whale_acct_ls") is not None]
        all_short = all(w < 1.0 for w in whale_vals)
        all_long = all(w > 1.0 for w in whale_vals)
        whale_monotonic = all_short or all_long
        
        if whale_monotonic:
            # Whale hep ayni yonde — SON KARAR'da sayilmaz
            signals.append(("GRI", "WHALE",
                            f"Whale monotonic ({'hep SHORT' if all_short else 'hep LONG'}) "
                            f"— SON KARAR'da sayilmaz"))
        else:
            # Whale cift yonlu — bilgi tasiyor, sinyal uret
            taker_ls = d1h.get("taker_ls_ratio", 1.0)
            taker_bullish = taker_ls > 1.0
            whale_bullish = whale_ls > 1.0
            
            if taker_bullish != whale_bullish:
                taker_k8 = clamp((taker_ls - 1.0) / 0.3) * 0.6
                whale_k8 = clamp((whale_ls - 1.0) / 0.3) * 0.6
                h1_diff = abs(taker_k8 - whale_k8)
                if h1_diff > 0.5:
                    signals.append(("KIRMIZI", "WHALE",
                                    f"Whale celisik (taker={taker_ls:.3f} vs whale={whale_ls:.4f})"))
                else:
                    signals.append(("SARI", "WHALE",
                                    f"Whale hafif celisik"))
            else:
                signals.append(("YESIL", "WHALE", "Whale uyumlu"))
    
    # --- 4. KATMAN 6: Son 3 run performansi ---
    recent_closed = []
    for rlabel in sorted(HISTORICAL_DATA.keys(), key=lambda x: int(x[1:]), reverse=True):
        rd = HISTORICAL_DATA[rlabel]
        if rd.get("actual") is None or rd.get("actual") == "BELIRSIZ":
            continue
        rr = compute_scorecard(rd["data_15m"], rd["data_1h"], rd["data_4h"], whale_ls=rd.get("whale_acct_ls"), oi_data=rd.get("api_open_interest", []))
        if rr["direction"] == "NOTR":
            continue
        rt = rd.get("run_time", "")
        m4 = _get_mfe_mae_for_run(rd, rr["direction"], rt, window_hours=4)
        ev = eval_actual(rr["direction"], rd["actual"], m4["mfe"], m4["mae"])
        recent_closed.append(ev["label"])
        if len(recent_closed) >= 3:
            break
    
    if len(recent_closed) >= 2:
        recent_fails = sum(1 for r in recent_closed if r in ("BASARISIZ", "YON_YANLIS"))
        if recent_fails >= 2:
            signals.append(("KIRMIZI", "SON_RUNLAR",
                            f"Son {len(recent_closed)} run'dan {recent_fails} basarisiz"))
        elif recent_fails == 0:
            signals.append(("YESIL", "SON_RUNLAR",
                            f"Son {len(recent_closed)} run hepsi yon-dogru"))
    
    # --- 5. GUVEN seviyesi ---
    if result["confidence"] == "YUKSEK" and result["contradiction"] < 2:
        signals.append(("YESIL", "GUVEN", "Guven YUKSEK, TF uyumlu"))
    elif result["confidence"] == "DUSUK":
        signals.append(("SARI", "GUVEN", "Guven DUSUK"))
    
    # --- 6. FLAG sayisi ---
    flag_count = len(result.get("flags", []))
    if flag_count >= 4:
        signals.append(("KIRMIZI", "BAYRAKLAR", f"{flag_count} bayrak aktif"))
    elif flag_count >= 3:
        signals.append(("SARI", "BAYRAKLAR", f"{flag_count} bayrak aktif"))
    
    # --- 6B. K8_LS AYNI VERİ UYARISI ---
    _k8_ayni = any("K8_LS_AYNI" in f for f in result.get("flags", []))
    if _k8_ayni:
        _k8f = result["det1h"].get("K8_LS", {}).get("final", 0)
        signals.append(("KIRMIZI", "K8_LS_AYNI", f"⚠️ taker_ls_ratio 3 TF ayni — K8 katkisi ({_k8f:+.3f}) yapay"))
    
    # --- 6C. K6_LIQ_FLUSH REVERSAL UYARISI (P48) ---
    _k6_flush = any("K6_LIQ_FLUSH" in f for f in result.get("flags", []))
    if _k6_flush:
        signals.append(("KIRMIZI", "K6_LIQ_FLUSH", "🔴 3TF long liq flush — tasfiye bitmiş olabilir, %75 reversal riski"))
    
    # --- 7. TF KOMBİNASYON UYARISI (pencere 34 backtest, 20 run, $1000 MFE) ---
    # Her kombinasyonun gecmis dogruluk orani → sinyal uret
    # Format: "15m/1h/4h": (SC_dogru, SC_toplam, [run listesi], renk)
    _notr_esik = 0.10
    _s15 = "N" if abs(result["h15"]) <= _notr_esik else ("L" if result["h15"] > 0 else "S")
    _s1h = "N" if abs(result["h1"]) <= _notr_esik else ("L" if result["h1"] > 0 else "S")
    _s4h = "N" if abs(result["h4"]) <= _notr_esik else ("L" if result["h4"] > 0 else "S")
    _tf_combo = f"{_s15}/{_s1h}/{_s4h}"
    
    # Backtest sonuclari (pencere 34, 20 run)
    _COMBO_HISTORY = {
        # combo: (dogru, toplam, "run detay")
        "S/S/S": (3, 5, "R2✓R5✓R6✗R8✓R15✗"),      # %60 — karisik
        "S/L/S": (3, 3, "R3✓R4✓R9✓"),               # %100 — hep dogru (+R19blr +R21blr)
        "L/L/S": (1, 2, "R12✓R14✗"),                 # %50 — yari yari
        "L/L/L": (2, 3, "R10✓R11✓R28✗"),                 # %67 — R28 YÖN_YANLIŞ
        "N/L/S": (0, 1, "R13✗"),                     # %0 — hep yanlis
        # Simetrik (ters yon) — veri yoksa None
        "L/S/L": None,  # S/L/S'in simetrigi — veri yok
        "S/S/L": None,  # L/L/S'in simetrigi — veri yok
        "N/S/L": None,  # N/L/S'in simetrigi — veri yok
    }
    
    if _tf_combo in _COMBO_HISTORY and _COMBO_HISTORY[_tf_combo] is not None:
        _ok, _n, _runs = _COMBO_HISTORY[_tf_combo]
        _pct = _ok / _n * 100 if _n > 0 else 0
        _n_note = f" ({_n} run)" if _n < 3 else ""
        
        if _pct >= 100 and _n >= 2:
            signals.append(("YESIL", "TF_COMBO",
                f"{_tf_combo} gecmiste {_ok}/{_n}=%{_pct:.0f} SC dogru [{_runs}]"))
        elif _pct >= 100 and _n == 1:
            signals.append(("SARI", "TF_COMBO",
                f"{_tf_combo} gecmiste {_ok}/{_n}=%{_pct:.0f} SC dogru — tek run, sinirli [{_runs}]"))
        elif _pct >= 60:
            signals.append(("SARI", "TF_COMBO",
                f"{_tf_combo} gecmiste {_ok}/{_n}=%{_pct:.0f} SC dogru — karisik [{_runs}]"))
        elif _pct == 50:
            signals.append(("KIRMIZI", "TF_COMBO",
                f"{_tf_combo} gecmiste {_ok}/{_n}=%{_pct:.0f} — yazi-tura [{_runs}]"))
        else:
            signals.append(("KIRMIZI", "TF_COMBO",
                f"!! {_tf_combo} gecmiste {_ok}/{_n}=%{_pct:.0f} SC yanlis [{_runs}]"))
    elif _tf_combo in _COMBO_HISTORY and _COMBO_HISTORY[_tf_combo] is None:
        # Simetrik pattern — veri yok ama bilinen patternin aynasi
        _mirror = {"L/S/L": "S/L/S", "S/S/L": "L/L/S", "N/S/L": "N/L/S"}.get(_tf_combo)
        if _mirror and _mirror in _COMBO_HISTORY and _COMBO_HISTORY[_mirror] is not None:
            _ok, _n, _runs = _COMBO_HISTORY[_mirror]
            _pct = _ok / _n * 100 if _n > 0 else 0
            signals.append(("SARI", "TF_COMBO",
                f"{_tf_combo} — simetrik {_mirror} gecmiste {_ok}/{_n}=%{_pct:.0f} [{_runs}] (ters yon, veri yok)"))
    else:
        # Hic gorulmemis kombinasyon
        signals.append(("SARI", "TF_COMBO",
            f"{_tf_combo} — bu kombinasyon gecmiste hic gorulmedi"))
    
    # === v3a BİRLEŞİK SİNYAL (YON-2-7, YON-3-1 güncelleme) ===
    # YON-3-1: Heatmap v3a oylamasından ve vetodan ÇIKARILDI.
    # Backtest (P41): HT yön doğruluğu 1/5=%20, v3a'yı %83→%67 düşürdü.
    # Formül: SC + MUM_15m + MUM_1h + WHALE_v2 (4 bileşen)
    # Heatmap gözlem olarak gösterilmeye devam eder ama skoru ETKİLEMEZ.
    
    # SC sinyali
    sc_sig = 1 if direction == "LONG" else -1
    
    # Mum sinyalleri (giriş anı)
    _active_label = f"R{get_active_run()}"
    _active_rd = HISTORICAL_DATA.get(_active_label, {})
    _rt = _active_rd.get("run_time", "")
    _entry_candles = get_entry_candle_signals(_rt)
    _m15_sig = _entry_candles["15m"]["sig"]
    _m1h_sig = _entry_candles["1h"]["sig"]
    _m15_det = _entry_candles["15m"]["reason"]
    _m1h_det = _entry_candles["1h"]["reason"]
    
    # Whale v2 sinyali
    _whale_ls = _active_rd.get("whale_acct_ls")
    _w_sig, _w_det = whale_signal_v2(_whale_ls)
    
    # YON-3-1: Heatmap ÇIKARILDI — v3a'ya dahil DEĞİL, gözlem de YOK
    _ht_sig = 0  # backward compat için sıfır
    
    # v3a toplam — SC + M15 + M1h + W (4 bileşen, YON-3-1)
    _v3a_total = sc_sig + _m15_sig + _m1h_sig + _w_sig
    
    # Birleşik sinyal kaydı
    def _sig_label(s):
        if s > 0: return "LONG"
        elif s < 0: return "SHORT"
        return "NOTR"
    
    signals.append(("---", "V3A_OYLAMA",
        f"SC={sc_sig:+d} M15={_m15_sig:+d}({_m15_det}) M1h={_m1h_sig:+d}({_m1h_det}) "
        f"W={_w_sig:+d}({_w_det}) = {_v3a_total:+d} → {_sig_label(_v3a_total)}"))
    
    # === KARAR (META-SKOR — P51) ===
    red = sum(1 for s in signals if s[0] == "KIRMIZI")
    green = sum(1 for s in signals if s[0] == "YESIL")
    yellow = sum(1 for s in signals if s[0] == "SARI")
    
    # Meta-skor: tüm sinyalleri tek sayıya indir
    meta_score, meta_breakdown, meta_decision = compute_meta_score(result, signals, candle_result)
    
    # v3a hâlâ hesaplanır (meta-skorun BİLEŞENİ)
    if _v3a_total > 0 and direction == "LONG":
        v3a_label = f"v3a={_v3a_total:+d} LONG uyumlu"
    elif _v3a_total < 0 and direction == "SHORT":
        v3a_label = f"v3a={_v3a_total:+d} SHORT uyumlu"
    elif _v3a_total == 0:
        v3a_label = f"v3a=0 — dengede"
    else:
        v3a_label = f"v3a={_v3a_total:+d} SC'ye ters"
    
    # Meta-skor kararı
    decision = meta_decision
    reason = f"meta={meta_score:+.1f} ({v3a_label})"
    
    return {
        "decision": decision,
        "reason": reason,
        "red": red,
        "green": green,
        "yellow": yellow,
        "signals": signals,
        "direction": direction,
        "size": result["size"],
        "confidence": result["confidence"],
        "h15": result["h15"],
        "h1": result["h1"],
        "h4": result["h4"],
        "v3a_total": _v3a_total,
        "v3a_signals": {"sc": sc_sig, "m15": _m15_sig, "m1h": _m1h_sig, 
                         "whale": _w_sig, "heatmap": _ht_sig},
        "heatmap_veto": False,  # YON-3-1: veto devre dışı
        "meta_score": meta_score,
        "meta_breakdown": meta_breakdown,
    }

def print_final_decision(fd):
    """Son karar ciktisini yazdir — meta-skor + v3a birlestik sinyal."""
    print(f"\n{'='*70}")
    print(f"  KATMAN 8 — SON KARAR (META-SKOR + v3a)")
    print(f"{'='*70}")
    
    if fd["decision"] == "BEKLE":
        print(f"  NOTR — pozisyon yok")
        return
    
    # Bilgilendirme sinyalleri
    for color, source, desc in fd["signals"]:
        if source == "V3A_OYLAMA":
            icon = "📊"
        elif color == "KIRMIZI":
            icon = "🔴"
        elif color == "YESIL":
            icon = "🟢"
        elif color == "GRI":
            icon = "⚪"
        elif color == "---":
            icon = "📊"
        else:
            icon = "🟡"
        print(f"  {icon} [{source}] {desc}")
    
    # v3a oylama kutusu
    v3a = fd.get("v3a_signals", {})
    _v3a_t = fd.get("v3a_total", 0)
    print(f"\n  v3a OYLAMA: SC={v3a.get('sc',0):+d} M15={v3a.get('m15',0):+d} "
          f"M1h={v3a.get('m1h',0):+d} W={v3a.get('whale',0):+d} = {_v3a_t:+d}")
    
    # Meta-skor breakdown
    meta = fd.get("meta_score", 0)
    mb = fd.get("meta_breakdown", {})
    if mb:
        print(f"\n  META-SKOR DETAY:")
        for k, v in mb.items():
            print(f"    {k}: {v}")
    
    # Karar kutusu — P53: GİRME'de güven/boyut gizlenir, ters yön kontrolü eklenir
    if fd["decision"] == "GIR":
        box_line2 = f"{fd['direction']} | {fd.get('confidence','?')} | {fd['size']}"
        print(f"\n  +{'='*56}+")
        print(f"  | {'META-SKOR: ' + f'{meta:+.1f}':^54s} |")
        print(f"  | {'GIR':^54s} |")
        print(f"  | {box_line2:^54s} |")
        print(f"  | {fd['reason']:^54s} |")
        print(f"  +{'='*56}+")
    else:
        box_line1 = f"GIRME (meta={meta:+.1f})"
        print(f"\n  +{'='*56}+")
        print(f"  | {box_line1:^54s} |")
        print(f"  | {'GIRME — pozisyon ACMA':^54s} |")
        print(f"  | {('Yon bilgi: ' + fd['direction']):^54s} |")
        print(f"  | {fd['reason']:^54s} |")
        print(f"  +{'='*56}+")
        
        _rev_dir = "LONG" if fd["direction"] == "SHORT" else "SHORT"
        _h15 = fd.get("h15", 0)
        _h1 = fd.get("h1", 0)
        _h4 = fd.get("h4", 0)
        if fd["direction"] == "SHORT":
            _rev_count = sum(1 for h in [_h15, _h1, _h4] if h > 0.10)
        else:
            _rev_count = sum(1 for h in [_h15, _h1, _h4] if h < -0.10)
        
        print(f"\n  TERS YON KONTROLU:")
        if _rev_count == 0:
            print(f"  Ters yon ({_rev_dir}): 3TF {fd['direction']} — sinyal YOK")
            print(f"  → BEKLEyin. Ters yone GIRMEyin.")
        elif _rev_count <= 1:
            print(f"  Ters yon ({_rev_dir}): {_rev_count}/3 TF — zayif, sinyal yetersiz")
            print(f"  → BEKLEyin. Ters yone GIRMEyin.")
        else:
            print(f"  Ters yon ({_rev_dir}): {_rev_count}/3 TF — sinyal var")
            print(f"  → Ayri run ile degerlendir. Bu run'dan TERS YONE GIRMEyin.")

# =========== GUNCEL VERI GIRISI — R18 ICIN BURAYI DEGISTIR ===========
# YON-1: R17 kapandi. Yeni Gemini verisi geldiginde buraya girilecek.

# P58: auto_fetch API zaman serileri (run_updater tarafından güncellenir)
api_open_interest_live = [["05-01 19:00", 105087.44], ["05-01 20:00", 104911.99], ["05-01 21:00", 104328.85], ["05-01 22:00", 103965.6], ["05-01 23:00", 104020.38], ["05-02 00:00", 103865.01], ["05-02 01:00", 103738.69], ["05-02 02:00", 103883.13], ["05-02 03:00", 103830.4], ["05-02 04:00", 104084.96], ["05-02 05:00", 103271.02], ["05-02 06:00", 102660.76], ["05-02 07:00", 102734.84], ["05-02 08:00", 102516.29], ["05-02 09:00", 102473.66], ["05-02 10:00", 102514.7], ["05-02 11:00", 102419.44], ["05-02 12:00", 102138.57], ["05-02 13:00", 102128.89], ["05-02 14:00", 102298.79], ["05-02 15:00", 102071.49], ["05-02 16:00", 102067.31], ["05-02 17:00", 102001.36], ["05-02 18:00", 101923.44], ["05-02 19:00", 101950.29], ["05-02 20:00", 102002.41], ["05-02 21:00", 102030.68], ["05-02 22:00", 101942.36], ["05-02 23:00", 102025.64], ["05-03 00:00", 102089.13]]
api_whale_account_live = [["05-01 19:00", 0.7578], ["05-01 20:00", 0.7619], ["05-01 21:00", 0.7648], ["05-01 22:00", 0.7677], ["05-01 23:00", 0.7632], ["05-02 00:00", 0.7633], ["05-02 01:00", 0.7625], ["05-02 02:00", 0.7614], ["05-02 03:00", 0.7736], ["05-02 04:00", 0.7789], ["05-02 05:00", 0.7571], ["05-02 06:00", 0.7536], ["05-02 07:00", 0.7536], ["05-02 08:00", 0.7542], ["05-02 09:00", 0.7536], ["05-02 10:00", 0.7528], ["05-02 11:00", 0.7549], ["05-02 12:00", 0.7553], ["05-02 13:00", 0.7549], ["05-02 14:00", 0.7606], ["05-02 15:00", 0.768], ["05-02 16:00", 0.7688], ["05-02 17:00", 0.7679], ["05-02 18:00", 0.7666], ["05-02 19:00", 0.7683], ["05-02 20:00", 0.7673], ["05-02 21:00", 0.7675], ["05-02 22:00", 0.7839], ["05-02 23:00", 0.7824], ["05-03 00:00", 0.7822]]
api_whale_position_live = [["05-01 19:00", 0.7578], ["05-01 20:00", 0.7618], ["05-01 21:00", 0.7649], ["05-01 22:00", 0.7677], ["05-01 23:00", 0.7634], ["05-02 00:00", 0.7634], ["05-02 01:00", 0.7624], ["05-02 02:00", 0.7615], ["05-02 03:00", 0.7737], ["05-02 04:00", 0.779], ["05-02 05:00", 0.7572], ["05-02 06:00", 0.7535], ["05-02 07:00", 0.7535], ["05-02 08:00", 0.7544], ["05-02 09:00", 0.7538], ["05-02 10:00", 0.7528], ["05-02 11:00", 0.755], ["05-02 12:00", 0.7553], ["05-02 13:00", 0.755], ["05-02 14:00", 0.7606], ["05-02 15:00", 0.768], ["05-02 16:00", 0.7687], ["05-02 17:00", 0.768], ["05-02 18:00", 0.7665], ["05-02 19:00", 0.7683], ["05-02 20:00", 0.7674], ["05-02 21:00", 0.7674], ["05-02 22:00", 0.7838], ["05-02 23:00", 0.7825], ["05-03 00:00", 0.7822]]
api_funding_rate_live = [["04-30 00:00", -4.22e-05, 75749.8], ["04-30 08:00", -1.837e-05, 76130.0], ["04-30 16:00", -2.904e-05, 76429.2], ["05-01 00:00", -3.746e-05, 76305.5], ["05-01 08:00", -1.81e-05, 77101.09816667], ["05-01 16:00", -3.143e-05, 78424.72796268], ["05-02 00:00", -8.22e-06, 78192.0], ["05-02 08:00", -5.103e-05, 78181.6], ["05-02 16:00", -2.54e-05, 78452.73851449], ["05-03 00:00", 2.29e-05, 78654.45395802]]
api_taker_ls_live = [["05-01 18:00", 1.0598], ["05-01 19:00", 1.1579], ["05-01 20:00", 0.6801], ["05-01 21:00", 1.3931], ["05-01 22:00", 0.8368], ["05-01 23:00", 0.8512], ["05-02 00:00", 1.1299], ["05-02 01:00", 1.0647], ["05-02 02:00", 1.2773], ["05-02 03:00", 1.243], ["05-02 04:00", 0.6084], ["05-02 05:00", 1.0439], ["05-02 06:00", 1.6357], ["05-02 07:00", 0.948], ["05-02 08:00", 1.057], ["05-02 09:00", 1.0716], ["05-02 10:00", 0.9891], ["05-02 11:00", 0.8471], ["05-02 12:00", 1.5161], ["05-02 13:00", 1.7705], ["05-02 14:00", 1.208], ["05-02 15:00", 1.1355], ["05-02 16:00", 1.3009], ["05-02 17:00", 0.6861], ["05-02 18:00", 0.9294], ["05-02 19:00", 1.0155], ["05-02 20:00", 0.9742], ["05-02 21:00", 1.461], ["05-02 22:00", 1.0115], ["05-02 23:00", 0.9362]]
data_5m = {"current_price": 78544.3, "ma5": 78619.96, "ma10": 78657.24, "ma30": 78677.41, "volume": 6239858, "volume_ma5": 14931548, "volume_ma10": 12968225, "net_long": 0.439, "net_short": 0.561, "futures_cvd": -4652932, "spot_cvd": 0, "taker_ls_ratio": 2.0799, "oi": 102095, "oi_delta": 6, "liquidations": {"long": 0, "short": 0}, "ma5_slope": -12.804, "cvd_momentum": -1.4458, "ls_slope": 0.34618, "oi_slope": -3.67, "oi_accel": -1.95, "np_slope": 5e-05, "depth_imbalance": 8.8979}
data_15m = {"current_price": 78544.3, "ma5": 78663.08, "ma10": 78675.35, "ma30": 78505.39, "volume": 56675055, "volume_ma5": 36409419, "volume_ma10": 50529920, "net_long": 0.4389, "net_short": 0.5611, "futures_cvd": -3774807, "spot_cvd": 0, "taker_ls_ratio": 0.8967, "oi": 102089, "oi_delta": -11, "liquidations": {"long": 0, "short": 0}, "ma5_slope": 6.754, "cvd_momentum": -4.7272, "ls_slope": -0.10894, "oi_slope": 16.77, "oi_accel": 0.64, "np_slope": -5e-05, "depth_imbalance": 8.8979}
data_1h = {"current_price": 78544.3, "ma5": 78619.08, "ma10": 78520.31, "ma30": 78319.05, "volume": 56675055, "volume_ma5": 226880276, "volume_ma10": 166833105, "net_long": 0.4389, "net_short": 0.5611, "futures_cvd": -3774807, "spot_cvd": 0, "taker_ls_ratio": 0.9362, "oi": 102089, "oi_delta": 63, "liquidations": {"long": 0, "short": 0}, "ma5_slope": 49.508, "cvd_momentum": 6.5335, "ls_slope": -0.01213, "oi_slope": 16.84, "oi_accel": 7.77, "np_slope": 0.00142, "depth_imbalance": 8.8979, "whale_acct_ls": 0.7822, "funding_rate": 2.206e-05}
data_4h = {"current_price": 78544.4, "ma5": 78439.32, "ma10": 78366.02, "ma30": 77090.95, "volume": 56695241, "volume_ma5": 530606223, "volume_ma10": 1200341639, "net_long": 0.4389, "net_short": 0.5611, "futures_cvd": -3783526, "spot_cvd": 0, "taker_ls_ratio": 1.2604, "oi": 102089, "oi_delta": 87, "liquidations": {"long": 0, "short": 0}, "ma5_slope": 22.502, "cvd_momentum": -0.2671, "ls_slope": 0.07791, "oi_slope": -99.05, "oi_accel": 362.36, "np_slope": 0.00217, "depth_imbalance": 8.8979}
# =========== MUM VERISI — ANLIK + ONCEKI (OPSIYONEL) ===========
# Her TF icin: Binance'ta mum ustune tikla → OHLC oku
# curr = anlik (kapanmamis) mum, prev = bir onceki (kapanmis) mum
# None birakirsan mum analizi atlanir

candles_data = {
    "5m": {
        "curr": {"open": 78575.0, "high": 78575.0, "low": 78538.1, "close": 78544.3},
        "prev": {"open": 78675.8, "high": 78675.9, "low": 78555.0, "close": 78575.1},
    },
    "15m": {
        "curr": {"open": 78652.8, "high": 78740.5, "low": 78538.1, "close": 78544.3},
        "prev": {"open": 78653.9, "high": 78676.1, "low": 78588.3, "close": 78652.9},
    },
    "1h": {
        "curr": {"open": 78652.8, "high": 78740.5, "low": 78538.1, "close": 78544.3},
        "prev": {"open": 78793.2, "high": 78793.2, "low": 78588.3, "close": 78652.9},
    },
    "4h": {
        "curr": {"open": 78652.8, "high": 78740.5, "low": 78538.1, "close": 78544.4},
        "prev": {"open": 78444.1, "high": 79145.0, "low": 78376.0, "close": 78652.9},
    },
}
# candles_data = {
#     "15m": {
#         "curr": {"open": 0, "high": 0, "low": 0, "close": 0},
#         "prev": {"open": 0, "high": 0, "low": 0, "close": 0},
#     },
#     "1h": {
#         "curr": {"open": 0, "high": 0, "low": 0, "close": 0},
#         "prev": {"open": 0, "high": 0, "low": 0, "close": 0},
#     },
#     "4h": {
#         "curr": {"open": 0, "high": 0, "low": 0, "close": 0},
#         "prev": {"open": 0, "high": 0, "low": 0, "close": 0},
#     },
# }

# =========== RUN KLİNES — GIRIS ANINDAKI SNAPSHOT (YON-2-8 YENİ) ===========
# Binance API'den gelen klines verisi — her run icin ayri saklanir.
# Global CANDLES_4H/1H/15M dizileri MFE/MAE icin korunuyor.
# Bu diziler per-run tekrar uretilebilirlik (reproducibility) icindir.
# Format: [("MM-DD HH:MM", open, high, low, close), ...]
# None birakirsan per-run klines saklanmaz (eski davranis).

run_klines_4h = None   # ~10 mum
run_klines_1h = None   # ~30 mum
run_klines_15m = None  # ~50 mum

# =========== HEATMAP RAW — 6 GÖRÜNÜM (YON-2-8 YENİ) ===========
# Coinglass heatmap screenshot'larindan elde edilen detayli veri.
# 6 gorunum: perp+spot × 15m/1h/4h
# Her gorunum: upper (ust cluster fiyati), upper_w (agirlik), lower, lower_w
# Agirlik degerleri: HAFIF, ORTA, AGIR, COK_AGIR
# None birakirsan heatmap_raw saklanmaz.
# Mevcut heatmap ozet formati heatmap_raw'dan otomatik turetilir.

run_heatmap_raw = None
# run_heatmap_raw = {
#     "price": 67230, "time": "04-04 23:52",
#     "perp_15m": {"upper": 67575, "upper_w": "COK_AGIR", "lower": 67000, "lower_w": "AGIR"},
#     "perp_1h":  {"upper": 0, "upper_w": "", "lower": 0, "lower_w": ""},
#     "perp_4h":  {"upper": 0, "upper_w": "", "lower": 0, "lower_w": ""},
#     "spot_15m": {"upper": 0, "upper_w": "", "lower": 0, "lower_w": ""},
#     "spot_1h":  {"upper": 0, "upper_w": "", "lower": 0, "lower_w": ""},
#     "spot_4h":  {"upper": 0, "upper_w": "", "lower": 0, "lower_w": ""},
# }

# =================== SHADOW HEATMAP V2 — RESEARCH-BASED (YON-2-9) ===================
# GÖZLEM MODU — production skorlamayı DEĞİŞTİRMEZ.
# K8_WHALE shadow ile aynı süreç: gözlem → 10 run → backtest → adoption kararı.
#
# Araştırma kaynakları: Bookmap imbalance, Rallis 2025 SSRN, CME 2025,
# Glassnode heatmap, Easley et al. VPIN, Alexander 2020 perp price discovery.
#
# Formül: Exponential decay × ATR-adaptif sigma
# TF ağırlığı: 4h=0.45 > 1h=0.35 > 15m=0.20 (yapısal > anlık)
# Perp/Spot: 0.80/0.20 (6× hacim + kaldıraç kaskadı)
# Concordance: 2/3 TF uyum gerekli
# Mıknatıs modeli: üstte yoğun cluster = fiyat yukarı çekilir

import math as _math

_SHT_WEIGHT_SCORE = {"HAFIF": 1, "ORTA": 2, "AGIR": 3, "COK_AGIR": 4,
                      "AĞIR": 3, "ÇOK_AĞIR": 4}
_SHT_TF_WEIGHT = {"15m": 0.20, "1h": 0.35, "4h": 0.45}
_SHT_MARKET_WEIGHT = {"perp": 0.80, "spot": 0.20}
_SHT_ATR_MULT = 1.0
_SHT_FALLBACK_SIGMA = {"15m": 80, "1h": 300, "4h": 600}
_SHT_VETO_ATR_MULT = 1.5
_SHT_CONCORDANCE_THRESH = 0.02
_SHT_CONVERGENCE_TOL = 100
_SHT_CONVERGENCE_MIN = 3
_SHT_CONVERGENCE_BONUS = 1.5

# [KALDIRILDI] _sht_calc_atr() — ölü kod temizliği

# [KALDIRILDI] _sht_get_atrs() — ölü kod temizliği

# [KALDIRILDI] _sht_exp_score() — ölü kod temizliği

# [KALDIRILDI] _sht_analyze_view() — ölü kod temizliği

# [KALDIRILDI] shadow_heatmap_v2() — ölü kod temizliği

# [KALDIRILDI] print_shadow_heatmap_v2() — ölü kod temizliği


# =================== REGIME FILTER FUNCTIONS ===================

def _regime_calc_adx(candles_ohlc, period=14):
    """ADX(14) hesapla. candles_ohlc = [(time, O, H, L, C), ...]"""
    if len(candles_ohlc) < period + 2:
        return None
    plus_dm, minus_dm, trs = [], [], []
    for i in range(1, len(candles_ohlc)):
        h, l = candles_ohlc[i][2], candles_ohlc[i][3]
        ph, pl, pc = candles_ohlc[i-1][2], candles_ohlc[i-1][3], candles_ohlc[i-1][4]
        up, down = h - ph, pl - l
        plus_dm.append(up if up > down and up > 0 else 0)
        minus_dm.append(down if down > up and down > 0 else 0)
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    if len(trs) < period:
        return None
    atr_s = sum(trs[:period])
    pdm_s = sum(plus_dm[:period])
    mdm_s = sum(minus_dm[:period])
    dx_list = []
    for i in range(period, len(trs)):
        atr_s = atr_s - atr_s / period + trs[i]
        pdm_s = pdm_s - pdm_s / period + plus_dm[i]
        mdm_s = mdm_s - mdm_s / period + minus_dm[i]
        pdi = 100 * pdm_s / atr_s if atr_s > 0 else 0
        mdi = 100 * mdm_s / atr_s if atr_s > 0 else 0
        di_sum = pdi + mdi
        dx_list.append(100 * abs(pdi - mdi) / di_sum if di_sum > 0 else 0)
    if len(dx_list) < period:
        return sum(dx_list) / len(dx_list) if dx_list else None
    adx = sum(dx_list[:period]) / period
    for i in range(period, len(dx_list)):
        adx = (adx * (period - 1) + dx_list[i]) / period
    return adx

def apply_regime_filter(result, run_time_str=None):
    """Regime filter uygula. ADX < REGIME_ADX_THRESHOLD → NOTR zorla.
    result dict'i yerinde (in-place) değiştirir.
    Returns: regime_info dict."""
    regime_info = {"adx": None, "regime": "UNKNOWN", "override": False, "original_direction": None}
    
    if not CANDLES_4H_REGIME or not run_time_str:
        return regime_info
    
    # run_time'a en yakın candle'ı bul
    def _parse_t(ts):
        parts = ts.strip().split(" ")
        dp, tp = parts[0].split("-"), parts[1].split(":")
        return (int(dp[0]), int(dp[1]), int(tp[0]), int(tp[1]))
    
    try:
        rt = _parse_t(run_time_str)
    except:
        return regime_info
    
    best_idx = 0
    for i, c in enumerate(CANDLES_4H_REGIME):
        ct = _parse_t(c[0])
        if ct <= rt:
            best_idx = i
    
    slice_4h = CANDLES_4H_REGIME[:best_idx + 1]
    if len(slice_4h) < 30:
        regime_info["regime"] = "YETERSIZ_VERI"
        return regime_info
    
    adx = _regime_calc_adx(slice_4h, 14)
    regime_info["adx"] = round(adx, 1) if adx else None
    
    if adx is None:
        regime_info["regime"] = "HESAPLANAMADI"
        return regime_info
    
    if adx < REGIME_ADX_THRESHOLD:
        regime_info["regime"] = "RANGING"
    elif adx < 25:
        regime_info["regime"] = "TRANSITION"
    else:
        regime_info["regime"] = "TRENDING"
    
    # RANGING override
    if regime_info["regime"] == "RANGING" and result["direction"] != "NOTR":
        regime_info["override"] = True
        regime_info["original_direction"] = result["direction"]
        result["direction"] = "NOTR"
        result["confidence"] = "BEKLE"
        result["size"] = "POZISYON ACMA"
        # Flag ekle
        result["flags"].insert(0, f"REGIME FILTER: ADX={adx:.1f} < {REGIME_ADX_THRESHOLD} → RANGING → NOTR zorla")
    
    return regime_info

def print_regime_filter(regime_info):
    """Regime filter çıktısını yazdır."""
    print(f"\n{'='*70}")
    print(f"  KATMAN 0 — REJIM FILTRESI (ADX-14, 4h)")
    print(f"{'='*70}")
    adx = regime_info.get("adx")
    regime = regime_info.get("regime", "UNKNOWN")
    override = regime_info.get("override", False)
    orig = regime_info.get("original_direction")
    
    if adx is not None:
        print(f"  ADX(14) = {adx:.1f}  |  Esik = {REGIME_ADX_THRESHOLD}  |  Rejim = {regime}")
        if override:
            print(f"  !! OVERRIDE: {orig} → NOTR (ranging piyasada pozisyon acilmaz)")
        elif regime == "RANGING":
            print(f"  Sinyal zaten NOTR — override gerekmedi")
        elif regime == "TRANSITION":
            print(f"  Dikkat: ADX {adx:.1f} transition bandinda (20.5-25)")
        else:
            print(f"  Trending — sinyal gecerli")
    else:
        print(f"  ADX hesaplanamadi ({regime})")

# =================== FİYAT HEDEFLERİ KALDIRILDI (P68) ===================
# P68: compute_price_targets + print_price_targets kaldırıldı (~130 satır).
# Geçmiş: P50'de eklendi (sabit $300/$1000), P67'de V2 ATR bazlı TP'ye geçti,
# P68'de backtest sonrası kaldırıldı.
# Kaldırma sebebi:
#   1. Karar mekanizmasına katkısı sıfır (sadece display)
#   2. entry_trigger_v2 calc_entry_levels ile çakışma (iki ayrı ATR/TP hesabı)
#   3. P68'de 3 tur düzeltme gerekti (simple range→TR, fallback mult, hit rate)
#   4. Gösterdiği tüm bilgi başka yerlerde mevcut:
#      - TP/SL/R:R → auto_compact V2 dashboard
#      - MA seviyeleri → print_scores_and_direction
#      - ATR → print_regime_filter
# =========================================================================


def build_fingerprint(result, d15, d1h, d4h):
    """P49: Run parmak izi — CBR (Case-Based Reasoning) için.
    Şu an sadece kayıt. R50+ sonrası güven/boyut müdahalesi için kullanılacak.
    Her run'ın multi-TF kriter profili, derivatif verisi ve karar metadatası."""
    fp = {
        "dir": result["direction"],
        "conf": result["confidence"],
        "size": result["size"],
        "h15": round(result["h15"], 4),
        "h1": round(result["h1"], 4),
        "h4": round(result["h4"], 4),
        "v_risk": result.get("v_risk", {}).get("triggered", False),
        "k1_raw": round(result["det1h"].get("K1_MA", {}).get("raw", 0), 4),
        "k3_raw": round(result["det1h"].get("K3_NETPOS", {}).get("raw", 0), 4),
        "k4_raw": round(result["det1h"].get("K4_CVD", {}).get("raw", 0), 4),
        "k6_raw": round(result["det1h"].get("K6_LIQ", {}).get("raw", 0), 4),
        "k7_raw": round(result["det1h"].get("K7_OI", {}).get("raw", 0), 4),
        "k8_raw": round(result["det1h"].get("K8_LS", {}).get("raw", 0), 4),
        # K13e rejim (P50)
        "k13_raw": round(result["det1h"].get("K13_OI_PRICE_DIV", {}).get("raw", 0), 4),
        "k13_regime": result["det1h"].get("K13_OI_PRICE_DIV", {}).get("regime", "?"),
        "whale": d1h.get("whale_acct_ls"),
        "funding": d1h.get("funding_rate"),
        "oi_delta": d1h.get("oi_delta", 0),
        "ls_15m": d15.get("taker_ls_ratio", 1.0),
        "ls_1h": d1h.get("taker_ls_ratio", 1.0),
        "ls_4h": d4h.get("taker_ls_ratio", 1.0),
        "tf_signs": (
            "+" if result["h15"] > 0.1 else ("-" if result["h15"] < -0.1 else "0"),
            "+" if result["h1"] > 0.1 else ("-" if result["h1"] < -0.1 else "0"),
            "+" if result["h4"] > 0.1 else ("-" if result["h4"] < -0.1 else "0"),
        ),
        "flags": result.get("flags", []),
    }
    return fp


def print_fingerprint(fp):
    """Parmak izini kompakt yazdır."""
    print(f"\n{'='*70}")
    print(f"  PARMAK İZİ (CBR kayıt — karar müdahalesi YOK)")
    print(f"{'='*70}")
    print(f"  Karar: {fp['dir']} | {fp['conf']} | {fp['size']}")
    print(f"  TF:    h15={fp['h15']:+.4f}  h1={fp['h1']:+.4f}  h4={fp['h4']:+.4f}  signs={''.join(fp['tf_signs'])}")
    print(f"  1h K:  MA={fp['k1_raw']:+.3f} NP={fp['k3_raw']:+.3f} CVD={fp['k4_raw']:+.3f} LIQ={fp['k6_raw']:+.3f} OI={fp['k7_raw']:+.3f} LS={fp['k8_raw']:+.3f}")
    print(f"  K13e:  {fp.get('k13_regime','?')} raw={fp.get('k13_raw',0):+.3f}")
    wh = f"{fp['whale']:.4f}" if fp['whale'] else "—"
    fr = f"{fp['funding']:.2e}" if fp['funding'] else "—"
    print(f"  Deriv: whale={wh} funding={fr} oi_Δ={fp['oi_delta']:+,.0f}")
    print(f"  LS:    15m={fp['ls_15m']:.4f} 1h={fp['ls_1h']:.4f} 4h={fp['ls_4h']:.4f}")
    if fp['v_risk']:
        print(f"  V-RISK: AKTİF")
    if fp['flags']:
        print(f"  Flags: {', '.join(str(f) for f in fp['flags'][:3])}")


# =================== LEADING KARAR SİSTEMİ (P55) ===================
# Öncü sinyallerle giriş kararı — SC'den ÖNCE çalışır.
# Backtest (P55, R2-R26, 17 ölçülebilir): 17/17 = %100, kapsam %77.
#
# KURALLAR (öncelik sırasıyla):
#   1. SHORT_TRAP:       whale<0.95 + OI_30h>0 → GİR SHORT (4/4=%100)
#   2. LONG_ANA:         whale>0.87 + LS_1h>0.85 → GİR LONG (10/10=%100)
#   3. LONG_LS_OVERRIDE: LS_1h>1.50 (trap değilse) → GİR_DİKKAT LONG (2/2=%100)
#   4. SHORT_ZAYIF:      whale<0.90 + LS_1h<0.85 → GİR_DİKKAT SHORT (1/1=%100)
#   5. GİRME:            hiçbiri tetiklenmezse

def leading_decision(whale_ls, oi_delta_30h, ls_1h, pct_ma30_4h=None):
    """Öncü sinyal karar sistemi.
    P60: pct_ma30_4h = fiyatın 4h MA30'dan yüzde sapması (displacement filtre)."""
    has_w = whale_ls is not None
    has_oi = oi_delta_30h is not None
    has_ls = ls_1h is not None
    
    if has_w and has_oi and whale_ls < 0.95 and oi_delta_30h > 0:
        return {"karar": "GİR", "yon": "SHORT", "kural": "SHORT_TRAP",
                "guven": "YÜKSEK", "backtest": "4/4=%100",
                "neden": f"Whale SHORT ({whale_ls:.4f}<0.95) + OI artıyor ({oi_delta_30h:+.0f})"}
    if has_w and has_ls and whale_ls > 0.87 and ls_1h > 0.85:
        if ls_1h < 1.20:
            # P67: Fiyat deplasmanı filtresi (ERKEN bölgede)
            # P60 eşik=3.0% → P67 eşik=4.0% (grid search: 1/3→3/3 doğru koruma)
            # R32(4.1%)=bloke✓, R33(3.5%)=geç✓, R36(3.2%)=geç✓
            if pct_ma30_4h is not None and pct_ma30_4h > 4.0:
                return {"karar": "GİRME", "yon": "NOTR", "kural": "LONG_ANA_DEPLASMAN",
                        "guven": "—", "backtest": "R32 bloke (4h%MA30=+4.31%, eşik=4.0%)",
                        "neden": f"LONG_ANA koşulları sağlanıyor ama fiyat 4h MA30'dan {pct_ma30_4h:+.1f}% uzakta (>4.0% = ralli tepesi)"}
            return {"karar": "GİR", "yon": "LONG", "kural": "LONG_ANA",
                    "guven": "YÜKSEK", "backtest": "4/5=%80 (R37 YANLIŞ)",
                    "neden": f"Whale LONG ({whale_ls:.4f}>0.87) + alıcı baskın ({ls_1h:.4f}, 0.85-1.20 ERKEN bölge)"}
        else:
            return {"karar": "GİR_DİKKAT", "yon": "LONG", "kural": "LONG_ANA_GEÇ",
                    "guven": "DÜŞÜK", "backtest": "0/5 iyi giriş (LS≥1.20 = geç)",
                    "neden": f"Whale LONG ({whale_ls:.4f}>0.87) + LS YÜKSEK ({ls_1h:.4f}≥1.20 — hareket olmuş olabilir)"}
    if has_ls and ls_1h > 1.50:
        return {"karar": "GİR_DİKKAT", "yon": "LONG", "kural": "LONG_LS_OVERRIDE",
                "guven": "ORTA", "backtest": "2/2=%100",
                "neden": f"Ağır alıcı ({ls_1h:.4f}>1.50), trap tetiklenmedi"}
    if has_w and has_ls and whale_ls < 0.90 and ls_1h < 0.85:
        return {"karar": "GİR_DİKKAT", "yon": "SHORT", "kural": "SHORT_ZAYIF",
                "guven": "ORTA", "backtest": "1/1=%100",
                "neden": f"Whale düşük ({whale_ls:.4f}<0.90) + satıcı baskın ({ls_1h:.4f}<0.85)"}
    missing = []
    if not has_w: missing.append("whale")
    if not has_oi: missing.append("OI_30h")
    if not has_ls: missing.append("LS_1h")
    return {"karar": "GİRME", "yon": "NOTR",
            "kural": "VERİ_YETERSİZ" if missing else "SİNYAL_YOK",
            "guven": "—", "backtest": "—",
            "neden": f"Eksik: {', '.join(missing)}" if missing else "Hiçbir kural tetiklenmedi"}

def print_leading_decision(ld, whale_ls, oi_delta, ls_1h):
    """Leading karar çıktısı."""
    print()
    print("=" * 70)
    print("  LEADING KARAR SİSTEMİ (P55 — öncü sinyaller)")
    print("=" * 70)
    w_str = f"{whale_ls:.4f}" if whale_ls is not None else "YOK"
    oi_str = f"{oi_delta:+.0f}" if oi_delta is not None else "YOK"
    ls_str = f"{ls_1h:.4f}" if ls_1h is not None else "YOK"
    print(f"  Whale: {w_str} | OI_30h: {oi_str} | LS_1h: {ls_str}")
    karar = ld["karar"]; yon = ld["yon"]; kural = ld["kural"]
    if karar == "GİR":
        box = f"{'★ ' + karar + ' ' + yon + ' ★':^56}"
        print(f"\n  +{'='*58}+")
        print(f"  |{box}|")
        print(f"  | {'Kural: ' + kural:^56} |")
        print(f"  | {'Güven: ' + ld['guven'] + ' (' + ld['backtest'] + ')':^56} |")
        print(f"  +{'='*58}+")
    elif karar == "GİR_DİKKAT":
        box = f"{'⚠ ' + karar + ' ' + yon + ' ⚠':^56}"
        print(f"\n  +{'-'*58}+")
        print(f"  |{box}|")
        print(f"  | {'Kural: ' + kural:^56} |")
        print(f"  | {'Güven: ' + ld['guven'] + ' (' + ld['backtest'] + ')':^56} |")
        print(f"  +{'-'*58}+")
    else:
        print(f"\n  +{'-'*58}+")
        print(f"  |{'GİRME — pozisyon açma':^58}|")
        print(f"  | {ld['neden']:^56} |")
        print(f"  +{'-'*58}+")
    print(f"\n  Neden: {ld['neden']}")


# =================== COMBO SİSTEMİ KALDIRILDI (P66) ===================
# P66: YÖN/BAĞLAM/GİRİŞ mimarisine geçildi.
# COMBO_TABLE, combo_decision(), print_combo_decision() kaldırıldı.
# Birleşik karar artık auto_compact.py'de yapılıyor.
# Geçmiş: P57'de eklendi, 18/18=%100 backtest. P66'da mimari değişiklik
# nedeniyle kaldırıldı — Leading artık SC'yi override etmiyor.
# Backtest kanıtı: 4 çatışma run'ında Leading 3/4 doğru ama R37'de
# tüm araçlar (SC+multi+scorecard) ters yöndeyken Leading tek kaldı.
# Yeni sistem: çatışmada konsensüs gücüne bakılıyor.



# =================== TAKER LS AUTO-FETCH ===================

def fetch_taker_ls():
    """Binance API'den TF-spesifik taker buy/sell ratio çek.
    Coinglass'ın ls_ratio'su TF-spesifik değil (anlık snapshot, 3 TF aynı).
    Bu fonksiyon gerçek TF-spesifik değerleri çeker ve data dict'leri günceller.
    Başarısızsa Coinglass değerleri korunur + uyarı verilir.
    """
    import urllib.request
    BASE = "https://fapi.binance.com/futures/data/takerlongshortRatio"
    results = {}
    for period in ["15m", "1h", "4h"]:
        url = f"{BASE}?symbol=BTCUSDT&period={period}&limit=1"
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                d = json.loads(resp.read())[0]
            results[period] = float(d["buySellRatio"])
        except:
            results[period] = None
    return results

# =================== CALISTIR ===================

if __name__ == "__main__":
    # ══════ TAKER LS OTOMATİK GÜNCELLEME ══════
    _tls = fetch_taker_ls()
    _tls_ok = all(v is not None for v in _tls.values())
    if _tls_ok:
        _old = data_1h.get("taker_ls_ratio", 1.0)
        data_15m["taker_ls_ratio"] = _tls["15m"]
        data_1h["taker_ls_ratio"] = _tls["1h"]
        data_4h["taker_ls_ratio"] = _tls["4h"]
        print(f"  ✅ taker_ls_ratio API'den güncellendi: 15m={_tls['15m']:.4f} 1h={_tls['1h']:.4f} 4h={_tls['4h']:.4f} (eski={_old:.4f})")
    else:
        print(f"  ⚠️ taker_ls_ratio API'den çekilemedi — Coinglass değerleri korunuyor")
    
    # ══════ LEADING KARAR (P55 — SC'den ÖNCE) ══════
    _trap_run = f"R{get_active_run()}"
    _trap_rd = HISTORICAL_DATA.get(_trap_run, {})
    _lead_whale = _trap_rd.get("whale_acct_ls") or data_1h.get("whale_acct_ls")
    _lead_oi_data = _trap_rd.get("api_open_interest", [])
    # P58: live API fallback
    if not _lead_oi_data and api_open_interest_live:
        _lead_oi_data = api_open_interest_live
    _lead_oi_delta = None
    if len(_lead_oi_data) >= 2:
        _lead_oi_delta = _lead_oi_data[-1][1] - _lead_oi_data[0][1]
    _lead_ls = data_1h.get("taker_ls_ratio")
    # P60: 4h%MA30 displacement filtresi
    _lead_pct_ma30 = None
    _4h_price = data_4h.get("current_price", 0)
    _4h_ma30 = data_4h.get("ma30", 0)
    if _4h_price > 0 and _4h_ma30 > 0:
        _lead_pct_ma30 = (_4h_price - _4h_ma30) / _4h_ma30 * 100
    _leading = leading_decision(_lead_whale, _lead_oi_delta, _lead_ls, _lead_pct_ma30)

    # ══════ HESAPLA (print yok) ══════
    dh = get_data_hash(data_15m, data_1h, data_4h)
    # P54 TRAP: whale ve OI verisi aktif run'dan al
    _trap_whale = _trap_rd.get("whale_acct_ls")
    _trap_oi = _trap_rd.get("api_open_interest", [])
    if not _trap_oi and api_open_interest_live:
        _trap_oi = api_open_interest_live
    result = compute_scorecard(data_15m, data_1h, data_4h, whale_ls=_trap_whale, oi_data=_trap_oi)
    price = data_1h["current_price"]

    # KATMAN 0 — Regime Filter (ADX < 20.5 → NOTR zorla)
    _active_run = get_active_run()
    _run_time = HISTORICAL_DATA.get(f"R{_active_run}", {}).get("run_time", "")
    # P61 FIX: Canlı run (HISTORICAL_DATA'da yok) → şu anki zamanı kullan
    if not _run_time:
        from datetime import datetime, timezone
        _now = datetime.now(timezone.utc)
        _run_time = _now.strftime("%m-%d %H:%M")
    regime_info = apply_regime_filter(result, _run_time)

    # P69: consultation_warnings ve similar_runs kaldırıldı (K7+K7B removed)
    candle_result = analyze_all_candles(candles_data, result["direction"])
    final_decision = compute_final_decision(
        result, data_15m, data_1h, data_4h, candle_result=candle_result)

    # ══════ P66 COMBO KALDIRILDI — YÖN/BAĞLAM/GİRİŞ mimarisi ══════
    # combo_decision() artık çağrılmıyor. Birleşik karar auto_compact'ta.

    # ══════ ÖZET DASHBOARD ══════
    _run_num = get_active_run()
    print()
    print("█" * 70)
    print(f"  ÖZET DASHBOARD — R{_run_num} | ${price:,.1f} (YON-5)")
    print("█" * 70)
    _ld_icon = "★" if _leading["karar"] == "GİR" else "⚠" if _leading["karar"] == "GİR_DİKKAT" else "—"
    print(f"  LEADING:     {_ld_icon} {_leading['karar']} {_leading['yon']} ({_leading['kural']})")
    # P69: BENZERLİK kaldırıldı
    _sc_meta = final_decision.get("meta_score", 0)
    print(f"  SC:           {result['direction']} (meta={_sc_meta:+.1f})")
    _v3a = final_decision.get("v3a_total", 0)
    _v3a_dir = "LONG" if _v3a > 0 else "SHORT" if _v3a < 0 else "NOTR"
    print(f"  V3A:          {_v3a:+.0f} → {_v3a_dir}")
    _regime_str = regime_info.get("regime", "?") if regime_info else "?"
    _adx_val = regime_info.get("adx", "?") if regime_info else "?"
    print(f"  REJİM:        {_regime_str} (ADX={_adx_val})")
    _mum_c = len(candle_result.get("conflict_flags", [])) if candle_result else 0
    print(f"  MUM:          {'✅ temiz' if _mum_c == 0 else f'⚠ {_mum_c} çelişki'}")
    # P69: DANIŞMA kaldırıldı
    print(f"  TF:           15m={result['h15']:+.2f} 1h={result['h1']:+.2f} 4h={result['h4']:+.2f} → {result['direction']}")
    _5m_p = data_5m.get("current_price", 0)
    _5m_ls = data_5m.get("taker_ls_ratio")
    _5m_ma5 = data_5m.get("ma5", 0)
    if _5m_p > 0 and _5m_ma5 > 0:
        _5m_pct = (_5m_p - _5m_ma5) / _5m_ma5 * 100
        print(f"  5m BİLGİ:     ${_5m_p:,.1f} LS={_5m_ls or '?'} %MA5={_5m_pct:+.2f}% (skorlamada YOK)")
    if result.get("flags"):
        print(f"  FLAGS:        {'; '.join(result['flags'][:3])}")
    print("█" * 70)

    # ══════ DETAY ÇIKTILARI ══════
    print_leading_decision(_leading, _lead_whale, _lead_oi_delta, _lead_ls)

    # ══════ TIER 1 — KARAR + RISK (TCAS: verdict first) ══════
    print_regime_filter(regime_info)
    print_final_decision(final_decision)
    
    # ══════ FİYAT HEDEFLERİ KALDIRILDI (P68) ══════
    # P68: compute_price_targets + print_price_targets kaldırıldı.
    # Sebep: Karar mekanizmasına katkısı sıfır. TP/SL/R:R bilgisi
    # entry_trigger_v2 (calc_entry_levels) tarafından üretiliyor ve
    # auto_compact dashboard'unda gösteriliyor. İki ayrı ATR/TP
    # hesaplama sync yükü yaratıyordu (3 tur düzeltme gerekti).

    # ══════ TIER 2 — KAVRAYIS (SA Level 2: Comprehension) ══════
    print_scores_and_direction(result, price)
    # candle_result zaten L7298'de hesaplandi — tekrar hesaplama kaldirildi
    print_candle_analysis(candle_result, result["direction"])
    if candle_result and candle_result["conflict_flags"]:
        print(f"\n  *** MUM CELISKISI TESPIT EDILDI — DIKKATLI OL ***")
    # P69: print_consultation kaldırıldı
    # P69: print_similarity kaldırıldı

    # ══════ TIER 3 — DETAY (SA Level 1: Perception) ══════
    print_recent_comparison(result, data_15m, data_1h, data_4h)
    print_wf_quality(result)
    
    # ══════ PARMAK İZİ (CBR kayıt) ══════
    fingerprint = build_fingerprint(result, data_15m, data_1h, data_4h)
    print_fingerprint(fingerprint)

    # ══════ TIER 4 — ARSIV ══════
    # P69: print_all_postmortems kaldırıldı
    print_historical_table()
    
    # YON-3-1: Heatmap tamamen çıkarıldı (P41 backtest: %20 yön, %25 cluster, net -1)
    # Shadow Heatmap V2 ve production heatmap artık çalıştırılmıyor.
