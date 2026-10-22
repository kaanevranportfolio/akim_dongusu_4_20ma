# T001 - iskelet testi
Durum: BİTTİ
## İstek
Goal: verify that the pipeline skeleton works before any module uses it. Run from the module folder <pipeline>\01_secim, <pipeline> = C:\pipelines\akim_dongusu_4_20ma (open the session there). Never commit / push / amend / delete. Edit only: this ticket file, and create <pipeline>\02_simulasyon\sim\ (new files only: canary_rc.cir copy and sim\out outputs). Everything else is read-only.
Steps:
1. Report which CLAUDE.md files are loaded (expect pipeline root + 01_secim and nothing from C:\eda or C:\KiCAD_Projects) and list every skill you can see and every slash command (/start /report /closeout).
2. Confirm .claude exists at the pipeline root and in each of the four modules, and that no DOT_claude folder remains (the engineer renamed them by hand). Report any miss and stop.
3. Settings: run `git commit --dry-run` and report whether it was denied (expected in a module folder) or asked. Run `git status --short` (allowed). Do not run any other git write command.
4. Python check: `python -c "import pymupdf, reportlab, matplotlib; print('ok')"`, then `python ..\.claude\skills\datasheet-lookup\pdf_search.py` with no arguments (expect a usage message, not an import or path error), and `python ..\tools\check_pdf.py` with no arguments (expect usage).
5. datasheet-lookup regression: copy nothing; run the 8 questions of ..\.claude\skills\datasheet-lookup\tests_reference_load.md against the PDFs in C:\eda\programmable_electronic_load\docs\ref, from a scratch FACTS.md named in the FACTS_MD environment variable (copy of C:\eda\programmable_electronic_load\FACTS.md placed under 02_simulasyon\sim\scratch\). Report how many of the 8 answers equal the reference "Found" column. If the gate fails because doc_registry.json is empty, report that and do not copy the load registry; the engineer decides.
6. Canary: copy ..\tools\canary\canary_rc.cir to 02_simulasyon\sim\, then from the pipeline root run `powershell -NoProfile -ExecutionPolicy Bypass -File tools\run_sim.ps1 -SimDir 02_simulasyon\sim`. Report exit code and the canary_err_pct value; compare with C:\eda\programmable_electronic_load\sim\out (canary_rc meas file).
7. Output: a table, at most 8 lines (check | PASS/FAIL | value or message), then at most 5 lines of open issues.
## Sonuç
| # | Kontrol | Sonuç | Değer / mesaj |
|---|---|---|---|
| 1 | CLAUDE.md + skill/komut | PASS | Yüklenen: kök CLAUDE.md + 01_secim\CLAUDE.md; C:\eda ve C:\KiCAD_Projects'ten hiçbiri yok. Proje skill'leri 9 (bring-up-log, check-pdf, datasheet-lookup, figures, footprint-check, module-intake, pcb-review, qspice-sim, schematic-review); komutlar /start /report /closeout görünüyor (.claude\commands\*.md). Not: listede ayrıca genel/yerleşik skill'ler ve anthropic-skills:* kopyaları (figures, qspice-sim, vscode-ticket dahil) var |
| 2 | .claude klasörleri | PASS | Kök, 00_coordination, 01_secim, 02_simulasyon, 03_kicad'de .claude var; DOT_claude kalmadı |
| 3 | git commit --dry-run / status | PASS | commit --dry-run DENIED (beklenen); git status --short çalıştı (tüm iskelet untracked, commit yok) |
| 4 | Python | PASS | import ok; pdf_search.py ve check_pdf.py argümansız usage verdi (zorunlu argüman hatası: pdf / md), import/yol hatası yok |
| 5 | datasheet-lookup regresyonu | FAIL | 0/8 koşturulabildi: doc_registry.json boş (yalnız _comment), pdf_tables.py D01 için `GATE FAIL ... not in doc_registry.json`, çıkış kodu 2. Yük kaydı kopyalanmadı; karar mühendisin. Scratch FACTS.md: 02_simulasyon\sim\scratch\FACTS.md (FACTS_MD ile verildi) |
| 6 | Canary | PASS | run_sim.ps1 çıkış kodu 0; canary_err_pct_1tau 0.000139361, 2tau 3.7485e-05, 5tau 1.62618e-06; C:\eda\...\sim\out\canary_rc.meas.txt ile birebir aynı |
| 7 | Yazma sınırı | PASS | Yalnız bu bilet ve 02_simulasyon\sim\ (canary_rc.cir, canary_rc.qraw, out\, scratch\) |

Açık sorunlar:
- Adım 5: doc_registry.json boş; 8 soru koşulamadı. Mühendis karar vermeli: yük kaydını kopyala mı, yoksa girdileri belgeden okuyarak yeniden mi yaz (kayıt sahibi 00_coordination).
- Yük projesinin PDF'leri D<nn>_ önekli (D01_DS_stm32f103c8.pdf vb.); tests_reference_load.md eski adları (ads1115.pdf...) kullanıyor, kayıt girdileri ve test dosyası adları uyumlu hale getirilmeli.
- Kaynak PDF kütüphanesi için ayrıca <pipeline>\docs\ref kontrol edilmedi (adım 5 yük projesinin klasörünü kullanıyor).
