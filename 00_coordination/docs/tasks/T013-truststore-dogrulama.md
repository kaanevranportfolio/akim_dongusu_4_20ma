# T013 - truststore doğrulaması (kimlik bilgisiz)
Durum: BİTTİ
## İstek
Goal: verify, without any credentials, that truststore fixes the TLS handshake to api.digikey.com for the same HTTP stack the DigiKey client uses (generated client may read certifi.where() directly, see 01_secim/T002 note). Use the venv C:\Users\kaane\AppData\Local\Temp\vdk (Python 3.12). Run from the pipeline root. Edit only this ticket file. Never commit / push / amend / delete.
Hard limits (root CLAUDE.md Safety): do not read .env, token, certificate files; do not run smoke_run.py or any script that loads .env; no certificate store access; no CA bundle files; no REQUESTS_CA_BUNDLE / SSL_CERT_FILE / CURL_CA_BUNDLE; no verify=False / CERT_NONE; no pip install. The only network call allowed is an unauthenticated `GET https://api.digikey.com/` (no headers, no body) in step 3. If anything else errors on network/certificates, STOP and report.
Steps:
1. Environment: confirm the three CA variables are empty in the process (print name + value for these three names only).
2. Read-only code check: in the installed `digikey` package inside the venv (site-packages\digikey), list `file:line` (at most 15 lines) of occurrences of: certifi, ssl_ca_cert, ca_certs, PoolManager, cert_reqs, verify. Report whether the client builds its own urllib3 PoolManager with ca_certs=certifi.where().
3. Offline then online test with a script written to the session scratch folder (not the repo):
   a. `import truststore; truststore.inject_into_ssl()` first, then `import urllib3, certifi, ssl`; print `ssl.SSLContext` and `urllib3.util.ssl_.SSLContext` class names (expect truststore's).
   b. Build `urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())` (the way step 2 shows the client does it; if the client does it differently, copy that way) and run `GET https://api.digikey.com/`. Success = any HTTP status (404 expected); failure = the exception class and first message line.
   c. Control: same request in a fresh process WITHOUT truststore. Expected: certificate verify error (the original failure).
   Report only: status code or exception line for b and c.
4. Conclusion in one line: truststore works / does not work for the client's stack / undetermined.
Output: table of at most 6 lines (check | result | value), then at most 3 lines of open issues. No raw dumps.
## Sonuç
| check | result | value |
|---|---|---|
| 1 CA değişkenleri (process) | üçü de boş | REQUESTS_CA_BUNDLE=[], SSL_CERT_FILE=[], CURL_CA_BUNDLE=[] |
| 2 İstemci kodu (venv digikey) | evet, kendi PoolManager'ını kuruyor | digikey\v3\batchproductdetails\rest.py:64 `cert_reqs = ssl.CERT_REQUIRED`, :73 `ca_certs = certifi.where()` (ssl_ca_cert yoksa), :98-102 `urllib3.PoolManager(cert_reqs=..., ca_certs=...)`; ordersupport\rest.py aynı kalıp. v4 productinformation için ayrı rest.py listelenmedi (aramada yalnız v3 dosyaları çıktı) [A: aynı üretici kalıp] |
| 3a truststore sonrası sınıflar | truststore'un | `ssl.SSLContext` ve `urllib3.util.ssl_.SSLContext` = truststore._api.SSLContext |
| 3b truststore ile GET https://api.digikey.com/ (PoolManager CERT_REQUIRED + ca_certs=certifi.where()) | başarılı | HTTP 404 |
| 3c kontrol: truststore'suz, taze süreç | başarısız (beklenen) | SSLError [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate |
| 4 Sonuç | truststore, istemcinin TLS yığınında çalışıyor | aynı PoolManager kalıbı: truststore ile 404 (el sıkışma tamam), truststore'suz doğrulama hatası |

Açık:
- v4 (Product Information) istemcisinin rest.py'si venv'de listelenmedi; kod kontrolü v3 paketlerine dayanıyor [A]. Gerçek v4 çağrısı kimlik bilgisi gerektirir (mühendis smoke testi).
- Test betikleri yalnız oturum scratch klasöründe (t13_ts.py, t13_ctl.py); repo ve .env'e dokunulmadı.
