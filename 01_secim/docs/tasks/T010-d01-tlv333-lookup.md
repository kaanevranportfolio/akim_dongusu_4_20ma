# T010 - d01-tlv333-lookup
Durum: BİTTİ
## İstek
Goal: extract the critical values of TLV333IDBVR from D01 (docs\ref\D01_tlv333.pdf) as a check table for the engineer, every row with D01 page and a crop PNG. Values are [R] until the engineer compares them with the crop. Use the datasheet-lookup skill (variant gate already passed, 00_coordination/T021) and the check-pdf skill for the PDF.
Session folder: C:\pipelines\akim_dongusu_4_20ma\01_secim . Lookup limit: at most 60 lines of document text per call; render a page as an image only for crops.
Variant: TLV333 column / row only (DBV 5-pin package, I grade -40...125 C). If the table is shared with TLV2333 / TLV4333, use the TLV333 values and say so in the Note column. Part: TLV333IDBVR. Pin names go to the table exactly as printed in Pin Functions.
Values to extract (each with test condition as printed, e.g. VS, TA, VCM, RL; MIN / TYP / MAX / UNIT):
1. Supply: Supply voltage range (Recommended Operating Conditions or Electrical Characteristics), Quiescent current per channel IQ (TYP and MAX, over temperature, state the temperature).
2. Offset: Input offset voltage VOS (TYP, MAX), offset drift dVOS/dT, long-term drift if printed.
3. Input: Input bias current IB, input offset current IOS, Common-mode voltage range VCM (state value at VS = 5 V and 3.3 V, and whether it includes the negative rail), CMRR, PSRR.
4. Output: Output swing from rail, short-circuit current, open-loop gain AOL, Gain bandwidth GBW, Slew rate, Settling time if printed.
5. Stability: Capacitive load drive / unity-gain stability statement and any figure number for it (page only, crop only if a table or figure states a limit).
6. Absolute Maximum Ratings: supply voltage, input voltage (signal input pins), differential input, input current, output short-circuit duration, operating / junction / storage temperature, ESD ratings if in the same table.
7. Recommended Operating Conditions: temperature range, supply range.
8. Pin Functions table: pin number, pin name, type, description for DBV package (IN+, IN-, OUT, V+/V-, as printed). Add a line comparing these names with the SPICE node order from 01_secim FACTS.md (`TLVx333 IN+ IN- VCC VEE OUT`): which datasheet pin maps to which node by name only; mark any mapping that needs a decision as "open".
Steps:
1. Find each value (text search, then confirm on the page). Record D01 page (PDF page number, plus printed page if different).
2. Crop each table as PNG, named D01_p<page>_<topic>.png (e.g. D01_p6_electrical.png), into 01_secim\docs\figures\. Each crop shows the table header row (MIN / TYP / MAX / UNIT), the parameter rows used and the test-condition column. For Pin Functions, crop the full table.
3. Write 01_secim\out\passA\check\D01_critical.md: columns Parametre | Symbol | Condition | MIN | TYP | MAX | UNIT | D01 p. | Crop | Label | Note. One table per section (supply, offset, input, output, stability, Absolute Maximum Ratings, Pin Functions). A row that needs checking never has an empty Crop cell. Label [R] for all. Not found = "not found", never guessed.
4. Add a short "G-filtre karşılaştırması" table (Turkish, after the data tables): G1 supply current, G2 common-mode range includes GND, G3 VOS + drift <= 2 mV, G4 IB, G5 stability with 10 nF, each as geçti / geçmedi / bilinmiyor with the D01 row it rests on (FACTS.md Gereksinimler defines G1-G5). No decision, only the comparison.
5. Generate the PDF with the check-pdf skill from the markdown: 01_secim\out\passA\check\D01_critical.pdf (landscape A4, large text, clickable Crop column). Never edit the PDF by hand.
6. FACTS.md: re-read it immediately before editing; add one row per critical value group to the table "Kritik değerler (mühendis kontrolü bekleyen)" only (value | [R] | D01 p. + crop name | Kontrol: bekliyor). Touch no other row.
7. /closeout: update HANDOFF.md and docs\DEVLOG.md (re-read before editing). No commit.
May edit: this ticket; new files under 01_secim\docs\figures\ and 01_secim\out\passA\check\; FACTS.md (that one table only); at /closeout HANDOFF.md and docs\DEVLOG.md. Everything else read-only. Never commit / push / amend / delete. Do not run QSPICE or any simulation. Network, TLS or certificate errors: stop and ask the engineer; never read or export the certificate store, build CA bundles, set CA environment variables or disable TLS verification (root CLAUDE.md Safety).
Result: at most 8 lines: number of rows, crops, rows not found, anything unclear, paths of the md and PDF.
## Sonuç
1. Tablo: out\passA\check\D01_critical.md, 8 tablo bölümü + G-filtre karşılaştırması; 53 veri satırı (supply 4, offset 5, input 8, output 7, stability 3, Absolute Maximum Ratings/ESD/Recommended 12, Pin Functions 5, düğüm eşlemesi 5, G1-G5 5 = 54 satır; md'de 62 "| " satırı başlık ve ayırıcıları da sayar).
2. PDF: out\passA\check\D01_critical.pdf (check-pdf, 18 sayfa, 6 crop, 0 eksik; landscape A4).
3. Crop'lar (docs\figures\): D01_p8_electrical_a.png, D01_p8_electrical_b.png, D01_p6_absmax_esd.png, D01_p6_recommended.png, D01_p3_pinfunctions.png, D01_p11_overshoot_cl.png.
4. not found: Absolute Maximum Ratings'te differential input voltage satırı yok; Electrical Characteristics'te birçok MIN/MAX hücresi yalnız TYP basılı (IB, IOS, dVOS/dT, GBW, SR, ISC); settling time için tablo satırı yok (yalnız Figure 13, sayısal çıkarılmadı).
5. Belirsiz: IQ satırında TYP 17 ve MAX 28 aynı koşulla (TA = –40…+125 °C) basılı, TYP'nin 25 °C olup olmadığı yazmıyor; VCM için VS = 5 V ve 3.3 V ayrı değer yok, tek ifade (hesaplanan değerler [C]); Figure 14 grafik okuması [C], 10 nF eksen dışı. Pin adı eşlemesinde VCC/VEE ↔ V+/V– "open" bırakıldı.
6. G-filtre (karar değil): G1 geçti (MAX 28 µA), G2 geçti, G3 geçti [C] (≈ 16 µV), G4 TYP'ye göre geçti (MAX yok), G5 bilinmiyor.
7. Yan bulgu (not): op-amp VS MAX 5.5 V (Absolute Maximum Ratings 7 V); SPEC besleme 12-36 V, bu yüzden yerel ray gerekli.
8. FACTS.md "Kritik değerler" tablosuna 6 satır eklendi (hepsi [R], Kontrol: bekliyor). Tüm değerler [R]: mühendis crop'larla karşılaştırınca [V] olur.
