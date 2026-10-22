# Açılış mesajları - her modül için bir chat
Sıra ve kural: önce 00_coordination chat'i açılır. Diğer chat'ler önkoşulları sağlanınca açılır (aşağıda yazılı); önkoşul yokken açılırsa chat yalnızca okur ve bekler.
Her chat: aynı claude.ai projesinde yeni chat, pipeline klasörü bağlı, mesaj = kod bloğunun içi. Chat uzun ömürlüdür; bağlam dolunca HANDOFF.md güncel olduğu için aynı mesajla yenisi açılır.

## 1. 00_coordination (şimdi)
```
Module: 00_coordination. Folder: C:\pipelines\akim_dongusu_4_20ma (connected).
Read the root CLAUDE.md, then 00_coordination\CLAUDE.md, HANDOFF.md, docs\RULE_LEDGER.md (skim) and SPEC.md (spec v0.1, draft, read-only for you).
Report in Turkish, about 10 lines: state, open items, decisions I must take.
First work: (1) go through the findings in HANDOFF open item 1 and propose the SPEC v0.2 changes as a list (old text -> new text); do not edit SPEC.md, I approve first. (2) Ask whether VS Code is idle and, if so, give me the one-liner for 00_coordination\docs\tasks\T001. Write nothing before I answer.
```

## 2. 01_secim (SPEC v0.2 onaylı ve T001 BİTTİ olunca)
```
Module: 01_secim, pass A. Folder: C:\pipelines\akim_dongusu_4_20ma (connected).
Read the root CLAUDE.md, then 01_secim\CLAUDE.md, HANDOFF.md, FACTS.md, docs\INTERFACES.md (sections 2, 3, 5, 6) and ..\00_coordination\SPEC.md (read-only). Values in SPEC marked (V) are assumptions [A].
First work: turn the SPEC constraints into a candidate filter for the core part, each line with its SPEC id. Ask me at most 10 questions, grouped, each with a proposed default marked [A]. Do not name MPNs from memory: any MPN you suggest is a candidate until it is seen in its own datasheet. Write the first ticket for VS Code (document intake and candidate search) only after I answer.
```

## 3. 02_simulasyon (ana komponent seçildi ve modeli kaydedildi olunca)
```
Module: 02_simulasyon, pass 1 (theory). Folder: C:\pipelines\akim_dongusu_4_20ma (connected).
Read the root CLAUDE.md, then 02_simulasyon\CLAUDE.md, HANDOFF.md, FACTS.md, docs\INTERFACES.md (sections 3, 4, 7, 8), ..\00_coordination\SPEC.md and ..\01_secim\out\passA (read-only).
First work: list the corners from SPEC section 4 and the acceptance criteria K1..K12, and propose the pass-1 testbench set (real model for the core part only, everything else ideal or ideal with stated parasitics) with the stress table columns it will fill. Ask me what you need; no ticket before my answer. Every simulation result comes with its circuit figure.
```

## 4. 03_kicad (dondurma etiketi konulunca)
```
Module: 03_kicad. Folder: C:\pipelines\akim_dongusu_4_20ma (connected).
Read the root CLAUDE.md, then 03_kicad\CLAUDE.md, HANDOFF.md, FACTS.md and the freeze package ..\02_simulasyon\out\freeze (read-only).
First work: write the ticket for the module-intake skill (file list, BOM status counts, BOM vs PINMAP vs FACTS consistency) and tell me what I must create in KiCad (project file) before schematic work. You never edit .kicad_* files.
```
