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
Windows konsolunda Unicode için `set PYTHONIOENCODING=utf-8`. Testler (ağ yok): `python -m pytest tools\component_selector\tests -q`. Bağımlılıklar: `requirements.txt` (digikey kütüphanesi ayrıca: `pip install git+https://github.com/hurricaneJoef/digikey-api.git`).

## Windows / Python 3.12
- Sabitlenen küme (`requirements.txt`, doğrulanmış venv'den): requests 2.34.2, urllib3 2.8.0, certifi 2026.10.19, pyOpenSSL 24.2.1, cryptography 42.0.8 (<43), six 1.17.0, python-dateutil 3.0.0, truststore 0.10.5, `setuptools<81`.
- Neden: `setuptools<81` (doğrulanan venv 80.10.2; üst sınırın kesin nedeni bu kayıtta belgelenmedi [A]); pyOpenSSL 24.2.1 yalnız `cryptography<43` ile çalışır.
- Venv repo DIŞINDA, kısa yolda kurulur (Windows 260 karakter yol sınırı): `py -3.12 -m venv C:\vdk`, sonra `C:\vdk\Scripts\python.exe -m pip install -r tools\component_selector\requirements.txt` (digikey kütüphanesi ayrıca, yukarıdaki komut).
- TLS: `truststore` Python'un TLS doğrulamasını tarayıcı gibi işletim sistemi sertifika doğrulamasıyla yaptırır; `search_digikey.py` ve `search_nexar.py` başında `truststore.inject_into_ssl()` çağrılır. Gerekçe: DigiKey sunucusu ara sertifikayı (Sectigo) tam sunmuyor [A]; tarayıcı tamamlar, certifi tamamlamaz (00_coordination/T010).
- CA paketi (bundle) üretilmez; `REQUESTS_CA_BUNDLE`, `SSL_CERT_FILE`, `CURL_CA_BUNDLE` ayarlanmaz; `verify=False` kullanılmaz.
- Kimlik bilgisi yalnız mühendisin yazdığı `.env` dosyasında durur; sohbete veya bilete yapıştırılmaz.
- 01_secim notu: `smoke_run.py` aynı dört satırlık truststore kodunu (try / import truststore / inject_into_ssl / except ImportError) gerektirir; 01_secim kendi biletiyle ekler.

## DigiKey yetkilendirme (mühendis yapar)
Ajan kimlik bilgisine dokunmaz. Mühendis DigiKey developer hesabında uygulamayı oluşturur ve OAuth onayını kendisi verir; ilk aramada tarayıcı açılır. `DIGIKEY_CLIENT_ID` / `DIGIKEY_CLIENT_SECRET` ortam değişkeni veya `.env` ile verilir (`search_digikey.py` `load_dotenv()` kullanır).
Kimlik bilgisi yeri: repo DIŞINDA (oturum ortam değişkenleri). Zorunluysa `tools\component_selector\.env` ve `.digikey_cache\` (token önbelleği) kullanılabilir; ikisi de `.gitignore`'dadır, hiçbir zaman okunmaz/yazılmaz/commit edilmez.

## Sağlayıcı eklentisi planı
Şimdi: DigiKey (`search_digikey.py`, `search_component(ref, spec)` -> aday listesi). `search_nexar.py` (Octopart/Nexar) kodda duruyor, hatta bağlı değil, test edilmedi. Sonra: LCSC, JLCPCB. Hepsi aynı aday sözlüğü şemasını döndüren sağlayıcı modülü olur; sistem çalışınca benchmark edilir (kapsam, doğru varyant, model bağlantısı, fiyat/stok). Datasheet her zaman karar verir.
