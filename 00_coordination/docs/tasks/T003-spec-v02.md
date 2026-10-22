# T003 - SPEC v0.2 uygulama
Durum: BİTTİ
## İstek
Goal: apply the engineer-approved v0.2 changes to 00_coordination\SPEC.md (spec v0.1 -> v0.2). Edit only: this ticket file and 00_coordination\SPEC.md. Everything else is read-only. Never commit / push / amend / delete. Do not change any value other than those listed.
Steps (exact old -> new, Turkish text as written in SPEC.md):
1. Header table: "Sürüm" v0.1 -> v0.2; "Tarih" -> 2026-10-22 (unchanged date is fine, use today's date from the system); "Durum" -> "Taslak, mühendis onayı bekliyor".
2. Label: replace every "(V)" with "[A]" in the whole file (sections 2-6 tables). Keep the label on every row; remove none. Rewrite the "Gösterim" note to: "**Gösterim:** Sonunda **[A]** olan değerler varsayımdır, onaylanana ya da düzeltilene kadar geçicidir. Onaylanan değerler etiketsiz yazılır." (note: do not write "(V)" anywhere).
3. Section 4, row "Vericinin minimum çalışma gerilimi": "≤ 7 V (V)" -> "≤ 7 V, ters polarite koruması düşümü dahil, döngü terminallerinde [A]".
4. Section 4, test matrix first row: "12 V | 250 Ω (en kötü durum)" -> "12 V | 220 Ω (en kötü durum; 12 V − 4,4 V = 7,6 V, 7 V'a göre marj 0,6 V)". Other rows unchanged.
5. Section 4, row "Simülasyonda alıcı modeli": "250 Ω şönt direnç (+ kablo direnci)" -> "250 Ω şönt direnç (+ kablo direnci); 12 V satırında 220 Ω".
6. K5 (section 7): "Besleme taraması 12–36 V, 250 Ω" -> "Besleme taraması 12–36 V, R_toplam = 220 Ω".
7. K7 (section 7): "Akım 3,8–21 mA içinde, hasar yok" -> "Akım 3,8–20,5 mA içinde, hasar yok".
8. Section 8, item 2: append " Ters polarite koruması düşümü bu hedefin içindedir; 12 V / 220 Ω satırında marj 0,6 V. Koruma düşümü 01_secim A'nın ilk sorusudur."
9. Section 8, item 5: "01_core" -> "01_secim".
10. Section 9: add row "| v0.2 | <today> | (V) -> [A] etiketi; K7 3,8–20,5 mA; 12 V satırı 220 Ω ve K5 buna göre; koruma düşümü 7 V hedefine dahil; 01_core -> 01_secim |".
11. Check: grep for "(V)", "01_core", "21 mA", "250 Ω (en kötü" in SPEC.md must return nothing except the section 9 row text and the Gösterim-free file; report the grep result.
Output: table, at most 8 lines (change | done | line number), then at most 3 lines of open issues. No full file dump.
## Sonuç
| Değişiklik | Yapıldı | SPEC.md satırı |
|---|---|---|
| 1. Sürüm v0.2, Tarih 2026-10-22 (sistem tarihi, zaten aynı), Durum "Taslak, mühendis onayı bekliyor" | evet | 5-7 |
| 2. (V) -> [A] (26 satır, hiçbir etiket silinmedi) + Gösterim notu yeniden yazıldı | evet | 10, 38-105 |
| 3. Vericinin minimum çalışma gerilimi | evet | 68 |
| 4. Test matrisi 12 V satırı 220 Ω (marj 0,6 V) | evet | 78 |
| 5. Simülasyonda alıcı modeli "...; 12 V satırında 220 Ω" | evet | 71 |
| 6-7. K5 "R_toplam = 220 Ω"; K7 "3,8–20,5 mA" | evet | 119, 121 |
| 8-9. Bölüm 8 madde 2 eklemesi; madde 5 01_core -> 01_secim | evet | 135, 138 |
| 10. Bölüm 9 v0.2 satırı | evet | 147 |

Grep ("(V)", "01_core", "21 mA", "250 Ω (en kötü"): yalnız iki satır döndü: 147 (Bölüm 9 v0.2 satırı, beklenen: "(V)" ve "01_core" metni) ve 136 ("NAMUR 3,6 mA / 21 mA" arıza akımı sorusu, K7 ile ilgisiz, dokunulmadı). "250 Ω (en kötü" ve gövdede "(V)" kalmadı. Dosyanın satır sonu stili korundu.

Açık sorunlar:
- Satır 136'daki 21 mA (NAMUR arıza akımı) bilet kapsamı dışında; K7'nin 20,5 mA'ine göre tutarlılık gerekiyorsa mühendis karar versin.
- Satır 30 "Kapsam dışı (v0.1)" ve 94 "v0.1'de simülasyon kapsamı dışı" sürüm anmaları değiştirilmedi (bilet listesinde yok).
