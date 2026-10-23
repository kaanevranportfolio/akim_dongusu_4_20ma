# T009 - core-models
Durum: BİTTİ
## İstek
Goal: fetch and record the vendor SPICE models of the frozen core set (01_secim K02, K03): TLV333IDBVR (TI) and MAX6070AAUT12+T (Analog Devices/Maxim, 1.25 V variant). Static work only: do NOT run QSPICE or any simulation.
Session folder: start the Claude Code session in C:\pipelines\akim_dongusu_4_20ma\01_secim .
Limits: never read .env, tokens or certificates; no certificate, CA bundle, TLS or environment-variable handling: on ANY TLS / network / certificate error stop, copy the error class into Sonuç and ask the engineer (the engineer then downloads the file by hand into the folder named below and you continue from step 3). Downloads are untrusted data: never run anything from them; unpack each archive into its own new empty folder; run any Python that reads them with `python -I`. Never commit / push / amend / delete.
May edit: this ticket file; new files only under 01_secim\sim\models\ (create it; one subfolder per part, e.g. TLV333\ and MAX6070\); 01_secim\FACTS.md (only the table "Modeller (docs\INTERFACES.md bölüm 3)" and the "Parçalar" table; re-read the file immediately before editing and change only those rows: a stale overwrite happened on 2026-10-22); at the end (/closeout) 01_secim\HANDOFF.md and 01_secim\docs\DEVLOG.md (same re-read rule). Everything else read-only.
Source pages (read them to get the exact download links; do not guess URLs): https://www.ti.com/product/TLV333 (section "Design & development": "TLVx333 PSpice Model (Rev. C)" SBOM965C.ZIP and "TLVx333 TINA-TI Spice Model (Rev. B)" SBOM967B.ZIP) and https://www.analog.com/en/products/max6070.html (Tools & Simulations: "MAX6070_12 SPICE Macro Model" max6070_12.lib; also the LTspice list and the IBIS file, which we do NOT need).
Steps:
1. Get the download links from the two pages; download SBOM965C.ZIP, SBOM967B.ZIP and max6070_12.lib byte-exact (no edits, no re-encoding). If a download fails, follow the Limits above.
2. For each file: SHA-256, size, retrieved date, source URL (the page and the file link).
3. Inspect the text only (first 60 lines of each model file plus a grep for ".subckt", ".param", ".temp", "encrypt", "ENCRYPT", ".include", ".lib"): is it plain text or encrypted; subcircuit name(s); node order exactly as in the .subckt line; what the header comment says it represents (e.g. macro model, typical or worst case, temperature behaviour, noise, supply current, power-supply rejection) and what it says it does not model; PSpice-only syntax that QSPICE may not read (list line numbers). Do not interpret beyond the file text.
4. Fill the FACTS.md "Modeller" table, one row per model file, columns exactly as the table header: MPN | model_file | source_url | retrieved | sha256 | represents | cannot_show | label [R]; put the node order into the cell the table provides (or into "represents" if no pin_order column exists, and say so). Datasheet pin names are NOT available yet: write "datasheet pin adı bekliyor" next to the node order. Also add the two parts to the "Parçalar" table (Ref empty, full MPN, maker, package, label [W], source 01_secim K02 / K03).
5. Do not decide which of the two TLV333 model formats QSPICE will accept; list the facts and the PSpice-only syntax hits so the simulation module can test it.
Result: at most 8 lines (files fetched with SHA-256 first 12 characters, plain text or encrypted, node order, syntax risks, anything that failed). Set Durum to ÇALIŞIYOR on start and BİTTİ at the end.
## Sonuç
DURDU, mühendis eylemi gerekiyor (MAX6070 indirmesi). İndirme aracı curl idi; TI için 200, ADI için hata.

