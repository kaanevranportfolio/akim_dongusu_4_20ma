# T012 - component_selector: truststore, sürüm sabitleme, README
Durum: BİTTİ
## İstek
Goal: fix the DigiKey TLS failure (00_coordination/T010; chain issuer Sectigo, browser trusts it, Python/certifi does not) the way the engineer decided: use the OS trust verification via `truststore` inside the selector scripts only, pin the verified package set, document the Windows/Python 3.12 setup. Run from the pipeline root. Edit only: this ticket file and, under <pipeline>\tools\component_selector\: requirements.txt, search_digikey.py, search_nexar.py, README.md. Everything else is read-only (01_secim\...\smoke_run.py is NOT edited here). Never commit / push / amend / delete.
Hard limits (root CLAUDE.md Safety): no reading .env, token, certificate files; no reading/exporting the certificate store; no CA bundle files; no REQUESTS_CA_BUNDLE / SSL_CERT_FILE / CURL_CA_BUNDLE; no verify=False. No DigiKey or Nexar network call in this ticket. If pip or any step hits a network or certificate error, STOP and report.
Steps:
1. Read requirements.txt, README.md, search_digikey.py, search_nexar.py (and list which other scripts import requests).
2. In search_digikey.py and search_nexar.py, before the first `import requests` (or any ssl/urllib3 use), add exactly:
   try:
       import truststore
       truststore.inject_into_ssl()
   except ImportError:
       pass
   Change nothing else in those files. Show the diff in the Sonuç.
3. Install `truststore` into the existing venv C:\Users\kaane\AppData\Local\Temp\vdk only (`pip install truststore`); report its version. Run the existing pytest suite with that venv (no network): report passed/failed (previous result: 27 passed).
4. requirements.txt: pin the verified working set from that venv's `pip freeze` for exactly these packages: requests, urllib3, certifi, pyOpenSSL, cryptography (<43), six, python-dateutil, truststore, plus `setuptools<81`. Keep all other existing lines as they are. Show the diff.
5. README.md: add a section "Windows / Python 3.12": the pinned set and why (setuptools<81; pyOpenSSL 24.2.1 with cryptography<43); create the venv outside the repo in a short path such as C:\vdk (Windows 260-character path limit); TLS: truststore makes Python use the OS certificate verification like the browser (the DigiKey server's intermediate certificate is not served completely [A]); do not build CA bundles or set CA environment variables; credentials only in .env written by the engineer, never pasted in chat or tickets. Note for 01_secim: smoke_run.py needs the same four-line truststore snippet (done by 01_secim, its own ticket).
6. Check: `python -m pytest` result and `git diff --stat` for the touched files only.
Output: table of at most 6 lines (step | done | value), then the two diffs, then at most 3 lines of open issues.
## Sonuç
| step | done | value |
|---|---|---|
| 1 Okuma | evet | `import requests` yalnız search_nexar.py:27; search_digikey.py `requests`'i doğrudan import etmiyor (digikey kütüphanesi üzerinden) |
| 2 truststore kodu | evet | search_digikey.py ve search_nexar.py, ilk import'tan önce 6 satır eklendi, başka değişiklik yok |
| 3 Kurulum + test | evet | truststore 0.10.5 vdk venv'ine kuruldu; `pytest tools\component_selector\tests`: 27 passed (ağ yok) |
| 4 requirements.txt | evet | requests, urllib3, certifi, pyOpenSSL, cryptography, six, python-dateutil, truststore sabitlendi + `setuptools<81`; diğer satırlar aynı |
| 5 README.md | evet | "Windows / Python 3.12" bölümü eklendi (+9 satır) |
| 6 git diff --stat | evet | README +9, requirements +9/-1, search_digikey +6, search_nexar +6 (4 dosya) |

Diff (search_digikey.py ve search_nexar.py, ikisi aynı ekleme; import'tan önce):
```diff
 """
 
+try:
+    import truststore
+    truststore.inject_into_ssl()
+except ImportError:
+    pass
+
 import os
```
Diff (requirements.txt):
```diff
-requests>=2.28.0
+requests==2.34.2
+urllib3==2.8.0
+certifi==2026.10.19
+pyOpenSSL==24.2.1
+cryptography==42.0.8
+six==1.17.0
+python-dateutil==3.0.0
+truststore==0.10.5
+setuptools<81
```
Açık:
- DigiKey'e gerçek çağrı yapılmadı (bilette yasak): truststore'un TLS hatasını çözdüğü henüz doğrulanmadı [A]; smoke_run.py için 01_secim biletine ihtiyaç var.
- README'de "setuptools<81" nedeni belgelenmedi, [A] olarak işaretlendi; mühendis nedeni verirse güncellenir.
- Düzenlemeler çalışma ağacında, commit edilmedi.
