# HANDOFF - 01_secim
Güncelleme: 2026-10-23 (K04 pin eşleme, 02_simulasyon devir notu; önceki: D02 MAX6070 kritik değer tablosu, 01_secim/T011)

## Durum
- Aşama/geçiş: Aşama 1 (çekirdek parça), geçiş A, devam. Girdi: ..\00_coordination\SPEC.md v0.2 (onaylı, 00_coordination K01).
- 01_secim K01 (mühendis, 2026-10-22): çekirdek = ayrık V→I devre (hassas op-amp + gerilim referansı + pass elemanı). Entegre 4-20 mA vericiler (AD694 yedek; MAX12900, XTR110, XTR105, XTR112 düştü) bkz. out\passA\core_candidates.md [W]. Nedeni: hiçbirinde F1-F12 ve SPICE modeli birlikte yok.
- Çekirdek set SEÇİLDİ [U]: TLV333IDBVR (K02) + MAX6070AAUT12+T (K03); yedekler OPA187IDBVR, LT6656AIS6-1.25.
- Son doğrulanan sonuç: üç üretici SPICE model dosyası indirildi, SHA-256 ve düz metin incelemesi yapıldı, FACTS.md "Modeller" ve "Parçalar" dolu [R]. Kaynak: 01_secim/T009 Sonuç; TLV333 modelleri TI sayfasından indirildi, MAX6070_12 mühendis tarafından elle indirildi (lisans onayı mühendiste). Üçü de düz metin, şifreli değil. QSPICE uygunluğu denenmedi.
- D01 (TLV333) kritik değerler çıkarıldı [R]: out\passA\check\D01_critical.md ve .pdf (6 crop, docs\figures\), FACTS.md "Kritik değerler" 6 satır, Kontrol: bekliyor. Kaynak: 01_secim/T010. PDF 01_secim/T012'de düzeltilmiş araçla (00_coordination/T023, T024) yeniden üretildi: 18 sayfa, 6 crop, 0 eksik, her crop sayfasında "← Tabloya dön" bağlantısı, tablo satırlarında iç bağlantı [R]; md değişmedi. G-filtre karşılaştırması (karar değil): G1 geçti (IQ MAX 28 µA), G2 geçti, G3 geçti [C], G4 TYP'ye göre geçti (MAX yok), G5 bilinmiyor (Figure 14 ekseni 1000 pF'de bitiyor, 10 nF yok). Not: op-amp VS MAX 5.5 V, SPEC besleme 12-36 V, yerel ray gerekli.
- D01 geri bildirimi: mühendis D01_critical.pdf'i kontrol etti, "genel olarak doğru" (satır satır değil; satırlar [R] kaldı); grafiklerden değer okunmadığı gözlemi 01_secim/T012 Sonuç'ta, sim ile ele alınacak.
- D02 (MAX6070AAUT12+T) kritik değerler çıkarıldı [R]: out\passA\check\D02_critical.md ve .pdf (21 sayfa, 7 crop, 0 eksik), FACTS.md "Kritik değerler" 7 satır, Parçalar paket hücresi 6 SOT23 [R]. Kaynak: 01_secim/T011. G-filtre karşılaştırması (karar değil): başlangıç ±0.04 % geçti, tempco MAX 6 ppm/°C geçti, Iq 130/200 µA (260 µA) geçti, VIN 2.7-5.5 V K03 iddiasıyla uyumlu. Bulunamayan: Dropout (1.25 V için basılı değil), short-circuit duration, ESD (Absolute Maximum Ratings'te yok), CL stabilite şekil numarası. Çelişkiler: turn-on settling 6 ms (tablo) / 10 ms (p.21 metni), ripple rejection 100 dB (1.25 V tablosu) / 85 dB (p.1 genel), Iq TYP 130 / "150 µA" (genel); uzlaşana kadar tasarımda kullanılmaz.
- DigiKey erişimi digikey_v4.keyword_search üzerinden, token 200 ve keyword search 200 [M]. IC/keyword girişi seçiciye eklenmez (00_coordination K03).
- FACTS.md Gereksinimler: SPEC kimlikleri ve G1-G9 [A]/[C] olarak dolu.

## Açık maddeler (nasıl kapanacak)
1. Kritik değerlerin mühendis kontrolü [R] -> [V]: TLV333 için D01_critical.pdf (genel kontrol yapıldı, satır satır değil); MAX6070 için D02_critical.pdf (hazır, kontrol bekliyor). Model düğüm eşlemesi: TLVx333 K04 ile kapandı (FACTS.md "Pin eşleme", Label [A]); MAX6070_12 FLTR ↔ FILTER (kısaltma) mühendis onayı bekliyor.
1b. AÇIK SORU (mühendis karar verir): MAX6070AAUT12+T için D02 p.25 Ordering Information'da tam satır yok (genel "MAX6070_AUT_ _+T"; A grade'de AAUT18/30/33/50 /V'li satırlar); tam MPN Selector Guide p.24'te var (FILTER Yes, 1.25 V, 0.04 %, +ACPF). Ayrıntı D02_critical.md "Açık soru". Çelişen değerler (turn-on settling 6/10 ms, ripple rejection 100/85 dB) uzlaşana kadar kullanılmaz. Mühendis 2026-10-23: Ordering sorusu şimdilik ertelendi, öncelik simülasyon.
2. QSPICE uygunluğu: iki TLV333 biçiminden (SBOM965C PSpice, SBOM967B TINA-TI) hangisinin QSPICE'a uyduğu ve MAX6070_12 (SIMETRIX/SPICE 2G6 için yazılmış, "diğer simülatörler çeviri gerektirebilir") denenmedi; PSpice sözdizimi riskleri satır numaralarıyla FACTS.md Modeller satırlarında. Kapanış: 02_simulasyon pass 1 modelleri deneyip sonucu bildirir; hangi modelin kullanıldığı mühendis kararı (K05 adayı).
3. Pass elemanının pass 1'de genel/ideal modelle mi gireceği [A], karar mühendiste; pass B'de seçilir.
4. docs\lessons.md: 01_secim/T006'da yaptığım düzeltmeler (Invalid clientId satırı [M] -> [A], .env doğrulama satırındaki "neden" ifadesi, Products=[] satırının [A] etiketi, distribütör verisi [W] satırı) güncel dosyada görünmüyor, eski [M] metinleri geri gelmiş; 2026-10-23 dosya yazma notu (DEVLOG) ile uyumlu bir yeniden yazma olabilir. Kapanış: lessons.md satır 5, 7, 8'i yeniden düzeltecek bir bilet (bu closeout eski metni geri yüklemedi, mühendis/planner kararı).
5. Mühendis silecekler (ajan silmez): out\passA\digikey_smoke\run.log, out\passA\digikey_smoke\result.json (eski, boş yanıt); sim\models\_pages\ (ti_tlv333.html, boş adi_max6070.html, çalışma dosyası).
6. 00_coordination'a istek: .gitignore'a out\passA\digikey_smoke\result*.json, run.log, *.tmp, out\passA\core_search\{op,ref}_*.json, out\passA\ref_search\ref2_*.json ve sim\models\_pages\.
7. 401 "Invalid clientId" nedeni kanıtlanmadı [A]; gerekmedikçe araştırılmaz.

## Uzun vadeli (mühendis notu 2026-10-23)
Pipeline bitip düzgün bir KiCad projesi çıkınca tedarikçi taraması genişletilir: Octopart/Nexar, LCSC, JLCPCB (modül CLAUDE.md "Tedarikçi" ve selector README ile uyumlu); şimdilik yalnız DigiKey.

## Açık kararlar
(docs\DECISIONS.md: K01-K04 verildi (K04: model düğümü ↔ datasheet pini ad konvansiyonu). Bekleyen karar yok; K05 adayı: QSPICE'a uyan model biçimi, madde 2.)

## Commit'e hazır yollar
(commit yalnız koordinatör biletiyle; pipeline kökünden; git status --short çıktısından, bu oturumda değişenler)
01_secim\FACTS.md, 01_secim\HANDOFF.md, 01_secim\docs\DECISIONS.md, 01_secim\docs\DEVLOG.md, 01_secim\docs\lessons.md,
01_secim\docs\tasks\T007-core-search.md, T008-ref-search.md, T009-core-models.md,
01_secim\out\passA\core_candidates.md,
01_secim\out\passA\check\D01_critical.md ve D01_critical.pdf (PDF'i commit etme kararı mühendisin),
01_secim\docs\figures\D01_p3_pinfunctions.png, D01_p6_absmax_esd.png, D01_p6_recommended.png, D01_p8_electrical_a.png, D01_p8_electrical_b.png, D01_p11_overshoot_cl.png,
01_secim\out\passA\check\D02_critical.md ve D02_critical.pdf (PDF'i commit etme kararı mühendisin),
01_secim\docs\figures\D02_p2_absmax.png, D02_p3_electrical_a.png, D02_p3_electrical_b.png, D02_p12_notes.png, D02_p19_pins.png, D02_p24_selector_a.png, D02_p25_ordering.png,
01_secim\docs\tasks\T010-d01-tlv333-lookup.md, T011-d02-max6070-lookup.md, T012-d01-pdf-regen.md,
01_secim\out\passA\core_search\core_search.py, core_spec.json, opamps.md, refs.md,
01_secim\out\passA\ref_search\ref_search.py, ref_spec.json, refs2.md,
01_secim\sim\models\TLV333\ (SBOM965C.ZIP, SBOM967B.ZIP, SBOM965C\, SBOM967B\), 01_secim\sim\models\MAX6070\max6070_12.lib.
Hariç (gitignore kararı bekliyor): out\passA\core_search\op_*.json, ref_*.json; out\passA\ref_search\ref2_*.json; sim\models\_pages\.

## Sonraki oturumun ilk görevi
Devir notu out\passA\devir_02_simulasyon.md hazır: 02_simulasyon pass 1 başlar (modelleri QSPICE'ta dener, IN+/IN- follower testi, stres tablosu). Dönen QSPICE uygunluk sonucuna göre K05. Ordering sorusu (1b) ertelendi; gerekirse DigiKey/ADI sayfası bileti. Yedek parçalar (OPA187IDBVR, LT6656AIS6-1.25) için belge alımı isteği gerekirse 00_coordination'a.
