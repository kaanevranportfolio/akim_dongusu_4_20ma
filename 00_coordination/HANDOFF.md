# HANDOFF - 00_coordination
Güncelleme: 2026-10-22 (T001-T013 bitti; T014 commit bekliyor)

## Durum
- Pipeline iskeleti kuruldu; SPEC v0.2 uygulandı (00_coordination/T003, T004) ve mühendis tarafından onaylandı (K01, T009). Seçim bu SPEC'e göre 01_secim'de yapılır.
- 00_coordination/T001 BİTTİ: 6/7 PASS (CLAUDE.md yüklemesi, .claude klasörleri, git deny, Python, canary, yazma sınırı). Adım 5 FAIL: doc_registry.json boş, regresyon koşmadı; skill kodu hatasız açıldı [R].

## Açık maddeler (nasıl kapanacak)
1. [spec] Mühendis kararları 2026-10-22: (a) "(V)" -> [A], tüm satırlar etiketli kalır. (b) K7 -> 3,8-20,5 mA. (c) 12 V satırı 220 Ω (7,6 V kalır, marj 0,6 V), K5 R_toplam = 220 Ω; 7 V hedefi ters polarite koruması düşümü dahil; koruma düşümü 01_secim A'nın ilk sorusu. (d) "01_core" -> 01_secim. Uygulandı: 00_coordination/T003 ve T004 BİTTİ. Onay: docs\DECISIONS.md K01, SPEC.md Durum "Onaylı" (00_coordination/T009). Bölüm 8 açık soruları (giriş tipi, Vmin, arıza akımı, sıcaklık, doğruluk) 01_secim A aday kontrolünde teyit edilir. Arıza akımı (NAMUR 3,6/21 mA) Bölüm 8 madde 3'te açık.
2. [tamam] 00_coordination/T001 BİTTİ (bkz. Durum). Kalan: doc_registry.json boş; mühendis kararı: yük kaydı kopyalanmaz, kayıt belge geldikçe belge alımı biletleriyle dolar. Regresyon testi (tests_reference_load.md, eski dosya adları) kendi PDF'lerimizle yeniden yazılır; ilk belge alımından sonra karar (olası T004). docs\ref henüz kontrol edilmedi.
3. [tamam, 00_coordination/T002 BİTTİ] component_selector -> tools\component_selector (kod, --out, ASSUMED_VERIFY, pytest 27/27, README) [R]. Tek kopya C:\component_selector_v1 ve güncel olan o: mühendis çalıştırdı, showcase videosu çekti, en düzgün çalışan sürüm [U]; LTSpice_Projects yolu eski sürümdü, artık yok. Kalan: tools\component_selector\tests\__pycache__ elle silinecek (mühendis); .digikey_cache betik klasöründe (gitignore'da), kimlik bilgisi ortam değişkeniyle; her koşuda --specs verilmeli; search_nexar.py test edilmedi.
4. [tamam] git: depo kökte, ilk commit tek parça atıldı (00_coordination/T005; commit kimliği kaanevranportfolio) ve origin/main'e pushlandı (00_coordination/T007), uzak depo kaanevranportfolio/akim_dongusu_4_20ma (private). `.gitignore`: **/sim/out/*.log eklendi (00_coordination/T006). `.gitignore`: 02_simulasyon/sim/scratch/ eklendi; ikinci küçük commit pushlandı (00_coordination/T008). Bilet dosyaları kendi son Sonuç satırlarını commit sonrası aldığı için bir sonraki iş commit'inde değişiklik olarak görünür; bu normal.
5. [claude.ai] vscode-ticket skill'i güncellenecek: [M] etiketi, <modül>/Tnnn atfı, ÇALIŞIYOR durumu, git kuralı kök CLAUDE.md'ye atıf (tekrarlama).
6. [docs] Belge kütüphanesi: yük projesinden gereken PDF'ler D<nn> ile docs\ref'e (örn. SPEC'teki çekirdek IC adayları) ->  01_secim A ile birlikte.
7. [tamam 2026-10-22] DOT_claude -> .claude yeniden adlandırması mühendis tarafından yapıldı; klasör C:\pipelines\akim_dongusu_4_20ma altına taşındı.
8. [temizlik] .claude\commands\start.md içinde 'C:\eda\CLAUDE.md (legacy ancestor file)' ifadesi artık gereksiz -> VS Code ile bir bilette sadeleştirilir (köprü .claude'a yazamaz).
9. [claude.ai] Proje kurulumu: talimat ve açılış mesajları docs\planner\ altında; vscode-ticket skill güncellemesi önerildi -> mühendis kaydeder, projeyi kurar.
10. [tls] DigiKey CERTIFICATE_VERIFY_FAILED (01_secim/T001). Tanı 00_coordination/T010 [R]: 3.10 yorumlayıcı yok, CA değişkenleri hiçbir düzeyde ayarlı değil, api.digikey.com sertifikasını Sectigo veriyor (tarayıcıda görüldü [U]), ağda HTTPS denetimi kanıtı yok. 00_coordination/T013 [R]: truststore ile GET https://api.digikey.com/ -> HTTP 404 (el sıkışma tamam); truststore olmadan "unable to get local issuer certificate" (eksik ara sertifika varsayımıyla uyumlu [A]). Çözüm (mühendis kararı): selector betiklerinde truststore.inject_into_ssl() + doğrulanmış paket seti (00_coordination/T012, tools\component_selector). Kalan: (a) [tamam] 00_coordination/T011 BİTTİ: CLAUDE.md Safety maddesi ve RULE_LEDGER kural 49 eklendi; .claude\settings.json deny önerisi T011 Sonuç'unda, uygulama mühendis kararı (uygulanmadı); (b) 01_secim/T002 smoke_run.py'ye aynı dört satırı ekledi; yeni DigiKey uygulaması (Product Information v4), kimlik bilgisi tools\component_selector\.env'e mühendis tarafından yazıldı; smoke testini mühendis kendi terminalinde koşacak, sonucu henüz yok; v4 istemci kodu venv'de listelenmedi, kontrol smoke testinde [A]; (c) [tamam] vdk\ca_bundle.pem mühendis tarafından silindi; (d) [tamam] vscode-ticket skill güncellemesi (TLS cümlesi) mühendis tarafından kaydedildi; (e) selector'e IC/keyword girişi: öneri şimdilik eklememek, mühendis kararı bekliyor (K02).

## Açık kararlar
(yok; kararlar docs\DECISIONS.md içinde K<nn> ile)

## Commit'e hazır yollar
Yalnız son bilet dosyalarının commit sonrası eklenen Sonuç satırları (ör. T008, bu HANDOFF). Commit yalnız koordinatör biletiyle, kök oturumunda.

## Sonraki oturumun ilk görevi
İlk belge alımı (docs\ref, D<nn>, INDEX.md, doc_registry.json) ve 01_secim A'ya devir (çekirdek IC adayları SPEC v0.2'ye göre). Ardından: vscode-ticket skill güncellemesi (madde 5), .claude\commands\start.md sadeleştirmesi (madde 8), docs\ref kontrolü, regresyon testinin kendi PDF'lerimizle yeniden yazımı, DigiKey API key testi (component_selector).
