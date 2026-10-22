# HANDOFF - 00_coordination
Güncelleme: 2026-10-22 (T001, T002 bitti; T003 hazır)

## Durum
- Pipeline iskeleti kuruldu; SPEC v0.1 (taslak) buraya kopyalandı. v0.2 değişiklikleri mühendis tarafından onaylandı, 00_coordination/T003 ile uygulanacak.
- 00_coordination/T001 BİTTİ: 6/7 PASS (CLAUDE.md yüklemesi, .claude klasörleri, git deny, Python, canary, yazma sınırı). Adım 5 FAIL: doc_registry.json boş, regresyon koşmadı; skill kodu hatasız açıldı [R].

## Açık maddeler (nasıl kapanacak)
1. [spec] Mühendis kararları 2026-10-22: (a) "(V)" -> [A], tüm satırlar etiketli kalır. (b) K7 -> 3,8-20,5 mA. (c) 12 V satırı 220 Ω (7,6 V kalır, marj 0,6 V), K5 R_toplam = 220 Ω; 7 V hedefi ters polarite koruması düşümü dahil; koruma düşümü 01_secim A'nın ilk sorusu. (d) "01_core" -> 01_secim. Uygulama: 00_coordination/T003 (SPEC.md'yi VS Code günceller). Kapanış: mühendis v0.2'yi okuyup onaylar.
2. [tamam] 00_coordination/T001 BİTTİ (bkz. Durum). Kalan: doc_registry.json boş; mühendis kararı: yük kaydı kopyalanmaz, kayıt belge geldikçe belge alımı biletleriyle dolar. Regresyon testi (tests_reference_load.md, eski dosya adları) kendi PDF'lerimizle yeniden yazılır; ilk belge alımından sonra karar (olası T004). docs\ref henüz kontrol edilmedi.
3. [tamam, 00_coordination/T002 BİTTİ] component_selector -> tools\component_selector (kod, --out, ASSUMED_VERIFY, pytest 27/27, README) [R]. Tek kopya C:\component_selector_v1 ve güncel olan o: mühendis çalıştırdı, showcase videosu çekti, en düzgün çalışan sürüm [U]; LTSpice_Projects yolu eski sürümdü, artık yok. Kalan: tools\component_selector\tests\__pycache__ elle silinecek (mühendis); .digikey_cache betik klasöründe (gitignore'da), kimlik bilgisi ortam değişkeniyle; her koşuda --specs verilmeli; search_nexar.py test edilmedi.
4. [git] Klasör C:\pipelines\akim_dongusu_4_20ma altına taşındı (C:\eda dışında, üst depo yok). `git init` mühendis tarafından bu klasörde yapılır; ilk commit koordinatör biletiyle (kök oturumu).
5. [claude.ai] vscode-ticket skill'i güncellenecek: [M] etiketi, <modül>/Tnnn atfı, ÇALIŞIYOR durumu, git kuralı kök CLAUDE.md'ye atıf (tekrarlama).
6. [docs] Belge kütüphanesi: yük projesinden gereken PDF'ler D<nn> ile docs\ref'e (örn. SPEC'teki çekirdek IC adayları) ->  01_secim A ile birlikte.
7. [tamam 2026-10-22] DOT_claude -> .claude yeniden adlandırması mühendis tarafından yapıldı; klasör C:\pipelines\akim_dongusu_4_20ma altına taşındı.
8. [temizlik] .claude\commands\start.md içinde 'C:\eda\CLAUDE.md (legacy ancestor file)' ifadesi artık gereksiz -> VS Code ile bir bilette sadeleştirilir (köprü .claude'a yazamaz).
9. [claude.ai] Proje kurulumu: talimat ve açılış mesajları docs\planner\ altında; vscode-ticket skill güncellemesi önerildi -> mühendis kaydeder, projeyi kurar.

## Açık kararlar
(yok; kararlar docs\DECISIONS.md içinde K<nn> ile)

## Commit'e hazır yollar
(oturum sonunda /closeout yazar; commit yalnız koordinatör biletiyle)

## Sonraki oturumun ilk görevi
T003'ü çalıştır (VS Code, pipeline kökü veya 00_coordination), v0.2'yi oku ve onayla; sonra T002, `git init` ve ilk commit bileti.
