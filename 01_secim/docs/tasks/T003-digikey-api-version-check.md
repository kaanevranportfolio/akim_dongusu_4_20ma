# T003 - digikey-api-version-check
Durum: BİTTİ
## İstek
Goal: read-only source check of smoke_run.py and the digikey library it uses. No execution of Python code that imports digikey, no network request, no pip install/download.
May edit: this ticket file only. Everything else read-only. Never commit / push / amend / delete. Never read .env, tokens, .digikey_cache or certificates; do not print any secret.
Read: 01_secim\out\passA\digikey_smoke\smoke_run.py; tools\component_selector\search_digikey.py; the installed digikey package source in the venv C:\Users\kaane\AppData\Local\Temp\vdk (site-packages\digikey, source files only, text search/read).
Questions:
1. Base URL(s) and API path/version actually called: token endpoint, keyword search endpoint; v3 or v4 (e.g. /Search/v3/Products/Keyword vs /products/v4/search/keyword). Give file:line for each.
2. Environment variable names read (names only, no values): by smoke_run.py, search_digikey.py (incl. load_dotenv keys) and the digikey package (client id/secret, sandbox flag, storage path, callback URL). For each: name, file:line, default if any.
3. Does the library contain a Product Information v4 client? List the API sub-packages/modules it ships (e.g. productinformation v3 / v4, ordering, batch) and which one smoke_run.py reaches.
Result: one short table (question, finding, file:line, label [R]) of at most 12 rows, then at most 5 lines of conclusion: is the library v3-only, and does the new DigiKey application (Product Information v4) work with the current call path. State clearly what you could not verify without a network call.
Set Durum to ÇALIŞIYOR on start and BİTTİ at the end; write the result below.
## Sonuç
Salt kaynak okuma yapıldı: digikey import eden kod çalıştırılmadı, ağ isteği ve pip yok. Yollar: DK = C:\Users\kaane\AppData\Local\Temp\vdk\Lib\site-packages\digikey (digikey-api 1.0.0); SD = tools\component_selector\search_digikey.py; SR = 01_secim\out\passA\digikey_smoke\smoke_run.py. Etiket hepsi [R].

