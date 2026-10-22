"""
search_nexar.py
Component Selector — Nexar API Search Layer
v1.0 | May 2026

Fetches real component data from Nexar (Octopart aggregator).
Covers DigiKey, Mouser, Farnell, Arrow, and others in a single query.

Responsibilities:
    - OAuth2 token management (auto-refresh)
    - GraphQL queries per component type
    - Returns raw candidate list — no derating logic here
    - Never fabricates data — NO CANDIDATE FOUND if search returns nothing

Usage (standalone test):
    python search_nexar.py

Usage (imported):
    from search_nexar import search_component
    candidates = search_component(ref, component_spec)
"""

import os
import sys
import json
import logging
import requests
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# ENV + LOGGER
# ---------------------------------------------------------------------------

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass   # dotenv optional — env vars may be set by OS

NEXAR_CLIENT_ID     = os.getenv("NEXAR_CLIENT_ID")
NEXAR_CLIENT_SECRET = os.getenv("NEXAR_CLIENT_SECRET")

NEXAR_TOKEN_URL = "https://identity.nexar.com/connect/token"
NEXAR_API_URL   = "https://api.nexar.com/graphql"

log = logging.getLogger("component_selector")
if not log.handlers:
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

# ---------------------------------------------------------------------------
# TOKEN MANAGER
# ---------------------------------------------------------------------------

_token_cache = {
    "access_token": None,
    "expires_at":   datetime.utcnow()
}


