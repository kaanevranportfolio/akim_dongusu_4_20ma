# 03_kicad - KiCad tasarımı (modül CLAUDE.md)
Kök yöntem: ..\CLAUDE.md geçerli. Burada yalnız bu modüle özgü olanlar var. Çelişkide bu dosya kazanır (Safety ve settings.json hariç).

## Rol
Dondurulmuş tasarımdan (..\02_simulasyon\out\freeze\, salt okunur) şema, yerleşim, DRC ve fabrikasyon çıktıları. Parça seçimi ve simülasyon burada yeniden yapılmaz.

## Girdi (intake)
module-intake skill: dosya listesi, BOM sayımı (SEÇİLDİ/VARSAYILAN/AÇIK/DÜŞTÜ), her BOM satırı PINMAP ve FACTS ile tutarlı mı, ilgili etiketleri taşıyarak FACTS.md / docs\NETS.md / docs\FOOTPRINTS.md tohumlama. Upstream'de bulunan sorun sessizce düzeltilmez: docs\UPSTREAM.md (madde, kanıt, önerilen değişiklik).

## KiCad kuralları
- Mühendis şematik ve kartı KiCad GUI'de düzenler. Claude .kicad_* dosyalarını düzenlemez; kicad-cli dışa aktarımları (netlist, ERC/DRC JSON, BOM, SVG/PDF) ve salt okunur betiklerle okur. Büyük .kicad_* dosyaları bağlama okunmaz.
- Pin kimliği: sembol pin adı ve numarası PINMAP.md; net adı freeze net listesi (alias kuralı: ASCII, büyük harf, alt çizgi, <PARÇA>_<PİN>, yalnız harf farkıyla ayrışan ad yok); referans BOM.md. Değişiklik docs\NETS.md ve docs\UPSTREAM.md'ye.
- Footprint: docs\FOOTPRINTS.md'de parça başına satır (MPN, paket basılı yazımla, D<nn> sayfa, land pattern crop, durum [R] -> [V]). Footprint-check ve mühendis kontrolü olmadan kullanılmaz; kütüphane footprint'i aday.
- Tasarım kısıtları (clearance, iz genişliği, Kelvin sense, ısıl, kart boyutu, katman) freeze'den etiketiyle gelir; belgede olmayan sayı [A] ve HANDOFF'ta listelenir.
- Kapılar: yerleşimden önce intake tamam, ERC temiz veya her uyarı gerekçeli, netlist = freeze net listesi (schematic-review), her footprint [V]. Fabrikasyondan önce DRC temiz veya gerekçeli (pcb-review), BOM = freeze BOM, mühendis go. Fab dosyaları go'dan önce üretilmez.

## Yollar
- KiCad projesi: 03_kicad\akim_dongusu_4_20ma.kicad_pro / .kicad_sch / .kicad_pcb [A] (mühendis KiCad'de oluşturur)
- kicad-cli: C:\Program Files\KiCad\10.0\bin\kicad-cli.exe
- Raporlar: docs\review\ (erc.json, drc.json, netlist, BOM); kontrol PDF'i: python ..\tools\check_pdf.py docs\<tablo>.md --crops ..\02_simulasyon\out\freeze\figures docs\figures docs\review\crops
