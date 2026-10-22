# T009 - SPEC v0.2 onay satırı
Durum: BİTTİ
## İstek
Goal: record the engineer's approval of SPEC v0.2 in 00_coordination\SPEC.md. Edit only: this ticket file and 00_coordination\SPEC.md. Everything else is read-only. Never commit / push / amend / delete. Do not change any value or label.
Steps:
1. Header table row "Durum": "Taslak, mühendis onayı bekliyor" -> "Onaylı (mühendis, 2026-10-22); Bölüm 8 açık soruları 01_secim A'da teyit edilir".
2. Section 9: add row "| v0.2 onayı | 2026-10-22 | Mühendis onayladı (docs\DECISIONS.md K01) |" after the v0.2 row.
3. Check: `git diff --stat SPEC.md` shows only these two places (show the diff, at most 10 lines).
Output: at most 3 lines.
## Sonuç
SPEC.md: Durum satırı "Onaylı (mühendis, 2026-10-22); ..." yapıldı, Bölüm 9'a "v0.2 onayı" satırı eklendi.
`git diff --stat SPEC.md`: 2 ekleme, 1 silme, yalnız bu iki yer (değer/etiket değişmedi).
Açık: yok.
