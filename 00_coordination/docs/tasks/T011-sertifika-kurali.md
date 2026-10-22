# T011 - sertifika/TLS güvenlik kuralı
Durum: BİTTİ
## İstek
Goal: add the certificate/TLS safety rule (incident 01_secim/T001, 2026-10-22) to the pipeline method. Run from the pipeline root C:\pipelines\akim_dongusu_4_20ma. Edit only: this ticket file, <pipeline>\CLAUDE.md (Safety section), <pipeline>\docs\RULE_LEDGER.md. Do NOT edit .claude\settings.json (step 3 is proposal only). Never commit / push / amend / delete.
Steps:
1. CLAUDE.md, section "## Safety": append this bullet after the ".env" bullet, exactly:
   `- Network, TLS or certificate errors (e.g. CERTIFICATE_VERIFY_FAILED): stop and ask the engineer. Never read, list or export the OS certificate store, never build or edit CA bundle files, never set REQUESTS_CA_BUNDLE / SSL_CERT_FILE / CURL_CA_BUNDLE (process, user or machine level), never disable TLS verification (verify=False, -k, CERT_NONE). A fix that changes how the machine trusts certificates is the engineer's decision.`
2. docs\RULE_LEDGER.md: add row 49 in the same table style (columns: # | Kural | Kaynak | Olay | Yeni yer | Not): `| 49 | Ağ/TLS/sertifika hatasında dur ve mühendise sor; sertifika deposu okunmaz/dışa aktarılmaz, CA paketi üretilmez, REQUESTS_CA_BUNDLE/SSL_CERT_FILE/CURL_CA_BUNDLE ayarlanmaz, TLS doğrulaması kapatılmaz | YENİ | 2026-10-22 01_secim/T001: DigiKey OAuth CERTIFICATE_VERIFY_FAILED; ajan pip-system-certs denedi (truststore çakışması), Windows ROOT/CA deposundan 53 kök sertifikayı dışa aktarıp certifi ile birleştirdi (bilet dışı); doğrulama kapatılmadı | CLAUDE.md Safety | Neden (ortam farkı mı, ağda TLS denetimi mi) kanıtlanmadı [A]; tanı 00_coordination/T010. vscode-ticket skill'ine aynı cümle (claude.ai tarafı) |`. Also update the header line of the ledger only if it states a row count.
3. Proposal only (do not apply): read .claude\settings.json and show, as a diff in the Sonuç (at most 15 lines), deny entries in the file's existing style that block the strings: Export-Certificate, certutil, `Cert:\` store paths, REQUESTS_CA_BUNDLE, SSL_CERT_FILE, CURL_CA_BUNDLE, `verify=False`, `--insecure`. Note that deny patterns match strings, not intent. The engineer decides and applies.
4. Check: `git diff --stat` for the two edited files (show it), and `grep -n "CERTIFICATE_VERIFY_FAILED" CLAUDE.md docs\RULE_LEDGER.md` shows both.
Output: at most 6 lines plus the step 3 diff.
## Sonuç
1. CLAUDE.md Safety: sertifika/TLS maddesi ".env" maddesinin hemen altına eklendi (CLAUDE.md:111), metin bilette verildiği gibi.
2. docs\RULE_LEDGER.md: satır 49 eklendi (tablonun sonu, satır 48'den sonra). Başlıkta satır sayısı yazmıyor, değiştirilmedi.
3. Öneri (UYGULANMADI, settings.json'a dokunulmadı): aşağıdaki diff.
4. `git diff --stat`: CLAUDE.md 1 +, docs/RULE_LEDGER.md 1 + (2 dosya, 2 ekleme). `CERTIFICATE_VERIFY_FAILED` grep: CLAUDE.md:111 ve RULE_LEDGER.md:56, ikisinde de var.

Öneri diff (.claude\settings.json, "deny" listesine; PowerShell biçimi gösterildi, Bash( ) için aynı 8 satırın `Bash(` karşılığı da eklenmeli; dosyadaki mevcut çift-kabuk stiline uygun):
```diff
       "PowerShell(git commit --amend*)"
+      "PowerShell(*Export-Certificate*)",
+      "PowerShell(*certutil*)",
+      "PowerShell(*Cert:\\*)",
+      "PowerShell(*REQUESTS_CA_BUNDLE*)",
+      "PowerShell(*SSL_CERT_FILE*)",
+      "PowerShell(*CURL_CA_BUNDLE*)",
+      "PowerShell(*verify=False*)",
+      "PowerShell(*--insecure*)",
```
(Önceki satırın sonuna virgül gerekir.) Deny kalıpları dizgeyi eşler, niyeti değil: `python -c`, betik dosyası içi veya dolaylı yoldan (ör. `$env:` yerine `[Environment]::SetEnvironmentVariable` ile birleştirilmiş ad) aşılabilir; `-k` (curl) kısa bayrağı kalıba alınmadı, çünkü çok geniş eşleşir. Karar ve uygulama mühendisin.
