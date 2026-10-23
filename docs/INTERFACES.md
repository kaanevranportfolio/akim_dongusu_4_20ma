# INTERFACES - modüller arası dosyalar (sözleşme)
Bir modülün `out\` klasörü sonraki modüle salt okunurdur. Değişiklik isteği alıcı modülün `docs\UPSTREAM.md` dosyasına yazılır (madde, kanıt, önerilen değişiklik); sahibi modül kendi biletiyle çözer. Sessiz düzeltme yok.
Her aralık değeri "nominal" mi "en kötü durum" mu olduğunu söyler (alan: `basis`); belirtilmeyen değer kullanılmaz.

## 1. SPEC (00_coordination\SPEC.md)
Gereksinim kimlikleri ve kabul kriterleri K1..K12. Sürüm başlıkta; her rapor spec sürümünü yazar. Spec'te varsayım işareti [A]'dır ("(V)" kullanılmaz).

## 2. Ana komponent adayları (01_secim\out\passA\core_candidates.md)
Sütunlar: MPN (tam ek), üretici, paket, D<nn> p.<n> (SPEC'e karşı kontrol edilen değerler + crop), model kaydı (bölüm 3), tedarikçi kaydı (kaynak URL, tarih, stok, [W]), durum (SEÇİLDİ/VARSAYILAN/AÇIK/DÜŞTÜ). Seçilen ana komponent K<nn> ile DECISIONS.md'ye yazılır.

## 3. Model kaydı (her sim-kritik parça için, modülün FACTS.md "Modeller" tablosunda)
`part` (tam MPN) | `model_file` (sim\models\...) | `source_url` (üretici sayfası) | `retrieved` (tarih) | `sha256` | `represents` (switching/averaged, ne içerir) | `cannot_show` | `pin_order` (düğüm sırası, datasheet pin adlarıyla) | etiket. Model yoksa satır yok ve parça sim-kritikse seçilemez; pasifler için parazitli genel L/C/R serbest (model sayılmaz).

## 4. Gerilim tablosu (02_simulasyon\out\pass1\stress_table.md ve .json)
Satır = referans x köşe. Alanlar: `ref`, `role`, `corner` (besleme/yük/sıcaklık/toleransın adı), `basis` (nominal | worst_case), `V_max`, `V_min` (V), `I_rms`, `I_pk`, `I_avg` (A), `P_avg` (W), `testbench`, `spec_ids` (K..), `label` ([C]), `notes`.
Değerler HAM'dır (derating uygulanmamış). Derating yalnız seçicinin derating profilinde yapılır; ikinci kez uygulanmaz (olay: gözetmenin L1 kuralı toleransı iki kez saydı, bkz. eda lessons).
PDF: aynı md'den check-pdf ile.

## 5. Seçici girdisi (01_secim\out\passB\component_specs.json)
Gerilim tablosundan türetilir; şema: tools\component_selector\schemas\component_specs_schema.json (taşıma bekliyor, 00_coordination/T002). Alan eşlemesi her türetmede `docs\DECISIONS.md` K<nn> ile kaydedilir (hangi stress alanı hangi *_min alanına).

## 6. Seçim çıktısı (01_secim\out\passB\)
`parts_map.json`, `selection_report.md`, `BOM.md` taslağı. BOM sütunları: `ref`, `qty`, `value`, `MPN`, `maker`, `package`, `footprint`, `status`, `datasheet` (D<nn> p.<n>), `model` (bölüm 3 satırı), `source_url` + `retrieved` ([W]), `notes`. Seçicinin eksik vendor verisi ("not in vendor data") PASS sayılmaz: satır VARSAYILAN [A] kalır ve datasheet kontrolü açık madde olur.

## 7. Doğrulama raporu (02_simulasyon\out\pass2\verification_report.md)
K1..K12 için: kriter, köşe, ölçülen değer, sınır, PASS/FAIL, testbench, model SHA256, spec sürümü, etiket. Her raporlanan sonucun devre şeması + sonuç grafiği vardır (kök Figures).

## 8. Dondurma paketi (02_simulasyon\out\freeze\)
`BOM.md` (tüm satırlar SEÇİLDİ veya gerekçeli VARSAYILAN), `FACTS.md` anlık görüntüsü, `PINMAP.md/.pdf`, `KICAD_HANDOFF.md` (net listesi, yerleşim kısıtları, açık maddeler), `sim\INDEX.md`, şekiller, crop'lar. Mühendis commit sonrası `design-freeze-vN` etiketini koyar (Claude etiket koymaz); 03_kicad FACTS.md etiket adını kaydeder. MANIFEST/SHA256 gerekmez: aynı depo, git geçmişi kanıt.

## 9. KiCad çıktıları (03_kicad\)
ERC/DRC JSON ve özetleri `docs\review\`, `docs\FOOTPRINTS.md`, `docs\NETS.md`, kontrol PDF'leri. Fabrikasyon çıktıları yalnız mühendis go'sundan sonra.

## 10. Pin eşleme tablosu (modülün FACTS.md "Pin eşleme" bölümü)
Simülasyon devre şekilleri her terminal için üç ad gösterir (kök Figures kural 2): datasheet pini (DS), SPICE model düğümü (SP), testbench net (TB). DS ve SP bu tablodan gelir; TB testbench .cir dosyasından okunur. Başlık satırı tam olarak şudur, parça başına terminal başına bir satır:

`Part | Doc (D<nn>) | Page | Pkg pin no | Datasheet pin name | Model file | .SUBCKT node position | SPICE node name | Label | Note`

Kurallar: (1) Datasheet sütunları (Doc, Page, Pkg pin no, Datasheet pin name) yalnız belgenin kendisinden gelir, etiket [R]; mühendis crop ile karşılaştırınca [V]. (2) SPICE sütunları (Model file, .SUBCKT node position 1 tabanlı, SPICE node name) model dosyasının .SUBCKT satırı okunarak yazılır, etiket [R]; netlist koşusu doğrularsa [M]. Etiket sütunu: [V], [R], [A] veya [M]. (3) Bilinmeyen hücre "?" yazılır, tahmin edilmez; şekilde taralı kutu ve altbilgide "UNMAPPED TERMINALS: n" olur. (4) Testbench'te olup tabloda olmayan terminal şekil üretiminde WARNING satırıdır. (5) Pin sırası ile .SUBCKT sırası farklı olabilir; bu hata değildir, şeklin göstermek istediği budur. (6) Bölüm yalnız tabloyu içerir; araç (docs\sim\pin_map.py) yalnız bu bölümün ilk tablosunu okur, başlık sütunları farklıysa hata verir. Üretici: docs\sim\pin_map.py `--pin-map <modül>\FACTS.md`.
