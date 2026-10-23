# RULE_LEDGER - her kuralın kaynağı, olayı ve yeni yeri
Üretildi: 2026-10-22 (pipeline kurulumu). Kaynak sürümler: EDA = C:\eda\CLAUDE.md (6405 B), KIT = C:\eda\new_project_essentials\00_ANA_SEVIYE_C-eda\CLAUDE.md (6706 B),
KCAD = C:\KiCAD_Projects\CLAUDE.md (7338 B), TASLAK = HANDOFF-pipeline ile gelen CLAUDE.md (4664 B), YÜK = programmable_electronic_load\CLAUDE.md, QS = qspice-sim skill (yük projesi), VT = vscode-ticket skill.
Olay sütunu: kaynak dosyada yazılı olay; "kayıtta yok" = olay bulunamadı (kural yine korunur, olay sonradan eklenir).

| # | Kural | Kaynak | Olay | Yeni yer | Not |
|---|---|---|---|---|---|
| 1 | Türkçe yanıt, içerik Türkçe (kural blokları, komut, dosya adı hariç) | EDA KIT KCAD TASLAK | kayıtta yok | CLAUDE.md Language | Bilet "İstek" bölümü İngilizce: açıkça eklendi (TASLAK/VT çelişkisi) |
| 2 | Datasheet terimleri çevrilmez | EDA KIT KCAD YÜK (TASLAK'ta YOK) | 2026-10-17 mühendis kuralı (yük HANDOFF) | CLAUDE.md Language | TASLAK düşürüyordu: geri alındı |
| 3 | Kontrole giden değer: D<nn> + sayfa + crop PNG; metin çıkarımı [R], crop sonrası [V] | EDA KIT KCAD YÜK (TASLAK'ta YOK) | LM1117 3,3 V sütun hatası (datasheet-lookup); TPS54360 Eq 2/7-10 (lessons) | CLAUDE.md Language | |
| 4 | Çok sütunlu kontrol tabloları md + script PDF | EDA KIT KCAD YÜK (TASLAK'ta YOK) | kayıtta yok | CLAUDE.md Language + check-pdf skill | |
| 5 | PDF'te Crop sütunu + iç bağlantı | KIT KCAD YÜK (EDA'da YOK: bir kural geride) | kayıtta yok | CLAUDE.md Language | EDA sürümü kitin gerisindeydi |
| 6 | Persona yok | tümü | - | Principles | |
| 7 | Tam parça, tam varyant | tümü | NRF2401.PDF (datasheet-lookup) | Principles | |
| 8 | Uydurma; bulunamadı = bulunamadı; emin değil = [A] | tümü | - | Principles | |
| 9 | Çelişen iki değer uzlaşana kadar kullanılmaz | tümü | - | Principles | |
| 10 | Kritik değer mühendis kontrolüne kadar kesin değil; AI MPN/değeri aday | EDA KIT YÜK KCAD(yalnız ikinci yarı) (TASLAK'ta YOK) | kayıtta yok | Principles | |
| 11 | Kesik görüntüde görünmeyen = "çıkarım" | EDA KIT (TASLAK'ta YOK) | kayıtta yok | Principles | |
| 12 | Dağıtıcı verisi aday listesi çıkarır, datasheet karar verir | METHODOLOGY_v2 kural 9 | kayıtta yok | Principles | Seçim modülü için gerekli |
| 13 | Etiket seti [V][M][C][R][U][W][A] | tümü (VT'de [M] eksikti) | VT'de [M] unutulmuş | CLAUDE.md Labels (tek kaynak) | VT bu listeyi tekrarlamamalı |
| 14 | BOM durum sözcükleri SEÇİLDİ/VARSAYILAN/AÇIK/DÜŞTÜ | KCAD, hand-off | - | CLAUDE.md Labels | |
| 15 | Belge numarası D<nn>, karar numarası K<nn> | YENİ | UPSTREAM U-12 (D04, D14 hem belge hem karar) | CLAUDE.md Labels | Eski atıflar "eda D<nn>" öneki alır |
| 16 | docs\ref gitignored; D<nn>_ adlandırma, INDEX.md, atıf "D03 p.38" | EDA KIT KCAD YÜK (TASLAK'ta YOK) | D03 yeniden adlandırma açık işi (yük HANDOFF) | CLAUDE.md Documents | Kütüphane tek: pipeline kökü (iki kopya + elle senkron kalkar) |
| 17 | Varyant kapısı | tümü | NRF2401.PDF | Documents + datasheet-lookup | _common.py FACTS yolu modül cwd'sine alındı |
| 18 | Arama sırası: FACTS, sonra arama ≤60 satır, şekil için tek crop | tümü | - | Documents | |
| 19 | Yalnız üretici modeli, byte-exact, SHA-256 kaydı, model yazılmaz | METHODOLOGY_v2 kural 3, QS | LM1117 modeli ESR kararsızlığını gösteremez | Documents + qspice-sim | URL kaydı eklendi (YENİ, spec model kaynağı şartı) |
| 20 | Şekil: gerçek veriden, elle çizilmez, kaynak/commit/etiket alt bilgisi | tümü | - | Figures | |
| 21 | Şekilde etiketler basılı yazımla | EDA YÜK (TASLAK'ta YOK) | kayıtta yok | Figures | |
| 22 | SVG kaynak, PNG gitignored | tümü | - | Figures | |
| 23 | Sim şekilleri: docs\sim\<testbench>\, iki şekil, altı kural | EDA YÜK QS | ilk grafikler şemasız teslim edildi (QS) | Figures + qspice-sim | |
| 24 | CLAUDE.md < 150 satır, modüle özgü | tümü | - | Layout | Kök bu sınırın dışında (117 satır) |
| 25 | FACTS/HANDOFF/DOCS_NEEDED/lessons/DEVLOG tanımları | tümü | HANDOFF'a commit durumu yazmak bayat kaldı (lessons) | Layout | |
| 26 | DECISIONS.md append-only | EDA KIT KCAD YÜK (TASLAK karar 5 kaldırıyordu) | mühendis kararı 2026-10-22: modül başına DECISIONS.md | Layout | |
| 27 | Kural yalnız tekrar eden hatadan sonra, olayıyla | tümü | - | Rules | |
| 28 | Hard block settings.json'da | tümü | - | Rules + settings | |
| 29 | Tekrarlı çok adımlı iş skill olur | tümü | - | Rules | |
| 30 | Skill prosedürü tutar, kural kökte; tekrar yok | YENİ | VT/EDA etiket listesi ayrışması; yük/KCAD skill sürümleri ayrışması | Rules | |
| 31 | ~/.claude okunmaz/yazılmaz | tümü | - | Safety | |
| 32 | .env, token, sertifika okunmaz | YENİ | component_selector_v1 klasöründe .env ve .digikey_cache var | Safety + settings deny | Olay değil, önlem; kayıtta yok |
| 33 | tag, amend, reset --hard, checkout ., clean yasak | tümü | - | Safety + settings | |
| 34 | Dosya silinmez (araç içi temizlik hariç) | tümü | 1,5 GB $RW2NFLO.qraw (lessons) | Safety | run_sim.ps1 -CleanRaw tek istisna |
| 35 | Modül oturumu commit/push yapmaz; kök oturumu koordinatör bileti ile | TASLAK, VT | - | Safety + settings (modül: deny, kök: ask) | EDA/KCAD'daki "go ile commit" modüller için kalktı |
| 36 | Claude KiCad dosyalarını düzenlemez; kicad-cli ile okur | KCAD | kayıtta yok | Safety + settings | Üreteç yalnız biletle, yeni dosyaya |
| 37 | Normal pencere, yönetici değil | tümü | - | Safety | |
| 38 | Modül kendi klasörüne yazar, diğerleri salt okunur | TASLAK | - | Layout | |
| 39 | Planner sadece md ve bilet; PDF/araç/script/şekil VS Code'a | EDA KIT KCAD | kayıtta yok | Session | |
| 40 | Tek yazar: planner VS Code boş mu diye sorar | EDA KIT KCAD VT | kayıtta yok | Session | |
| 41 | Durum yalnız dosyada | tümü | SPEC v1.3 metni oturum bitince kayboldu (lessons) | Session | |
| 42 | /start /report /closeout | tümü | - | Session + .claude\commands | /closeout commit sunmaz |
| 43 | Bilet: İstek planner, Sonuç VS Code; Durum AÇIK/ÇALIŞIYOR/BİTTİ | yük docs\tasks\README.md (VT yalnız AÇIK/BİTTİ) | - | 00_coordination/docs/tasks/README.md | ÇALIŞIYOR geri alındı: elle "boşta mı" sorusunu azaltır |
| 44 | Simülasyon: .save, max adım, canary, adım etiketine göre eşle, LONG | QS METHODOLOGY_v2 | 1,5 GB ham dosya; AS BUILT/COMPARISON etiketleri karıştı; FB 0 V foldback | qspice-sim | Kökte tekrarlanmaz |
| 45 | Limit datasheet'ten, model davranışından değil | QS | TPS54360 modeli 118 ns vs 135 ns | qspice-sim | |
| 46 | Pin kimliği: PINMAP, ASCII büyük harf alias, <PARÇA>_<PİN>, yalnız harf farkıyla ayrışan ad yok | YÜK KCAD | QSPICE düğüm adları harf duyarsız (naming canary) | 01_secim/02_simulasyon/03_kicad CLAUDE.md | Modül dosyalarında |
| 47 | KiCad kapıları: ERC, netlist=upstream, footprint [V]; DRC, BOM, mühendis go | KCAD | kayıtta yok | 03_kicad/CLAUDE.md | |
| 48 | Her aralık nominal mi en kötü durum mu söylenir | lessons (pratik, kural değil) | L1 penceresi nominal sanıldı; E12 DCM cümlesi | docs\INTERFACES.md (stress table) | Kural olarak kökte değil |
| 49 | Ağ/TLS/sertifika hatasında dur ve mühendise sor; sertifika deposu okunmaz/dışa aktarılmaz, CA paketi üretilmez, REQUESTS_CA_BUNDLE/SSL_CERT_FILE/CURL_CA_BUNDLE ayarlanmaz, TLS doğrulaması kapatılmaz | YENİ | 2026-10-22 01_secim/T001: DigiKey OAuth CERTIFICATE_VERIFY_FAILED; ajan pip-system-certs denedi (truststore çakışması), Windows ROOT/CA deposundan 53 kök sertifikayı dışa aktarıp certifi ile birleştirdi (bilet dışı); doğrulama kapatılmadı | CLAUDE.md Safety | Neden (ortam farkı mı, ağda TLS denetimi mi) kanıtlanmadı [A]; tanı 00_coordination/T010. vscode-ticket skill'ine aynı cümle (claude.ai tarafı) |
| 50 | Planner bileti sohbete koymaz ve outputs altına Write ile yazmaz; scratchpad'de yazar, device_commit_files ile modülün docs\tasks klasörüne aktarır; sohbette yalnız dosya adı, 2-3 satır özet ve tek satır komut | YENİ | 2026-10-23 01_secim: bilet md'leri Write ile outputs altına yazıldı, sohbete tam metin ve dosya kartı düştü (şişme) | CLAUDE.md Session | vscode-ticket skill'i ve proje instructions satırı claude.ai tarafında (mühendis kaydeder) |
| 52 | Simülasyon devre şekli her terminalde üç ad gösterir: DS (datasheet pin no + ad + D<nn> p.<n>), SP (.SUBCKT konumu + SPICE düğümü), TB (testbench net); önek ve şekil ayırır, renk yardımcıdır; bilinmeyen "?" taranır, tahmin yok | YENİ | 2026-10-23 mühendis önerisi (01_secim): datasheet pini, SPICE model düğümü ve testbench net karışması şekilde görünmüyordu | CLAUDE.md Figures kural 2 + figures skill + docs\INTERFACES.md bölüm 10 | docs\sim\circuits.py repoda yok; yalnız docs\sim\pin_map.py yazıldı (T025) |
| 51 | Kontrol tablosu veren oturum son mesajında `kontrol PDF'i hazır: <yol>.pdf, <N> sayfa, <M> crop, <K> eksik` satırını yazar; K sıfır değilse PDF teslim edilmez | YENİ | 2026-10-23 01_secim: kontrol PDF'inin yolu mühendise bildirilmedi | CLAUDE.md Session + check-pdf skill adım 3 + 01_secim, 02_simulasyon CLAUDE.md | 03_kicad/CLAUDE.md satır 20 komutu taşır, bildirim satırını taşımaz (T024 adım 7c) |

## Bilerek düşenler
- `/brief`, supervisor_brief.md, SUPERVISOR DECISIONS bloğu (METHODOLOGY_v2 rolleri): eski Supervisor modeli; yerine planner + bilet + HANDOFF.
- `proposals\` klasörü: aynı işi SPEC (00_coordination), bilet ve HANDOFF görüyor. Dayandığı olay (SPEC v1.3 kaybı) kural 41 ile korunuyor.
- /closeout içindeki "1 commit / 2 kendi mesajım / 3 commit etme": karar 7 ile çelişir; commit yalnız kök oturumda koordinatör biletiyle.
- C:\eda\CLAUDE.md "Show git status before any commit; commit only after the engineer's go": modüller commit etmez; kök oturumu için Safety'de daha sıkı biçim var.
- Faz/Rule 1-11 sayıları (eski küresel kural numaraları): arşiv projelerde atıf olarak kalır, burada kullanılmaz.
- Üreteç tabanlı şema/PCB akışı (gen_sch.py, gen_pcb.py): nrf24'e bağlı, bu turda taşınmadı.

## Doğrulanması bekleyenler
- Skill görünürlüğü (modül klasöründen oturum): 00_coordination/T001.
- Modül ve kök settings.json etkisi: 00_coordination/T001.
