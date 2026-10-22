"""
select_components.py
Component Selector — Master Orchestrator
v1.0 | May 2026

Entry point for the entire pipeline. Run this script to select components.

Pipeline:
    1. validate_specs.py  — validates component_specs.json against schema
    2. search_digikey.py  — fetches candidates from DigiKey API
    3. ranker.py          — applies derating rules, ranks candidates
    4. Writes parts_map.json       — machine-readable, KiCad compatible
    5. Writes selection_report.md  — human-readable design review document

Usage:
    python select_components.py
    python select_components.py --specs path/to/component_specs.json
"""

import json
import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------

_BASE               = os.path.dirname(os.path.abspath(__file__))
_SPECS_PATH         = os.path.join(_BASE, "component_specs.json")
_REFERENCE_MAP_PATH = os.path.join(_BASE, "reference_parts_map.json")  # overridden by --reference-map
_OUT_DIR            = os.getcwd()                                      # overridden by --out
_MAP_PATH           = os.path.join(_OUT_DIR, "parts_map.json")
_REPORT_PATH        = os.path.join(_OUT_DIR, "selection_report.md")
_LOG_PATH           = os.path.join(_OUT_DIR, "selection.log")

# ---------------------------------------------------------------------------
# LOGGER — terminal + file, same format as validate_specs.py
# ---------------------------------------------------------------------------

def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("component_selector")
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    return logger  # file handler is attached in run(), once --out is known

log = _setup_logger()


