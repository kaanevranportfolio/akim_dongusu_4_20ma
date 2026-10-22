# T005 - smoke-queries
Durum: BİTTİ
## İstek
Goal: extend the DigiKey smoke test so one engineer-run produces real search results and a field table. Edit only; do NOT run the script, do NOT read .env/tokens/.digikey_cache/certificates, do NOT send any network request. Never commit / push / amend / delete.
Context: 01_secim/T004 run by the engineer: token 200, /products/v4/search/keyword 200, but the raw body had Products=[] and no ProductsCount (query "loop-powered 4-20 mA transmitter IC" was too specific). The V4 client and TLS work; only the query needs changing.
May edit: this ticket file; 01_secim\out\passA\digikey_smoke\smoke_run.py and smoke_spec.json; new files only inside 01_secim\out\passA\digikey_smoke\. Everything else read-only.
Changes:
1. smoke_spec.json: replace the single query by a list "queries" with exactly these four short generic keyword strings, limit 10 each: "4-20mA transmitter", "current loop transmitter", "4-20mA", "voltage to current converter". No MPNs anywhere.
2. smoke_run.py: loop over the queries; per query call digikey_v4.keyword_search(q, limit, 0); save the raw JSON body only to result_<n>.json (n = 1..4); print one line per query: query, HTTP outcome class (ok / the three digikey_v4 exceptions), len(Products), ProductsCount. On any auth, TLS, network or rate-limit error: print the class and stop; no retry loop, no certificate handling.
3. After the loop the script writes fields_table.md: for each field path found in the returned product dicts (e.g. manufacturer product number, manufacturer name, description, quantity available, unit price / price breaks, product status, datasheet URL, product URL, package / case, any ECAD / model / media link), the count of products with that field present and non-empty out of the total, plus the field names exactly as the JSON prints them. Also write found_parts.md: a table per query with manufacturer, manufacturer product number, package, datasheet URL, stock, product status, source query, label [W] and the header line "Distributor data, shortlist only. Not candidates: a part is a candidate only after it is seen in its own datasheet." Do not print part lists to the console beyond the per-query lines.
4. Show the diff in Sonuç. Syntax check with ast.parse only.
Result: diff + at most 5 lines. The engineer runs the script in their own terminal (venv Temp\vdk, no CA environment variable) and reports the console lines. Set Durum to ÇALIŞIYOR on start and BİTTİ at the end.
## Sonuç
smoke_spec.json ve smoke_run.py güncellendi. Çalıştırılmadı, ağ isteği yok, .env/token/cache/sertifika okunmadı; yalnız `ast.parse` + `json.load` ile sözdizimi kontrol edildi.

Diff özeti:
```
smoke_spec.json:
-  "query": "loop-powered 4-20 mA transmitter IC",
+  "queries": ["4-20mA transmitter", "current loop transmitter", "4-20mA", "voltage to current converter"],
   "limit": 10        (15 -> 10; MPN yok)

smoke_run.py (truststore, SEL/sys.path, import search_digikey/digikey_v4, _check_credentials aynı):
-res = digikey_v4.keyword_search(spec["query"], limit=spec["limit"], offset=0)  (tek sorgu, 3 except)
+for n, q in enumerate(spec["queries"], 1):
+    res = digikey_v4.keyword_search(q, limit=spec["limit"], offset=0)
+    except DigiKeyAuthError / DigiKeyForbiddenError / DigiKeyRateLimitError / Exception (ağ, TLS, diğer):
+        sınıf adı + mesajın ilk 300 karakteri yazılır, sys.exit(2); yeniden deneme yok, sertifika işlemi yok
+    json.dump(res, result_<n>.json)            # yalnız ham gövde
+    print(f"{q!r}: ok, Products={len(...)}, ProductsCount={res.get('ProductsCount')}")
-sd._normalise_product / raw_attrs / tek result.json
+fields_table.md: ürün sözlüklerinden alan yolları (iç içe, liste öğeleri `path[]`), "dolu ürün / toplam", link/medya/model/ECAD adayı işareti, ayrıca türetilmiş package sayısı
+found_parts.md: sorgu başına tablo (Manufacturer, Manufacturer Product Number, Package, Datasheet URL, Stock, Product Status, Source query, Label [W]); başlıkta "Distributor data, shortlist only. Not candidates: a part is a candidate only after it is seen in its own datasheet."
+son satır: alan yolu sayısı ve toplam ürün; parça listesi konsola basılmaz
```
Notlar:
- Alan adları JSON'da yazıldığı gibi gelir (ör. Manufacturer.Name, ManufacturerProductNumber, QuantityAvailable, ProductStatus.Status, DatasheetUrl); çalıştırmadan doğrulanmadı [A], tablo gerçek adları üretecek.
- Eski result.json dokunulmadı; yeni dosyalar result_1..4.json. Mühendis venv Temp\vdk ile, CA ortam değişkeni olmadan çalıştırır ve konsol satırlarını bildirir.
