"""
search_digikey.py
Component Selector — DigiKey Product Information V4 Search Layer
v1.0 | May 2026

Fetches real component data from DigiKey's Product Information V4 API.
Returns normalised candidate list — same format as search_nexar.py.
No derating logic here. Never fabricates data.

Auth note:
    2-legged OAuth (client credentials) via digikey_v4.py. No browser login.
    Token is kept in memory only; no token file, no .digikey_cache needed.

Usage (standalone test):
    python search_digikey.py
    python search_digikey.py --ref L1

Usage (imported):
    from search_digikey import search_component
    candidates = search_component(ref, component_spec)
"""

try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

import os
import sys
import json
import logging

# ---------------------------------------------------------------------------
# ENV SETUP
# ---------------------------------------------------------------------------

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

_BASE = os.path.dirname(os.path.abspath(__file__))

import digikey_v4   # direct Product Information V4 HTTP client (requests only)

# ---------------------------------------------------------------------------
# LOGGER
# ---------------------------------------------------------------------------

log = logging.getLogger("component_selector")
if not log.handlers:
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

# ---------------------------------------------------------------------------
# CREDENTIALS CHECK
# ---------------------------------------------------------------------------

def _check_credentials() -> None:
    """Fail fast if DigiKey credentials are missing."""
    if not os.environ.get("DIGIKEY_CLIENT_ID"):
        log.error("DIGIKEY_CLIENT_ID not found in .env file.")
        sys.exit(1)
    if not os.environ.get("DIGIKEY_CLIENT_SECRET"):
        log.error("DIGIKEY_CLIENT_SECRET not found in .env file.")
        sys.exit(1)

# ---------------------------------------------------------------------------
# QUERY STRING BUILDERS — one per component type
# Broad enough to return results, specific enough to be relevant.
# Filtering is done by derating_rules.py — not here.
# ---------------------------------------------------------------------------

def _build_inductor_query(spec: dict) -> str:
    """
    Broad search — value and type only.
    No package. Signal inductors without Isat will be rejected by derating downstream.
    """
    uH = spec.get("inductance_uH", "")
    return f"inductor {uH}uH"


def _build_cap_ceramic_query(spec: dict) -> str:
    """
    Broad search — value, dielectric, and minimum rated voltage.
    No package. Voltage guides DigiKey to return correctly-rated parts.
    2x derating applied by engine: 60V working → 120V min → search 250V.
    """
    if "capacitance_uF" in spec:
        val = f"{spec['capacitance_uF']}uF"
    else:
        val = f"{spec.get('capacitance_pF')}pF"
    diel  = spec.get("dielectric", "")
    v     = float(spec.get("V_working_min_V", 0))
    v_min = 2.0 * v   # minimum rated voltage after derating

    # Round up to next standard MLCC voltage rating
    if v_min > 100:
        v_str = "250V"
    elif v_min > 50:
        v_str = "100V"
    elif v_min > 25:
        v_str = "50V"
    elif v_min > 10:
        v_str = "25V"
    else:
        v_str = ""

    return f"capacitor {val} {diel} {v_str}".strip()


def _build_cap_electrolytic_query(spec: dict) -> str:
    """
    Broad search — value and minimum rated voltage.
    No package. 1.5x derating: 10V working → 15V min → search 16V.
    """
    val   = f"{spec.get('capacitance_uF')}uF"
    v     = float(spec.get("V_working_min_V", 0))
    v_min = 1.5 * v

    if v_min > 35:
        v_str = "50V"
    elif v_min > 25:
        v_str = "35V"
    elif v_min > 16:
        v_str = "25V"
    else:
        v_str = "16V"

    return f"electrolytic capacitor {val} {v_str}"