def _attach_file_log(path: str) -> None:
    """Add the selection.log file handler (same format as the terminal one)."""
    fh = logging.FileHandler(path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        fmt="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    log.addHandler(fh)

# ---------------------------------------------------------------------------
# REFERENCE PARTS MAP — loaded at startup, provides footprint precedence
# ---------------------------------------------------------------------------

_REFERENCE_MAP = None  # Loaded by run()

def _load_reference_map():
    """Load reference_parts_map.json if it exists. Returns None if not found."""
    if not os.path.exists(_REFERENCE_MAP_PATH):
        return None
    try:
        with open(_REFERENCE_MAP_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log.warning(f"Failed to load reference_parts_map.json: {e}")
        return None

try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
    _COLOR = True
except ImportError:
    _COLOR = False

def _c(text, color):
    if not _COLOR:
        return str(text)
    colors = {"green": Fore.GREEN, "red": Fore.RED, "yellow": Fore.YELLOW,
              "cyan": Fore.CYAN, "bold": Style.BRIGHT, "white": Fore.WHITE}
    return f"{colors.get(color,'')}{text}{Style.RESET_ALL}"

# ---------------------------------------------------------------------------
# TYPE-BASED FOOTPRINT DEFAULTS — fallback when not in reference map
# ---------------------------------------------------------------------------

_TYPE_FOOTPRINT_DEFAULTS = {
    "resistor":         ("Resistor_SMD.pretty",   "R_0805_2012Metric"),
    "cap_ceramic":      ("Capacitor_SMD.pretty",  "C_0402_1005Metric"),
    "cap_electrolytic": ("Capacitor_SMD.pretty",  "C_1210_3225Metric"),
    "inductor":         ("Inductor_SMD.pretty",   "L_1210_3225Metric"),
    "diode_schottky":   ("Diode_SMD.pretty",      "D_SMA"),
    "mosfet":           ("Package_TO_SOT_SMD.pretty", "SOT-23"),
}


def _get_footprint(ref: str, spec: dict) -> tuple:
    """
    Get (footprint_lib, footprint) for a component.
    
    Precedence:
    1. Look up ref in reference_parts_map["components"] if available
    2. Fall back to type-based defaults from _TYPE_FOOTPRINT_DEFAULTS
    3. If neither found, return None and log a warning
    """
    # Check reference map first
    if _REFERENCE_MAP:
        ref_comps = _REFERENCE_MAP.get("components", {})
        if ref in ref_comps:
            ref_comp = ref_comps[ref]
            lib = ref_comp.get("footprint_lib")
            fp = ref_comp.get("footprint")
            if lib and fp:
                return (lib, fp)
            else:
                log.warning(f"{ref}: reference map entry missing footprint_lib or footprint")

    # Fall back to type-based defaults
    ctype = spec.get("type", "")
    if ctype in _TYPE_FOOTPRINT_DEFAULTS:
        return _TYPE_FOOTPRINT_DEFAULTS[ctype]

    # Neither found — warn loudly
    log.warning(f"{ref}: no footprint found in reference map or type defaults — manual assignment required")
    return None


def _get_value(ref: str, spec: dict, selected: dict) -> str:
    """Build the schematic value string for a component."""
    ctype = spec.get("type", "")

    if ctype == "inductor":
        return f"{spec.get('inductance_uH')}µH"
    if ctype in ("cap_ceramic", "cap_electrolytic"):
        if "capacitance_uF" in spec:
            return f"{spec['capacitance_uF']}µF"
        return f"{spec.get('capacitance_pF')}pF"
    if ctype == "resistor":
        if "resistance_kOhm" in spec:
            v = spec["resistance_kOhm"]
            return f"{v}kΩ"
        return f"{spec.get('resistance_Ohm')}Ω"
    if ctype == "diode_schottky":
        return selected.get("mpn", "")
    return selected.get("mpn", "")

# ---------------------------------------------------------------------------
# PARTS MAP BUILDER — KiCad compatible output
# ---------------------------------------------------------------------------

def _build_parts_map(specs: dict, results: dict) -> dict:
    """
    Build parts_map.json from selection results.
    Format matches existing pipeline parts_map.json pattern.
    Fixed components (ic_fixed) are carried through unchanged from a
    reference parts_map if present, otherwise built from spec.
    """
    project  = specs.get("project", "Unknown")
    comps    = specs.get("components", {})

    parts_map = {
        "_meta": {
            "description":    "Component Selector output — KiCad BOM with procurement data",
            "project":        project,
            "generated":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "derating_profile": specs.get("derating_profile", "industrial"),
            "tool_version":   "1.0",
        },
        "exclude_from_pcb": ["V1", "RLOAD"],
        "components": {}
    }

    for ref, spec in comps.items():
        ctype = spec.get("type")

        if ctype == "ic_fixed":
            # Fixed ICs: carry through from spec, with pin_map from reference if available
            entry = {
                "type":      "ic_fixed",
                "part":      spec.get("part"),
                "fixed":     True,
                "notes":     spec.get("notes", ""),
            }
            # Check for pin_map in reference_parts_map
            if _REFERENCE_MAP:
                ref_comp = _REFERENCE_MAP.get("components", {}).get(ref)
                if ref_comp and "pin_map" in ref_comp:
                    entry["pin_map"] = ref_comp["pin_map"]
            parts_map["components"][ref] = entry
            continue

        result = results.get(ref)
        if result is None or result["status"] != "OK":
            parts_map["components"][ref] = {
                "status":  result["status"] if result else "NOT_RUN",
                "error":   "No candidate found — manual selection required",
            }
            continue

        selected = result["selected"]
        fp_lib, fp = _get_footprint(ref, spec)
        value      = _get_value(ref, spec, selected)

        entry = {
            "footprint_lib":  fp_lib,
            "footprint":      fp,
            "value":          value,
            "mpn":            selected.get("mpn"),
            "manufacturer":   selected.get("manufacturer"),
            "digikey_pn":     selected.get("digikey_pn"),
            "datasheet":      selected.get("datasheet"),
            "unit_price_usd": selected.get("unit_price_usd"),
            "stock":          selected.get("stock"),
            "lead_time_weeks": selected.get("lead_time_weeks"),
            "lifecycle":      selected.get("lifecycle"),
            "derating_status": ("ASSUMED_VERIFY"
                                if selected.get("_derating", {}).get("assumed_rules")
                                else "PASS"),
            "derating_notes": [
                r["note"] for r in result["selected"].get("_derating", {}).get("rules", [])
                if r.get("note")
            ],
        }

        # Add alternatives as separate list
        if result.get("alternatives"):
            entry["alternatives"] = [
                {
                    "mpn":            a.get("mpn"),
                    "manufacturer":   a.get("manufacturer"),
                    "digikey_pn":     a.get("digikey_pn"),
                    "unit_price_usd": a.get("unit_price_usd"),
                    "stock":          a.get("stock"),
                }
                for a in result["alternatives"]
            ]

        if result.get("flags"):
            entry["flags"] = result["flags"]

        parts_map["components"][ref] = entry

    return parts_map


# ---------------------------------------------------------------------------
# SELECTION REPORT BUILDER — markdown
# ---------------------------------------------------------------------------

def _build_report(specs: dict, results: dict, parts_map: dict) -> str:
    """Build selection_report.md — human-readable design review document."""

    project = specs.get("project", "Unknown")
    profile = specs.get("derating_profile", "industrial")
    now     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    total      = sum(1 for s in specs["components"].values() if s.get("type") != "ic_fixed")
    selected   = sum(1 for r in results.values() if r and r["status"] == "OK")
    failed     = total - selected
    all_flags  = [f for r in results.values() if r for f in r.get("flags", [])]
    all_manual = []
    assumed_rules = 0
    for r in results.values():
        if r and r["status"] == "OK" and r["selected"]:
            for rule in r["selected"].get("_derating", {}).get("rules", []):
                if rule.get("status") == "ASSUMED_VERIFY":
                    assumed_rules += 1
                if rule.get("status") == "ASSUMED_VERIFY" or "verify" in rule.get("note", "").lower():
                    all_manual.append(rule["note"])

    lines = []
    lines.append(f"# Component Selection Report")
    lines.append(f"")
    lines.append(f"**Project:** {project}  ")
    lines.append(f"**Derating profile:** {profile.upper()}  ")
    lines.append(f"**Generated:** {now}  ")
    lines.append(f"**Tool:** Component Selector v1.0  ")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## Summary")
    lines.append(f"")
    lines.append(f"| | |")
    lines.append(f"|---|---|")
    lines.append(f"| Components to select | {total} |")
    lines.append(f"| Successfully selected | {selected} |")
    lines.append(f"| Failed / manual required | {failed} |")
    lines.append(f"| Lead time flags | {len(all_flags)} |")
    lines.append(f"| Manual verification required | {len(all_manual)} |")
    lines.append(f"| ASSUMED_VERIFY (not PASS) rules | {assumed_rules} |")
    lines.append(f"")

    if failed > 0:
        lines.append(f"## ⚠ Action Required — Manual Selection Needed")
        lines.append(f"")
        for ref, result in results.items():
            if result and result["status"] != "OK":
                lines.append(f"- **{ref}**: {result['status']} — no candidate passed derating. Manual selection required.")
        lines.append(f"")

    if all_manual:
        lines.append(f"## ⚠ Manual Verification Required")
        lines.append(f"")
        lines.append(f"The following parameters were not available in vendor data.")
        lines.append(f"Verify against manufacturer datasheet before ordering:")
        lines.append(f"")
        seen = set()
        for note in all_manual:
            if note not in seen:
                lines.append(f"- {note}")
                seen.add(note)
        lines.append(f"")

    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## Selected Components")
    lines.append(f"")

    for ref, spec in specs["components"].items():
        ctype = spec.get("type")
        if ctype == "ic_fixed":
            continue

        result = results.get(ref)
        if not result or result["status"] != "OK":
            lines.append(f"### {ref} — ❌ NO CANDIDATE FOUND")
            lines.append(f"")
            lines.append(f"Manual selection required.")
            lines.append(f"")
            continue

        s      = result["selected"]
        price  = f"${s['unit_price_usd']:.4f}" if s.get("unit_price_usd") else "N/A"
        stock  = f"{s.get('stock', 0):,}"
        lt     = f"{s.get('lead_time_weeks')} weeks" if s.get("lead_time_weeks") else "N/A"
        lc     = s.get("lifecycle", "N/A")
        fp_lib, fp = _get_footprint(ref, spec)

        lines.append(f"### {ref} — {s.get('mpn')}")
        lines.append(f"")
        lines.append(f"| Field | Value |")
        lines.append(f"|---|---|")
        lines.append(f"| Manufacturer | {s.get('manufacturer')} |")
        lines.append(f"| MPN | `{s.get('mpn')}` |")
        lines.append(f"| DigiKey PN | `{s.get('digikey_pn', 'N/A')}` |")
        lines.append(f"| Unit price | {price} |")
        lines.append(f"| Stock | {stock} |")
        lines.append(f"| Lead time | {lt} |")
        lines.append(f"| Lifecycle | {lc} |")
        lines.append(f"| Footprint | `{fp_lib}:{fp}` |")
        if s.get("datasheet"):
            lines.append(f"| Datasheet | [{s['mpn']} datasheet]({s['datasheet']}) |")
        lines.append(f"")

        # Derating summary
        derating = result.get("derating_applied", [])
        if derating:
            lines.append(f"**Derating checks:**")
            lines.append(f"")
            for d in derating:
                status = "⚠" if "ASSUMED_VERIFY" in d else ("✅" if "PASS" in d else "❌")
                verify = "⚠ verify" if "verify" in d.lower() else ""
                lines.append(f"- {status} {d} {verify}".strip())
            lines.append(f"")

        # Alternatives
        alts = result.get("alternatives", [])
        if alts:
            lines.append(f"**Alternatives:**")
            lines.append(f"")
            for i, a in enumerate(alts, 2):
                ap = f"${a['unit_price_usd']:.4f}" if a.get("unit_price_usd") else "N/A"
                lines.append(f"{i}. `{a.get('mpn')}` — {a.get('manufacturer')} — {ap}")
            lines.append(f"")

        # Flags
        flags = result.get("flags", [])
        if flags:
            for flag in flags:
                lines.append(f"> ⚠ {flag}")
            lines.append(f"")

    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## BOM Cost Summary")
    lines.append(f"")

    total_cost = 0.0
    lines.append(f"| Ref | MPN | Price |")
    lines.append(f"|---|---|---|")
    for ref, spec in specs["components"].items():
        if spec.get("type") == "ic_fixed":
            lines.append(f"| {ref} | {spec.get('part')} | fixed |")
            continue
        result = results.get(ref)
        if result and result["status"] == "OK":
            s     = result["selected"]
            price = s.get("unit_price_usd") or 0
            total_cost += price
            lines.append(f"| {ref} | `{s.get('mpn')}` | ${price:.4f} |")
        else:
            lines.append(f"| {ref} | — | N/A |")
    lines.append(f"")
    lines.append(f"**Total BOM cost (excl. U1):** ${total_cost:.4f}")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"*Generated by Component Selector v1.0 — {now}*")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MASTER ORCHESTRATOR
# ---------------------------------------------------------------------------

def run(specs_path: str = None, out_dir: str = None, reference_map_path: str = None) -> int:
    """
    Run the full component selection pipeline.

    Returns:
        0 on success (all components selected)
        1 on partial failure (some components not selected)
        2 on fatal error (validation failure, API error)
    """
    global _REFERENCE_MAP, _REFERENCE_MAP_PATH, _OUT_DIR, _MAP_PATH, _REPORT_PATH, _LOG_PATH

    specs_path = specs_path or _SPECS_PATH
    if reference_map_path:
        _REFERENCE_MAP_PATH = reference_map_path
    if out_dir:
        _OUT_DIR = os.path.abspath(out_dir)
    os.makedirs(_OUT_DIR, exist_ok=True)
    _MAP_PATH    = os.path.join(_OUT_DIR, "parts_map.json")
    _REPORT_PATH = os.path.join(_OUT_DIR, "selection_report.md")
    _LOG_PATH    = os.path.join(_OUT_DIR, "selection.log")
    _attach_file_log(_LOG_PATH)

    # --- Load reference parts map (optional) ---
    _REFERENCE_MAP = _load_reference_map()
    if _REFERENCE_MAP:
        log.info(f"Loaded reference_parts_map.json with {len(_REFERENCE_MAP.get('components', {}))} components")

    # --- Step 1: Validate ---
    log.info("=" * 60)
    log.info("Component Selector v1.0")
    log.info("=" * 60)

    try:
        from validate_specs import validate_specs
        specs = validate_specs(specs_path=specs_path)
    except SystemExit:
        return 2

    # --- Step 2 + 3: Search + Rank ---
    try:
        from search_digikey import search_component
        from ranker import rank_candidates
    except ImportError as e:
        log.error(f"Import error: {e}")
        return 2

    profile    = specs.get("derating_profile", "industrial")
    components = specs.get("components", {})
    results    = {}

    selectable = {k: v for k, v in components.items()
                  if v.get("type") != "ic_fixed"}

    log.info(f"Selecting {len(selectable)} components — profile: {profile}")
    log.info("-" * 60)

    for ref, spec in selectable.items():
        candidates = search_component(ref, spec)
        result     = rank_candidates(ref, spec, candidates, profile)
        results[ref] = result

    # --- Summary ---
    selected_refs = [r for r, v in results.items() if v["status"] == "OK"]
    failed_refs   = [r for r, v in results.items() if v["status"] != "OK"]
    all_flags     = [f for v in results.values() for f in v.get("flags", [])]

    log.info("=" * 60)
    log.info("SELECTION COMPLETE")
    log.info(f"  Selected  : {len(selected_refs)}/{len(selectable)}")
    if failed_refs:
        log.warning(f"  Failed    : {', '.join(failed_refs)}")
    if all_flags:
        log.info(f"  Flags     : {len(all_flags)} (see report)")
    log.info("=" * 60)

    # --- Step 4: Write parts_map.json ---
    parts_map = _build_parts_map(specs, results)
    with open(_MAP_PATH, "w", encoding="utf-8") as f:
        json.dump(parts_map, f, indent=2, ensure_ascii=False)
    log.info(f"✔  parts_map.json written → {_MAP_PATH}")

    # --- Step 5: Write selection_report.md ---
    report = _build_report(specs, results, parts_map)
    with open(_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    log.info(f"✔  selection_report.md written → {_REPORT_PATH}")

    # --- Terminal summary ---
    print()
    print(_c("=" * 60, "cyan"))
    print(_c("  Component Selector — Complete", "bold"))
    print(_c("=" * 60, "cyan"))
    print(f"  {_c('✔', 'green')}  Selected  : {_c(str(len(selected_refs)), 'bold')}/{len(selectable)}")
    if failed_refs:
        print(f"  {_c('✖', 'red')}  Failed    : {_c(', '.join(failed_refs), 'red')}")
    if all_flags:
        print(f"  {_c('⚠', 'yellow')}  Flags     : {len(all_flags)} — see selection_report.md")
    print(f"  {_c('→', 'cyan')}  parts_map.json")
    print(f"  {_c('→', 'cyan')}  selection_report.md")
    print(f"  {_c('→', 'cyan')}  selection.log")
    print(_c("=" * 60, "cyan"))
    print()

    return 0 if not failed_refs else 1


# ---------------------------------------------------------------------------
# CLI ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Component Selector — automated BOM generation from component_specs.json"
    )
    parser.add_argument(
        "--specs",
        default=_SPECS_PATH,
        help="Path to component_specs.json (default: project root)"
    )
    parser.add_argument(
        "--out",
        default=os.getcwd(),
        help="Output directory for parts_map.json, selection_report.md, selection.log (default: current directory)"
    )
    parser.add_argument(
        "--reference-map",
        default=None,
        help="Path to reference_parts_map.json (default: next to this script; skipped if absent)"
    )
    args = parser.parse_args()
    sys.exit(run(specs_path=args.specs, out_dir=args.out, reference_map_path=args.reference_map))
