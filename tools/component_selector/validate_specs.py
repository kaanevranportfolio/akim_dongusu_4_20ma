"""
validate_specs.py
Component Selector — Input Validator
v1.0 | May 2026

Validates component_specs.json against schemas/component_specs_schema.json.
Must be the first script called by select_components.py.

Exits with code 1 on any validation failure — nothing downstream runs.

Usage (standalone):
    python validate_specs.py
    python validate_specs.py --specs path/to/component_specs.json

Usage (imported):
    from validate_specs import validate_specs
    specs = validate_specs()   # returns parsed dict or exits
"""

import json
import os
import sys
import argparse
import logging
from datetime import datetime

try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)   # Windows: converts ANSI codes automatically
    _COLOR = True
except ImportError:
    _COLOR = False

# ---------------------------------------------------------------------------
# COLOR HELPERS  (terminal only — log file stays plain text)
# ---------------------------------------------------------------------------

def _c(text: str, color: str) -> str:
    """Wrap text in a color code if colorama is available."""
    if not _COLOR:
        return text
    colors = {
        "green":  Fore.GREEN,
        "red":    Fore.RED,
        "yellow": Fore.YELLOW,
        "cyan":   Fore.CYAN,
        "white":  Fore.WHITE,
        "bold":   Style.BRIGHT,
    }
    return f"{colors.get(color, '')}{text}{Style.RESET_ALL}"


def _print_color(text: str) -> None:
    """Print colored text to terminal only — not to log file."""
    print(text)

# ---------------------------------------------------------------------------
# PATHS  (relative to this script's location)
# ---------------------------------------------------------------------------

_BASE        = os.path.dirname(os.path.abspath(__file__))
_SPECS_PATH  = os.path.join(_BASE, "component_specs.json")
_SCHEMA_PATH = os.path.join(_BASE, "schemas", "component_specs_schema.json")
_LOG_PATH    = os.path.join(_BASE, "selection.log")

# ---------------------------------------------------------------------------
# LOGGER
# ---------------------------------------------------------------------------

