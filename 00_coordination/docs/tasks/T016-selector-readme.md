# T016 - component_selector README: Production uygulaması, ortam, sorun giderme
Durum: BİTTİ
## İstek
Goal: finish tools\component_selector\README.md after the DigiKey incident (01_secim DEVLOG 2026-10-22, 00_coordination/T010-T015). Run from the pipeline root. Edit only: this ticket file and <pipeline>\tools\component_selector\README.md. Everything else is read-only. Never commit / push / amend / delete. Never read or print .env, tokens or credential values. No network call, no pip install.
Steps:
1. Read README.md. Check what T012/T015 already wrote (Windows / Python 3.12 section, V4 section) and do not duplicate it.
2. Add or fix these points (short, Turkish prose, English technical terms as printed):
   a. The DigiKey app must be a Production app (created under the Organization) with the product "Product Information V4" attached. A Sandbox app's Client ID returns HTTP 401 "Invalid clientId / clientId invalid for requested resource" on api.digikey.com (observed 2026-10-22 [M]); sandbox data is also incomplete.
   b. Credentials only as DIGIKEY_CLIENT_ID and DIGIKEY_CLIENT_SECRET in .env (names only, never values in chat or tickets). python-dotenv `load_dotenv()` does NOT overwrite a variable already set in the shell or user environment: a stale value from an old terminal wins; open a new terminal or clear that variable. Do not document `override=True` as existing behaviour.
   c. Remove any mention of DIGIKEY_STORAGE_PATH, .digikey_cache and the `digikey` library if still present (token is kept in memory since T015).
   d. A "Sorun giderme" table of at most 6 rows: CERTIFICATE_VERIFY_FAILED (truststore installed in the venv? otherwise STOP and ask the engineer, root CLAUDE.md Safety rule 49: no CA bundle, no CA environment variables, no verify=False); 401 Invalid clientId (app type / product / stale environment variable); 403 (product not enabled for the app); 429 (rate limit, one automatic retry, then wait); Products empty with HTTP 200 (query too specific: use short keyword queries); Windows path/venv problems (short path such as C:\vdk, 260-character limit).
3. Check: show `git diff --stat` for README.md only and the new "Sorun giderme" table.
Output: at most 5 lines plus the table.
## Sonuç
1. T012/T015 bölümleri (Windows / Python 3.12, V4) tekrar edilmedi; yalnız tamamlandı.
2. README.md: (a) Production uygulama + Organization + Product Information V4, Sandbox Client ID 401 (2026-10-22 [M]); (b) yalnız DIGIKEY_CLIENT_ID / DIGIKEY_CLIENT_SECRET adları, `load_dotenv()` mevcut değişkeni ezmez (bayat değer kazanır), `override=True` belgelenmedi; (c) DIGIKEY_STORAGE_PATH, `.digikey_cache` ve `digikey` kütüphanesi anıları kaldırıldı (grep ile doğrulandı: kalmadı); (d) "Sorun giderme" tablosu eklendi.
3. `git diff --stat` (yalnız README.md): 1 dosya, 43 ekleme, 5 silme (T015 değişiklikleriyle birlikte, commit edilmedi).

| belirti | olası neden / ne yapılır |
|---|---|
| `CERTIFICATE_VERIFY_FAILED` | venv'de `truststore` kurulu mu (`pip show truststore`)? Değilse mühendise sor ve DUR (kök CLAUDE.md Safety, kural 49): CA paketi yok, CA ortam değişkeni yok, `verify=False` yok |
| 401 "Invalid clientId" | uygulama Sandbox türünde; ya da Production uygulamaya Product Information V4 bağlı değil; ya da eski terminalden kalan bayat `DIGIKEY_CLIENT_ID` / `DIGIKEY_CLIENT_SECRET` (`.env`'i ezer): yeni terminal aç |
| 403 | ürün (Product Information V4) bu uygulamada etkin değil |
| 429 | rate limit; `Retry-After` kadar bekleyip bir kez otomatik yeniden denenir, yine 429 gelirse bir süre bekle |
| HTTP 200 ama `Products` boş | sorgu fazla özgül; kısa keyword sorguları kullan |
| Windows yol / venv hataları | venv kısa yolda (`C:\vdk`) olsun; 260 karakter yol sınırı |
