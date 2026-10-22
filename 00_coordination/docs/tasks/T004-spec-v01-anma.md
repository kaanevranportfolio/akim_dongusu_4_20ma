# T004 - SPEC v0.1 anmalarını v0.2 yap
Durum: BİTTİ
## İstek
Goal: in 00_coordination\SPEC.md replace three leftover version mentions. Edit only: this ticket file and 00_coordination\SPEC.md. Everything else is read-only. Never commit / push / amend / delete. Engineer approved (ref 00_coordination/T003 follow-up).
Steps:
1. Line 30: "**Kapsam dışı (v0.1):**" -> "**Kapsam dışı (v0.2):**".
2. Line 94 (ESD row): "v0.1'de simülasyon kapsamı dışı" -> "v0.2'de simülasyon kapsamı dışı".
3. Line 58 (Arıza akımı row): "v0.1'de zorunlu değil" -> "v0.2'de zorunlu değil".
4. Do NOT touch line 146 (section 9 v0.1 history row), line 136 (NAMUR 3,6 mA / 21 mA), or any other line.
5. Check: grep -n "v0.1" SPEC.md must return only line 146.
Output: at most 3 lines: lines changed, grep result, open issues.
## Sonuç
Değişen satırlar: 30, 58, 94 (v0.1 -> v0.2). Satır 136 ve 146'ya dokunulmadı.
Grep `v0.1` SPEC.md: yalnız satır 146.
Açık sorun yok.
