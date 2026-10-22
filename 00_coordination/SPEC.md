# Spec: 4–20 mA akım döngüsü vericisi

| | |
|---|---|
| **Sürüm** | v0.2 |
| **Tarih** | 2026-10-22 |
| **Durum** | Taslak, mühendis onayı bekliyor |
| **Sahibi** | 00_coordination (koordinatör) |

> **Gösterim:** Sonunda **[A]** olan değerler varsayımdır, onaylanana ya da düzeltilene kadar geçicidir. Onaylanan değerler etiketsiz yazılır.

---

## 0. Proje çıktısı (bitiş tanımı)

Proje bittiğinde şu üç şey elimizde olmalı:

1. **Çıkış akımı eğrisi:** QSPICE'ta ölçülmüş `I_out = f(V_in)` eğrisi. Girişte 0–10 V karşılığında döngü akımı 4–20 mA, doğruluk ±0,1 % (aralık bazında).
2. **Kabul kriteri raporu:** Bölüm 7'deki tüm kriterlerin geçti/kaldı sonucu.
3. **KiCad kartı:** Şema ve yerleşim tamam, DRC temiz, BOM'daki her MPN kaynak URL'siyle kayıtlı.

Başarı ölçütünün özü: **doğru ve kararlı döngü akımı**, besleme ve yük aralığının tamamında.

---

## 1. Amaç

Gerilim çıkışlı bir sensörün ya da sinyal kaynağının ölçümünü, 2 telli bir akım döngüsü üzerinden uzaktaki bir PLC'ye taşımak. Vericiyi simüle ederken alıcı tarafı basit bir şönt direnç olarak modellenir (Bölüm 4).

**Kapsam dışı (v0.2):** alıcı devresi, galvanik izolasyon, HART, EMC testlerinin tamamı, seri üretim.

---

## 2. Giriş

| Parametre | Değer |
|---|---|
| Sinyal tipi | Gerilim, 0–10 V [A] |
| Giriş empedansı | ≥ 100 kΩ [A] |
| Girişe izin verilen maks. gerilim | ±30 V hasarsız [A] |
| Giriş kaynağı | Harici, kendi beslemesi var. Döngüden yalnızca verici devresi beslenir [A] |

---

## 3. Çıkış (döngü akımı)

| Parametre | Değer |
|---|---|
| Çıkış aralığı | 4–20 mA (aralık = 16 mA) |
| Transfer fonksiyonu | `I_out = 4 mA + 1,6 mA/V × V_in` |
| Doğruluk, 25 °C | ±0,1 % aralık (±16 µA) [A] |
| Doğruluk, tüm sıcaklık aralığı | ±0,25 % aralık (±40 µA) [A] |
| Doğrusallık | ±0,05 % aralık (±8 µA) [A] |
| Besleme duyarlılığı | ≤ 1 µA/V [A] |
| Yerleşme süresi (±0,1 % aralık) | ≤ 20 ms [A] |
| Aşım (overshoot) | ≤ 2 % aralık [A] |
| Aralık dışı davranış | Akım 3,8–20,5 mA arasında sınırlanır (NAMUR NE43 ölçüm aralığı) [A] |
| Arıza akımı | v0.2'de zorunlu değil, Bölüm 8'de açık soru |

---

## 4. Döngü

| Parametre | Değer |
|---|---|
| Besleme tipi | 2 telli, loop-powered [A] |
| Besleme aralığı | 12–36 V DC, nominal 24 V [A] |
| Vericinin minimum çalışma gerilimi | ≤ 7 V, ters polarite koruması düşümü dahil, döngü terminallerinde [A] |
| İç tüketim (sıfır girişte) | ≤ 3,5 mA, yani 4 mA tabanının altında kalmalı [A] |
| Yük + kablo direnci | `R_toplam,maks = (V_besleme − 7 V) / 20 mA` |
| Simülasyonda alıcı modeli | 250 Ω şönt direnç (+ kablo direnci); 12 V satırında 220 Ω |
| Kablo kapasitansi (kararlılık testi) | 10 nF'a kadar [A] |

