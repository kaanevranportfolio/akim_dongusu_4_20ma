# T022 - kural: bilet md'sini sohbete koyma
Durum: BİTTİ
## İstek
Goal: add the rule "planner chats never echo ticket files into the conversation" to the pipeline method (incident 01_secim, 2026-10-23: ticket md files were written with Write under /mnt/user-data/outputs/, which printed the full ticket text and a file card into the chat). Run from the pipeline root C:\pipelines\akim_dongusu_4_20ma. Edit only: this ticket file, <pipeline>\CLAUDE.md (section "## Session"), <pipeline>\docs\RULE_LEDGER.md. Do NOT edit .claude\ or the claude.ai skill (the engineer saves the skill and the project instruction line). Never commit / push / amend / delete.
Steps:
1. CLAUDE.md, section "## Session": append this bullet at the end of the section, exactly:
   `- Planner chats never paste a ticket file (docs\tasks\Tnnn-*.md) into the conversation and never write it with Write under /mnt/user-data/outputs/ (that echoes the full text and a file card). The ticket is written in the scratchpad, copied into the module's docs\tasks with device_commit_files, and the chat gets only the file name, a 2-3 line summary and the one-line command.`
2. docs\RULE_LEDGER.md: add row 50 in the same table style (columns: # | Kural | Kaynak | Olay | Yeni yer | Not): `| 50 | Planner bileti sohbete koymaz ve outputs altına Write ile yazmaz; scratchpad'de yazar, device_commit_files ile modülün docs\tasks klasörüne aktarır; sohbette yalnız dosya adı, 2-3 satır özet ve tek satır komut | YENİ | 2026-10-23 01_secim: bilet md'leri Write ile outputs altına yazıldı, sohbete tam metin ve dosya kartı düştü (şişme) | CLAUDE.md Session | vscode-ticket skill'i ve proje instructions satırı claude.ai tarafında (mühendis kaydeder) |`.
3. Check: `git diff --stat` for the two files and `grep -n "never paste a ticket" CLAUDE.md`.
Output: at most 4 lines.
## Sonuç
- CLAUDE.md "## Session" sonuna kural satırı eklendi (satır 103); docs\RULE_LEDGER.md'ye satır 50 eklendi.
- `git diff --stat`: CLAUDE.md 1 ekleme, docs/RULE_LEDGER.md 1 ekleme (iki dosya da başka değişiklik içermiyordu).
- `grep -n "never paste a ticket" CLAUDE.md` -> satır 103 eşleşti.
- Commit/push/amend/silme yapılmadı; .claude\ ve claude.ai skill'ine dokunulmadı.
