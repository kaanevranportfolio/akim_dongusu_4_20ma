# T006 - cleanup-digikey
Durum: BİTTİ
## İstek
Goal: clean up the 01_secim side after the closed DigiKey incident (00_coordination/T015, T016). Work only inside 01_secim. Never delete files (list what the engineer should delete), never commit / push / amend. Do NOT read .env, tokens, .digikey_cache or certificates, do NOT send any network request, do NOT run any script. Add no certificate-related setting anywhere.
Run only after 01_secim/T005 is BİTTİ (both tickets touch the digikey_smoke scripts; never run them at the same time).
May edit: this ticket file; 01_secim\FACTS.md, 01_secim\HANDOFF.md, 01_secim\docs\DEVLOG.md (append-only: correct old text with a new dated entry that refers to it), 01_secim\docs\lessons.md, and the scripts smoke_run.py / smoke_spec.json in 01_secim\out\passA\digikey_smoke\ (wrong or outdated statements only). Everything else is read-only; tools\, pipeline root files and .gitignore are not ours.
Steps:
1. Inventory of every file under 01_secim\out\ (incl. out\passA\digikey_smoke\): table name | size | what it is | status (keep / should be gitignored / engineer deletes). Use names, sizes and first heading/line only; do not open contents. Candidates: raw_out.tmp, run.log, old result.json, result_<n>.json, old smoke versions, T003-related files.
2. Search md/py/json under 01_secim (grep) for leftovers of the old approach: certifi, REQUESTS_CA_BUNDLE, SSL_CERT_FILE, CURL_CA_BUNDLE, ca_bundle, "TLS inspection", `import digikey` / `digikey.v3|v4` library use, DIGIKEY_STORAGE_PATH, .digikey_cache. Per hit: file:line and a recommendation (update / delete / leave). Fix wrong or outdated statements in our own md files and smoke scripts.
3. Make FACTS.md, HANDOFF.md, docs\DEVLOG.md and docs\lessons.md consistent with these points: (a) DigiKey access goes through digikey_v4.keyword_search; token 200 and keyword search 200 [M]. (b) The cause of the 401 "Invalid clientId" is NOT proven: Sandbox credentials on the production host [A] and/or the old V3 library path [A] (00_coordination finding); never write it as "the" cause. Check specifically lessons.md (the Sandbox line is labelled [M] for a cause and must be relabelled [A]) and DEVLOG items 3 and 4. (c) Products=[] on the first query is attributed to a too-specific query [A], open until the T005 result. (d) Distributor data is [W] and a shortlist, not a candidate list; the datasheet decides. Do not fill the FACTS.md requirements table; the planner does that.
4. Collect every request for 00_coordination in one place at the end of Sonuç, at most three lines: which 01_secim\out files should be gitignored (e.g. result.json, result_*.json, run.log, *.tmp), and anything that must be fixed at pipeline level.
Result: at most 8 table lines + the list of files the engineer should delete + the list of requests for 00_coordination. Set Durum to ÇALIŞIYOR on start and BİTTİ at the end.
## Sonuç
Çalıştırma/ağ/okuma yok: out\ içerikleri açılmadı (yalnız ad, boyut, md başlık satırı); .env/token/cache/sertifikaya dokunulmadı; hiçbir şey silinmedi. T005 BİTTİ olduktan sonra yapıldı.

Adım 1, envanter (01_secim\out\passA\digikey_smoke\):
| Ad | Boyut (bayt) | Ne | Durum |
|---|---|---|---|
| smoke_run.py | 4693 | dört sorgu V4 smoke betiği | keep |
| smoke_spec.json | 340 | dört kısa sorgu, limit 10 | keep |
| fields_table.md | 4252 | alan tablosu [W] (T005 çıktısı) | keep |
| found_parts.md | 7913 | sorgu başına parça listesi [W], "not candidates" başlığı | keep |
| result_1..4.json | 67120 / 70630 / 111760 / 114598 | ham yanıt gövdeleri [W] | should be gitignored |
| result.json | 141 | eski tek sorgu, boş yanıt (T004 koşusu) | engineer deletes (+ gitignore) |
| run.log | 404 | T001 dönemi redakte log | engineer deletes (+ gitignore; mevcut `**/sim/out/*.log` kuralı kapsamaz) |
| raw_out.tmp | yok | mühendis silmiş görünüyor | - |

Adım 2, grep (md/py/json, 01_secim):
- smoke_run.py: certifi/CA/`import digikey` kalıntısı YOK (satır 12 `import digikey_v4`; satır 66 yorumu "no certificate handling" doğru) -> leave.
- .claude\settings.json:12 `Read(**/.digikey_cache/**)` deny kuralı -> leave (koruma).
- docs\DEVLOG.md:8-12, docs\lessons.md:3-4: sertifika olayı anlatımı, doğru ve olay kaydı -> leave; yanlış etiketli satırlar düzeltildi (aşağıda).
- docs\tasks\T001-T005: eski yaklaşım (ca_bundle, REQUESTS_CA_BUNDLE, certifi, digikey.v4, TLS denetimi tahmini, "kütüphane v3") tarihsel bilet metni; bu bilet onları düzenleme yetkisi vermiyor -> leave; güncel gerçek DEVLOG 2026-10-22 düzeltme girdisinde.
Hiçbir script düzeltmesi gerekmedi.

Adım 3, tutarlılık:
| Madde | Yapılan |
|---|---|
| (a) erişim yolu, token 200 / keyword 200 [M] | FACTS.md yeni "Araçlar ve veri kaynağı (DigiKey)" bölümü; HANDOFF Durum; DEVLOG düzeltme girdisi |
| (b) 401 nedeni kanıtlanmadı [A] | lessons.md "Sandbox ... [M]" satırı yeniden yazıldı (olay [M], neden [A], "tek neden" değil); aynı dosyada .env doğrulama satırındaki "neden Sandbox/Production uyumsuzluğuydu" kaldırıldı; DEVLOG yeni girdi madde 3/4/5'e atıfla düzeltir (eski metin değişmedi); FACTS satırı [A] |
| (c) Products=[] nedeni [A], T005 sonucuna kadar açık | lessons.md satırı [M]/[A] ayrıldı; FACTS, HANDOFF madde 2 |
| (d) distribütör verisi [W], kısa liste | lessons.md yeni satır; FACTS satırı; HANDOFF |
FACTS.md gereksinim tablosu doldurulmadı. HANDOFF.md ayrıca güncellendi (eski "seçici henüz tools altında değil" maddesi kaldırıldı).

Mühendisin silmesi gerekenler: 01_secim\out\passA\digikey_smoke\run.log; 01_secim\out\passA\digikey_smoke\result.json. Repo dışı (durumları doğrulanmadı): Temp\vdk\ca_bundle.pem; scratchpad'deki eski venv_digikey.

00_coordination'a istekler (adım 4):
1. .gitignore: 01_secim/out/passA/digikey_smoke/result*.json, run.log ve *.tmp (ham yanıtlar ve loglar commit'e girmesin; şu an hiçbiri ignore'da değil).
2. tools\component_selector\README.md: Windows/Python 3.12 venv notları (kısa yol, truststore), CA ortam değişkeni yok.
3. Pipeline düzeyi: T001-T005 bilet metinlerindeki eski TLS/V3 anlatımı tarihsel; düzeltme gerekiyorsa koordinatör karar versin.
