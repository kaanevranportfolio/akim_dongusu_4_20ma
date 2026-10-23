# FACTS - 01_secim
Etiketler: kök CLAUDE.md "Labels" (tek kaynak). Her satır: değer | etiket | kaynak (D<nn> p.<n>, K<nn> veya <modül>/Tnnn).
Kritik değerler mühendis kontrolüne kadar kesin değildir.

## Gereksinimler (SPEC kimliğiyle)
| ID | Değer | Etiket | Kaynak |
|---|---|---|---|
| §2 Sinyal tipi | Gerilim, 0-10 V | [A] | SPEC v0.2 §2 |
| §2 Giriş empedansı | ≥ 100 kΩ | [A] | SPEC v0.2 §2 |
| §2 Girişe izin verilen maks. gerilim | ±30 V hasarsız | [A] | SPEC v0.2 §2 |
| §3 Çıkış aralığı, transfer | 4-20 mA; I_out = 4 mA + 1,6 mA/V × V_in | [U] | SPEC v0.2 §3 (onaylı, K01) |
| §3 Doğruluk | ±16 µA (25 °C), ±40 µA (tüm sıcaklık), doğrusallık ±8 µA | [A] | SPEC v0.2 §3; K1-K3, K6 |
| §3 Besleme duyarlılığı | ≤ 1 µA/V | [A] | SPEC v0.2 §3; K5 |
| §3 Yerleşme, aşım | ≤ 20 ms (±0,1 %), ≤ %2 | [A] | SPEC v0.2 §3; K11 |
| §3 Aralık dışı | akım 3,8-20,5 mA arasında sınırlanır | [A] | SPEC v0.2 §3; K7 |
| §4 Besleme | 12-36 V DC, 2 telli loop-powered | [A] | SPEC v0.2 §4 |
| §4 Vmin | ≤ 7 V terminalde, ters polarite koruması düşümü dahil; 12 V / 220 Ω köşesinde 7,6 V kalır, marj 0,6 V | [A] / [C] | SPEC v0.2 §4; K01 (00_coordination) |
| §4 İç tüketim | ≤ 3,5 mA (V_in = 0 V) | [A] | SPEC v0.2 §4; K10 |
| §4 Kablo kapasitansı | 10 nF'a kadar | [A] | SPEC v0.2 §4; K12 |
| §5 Koruma | ters polarite -36 V (≤ 1 mA), 36 V sürekli hasarsız, TVS kırpma ≤ parça maksimumu | [A] | SPEC v0.2 §5; K8, K9 |
| §6 Çevre, kart | -25...+70 °C; 2 katman ≤ 50 × 30 mm; tek yüz SMD tercih | [A] | SPEC v0.2 §6 |
| G1 Op-amp supply current | MAX, -25...+70 °C: ≤ ~1 mA (bütçe: 3,5 mA - referans - bölücü - regülatör) | [A] | K01 (01_secim); SPEC §4 |
| G2 Op-amp giriş ortak mod aralığı | negatif ray (GND) dahil, tek besleme | [A] | K01 (01_secim) |
| G3 Op-amp Vos + sürüklenme | toplam ≤ 2 mV (-25...+70 °C): Rs ≈ 100 Ω için ±20 µA = hata bütçesinin %50'si | [C] | SPEC §3 (±40 µA) × %50 [A] × 100 Ω [A] |
| G4 Op-amp giriş kutuplama akımı | Ib × R_kaynak ≪ 2 mV; 100 kΩ'da 10 nA = 1 mV | [C] | SPEC §2 (≥ 100 kΩ) |
| G5 Op-amp kararlılık, hız | 10 nF kablo ve pass kapasitansı ile kararlı; yerleşme ≤ 20 ms için τ ≲ 2,9 ms, kapalı çevrim ≳ 60 Hz | [C] | SPEC §3, §4 |
| G6 Gerilim referansı | başlangıç hatası ve tempco toplam hata bütçesinin %50'sini aşmaz (toplam ~26 ppm/°C ≈ 40 µA / 16 mA / 95 °C); Iq küçük | [A] / [C] | SPEC §3, §6 |
| G7 Pass elemanı | BV ≥ 36 V + TVS marjı, I ≥ 20 mA, en kötü Pd ≈ 0,6 W (36 V / 250 Ω / 20 mA) | [C] | SPEC §4, §5; pass B'de seçilir, pass 1'de genel model [A] |
| G8 SPICE modeli | üretici kaynaklı, düz metin SPICE (.lib/.sub/.cir), QSPICE'a çevrilebilir; şifreli ise mühendise sorulur | [A] | docs\INTERFACES.md bölüm 3 |
| G9 Yaşam döngüsü, paket | Active, SMD | [A] | SPEC §6 |

