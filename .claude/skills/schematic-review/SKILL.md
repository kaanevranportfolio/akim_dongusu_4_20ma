---
name: schematic-review
description: Run ERC, export the netlist and compare it with the upstream (freeze) net list, BOM and PINMAP. Triggers - ERC, netlist, schematic review, şematik.
---

# schematic-review

Bu dosyada proje adı, yol veya sayı yazılı değildir. Şematik dosyası ve kicad-cli yolu bu projenin `CLAUDE.md` "Yollar" bölümünden okunur; yoksa mühendise sor. Net adları, pin atamaları ve parça adları `FACTS.md`, `docs\NETS.md`, `..\02_simulasyon\out\freeze\KICAD_HANDOFF.md`, `..\02_simulasyon\out\freeze\BOM.md`, `..\02_simulasyon\out\freeze\PINMAP.md` dosyalarından okunur; değer yoksa [A] işaretle, hafızadan doldurma. `.kicad_sch` dosyası asla düzenlenmez ve bağlama bütün olarak okunmaz.

Adımlar:
1. ERC: `kicad-cli sch erc --format json --severity-all --exit-code-violations -o docs\review\erc.json <şematik>`. Çıktıyı özetle (tür, adet); her uyarı için gerekçe iste.
2. Netlist: `kicad-cli sch export netlist --format kicadsexpr -o docs\review\<proje>.net <şematik>`.
3. BOM: `kicad-cli sch export bom` ile referans, değer, footprint, MPN alanlarını al; `..\02_simulasyon\out\freeze\BOM.md` ile satır satır karşılaştır (referans, MPN, durum). Eksik, fazla ve farklı satırları listele.
4. Netleri ve pin atamalarını `..\02_simulasyon\out\freeze\KICAD_HANDOFF.md` net listesi ve `..\02_simulasyon\out\freeze\PINMAP.md` alias'larıyla karşılaştır (sembol pin adı/numarası PINMAP'te basılı yazımla). Her IC besleme pininin aynı netteki decoupling kondansatörünü kontrol et.
5. Farkları etiketli tabloyla raporla ([R]); upstream (freeze)'taki bir hata `docs\UPSTREAM.md`'ye, bu projenin eksiği `HANDOFF.md` açık maddesine yazılır. Çok sütunlu rapor tablosu PDF olarak da üretilir (check-pdf skill; kök CLAUDE.md "Language", Human reading): her fark satırında ilgili şematik bölgesinin crop'u (`kicad-cli sch export svg/pdf` çıktısından kırpılmış PNG) iç bağlantılı Crop sütunuyla verilir.

Doğrular: ERC temiz (veya her uyarı gerekçeli), netlist = upstream (freeze), BOM = upstream (freeze).
