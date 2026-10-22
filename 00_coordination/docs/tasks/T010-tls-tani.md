# T010 - TLS hatası tanısı (salt okuma)
Durum: BİTTİ (kısmi: adım 3-4 çalıştırılamadı)
## İstek
Goal: find out why the DigiKey OAuth request failed with CERTIFICATE_VERIFY_FAILED in 01_secim/T001 (venv C:\Users\kaane\AppData\Local\Temp\vdk, Python 3.12) while the original C:\component_selector_v1 reached DigiKey from the command line (Python 3.10). Diagnosis only: environment difference or TLS inspection on the network. Run from the pipeline root. Edit only this ticket file. Never commit / push / amend / delete.
Hard limits (engineer rule): do NOT read, list, export or write the Windows certificate store; do NOT create or edit CA bundle files; do NOT set REQUESTS_CA_BUNDLE / SSL_CERT_FILE / CURL_CA_BUNDLE (process, user or machine level); do NOT disable TLS verification (verify=False, -k, CERT_NONE); do NOT pip install/uninstall anything; do NOT read .env, token or certificate file contents. If a network or certificate error blocks a step, STOP and report it.
Steps:
1. Interpreters: `py -0p` and `python --version` (names and paths only). Find which interpreter the original C:\component_selector_v1 was run with (check tests\ __pycache__ file names, e.g. cpython-310; no file contents). Report.
2. Package versions: `pip freeze` of (a) the venv at C:\Users\kaane\AppData\Local\Temp\vdk and (b) the original interpreter from step 1 if it exists. Show only requests, urllib3, certifi, pyOpenSSL, cryptography, truststore, pip-system-certs, setuptools, six, python-dateutil and their versions in a side-by-side table.
3. Reproduce without any CA override: first confirm the three variables are NOT set in the process (`echo` only their names/values, nothing else from the environment). Then run the existing smoke token request (01_secim\out\passA\digikey_smoke\smoke_run.py or the selector's own token call, whichever 01_secim/T001 used) once with the venv (3.12) and once with the original interpreter (3.10) if available, without any bundle variable. Report only: success / the exception class and message line, per interpreter. Do not retry in other ways.
4. Report the issuer common name of the certificate chain presented by api.digikey.com only if it can be obtained without disabling verification and without touching the certificate store (e.g. from the exception text); otherwise write "not determined".
5. Persistence: check whether REQUESTS_CA_BUNDLE, SSL_CERT_FILE, CURL_CA_BUNDLE exist at User or Machine level: `[Environment]::GetEnvironmentVariable('<NAME>','User')` and `'Machine'` for exactly these three names, print name + value only. Also report existence, size and modified time (metadata only, no content) of C:\Users\kaane\AppData\Local\Temp\vdk\ca_bundle.pem. Deleting anything is the engineer's job: only report.
6. Conclusion in one line: environment difference / network TLS inspection / undetermined, with the evidence.
Output: one table (check | result | value) of at most 8 lines, then at most 4 lines of open issues. No raw dumps.
## Sonuç
| check | result | value |
|---|---|---|
| 1 Interpreters | `py -0p`: yalnız 3.12; 3.10 kurulu değil | 3.12.10 (Python312); orijinal proje __pycache__ = cpython-310 → 3.10 ile çalıştırılmış, o yorumlayıcı bu makinede yok |
| 2 Paketler (venv vdk 3.12 / sistem 3.12 / 3.10) | 3.10 yok → karşılaştırma yapılamadı | venv: requests 2.34.2, urllib3 2.8.0, certifi 2026.10.19, pyOpenSSL 24.2.1, cryptography 42.0.8, setuptools 80.10.2, six 1.17.0, python-dateutil 3.0.0; truststore, pip-system-certs yok. Sistem 3.12: yalnız six 1.17.0, python-dateutil 2.9.0.post0 |
| 3 Üç değişken process'te | ayarlı DEĞİL | REQUESTS_CA_BUNDLE, SSL_CERT_FILE, CURL_CA_BUNDLE = boş |
| 3 Smoke token isteği (3.12 / 3.10) | ÇALIŞTIRILMADI | otomatik izin sınıflandırıcısı komutu reddetti ([Credential Exploration]: smoke_run.py selector'ün .env'ini yükler); dolanılmadı |
| 4 api.digikey.com issuer CN | not determined | adım 3 çalışmadığı için exception metni yok |
| 5 Kalıcılık User/Machine | üç değişken de User ve Machine düzeyinde boş | — |
| 5 vdk\ca_bundle.pem | VAR (yalnız metadata) | 325642 bayt, değişiklik 2026-10-22 17:46:08; silmek mühendisin işi |
| 6 Sonuç | undetermined | Ortam farkı kanıtlı: orijinal 3.10 yorumlayıcı yok, venv 3.12 paketleri farklı; TLS inspection için kanıt yok (istek çalışmadı). smoke_run.py başlığındaki "TLS inspection on this PC" notu [U]/[A] düzeyinde, bu bilette doğrulanmadı |

Açık:
- Adım 3-4 için mühendisin açık izni gerekir (smoke_run.py `.env` yükler; sınıflandırıcı reddetti). İzin gelirse tek seferlik, result.json'a yazmadan koşulacak.
- 3.10 yorumlayıcı yok: orijinalin hangi sertifika yığınıyla (ör. 3.10 + eski certifi/pip-system-certs) çalıştığı bu makinede karşılaştırılamıyor.
- Bu bilet dışında dosya değiştirilmedi.
