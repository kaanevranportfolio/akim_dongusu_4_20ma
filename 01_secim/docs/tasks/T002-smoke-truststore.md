# T002 - smoke-truststore
Durum: BİTTİ
## İstek
Goal: make 01_secim\out\passA\digikey_smoke\smoke_run.py verify TLS through the OS trust store (truststore), with no certificate file, CA bundle or CA environment variable. Edit only; do NOT run anything against the network.
Run only after 00_coordination/T012 is BİTTİ.
May edit: this ticket file; 01_secim\out\passA\digikey_smoke\smoke_run.py. Everything else is read-only. Never commit / push / amend / delete.
Steps:
1. At the very top of smoke_run.py, before `import requests` (or the first import that uses ssl/urllib3), insert exactly these four lines, no other change to the file:
       try:
           import truststore
           truststore.inject_into_ssl()
       except ImportError:
           pass
2. Show the diff (git diff or equivalent, read-only) in Sonuç.
3. Do NOT run smoke_run.py, do NOT send any request to DigiKey, do NOT read .env, tokens, .digikey_cache or certificates, do NOT touch the certificate store or set REQUESTS_CA_BUNDLE / SSL_CERT_FILE / CURL_CA_BUNDLE. On any network, TLS or certificate error: stop and ask the engineer.
4. Put this short checklist for the engineer in Sonuç (the engineer runs the test in their own terminal, with the venv C:\Users\kaane\AppData\Local\Temp\vdk and no CA environment variable set):
   (1) in the venv: `pip show truststore` -> version;
   (2) REQUESTS_CA_BUNDLE, SSL_CERT_FILE, CURL_CA_BUNDLE are empty;
   (3) .env has the key and secret of the new DigiKey application (Product Information v4); never paste them into chat or tickets.
Result: diff + at most 5 lines.
## Sonuç
Ön koşul: 00_coordination/T012 Durum = BİTTİ (kontrol edildi). smoke_run.py çalıştırılmadı, ağ isteği yok.

Diff (01_secim/out/ git'te izlenmiyor, `git diff` boş; eklenen satırlar elle gösterildi; docstring'den sonra, ilk import'tan önce):
```diff
 """DigiKey connectivity/field smoke test. ... Reads no secrets."""
+try:
+    import truststore
+    truststore.inject_into_ssl()
+except ImportError:
+    pass
 import json, os, sys
```
Mühendis kontrol listesi (kendi terminalinde, venv C:\Users\kaane\AppData\Local\Temp\vdk):
1. `pip show truststore` -> sürüm (beklenen 0.10.5);
2. REQUESTS_CA_BUNDLE, SSL_CERT_FILE, CURL_CA_BUNDLE boş;
3. `.env` yeni DigiKey uygulamasının (Product Information v4) key ve secret'ını içeriyor; sohbete/bilete yapıştırılmaz.

Not: dosyadaki `REQUESTS_CA_BUNDLE` → `certifi.where` satırları bilet gereği değiştirilmedi; değişken boşsa etkisizdir.
