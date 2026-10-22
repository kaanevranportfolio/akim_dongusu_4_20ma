# DEVLOG - 01_secim
Append-only oturum günlüğü: tarih, görev, değişiklik, etiketli sonuçlar.

- 2026-10-22 iskelet kuruldu (kök CLAUDE.md, RULE_LEDGER, INTERFACES, modül şablonları).

- 2026-10-22 DigiKey bağlantı testi (01_secim/T001-T005, 00_coordination/T010, T012, T015). Sonuç: token 200, /products/v4/search/keyword 200 [M]; ilk sorgu 0 sonuç. Zincir:
  1. Ortam (T001): Python 3.12'de eksik paketler ve sürüm çakışmaları; venv C:\Users\kaane\AppData\Local\Temp\vdk. pytest 27/27 geçti [R].
  2. TLS (T001): api.digikey.com CERTIFICATE_VERIFY_FAILED. Ajan bilet dışı Windows kök deposundan 53 sertifikayı ca_bundle.pem'e aktardı, REQUESTS_CA_BUNDLE/SSL_CERT_FILE'ı o kabuk için ayarladı [R]. Mühendis itirazı üzerine koordinatör (T010): sertifika Sectigo, ağda denetim kanıtı yok, tarayıcı güveniyor, Python/certifi güvenmiyor; olası neden ara sertifika eksikliği [A]. Mühendis kararı: dosya/CA paketi/ortam değişkeni yok, yalnız truststore; kural 49 Safety'ye eklendi.
  3. Kütüphane (T003, T004): eski digikey-api zaten v4 yolunu (/products/v4/search/keyword) çağırıyordu [R]; callback URL koda sabit. 00_coordination/T015 ile tools\component_selector\digikey_v4.py (V4, 2-legged, token bellekte) geldi; smoke_run.py ona taşındı, certifi bloğu kalktı, truststore 4 satırı kaldı [R].
  4. Kimlik (mühendis koşuları, TLS geçtikten sonra): POST /v1/oauth2/token 401 "Invalid clientId"; .env biçimi temiz (anahtar adları var, len 48/64, boşluk/tırnak yok) [M]. Neden: Sandbox uygulamasının kimliği canlı host'ta tanınmaz [A]. Çözüm: mühendis Production + v4 ekli eski "digikey query" uygulamasının anahtarlarıyla yeniden denedi, token 200 [U][M].
  5. Arama: /products/v4/search/keyword 200, ham yanıt Products=[] ve ExactMatches=[], ProductsCount yok [M]. Sorgu "loop-powered 4-20 mA transmitter IC" fazla spesifikti [A]. Takip: 01_secim/T005 (dört kısa sorgu, alan tablosu).
  Açık/elle: Temp\vdk\ca_bundle.pem ve digikey_smoke\raw_out.tmp mühendis tarafından silinecek; CA ortam değişkenlerinin kalıcı olmadığı doğrulanmadı; README'ye Windows/Python 3.12 notları 00_coordination işi.

- 2026-10-22 DigiKey kaydının düzeltmesi (01_secim/T006; yukarıdaki 2026-10-22 DigiKey girdisinin 3, 4, 5 ve "Açık/elle" maddelerine atıfla; eski metin değişmedi):
  - Erişim yolu: DigiKey erişimi tools\component_selector\digikey_v4.keyword_search üzerinden; token 200 ve /products/v4/search/keyword 200 [M]. `digikey` kütüphanesi artık kullanılmıyor.
  - Madde 4 düzeltmesi: 401 "Invalid clientId" nedeni KANITLANMADI. "Sandbox kimliği canlı host'ta tanınmaz" yalnız bir olasılık [A]; eski V3 kütüphane yolu da olasılık [A] (00_coordination bulgusu). Production + v4 ekli uygulamanın anahtarlarıyla token 200 oldu [U][M]; bu neden kanıtı değildir. lessons.md'de [M] etiketi neden için [A]'ya çevrildi.
  - Madde 3 netleştirmesi: eski digikey-api'nin v4 yolunu (/products/v4/search/keyword) çağırdığı kaynak okumasıdır [R]; OAuth uçları v1 ve her iki sürümde ortak. Hatanın bu kütüphaneden gelip gelmediği bilinmiyor.
  - Madde 5: Products=[] için "fazla spesifik sorgu" [A], 01_secim/T005 (dört kısa sorgu) sonucuna kadar açık. out\passA\digikey_smoke altında result_1..4.json, fields_table.md, found_parts.md mevcut, ancak mühendisin konsol çıktısı bu girdiye işlenmedi; sonuç okunmadan karar yok.
  - Distribütör verisi [W] ve kısa listedir; dönen parçalar aday değildir, datasheet karar verir.
  - "Açık/elle" güncellemesi: raw_out.tmp artık out\ altında yok (silinmiş görünüyor). Temp\vdk\ca_bundle.pem durumu bu oturumda doğrulanmadı (repo dışı, sertifika dosyası, dokunulmadı). Silinecekler listesi 01_secim/T006 Sonuç'ta.
