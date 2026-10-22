# DECISIONS - 00_coordination
Append-only. Numara K<nn> (belge numarası D<nn> ile karışmaz). Düzeltme yeni kayıtla yapılır ve eskisine atıf verir.
| K | Tarih | Karar | Alternatifler | Neden | Kanıt (D<nn> p.<n> / bilet) | Mühendis kontrolü |
|---|---|---|---|---|---|---|
| K01 | 2026-10-22 | SPEC v0.2 onaylandı: varsayımlar [A] etiketli kalır; K7 akım sınırı 3,8-20,5 mA; 12 V test noktası 220 Ω (7,6 V kalır, marj 0,6 V) ve K5 R_toplam = 220 Ω; 7 V hedefi ters polarite koruması düşümü dahil; 01_core -> 01_secim. Seçim 01_secim'de bu SPEC'e göre yapılır; Bölüm 8 açık soruları (giriş tipi, Vmin, arıza akımı, sıcaklık, doğruluk) 01_secim A aday kontrolünde teyit edilir. | 12 V / 250 Ω (marj 0); Vmin hedefini 6,5 V yapmak; minimum beslemeyi 13 V yapmak; K7'de 21 mA | 12 V / 250 Ω köşesinde 250 Ω x 20 mA = 5 V, 7 V kalır: vericinin minimum çalışma gerilimiyle sıfır marj, ters polarite düşümü sığmaz | SPEC.md v0.2, 00_coordination/T003, T004 | Mühendis 2026-10-22 sohbette onayladı [U] |
