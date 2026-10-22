"""DigiKey connectivity/field smoke test. Four generic keyword searches, raw results + field table saved. Reads no secrets."""
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SEL = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "tools", "component_selector"))
sys.path.insert(0, SEL)
import search_digikey as sd  # loads .env from the selector folder itself; values never printed
import digikey_v4

PACKAGE_PARAMS = ("Package / Case", "Supplier Device Package")
DISCLAIMER = ("Distributor data, shortlist only. Not candidates: a part is a candidate only after it is "
              "seen in its own datasheet.")

spec = json.load(open(os.path.join(HERE, "smoke_spec.json"), encoding="utf-8"))
sd._check_credentials()


def _get(d, *path):
    for k in path:
        d = d.get(k) if isinstance(d, dict) else None
    return d


def _package(p):
    return next((x.get("ValueText") for x in (p.get("Parameters") or [])
                 if x.get("ParameterText") in PACKAGE_PARAMS), None)


def _paths(obj, prefix=""):
    """Field paths present (and non-empty) in one product dict; list items collapse to path[]."""
    found = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else k
            if v not in (None, "", [], {}):
                found.add(p)
            found |= _paths(v, p)
    elif isinstance(obj, list):
        for v in obj:
            found |= _paths(v, prefix + "[]")
    return found


def _cell(v):
    return "" if v is None else str(v).replace("|", "\\|").replace("\n", " ")


results = []  # (query, [products])
for n, q in enumerate(spec["queries"], 1):
    try:
        res = digikey_v4.keyword_search(q, limit=spec["limit"], offset=0)
        outcome = "ok"
    except digikey_v4.DigiKeyAuthError as e:
        print(f"{q!r}: DigiKeyAuthError (401): {str(e)[:300]}")
        sys.exit(2)
    except digikey_v4.DigiKeyForbiddenError as e:
        print(f"{q!r}: DigiKeyForbiddenError (403): {str(e)[:300]}")
        sys.exit(2)
    except digikey_v4.DigiKeyRateLimitError as e:
        print(f"{q!r}: DigiKeyRateLimitError (429): {str(e)[:300]}")
        sys.exit(2)
    except Exception as e:  # network / TLS / other DigiKeyError: print class, stop, no retry, no certificate handling
        print(f"{q!r}: {type(e).__name__}: {str(e)[:300]}")
        sys.exit(2)
    products = res.get("Products") or []
    # raw response body only: no request headers, token, client id or secret
    json.dump(res, open(os.path.join(HERE, f"result_{n}.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"{q!r}: {outcome}, Products={len(products)}, ProductsCount={res.get('ProductsCount')}")
    results.append((q, products))

# --- fields_table.md: field path -> products with the field present and non-empty ---
all_products = [p for _, ps in results for p in ps]
total = len(all_products)
counts = {}
for p in all_products:
    for path in _paths(p):
        counts[path] = counts.get(path, 0) + 1
link_re = re.compile(r"url|link|media|ecad|model|photo|datasheet|image|spice", re.I)
with open(os.path.join(HERE, "fields_table.md"), "w", encoding="utf-8") as f:
    f.write(f"# Alanlar (DigiKey V4 keyword search, ham JSON adlari) [W]\n\nToplam urun: {total} ({len(results)} sorgu).\n\n")
    f.write("| Alan yolu (JSON'daki gibi) | Dolu urun / toplam | Link/medya/model adayi |\n|---|---|---|\n")
    for path in sorted(counts):
        f.write(f"| {_cell(path)} | {counts[path]} / {total} | {'evet' if link_re.search(path) else ''} |\n")
    pk = sum(1 for p in all_products if _package(p))
    f.write(f"\nTuretilmis: package (Parameters[] ParameterText in {PACKAGE_PARAMS}): {pk} / {total}\n")

# --- found_parts.md: one table per query ---
with open(os.path.join(HERE, "found_parts.md"), "w", encoding="utf-8") as f:
    f.write(f"# found_parts\n\n{DISCLAIMER}\n\nEtiket: [W]\n")
    for q, products in results:
        f.write(f"\n## Sorgu: {_cell(q)}\n\n")
        f.write("| Manufacturer | Manufacturer Product Number | Package | Datasheet URL | Stock | Product Status | Source query | Label |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for p in products:
            f.write("| " + " | ".join(_cell(x) for x in (
                _get(p, "Manufacturer", "Name"), p.get("ManufacturerProductNumber"), _package(p),
                p.get("DatasheetUrl"), p.get("QuantityAvailable"), _get(p, "ProductStatus", "Status"), q, "[W]")) + " |\n")
print(f"fields_table.md ({len(counts)} alan yolu), found_parts.md yazildi; toplam urun {total}")