**Test matrisi** (hepsinde 20 mA'e ulaşılmalı):

| Besleme | R_toplam |
|---|---|
| 12 V | 220 Ω (en kötü durum; 12 V − 4,4 V = 7,6 V, 7 V'a göre marj 0,6 V) |
| 24 V | 300 Ω (250 Ω şönt + 50 Ω kablo) |
| 24 V | 600 Ω |
| 36 V | 250 Ω |

> **Kritik kısıt:** Devrenin kendi tüketimi 4 mA tabanını aşarsa, sıfır girişte 4 mA'e inilemez. Çekirdek IC ve çevre parçaları bu bütçeye göre seçilir.

---

## 5. Koruma

| Parametre | Değer |
|---|---|
| Ters polarite | −36 V sürekli hasarsız, ters akım ≤ 1 mA [A] |
| Aşırı gerilim | 36 V sürekli hasarsız [A] |
| Geçici aşırı gerilim (TVS) | Kırpma seviyesi hiçbir parçanın mutlak maksimumunu aşmamalı [A] |
| ESD | IEC 61000-4-2, ±4 kV temas (hedef, v0.2'de simülasyon kapsamı dışı) [A] |
| İzolasyon | Yok (izolasyonsuz tasarım) [A] |

---

## 6. Çevre ve kart

| Parametre | Değer |
|---|---|
| Çalışma sıcaklığı | −25 … +70 °C [A] |
| Kart | 2 katman, en fazla 50 × 30 mm [A] |
| Montaj | Tek yüzde SMD tercih [A] |

---

## 7. Kabul kriterleri (QSPICE'ta geçti/kaldı)

Her kriter, spec sürümü ile birlikte raporlanır.

| # | Test | Geçme koşulu |
|---|---|---|
| K1 | `V_in = 0 V`, 24 V / 250 Ω, 25 °C | `I_out = 4 mA ± 16 µA` |
| K2 | `V_in = 10 V`, 24 V / 250 Ω, 25 °C | `I_out = 20 mA ± 16 µA` |
| K3 | `V_in` taraması 0–10 V | Doğrusallık hatası ≤ ±8 µA |
| K4 | Bölüm 4'teki tüm besleme/yük noktaları, `V_in = 10 V` | 20 mA'e ulaşır, doyma yok |
| K5 | Besleme taraması 12–36 V, R_toplam = 220 Ω | Akım değişimi ≤ 1 µA/V |
| K6 | −25 / +25 / +70 °C, parça toleransları uç değerde | Hata ≤ ±40 µA |
| K7 | Aralık dışı giriş: `V_in = −1 V` ve `12 V` | Akım 3,8–20,5 mA içinde, hasar yok |
| K8 | Ters polarite −36 V | Ters akım ≤ 1 mA, hiçbir parça maksimumu aşmaz |
| K9 | Aşırı gerilim 36 V sürekli ve TVS kırpma kontrolü | Hiçbir parça maksimumu aşmaz |
| K10 | `V_in = 0 V` iç tüketim | ≤ 3,5 mA |
| K11 | `V_in` adımı 0 → 10 V | Yerleşme ≤ 20 ms, aşım ≤ 2 % |
| K12 | 10 nF kablo kapasitansı | Osilasyon yok, K11 sağlanır |

**Not (parça modeli):** K6 için çekirdek IC'nin üretici SPICE modeli kullanılır. Üretici modeli sıcaklık ve tolerans köşelerini desteklemiyorsa bu kriter çevre parçalarının toleranslarıyla ve datasheet garanti değerleriyle birlikte değerlendirilir.

---

## 8. Açık sorular

1. Giriş tipi gerçekten 0–10 V mu? Çekirdek IC adayları giriş tipini kısıtlarsa (ör. akım girişli çipler) spec v0.2'de revize edilir.
2. Vericinin minimum çalışma gerilimi hedefi 7 V mu, yoksa daha düşük/yüksek mi? Ters polarite koruması düşümü bu hedefin içindedir; 12 V / 220 Ω satırında marj 0,6 V. Koruma düşümü 01_secim A'nın ilk sorusudur.
3. Arıza akımı (NAMUR 3,6 mA / 21 mA) istenecek mi?
4. Sıcaklık aralığı −25…+70 °C yeterli mi, yoksa −40…+85 °C mi?
5. Doğruluk hedefi ±0,1 %, seçilecek çekirdek IC için gerçekçi mi? 01_secim aday kontrolünde teyit edilecek.

---

## 9. Sürüm geçmişi

| Sürüm | Tarih | Değişiklik |
|---|---|---|
| v0.1 | 2026-10-22 | İlk taslak, varsayılan değerlerle |
| v0.2 | 2026-10-22 | (V) -> [A] etiketi; K7 3,8–20,5 mA; 12 V satırı 220 Ω ve K5 buna göre; koruma düşümü 7 V hedefine dahil; 01_core -> 01_secim |
