---
name: datasheet-lookup
description: Look up a value in a vendor document with minimal text. Triggers - datasheet, ESR, limit, pin, page, değer, belge, sayfa, tablo, figure.
---

# datasheet-lookup

Yollar: oturum modül klasöründen açılır (cwd = modül). Betikler `..\.claude\skills\datasheet-lookup\` altındadır; PDF'ler `..\docs\ref\` kütüphanesindedir (tek kütüphane); `FACTS.md` o modülün kendi dosyasıdır (cwd); kapı kaydı `doc_registry.json` bu skill klasöründedir (pipeline geneli, sahibi 00_coordination). Mühendise verilecek crop'lar `--out docs\figures` ile modülün şekil klasörüne yazılır.

Sıra (değiştirme):
1. `FACTS.md` önce. Değer orada [V] + sayfa ile varsa belgeye gitme.
2. Yoksa ara: `python ..\.claude\skills\datasheet-lookup\pdf_search.py <pdf> "<terim>" [--context 2]`
   Çıktı sayfa işaretlidir (`=== PDF p.N ===`) ve en çok 60 satırdır.
   Parametre tablosu için: `python ..\.claude\skills\datasheet-lookup\pdf_tables.py <pdf> <sayfa> [--table K] [--grep METİN]` (en çok 60 satır; satırlar sütun başlıklarıyla: min/typ/max/birim/koşul).
3. Gerekirse tek sayfanın tek aralığını oku: `pdf_search.py <pdf> --page N --from L1 --to L2` (en çok 60 satır).
4. Yalnızca şekil/grafik/land pattern/denklem için: `python ..\.claude\skills\datasheet-lookup\pdf_crop.py <pdf> <sayfa> x0 y0 x1 y1 [--dpi 150]`
   Koordinatlar sayfanın 0-1 oransal değerleridir; tek kırpılmış PNG yazar (`docs\ref\_crops\`), sonra Read ile görüntüle. Tam sayfa görüntü yok.
   Metin olarak temiz çıkmayan denklem veya sembol: `pdf_crop.py <pdf> <sayfa> --around "<etiket metni>" [--pad-up 0.04] [--pad-down 0.10]` denklemi etiketiyle tek görüntüde kırpar.
   Crop adı kuralı: mühendise verilen her crop `D<nn>_p<sayfa>_<konu>.png` adıyla kaydedilir (`--topic <konu>`, D<nn> PDF dosya adından veya `--doc D<nn>`), cevapta D<nn> ve sayfa atfedilir.
5. Ekran görüntüsü yerine netlist veya SVG kullan.

## Varyant kapısı (her aramadan önce, otomatik)
Her betik başlarken `GATE OK` / `GATE FAIL` basar. Kapı `doc_registry.json` kaydına bakar: parça adı `FACTS.md`'de geçmeli, belgede kayıttaki zorunlu metinler bulunmalı, ilk 3 sayfada yasak metin olmamalı, revizyon metni sayfa 1-2'de olmalı. Kayıtta olmayan veya uyuşmayan belgede betik çıkış kodu 2 ile durur: aramayı sürdürme, mühendise bildir (olay: NRF2401.PDF). Yeni belgeyi kayda eklemeden önce parçayı, tam varyantı ve revizyonu belgenin kendisinden oku ve FACTS.md ile karşılaştır.

## Kayıt kuralları
- Her kayıtlı değer şunları taşır: sütun (min / typ / max), birim, koşullar (tablo üstündeki genel koşul satırı, satır koşulu, dipnot harfi ve metni), belge, sayfa. Yalnızca typ verilmişse "yalnızca typ" yaz; typ min/max yerine kullanılmaz.
- Sayfa: her zaman PDF sayfası; basılı sayfa farklıysa ikisi birlikte (`PDF p.N (printed p.M)`). Betik ikisini de basar; basılı sayfa bulunamazsa "not determinable" der.
- Tablo hücresi birleşikse (örn. `1.238 1.25 1.262` tek hücrede) `pdf_tables.py` `[MERGED CELL ...]`, `[AMBIGUOUS ...]` veya `[single value under MIN only ...]` işaretler. İşaretli satırı sayfa görüntüsüyle doğrula (adım 4) ve sonucu MATCH / CORRECTED (eski -> yeni) olarak kaydet. Örnek: LM1117-3.3, TJ = 25 °C satırındaki 3,3 V metinde min sütununda göründü, görüntüde typ sütunundadır.
- Dipnot harfleri (a, b, ...) satırın koşuludur; `pdf_tables.py` dipnotları tablonun altında basar.
- Grafikten okunan değer [V] olmaz: `[C] grafikten okundu, ±x %`.

## Arama terimleri
Belgenin kendi eş anlamlılarını dene, sonra "bulunamadı" de: `pdf_search.py` terim eşleşmezse otomatik dener (VDD / VCC / supply voltage / power supply; ESR / equivalent series resistance; Iq / quiescent / supply current; output capacitor / Cout; absolute maximum; dropout; thermal resistance ...). Çıktı hangi eş anlamlıyla bulduğunu veya `no match after trying: ...` listesini yazar. Liste `pdf_search.py` içindeki `SYNONYMS`; belgeye özgü yeni terim görürsen oraya ekle.

## Rapor
Her betik son satırda `REPORT: lines_read=N tables_used=T images_used=I` basar. Her aramanın sonunda bu üçünü bildir (okunan satır, kullanılan tablo, kullanılan görüntü). Bir aramanın birden çok çağrısı varsa topla.

## Kurallar
- Değer yalnızca **tam parçanın kendi belgesinden** alınır (varyant/paket eşleşmeli). Başka parça, ailenin başka üyesi veya benzer belge kullanılmaz.
- Her değer FACTS.md'ye `[V] belge + sayfa` ile yazılır. Tablo değerinde birim/sütun şüpheliyse sayfa görüntüsüyle (adım 4) doğrula; grafikten okunan değer [V] olmaz, `[C] grafikten okundu, ±x %` yazılır.
- Birbiriyle çelişen iki değer uzlaştırılana kadar kullanılmaz; ikisi de FACTS.md'de çelişki notuyla durur ve HANDOFF'a açık madde olur.
- Belge yoksa dur: değer [A] kalır, `DOCS_NEEDED.md` güncellenir.
- Yeni PDF'ler (mühendis ekledi ya da otomatik indirildi) kayıt sırasında sıradaki boş `D<nn>_` önekini alır ve `..\docs\ref\INDEX.md`'ye bir satır yazılır; bu iş 00_coordination biletiyle yapılır, modül oturumu belge kütüphanesine yazmaz.

## Test seti
`tests.md` ve `tests_reference_load.md`: yük projesinin 8 sorusu (referans yanıtlar mühendis onaylı). Betikleri değiştirdikten sonra sorular yeniden yanıtlanır; mühendisin onayladığı yanıtlar beklenen değerdir.

Doğrular: bir değerin gerçekten hangi belgenin hangi sayfasından geldiğini.
