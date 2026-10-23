# docs\sim INDEX (template, format only: copy to docs\sim\INDEX.md and add one row per testbench; the rows below are placeholders)

Biçim: her testbench için bir klasör `docs\sim\<testbench>\` (`circuit.svg/.png`, `circuit_layout.py`, `result.svg/.png`, `result.py`). Devre şeması `docs\sim\circuits.py` ile .cir'den, sonuç grafiği `docs\sim\plotkit.py` ile (şablon `result_template.py`) üretilir. Şekildeki çıkış adları (kırmızı kutular) `.save` adlarıdır. Model SHA256: tam değer burada ve modül FACTS.md "Modeller" tablosunda; bu tablodaki değer [C] (dosyayla karşılaştırıldı). Satırlar elle değil, üretimden sonra güncellenir.

Durum sözcükleri: **DRAFT** (devre veya sonuç şekli üretildi, mühendis görmedi; sonuç [R]) | **RUN** (koşu bitti, finish() ve limit denetimleri geçti, mühendis okumadı; sonuç [R]) | **CHECKED** (mühendis devreyi ve sonucu okuyup onayladı; sonuç [C], ancak o zaman karar veya [V] girdisi olabilir) | **DÜŞTÜ** (kullanılmıyor). Etiketler kök CLAUDE.md "Labels": [V] [M] [C] [R] [U] [W] [A]; SPEC kabul ölçütleri K<nn>.

| testbench | amaç | circuit.png | result.png | SPEC K<nn> | model dosyaları + SHA256 | durum | tarih |
|---|---|---|---|---|---|---|---|
| `<testbench>` | tek cümle: ne sınanıyor, hangi koşulda | [circuit](<testbench>/circuit.png) | [result](<testbench>/result.png) | K<nn>, K<nn> (sonuç hangi ölçütleri besliyor; yoksa "-") | `<model.lib>` `<64 hane sha256>` (yoksa "-") | DRAFT / RUN / CHECKED | YYYY-MM-DD |
| `<testbench-2>` | ... | [circuit](<testbench-2>/circuit.png) | yok (henüz üretilmedi) | - | - | DRAFT | YYYY-MM-DD |

Sütun kuralları: (1) `circuit.png` ve `result.png` ikisi de olmadan sonuç raporlanmış sayılmaz (kök Figures kural 1); eksik olan "yok (neden)" yazılır. (2) `SPEC K<nn>`: sonuç limitleri yalnız SPEC'ten ya da [A] etiketiyle gelir; [A] limit olan satırda sütuna "[A]" eklenir. (3) `model dosyaları`: yalnız üretici modeli, byte-exact; model yoksa satır "model yok: DUR" notuyla DRAFT'ta kalır. (4) `tarih`: koşu veya son üretim tarihi (`--date` argümanı, saat okunmaz).
