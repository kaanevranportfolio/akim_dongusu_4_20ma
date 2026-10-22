# T014 - TLS düzeltmesi commit ve push
Durum: ÇALIŞIYOR
## İstek
Goal: commit and push the TLS-fix work as one commit. Run only after 00_coordination/T011 is BİTTİ. Run this session from the pipeline root C:\pipelines\akim_dongusu_4_20ma. Edit only this ticket file. Allowed git write commands: `git add` with explicit file paths, one `git commit`, `git push`. Never tag / amend / reset / checkout . / clean / force-push / delete. Never read or print .env, tokens or credential files.
Steps (STOP = wait for the engineer's reply):
1. Read-only: `git status --short -uall`, `git log --oneline -2`, `git branch --show-current`, `git remote -v`, `git config --local user.name`, `git config --local user.email`. Expect branch main, origin set, identity kaanevranportfolio / kaanevran@hotmail.com. If different, STOP.
2. Hygiene: no .env, .digikey_cache, *.pem, *.pdf, *.log, *.qraw, __pycache__, files over 1 MB may be in the add list; if any appears, STOP and report (do not edit .gitignore). Confirm with `git check-ignore -v tools/component_selector/.env` that .env is ignored.
3. Proposed add list: every modified/untracked path from step 1 as individual file paths (no directories, no wildcards). Expected: CLAUDE.md, docs\RULE_LEDGER.md, tools\component_selector\requirements.txt, README.md, search_digikey.py, search_nexar.py, 00_coordination\HANDOFF.md, 00_coordination\docs\lessons.md, ticket files T008, T010-T014. Flag anything else. Show file count and total size. STOP: wait for the engineer's "commit go".
4. After go: `git add` with the explicit paths, `git status --short`, one `git commit -m "TLS duzeltmesi: truststore, paket sabitleme, kural 49, biletler"`; report hash and `git show --stat --oneline HEAD | tail -3`.
5. STOP: wait for the separate "push go". After it: `git push`. If it fails, report the message and STOP. Then report `git log origin/main --oneline -1` (must equal HEAD) and `git status --short`.
Output: table of at most 6 lines (step | done | value), then at most 3 lines of open issues.
## Sonuç
| step | done | value |
|---|---|---|
| ön koşul | evet | T011 Durum = BİTTİ |
| 1 Salt okuma | evet | main; origin https://github.com/kaanevranportfolio/akim_dongusu_4_20ma.git; kaanevranportfolio / kaanevran@hotmail.com (beklenenle aynı); son commit 2dae4a4 |
| 2 Hijyen | UYARI | .env ignore'da (tools/component_selector/.gitignore:1). `01_secim/out/passA/digikey_smoke/run.log` listede: `*.log` kuralına takılıyor → eklenmeyecek, mühendis karar versin (404 bayt) |
| 3 Önerilen add listesi | evet, onay bekliyor | 20 yol, toplam 108333 bayt (hepsi <1 MB); .pem/.pdf/.qraw/__pycache__/.env yok |
| 4 Commit | YAPILMADI | "commit go" bekleniyor |
| 5 Push | YAPILMADI | ayrı "push go" bekleniyor |

Add listesi (tek tek yol): CLAUDE.md; docs/RULE_LEDGER.md; tools/component_selector/{requirements.txt, README.md, search_digikey.py, search_nexar.py}; 00_coordination/HANDOFF.md; 00_coordination/docs/lessons.md; 00_coordination/docs/tasks/{T008-ikinci-commit, T010-tls-tani, T011-sertifika-kurali, T012-truststore, T013-truststore-dogrulama, T014-ucuncu-commit}.md.
Beklenenin DIŞINDA (işaretli, mühendis karar versin): 01_secim/docs/tasks/T001-digikey-smoke.md, 01_secim/docs/tasks/T002-smoke-truststore.md, 01_secim/out/passA/digikey_smoke/{smoke_run.py, smoke_spec.json, result.json}; run.log hariç tutulacak.

Açık:
- 01_secim dosyaları (2 bilet + out\passA\digikey_smoke altı 3 dosya) bu commit'e girsin mi? result.json içeriği okunmadı (136 bayt, önceki bir çalıştırmadan).
- run.log: ignore edilmeli mi (.gitignore'u bu bilet düzenlemez)? Şimdilik eklenmeyecek.
- "commit go" ve ayrı "push go" gelmeden git add/commit/push yapılmadı.
