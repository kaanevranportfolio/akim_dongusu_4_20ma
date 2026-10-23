# T023 - check_pdf back-to-table link: review, regression test, doc-vs-code audit
Durum: BİTTİ
## İstek
Context: tools\check_pdf.py docstring and the check-pdf SKILL.md promise a "back to table" link on every crop page; the code did not produce it (missed when moved from LOAD). A Cowork session then patched tools\check_pdf.py directly, outside any ticket, uncommitted: row anchors in the table, a "← Tabloya dön" line link at the top of each crop page (max 12), crop height FRAME_H-90. Reported test: 01_secim\out\passA\check\D01_critical.md -> 18 pages, 6 crops, 0 missing, links go to rows.
Never commit / push / amend / delete / revert. Do NOT revert or discard the existing patch. Never read .env or tokens. Never open PDFs in docs\ref except through the existing tools. Edit only: this ticket, tools\check_pdf.py, tools\tests\ (new test files), .claude\skills\check-pdf\SKILL.md (only the "Doğrular" line in step B). Test output goes to a temp/scratch dir, never into 01_secim\out. Do not run anything in 01_secim.
Steps:
A. Run `git status` and `git diff -- tools\check_pdf.py`. Review the patch (anchor ids unique and stable, link targets resolve, 12-link cap behavior when a crop is used by more than 12 rows, FRAME_H-90 does not clip content). Fix defects in place. Show the diff summary (at most 15 lines) in Sonuç.
B. Add a regression test (tools\tests\test_check_pdf.py or the existing test layout): build a sample md + 2 crops, generate the PDF, assert (1) per crop page, number of back-links = number of rows using that crop (capped at 12), (2) every link destination resolves to an existing anchor/named destination. Offline, no network. Add one sentence to the check-pdf SKILL.md "Doğrular" line stating this check. Report pytest counts.
C. Audit doc-vs-code mismatches: for each of check_pdf, pdf_crop, pdf_search, pdf_tables, run_sim, qraw_export (tools\ and their skills\SKILL.md; origin LOAD or KiCAD), list every claim in the docstring and SKILL.md and whether the code implements it (claim | where stated | code evidence file:line | OK/MISSING/PARTIAL). Report only; do NOT fix (separate ticket). If a tool or skill file is not found, say so.
D. Find where the T001 skeleton test is defined (T001 itself is closed/append-only: do not edit it). If a reusable source exists (script, command, checklist), add a check_pdf sample run there; otherwise report where it should go and why none exists. State briefly why the missing link was not caught earlier [A allowed, label it].
E. Identify what is missing or too weak so sessions report the PDF path: read .claude\skills\check-pdf\SKILL.md step 3 ("kontrol PDF'i hazır: <yol>, <M> crop") and the module CLAUDE.md files (read-only). Report gaps and a concrete wording proposal; do not edit module CLAUDE.md files.
F. Not in this ticket: regenerating 01_secim\out\passA\check\D01_critical.pdf is a separate 01_secim ticket after A-B are done.
Output: Sonuç with A diff summary, B test counts, C table (at most 30 lines), D and E at most 6 lines each, git status listing of changed paths. No full file dumps.
## Sonuç
**A. Yama incelemesi** (Cowork yamasına dokunulmadı, geri alınmadı; üstüne bir düzeltme eklendi)
- Satır çapaları `row_<tablo>_<satır>`: benzersiz ve kararlı; hedefler çözülüyor (B testi). Bir crop >12 satırda kullanılınca ilk 12 link yazılıyordu, fazlası sessizce kesiliyordu.
- Kusur 1: `FRAME_H-90` sabit payı, 12 link satırı sarınca yetmeyebilirdi (başlık+link satırı+altyazı gerçek yüksekliği ölçülmüyordu). Düzeltme: yükseklik `wrap()` ile ölçülüp ayrılıyor.
- Kusur 2: kesilen satırlar görünmüyordu. Düzeltme: 12'den fazlaysa "(+N more rows)" yazılıyor.
- Kusur 3 (doc): docstring kullanım örnekleri `python docs\check_pdf.py` idi (eski LOAD yolu); `python ..\tools\check_pdf.py` ve varsayılan crop klasörleri olarak düzeltildi.
- Diff: tools\check_pdf.py +29/-10 (Cowork yaması + bu düzeltmeler), SKILL.md +1/-1.

