---
name: check-pdf
description: Turn a markdown check table (parts, footprints, nets, pin map, ERC/DRC findings, layout constraints) into a PDF for the engineer with a clickable Crop column. Triggers - kontrol PDF, check table, crop link, footprint tablosu, ERC raporu, DRC raporu, PDF üret.
---

# check-pdf

Kural kaynağı: kök CLAUDE.md "Language" (Human reading, Crop sütunu). Bu skill o kuralı tek komuta çevirir. Dosya adı, yol veya sayı bu dosyada yazılı değildir.

Ne zaman: mühendisin satır satır kontrol edeceği her çok sütunlu tablo (FOOTPRINTS, NETS, BOM karşılaştırması, ERC/DRC bulguları, kısıt kontrolü, hand-off'tan gelen kontrol listesi).

Adımlar:
1. Kaynak md tablosunda her satırın kontrol edilecek kanıtı crop PNG adıyla satırın içinde yazılı olsun: datasheet için `D<nn>_p<sayfa>_<konu>.png` (`pdf_crop.py --topic`), şematik veya kart için `kicad-cli` dışa aktarımından kırpılmış PNG (adı `<ref>_<konu>.png`; yer: `docs\review\crops\`). Crop adı olmayan satır PDF'te "-" görünür; kontrol gerektiren satır crop'suz bırakılmaz.
2. Çalıştır (modül klasöründen): `python ..\tools\check_pdf.py docs\<tablo>.md` (çıktı aynı adlı .pdf). Crop klasörleri: `--crops docs\ref\_crops ..\02_simulasyon\out\freeze\figures docs\figures docs\review\crops` (varsayılan bunlardır; `pdf_crop.py` crop'ları `docs\ref\_crops\` altına yazar).
3. Çıktıyı oku: `OK ...: N pages, M crops, K missing`. K sıfırdan büyükse eksik crop'u üret, sonra yeniden çalıştır. Tabloyu mühendise veren her oturum son mesajına şu satırı koyar: `kontrol PDF'i hazır: <modüle göreli yol>.pdf, <N> sayfa, <M> crop, <K> eksik`; K 0 değilse PDF teslim edilmiş sayılmaz. Komut: `python ..\tools\check_pdf.py docs\<tablo>.md`.
4. PDF elle düzenlenmez; değişiklik md'de yapılır ve yeniden üretilir. PDF'i commit etme kararı mühendisindir.

Her satırda: "Crop" hücresi crop adı + PDF sayfa numarası, tıklanınca o sayfaya gider; crop sayfası tabloya geri dönmeye yardım eder (sayfa başlığı crop adıdır). Mühendis crop ile karşılaştırınca satır [R] -> [V] olur; durumu md'de mühendis söyleyince işlenir.

Doğrular (tam olarak): (1) `K missing` = 0 olmadıkça PDF teslim edilmez (betik eksik crop için hata kodu vermez, yalnız `MISSING crop:` basar ve PDF'te kırmızı işaret koyar). (2) Her crop sayfasındaki "Tabloya dön" bağlantı sayısı o crop'u anan satır sayısına eşittir, en çok 12; 12'den fazla satırda kalanlar `(+N more rows)` notuyla yazılır, bağlantı olmaz. (3) Her bağlantı hedefi PDF içinde çözülür. (4) Aynı md ve crop'larla iki kez üretilen PDF bayt bayt aynıdır (reportlab invariant modu). Madde 2-4 ve crop görüntüsünün kırpılmaması `tools\tests\test_check_pdf.py` ile zorlanır (`python -m unittest discover tools\tests`); madde 1 testte yalnız "0 missing" çıktısı olarak sınanır. Doğrulamaz: crop içeriğinin satırdaki değerle uyuştuğunu (bunu mühendis kontrol eder).
