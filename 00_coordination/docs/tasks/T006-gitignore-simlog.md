# T006 - .gitignore: sim/out log dosyaları
Durum: BİTTİ
## İstek
Goal: make git ignore simulation log files under any sim\out folder, before the first commit (00_coordination/T005 is waiting at its step 2). Run from the pipeline root C:\pipelines\akim_dongusu_4_20ma. Edit only: this ticket file and <pipeline>\.gitignore. Everything else is read-only. Never commit / push / amend / delete / git add. Do not run `git commit` or `git add`.
Steps:
1. Show the current .gitignore (it is small) and `git status --short` (read-only).
2. Append one line to .gitignore, in the section that lists log/simulation outputs (or at the end if none): `**/sim/out/*.log`. Add nothing else; keep line endings as in the file.
3. Verify: `git check-ignore -v 02_simulasyon/sim/out/canary_rc.log` must print the new rule.
4. Report, names only, every file under any sim\out and sim\scratch folder that is still NOT ignored (git status --short -uall for those paths). Do not edit .gitignore for them; the engineer decides.
Output: at most 5 lines: the added line, check-ignore result, the list from step 4.
## Sonuç
Eklenen satır: `**/sim/out/*.log` (.gitignore satır 15, "Python / simulation byproducts" bölümünde, `**/sim/out/*.raw` altında; dosya LF, korundu).
check-ignore: `.gitignore:15:**/sim/out/*.log	02_simulasyon/sim/out/canary_rc.log`
Hâlâ ignore edilmeyen (sim\out ve sim\scratch): 02_simulasyon/sim/out/canary_rc.meas.txt, 02_simulasyon/sim/scratch/FACTS.md
Not: sim\scratch\FACTS.md, T001'de yük projesinden kopyalanan geçici FACTS.md; commit'e girsin mi karar mühendisin.