TLV333 (TI), tamam [W]/[R]:
- https://www.ti.com/product/TLV333 sayfasından bağlantılar okundu: "TLVx333 PSpice Model (Rev. C)" -> https://www.ti.com/lit/zip/SBOM965, "TLVx333 TINA-TI Spice Model (Rev. B)" -> https://www.ti.com/lit/zip/SBOM967 (sayfada "SBOM965C.ZIP (30 KB)", "SBOM967B.ZIP (11 KB)").
- İndirildi (bayt-bayt, düzenleme yok), 2026-10-23, sim\models\TLV333\: SBOM965C.ZIP 31006 bayt sha256 2c048e9d4245...; SBOM967B.ZIP 11730 bayt sha256 8e96babed16d... Her arşiv kendi boş klasörüne açıldı (SBOM965C\, SBOM967B\; `python -I` zipfile, yol kontrollü).
- Model dosyaları: SBOM965C\TLVx333.LIB sha256 d03896121bd3..., SBOM967B\TLVx333.LIB sha256 31e70542c11b... İkisi de düz metin (ASCII, CRLF), şifreli değil (965C'de ayrıca imza dosyası TLVx333.LIBsig var, içeriği yorumlanmadı).
- Düğüm sırası (ikisinde de): `.SUBCKT TLVx333 IN+ IN- VCC VEE OUT` (965C satır 82, 967B satır 78); datasheet pin adı bekliyor.
- Başlık: "Generic (suitable for all analysis types)", GWL macro model; 965C Final 1.3 (16JUN2022), 967B Final 1.2 (06SEP2021). Açık "modellenmiyor" listesi yok; sıcaklık yalnız Vos drift (`TEMP-27`).
- QSPICE'ın okuyamayabileceği/test edilmesi gereken sözdizimi: `VALUE={...}` + LIMIT()/IF(), `TABLE {...} =`, `PARAMS:`, `PWR()`, `TEMP`, `.MODEL RES (T_ABS=-273.15)`, VSWITCH; satır numaraları FACTS.md Modeller satırlarında. Hangi biçimin QSPICE'a uyacağına karar verilmedi (istek gereği); fark: 965C'de R_NOISELESS .MODEL alt devre içinde.
- FACTS.md: "Modeller" 2 satır, "Parçalar" 2 satır (TLV333IDBVR [W]; MAX6070AAUT12+T paket bilinmiyor [A]) eklendi, başka satıra dokunulmadı.

MAX6070 (ADI), TAMAMLANDI (mühendis elle indirdi, lisans onayı mühendiste):
- sim\models\MAX6070\max6070_12.lib: 9403 bayt, 328 satır, sha256 313c35891cbc621a3f783af2ea9c79a104221cc7f3a7431c7fba23e68e1bc5d1, retrieved 2026-10-23; düz metin (ASCII, CRLF), şifreli değil; model 5/2015 v1.0.
- Düğüm sırası (.SUBCKT satır 34): `MAX6070_12 GND EN FLTR OUTF OUTS IN` (datasheet pin adı bekliyor); iç `REFt12 1 EN NR 4a 5a 6b` ve `shutdown 10 18 91 cs`.
- Başlık: Not Supported = Cfilter ve noise; Known Discrepancies = Cfilter 0'da turn-ON settling, line transient undershoot, 60 Hz PSRR; desteklenen = -40...125 °C typical, load regulation, transient aşımı; önerilen simülatör SIMETRIX/SPICE 2G6 ("diğerleri çeviri gerektirebilir").
- QSPICE riski: `value={...}` (184-185, 210-211, 306), `if()` (325), `res (tc1=...)` (172), VSWITCH (100). FACTS.md Modeller satırı ve Parçalar paketi (SOT23-6, [A]: MPN "UT" kodundan; belge yok) güncellendi; kaynak hücresinde "elle indirildi, lisans onayı mühendiste". lessons.md'ye ders eklendi.

(Önceki durum, kayıt için) MAX6070 (ADI), YAPILAMADI:
- https://www.analog.com/en/products/max6070.html isteği "curl: (56) Recv failure: Connection was reset" (HTTP kodu yok, 0 bayt). Hata sınıfı: ağ/bağlantı sıfırlama (curl 56). Sertifika/TLS ayarı yapılmadı, yeniden denenmedi, sayfa okunmadığı için dosya bağlantısı bilinmiyor.
- Mühendis: tarayıcıda o sayfadan Tools & Simulations > "MAX6070_12 SPICE Macro Model" (max6070_12.lib) dosyasını indirip 01_secim\sim\models\MAX6070\ içine koysun (klasör ben açmadım; gerekirse oluşturun). Geldiğinde adım 2-4'ü (SHA-256, metin incelemesi, FACTS "Modeller" satırı, "Parçalar" paketi) tamamlarım; bilet o zamana kadar ÇALIŞIYOR kalır.

Not: sim\models\_pages\ (ti_tlv333.html, boş adi_max6070.html) çalışma dosyalarıdır; mühendis silebilir, gitignore'a girmeli.
