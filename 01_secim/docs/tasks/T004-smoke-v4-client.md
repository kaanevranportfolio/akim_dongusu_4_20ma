# T004 - smoke-v4-client
Durum: BİTTİ
## İstek
Goal: port 01_secim\out\passA\digikey_smoke\smoke_run.py to the new V4 client tools\component_selector\digikey_v4.py (00_coordination/T015 BİTTİ; the `digikey` library is no longer used). Edit only. Do NOT run the script, do NOT read .env/tokens/.digikey_cache/certificates, do NOT send any network request. Never commit / push / amend / delete.
May edit: this ticket file; 01_secim\out\passA\digikey_smoke\smoke_run.py. Everything else read-only (read digikey_v4.py and search_digikey.py only to match names and signatures).
Context of digikey_v4.py: V4, 2-legged OAuth, token in memory; keyword_search(keywords, limit, offset) and product_details(product_number) return raw JSON dicts; errors: DigiKeyAuthError (401), DigiKeyForbiddenError (403), DigiKeyRateLimitError (429).
Changes in smoke_run.py (nothing else):
1. Remove the certifi / REQUESTS_CA_BUNDLE block (about lines 3-7 after the truststore lines) and the wrong "TLS inspection" comment. Keep the four truststore lines (try: import truststore; truststore.inject_into_ssl(); except ImportError: pass).
2. Replace sd.digikey.keyword_search(body=req) and sd.KeywordRequest with: import digikey_v4 (module found via the existing SEL path) and res = digikey_v4.keyword_search(spec["query"], limit=spec["limit"], offset=0).
3. res is now a dict: products = res.get("Products") or []; products_total = res.get("ProductsCount").
4. sd._normalise_product(p, "ic") stays; p is a dict.
5. raw_attrs: sorted(p.keys()); package: from Parameters[] take ValueText of the entry whose ParameterText is "Package / Case" or "Supplier Device Package" (dict access).
6. Handle the three exception classes above explicitly; never print headers, token, client id or secret.
7. Saving: write the raw JSON response body only (no request headers, token, client id) to digikey_smoke\result.json.
If anything in digikey_v4.py contradicts these names or signatures, stop and ask the engineer instead of guessing.
Result: show the diff (read-only) in Sonuç + at most 5 lines. The engineer runs the test in their own terminal with the venv Temp\vdk. Set Durum to ÇALIŞIYOR on start and BİTTİ at the end.
## Sonuç
smoke_run.py V4 istemcisine taşındı. Çalıştırılmadı, ağ isteği yok, .env/token/cache/sertifika okunmadı; yalnız `ast.parse` ile sözdizimi kontrol edildi. digikey_v4.py ve search_digikey.py'deki adlar/imzalar istekle çelişmedi (keyword_search(keywords, limit, offset) -> ham dict "Products"/"ProductsCount"; DigiKeyAuthError/ForbiddenError/RateLimitError; search_digikey._normalise_product(product: dict, type)).

Diff (eski -> yeni, özet):
```
 try: import truststore; truststore.inject_into_ssl() / except ImportError: pass   (korundu)
-# Windows root certs appended to certifi (TLS inspection on this PC); ...
-import certifi
-_CA = os.environ.get("REQUESTS_CA_BUNDLE")
-if _CA:
-    certifi.where = lambda: _CA
 HERE/SEL/sys.path.insert(0, SEL); import search_digikey as sd   (aynı)
+import digikey_v4
 sd._check_credentials()   (aynı)
-req = sd.KeywordRequest(keywords=spec["query"], limit=spec["limit"], offset=0)
-res = sd.digikey.keyword_search(body=req)
+try:
+    res = digikey_v4.keyword_search(spec["query"], limit=spec["limit"], offset=0)
+except digikey_v4.DigiKeyAuthError as e:      print("AUTH ERROR (401): ..."); sys.exit(2)
+except digikey_v4.DigiKeyForbiddenError as e: print("FORBIDDEN (403): ...");  sys.exit(2)
+except digikey_v4.DigiKeyRateLimitError as e: print("RATE LIMIT (429): ..."); sys.exit(2)
-products = getattr(res, "products", []) or []
+products = res.get("Products") or []
+products_total = res.get("ProductsCount")
 c = sd._normalise_product(p, "ic")   (aynı, p artık dict)
-c["raw_attrs"] = sorted(a for a in dir(p) ...)
+c["raw_attrs"] = sorted(p.keys())
-c["package"] = next((getattr(x, "value_text", None) for x in (getattr(p, "parameters", []) or []) if getattr(x, "parameter_text", "") in (...)), None)
+c["package"] = next((x.get("ValueText") for x in (p.get("Parameters") or []) if x.get("ParameterText") in ("Package / Case", "Supplier Device Package")), None)
-json.dump({"label": "[W]", ..., "candidates": out}, open(result.json...))
+json.dump(res, open(result.json...), indent=2, ensure_ascii=False)   # yalnız ham yanıt gövdesi
-print(f"candidates returned: {len(out)}")
+print(f"candidates returned: {len(out)} (ProductsCount={products_total})")
```
Notlar:
- Hata mesajları 300 karaktere kısaltılıp yazdırılır; başlık/token/client id/secret yazdırılmaz. Mesaj metni digikey_v4._error_detail'den gelir (okunmadı, sızıntı yok varsayımı [A]).
- result.json artık ham yanıt: eski result.json (count 0, aday özeti) bir sonraki koşuda ezilir; normalleştirilmiş aday listesi (`out`) dosyaya yazılmaz, yalnız sayısı basılır (istek "başka değişiklik yok" dedi).
- Mühendis testi kendi terminalinde Temp\vdk venv ile çalıştırır.