def _build_diode_query(spec: dict) -> str:
    """
    Broad search — type, minimum voltage, and minimum current.
    Current required — without it DigiKey returns signal diodes (200mA) not power diodes (3-5A).
    Derating: 1.5x V_reverse, 1.5x I_avg applied before selecting voltage/current strings.
    """
    vr   = float(spec.get("V_reverse_min_V", 0))
    iavg = float(spec.get("I_avg_min_A", 0))

    # Minimum rated values after derating
    vr_min   = 1.5 * vr
    iavg_min = 1.5 * iavg

    # Round up to next standard voltage
    if vr_min > 60:
        v_str = "100V"
    elif vr_min > 40:
        v_str = "60V"
    elif vr_min > 20:
        v_str = "40V"
    else:
        v_str = ""

    # Round current up to nearest whole amp
    i_str = f"{int(iavg_min) + 1}A" if iavg_min > 0 else ""

    return f"schottky diode {v_str} {i_str}".strip()


def _build_resistor_query(spec: dict) -> str:
    """
    Broad search — value and tolerance only. No package.
    Use full value with units to prevent partial matches:
    '162 kohm 1%' is unambiguous. '162k' can match '2k' parts containing '162'.
    """
    if "resistance_kOhm" in spec:
        val = f"{spec['resistance_kOhm']} kohm"
    else:
        val = f"{spec.get('resistance_Ohm')} ohm"
    tol = spec.get("tolerance_pct", "")
    return f"resistor {val} {tol}%"


_QUERY_BUILDERS = {
    "inductor":         _build_inductor_query,
    "cap_ceramic":      _build_cap_ceramic_query,
    "cap_electrolytic": _build_cap_electrolytic_query,
    "diode_schottky":   _build_diode_query,
    "resistor":         _build_resistor_query,
}

# ---------------------------------------------------------------------------
# PARAMETER EXTRACTOR
# ---------------------------------------------------------------------------

def _extract_float(raw: str) -> float | None:
    """
    Extract a numeric value from a raw parameter string.
    Handles unit suffixes: uH, mOhm, pF, uF, V, mV, A, mA, W, MHz, ppm etc.
    DigiKey uses "-" for unpopulated fields — treated as None.
    Returns None if parsing fails — never raises.
    """
    if not raw:
        return None

    import re
    raw = str(raw).strip()

    # DigiKey dash values — genuinely not specified
    if raw in ("-", "—", "N/A", "n/a", "-/-", "−"):
        return None

    # Strip condition suffix: "800 mV @ 100 mA" → "800 mV"
    if "@" in raw:
        raw = raw.split("@")[0].strip()

    # Strip parenthetical suffix: "200mA (DC)" → "200mA"
    if "(" in raw:
        raw = raw.split("(")[0].strip()

    multipliers = {
        "mohm": 1e-3,  "kohm": 1e3,   "mohms": 1e-3,  "kohms": 1e3,
        "uh":   1.0,   "nh":   1e-3,  "mh":   1e3,
        "pf":   1e-6,  "nf":   1e-3,  "uf":   1.0,    "µf":   1.0,
        "ma":   1e-3,  "ua":   1e-6,
        "mv":   1e-3,                  # millivolts → volts
        "mw":   1e-3,  "kw":   1e3,
        "mhz":  1.0,   "khz":  1e-3,
        "ppm":  1.0,
    }

    match = re.match(
        r"^([0-9]*\.?[0-9]+(?:[eE][+-]?[0-9]+)?)\s*([a-zA-Zµ/°Ω]*)",
        raw
    )
    if not match:
        return None

    value_str = match.group(1)
    unit      = match.group(2).lower().replace("ω", "ohm").replace("µ", "u").replace("°", "")

    try:
        value = float(value_str)
    except ValueError:
        return None

    return value * multipliers.get(unit, 1.0)


# ---------------------------------------------------------------------------
# PARAMETER MAPPER
# DigiKey returns parameters as list of {ParameterId, ParameterText, ValueText}
# We map ParameterText (lowercased) to our internal field names.
# ---------------------------------------------------------------------------

