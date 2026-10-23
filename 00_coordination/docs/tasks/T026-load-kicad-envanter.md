# T026 - inventory of the legacy LOAD / KiCAD simulation and figure tooling vs the pipeline (read-only)
Durum: BİTTİ
## İstek
Context: the engineer wants to know whether the QSPICE simulation flow and the circuit-schematic / figure drawing that worked in the earlier projects (LOAD at C:\eda, KiCAD at C:\KiCAD_Projects) were fully taken into the pipeline. Today the pipeline has tools\run_sim.ps1, tools\qraw_export.py, tools\check_pdf.py, the qspice-sim / figures / check-pdf / datasheet-lookup skills, and docs\sim\pin_map.py; docs\sim\circuits.py (the netlist-to-schematic drawer named by CLAUDE.md Figures rule 1) does not exist. We need an evidence-based list of what exists in the legacy trees and is not in the pipeline.
This ticket is READ-ONLY inventory. Never commit / push / amend / delete / move / copy files into the pipeline. Never read .env, tokens, certificates or any file named like them. Do not open PDFs. Do not run simulations or any legacy script; reading file names, sizes, dates, docstrings, SKILL.md files, CLAUDE.md files and script source text is allowed. Read the legacy trees only down to depth 4 from C:\eda and C:\KiCAD_Projects; do not search elsewhere. Edit only this ticket.
Steps:
0. First look for any existing migration record made when the pipeline was set up (what was taken from the old project folders and what was left): search only inside the pipeline (HANDOFF.md, DEVLOG*, docs\, docs\tasks\T001/T002, CLAUDE.md files, .claude\) and report what it says in at most 10 lines with file names. The engineer says all old project folders were shown during setup, so if a record exists use it as the baseline and mark every item as "recorded" or "not recorded"; the rest of the steps then verify only items that are not recorded or whose pipeline copy differs.
1. List both roots (depth <= 4), excluding .git, __pycache__, venvs, large outputs (*.raw, *.png, *.pdf, *.mp4). Report counts and the top-level folder names only.
2. Find every item of these kinds and report one row each: path | size | last modified | one-line purpose from its docstring/header | present in pipeline? (same name or same function; give the pipeline path) | status: COPIED / ADAPTED / MISSING / DIFFERENT.
   a) QSPICE flow: run scripts, batch runners, canary files, .raw analyzers/exporters, measurement (.meas) helpers, log parsers, sweep/corner/Monte Carlo drivers.
   b) Schematic / circuit drawing: netlist parsers, schematic or block-diagram generators, SVG/PNG figure scripts, plotting scripts for waveforms/Bode/loop gain, color/legend helpers, any script that verifies "every element drawn".
   c) Skills and commands: .claude\skills, .claude\commands, CLAUDE.md rules about figures and simulation, tests files.
   d) Anything else clearly reusable for a 4-20 mA loop transmitter simulation (templates, testbench libraries, SPICE model folders with license notes).
