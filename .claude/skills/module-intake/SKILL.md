---
name: module-intake
description: Check the incoming freeze package from the upstream module and seed FACTS, NETS and FOOTPRINTS. Triggers - handoff, hand-off, paket, intake, devir, freeze.
---

# module-intake

Bu dosyada parça, yol veya sayı yazılı değildir. Paket `..\02_simulasyon\out\freeze\` klasöründe, salt okunur. Arayüz: `..\docs\INTERFACES.md` bölüm 8.

Adımlar:
1. Dosya listesi: `..\docs\INTERFACES.md` bölüm 8'deki beklenen dosyalara göre var/yok tablosu. Eksik dosya açık madde.
2. BOM sayımı: durum sütununa göre SEÇİLDİ / VARSAYILAN / AÇIK / DÜŞTÜ adedi; AÇIK ve VARSAYILAN satırların listesi (parça, neden açık).
3. Tutarlılık: her BOM parçası için PINMAP.md'de satır var mı (yoksa listele), FACTS.md'deki MPN BOM ile aynı mı, DECISIONS ile çelişen satır var mı. Çelişki uzlaştırılana kadar kullanılmaz; `docs\UPSTREAM.md`'ye yazılır.
4. Tohumlama (yalnız bu projenin dosyaları): FACTS.md "Parçalar" tablosunu BOM'dan, `docs\NETS.md`'yi KICAD_HANDOFF net listesinden, `docs\FOOTPRINTS.md`'yi BOM paket/footprint notlarından doldur; her satır özgün etiketi ve kaynağı (D<nn> p.<n>) taşır, etiket yükseltilmez. Yerleşim kısıtları FACTS "Yerleşim kısıtları" tablosuna.
5. Rapor: tek ekran özet + mühendisin karar vermesi gereken liste. Değer uydurma; bulunamayan "not found".

Doğrular: paketin eksiksizliğini ve kendi içinde tutarlılığını; hiçbir değeri yeniden doğrulamaz (doğrulama kaynak projede yapıldı, [V] etiketi aynen taşınır).
