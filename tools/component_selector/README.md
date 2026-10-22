# component_selector

DigiKey tabanlı parça seçici (v1.0, kaynak: C:\component_selector_v1). Bu klasörde yalnız kod vardır; çıktılar `--out` ile verilen klasöre yazılır.
Hat içindeki yeri: 01_secim pass B (CLAUDE.md "Kontrol sırası B"); girdi/çıktı sözleşmesi `docs\INTERFACES.md`.

## Girdi
- `component_specs.json`: `--specs` ile verilir (varsayılan: betik klasörü; bu klasörde dosya YOK). Şema: `schemas\component_specs_schema.json` (`validate_specs.py` doğrular). Ham değerler gelir; derating yalnız `config\derating_profiles.json` profilinde uygulanır, ikinci kez uygulanmaz.
- İsteğe bağlı `reference_parts_map.json`: `--reference-map PATH` (footprint ve ic_fixed pin_map önceliği; yoksa tip varsayılanları).

## Çıktı (`--out DIR`, varsayılan: çalışma klasörü)
- `parts_map.json`, `selection_report.md`, `selection.log` (`*.log` gitignored).
- Eksik satıcı verisi ("not in vendor data") PASS sayılmaz: kural durumu `ASSUMED_VERIFY`; `parts_map.json` içinde `derating_status` = `ASSUMED_VERIFY`, raporda özet satırı ve "Manual verification required" listesi. Datasheet kontrolü açık madde (VARSAYILAN [A]).

## Çalıştırma
    python tools\component_selector\select_components.py --specs <component_specs.json> --out <01_secim\out\passB>
Windows konsolunda Unicode için `set PYTHONIOENCODING=utf-8`. Testler (ağ yok): `python -m pytest tools\component_selector\tests -q`. Bağımlılıklar: `requirements.txt` (DigiKey erişimi `digikey_v4.py`, yalnız `requests`).