def _setup_logger() -> logging.Logger:
    """
    Configure logger to write to both terminal and selection.log.
    Format: [YYYY-MM-DD HH:MM:SS] LEVEL: message
    """
    logger = logging.getLogger("component_selector")

    if logger.handlers:
        return logger   # already configured — avoid duplicate handlers

    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Terminal handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File handler
    fh = logging.FileHandler(_LOG_PATH, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger


log = _setup_logger()

# ---------------------------------------------------------------------------
# CORE VALIDATION
# ---------------------------------------------------------------------------

def validate_specs(specs_path: str = None) -> dict:
    """
    Load and validate component_specs.json against the JSON schema.

    Args:
        specs_path: path to component_specs.json.
                    Defaults to component_specs.json in project root.

    Returns:
        Parsed and validated specs dict.

    Exits with code 1 on:
        - jsonschema not installed
        - specs file not found
        - schema file not found
        - JSON parse error
        - schema validation failure
    """
    specs_path  = specs_path  or _SPECS_PATH
    schema_path = _SCHEMA_PATH

    _print_color(_c("=" * 60, "cyan"))
    _print_color(_c("  Component Selector — Input Validation", "bold"))
    _print_color(_c("=" * 60, "cyan"))
    log.info("=" * 60)
    log.info("Component Selector — Input Validation")
    log.info("=" * 60)

    # --- Dependency check ---
    try:
        import jsonschema
    except ImportError:
        _print_color(_c("✖  jsonschema not installed.", "red"))
        _print_color(_c("   Fix: pip install jsonschema", "yellow"))
        log.error("jsonschema not installed.")
        log.error("Fix: pip install jsonschema")
        sys.exit(1)

    # --- File existence ---
    if not os.path.exists(specs_path):
        _print_color(_c(f"✖  Specs file not found: {specs_path}", "red"))
        log.error(f"Specs file not found: {specs_path}")
        log.error("Expected: component_specs.json in project root")
        sys.exit(1)

    if not os.path.exists(schema_path):
        _print_color(_c(f"✖  Schema file not found: {schema_path}", "red"))
        log.error(f"Schema file not found: {schema_path}")
        log.error("Expected: schemas/component_specs_schema.json")
        sys.exit(1)

    _print_color(f"  {_c('✔', 'green')}  Specs  : {specs_path}")
    _print_color(f"  {_c('✔', 'green')}  Schema : {schema_path}")
    log.info(f"Specs  : {specs_path}")
    log.info(f"Schema : {schema_path}")

    # --- JSON parse ---
    try:
        with open(specs_path, encoding="utf-8") as f:
            specs = json.load(f)
    except json.JSONDecodeError as e:
        _print_color(_c(f"✖  JSON parse error in {specs_path}", "red"))
        _print_color(_c(f"   {e}", "yellow"))
        log.error(f"JSON parse error in {specs_path}")
        log.error(f"  {e}")
        sys.exit(1)

    try:
        with open(schema_path, encoding="utf-8") as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        _print_color(_c(f"✖  JSON parse error in {schema_path}", "red"))
        _print_color(_c(f"   {e}", "yellow"))
        log.error(f"JSON parse error in {schema_path}")
        log.error(f"  {e}")
        sys.exit(1)

    # --- Schema validation ---
    try:
        jsonschema.validate(instance=specs, schema=schema)
    except jsonschema.ValidationError as e:
        _print_color(_c("✖  Schema validation FAILED", "red"))
        path_str = ' -> '.join(str(p) for p in e.absolute_path) or '(root)'
        _print_color(_c(f"   Field path : {path_str}", "yellow"))
        _print_color(_c(f"   Reason     : {e.message}", "yellow"))
        _print_color(_c("   Fix component_specs.json and re-run.", "yellow"))
        log.error("Schema validation FAILED")
        log.error(f"  Field path : {path_str}")
        log.error(f"  Reason     : {e.message}")
        log.error("Fix component_specs.json and re-run.")
        sys.exit(1)
    except jsonschema.SchemaError as e:
        _print_color(_c("✖  Schema file itself is invalid — this is a tool bug.", "red"))
        _print_color(_c(f"   {e.message}", "yellow"))
        log.error("Schema file itself is invalid — this is a tool bug.")
        log.error(f"  {e.message}")
        sys.exit(1)

    _print_color(f"  {_c('✔', 'green')}  {_c('Schema validation PASSED', 'green')}")
    log.info("Schema validation PASSED")

    # --- Content summary ---
    _log_summary(specs)

    return specs


# ---------------------------------------------------------------------------
# SUMMARY PRINTER
# ---------------------------------------------------------------------------

# Components the selector will skip — no search, no derating
_SKIP_TYPES = {"ic_fixed"}

# Maps type string to a display label
_TYPE_LABELS = {
    "inductor":          "Inductor",
    "cap_ceramic":       "Capacitor (ceramic)",
    "cap_electrolytic":  "Capacitor (electrolytic)",
    "diode_schottky":    "Diode (Schottky)",
    "resistor":          "Resistor",
    "mosfet":            "MOSFET",
    "ic_fixed":          "IC — fixed (skip)",
}


def _log_summary(specs: dict) -> None:
    """
    Print a human-readable summary of what needs to be selected.
    Separates fixed/skipped components from selectable ones.
    """
    project  = specs.get("project", "Unknown")
    profile  = specs.get("derating_profile", "Unknown")
    version  = specs.get("schema_version", "Unknown")
    comps    = specs.get("components", {})

    _print_color("")
    _print_color(_c("-" * 60, "cyan"))
    _print_color(f"  {_c('Project          :', 'white')} {_c(project, 'bold')}")
    _print_color(f"  {_c('Derating profile :', 'white')} {_c(profile.upper(), 'cyan')}")
    _print_color(f"  {_c('Schema version   :', 'white')} {version}")
    _print_color(f"  {_c('Total components :', 'white')} {len(comps)}")
    _print_color(_c("-" * 60, "cyan"))
    log.info("-" * 60)
    log.info(f"Project          : {project}")
    log.info(f"Derating profile : {profile}")
    log.info(f"Schema version   : {version}")
    log.info(f"Total components : {len(comps)}")
    log.info("-" * 60)

    selectable = {}
    skipped    = {}

    for ref, comp in comps.items():
        ctype = comp.get("type", "unknown")
        if ctype in _SKIP_TYPES:
            skipped[ref] = comp
        else:
            selectable[ref] = comp

    if skipped:
        _print_color(f"  {_c('Fixed / skipped', 'yellow')} ({len(skipped)}):")
        log.info(f"Fixed / skipped ({len(skipped)}):")
        for ref, comp in skipped.items():
            label = _TYPE_LABELS.get(comp.get("type"), comp.get("type"))
            part  = comp.get("part", "")
            _print_color(f"    {_c('—', 'yellow')}  {ref:8s}  {label}  {_c(part, 'yellow')}")
            log.info(f"  {ref:8s}  {label}  {part}")

    _print_color(f"  {_c('Selectable components', 'green')} ({len(selectable)}):")
    log.info(f"Selectable components ({len(selectable)}):")

    # Group by type for readability
    by_type = {}
    for ref, comp in selectable.items():
        ctype = comp.get("type", "unknown")
        by_type.setdefault(ctype, []).append((ref, comp))

    for ctype, entries in by_type.items():
        label = _TYPE_LABELS.get(ctype, ctype)
        _print_color(f"    {_c(label, 'cyan')}:")
        log.info(f"  {label}:")
        for ref, comp in entries:
            detail = _component_detail(ref, comp)
            _print_color(f"      {_c('✔', 'green')}  {_c(ref, 'bold'):10s}  {detail}")
            log.info(f"    {ref:8s}  {detail}")

    _print_color("")
    _print_color(_c("-" * 60, "cyan"))
    _print_color(
        f"  {_c('✔', 'green')}  "
        f"{_c('Validation complete.', 'green')}  "
        f"{_c(str(len(selectable)), 'bold')} components queued for selection."
    )
    _print_color(_c("=" * 60, "cyan"))
    log.info("-" * 60)
    log.info(f"Validation complete. {len(selectable)} components queued for selection.")
    log.info("=" * 60)


def _component_detail(ref: str, comp: dict) -> str:
    """
    Return a one-line summary string for a component.
    Covers all supported types.
    """
    ctype = comp.get("type", "")

    if ctype == "inductor":
        return (
            f"{comp.get('inductance_uH')}uH  "
            f"Isat>={comp.get('Isat_min_A')}A  "
            f"Irms>={comp.get('Irms_min_A')}A  "
            f"DCR<={comp.get('DCR_max_mOhm')}mOhm  "
            f"pkg={comp.get('package')}"
        )

    if ctype == "cap_ceramic":
        val = (
            f"{comp['capacitance_uF']}uF" if "capacitance_uF" in comp
            else f"{comp.get('capacitance_pF')}pF"
        )
        diel = comp.get("dielectric", "any")
        return (
            f"{val}  "
            f"V_work>={comp.get('V_working_min_V')}V  "
            f"diel={diel}  "
            f"pkg={comp.get('package')}"
        )

    if ctype == "cap_electrolytic":
        return (
            f"{comp.get('capacitance_uF')}uF  "
            f"V_work>={comp.get('V_working_min_V')}V  "
            f"ESR<={comp.get('ESR_max_mOhm', 'n/a')}mOhm  "
            f"pkg={comp.get('package')}"
        )

    if ctype == "diode_schottky":
        return (
            f"Vr>={comp.get('V_reverse_min_V')}V  "
            f"If>={comp.get('I_avg_min_A')}A  "
            f"Vf<={comp.get('Vf_max_V', 'n/a')}V  "
            f"pkg={comp.get('package')}"
        )

    if ctype == "resistor":
        val = (
            f"{comp['resistance_kOhm']}kOhm" if "resistance_kOhm" in comp
            else f"{comp.get('resistance_Ohm')}Ohm"
        )
        fb = "FB/timing" if comp.get("is_feedback_or_timing") else ""
        return (
            f"{val}  "
            f"tol={comp.get('tolerance_pct')}%  "
            f"pkg={comp.get('package')}  "
            f"{fb}"
        ).strip()

    if ctype == "mosfet":
        return (
            f"Vds>={comp.get('Vds_max_V')}V  "
            f"Id>={comp.get('Id_min_A')}A  "
            f"pkg={comp.get('package')}"
        )

    return str(comp)


# ---------------------------------------------------------------------------
# CLI ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate component_specs.json against JSON schema."
    )
    parser.add_argument(
        "--specs",
        default=_SPECS_PATH,
        help="Path to component_specs.json (default: project root)"
    )
    args = parser.parse_args()

    specs = validate_specs(specs_path=args.specs)
    sys.exit(0)