_PARAM_MAP = {
    # --- Inductors ---
    "inductance":                           "inductance_uH_raw",
    "dc resistance (dcr)":                  "dcr_raw",
    "dc resistance":                        "dcr_raw",
    "current rating (amps)":               "irms_raw",
    "current - rated":                      "irms_raw",
    "current-rated":                        "irms_raw",
    "saturation current":                   "isat_raw",
    "current - saturation (isat)":          "isat_raw",
    "current-saturation (isat)":            "isat_raw",
    "current - saturation":                 "isat_raw",
    "frequency - self resonant":            "srf_raw",
    "frequency-self resonant":              "srf_raw",

    # --- Capacitors ---
    "capacitance":                          "capacitance_raw",
    "voltage - rated":                      "v_rated_raw",
    "voltage-rated":                        "v_rated_raw",
    "voltage rating - dc":                  "v_rated_raw",
    "voltage rating":                       "v_rated_raw",
    # Dielectric — DigiKey uses "temperature coefficient" for MLCC dielectric code
    "temperature coefficient":              "dielectric",
    "dielectric":                           "dielectric",
    "material":                             "dielectric",
    "esr (equivalent series resistance)":   "esr_raw",
    "esr":                                  "esr_raw",
    "current - ripple (100khz)":            "irms_raw",
    "current - ripple":                     "irms_raw",
    "current - leakage":                    "irms_raw",
    "operating temperature":                "temp_rating_raw",

    # --- Diodes ---
    "voltage - dc reverse (vr) (max)":                      "v_reverse_raw",
    "voltage - reverse (vr) (max)":                         "v_reverse_raw",
    "voltage - reverse":                                     "v_reverse_raw",
    "voltage-dc reverse (vr) (max)":                        "v_reverse_raw",
    # Confirmed from DigiKey v4 debug May 2026:
    "current - average rectified (io) (per diode)":         "i_avg_raw",
    "current - average rectified (io)":                     "i_avg_raw",
    "current - average rectified":                          "i_avg_raw",
    "current-average rectified (io)":                       "i_avg_raw",
    "current - forward (if) (max)":                         "i_avg_raw",
    "voltage - forward (vf) (max) @ if":                    "vf_raw",
    "voltage - forward (vf) (max)":                         "vf_raw",
    "voltage-forward (vf) (max) @ if":                      "vf_raw",
    "voltage - forward (vf) @ if":                          "vf_raw",
    "capacitance @ vr":                                     "cj_raw",
    "capacitance-junction":                                 "cj_raw",

    # --- Resistors ---
    "resistance":                           "resistance_raw",
    "tolerance":                            "tolerance_raw",
    "power (watts)":                        "p_rated_raw",
    "power rating":                         "p_rated_raw",
    "composition":                          "_composition",  # informational

    # --- Lifecycle ---
    "product status":                       "lifecycle_raw",
}


def _parse_parameters(params: list) -> dict:
    """
    Convert DigiKey's parameter list into a flat dict using internal field names.
    Unmapped parameters stored under _raw_ prefix for debugging.
    """
    out = {}
    for p in params:
        key = p.get("ParameterText", "").lower().strip()
        val = p.get("ValueText", "")
        if key in _PARAM_MAP:
            out[_PARAM_MAP[key]] = val
        else:
            out[f"_raw_{key}"] = val
    return out


# ---------------------------------------------------------------------------
# NORMALISER — convert DigiKey product to our candidate dict
# ---------------------------------------------------------------------------