## Parçalar (tam MPN)
| Ref | MPN | Üretici | Paket | Etiket | Kaynak |
|---|---|---|---|---|---|
| | TLV333IDBVR | Texas Instruments | SOT-23 (DBV), 5 pin (TI ürün sayfası listesi; D<nn> bekliyor) | [W] | 01_secim K02; https://www.ti.com/product/TLV333 (2026-10-23) |
| | MAX6070AAUT12+T | Analog Devices (Maxim), 1,25 V varyantı | 6 SOT23 (D02 p.25 Ordering Information genel satır MAX6070_AUT_ _+T, PIN-PACKAGE "6 SOT23"; D02 p.2 Package Information U6+5/U6+5A; tam MPN'li Ordering satırı yok, Selector Guide p.24'te tam satır var, paket sütunu yok) | [R] | 01_secim K03; D02 p.25 + D02_p25_ordering.png; D02 p.2 + D02_p2_absmax.png |

## Modeller (docs\INTERFACES.md bölüm 3)
| MPN | model_file | source_url | retrieved | sha256 | represents | cannot_show | Etiket |
|---|---|---|---|---|---|---|---|
| TLV333IDBVR (model adı TLVx333; TLV333/TLV2333/TLV4333 ortak) | sim\models\TLV333\SBOM965C\TLVx333.LIB (arşiv SBOM965C.ZIP, 31006 bayt, sha256 2c048e9d424506c7c5ea5cd1ff257a55908ab8bae39c5bac82de6c303950a6e9; PSpice paketi, ayrıca .OLB/.LIBsig/test devresi) | sayfa https://www.ti.com/product/TLV333 ("TLVx333 PSpice Model (Rev. C)"); dosya https://www.ti.com/lit/zip/SBOM965 | 2026-10-23 | d03896121bd3d0ca0ee2922a9d7f7caa5c186e370b4dcaeff3e11fb119e16c3e | düz metin (ASCII, CRLF), şifreli değil; başlık: "Generic (suitable for all analysis types)", Final 1.3, 16JUN2022, GWL macro model. Modellenenler (başlık listesi a-y): Aol, GBW, CMRR, PSRR, Zid, Zic, Zo, Iout, en, in, Vo swing, Isc, Iq, ts, SR, aşım, büyük sinyal, tor, Ib, Ios, Vos, Vos drift, Vcm, Vos-Vcm, ESD. Düğüm sırası (.SUBCKT satır 82): `TLVx333 IN+ IN- VCC VEE OUT` (datasheet pin eşlemesi: bölüm "Pin eşleme", K04). Alt devreler: BLOCK_DC_H1/H2/H3/S1/S2, AOL_1/2, CLAMP_AMP_HI/LO, CLAWN/CLAWP/CLAW_SRC, CL_SRC, ESD_BB/IN/OUT, FEMT, GR_SRC, IQ_SRC, OL_SENSE, SW_OL, VCM_CLAMP, VNSE, VOS_DRIFT, ZO_SRC (hepsi *_TLVx333 son ekli). .ENDS satır 320 | başlıkta açık "modellenmiyor" listesi YOK; listede olmayan [A] modellenmiyor sayılır. Sıcaklık yalnız Vos drift'te (satır 457-458, `TEMP-27`); "Generic" tip = typ değerler, worst case / tolerans köşesi belirtilmemiş. QSPICE'a uygunluk test edilmedi. PSpice/SPICE3 sözdizimi riski (satır numaraları): `VALUE={...}` ifadeleri ve `LIMIT()`/`IF()` (350,354,358-359,363-364,396,400,...), `TABLE {...} =` (368,382), `PARAMS:` (285-317, 349-463), `PWR()` (425-426,452-453), `TEMP` (458), `.MODEL ... RES (T_ABS=-273.15)` (319), `VSWITCH` modelleri (340,346,404,410,418,443). `.include`/`.lib`/`.param`/`.temp` yok | [R] |
| TLV333IDBVR (model adı TLVx333) | sim\models\TLV333\SBOM967B\TLVx333.LIB (arşiv SBOM967B.ZIP, 11730 bayt, sha256 8e96babed16d35cf509df7a1ab2558e1b62795546ed18b1adc989a96def83c2a; ayrıca .TLD/.TSM TINA dosyaları) | sayfa https://www.ti.com/product/TLV333 ("TLVx333 TINA-TI Spice Model (Rev. B)"); dosya https://www.ti.com/lit/zip/SBOM967 | 2026-10-23 | 31e70542c11b6b87fcd0fb9c3841d9f0e00a49e3cf5168b45232e12cfa574ee6 | düz metin (ASCII, CRLF), şifreli değil; başlık: "Generic", Final 1.2, 06SEP2021, GWL macro model; modellenenler listesi 965C ile aynı (a-y). Düğüm sırası (.SUBCKT satır 78): `TLVx333 IN+ IN- VCC VEE OUT` (datasheet pin eşlemesi: bölüm "Pin eşleme", K04). 965C'den fark (gözle diff, ana alt devre gövdesi aynı): `.MODEL R_NOISELESS` .SUBCKT içinde değil satır 460'ta (965C Final 1.3'te içeri taşınmış), Final 1.3 notları yok. .ENDS satır 315 | 965C ile aynı: açık "modellenmiyor" listesi yok; sıcaklık yalnız Vos drift (satır 453-454 `TEMP-27`); worst case yok. QSPICE'a uygunluk test edilmedi. PSpice/SPICE3 sözdizimi riski 965C ile aynı türden (VALUE/LIMIT/IF 345,349,353-354,358-359,391,395; TABLE 363,377; PARAMS 281-313,344-458; PWR; TEMP; T_ABS satır 460; VSWITCH 335,341,399,405,413). `.include`/`.lib`/`.param`/`.temp` yok | [R] |
| MAX6070AAUT12+T (model adı MAX6070_12, 1,25 V) | sim\models\MAX6070\max6070_12.lib (9403 bayt, 328 satır) | sayfa https://www.analog.com/en/products/max6070.html (Tools & Simulations "MAX6070_12 SPICE Macro Model"); elle indirildi, lisans onayı mühendiste; dosya bağlantısı oturumda görülmedi | 2026-10-23 | 313c35891cbc621a3f783af2ea9c79a104221cc7f3a7431c7fba23e68e1bc5d1 | düz metin (ASCII, CRLF), şifreli değil; Maxim MIT benzeri izin başlığı; "MAX6070_12 is a voltage reference with output voltage of 1.25V", oluşturma 5/2015, v1.0. Düğüm sırası (.SUBCKT satır 34): `MAX6070_12 GND EN FLTR OUTF OUTS IN` (başlık yorumu: OUTF = Voltage Reference Force Output, OUTS = Voltage Reference Sense Output, IN = Supply Input; datasheet pin eşlemesi: bölüm "Pin eşleme", K04). İç alt devre: `.SUBCKT REFt12 1 EN NR 4a 5a 6b` (satır 73) `X_1 GND EN FLTR IN OUTS OUTF REFt12` ile çağrılıyor (satır 70, metin sırası: 4a=IN, 5a=OUTS, 6b=OUTF), ayrıca `.SUBCKT shutdown 10 18 91 cs` (satır 304; `X_en en1 0 EN trig shutdown`, satır 97). Desteklenen (başlık): -40...125 °C aralığında typical performans, load regulation datasheet içinde, line/load transient aşımı datasheet içinde. Önerilen simülatör: SIMETRIX veya SPICE 2G6, "diğer simülatörler çeviri gerektirebilir" | başlıkta açık "Not Supported": Cfilter ve noise modellenmiyor. "Known Discrepancies": Cfilter = 0'da turn-ON settling time spec'i karşılamıyor; line transient undershoot datasheet'ten büyük; 60 Hz PSRR datasheet'ten düşük. Worst-case/tolerans köşesi belirtilmemiş (typical). QSPICE'a uygunluk test edilmedi. PSpice/SPICE3 sözdizimi riski: `value={...}` (184-185, 210-211, 306), `if()` (325), `VALUE`/`table` yorum satırlarında (179-182, kullanılmıyor), `.model ares res (tc1=-2.2e-5)` (172), VSWITCH (100), alt devre adı büyük/küçük harf karışık (`.ends` 328 / `.ENDS`), bölme adı `4a 5a 6b`. `.include`/`.lib`/`.param`/`.temp` yok | [R] |

