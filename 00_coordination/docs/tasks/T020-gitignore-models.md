# T020 - .gitignore/.gitattributes: SPICE modelleri ve ham çıktılar
Durum: AÇIK
## İstek
Goal: set the commit policy for vendor SPICE models and keep raw DigiKey/lookup outputs out of git. Run from the pipeline root C:\pipelines\akim_dongusu_4_20ma. Edit only: this ticket file, <pipeline>\.gitignore, <pipeline>\.gitattributes. Never commit / push / amend / delete / git add.
Policy decided by the coordinator (engineer to confirm in the Sonuç review): vendor SPICE models are TRACKED in git (private repo), byte-exact, never edited, each recorded in the module's FACTS.md with source URL and SHA-256 (root CLAUDE.md Documents). Line-ending conversion would change the bytes and break the SHA-256, so model folders get `-text`. If a vendor's terms forbid redistribution, the engineer decides to ignore that single file (not part of this ticket).
Steps:
1. Read-only: show .gitattributes and .gitignore. Run `git check-ignore -v` for these sample paths (they need not exist): 01_secim/sim/models/x.lib, x.mod, x.cir, x.sub, x.zip, x.txt, 02_simulasyon/sim/models/x.lib, x.zip. Report which are ignored and by which rule.
2. .gitattributes: add `01_secim/sim/models/** -text -diff` and `02_simulasyon/sim/models/** -text -diff` (keep the file's style). If an existing rule such as `* text=auto` is present, say so in the report.
3. .gitignore: if any sample model path from step 1 is ignored by a general rule (for example *.zip or *.raw), add negation lines `!01_secim/sim/models/**` and `!02_simulasyon/sim/models/**` AFTER that rule; re-run check-ignore to prove nothing under the models folders is ignored.
4. Raw outputs: find the files named ref_*.json, ref2_*.json, op_*.json (01_secim T008-era outputs) anywhere in the repo working tree (list path, size, tracked or untracked; do NOT open them). If all are under 01_secim/out/, add `01_secim/out/**/ref_*.json`, `01_secim/out/**/ref2_*.json`, `01_secim/out/**/op_*.json` to .gitignore, first checking that no TRACKED file matches (`git ls-files` with the patterns). If any is elsewhere or tracked, do not add that pattern: report the path and a proposal.
5. Verify with `git check-ignore -v` on each found raw file (must print a rule) and `git diff --stat` for .gitignore and .gitattributes.
Output: at most 8 lines (what was added, check-ignore results, anything left untracked and unignored under 01_secim).
## Sonuç
(VS Code writes here.)
