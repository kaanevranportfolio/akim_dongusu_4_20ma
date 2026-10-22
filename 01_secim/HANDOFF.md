# HANDOFF - 01_secim
Güncelleme: 2026-10-22 (DigiKey smoke temizliği, 01_secim/T006)

## Durum
- Geçiş: A (başlamadı). Girdi: ..\00_coordination\SPEC.md (v0.2, onay bekliyor).
- Seçici tools\component_selector altında; DigiKey erişimi digikey_v4.keyword_search üzerinden, token 200 ve keyword search 200 [M].

## Açık maddeler (nasıl kapanacak)
1. Geçiş A: SPEC onaylandıktan sonra ana komponent aday filtresi.
2. İlk sorguda Products=[] nedeni (fazla spesifik sorgu) [A]: out\passA\digikey_smoke altındaki T005 çıktıları (result_1..4.json, fields_table.md, found_parts.md) mevcut; mühendisin konsol satırlarını bildirmesiyle ve sonuçların okunmasıyla kapanır. found_parts.md [W] kısa listedir, aday değildir.
3. 401 "Invalid clientId" nedeni kanıtlanmadı [A] (Sandbox kimliği canlı host'ta ve/veya eski V3 kütüphane yolu); Production + v4 anahtarlarıyla token 200. Kapanış: 00_coordination bulgusuna bağlı, gerekmedikçe araştırılmaz.
4. Mühendis silecekler (ajan silmez): out\passA\digikey_smoke\run.log, out\passA\digikey_smoke\result.json (eski, boş yanıt); repo dışı: Temp\vdk\ca_bundle.pem, scratchpad'deki eski venv_digikey (durumları doğrulanmadı).
5. 00_coordination'a istek: out\passA\digikey_smoke\result*.json, run.log, *.tmp gitignore'a (01_secim/T006 Sonuç); README'ye Windows/Python 3.12 notları.

## Açık kararlar
(yok; kararlar docs\DECISIONS.md içinde K<nn> ile)

## Commit'e hazır yollar
(commit yalnız koordinatör biletiyle) 01_secim\FACTS.md, HANDOFF.md, docs\DEVLOG.md, docs\lessons.md, docs\tasks\T001-T006, out\passA\digikey_smoke\smoke_run.py, smoke_spec.json, fields_table.md, found_parts.md. Gitignore'a girmesi istenenler (result*.json, run.log) hariç.

## Sonraki oturumun ilk görevi
SPEC onayı sonrası geçiş A: aday filtresini SPEC kimlikleriyle yaz (planner). Önce T005 çıktılarının okunması.