## Pin eşleme (docs\INTERFACES.md bölüm 10)
| Part | Doc (D<nn>) | Page | Pkg pin no | Datasheet pin name | Model file | .SUBCKT node position | SPICE node name | Label | Note |
|---|---|---|---|---|---|---|---|---|---|
| TLV333IDBVR | D01 | 3 | 1 | OUT | sim\models\TLV333\SBOM965C\TLVx333.LIB | 5 | OUT | [R] | aynı ad; SBOM967B\TLVx333.LIB düğüm sırası aynı (satır 78) |
| TLV333IDBVR | D01 | 3 | 2 | V– | sim\models\TLV333\SBOM965C\TLVx333.LIB | 4 | VEE | [A] | ad konvansiyonu (negatif besleme); K04, mühendis onayı 2026-10-23 [U] |
| TLV333IDBVR | D01 | 3 | 3 | +IN | sim\models\TLV333\SBOM965C\TLVx333.LIB | 1 | IN+ | [A] | ad konvansiyonu (non-inverting); K04; netlist follower testiyle doğrulanır |
| TLV333IDBVR | D01 | 3 | 4 | –IN | sim\models\TLV333\SBOM965C\TLVx333.LIB | 2 | IN- | [A] | ad konvansiyonu (inverting); K04; netlist follower testiyle doğrulanır |
| TLV333IDBVR | D01 | 3 | 5 | V+ | sim\models\TLV333\SBOM965C\TLVx333.LIB | 3 | VCC | [A] | ad konvansiyonu (pozitif besleme); K04, mühendis onayı 2026-10-23 [U] |
| MAX6070AAUT12+T | D02 | 19 | 1 | FILTER | sim\models\MAX6070\max6070_12.lib | 3 | FLTR | [A] | kısaltma; mühendis onayı bekliyor |
| MAX6070AAUT12+T | D02 | 19 | 2 | GND | sim\models\MAX6070\max6070_12.lib | 1 | GND | [R] | aynı ad |
| MAX6070AAUT12+T | D02 | 19 | 3 | EN | sim\models\MAX6070\max6070_12.lib | 2 | EN | [R] | aynı ad |
| MAX6070AAUT12+T | D02 | 19 | 4 | IN | sim\models\MAX6070\max6070_12.lib | 6 | IN | [R] | aynı ad |
| MAX6070AAUT12+T | D02 | 19 | 5 | OUTS | sim\models\MAX6070\max6070_12.lib | 5 | OUTS | [R] | aynı ad (model başlığı: Sense Output) |
| MAX6070AAUT12+T | D02 | 19 | 6 | OUTF | sim\models\MAX6070\max6070_12.lib | 4 | OUTF | [R] | aynı ad (model başlığı: Force Output) |

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
| TLV333IDBVR supply: VS 1.8-5.5 V (Recommended Operating Conditions ve Electrical Characteristics); IQ per amplifier TYP 17 / MAX 28 µA (IO = 0 mA, TA = –40…+125 °C) | [R] | D01 p.6 + D01_p6_recommended.png; D01 p.8 + D01_p8_electrical_b.png (tablo: out\passA\check\D01_critical.md) | bekliyor |
| TLV333IDBVR offset: VOS TYP 2 / MAX 15 µV (VS = 5 V, 25 °C); dVOS/dT TYP 0.02 µV/°C; PSRR TYP 1 / MAX 8 µV/V; long-term stability TYP 1 µV | [R] | D01 p.8 + D01_p8_electrical_a.png | bekliyor |
| TLV333IDBVR input: IB TYP ±70 pA (±150 pA –40…+125 °C), IOS TYP ±140 pA; VCM (V–) – 0.1 … (V+) + 0.1 V; CMRR MIN 102 / TYP 115 dB | [R] | D01 p.8 + D01_p8_electrical_a.png | bekliyor |
| TLV333IDBVR output/stability: AOL MIN 102 / TYP 130 dB; GBW TYP 350 kHz (CL = 100 pF); SR TYP 0.16 V/µs; swing from rail TYP 30 / MAX 70 mV; ISC TYP ±5 mA; CL "See Typical Characteristics", Figure 14 overshoot ≈ 10 % @ 100 pF ([C], eksen 1000 pF'de bitiyor, 10 nF yok) | [R] | D01 p.8 + D01_p8_electrical_b.png; D01 p.11 + D01_p11_overshoot_cl.png | bekliyor |
| TLV333IDBVR Absolute Maximum Ratings: VS 7 V; signal input (V–) – 0.3 … (V+) + 0.3 V, ±10 mA; output short-circuit continuous; Tj 150 °C; ESD HBM ±4000 V, CDM ±1000 V; differential input: not found | [R] | D01 p.6 + D01_p6_absmax_esd.png | bekliyor |
| TLV333IDBVR Pin Functions (DBV): OUT 1, V– 2, +IN 3, –IN 4, V+ 5; SPICE düğüm sırası IN+ IN- VCC VEE OUT ile isim eşlemesi: VCC/VEE ↔ V+/V– "open" | [R] | D01 p.3 + D01_p3_pinfunctions.png | bekliyor |
| MAX6070AAUT12+T output (1.25 V tablosu, VIN = 5.0 V, genel koşul TA = -40…+125 °C): Output Voltage Accuracy A grade ±0.04 % (25 °C); TCVOUT TYP 1.5 / MAX 6 ppm/°C (box method, Note 2); Line Regulation TYP 13 / MAX 100 µV/V (25 °C), MAX 125 (TMIN-TMAX); Load Regulation sink TYP 70 / MAX 150, source TYP 100 / MAX 150 µV/mA; IOUT ±10 mA; Dropout 1.25 V için basılı değil | [R] | D02 p.3 + D02_p3_electrical_a.png; Note 2 D02 p.12 + D02_p12_notes.png (tablo: out\passA\check\D02_critical.md) | bekliyor |
| MAX6070AAUT12+T supply: VIN 2.7-5.5 V; IIN TYP 130 / MAX 200 µA (25 °C), MAX 260 µA (TMIN-TMAX); ISD MAX 6 µA; EN VIH MIN 0.7 x VIN, VIL MAX 0.3 x VIN | [R] | D02 p.3 + D02_p3_electrical_b.png | bekliyor |
| MAX6070AAUT12+T dynamic/long-term: noise 0.1-10 Hz TYP 3.6 µVP-P; wideband (CFILTER = 0.1 µF) TYP 2.5 µVRMS; ripple rejection 60 Hz TYP 100 dB (p.1 "85 dB" genel); turn-on settling TYP 6 ms (p.21 metni 10 ms: çelişki, uzlaşana kadar kullanılmaz); COUT 0.1-10 µF; long-term stability TYP 35 ppm / 1000 h; thermal hysteresis TYP 85 ppm | [R] | D02 p.3 + D02_p3_electrical_a.png, D02_p3_electrical_b.png; D02 p.21 metin | bekliyor |
| MAX6070AAUT12+T Absolute Maximum Ratings: IN, OUTS, EN -0.3...+6 V; OUTF ve FILTER -0.3 V ... lower of (VIN + 0.3 V), +6 V; GNDS to GNDF ±0.3 V; SOT23 347.8 mW; Tj +150 °C; operating -40...+125 °C; ESD ve short-circuit duration: not found | [R] | D02 p.2 + D02_p2_absmax.png | bekliyor |
| MAX6070AAUT12+T Pin Description (SOT23-6, MAX6070): 1 FILTER, 2 GND, 3 EN, 4 IN, 5 OUTS, 6 OUTF; SPICE düğüm sırası GND EN FLTR OUTF OUTS IN ile isim eşlemesi: FLTR ↔ FILTER "open" (kısaltma) | [R] | D02 p.19 + D02_p19_pins.png | bekliyor |
| MAX6070AAUT12+T Ordering Information: p.25'te MAX6070AAUT12+T için tam satır yok, genel satır "MAX6070_AUT_ _+T"; Selector Guide p.24'te tam satır var (FILTER Yes, VOUT 1.25, ACCURACY 0.04 %, TOP MARK +ACPF): AÇIK SORU, mühendis karar verir | [R] | D02 p.25 + D02_p25_ordering.png; D02 p.24 + D02_p24_selector_a.png | bekliyor |
