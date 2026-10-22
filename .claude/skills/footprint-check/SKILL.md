---
name: footprint-check
description: Compare a KiCad footprint with the exact part's land pattern. Triggers - footprint, land pattern, pad, pin 1, exposed pad.
---

# footprint-check

Bu dosyada parça, yol veya sayı yazılı değildir. Tam parça, varyant ve paket `FACTS.md`'den; PCB dosyası `03_kicad\CLAUDE.md` "Yollar" bölümünden okunur; yoksa mühendise sor. Değer yoksa [A] işaretle, hafızadan doldurma.

Adımlar:
1. `FACTS.md` -> tam parça, varyant, paket. Eksikse dur ve [A] işaretle.
2. `datasheet-lookup` -> land pattern / paket çizimi (şekil için tek kırpılmış görüntü).
3. Footprint pad'lerini `.kicad_pcb` dosyasından **salt okunur** oku (asla düzenleme; kartı mühendis KiCad GUI'de değiştirir).
4. Karşılaştır: pad sayısı, aralık (pitch), pad boyutu, pin 1 konumu ve numaralama, açıkta/termal pad boyutu ve neti.
5. Etiketli tablo ver; her uyumsuzluk HANDOFF.md'ye açık madde olur; doğrulanan değerler FACTS.md'ye `[V]` + sayfa ile girer.

Doğrular: footprint geometrisini ve pin eşlemesini tam parçanın belgesine göre.
