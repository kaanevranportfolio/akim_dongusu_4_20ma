# tools - pipeline ortak araçları (tek kopya)
Sahibi: 00_coordination (değişiklik biletle). Kaynaklar C:\eda\tools ve KiCAD_Projects; bu kopyalar 2026-10-22'de alındı.
| Dosya | Ne | Kaynak | Değişiklik |
|---|---|---|---|
| run_sim.ps1 | QSPICE koşucusu (canary, .save kapısı, çıkış kodları, -CleanRaw) | C:\eda\tools\run_sim.ps1 | yalnız yorum satırları farklı (T024: yol örneği ve canary notu; davranış aynı, byte-exact DEĞİL); -SimDir pipeline köküne göredir. Byte-exact kopyalar: qraw.py, qraw_export.py (sha256 legacy ile aynı). canary_rc.cir: netlist satırları aynı, başlık yorumu T029'da değişti (modül kopyaları eski başlıkta kalabilir) |
| qraw.py, qraw_export.py | .qraw okuma ve CSV dışa aktarma | C:\eda\tools | yok (byte-exact kopya) |
| canary\canary_rc.cir | sayısal canary testbench | C:\eda\programmable_electronic_load\sim\canary_rc.cir | yok; her modülün sim\ klasörüne kopyalanır |
| check_pdf.py | md tablosu -> crop bağlantılı PDF | KiCAD_Projects\...\docs\check_pdf.py | ROOT = cwd (modül), varsayılan crop klasöründe handoff -> freeze\figures |
| component_selector\ | parça seçici | C:\component_selector_v1 | taşınmadı: 00_coordination/T002 |

Bağımlılıklar: Python 3.12, pymupdf, reportlab, matplotlib; QSPICE (C:\Program Files\QSPICE); kicad-cli 10.0.
