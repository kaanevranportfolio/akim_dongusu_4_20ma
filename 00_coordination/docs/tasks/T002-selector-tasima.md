# T002 - component selector tasima
Durum: BİTTİ
## İstek
Run only after T001 is BİTTİ. Goal: move the component selector into the pipeline as code only, with output paths and credentials handled safely. Never commit / push / amend / delete. Never read or print .env, .digikey_cache or any token/certificate content. Edit only files under <pipeline>\tools\component_selector\ (new) and this ticket.
Steps:
1. Find which copy is current: C:\component_selector_v1 vs C:\Users\kaane\LTSpice_Projects\component_selector_v1 (the 2026-10-21 log names the second path). Compare file names, sizes and SHA-256 of the .py, schemas\, config\, tests\ files; report differences in a table; do not choose silently.
2. Copy the current copy's code only: select_components.py, ranker.py, derating_rules.py, validate_specs.py, search_digikey.py, search_nexar.py, schemas\, config\, tests\, requirements.txt. Do NOT copy .env, .digikey_cache\, *.log, parts_map.json, reference_parts_map.json, selection_report.md, __pycache__, .pytest_cache, automation_test.mp4. Add tools\component_selector\.gitignore listing .env, .digikey_cache/, *.log.
3. Parametrize outputs: add --out DIR (default: current directory) so parts_map.json and selection_report.md are no longer written next to the script; keep all other behaviour unchanged. Add --reference-map PATH if reference_parts_map.json is needed (it is read today from the script folder).
4. Missing vendor data: wherever a check passes with a note like "not in vendor data - verify datasheet", make it report status ASSUMED_VERIFY (not PASS) in parts_map.json and in the report summary; list those rows under "Manual verification required" as today. Show the diff of this change in the Sonuç.
5. Run the existing pytest tests (no network). Report pass/fail counts. Do not run the DigiKey search (OAuth needs the engineer).
6. Write tools\component_selector\README.md: inputs (component_specs.json, schema), outputs, how the engineer authorizes DigiKey, where credentials must live (outside the repo, folder named in .gitignore), and the provider-plugin plan (DigiKey now; Octopart/Nexar, LCSC, JLCPCB later, benchmark after the pipeline is running).
7. Output: table of at most 8 lines plus open issues (at most 5 lines).
## Sonuç
T001 BİTTİ olduğundan çalıştırıldı.

| # | Kontrol | Sonuç | Değer / mesaj |
|---|---|---|---|
| 1 | Güncel kopya | PASS | C:\Users\kaane\LTSpice_Projects\component_selector_v1 YOK (LTSpice_Projects klasörü bile yok; C: derinlik 3'te başka kopya da yok). Tek kopya C:\component_selector_v1; fark tablosu çıkmadı, sessiz seçim yok. Mühendis ikinci yolu başka diskte/adla biliyorsa söylesin |
| 2 | Kod kopyası | PASS | 7 .py/.txt + schemas\ + config\ + tests\ (fixtures dahil); .env, .digikey_cache, *.log, parts_map, reference_parts_map, selection_report, automation_test.mp4 kopyalanmadı. .gitignore: .env, .digikey_cache/, *.log (+ __pycache__/, .pytest_cache/) |
| 3 | --out / --reference-map | PASS | select_components.py: parts_map.json, selection_report.md, selection.log artık --out (varsayılan cwd) altına; --reference-map yoksa betik klasörü varsayılanı. `--help` doğrulandı; arama koşulmadı |
| 4 | ASSUMED_VERIFY | PASS | "not in vendor data" ile geçen kural artık ASSUMED_VERIFY; parts_map `derating_status` ASSUMED_VERIFY, rapor özetinde ayrı satır ve ⚠ işareti, "Manual verification required" listesi aynı. Ağsız sahte aday denemesiyle doğrulandı. `overall` PASS/FAIL kalır (ranker/test uyumu). Diff aşağıda |
| 5 | pytest | PASS | 27 passed, 0 failed (ağ yok; scratchpad venv, requirements.txt'ten pytest/colorama/jsonschema/dotenv/requests) |
| 6 | README.md | PASS | girdi, çıktı, DigiKey yetkilendirme, kimlik bilgisi yeri, sağlayıcı planı |
| 7 | Yazma sınırı | PASS | Yalnız tools\component_selector\ ve bu bilet; ayrıca scratchpad (venv). |

Diff (v1 -> tools; satır sonu farkları yok sayıldı, --strip-trailing-cr). derating_rules.py:
```
+def _rule_status(passed: bool, note: str) -> str:
+    """FAIL, ASSUMED_VERIFY (passed only because vendor data is missing) or PASS."""
+    if not passed:
+        return "FAIL"
+    if "not in vendor data" in note.lower():
+        return "ASSUMED_VERIFY"
+    return "PASS"
 ...
-        "status":   "PASS" if passed else "FAIL",
+        "status":   _rule_status(passed, note),
 ...
         "overall":      "PASS" if not failed else "FAIL",
+        "assumed_rules": [r["rule"] for r in rules if r["status"] == "ASSUMED_VERIFY"],
```
select_components.py (durum kısmı; yol/--out kısmı kodda, yaklaşık +33 satır):
```
-            "derating_status": "PASS",
+            "derating_status": ("ASSUMED_VERIFY"
+                                if selected.get("_derating", {}).get("assumed_rules")
+                                else "PASS"),
 ...
+                if rule.get("status") == "ASSUMED_VERIFY":
+                    assumed_rules += 1
-                if "verify" in rule.get("note", "").lower():
+                if rule.get("status") == "ASSUMED_VERIFY" or "verify" in rule.get("note", "").lower():
 ...
+    lines.append(f"| ASSUMED_VERIFY (not PASS) rules | {assumed_rules} |")
-                status = "✅" if "PASS" in d else "❌"
+                status = "⚠" if "ASSUMED_VERIFY" in d else ("✅" if "PASS" in d else "❌")
```

Açık sorunlar:
- tools\component_selector\tests\__pycache__ kopyalama sırasında girdi (silme yasak olduğu için kalıyor); gitignore'da. Mühendis elle silebilir.
- search_digikey.py token önbelleğini hâlâ betik klasöründe (.digikey_cache) tutuyor ve load_dotenv() kullanıyor; "kimlik bilgisi repo dışında" için ortam değişkeni önerildi, kod değişmedi (istek dışı). validate_specs.py ve ranker/search_*.py `__main__` blokları hâlâ betik klasörünü varsayılan alıyor; select_components yolundan etkilenmez.
- component_specs.json bu klasörde yok; her koşuda --specs verilmeli (K<nn> alan eşlemesi, INTERFACES bölüm 2 henüz uygulanmadı).
- Windows konsolunda Unicode için PYTHONIOENCODING=utf-8 gerekiyor (README'de).
- search_nexar.py kopyalandı ama hatta bağlı/test edilmedi.
