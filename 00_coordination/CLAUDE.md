# 00_coordination - modül CLAUDE.md
Kök yöntem: ..\CLAUDE.md geçerli. Burada yalnız bu modüle özgü olanlar var. Çelişkide bu dosya kazanır (Safety ve settings.json hariç).

## Rol
Koordinatör: SPEC.md sahibi, genel durum, belge kütüphanesi (docs\ref: D numaraları), pipeline kökü dosyaları (CLAUDE.md, docs\, tools\, .claude\) ve git.
Diğer modüllerin HANDOFF.md ve FACTS.md dosyalarını salt okunur okur; onların klasörlerine yazmaz.

## Spec
SPEC.md mühendisin metnidir. Ajan sürüm yükseltmez, değer değiştirmez; önerdiği değişiklikler HANDOFF.md açık maddesine yazılır, mühendis v0.2'yi onaylar.

## Belge alımı (docs\ref)
Yeni PDF: docs\ref\'e konur -> sıradaki D<nn> (hiç yeniden kullanılmaz) -> docs\ref\INDEX.md satırı -> .claude\skills\datasheet-lookup\doc_registry.json kaydı (tam parça, varyant ve revizyon belgenin kendisinden okunur, ilgili modülün FACTS.md ile karşılaştırılır).

## Git
Commit ve push yalnız pipeline kökünden açılan oturumda, bu klasörün docs\tasks biletiyle: önce git status, açık yollar, tam mesaj, commit ve push için mühendisin ayrı onayı. Etiketi (tag) yalnız mühendis koyar.

## Ortak araçlar
tools\ (run_sim.ps1, qraw*.py, check_pdf.py, canary\, component_selector\) ve .claude\skills tek kopyadır; değişiklik bu klasörün biletiyle yapılır ve docs\RULE_LEDGER.md güncellenir.
