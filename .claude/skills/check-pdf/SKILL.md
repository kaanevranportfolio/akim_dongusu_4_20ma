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
3. Çıktıyı oku: `OK ...: N pages, M crops, K missing`. K sıfırdan büyükse eksik crop'u üret, sonra yeniden çalıştır. Sonucu mühendise "kontrol PDF'i hazır: <yol>, <M> crop" diye bildir.
4. PDF elle düzenlenmez; değişiklik md'de yapılır ve yeniden üretilir. PDF'i commit etme kararı mühendisindir.

Her satırda: "Crop" hücresi crop adı + PDF sayfa numarası, tıklanınca o sayfaya gider; crop sayfası tabloya geri dönmeye yardım eder (sayfa başlığı crop adıdır). Mühendis crop ile karşılaştırınca satır [R] -> [V] olur; durumu md'de mühendis söyleyince işlenir.

Doğrular: `K missing` = 0, link sayısı = crop'lu satır sayısı, PDF aynı md'den yeniden üretilince aynı çıkar.
