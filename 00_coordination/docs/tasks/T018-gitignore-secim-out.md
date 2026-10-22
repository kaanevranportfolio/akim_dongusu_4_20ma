# T018 - .gitignore: 01_secim out ham yanıt ve log dosyaları
Durum: BİTTİ
## İstek
Goal: make git ignore raw DigiKey responses and logs under 01_secim\out, before the next commit (00_coordination/T017 waits for this). Run from the pipeline root C:\pipelines\akim_dongusu_4_20ma. Edit only: this ticket file and <pipeline>\.gitignore. Never commit / push / amend / delete / git add.
Steps:
1. Show the current .gitignore and `git status --short -uall` (read-only). Do not open any file under 01_secim\out.
2. Append these lines to .gitignore (next to the other output/log patterns, keep line endings):
   01_secim/out/**/result*.json
   01_secim/out/**/run.log
   01_secim/out/**/*.tmp
   Do NOT ignore smoke_run.py, smoke_spec.json, *.md under 01_secim\out (fields_table.md etc.).
3. Verify with `git check-ignore -v` for 01_secim/out/passA/digikey_smoke/result.json, run.log and raw_out.tmp (each must print a rule), and `git check-ignore -v` for smoke_run.py and smoke_spec.json (must print nothing). If a pattern matches a path that is already tracked, report it (tracked files stay tracked).
4. Report the paths under 01_secim\out that are still untracked and not ignored after the change (names only).
Output: at most 6 lines.
## Sonuç
1. .gitignore'a 3 desen eklendi (LF korundu, "Secrets and caches" bloğunun altına, yorum satırıyla): `01_secim/out/**/result*.json`, `01_secim/out/**/run.log`, `01_secim/out/**/*.tmp`.
2. check-ignore: result.json → .gitignore:35, run.log → :36, raw_out.tmp → :37, result_1.json → :35 (hepsi kural yazdı). smoke_run.py ve smoke_spec.json: çıktı yok (ignore değil).
3. Bu desenlerle eşleşen izlenen (tracked) dosya yok.
4. 01_secim\out altında hâlâ izlenmeyen ve ignore edilmeyen: fields_table.md, found_parts.md (01_secim\out altındaki hiçbir dosyanın içeriği açılmadı).
5. git add / commit / push yapılmadı.