def _get_token() -> str:
    """
    Fetch or return cached OAuth2 bearer token from Nexar identity server.
    Token is refreshed automatically when expired.

    Returns:
        Bearer token string.

    Exits with code 1 if credentials are missing or auth fails.
    """
    if not NEXAR_CLIENT_ID or not NEXAR_CLIENT_SECRET:
        log.error("Nexar credentials not found.")
        log.error("Expected NEXAR_CLIENT_ID and NEXAR_CLIENT_SECRET in .env file.")
        sys.exit(1)

    now = datetime.utcnow()
    if _token_cache["access_token"] and now < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    log.info("Fetching Nexar OAuth2 token...")
    try:
        response = requests.post(
            NEXAR_TOKEN_URL,
            data={
                "grant_type":    "client_credentials",
                "client_id":     NEXAR_CLIENT_ID,
                "client_secret": NEXAR_CLIENT_SECRET,
            },
            timeout=10
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        log.error("Cannot connect to Nexar identity server.")
        log.error("Check internet connection and try again.")
        sys.exit(1)
    except requests.exceptions.Timeout:
        log.error("Nexar token request timed out.")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        log.error(f"Nexar auth failed: {e.response.status_code} {e.response.text}")
        log.error("Check NEXAR_CLIENT_ID and NEXAR_CLIENT_SECRET in .env")
        sys.exit(1)

    data = response.json()
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"]   = now + timedelta(seconds=data.get("expires_in", 3600) - 60)
    log.info("Nexar token obtained.")
    return _token_cache["access_token"]


# ---------------------------------------------------------------------------
# GRAPHQL QUERY RUNNER
# ---------------------------------------------------------------------------

def _run_query(query: str, variables: dict) -> dict:
    """
    Execute a GraphQL query against the Nexar API.

    Args:
        query:     GraphQL query string
        variables: dict of query variables

    Returns:
        Parsed JSON response dict.

    Exits with code 1 on network or API errors.
    """
    token = _get_token()
    try:
        response = requests.post(
            NEXAR_API_URL,
            json={"query": query, "variables": variables},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type":  "application/json",
            },
            timeout=15
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        log.error("Cannot connect to Nexar API.")
        sys.exit(1)
    except requests.exceptions.Timeout:
        log.error("Nexar API request timed out.")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        log.error(f"Nexar API error: {e.response.status_code}")
        log.error(e.response.text[:300])
        sys.exit(1)

    result = response.json()
    if "errors" in result:
        for err in result["errors"]:
            log.error(f"Nexar GraphQL error: {err.get('message')}")
        sys.exit(1)

    return result


# ---------------------------------------------------------------------------
# GRAPHQL QUERIES — one per component type
# ---------------------------------------------------------------------------

# Common procurement fields reused across all queries
# Note: lifecycleStatus is NOT a top-level SupPart field.
# It is returned as a spec attribute with shortname "lifecyclestatus" inside specs[].
_PROCUREMENT_FRAGMENT = """
    sellers {
        company { name }
        offers {
            inventoryLevel
            prices { quantity currency price }
            factoryLeadDays
        }
    }
    manufacturerUrl
"""

_QUERY_INDUCTOR = """
query SearchInductor($q: String!, $limit: Int!) {
  supSearch(q: $q, limit: $limit, filters: {}) {
    results {
      part {
        mpn
        manufacturer { name }
        shortDescription
        specs {
          attribute { name shortname }
          displayValue
        }
        """ + _PROCUREMENT_FRAGMENT + """
      }
    }
  }
}
"""

_QUERY_CAPACITOR = """
query SearchCapacitor($q: String!, $limit: Int!) {
  supSearch(q: $q, limit: $limit, filters: {}) {
    results {
      part {
        mpn
        manufacturer { name }
        shortDescription
        specs {
          attribute { name shortname }
          displayValue
        }
        """ + _PROCUREMENT_FRAGMENT + """
      }
    }
  }
}
"""

_QUERY_DIODE = """
query SearchDiode($q: String!, $limit: Int!) {
  supSearch(q: $q, limit: $limit, filters: {}) {
    results {
      part {
        mpn
        manufacturer { name }
        shortDescription
        specs {
          attribute { name shortname }
          displayValue
        }
        """ + _PROCUREMENT_FRAGMENT + """
      }
    }
  }
}
"""

_QUERY_RESISTOR = """
query SearchResistor($q: String!, $limit: Int!) {
  supSearch(q: $q, limit: $limit, filters: {}) {
    results {
      part {
        mpn
        manufacturer { name }
        shortDescription
        specs {
          attribute { name shortname }
          displayValue
        }
        """ + _PROCUREMENT_FRAGMENT + """
      }
    }
  }
}
"""

# ---------------------------------------------------------------------------
# QUERY STRING BUILDERS — one per component type
# ---------------------------------------------------------------------------

def _build_inductor_query(spec: dict) -> str:
    """Build a Nexar search string for an inductor."""
    uH  = spec.get("inductance_uH", "")
    pkg = spec.get("package", "")
    return f"inductor {uH}uH SMD {pkg}".strip()


def _build_cap_ceramic_query(spec: dict) -> str:
    """Build a Nexar search string for an MLCC."""
    if "capacitance_uF" in spec:
        val = f"{spec['capacitance_uF']}uF"
    else:
        val = f"{spec.get('capacitance_pF')}pF"
    v   = spec.get("V_working_min_V", "")
    pkg = spec.get("package", "")
    diel = spec.get("dielectric", "")
    return f"capacitor {val} {diel} {v}V {pkg}".strip()


def _build_cap_electrolytic_query(spec: dict) -> str:
    """Build a Nexar search string for an electrolytic capacitor."""
    val = f"{spec.get('capacitance_uF')}uF"
    v   = spec.get("V_working_min_V", "")
    pkg = spec.get("package", "")
    return f"electrolytic capacitor {val} {v}V SMD {pkg}".strip()


def _build_diode_query(spec: dict) -> str:
    """Build a Nexar search string for a Schottky diode."""
    vr  = spec.get("V_reverse_min_V", "")
    iav = spec.get("I_avg_min_A", "")
    pkg = spec.get("package", "")
    return f"schottky diode {vr}V {iav}A {pkg}".strip()


def _build_resistor_query(spec: dict) -> str:
    """Build a Nexar search string for a resistor."""
    if "resistance_kOhm" in spec:
        val = f"{spec['resistance_kOhm']}kohm"
    else:
        val = f"{spec.get('resistance_Ohm')}ohm"
    tol = spec.get("tolerance_pct", "")
    pkg = spec.get("package", "")
    return f"resistor {val} {tol}% {pkg}".strip()


# ---------------------------------------------------------------------------
# SPEC PARSER — convert raw Nexar spec list to a flat dict
# ---------------------------------------------------------------------------

# Maps Nexar spec shortnames to our internal field names
_SPEC_MAP = {
    # Inductors
    "inductance":           "inductance_uH_raw",
    "dc_resistance":        "dcr_raw",
    "saturation_current":   "isat_raw",
    "rated_current":        "irms_raw",
    "self_resonant_freq":   "srf_raw",
    # Capacitors
    "capacitance":          "capacitance_raw",
    "voltage_rating_dc":    "v_rated_raw",
    "dielectric":           "dielectric",
    "esr":                  "esr_raw",
    "ripple_current":       "irms_raw",
    "operating_temperature":"temp_rating_raw",
    # Diodes
    "reverse_voltage":      "v_reverse_raw",
    "forward_current":      "i_avg_raw",
    "forward_voltage":      "vf_raw",
    "junction_capacitance": "cj_raw",
    # Resistors
    "resistance":           "resistance_raw",
    "tolerance":            "tolerance_raw",
    "power_rating":         "p_rated_raw",
    "temperature_coefficient": "tempco_raw",
    # Lifecycle — lives in specs[], not as a top-level SupPart field
    "lifecyclestatus":      "lifecycle_raw",
    "lifecycle_status":     "lifecycle_raw",
}


def _parse_specs(spec_list: list) -> dict:
    """
    Convert Nexar's list of {attribute: {shortname}, displayValue} specs
    into a flat dict using our internal field names.

    Values are stored as raw strings — parsing to float is done by
    _extract_float() in the normaliser.
    """
    out = {}
    for item in spec_list:
        shortname = item.get("attribute", {}).get("shortname", "").lower()
        value     = item.get("displayValue", "")
        if shortname in _SPEC_MAP:
            out[_SPEC_MAP[shortname]] = value
        else:
            # Store unmapped specs under their original name for debugging
            out[f"_raw_{shortname}"] = value
    return out


def _extract_float(raw: str) -> float | None:
    """
    Extract a numeric value from a raw spec string.
    Handles unit suffixes: uH, mOhm, Ohm, pF, uF, nF, A, mA, V, MHz, kHz, W, mW, ppm
    Returns None if parsing fails — never raises.
    """
    if not raw:
        return None

    import re
    raw = raw.strip()

    multipliers = {
        "mohm": 1e-3,   "kohm": 1e3,    "mohms": 1e-3,  "kohms": 1e3,
        "uh":   1.0,    "nh":   1e-3,   "mh":   1e3,
        "pf":   1e-6,   "nf":   1e-3,   "uf":   1.0,
        "ma":   1e-3,   "ua":   1e-6,
        "mw":   1e-3,   "kw":   1e3,
        "mhz":  1.0,    "khz":  1e-3,
        "ppm":  1.0,
        "mohm/c": 1.0,
    }

    # Try to match: number + optional unit
    match = re.match(r"^([0-9]*\.?[0-9]+(?:[eE][+-]?[0-9]+)?)\s*([a-zA-Z/°Ω]*)", raw)
    if not match:
        return None

    value_str = match.group(1)
    unit      = match.group(2).lower().replace("ω", "ohm").replace("°", "")

    try:
        value = float(value_str)
    except ValueError:
        return None

    multiplier = multipliers.get(unit, 1.0)
    return value * multiplier


# ---------------------------------------------------------------------------
# NORMALISER — convert raw Nexar part into our candidate dict format
# ---------------------------------------------------------------------------

def _normalise_part(raw_part: dict, component_type: str) -> dict:
    """
    Convert a raw Nexar part dict into a normalised candidate dict
    with typed numeric fields ready for derating_rules.py.

    Fields that cannot be parsed are set to None — never fabricated.

    Returns:
        Candidate dict with:
            mpn, manufacturer, description, lifecycle,
            unit_price_usd, stock, lead_time_weeks,
            + type-specific numeric fields
    """
    specs = _parse_specs(raw_part.get("specs", []))

    # --- Procurement ---
    unit_price  = None
    stock       = 0
    lead_days   = None

    for seller in raw_part.get("sellers", []):
        for offer in seller.get("offers", []):
            inv = offer.get("inventoryLevel", 0) or 0
            stock += inv

            prices = offer.get("prices", [])
            if prices:
                # Take the price for qty=1 if available, else first entry
                for p in prices:
                    if p.get("quantity", 0) <= 1 and p.get("currency") == "USD":
                        unit_price = p.get("price")
                        break
                if unit_price is None and prices[0].get("currency") == "USD":
                    unit_price = prices[0].get("price")

            if lead_days is None and offer.get("factoryLeadDays"):
                lead_days = offer["factoryLeadDays"]

    lead_weeks = round(lead_days / 7) if lead_days else None

    candidate = {
        "mpn":           raw_part.get("mpn", "PARAMETER NOT AVAILABLE"),
        "manufacturer":  raw_part.get("manufacturer", {}).get("name", "PARAMETER NOT AVAILABLE"),
        "description":   raw_part.get("shortDescription", "PARAMETER NOT AVAILABLE"),
        "lifecycle":     specs.get("lifecycle_raw", None),   # from specs[], not top-level
        "datasheet":     raw_part.get("manufacturerUrl", None),
        "unit_price_usd": unit_price,
        "stock":          stock,
        "lead_time_weeks": lead_weeks,
        "_raw_specs":     specs,   # keep for debugging
    }

    # --- Type-specific numeric fields ---
    if component_type == "inductor":
        candidate.update({
            "inductance_uH": _extract_float(specs.get("inductance_uH_raw")),
            "isat_A":        _extract_float(specs.get("isat_raw")),
            "irms_A":        _extract_float(specs.get("irms_raw")),
            "dcr_mOhm":      _extract_float(specs.get("dcr_raw")),
            "srf_MHz":       _extract_float(specs.get("srf_raw")),
        })

    elif component_type in ("cap_ceramic", "cap_electrolytic"):
        cap_val = _extract_float(specs.get("capacitance_raw"))
        candidate.update({
            "capacitance_uF":  cap_val,
            "v_rated_V":       _extract_float(specs.get("v_rated_raw")),
            "dielectric":      specs.get("dielectric", None),
            "esr_mOhm":        _extract_float(specs.get("esr_raw")),
            "irms_A":          _extract_float(specs.get("irms_raw")),
            "temp_rating_C":   _extract_float(specs.get("temp_rating_raw")),
        })

    elif component_type == "diode_schottky":
        candidate.update({
            "v_reverse_V":  _extract_float(specs.get("v_reverse_raw")),
            "i_avg_A":      _extract_float(specs.get("i_avg_raw")),
            "vf_V":         _extract_float(specs.get("vf_raw")),
            "cj_pF":        _extract_float(specs.get("cj_raw")),
        })

    elif component_type == "resistor":
        candidate.update({
            "resistance_kOhm": _extract_float(specs.get("resistance_raw")),
            "tolerance_pct":   _extract_float(specs.get("tolerance_raw")),
            "p_rated_W":       _extract_float(specs.get("p_rated_raw")),
            "tempco_ppm":      _extract_float(specs.get("tempco_raw")),
        })

    return candidate


# ---------------------------------------------------------------------------
# TYPE DISPATCHER
# ---------------------------------------------------------------------------

_QUERY_MAP = {
    "inductor":         (_QUERY_INDUCTOR,   _build_inductor_query),
    "cap_ceramic":      (_QUERY_CAPACITOR,  _build_cap_ceramic_query),
    "cap_electrolytic": (_QUERY_CAPACITOR,  _build_cap_electrolytic_query),
    "diode_schottky":   (_QUERY_DIODE,      _build_diode_query),
    "resistor":         (_QUERY_RESISTOR,   _build_resistor_query),
}

_RESULTS_LIMIT = 15   # candidates fetched per component — ranker trims to top 3


def search_component(ref: str, spec: dict) -> list:
    """
    Search Nexar for candidates matching the given component spec.

    Args:
        ref:  reference designator e.g. "L1", "C1"
        spec: component dict from component_specs.json

    Returns:
        List of normalised candidate dicts.
        Empty list if no results — never fabricates.
    """
    ctype = spec.get("type")

    if ctype == "ic_fixed":
        log.info(f"  {ref}: ic_fixed — skipped")
        return []

    if ctype not in _QUERY_MAP:
        log.warning(f"  {ref}: unknown type '{ctype}' — skipped")
        return []

    query, build_query_str = _QUERY_MAP[ctype]
    query_str = build_query_str(spec)

    log.info(f"  {ref} ({ctype}): searching — '{query_str}'")

    try:
        result = _run_query(query, {"q": query_str, "limit": _RESULTS_LIMIT})
    except SystemExit:
        log.error(f"  {ref}: search failed — see errors above")
        return []

    raw_results = result.get("data", {}).get("supSearch", {}).get("results", [])

    if not raw_results:
        log.warning(f"  {ref}: NO CANDIDATE FOUND — Nexar returned 0 results for '{query_str}'")
        return []

    candidates = []
    for item in raw_results:
        raw_part = item.get("part", {})
        if not raw_part:
            continue
        candidate = _normalise_part(raw_part, ctype)
        candidates.append(candidate)

    log.info(f"  {ref}: {len(candidates)} candidates returned")
    return candidates


# ---------------------------------------------------------------------------
# CLI STANDALONE TEST
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    _BASE       = os.path.dirname(os.path.abspath(__file__))
    _SPECS_PATH = os.path.join(_BASE, "component_specs.json")

    parser = argparse.ArgumentParser(
        description="Test Nexar search for one or all components in component_specs.json"
    )
    parser.add_argument(
        "--ref",
        default=None,
        help="Reference designator to test e.g. --ref L1. Omit to test all."
    )
    args = parser.parse_args()

    with open(_SPECS_PATH, encoding="utf-8") as f:
        specs = json.load(f)

    components = specs.get("components", {})

    if args.ref:
        if args.ref not in components:
            print(f"ERROR: '{args.ref}' not found in component_specs.json")
            sys.exit(1)
        to_search = {args.ref: components[args.ref]}
    else:
        to_search = components

    print(f"\nNexar Search Test — {len(to_search)} component(s)\n")

    for ref, spec in to_search.items():
        ctype = spec.get("type")
        if ctype == "ic_fixed":
            print(f"  {ref}: SKIPPED (ic_fixed)")
            continue

        candidates = search_component(ref, spec)

        if not candidates:
            print(f"  {ref}: NO CANDIDATE FOUND")
            continue

        print(f"\n  {ref} — {len(candidates)} candidates:")
        for i, c in enumerate(candidates[:3], 1):
            price = f"${c['unit_price_usd']:.4f}" if c["unit_price_usd"] else "price N/A"
            stock = c["stock"] if c["stock"] else "stock N/A"
            print(f"    [{i}] {c['mpn']:30s}  {c['manufacturer']:20s}  {price}  stock={stock}")

    print("\nDone.\n")
