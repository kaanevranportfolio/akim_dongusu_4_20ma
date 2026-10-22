# T001 - digikey-smoke
Durum: BİTTİ
## İstek
Goal: check that the DigiKey component selector works end to end. This is a connectivity and field test only, NOT a candidate search (no MPN is chosen or recorded as a candidate).
Inputs (read-only): tools\component_selector\README.md, search_digikey.py, schemas\component_specs_schema.json, tools\component_selector\tests.
May edit: this ticket file; new files under 01_secim\out\passA\digikey_smoke\ ; at the end (/closeout) 01_secim\HANDOFF.md and 01_secim\docs\DEVLOG.md. Everything else is read-only. Never commit / push / amend / delete. Never read .env, tokens, .digikey_cache or certificates.
Steps:
1. Run the offline tests: `python -m pytest tools\component_selector\tests -q` (set PYTHONIOENCODING=utf-8). Report pass/fail count. If a package is missing, stop and list it; do not install without the engineer's OK.
2. Check which DigiKey variables are set, by name only (DIGIKEY_CLIENT_ID, DIGIKEY_CLIENT_SECRET present yes/no; never print values). If missing, stop and report; the engineer sets them by hand.
3. Run ONE keyword search through search_digikey.py (search_component or the module's own entry point; read the code to choose). Query: "loop-powered 4-20 mA transmitter IC" (generic words, no MPN). Use a throwaway spec file in 01_secim\out\passA\digikey_smoke\ , not in out\passB. The first call may open the browser for OAuth: the engineer approves it. Save the raw candidate list as digikey_smoke\result.json and the run log there.
4. From result.json report which fields come back per candidate (MPN, manufacturer, package, datasheet URL, stock, price, lifecycle status, any model/ECAD link) as a table, field vs present/empty, plus the number of candidates returned.
5. On any auth, network or API error: stop, copy the error text (no secrets) into Sonuç, do not retry more than once.
Result format: at most 8 lines of conclusion + the field table. Label all data [W]. Do not list returned parts as candidates; a part number is a candidate only after it is seen in its own datasheet.
## Sonuç
Güncelleme: mühendis OK verdi, venv kuruldu: C:\Users\kaane\AppData\Local\Temp\vdk (repo dışı; scratchpad yolu Windows 260 karakter sınırına takıldı). requirements.txt + setuptools<81 (digikey-api `distutils` ister, Python 3.12'de yok) + six, python-dateutil, urllib3, certifi (digikey-api'nin bildirmediği bağımlılıklar) + digikey-api (git).
Adım 1: PASS, 27 passed, 0 failed. Adım 2: DIGIKEY_CLIENT_ID: yok, DIGIKEY_CLIENT_SECRET: yok (oturum ortamında). DURDU; adım 3-5 yapılmadı. Mühendis değişkenleri bu oturumun ortamına elle koymalı (değerler yazdırılmadı/okunmadı).

Adım 2 mühendis talimatıyla atlandı (.env tools\component_selector içinde; dosya okunmadı, `search_digikey.py` kendisi yüklüyor).
Adım 3: search_component() yalnız pasif tipleri destekliyor (inductor, cap, diode, resistor; IC tipi yok). Bu yüzden out\passA\digikey_smoke\smoke_run.py aynı modülün KeywordRequest + _normalise_product kodunu kullanıp tek anahtar kelime araması yapıyor (smoke_spec.json: "loop-powered 4-20 mA transmitter IC"). Dosyalar: smoke_run.py, smoke_spec.json, run.log (redakte; raw_out.tmp aynı içerik, silme yasak olduğundan kaldı).
Koşu 1: yerel hata, OAuth'a girmeden: certauth, pyOpenSSL 26.4'te `X509.add_extensions` yok -> venv'de pyOpenSSL 24.2.1 + cryptography<43'e indirildi (repo kodu değişmedi).
Koşu 2 (tek deneme): tarayıcı onayı alındı (auth code geldi), ancak token değişimi HATA, DURDU: `requests.exceptions.SSLError ... api.digikey.com:443 /v1/oauth2/token: CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate`. Yani DigiKey'e bağlantı kuruluyor ama bu Python'un sertifika zinciri (certifi) sunucu sertifikasını doğrulayamıyor; olası neden: ağdaki TLS denetimi (antivirüs/güvenlik duvarı) kök sertifikası Windows deposunda var ama certifi'de yok. Doğrulamayı kapatmadım; yeniden denemedim (kural: en fazla bir tekrar, ilk hata yerel bağımlılıktı).
result.json üretilmedi; adım 4 (alan tablosu) yapılamadı, aday sayısı yok.
Öneri (mühendis kararı): venv'e `pip-system-certs` (Windows sertifika deposunu kullanır) kurmak, ya da şirket/AV kök sertifikasını bildirmek. Sonra adım 3 yeniden (OAuth tarayıcı onayı bir kez daha gerekir; token önbelleği oluşmadı).

--- Seçenek 1 sonrası (nihai) ---
`pip-system-certs` denendi: DigiKey'in yerel OAuth geri çağrı sunucusuyla (server_side wrap_socket) çakıştı (truststore AttributeError), ağa çıkmadan düştü; kaldırıldı. Yerine Windows ROOT/CA deposundan 53 kök sertifika + certifi birleştirilerek C:\Users\kaane\AppData\Local\Temp\vdk\ca_bundle.pem üretildi (REQUESTS_CA_BUNDLE/SSL_CERT_FILE ile verildi; smoke_run.py yalnız certifi.where() yönlendirmesi ekledi; doğrulama KAPATILMADI).
Sonuç: OAuth token değişimi OK (tarayıcı onayı alındı), keyword_search çağrısı HTTP 200, "Requests remaining 999/1000" [W]. Aday sayısı: 0 (query "loop-powered 4-20 mA transmitter IC"). result.json yazıldı (count 0).
Alan tablosu (adım 4): doldurulamadı, çünkü dönen ürün yok; alan var/yok sonucu üretilemez. Bu yüzden "alanlar sağlam" denemez.
Yorum: bağlantı/yetkilendirme/Windows TLS sorunu çözüldü; 0 sonuç büyük olasılıkla fazla spesifik/tireli anahtar kelimeden (DigiKey keyword araması terimleri birlikte arar); `products` yanıt alanı adı da doğrulanmadı (products_count null) ama modül pasifler için aynı alanı kullanıyor. Ticket tek arama izin verdiği için ikinci sorgu çalıştırılmadı.
Sonraki adım (mühendis kararı): daha kısa jenerik sorgu, örn. "4-20 mA loop transmitter" ya da "current loop transmitter", tek arama daha; token artık önbellekte (.digikey_cache, gitignore'da), tarayıcı onayı gerekmez.
Ortam notu: venv tuzağı ve sertifika bilgisi tools\component_selector\README.md'ye yazılmalı (00_coordination bileti; bu bilet o dosyayı düzenlemiyor): Python 3.12 için setuptools<81, six/dateutil/urllib3/certifi, pyOpenSSL 24.2.1 + cryptography<43, Windows CA paketi.

Önceki durum: Adım 1'de DURDU (paket eksik, kurulum için mühendis OK'i bekleniyordu). Sistem Python 3.12'de (C:\Users\kaane\AppData\Local\Programs\Python\Python312) eksik paketler: pytest, colorama, jsonschema, python-dotenv, requests ve digikey (digikey-api, `pip install git+https://github.com/hurricaneJoef/digikey-api.git`). `pytest` koşulamadı; adım 2-5 yapılmadı.
Öneri: tools\component_selector\requirements.txt'ten ayrı bir venv (repo dışı) kurmak; "kur" yanıtında bunu yaparım. Ayrıca not: dosya konumu 01_secim\docs\tasks, DigiKey değişkenlerini (DIGIKEY_CLIENT_ID/SECRET) adım 2'de yalnız adıyla kontrol edeceğim.
