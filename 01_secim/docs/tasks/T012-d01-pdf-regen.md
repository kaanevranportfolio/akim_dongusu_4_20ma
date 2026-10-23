# T012 - d01-pdf-regen
Durum: BİTTİ
## İstek
Goal: regenerate 01_secim\out\passA\check\D01_critical.pdf with the fixed tool (00_coordination/T023, T024); the old PDF came from the old tool. Do not edit the md.
Session folder: C:\pipelines\akim_dongusu_4_20ma\01_secim . Run only if no other 01_secim ticket is ÇALIŞIYOR (T011 touches FACTS.md, not these files).
Steps:
1. From the session folder run: `python ..\tools\check_pdf.py out\passA\check\D01_critical.md --out out\passA\check\D01_critical.pdf --crops docs\figures` (add docs\ref\_crops only if the tool or the md needs it). Overwrite the old PDF; no other file is deleted.
2. Check the new PDF (PyMuPDF text search is fine): every crop page starts with a "← Tabloya dön" link (at most 12 per crop, then "(+N more rows)"); every table row with a Crop cell has an internal link; count pages (N), crops placed (M), crops named in the md but not found (K).
3. If K is not 0: do not deliver the PDF; list the missing crop names in Sonuç and stop.
4. Last message of the session must contain exactly: `kontrol PDF'i hazır: out\passA\check\D01_critical.pdf, <N> sayfa, <M> crop, <K> eksik`.
5. /closeout: HANDOFF.md and docs\DEVLOG.md (re-read before editing). No commit.
May edit: this ticket; out\passA\check\D01_critical.pdf (overwrite, generated); at /closeout HANDOFF.md and docs\DEVLOG.md. Everything else read-only. Never commit / push / amend / delete.
Result: at most 5 lines: N, M, K, whether every crop page has the return link, tool warnings if any.
## Sonuç
N = 18 sayfa (12 tablo + 6 crop), M = 6 crop yerleştirildi, K = 0 eksik (`OK out\passA\check\D01_critical.pdf: 18 pages, 6 crops, 0 missing`).
Her crop sayfası "← Tabloya dön" bağlantısıyla başlıyor (6/6: sayfa 13-18); D01_p8_electrical_a.png sayfasında 12 satır bağlantısı + "(+3 more rows)" işareti (15 satır, sınır 12).
Tablo sayfalarında 55 iç bağlantı, md'de crop adı geçen 53 satır; her Crop hücreli satırın bağlantısı var. Araç uyarısı yok. md düzenlenmedi, eski PDF üzerine yazıldı, hiçbir dosya silinmedi.
kontrol PDF'i hazır: out\passA\check\D01_critical.pdf, 18 sayfa, 6 crop, 0 eksik

Ana chat için not (mühendis geri bildirimi, 2026-10-23):
1. Mühendis D01_critical.pdf'i kontrol etti: "genel olarak doğru". Satır satır karşılaştırma bildirilmedi, bu yüzden FACTS.md "Kritik değerler" satırları [R] / Kontrol: bekliyor kaldı; hangi satırların [V] olacağı mühendisin açık kararı bekliyor (planner: bilet veya talimat).
2. Mühendisin gözlemi: Typical Characteristics grafikleri verilmiş ama değer çıkarılmamış; model değer okunacaksa hassas okunmalı. Durum: yalnız Figure 14 (Small-Signal Overshoot vs Load Capacitance, D01 p.11) kaba okundu [C] (≈ 10 % @ 100 pF); diğer grafiklerden okuma yapılmadı (bilet kapsamı tablo değerleriydi).
3. Mühendis yaklaşımı: SPICE modeliyle simülasyon yapılacak, terslik çıkarsa grafiğe dönülecek (G5, 10 nF kararlılığı, simülasyonla cevaplanacak; D01'de 10 nF yok). Model-datasheet karşılaştırması gerekirse grafikten nokta okuma ihtiyacı doğar.
4. Öneri (karar mühendiste/planner'da): isteğe bağlı küçük bilet: seçili grafiklerden (Aol/faz–frekans, Iq–sıcaklık/besleme, IB–sıcaklık, çıkış salınımı–akım, overshoot–CL) belirli noktalar okunur; her değer [C], ± belirsizlik, crop'lu, ayrı tablo; [V] olmaz.
5. Açık: SPICE düğümü VCC/VEE ↔ datasheet V+/V– eşlemesi "open", simülasyonda kullanılacağı için mühendis onayı gerekiyor.
