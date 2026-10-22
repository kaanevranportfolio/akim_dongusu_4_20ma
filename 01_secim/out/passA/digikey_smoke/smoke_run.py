"""DigiKey connectivity/field smoke test. One keyword search, raw result saved. Reads no secrets."""
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass
import json, os, sys
# Windows root certs appended to certifi (TLS inspection on this PC); generated API client reads certifi.where()
import certifi
_CA = os.environ.get("REQUESTS_CA_BUNDLE")
if _CA:
    certifi.where = lambda: _CA
HERE = os.path.dirname(os.path.abspath(__file__))
SEL = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "tools", "component_selector"))
sys.path.insert(0, SEL)
import search_digikey as sd  # loads .env from the selector folder itself; values never printed

spec = json.load(open(os.path.join(HERE, "smoke_spec.json"), encoding="utf-8"))
sd._check_credentials()
req = sd.KeywordRequest(keywords=spec["query"], limit=spec["limit"], offset=0)
res = sd.digikey.keyword_search(body=req)          # exceptions propagate (reported, not swallowed)
products = getattr(res, "products", []) or []
out = []
for p in products:
    c = sd._normalise_product(p, "ic")
    c.pop("_raw_params", None)
    c["raw_attrs"] = sorted(a for a in dir(p) if not a.startswith("_") and not callable(getattr(p, a, None)))
    c["package"] = next((getattr(x, "value_text", None) for x in (getattr(p, "parameters", []) or [])
                         if getattr(x, "parameter_text", "") in ("Package / Case", "Supplier Device Package")), None)
    out.append(c)
json.dump({"label": "[W]", "query": spec["query"], "count": len(out), "products_total": getattr(res, "products_count", None), "candidates": out},
          open(os.path.join(HERE, "result.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False, default=str)
print(f"candidates returned: {len(out)}")