3. For every MISSING or DIFFERENT item that matters, say in one line what in the pipeline depends on it or would (e.g. Figures rule 1 needs the drawer; 02_simulasyon needs X). Do not guess: if purpose is unclear from the header, write "unclear".
4. Compare run_sim.ps1 and qraw_export.py against their legacy originals if the originals are found (hash + diff summary of at most 10 lines each).
5. Propose an adaptation plan (not executed): ordered list of follow-up tickets, each with scope, files to copy/adapt, tests, and which module owns it. Mark licensing or path issues (hard-coded C:\eda paths, machine-specific assumptions).
6. Do NOT copy or modify anything. Sonuç: inventory table (at most 40 rows; group trivial files), dependency lines, diff summaries, plan (at most 15 lines), then "OPEN:" line with unknowns.
## Sonuç
Yalnız okundu; kopyalama/değiştirme/komut çalıştırma yok (okunan: dosya adı, boyut, tarih, docstring/başlık, sha256 hash'i, diff). Uyarı (kapsam): derinlik 4 sınırı `.claude` ağaçlarında bir kademe aşıldı (KiCAD pcb `.claude\skills` dosya adları listelendi, içerikleri okunmadı). `C:\eda\programmable_electronic_load\.claude\skills` ve `docs\sim\<testbench>\result.py` (derinlik 5) ve `C:\eda\...\sim\out` incelenmedi.

**Adım 0 - mevcut göç kaydı (7 satır).** (1) `tools\README.md`: kaynaklar C:\eda\tools ve KiCAD_Projects, kopyalar 2026-10-22; run_sim.ps1, qraw.py, qraw_export.py "byte-exact kopya", canary_rc.cir her modüle kopyalanır, check_pdf.py uyarlandı (ROOT=cwd), component_selector T002'ye bırakıldı. (2) `docs\RULE_LEDGER.md` (2026-10-22): kural kaynakları EDA/KIT/KCAD/YÜK/QS tablosu; "Bilerek düşenler": /brief, supervisor, proposals\, gen_sch.py/gen_pcb.py ("nrf24'e bağlı, bu turda taşınmadı"). (3) `00_coordination\HANDOFF.md` madde 7-8 (klasör taşıma, eski start.md atfı). (4) T001 canary karşılaştırması: C:\eda koşusuyla birebir aynı. (5) `.claude\skills\datasheet-lookup\tests.md`: tests_reference_load.md yük projesinden. docs\sim\circuits.py, plotkit.py, pinmap_pdf.py, power_pdf.py, doc_layout.py, SİM/şekil üreteçleri, SPICE model klasörü ve legacy docs\ (ARCHITECTURE/backlog/lessons) için kayıt YOK: "taşınmadı" ya da "bilerek düşen" diye yazılmamış.

**Adım 1 - kökler (derinlik <=4, .git/__pycache__/*.raw/*.png/*.pdf/*.qraw hariç).** C:\eda: 392 dosya; üst klasörler: .claude, docs, new_project_essentials, nrf24_power_module, programmable_electronic_load, tools, tps54360_buck (dosya türleri: 88 md, 76 cir, 27 py, 1 ps1). C:\KiCAD_Projects: 63 dosya; üst klasörler: new_kicad_project_kit, programmable_electronic_load_pcb (51 md, 4 py).

**Adım 2 - envanter** (tarih: LOAD betikleri 2026-10-16/17).

| # | yol (C:\eda altında, aksi belirtilmedikçe) | boyut | amaç (docstring) | pipeline'da | durum |
|---|---|---|---|---|---|
| a1 | tools\run_sim.ps1 | 15 274 | QSPICE batch koşucusu | tools\run_sim.ps1 | ADAPTED (yalnız 3 yorum satırı farklı, T024; sha256 farkı bu yüzden; README "byte-exact" artık yanlış) |
| a2 | tools\qraw.py (5 438) | | .qraw okuyucu | tools\qraw.py | COPIED (sha256 aynı 88202a79) |
| a3 | tools\qraw_export.py (6 767) | | .qraw -> CSV | tools\qraw_export.py | COPIED (sha256 aynı bf1b94bc) |
| a4 | programmable_electronic_load\sim\canary_rc.cir (+3 şablon/proje kopyası, 940) | | sayısal canary | tools\canary\canary_rc.cir, 02_simulasyon\sim\canary_rc.cir | COPIED (sha256 aynı a39ff675) |
| a5 | nrf24_power_module\sim\analyze_*.py (3), report_dvr.py (44 113), lessons_learned.py (18 603); tps54360_buck\sim\analyze_smoke.py | | proje analizörleri/rapor (.qraw akışı, DVR PDF) | yok | MISSING (nrf24/tps54360'a özgü; DVR PDF üreteci ayrıca doc_layout.py'ye bağlı) |
| a6 | programmable_electronic_load\sim\*.cir (~76 .cir: diag_*, loop_*, naming_canary*, irfp250n_*, opa2192\*) | | yük devresi testbench'leri ve tanılar | yok | MISSING (4-20 mA için doğrudan değil; naming_canary_* = QSPICE harf duyarsızlığı kanıtı, kural 46 ile ilişkili) |
| a7 | nrf24 sim\*.cir (7), tps54360 sim\tps54360_smoke.cir | | LDO/buck testbench'leri | yok | MISSING (unclear kullanım) |
| a8 | sweep/corner/Monte Carlo sürücüsü, .meas yardımcısı, log ayrıştırıcı | | | yok (legacy'de de yok) | arandı, bulunamadı |
| b1 | programmable_electronic_load\docs\sim\circuits.py | 64 066 | "Draw the circuit schematic of a QSPICE testbench from its .cir netlist"; Netlist ayrıştırıcı, Sheet çizim ilkelleri, `finish()` her eleman bir kez çizildi/başka bir şey çizilmedi/her net bağlı/her .save sinyalinin probe etiketi var doğrulaması; `check_pinmap`/`pinmap_report` (model pin adı - PINMAP karşılaştırması); yerleşim elle | **docs\sim\circuits.py YOK** | MISSING |
| b2 | ... docs\sim\plotkit.py | 3 358 | result.py'ler için CSV yükleme, altbilgi (model SHA), SVG+PNG çıktı, kesişim ölçümü | yok | MISSING |
| b3 | ... docs\sim\<45 testbench klasörü> (circuit/result .svg/.png/.py) ve docs\sim\INDEX.md (16 398) | | üretilmiş çıktılar ve indeks | docs\sim\ yok (yalnız T025 pin_map.py) | MISSING (çıktılar yük projesine özgü, yalnız biçim referansı) |
| b4 | ... docs\figures\power-tree.py (7 432), pre-boot-strapping.py (9 946); KiCAD_Projects\...\handoff\extra\power-tree.py (aynı 7 432) | | veri md'den okunan SVG+PNG şekil üreteci | yok | MISSING (yük projesine özgü; yaklaşım şekil kuralıyla uyumlu) |
| b5 | ... docs\pinmap_pdf.py (14 500), docs\power_pdf.py (7 041), new_project_essentials\...\docs\pinmap_pdf.py (11 759) | | PINMAP.md/POWER.md -> PDF (crop sayfaları, geri link) | tools\check_pdf.py işlevi (genel) | ADAPTED/işlev kapsanıyor (pipeline genel tablo->PDF; PINMAP'e özgü ayrıştırma yok) |
| b6 | tools\doc_layout.py (20 292), gen_manual.py (19 873), gen_operator_guide.py (14 561) | | PDF sayfa motoru (çakışma kontrolü), kullanım kılavuzu üreteçleri | yok | MISSING (kılavuz üreteçleri gereksiz; çakışma denetimli sayfa motoru unclear gereksinim) |
| b7 | tools\gen_sch.py (8 208), gen_pcb.py (7 857), project_data.py (1 336); nrf24 board\sch_data.py, pcb_data.py | | KiCad şematik/PCB üreteci | yok | MISSING, bilerek ertelendi (RULE_LEDGER: "bu turda taşınmadı"); Safety kuralı .kicad_* yazımını biletsiz yasaklıyor |
| b8 | tools\drc_summary.py (758) | | kicad-cli DRC JSON özeti | yok | MISSING (03_kicad pcb-review skill'i işi kapsıyor mu: unclear) |
| b9 | tools\pdf_pages.py (1 907) | | datasheet sayfasını PNG'ye | datasheet-lookup\pdf_crop.py | ADAPTED/işlev kapsanıyor |
| c1 | KiCAD_Projects\...\.claude\skills (bring-up-log, check-pdf, datasheet-lookup, figures, footprint-check, handoff-intake, pcb-review, schematic-review) | | | .claude\skills (9: ayrıca module-intake=handoff-intake, qspice-sim) | ADAPTED (içerik bu envanterde karşılaştırılmadı: "unclear"); datasheet-lookup betikleri T024'te değiştirildi |
| c2 | .claude\commands: brief, closeout, report, start | | | start, report, closeout | brief bilerek düştü (RULE_LEDGER) |
| c3 | CLAUDE.md figures/sim kuralları (QS METHODOLOGY_v2: .save, canary, adım etiketi...) | | | kök CLAUDE.md Figures + qspice-sim | ADAPTED (RULE_LEDGER kural 44-46) |
| c4 | datasheet-lookup tests.md / tests_reference_load.md | | 8 soru | skill klasöründe | COPIED (tests_reference_load.md çalıştırılamaz, T024) |
| d1 | programmable_electronic_load\sim\models: OPAx188.LIB, OPAx192.LIB, OPAx333.LIB (16-19 KB), irf4905.spi, irfp250n.spi, lm358.txt, lmx58_lm2904.lib | | vendor modeller (lisans/kaynak notu için FACTS.md/INDEX bakılmadı) | 01_secim\sim\models yalnız MAX6070, TLV333 (boş-benzeri klasörler, dosya sayısı bu envanterde sayılmadı) | MISSING (OPAx333 aile modeli; TLV333 değil, tam varyant kuralı: farklı parça, kullanılmaz) |
| d2 | eda\docs: ARCHITECTURE.md (7 699), backlog.md, lessons.md (7 027), METHODOLOGY_v2.pdf (açılmadı), OPERATOR_GUIDE.pdf | | arşiv | yalnız atıf (lessons "arşiv") | MISSING bilerek (arşiv) |
| d3 | KiCAD kit: tools\new_kicad_project.py (18 367), 01_PROJE_SABLONU, 02_PLANNER, 03_PROMPTLAR | | yeni proje iskeleti kurucu | pipeline iskeleti elle kuruldu | MISSING (tek seferlik, gereksiz) |

**Adım 3 - bağımlılıklar (MISSING/DIFFERENT önemli olanlar).**
- b1 circuits.py: kök CLAUDE.md Figures kural 1 (netlistten üreten + "her eleman çizildi" betiği) ve kural 2/T025 (üç ad: pin_map.py bunu çağıracak); qspice-sim SKILL adım 6; 02_simulasyon her sonuç raporu devre şekline ihtiyaç duyar. Legacy dosya yük devresine özgü `draw_*` fonksiyonlarını içerir; genel çekirdek (Netlist, Sheet, finish, footer, check_pinmap) bir 4-20 mA yeniden yazımına temel olabilir, ama elle yerleşim ve LM358/IRFP250N çizimleri taşınamaz. ROOT = parents[2], pipeline'da docs\sim\ konumunda aynı kalır; `C:\eda` sabiti yalnız plotkit.py docstring'inde.
- b2 plotkit.py: Figures "sonuç grafiği" kuralı; CSV'yi qraw_export.py çıktısından okur, uyumlu.
- a5/b6: yalnız DVR PDF istenirse (SPEC K1..K12 doğrulama raporu, INTERFACES bölüm 7) gerekir; kapsam kararı mühendise.
- d1 modeller: 02_simulasyon "eksik model işi durdurur"; 01_secim T009 çekirdek modeller kendi kaynaklarından gelir, legacy OPAx333 yerine geçmez.
- a1: README "byte-exact" ifadesi T024'ten beri yanlış (yalnız yorum farkı).

**Adım 4 - karşılaştırma.** run_sim.ps1: legacy sha256 4da69e31..., pipeline 733a93ab...; diff 3 satır (satır 21 yol yorumu, +2 satır canary yorumu), davranış farkı yok. qraw_export.py ve qraw.py: sha256 aynı. check_pdf.py (iki legacy kopya aynı, 33f6fdfb... vs pipeline 891c4e0a...): 41 satır fark; ROOT=cwd, varsayılan crop klasörleri, komut yolları, geri-link çoğaltma (T023), docstring; bilinçli uyarlama. canary_rc.cir: üç legacy kopya ve pipeline aynı.

**Adım 5 - uyarlama planı (yürütülmedi).**
1. 00_coordination: `docs\sim\circuits.py` çekirdeği (Netlist, Sheet, finish doğrulamaları, footer) legacy'den okunarak 4-20 mA'ya genel yazılır; yük'e özgü draw_* alınmaz; pin_map.py entegrasyonu; testler (fixture .cir, "her eleman çizildi" ihlal testi). Bağımlılık: PyMuPDF.
2. 00_coordination: `docs\sim\plotkit.py` + INDEX.md biçimi + `result.py` şablonu (qraw_export CSV girdisi); test: sentetik CSV.
3. 00_coordination: README "byte-exact" düzeltmesi ve kaynak yolu (docs\README, canary başlık yorumu T024 OPEN).
4. 02_simulasyon: kendi testbench'leri; legacy a6/a7'den yalnız fikir (naming_canary kanıtı, diag adımları).
5. 03_kicad (sonra): drc_summary.py işlevi pcb-review skill'inde var mı kontrol; yoksa küçük bilet. gen_sch/gen_pcb bilerek ertelendi: ayrı karar.
6. Karar bileti (mühendis): DVR PDF/doc_layout.py gerekli mi.
Yol/lisans notları: legacy betiklerde `C:\Program Files\KiCad\10.0` ve QSPICE sabit yolları (pipeline da kullanıyor); gen_sch.py KiCad sembol klasörü sabit; vendor modellerin (OPAx*.LIB, lmx58, irf*) lisans notları bu envanterde okunmadı; pipeline'a model taşınmadan önce kaynak URL + SHA kaydı gerekir.

OPEN: (1) Legacy qspice-sim skill ve C:\eda\...\.claude\skills (derinlik 5) ile pipeline karşılaştırması yapılmadı (a/c1 içerik farkları unclear). (2) result.py ve docs\sim klasör içi çıktılar incelenmedi. (3) Vendor model lisans notları ve legacy docs\ARCHITECTURE/backlog içeriği okunmadı. (4) DVR/doc_layout ve gen_sch/gen_pcb gerekliliği mühendis kararı. (5) 01_secim\sim\models içeriği sayılmadı.