def _normalise_product(product: dict, component_type: str) -> dict:
    """
    Convert a raw DigiKey Product Information V4 product (JSON dict, PascalCase keys)
    into a normalised candidate dict. Field names: V4 Swagger (KeywordSearch, definition Product):
        Manufacturer.Name, ManufacturerProductNumber, UnitPrice, QuantityAvailable,
        ProductStatus.Status, Description.DetailedDescription / ProductDescription,
        ProductVariations[].DigiKeyProductNumber, Parameters[].ParameterText / ValueText,
        ManufacturerLeadWeeks, DatasheetUrl, ProductUrl.
    A field missing in the response becomes None (or the existing "PARAMETER NOT AVAILABLE" text).
    """
    product = product or {}

    # --- Parameters ---
    params = _parse_parameters([
        {
            "ParameterText": p.get("ParameterText") or "",
            "ValueText":     p.get("ValueText") or "",
        }
        for p in (product.get("Parameters") or [])
    ])

    # --- Price ---
    unit_price = product.get("UnitPrice")
    try:
        unit_price = float(unit_price) if unit_price is not None else None
    except (ValueError, TypeError):
        unit_price = None

    # --- Stock ---
    stock = product.get("QuantityAvailable") or 0

    # --- DigiKey PN — ProductVariations[0] ---
    variations = product.get("ProductVariations") or []
    digikey_pn = variations[0].get("DigiKeyProductNumber") if variations else None

    # --- Lead time ---
    lead_weeks_raw = product.get("ManufacturerLeadWeeks")
    try:
        lead_weeks = int(lead_weeks_raw) if lead_weeks_raw else None
    except (ValueError, TypeError):
        lead_weeks = None

    # --- Lifecycle ---
    lifecycle = (product.get("ProductStatus") or {}).get("Status")

    # --- Description ---
    desc_obj = product.get("Description") or {}
    description = (
        desc_obj.get("DetailedDescription") or
        desc_obj.get("ProductDescription") or
        "PARAMETER NOT AVAILABLE"
    )

    # --- Manufacturer ---
    manufacturer = (product.get("Manufacturer") or {}).get("Name") or "PARAMETER NOT AVAILABLE"

    candidate = {
        "mpn":            product.get("ManufacturerProductNumber") or "PARAMETER NOT AVAILABLE",
        "manufacturer":   manufacturer,
        "description":    description,
        "lifecycle":      lifecycle,
        "datasheet":      product.get("DatasheetUrl"),
        "digikey_pn":     digikey_pn,
        "product_url":    product.get("ProductUrl"),
        "unit_price_usd": unit_price,
        "stock":          stock,
        "lead_time_weeks": lead_weeks,
        "_raw_params":    params,
    }

    # --- Type-specific numeric fields ---
    if component_type == "inductor":
        candidate.update({
            "inductance_uH": _extract_float(params.get("inductance_uH_raw")),
            "isat_A":        _extract_float(params.get("isat_raw")),
            "irms_A":        _extract_float(params.get("irms_raw")),
            "dcr_mOhm":      _extract_float(params.get("dcr_raw")),
            "srf_MHz":       _extract_float(params.get("srf_raw")),
        })

    elif component_type in ("cap_ceramic", "cap_electrolytic"):
        candidate.update({
            "capacitance_uF": _extract_float(params.get("capacitance_raw")),
            "v_rated_V":      _extract_float(params.get("v_rated_raw")),
            "dielectric":     params.get("dielectric", None),
            "esr_mOhm":       _extract_float(params.get("esr_raw")),
            "irms_A":         _extract_float(params.get("irms_raw")),
            "temp_rating_C":  _extract_float(params.get("temp_rating_raw")),
        })

    elif component_type == "diode_schottky":
        candidate.update({
            "v_reverse_V": _extract_float(params.get("v_reverse_raw")),
            "i_avg_A":     _extract_float(params.get("i_avg_raw")),
            "vf_V":        _extract_float(params.get("vf_raw")),
            "cj_pF":       _extract_float(params.get("cj_raw")),
        })

    elif component_type == "resistor":
        candidate.update({
            "resistance_kOhm": _extract_float(params.get("resistance_raw")),
            "tolerance_pct":   _extract_float(params.get("tolerance_raw")),
            "p_rated_W":       _extract_float(params.get("p_rated_raw")),
            "tempco_ppm":      _extract_float(params.get("tempco_raw")),
        })

    return candidate


# ---------------------------------------------------------------------------
# MAIN SEARCH FUNCTION
# ---------------------------------------------------------------------------

_RESULTS_LIMIT = 15   # candidates per component — ranker trims to top 3