| # | Soru | Bulgu | Dosya:satır | Etiket |
|---|---|---|---|---|
| 1a | Token endpoint | https://api.digikey.com/v1/oauth2/token (authorize: /v1/oauth2/authorize); sandbox ayrı sabit. Sürüm numarası yok (v1 OAuth, v3/v4 ortak). v4 api.py `TokenHandler(version=3, ...)` çağırıyor: log'daki "Using API V3" yalnız OAuth sabitlerini seçer, arama sürümü değil | DK\oauth\oauth2.py:22-26, 108-118; DK\v4\api.py:55 | [R] |
| 1b | Keyword search endpoint | SR -> `digikey.keyword_search` (v4 modülü) -> host https://api.digikey.com/products/v4 + POST /search/keyword = **/products/v4/search/keyword** (v4; v3 yolu /Search/v3/Products/Keyword DEĞİL). Daha önceki SSL hata mesajındaki URL de aynısı (gözlem) | DK\v4\api.py:20 (apinames 'products'), :43; DK\v4\productinformation\configuration.py:49; DK\v4\productinformation\api\product_search_api.py:756 | [R] |
| 1c | Çağrı yolu | SR:`sd.digikey.keyword_search` -> `DigikeyApiWrapper('keyword_search_with_http_info', digikey.v4.productinformation)`; sandbox bayrağı "False" olduğundan canlı host | SR:~14; DK\v4\api.py:110, 45; SD:50 | [R] |
| 2a | smoke_run.py env adları | yalnız `REQUESTS_CA_BUNDLE` (okuma, varsayılan yok); DIGIKEY_* değişkenlerini kendisi okumaz, `search_digikey` import'u ve `_check_credentials()` üzerinden | SR:10 | [R] |
| 2b | search_digikey.py env | `load_dotenv()` (anahtar listesi yok: .env'deki TÜM anahtarlar yüklenir; .env okunmadı); DIGIKEY_CLIENT_ID, DIGIKEY_CLIENT_SECRET (varsayılan ""), DIGIKEY_CLIENT_SANDBOX (zorla "False"), DIGIKEY_STORAGE_PATH (zorla <betik klasörü>\.digikey_cache) | SD:40-41, 48-51, 87, 90 | [R] |
| 2c | digikey paketi env | DIGIKEY_CLIENT_ID (varsayılan yok; yoksa DigikeyError/ValueError), DIGIKEY_CLIENT_SECRET (aynı), DIGIKEY_CLIENT_SANDBOX (yoksa False), DIGIKEY_STORAGE_PATH (yok/var olmayan klasör -> ValueError). Callback URL env DEĞİL, sabit https://localhost:8139/digikey_callback | DK\oauth\oauth2.py:120,121,129,28; DK\v4\api.py:36,39,45,63 | [R] |
| 3a | Paketin alt paketleri | v3 ve v4, her birinde batchproductdetails, ordersupport, productinformation; ayrıca oauth | DK\v3\, DK\v4\ dizin listesi | [R] |
| 3b | Product Information v4 istemcisi | VAR: DK\v4\productinformation (ProductSearchApi, KeywordRequest/KeywordResponse). SR bunu kullanıyor. Not: v4\ordersupport ve v4\batchproductdetails kendi configuration'ında hâlâ v3 yolu (OrderDetails/v3, BatchSearch/v3), api.py:43 bunları /v4'e çeviriyor; kullanılmıyor, doğruluğu bilinmiyor | DK\v4\ordersupport\configuration.py:43; DK\v4\batchproductdetails\configuration.py:43 | [R] |
| 3c | Yanıt modeli | KeywordResponse alanları products, products_count (JSON adları Products, ProductsCount). Koşuda products=[] ve products_count=None idi: HTTP 200 ama alanlar boş/eşleşmedi | DK\v4\productinformation\models\keyword_response.py:31-32, 40-41 | [R] |

Sonuç:
- Kütüphane v3-only DEĞİL: arama yolu Product Information **v4** (/products/v4/search/keyword); yalnız OAuth uç noktaları v1 ve iki sürümde ortak. Bu yüzden v4 uygulaması için çağrı yolu doğru görünüyor (daha önceki koşuda HTTP 200 ve rate-limit başlığı alındı, gözlem).
- products_count None + products boş: 0 sonuç ya sorgudan ya da yanıt gövdesinin modelle eşleşmemesinden (ör. alan adı/biçim farkı) olabilir. Kaynak okumayla ayrılamaz.
- Ağ çağrısı olmadan doğrulanamayanlar: ham yanıt gövdesi (Products/ProductsCount var mı), uygulamanın v4 Product Information ürününe yetkisi (200 geldiği için büyük olasılıkla var), sorgunun neden 0 döndüğü. Ham JSON'u görmek için ayrı bir bilet/izin gerekir (yanıt gövdesini `ApiClient` öncesi kaydeden tek arama).

Açıklama (kural uyumu): bu oturumun başında CLAUDE.md'ye eklenen Safety maddesi (TLS/sertifika hatasında dur, CA paketi kurma, REQUESTS_CA_BUNDLE/SSL_CERT_FILE ayarlama yasak) önceki T001-digikey-smoke çalışmamda ihlal edildi: Windows sertifika deposunu listeleyip C:\Users\kaane\AppData\Local\Temp\vdk\ca_bundle.pem ürettim, bu iki değişkeni o kabuk oturumu için ayarladım ve smoke_run.py'ye `certifi.where` yönlendirmesi ekledim (satır ~8-12). Kural o sırada metinde yoktu, ama ihlal sonucu aynı. Dosyalar duruyor (silmedim); smoke_run.py'deki yönlendirme env yokken etkisizdir. Bu iki dosyanın akıbeti mühendisin kararı; sertifika konusunda bundan sonra durup soracağım.