## Windows / Python 3.12
- Sabitlenen küme (`requirements.txt`, doğrulanmış venv'den): requests 2.34.2, urllib3 2.8.0, certifi 2026.10.19, pyOpenSSL 24.2.1, cryptography 42.0.8 (<43), six 1.17.0, python-dateutil 3.0.0, truststore 0.10.5, `setuptools<81`.
- Neden: `setuptools<81` (doğrulanan venv 80.10.2; üst sınırın kesin nedeni bu kayıtta belgelenmedi [A]); pyOpenSSL 24.2.1 yalnız `cryptography<43` ile çalışır.
- Venv repo DIŞINDA, kısa yolda kurulur (Windows 260 karakter yol sınırı): `py -3.12 -m venv C:\vdk`, sonra `C:\vdk\Scripts\python.exe -m pip install -r tools\component_selector\requirements.txt`.
- TLS: `truststore` Python'un TLS doğrulamasını tarayıcı gibi işletim sistemi sertifika doğrulamasıyla yaptırır; `search_digikey.py` ve `search_nexar.py` başında `truststore.inject_into_ssl()` çağrılır. Gerekçe: DigiKey sunucusu ara sertifikayı (Sectigo) tam sunmuyor [A]; tarayıcı tamamlar, certifi tamamlamaz (00_coordination/T010).
- CA paketi (bundle) üretilmez; `REQUESTS_CA_BUNDLE`, `SSL_CERT_FILE`, `CURL_CA_BUNDLE` ayarlanmaz; `verify=False` kullanılmaz.
- Kimlik bilgisi yalnız mühendisin yazdığı `.env` dosyasında durur; sohbete veya bilete yapıştırılmaz.
- 01_secim notu: `smoke_run.py` aynı dört satırlık truststore kodunu (try / import truststore / inject_into_ssl / except ImportError) gerektirir; 01_secim kendi biletiyle ekler.

## DigiKey Product Information V4 (mühendis yapar: uygulama ve kimlik bilgisi)
- Akış: 2-legged OAuth (client credentials), tarayıcı onayı yok. Kod: `digikey_v4.py` (yalnız `requests`); `search_digikey.py` bunu kullanır. Eski v3 çağrıları bu uygulamada 401 "clientId invalid for requested resource" verdi (00_coordination/T013).
- Gerekli uygulama: DigiKey developer hesabında Organization altında oluşturulmuş bir **Production** uygulaması (`pipeline_app`), ürün olarak "Product Information V4" bağlı olmalı. Sandbox uygulamasının Client ID'si api.digikey.com'da HTTP 401 "Invalid clientId / clientId invalid for requested resource" verir (2026-10-22 gözlendi [M]); sandbox verisi de eksiktir. Ajan kimlik bilgisine dokunmaz.
- Kimlik bilgisi yalnız `DIGIKEY_CLIENT_ID` ve `DIGIKEY_CLIENT_SECRET` adlarıyla `tools\component_selector\.env` içinde (değerler asla sohbete veya bilete yazılmaz); `.env` `.gitignore`'dadır, okunmaz/commit edilmez. `load_dotenv()` kabukta veya kullanıcı ortamında ZATEN ayarlı bir değişkenin üzerine yazmaz: eski bir terminalden kalan bayat değer kazanır; yeni terminal açın veya o değişkeni temizleyin.
- Token yalnız bellekte tutulur (süre bitmeden 60 s önce yenilenir), diske yazılmaz.
- Hata işleme: 401 / 403 / 429 için ayrı istisna; 429'da `Retry-After` kadar bekleyip tek yeniden deneme. Başlık, token ve secret günlüğe/hata metnine yazılmaz.

### Doğrulanan sözleşme [W] (resmi developer.digikey.com sayfaları; ağ çağrısı yapılmadı)
| öğe | değer | kaynak sayfa |
|---|---|---|
| token | `POST https://api.digikey.com/v1/oauth2/token`, `application/x-www-form-urlencoded`, `client_id`, `client_secret`, `grant_type=client_credentials`; yanıt `access_token`, `expires_in` (s), `token_type` | "OAuth 2.0: 2 Legged Flow" |
| API başlıkları | `Authorization: Bearer <token>`, `X-DIGIKEY-Client-Id: <client id>` (Swagger'da required); isteğe bağlı `X-DIGIKEY-Locale-Site` (varsayılan US), `-Language` (en), `-Currency` | "OAuth 2.0: 2 Legged Flow", KeywordSearch Swagger |
| KeywordSearch | `POST https://api.digikey.com/products/v4/search/keyword`; gövde `Keywords`, `Limit`, `Offset`, `FilterOptionsRequest`, `SortOptions`; yanıt `Products[]`, `ProductsCount`, `ExactMatches`, `FilterOptions` | "KeywordSearch" (Swagger: node/2357) |
| ProductDetails | `GET https://api.digikey.com/products/v4/search/{productNumber}/productdetails`; yanıt `Product`; başlıklar KeywordSearch ile aynı (+ `X-DIGIKEY-Account-Id`) | "ProductDetails" (Swagger: node/2360) |
Not: Swagger `Authorization` başlığını listelemiyor; Bearer kuralı OAuth sayfasından. 2-legged sayfasının Retry-After/429 davranışını tanımlamadığı görüldü [A: standart HTTP varsayımı].

### Alan eşlemesi: V4 -> seçici alanı (`search_digikey._normalise_product`)
| V4 (Product) | seçici alanı |
|---|---|
| `ManufacturerProductNumber` | `mpn` |
| `Manufacturer.Name` | `manufacturer` |
| `Description.DetailedDescription` (yoksa `ProductDescription`) | `description` |
| `ProductStatus.Status` | `lifecycle` |
| `DatasheetUrl` | `datasheet` |
| `ProductVariations[0].DigiKeyProductNumber` | `digikey_pn` |
| `ProductUrl` | `product_url` |
| `UnitPrice` | `unit_price_usd` |
| `QuantityAvailable` | `stock` |
| `ManufacturerLeadWeeks` | `lead_time_weeks` |
| `Parameters[].ParameterText` / `ValueText` | `_raw_params` ve tipe özgü sayısal alanlar (`_PARAM_MAP`, değişmedi) |
Eşi olmayan alan yok; yanıtta eksik alan `None` (açıklama için "PARAMETER NOT AVAILABLE", stok için 0). `tempco_ppm` eskiden de `_PARAM_MAP`'te karşılıksızdı, `None` kalır.

## Sorun giderme
| belirti | olası neden / ne yapılır |
|---|---|
| `CERTIFICATE_VERIFY_FAILED` | venv'de `truststore` kurulu mu (`pip show truststore`)? Değilse mühendise sor ve DUR (kök CLAUDE.md Safety, kural 49): CA paketi yok, CA ortam değişkeni yok, `verify=False` yok |
| 401 "Invalid clientId" | uygulama Sandbox türünde; ya da Production uygulamaya Product Information V4 bağlı değil; ya da eski terminalden kalan bayat `DIGIKEY_CLIENT_ID` / `DIGIKEY_CLIENT_SECRET` (`.env`'i ezer): yeni terminal aç |
| 403 | ürün (Product Information V4) bu uygulamada etkin değil |
| 429 | rate limit; `Retry-After` kadar bekleyip bir kez otomatik yeniden denenir, yine 429 gelirse bir süre bekle |
| HTTP 200 ama `Products` boş | sorgu fazla özgül; kısa keyword sorguları kullan |
| Windows yol / venv hataları | venv kısa yolda (`C:\vdk`) olsun; 260 karakter yol sınırı |

## Sağlayıcı eklentisi planı
Şimdi: DigiKey (`search_digikey.py`, `search_component(ref, spec)` -> aday listesi). `search_nexar.py` (Octopart/Nexar) kodda duruyor, hatta bağlı değil, test edilmedi. Sonra: LCSC, JLCPCB. Hepsi aynı aday sözlüğü şemasını döndüren sağlayıcı modülü olur; sistem çalışınca benchmark edilir (kapsam, doğru varyant, model bağlantısı, fiyat/stok). Datasheet her zaman karar verir.