**B. Regresyon testi**: tools\tests\test_check_pdf.py (çevrimdışı, geçici klasörde 2 crop; 16 satır: 15'i CROP_A'yı, 2'si CROP_B'yi kullanır (biri ikisini birden); beklenen geri-link A için 12 (üst sınır), B için 2).
- Sayım: `python tools\tests\test_check_pdf.py` -> Ran 6 tests, OK (6 geçti, 0 kaldı). **pytest bu makinede kurulu değil** (`No module named pytest`); test unittest tabanlı olduğu için pytest ile de çalışır, ama pytest sayımı alınmadı. Kurmak mühendisin kararı (ağ).
- Test eski HEAD sürümünde 3 test düşürüyor (geri-link 0), yenide geçiyor.
- SKILL.md "Doğrular" satırına bu denetim cümlesi eklendi.

**C. Doc-vs-code denetimi** (yalnız rapor; düzeltme yok)
| İddia | Nerede | Kod kanıtı | Durum |
|---|---|---|---|
| Satırda crop adı -> Crop hücresi + sayfa linki | check_pdf docstring, SKILL | check_pdf.py:147-155 | OK |
| Crop başına tek sayfa, geri link | docstring, SKILL | check_pdf.py:169-176 | OK (T023 ile) |
| Eksik crop yazdırılır, hata yok | docstring | check_pdf.py:176, 201-204 | OK |
| Aynı girdi -> aynı çıktı | docstring | invariant=1 (satır 187) | OK (yeniden-üretim testi yok) |
| `--crops` varsayılanı = SKILL'deki liste | SKILL adım 2 | DEFAULT_CROPS satır 33 | OK |
| Kullanım `docs\check_pdf.py` | eski docstring | — | düzeltildi (A) |
| "K missing=0, link sayısı=crop'lu satır" | SKILL Doğrular | yalnız missing sayılıyor; link sayısı test ile | PARTIAL -> T023 testi |
| pdf_crop: oransal koordinat, tek PNG | pdf_crop docstring, SKILL 4 | pdf_crop.py:92-93, 112 | OK |
| "Tam sayfa görüntü yok" | SKILL 4 | `0 0 1 1` kabul ediliyor (satır 92) | PARTIAL |
| `--topic` -> D<nn>_p<s>_<konu>.png | pdf_crop | pdf_crop.py:116-121 | OK; D<nn> bulunamazsa sessizce eski ad (belgeli) |
| `--around`, pad-up/down | SKILL 4 | pdf_crop.py:102-108 | OK |
| dpi 100..200 | (kodda) | satır 94 | SKILL'de yok (belgesiz) |
| pdf_search: en çok 60 satır | SKILL 2 | _common MAX_LINES=60; pdf_search.py:213-215 | PARTIAL (kesme notu +1 satır) |
| pdf_search: eş anlamlı otomatik | SKILL "Arama terimleri" | pdf_search.py:145-208 | PARTIAL: eşleşme yalnız aranan terim kodun 7 grubundan birine tam eşitse; SKILL listesinin sonu (kesik satır) kodla karşılaştırılmadı |
| Her betik son satırda REPORT basar | SKILL "Rapor" | pdf_crop.py:124, pdf_tables.py:117 var; **pdf_search.py'de report() çağrısı yok** | **MISSING** (pdf_search) |
| Her betik GATE OK/FAIL basar | SKILL Varyant kapısı | gate() search/crop/tables'ta çağrılıyor | OK |
| Kapı: kayıt, FACTS'te parça, require/forbid, revizyon | SKILL | _common.py:25-53 | OK |
| Basılı sayfa "not determinable" | SKILL | _common.py:70-74 | OK |
| pdf_tables: MERGED/AMBIGUOUS/single-value işaretleri, dipnot | SKILL, docstring | pdf_tables.py:38,43,44,61 | OK |
| pdf_tables: en çok 60 satır, --table, --grep | SKILL 2 | pdf_tables.py:69-70, 113-115 | OK |
| Test seti 8 soru | SKILL "Test seti" | tests_reference_load.md; eski PDF adları, kayıt boş (T001) | PARTIAL (koşulamıyor) |
| run_sim: -SimDir zorunlu | SKILL 4 | run_sim.ps1:38-46 | OK |
| .tran .save'siz -> çıkış 4 | SKILL exit codes | run_sim.ps1:149-150, 236 | OK |
| Eksik model -> 3 | SKILL | run_sim.ps1:140-146, 235 | OK; "sembol kütüphanesi model olarak" kısmı Test-Models'te bakılmadı |
| Canary > %0.01 -> 5 | SKILL | run_sim.ps1:172-176, 237 | OK |
| "canary_rc.cir önce koşar" | SKILL 4 | `canary_err_pct` yalnız .meas ile aranıyor; canary'nin otomatik ilk koşması koddan görülmedi | PARTIAL [A] |
| LONG: -Long, 30 dk / 4 sa | SKILL 3-4 | run_sim.ps1:130-136, 154 | OK; "15 dk üstü LONG işaretlenir" insan kuralı, kodda yok |
| -CleanRaw yalnız temiz parti + analyzer 0 | SKILL 7 | run_sim.ps1:217-230 | OK |
| SIM_RAW_LIST / SIM_OUT_DIR | qraw_export docstring | run_sim.ps1:194-195; qraw_export.py:143-144 | OK |
| qraw_export: --max-points, 5000, dekimasyon, çıkış 0/1 | docstring | qraw_export.py:28,132,161 | OK |
| Dosyalar bulundu mu | — | pdf_crop/search/tables `.claude\skills\datasheet-lookup\` altında (tools\ altında DEĞİL); run_sim, qraw_export tools\ | hepsi bulundu; kaynak LOAD/KiCAD kopyası, orijinallerle karşılaştırılmadı |

**D. T001 iskelet testi**: T001 (kapalı) adım 4 yalnız `check_pdf.py`'yi argümansız çalıştırdı (usage); örnek koşu yoktu, tests.md yalnız datasheet-lookup içindi. Yeniden kullanılabilir kaynak yok. Öneri: örnek koşu tools\tests\test_check_pdf.py (bu bilet) olsun; bir sonraki iskelet/denetim bileti bunu çağırsın. Neden yakalanmadı [A]: iskelet testi araçların "başlıyor mu" yanıtına bakıyordu, çıktı içeriğine (link) bakmıyordu; yama LOAD'dan taşınırken docstring/SKILL kopyalandı, davranış testi yoktu.

**E. PDF yolunun bildirilmesi**: SKILL adım 3 "kontrol PDF'i hazır: <yol>, <M> crop" diyor ama (1) hangi crop sayfası/link doğrulandı belirtilmiyor, (2) hiçbir modül CLAUDE.md'si bunu çağırmıyor: yalnız 03_kicad/CLAUDE.md:20 komutu veriyor; 01_secim ve 02_simulasyon'da PDF/check kuralı yok, (3) kök kuralı "delivered as PDF" diyor ama yolu bildirme yok. Öneri (modül CLAUDE.md'lerine, ayrı bilet): "Mühendise kontrol tablosu veren her oturum, son mesajına şu satırı koyar: `kontrol PDF'i hazır: <modül göreli yol>.pdf, <N> sayfa, <M> crop, <K> eksik` ve `K=0` değilse dosyayı teslim etmez." Komut: `python ..\tools\check_pdf.py docs\<tablo>.md`.

**Değişen yollar (git status)**: M tools\check_pdf.py, M .claude\skills\check-pdf\SKILL.md, ?? tools\tests\ (test_check_pdf.py; __pycache__ üretildi), ?? bu bilet. 01_secim\out'a yazılmadı, 01_secim'de çalıştırılmadı. Commit/push yapılmadı. F (D01_critical.pdf yenileme) kapsam dışı.
