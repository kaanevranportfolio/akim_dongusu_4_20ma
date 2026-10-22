---
name: pcb-review
description: Run DRC and check the board against the upstream (freeze) layout constraints. Triggers - DRC, PCB review, yerleşim, layout, gerber.
---

# pcb-review

Bu dosyada proje adı, yol veya sayı yazılı değildir. PCB dosyası ve kicad-cli yolu `CLAUDE.md` "Yollar" bölümünden; kısıtlar `FACTS.md` "Yerleşim kısıtları" ve `..\02_simulasyon\out\freeze\KICAD_HANDOFF.md` dosyasından okunur. `.kicad_pcb` asla düzenlenmez ve bağlama bütün olarak okunmaz.

Adımlar:
1. DRC: `kicad-cli pcb drc --format json --severity-all --exit-code-violations -o docs\review\drc.json <pcb>`; tür ve adet özeti, her ihlal için gerekçe iste (unconnected, clearance, courtyard, silk).
2. Kısıt kontrolü: FACTS kısıtlarını tek tek (kart boyutu ve katman sayısı, şönt Kelvin yönlendirmesi, gate direnci yerleşimi, güç parçalarının ısı alanı, bypass yakınlığı, vb.) kicad-cli dışa aktarımları veya salt okunur betikle ölç; her satır PASS/FAIL + değer + etiket [C].
3. Footprint durumu: `docs\FOOTPRINTS.md`'de [V] olmayan footprint kartta kullanılıyorsa FAIL.
4. Üretim çıktıları (gerber, drill, BOM, pick-and-place) yalnız mühendisin açık onayından sonra üretilir; üretildiğinde `kicad-cli pcb export` çıktıları `docs\review\fab\` altına ve dosya listesi rapora yazılır.
5. Rapor tablosu (kısıt kontrolü ve DRC bulguları) PDF olarak da üretilir (check-pdf skill): her satırın yanında ilgili kart bölgesinin crop'u (`kicad-cli pcb export svg/pdf` çıktısından kırpılmış PNG, `docs\review\crops\`) ve iç bağlantılı Crop sütunu bulunur; DRC işaretçisi olan satırda işaretçi konumu crop'ta görünür. bulgular HANDOFF açık maddesi, upstream (freeze) kaynaklı olanlar `docs\UPSTREAM.md`.

Doğrular: DRC temiz (veya gerekçeli), kısıtlar sağlanıyor, footprint'ler [V].
