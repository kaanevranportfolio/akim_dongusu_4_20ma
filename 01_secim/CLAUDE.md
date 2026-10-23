# 01_secim - parça seçimi (modül CLAUDE.md)
Kök yöntem: ..\CLAUDE.md geçerli. Burada yalnız bu modüle özgü olanlar var. Çelişkide bu dosya kazanır (Safety ve settings.json hariç).

## Rol
İki geçiş, aynı klasör. A: SPEC'ten ana komponent (core IC) adayları, mühendis seçer. B: 02_simulasyon\out\pass1\stress_table.json ile kalan parçaların seçimi.
Geçiş HANDOFF.md'de "Geçiş" satırıyla izlenir; çıktılar out\passA\ ve out\passB\ altına (docs\INTERFACES.md bölüm 2, 3, 5, 6).

## Kontrol sırası
A:
1. SPEC kısıtlarını (besleme aralığı, iç tüketim, doğruluk, giriş tipi, sıcaklık) aday filtresine çevir; her filtre SPEC kimliğiyle.
2. Tedarikçi araması yalnız kısa liste çıkarır (şimdilik DigiKey, seçici ile). Veri [W]; datasheet karar verir.
3. Her aday için tam MPN'in kendi belgesi (D<nn>); kritik değerler crop ile mühendis kontrolünde [R] -> [V].
4. SPICE modeli: üretici sayfasında var mı, URL + SHA-256 kaydı (docs\INTERFACES.md bölüm 3). Sim-kritik parçada güvenilir kaynakta model yoksa aday elenir veya "model yok" notuyla mühendise sorulur.
5. Mühendis seçer (SEÇİLDİ), karar docs\DECISIONS.md'ye K<nn> ile yazılır.
B:
1. stress_table.json -> component_specs.json. Ham değerler; derating yalnız seçici profilinde (ikinci kez uygulanmaz). Alan eşlemesi K<nn> ile kaydedilir.
2. Seçiciyi çalıştırma yetkilendirmesi mühendisindir (DigiKey OAuth); ajan kimlik bilgisine dokunmaz.
3. Satırda "not in vendor data" varsa PASS sayılmaz: VARSAYILAN [A], datasheet kontrolü açık madde.
4. Sim-kritik parça (IC, diyot, MOSFET) için model kaydı; pasifler için parazitli genel L/C/R (model sayılmaz).
5. BOM taslağı ve selection_report.md; her MPN için ürün sayfası URL + tarih [W].

## Tedarikçi
DigiKey ile başla. Arayüz eklenti gibi tasarlanır; Octopart/Nexar, LCSC ve JLCPCB sistem kurulduktan sonra eklenir ve benchmark edilir. Kimlik bilgileri (.env, token, sertifika) okunmaz, yazılmaz, commit edilmez.

## Öncelik
Önce SPICE modelinin güvenilir kaynakta olması ve tam varyant doğruluğu; sonra fiyat, stok, teslim süresi.
- Kontrol PDF'i: Every session that gives the engineer a check table also puts this line in its last message: `kontrol PDF'i hazır: <module-relative path>.pdf, <N> sayfa, <M> crop, <K> eksik`; if K is not 0 the PDF is not delivered. Command: `python ..\tools\check_pdf.py docs\<table>.md`.
