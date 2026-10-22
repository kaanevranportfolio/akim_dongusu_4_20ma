---
name: bring-up-log
description: Guide and record the first power-up of a built board. Triggers - bring-up, ölçüm, measurement, prototip.
---

# bring-up-log

Sayısal değerlerin hiçbiri bu dosyada yazılı değildir. Tüm sayılar (ray sınırları, akım sınırları, eşikler, pin ve parça adları) bu projenin `FACTS.md` dosyasından çalışma anında okunur. `FACTS.md`'de değer yoksa [A] işaretle ve mühendise sor; hafızadan doldurma. Durdurma kuralları bu projenin `CLAUDE.md` dosyasında "##" başlığı "Bring-up durdurma kural" ile BAŞLAYAN bölümden gelir (önek eşleşmesi: "kuralları" ve "kurallari" ikisi de eşleşir, başlığın sonundaki ek metin örn. " [A] (...)" yok sayılır); böyle bir başlık yoksa dur ve sor.

Adımlar:
1. Güç vermeden önce: akım sınırlı besleme; sınır `FACTS.md`'deki belge değeridir, yoksa [A]; polarite kontrolü; her ray ile GND arasındaki direnç ölçülür (kısa devre yok). Ray listesi `FACTS.md`'den alınır.
2. Durdurma kuralları: `CLAUDE.md`'de "Bring-up durdurma kural" ile başlayan "##" bölümündeki her kural, eşiğiyle birlikte, güç verilmeden önce mühendise okunur. Kural tetiklenirse önce gücü kes. Eşikler `FACTS.md`'deki [V] değerlere dayanmalıdır; dayanmayan eşik [A] kalır.
3. Her ölçümü kaydet: büyüklük, değer, cihaz, koşullar, tarih -> `FACTS.md` `[M]`.
4. `FACTS.md`'deki simülasyon değerleriyle karşılaştır, sapmaları not et.
5. Olaylar `docs\lessons.md`'ye; bir DEVLOG girdisi.

Doğrular: ölçülen değerleri, [M] etiketiyle, tahminlere karşı.
