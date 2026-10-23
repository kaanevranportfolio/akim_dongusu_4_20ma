# T017 - DigiKey V4 istemcisi ve temizlik commit/push
Durum: BİTTİ
## İstek
Goal: commit and push the DigiKey V4 work (00_coordination/T015, T016) and the pending ticket/result files as ONE commit. Run from the pipeline root C:\pipelines\akim_dongusu_4_20ma. Edit only this ticket file. Allowed git write commands: `git add` with explicit file paths, one `git commit`, `git push`. Never tag / amend / reset / checkout . / clean / force-push / delete. Never read or print .env, tokens or credential files.
Steps (STOP = wait for the engineer's reply):
1. Read-only: `git status --short -uall`, `git log --oneline -2`, `git branch --show-current`, `git remote -v`, `git config --local user.name`, `git config --local user.email`. Expect branch main, origin set, identity kaanevranportfolio / kaanevran@hotmail.com, HEAD 8243d58 (or later). If different, STOP.
2. Hygiene: list any .env, .digikey_cache, *.pem, *.pdf, *.log, *.tmp, *.qraw, __pycache__, result.json, files over 1 MB among the changed/untracked paths. These must NOT be added; list them as excluded. Confirm `git check-ignore -v tools/component_selector/.env`. Do not edit .gitignore.
3. Proposed add list: every other modified/untracked path as individual file paths (no directories, no wildcards), grouped by module (tools\component_selector, 00_coordination, 01_secim, root docs), with file count and total size. Expected: tools\component_selector\digikey_v4.py, search_digikey.py, README.md, tests\test_digikey_v4.py, tests\test_derating.py, tests\fixtures\digikey_v4_keyword_response.json; 00_coordination\HANDOFF.md, docs\DECISIONS.md, docs\tasks\T014..T017; 01_secim tickets and md files and smoke_run.py if changed. Flag anything unexpected. STOP: wait for the engineer's "commit go".
4. After go: `git add` with the explicit paths, `git status --short`, one `git commit -m "DigiKey V4 istemcisi, selector README, biletler"`; report hash and `git show --stat --oneline HEAD | tail -3`.
5. STOP: wait for the separate "push go". After it: `git push`. If it fails, report the message and STOP. Then report `git log origin/main --oneline -1` (must equal HEAD) and `git status --short`.
Output: table of at most 6 lines (step | done | value), then at most 3 lines of open issues.
## Sonuç
| step | done | value |
|---|---|---|
| 1 Salt okuma | evet | main; origin https://github.com/kaanevranportfolio/akim_dongusu_4_20ma.git; kaanevranportfolio / kaanevran@hotmail.com; HEAD 8243d58 (beklenen) |
| 2 Hijyen (yenilendi, T018 sonrası) | temiz | `.env` ignore'da. Değişen/izlenmeyen yollar arasında .env, .digikey_cache, *.pem, *.pdf, *.log, *.tmp, *.qraw, __pycache__, result*.json, 1 MB üstü dosya YOK. result_1..4.json artık ignore'da (.gitignore:35), listede görünmüyor |
| 3 Önerilen add listesi | evet, onay bekliyor | 25 yol, 128495 bayt (aşağıda) |
| 4 Commit | evet (commit go alındı) | 3d311fa, 25 dosya, 1058 ekleme / 130 silme; commit sonrası `git status --short` temiz. Bu satır commit'ten sonra yazıldı (bilet çalışma ağacında değişik görünür) |
| 5 Push | evet (push go alındı) | 8243d58..3d311fa main -> main; `git log origin/main --oneline -1` = 3d311fa = HEAD. `git status --short`: yalnız M T017 (bu bilet, commit sonrası yazılan satırlar) |

Add listesi (tek tek yol):
- tools/component_selector (6 dosya, 49004 bayt): digikey_v4.py, search_digikey.py, README.md, tests/test_digikey_v4.py, tests/test_derating.py, tests/fixtures/digikey_v4_keyword_response.json
- 00_coordination (6 dosya): HANDOFF.md, docs/tasks/T014-ucuncu-commit.md, T015-digikey-v4.md, T016-selector-readme.md, T017-dorduncu-commit.md, T018-gitignore-secim-out.md
- 01_secim (12 dosya): FACTS.md, HANDOFF.md, docs/DEVLOG.md, docs/lessons.md, docs/tasks/T003-digikey-api-version-check.md, T004-smoke-v4-client.md, T005-smoke-queries.md, T006-cleanup-digikey.md, out/passA/digikey_smoke/smoke_run.py, smoke_spec.json, fields_table.md, found_parts.md
- root (1 dosya): .gitignore (T018 değişikliği, 927 bayt)
- root docs: başka değişiklik yok. (Not: 00_coordination/docs/DECISIONS.md değişmemiş, listede yok.)

Beklenmeyen / işaretli:
- 00_coordination/docs/tasks/T018-gitignore-secim-out.md (yeni bilet, beklenen listede yok; T017'den sonra açılmış).
- 01_secim/docs/tasks/T003-T006 ve fields_table.md, found_parts.md: "01_secim tickets and md files" kapsamında sayıldı. found_parts.md / fields_table.md gerçek DigiKey verisinden türemiş görünüyor (içerik okunmadı).
- smoke_spec.json değişmiş (340 bayt, içerik gözden geçirilmedi).

Açık:
- (çözüldü) result_1..4.json T018 ile ignore edildi, eklenmeyecek; fields_table.md, found_parts.md, smoke_spec.json ve T018 bileti listeye dahil (mühendis kararı).
- "commit go" ve ayrı "push go" gelmeden git add/commit/push yapılmadı.
