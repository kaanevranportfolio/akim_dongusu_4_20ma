# 02_simulasyon - QSPICE (modül CLAUDE.md)
Kök yöntem: ..\CLAUDE.md geçerli. Burada yalnız bu modüle özgü olanlar var. Çelişkide bu dosya kazanır (Safety ve settings.json hariç).

## Rol
Geçiş 1 (teori): ana komponent gerçek vendor modeliyle, diğer her şey teorik (ideal kaynak, ideal veya parazitli L/C/R). Amaç: her referansın maruz kalacağı V/I/P değerleri -> out\pass1\stress_table (HAM, köşe başına, nominal/worst_case etiketli).
Geçiş 2 (doğrulama): seçilmiş parçalar ve modelleri; SPEC K1.. kriterleri; out\pass2\verification_report.md; mühendis onayından sonra out\freeze\ dondurma paketi (docs\INTERFACES.md bölüm 4, 7, 8).

## Çalışma
- Prosedür ve simülasyon kuralları: qspice-sim skill (tek kaynak). Şekiller: figures skill, kök CLAUDE.md "Figures".
- Koşucu pipeline kökünden: powershell -NoProfile -ExecutionPolicy Bypass -File tools\run_sim.ps1 -SimDir 02_simulasyon\sim -Analyze <analyzer'lar> (ayrıntı skill'de). Modeller sim\models (byte-exact); canary_rc.cir tools\canary\'dan kopyalanır.
- Köşeler SPEC Bölüm 4 test matrisinden (12 V/250 Ω, 24 V/300 Ω, 24 V/600 Ω, 36 V/250 Ω), sıcaklık ve parça toleransı uçları; her köşe adlandırılır.
- Doğruluk bütçesi sayılırken çözücü hatası (canary) ile model/parça belirsizliği ayrı yazılır.
- Pin kimliği: her parça için docs\PINMAP.md'de tek tablo (datasheet pin adı ve numarası, kaynak D<nn> p.<n> + crop, SPICE model düğümü, testbench net'i, SPICE alias, KiCad sembol pini). QSPICE düğüm adları büyük/küçük harf duyarsızdır: yalnız harf farkıyla ayrışan ad yasak; alias ASCII, büyük harf, alt çizgi, + ve - yok, <PARÇA>_<PİN> biçimi. Alt devre iç düğümü .save ile alınamaz: gereken sinyal dış pinde olmalı. Yeni testbench önce PINMAP'te olmayan pin kullanamaz.
- Ham veri: .save yalnız gereken sinyaller; analiz küçük sonuç dosyalarını (sim\out\*.csv, .meas) yazar, ham .qraw -CleanRaw ile silinir (izinli tek silme).
- Sonuç etiketi [R]; mühendis yeniden üretince [C]. Mühendis okuyup onaylamadan sonuç [V] veya karar olmaz.