def search_component(ref: str, spec: dict) -> list:
    """
    Search DigiKey for candidates matching the given component spec.

    Args:
        ref:  reference designator e.g. "L1", "C1"
        spec: component dict from component_specs.json

    Returns:
        List of normalised candidate dicts.
        Empty list if no results — never fabricates.
    """
    _check_credentials()

    ctype = spec.get("type")

    if ctype == "ic_fixed":
        log.info(f"  {ref}: ic_fixed — skipped")
        return []

    if ctype not in _QUERY_BUILDERS:
        log.warning(f"  {ref}: unknown type '{ctype}' — skipped")
        return []

    query_str = _QUERY_BUILDERS[ctype](spec)
    log.info(f"  {ref} ({ctype}): searching — '{query_str}'")

    try:
        result = digikey_v4.keyword_search(query_str, limit=_RESULTS_LIMIT, offset=0)
    except Exception as e:
        log.error(f"  {ref}: DigiKey search failed — {e}")
        return []

    if result is None:
        log.warning(f"  {ref}: NO CANDIDATE FOUND — DigiKey returned None")
        return []

    products = result.get("Products") or []

    if not products:
        log.warning(f"  {ref}: NO CANDIDATE FOUND — DigiKey returned 0 results for '{query_str}'")
        return []

    candidates = []
    for product in products:
        try:
            candidate = _normalise_product(product, ctype)
            candidates.append(candidate)
        except Exception as e:
            log.warning(f"  {ref}: failed to normalise product — {e}")
            continue

    log.info(f"  {ref}: {len(candidates)} candidates returned")
    return candidates


# ---------------------------------------------------------------------------
# CLI STANDALONE TEST
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    _SPECS_PATH = os.path.join(_BASE, "component_specs.json")

    parser = argparse.ArgumentParser(
        description="Test DigiKey search for one or all components in component_specs.json"
    )
    parser.add_argument(
        "--ref",
        default=None,
        help="Reference designator to test e.g. --ref L1. Omit to test all."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show parsed numeric fields for first candidate of each component."
    )
    args = parser.parse_args()

    if not os.path.exists(_SPECS_PATH):
        print(f"ERROR: component_specs.json not found at {_SPECS_PATH}")
        sys.exit(1)

    with open(_SPECS_PATH, encoding="utf-8") as f:
        specs = json.load(f)

    components = specs.get("components", {})

    if args.ref:
        if args.ref not in components:
            print(f"ERROR: '{args.ref}' not found in component_specs.json")
            sys.exit(1)
        to_search = {args.ref: components[args.ref]}
    else:
        to_search = {k: v for k, v in components.items()
                     if v.get("type") != "ic_fixed"}

    print(f"\nDigiKey Search Test — {len(to_search)} component(s)\n")

    for ref, spec in to_search.items():
        candidates = search_component(ref, spec)

        if not candidates:
            print(f"  {ref}: NO CANDIDATE FOUND")
            continue

        print(f"\n  {ref} — {len(candidates)} candidates:")
        for i, c in enumerate(candidates[:3], 1):
            price = f"${c['unit_price_usd']:.4f}" if c["unit_price_usd"] else "price N/A"
            stock = c["stock"] if c["stock"] else "stock N/A"
            dk_pn = c.get("digikey_pn", "")
            print(
                f"    [{i}] {c['mpn']:35s}  "
                f"{str(c['manufacturer']):22s}  "
                f"{price:12s}  "
                f"stock={stock:>8}  "
                f"DK={dk_pn}"
            )
            if args.debug and i == 1:
                print(f"         --- Parsed numeric fields (first candidate) ---")
                skip = {"mpn","manufacturer","description","lifecycle","datasheet",
                        "digikey_pn","product_url","unit_price_usd","stock",
                        "lead_time_weeks","_raw_params"}
                for k, v in c.items():
                    if k not in skip:
                        print(f"         {k:25s} = {v}")
                print(f"         --- Raw DigiKey parameter names ---")
                for k, v in c["_raw_params"].items():
                    if not k.startswith("_raw_"):
                        print(f"         {k:35s} = {v}")
                    else:
                        print(f"         {k[5:]:35s} [unmapped] = {v}")

    print("\nDone.\n")
