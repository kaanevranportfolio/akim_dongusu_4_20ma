# FACTS - 01_secim
Etiketler: kök CLAUDE.md "Labels" (tek kaynak). Her satır: değer | etiket | kaynak (D<nn> p.<n>, K<nn> veya <modül>/Tnnn).
Kritik değerler mühendis kontrolüne kadar kesin değildir.

## Gereksinimler (SPEC kimliğiyle)
| ID | Değer | Etiket | Kaynak |
|---|---|---|---|

## Parçalar (tam MPN)
| Ref | MPN | Üretici | Paket | Etiket | Kaynak |
|---|---|---|---|---|---|

## Modeller (docs\INTERFACES.md bölüm 3)
| MPN | model_file | source_url | retrieved | sha256 | represents | cannot_show | Etiket |
|---|---|---|---|---|---|---|---|

## Araçlar ve veri kaynağı (DigiKey)
| Madde | Değer | Etiket | Kaynak |
|---|---|---|---|
| Erişim yolu | tools\component_selector\digikey_v4.keyword_search (Product Information V4, 2-legged OAuth); `digikey` kütüphanesi kullanılmıyor | [M] | token 200, /products/v4/search/keyword 200; docs\DEVLOG.md 2026-10-22 |
| 401 "Invalid clientId" nedeni | KANITLANMADI: Sandbox kimliği canlı host'ta [A] ve/veya eski V3 kütüphane yolu [A]; Production + v4 uygulama anahtarlarıyla token 200 | [A] | docs\lessons.md; 00_coordination bulgusu |
| İlk sorguda Products=[] | fazla spesifik sorgu; AÇIK, 01_secim/T005 sonucu bekleniyor | [A] | docs\DEVLOG.md 2026-10-22 |
| Distribütör verisi | kısa liste, aday değil; datasheet karar verir | [W] | kök CLAUDE.md Principles |

## Kritik değerler (mühendis kontrolü bekleyen)
| Değer | Etiket | Kaynak + crop | Kontrol |
|---|---|---|---|
