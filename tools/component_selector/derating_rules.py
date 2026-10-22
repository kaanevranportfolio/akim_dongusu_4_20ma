"""
derating_rules.py
Component Selector — Derating Engine
v2.0 | May 2026

Loads all derating multipliers from config/derating_profiles.json at runtime.
No hardcoded values. Profile is selected by the caller.

Public API:
    load_profile(profile_name)     -> dict of multipliers for that profile
    check_inductor(req, cand, M)   -> summary dict
    check_capacitor_ceramic(...)   -> summary dict
    check_capacitor_electrolytic(...)
    check_diode_schottky(...)
    check_resistor(...)
    check_lifecycle(lifecycle_str) -> dict
    check_lead_time(weeks, M)      -> dict

All check_* functions return:
    {
        "overall":      "PASS" | "FAIL",
        "rules":        [ { rule, required, actual, status, note } ],
        "failed_rules": [ "RuleName", ... ]
    }
"""

import json
import os

# ---------------------------------------------------------------------------
# PROFILE LOADER
# ---------------------------------------------------------------------------

_PROFILES_PATH = os.path.join(os.path.dirname(__file__), "config", "derating_profiles.json")
_PROFILES_CACHE = None

LIFECYCLE_REJECTED = {"eol", "end of life", "obsolete"}
LIFECYCLE_FLAGGED  = {"nrnd", "not recommended for new design"}


def load_profile(profile_name: str) -> dict:
    """
    Load derating multipliers for the given profile name from
    config/derating_profiles.json. Results are cached after first load.

    Args:
        profile_name: one of 'hobby', 'commercial', 'industrial', 'military'

    Returns:
        dict with keys: capacitor_ceramic, capacitor_electrolytic,
                        inductor, diode_schottky, resistor, mosfet, general

    Raises:
        FileNotFoundError: if derating_profiles.json is not found
        KeyError: if profile_name is not defined in the file
    """
    global _PROFILES_CACHE

    if _PROFILES_CACHE is None:
        if not os.path.exists(_PROFILES_PATH):
            raise FileNotFoundError(
                f"Derating profiles not found at: {_PROFILES_PATH}\n"
                f"Expected: config/derating_profiles.json relative to derating_rules.py"
            )
        with open(_PROFILES_PATH, encoding="utf-8") as f:
            _PROFILES_CACHE = json.load(f)

    profiles = _PROFILES_CACHE.get("profiles", {})
    if profile_name not in profiles:
        valid = list(profiles.keys())
        raise KeyError(
            f"Profile '{profile_name}' not found in derating_profiles.json. "
            f"Valid profiles: {valid}"
        )

    return profiles[profile_name]


# ---------------------------------------------------------------------------
# RESULT BUILDER  (internal helpers)
# ---------------------------------------------------------------------------

def _rule_status(passed: bool, note: str) -> str:
    """FAIL, ASSUMED_VERIFY (passed only because vendor data is missing) or PASS."""
    if not passed:
        return "FAIL"
    if "not in vendor data" in note.lower():
        return "ASSUMED_VERIFY"
    return "PASS"


def _rule(name: str, required, actual, unit: str, passed: bool, note: str = "") -> dict:
    """Build a single derating rule result dict."""
    return {
        "rule":     name,
        "required": f"{required:.4g} {unit}".strip() if isinstance(required, (int, float)) else str(required),
        "actual":   f"{actual:.4g} {unit}".strip()   if isinstance(actual,   (int, float)) else "NOT PROVIDED",
        "status":   _rule_status(passed, note),
        "note":     note,
    }


def _summary(rules: list) -> dict:
    """Summarise a list of rule results into an overall PASS/FAIL dict."""
    failed = [r for r in rules if r["status"] == "FAIL"]
    return {
        "overall":      "PASS" if not failed else "FAIL",
        "assumed_rules": [r["rule"] for r in rules if r["status"] == "ASSUMED_VERIFY"],
        "rules":        rules,
        "failed_rules": [r["rule"] for r in failed],
    }


# ---------------------------------------------------------------------------
# INDUCTOR
# ---------------------------------------------------------------------------

def check_inductor(requirements: dict, candidate: dict, M: dict) -> dict:
    """
    Validate an inductor candidate against derating rules.
    Missing parametric data → PASS with manual verification flag.
    Only rejects when data exists and fails the threshold.
    """
    rules = []
    ind = M["inductor"]

    # Isat
    isat_req  = requirements.get("Isat_min_A")
    isat_cand = candidate.get("isat_A")
    if isat_req is not None:
        isat_min = ind["isat_multiplier"] * isat_req
        if isat_cand is None:
            rules.append(_rule(
                "Isat", isat_min, isat_cand, "A", True,
                note=f"Isat not in vendor data — verify datasheet: need >= {isat_min:.3f}A"
            ))
        else:
            passed = isat_cand >= isat_min
            rules.append(_rule(
                "Isat", isat_min, isat_cand, "A", passed,
                note=f"{ind['isat_multiplier']}x {isat_req}A (peak) = {isat_min:.3f}A required"
            ))

    # Irms
    irms_req  = requirements.get("Irms_min_A")
    irms_cand = candidate.get("irms_A")
    if irms_req is not None:
        irms_min = ind["irms_multiplier"] * irms_req
        if irms_cand is None:
            rules.append(_rule(
                "Irms", irms_min, irms_cand, "A", True,
                note=f"Irms not in vendor data — verify datasheet: need >= {irms_min:.3f}A"
            ))
        else:
            passed = irms_cand >= irms_min
            rules.append(_rule(
                "Irms", irms_min, irms_cand, "A", passed,
                note=f"{ind['irms_multiplier']}x {irms_req}A (rms) = {irms_min:.3f}A required"
            ))

    # DCR — absolute limit, no multiplier
    dcr_max  = requirements.get("DCR_max_mOhm")
    dcr_cand = candidate.get("dcr_mOhm")
    if dcr_max is not None:
        if dcr_cand is None:
            rules.append(_rule(
                "DCR", dcr_max, dcr_cand, "mOhm", True,
                note=f"DCR not in vendor data — verify datasheet: need <= {dcr_max} mOhm"
            ))
        else:
            passed = dcr_cand <= dcr_max
            rules.append(_rule(
                "DCR", dcr_max, dcr_cand, "mOhm", passed,
                note=f"Must be <= {dcr_max} mOhm (absolute spec — no multiplier)"
            ))

    # SRF — only checked if both provided
    srf_cand = candidate.get("srf_MHz")
    fsw_kHz  = requirements.get("switching_freq_kHz")
    if srf_cand is not None and fsw_kHz is not None:
        srf_min = ind["srf_multiplier"] * fsw_kHz / 1000
        passed  = srf_cand >= srf_min
        rules.append(_rule(
            "SRF", srf_min, srf_cand, "MHz", passed,
            note=f"{ind['srf_multiplier']}x {fsw_kHz}kHz = {srf_min:.1f}MHz required"
        ))

    return _summary(rules)


# ---------------------------------------------------------------------------
# CAPACITOR — CERAMIC (MLCC)
# ---------------------------------------------------------------------------

def check_capacitor_ceramic(requirements: dict, candidate: dict, M: dict) -> dict:
    """
    Validate an MLCC ceramic capacitor candidate.

    Args:
        requirements: V_working_min_V, dielectric (optional), Irms_min_A (optional),
                      ESR_max_mOhm (optional)
        candidate:    v_rated_V, dielectric, irms_A (optional), esr_mOhm (optional)
        M:            profile dict from load_profile()
    """
    rules = []
    cap = M["capacitor_ceramic"]

    ACCEPTED = {"X7R", "X5R", "C0G", "NP0"}
    REJECTED  = {"Y5V", "Z5U", "Y5U"}

    # Voltage
    v_work = requirements.get("V_working_min_V")
    v_rated = candidate.get("v_rated_V")
    if v_work is not None:
        v_min = cap["voltage_multiplier"] * v_work
        passed = (v_rated is not None) and (v_rated >= v_min)
        rules.append(_rule(
            "Voltage", v_min, v_rated, "V", passed,
            note=f"{cap['voltage_multiplier']}x {v_work}V = {v_min}V required"
        ))

    # Dielectric
    req_diel  = requirements.get("dielectric", "").upper().strip()
    cand_diel = candidate.get("dielectric",    "").upper().strip()
    if req_diel:
        passed = cand_diel == req_diel
        if cand_diel in REJECTED:
            note = f"REJECTED: {cand_diel} prohibited — capacitance varies +-80% with temperature"
        elif not passed:
            note = f"Spec requires {req_diel}, candidate is {cand_diel or 'NOT PROVIDED'}"
        else:
            note = f"{cand_diel} matches required {req_diel}"
        rules.append(_rule("Dielectric", req_diel, cand_diel, "", passed, note=note))
    elif cand_diel in REJECTED:
        rules.append(_rule(
            "Dielectric", "Not Y5V/Z5U", cand_diel, "", False,
            note=f"REJECTED: {cand_diel} prohibited for power applications"
        ))

    # Irms
    irms_req  = requirements.get("Irms_min_A")
    irms_cand = candidate.get("irms_A")
    if irms_req is not None:
        if irms_cand is None:
            # Parameter not available from vendor — flag for review, do not reject
            rules.append(_rule(
                "Irms", irms_req, irms_cand, "A", True,
                note="Ripple current not in vendor data — verify manually before ordering"
            ))
        else:
            passed = irms_cand >= irms_req
            rules.append(_rule(
                "Irms", irms_req, irms_cand, "A", passed,
                note="Ripple current — absolute thermal limit, no multiplier"
            ))

    # ESR
    esr_max  = requirements.get("ESR_max_mOhm")
    esr_cand = candidate.get("esr_mOhm")
    if esr_max is not None and esr_cand is not None:
        passed = esr_cand <= esr_max
        rules.append(_rule(
            "ESR", esr_max, esr_cand, "mOhm", passed,
            note=f"Must be <= {esr_max} mOhm — governs output voltage ripple"
        ))

    return _summary(rules)


# ---------------------------------------------------------------------------
# CAPACITOR — ELECTROLYTIC
# ---------------------------------------------------------------------------

def check_capacitor_electrolytic(requirements: dict, candidate: dict, M: dict) -> dict:
    """
    Validate an electrolytic capacitor candidate.

    Args:
        requirements: V_working_min_V, Irms_min_A (optional),
                      ESR_max_mOhm (optional), temp_max_C (optional)
        candidate:    v_rated_V, irms_A (optional),
                      esr_mOhm (optional), temp_rating_C (optional)
        M:            profile dict from load_profile()
    """
    rules = []
    cap = M["capacitor_electrolytic"]
    gen = M["general"]

    # Voltage
    v_work  = requirements.get("V_working_min_V")
    v_rated = candidate.get("v_rated_V")
    if v_work is not None:
        v_min = cap["voltage_multiplier"] * v_work
        passed = (v_rated is not None) and (v_rated >= v_min)
        rules.append(_rule(
            "Voltage", v_min, v_rated, "V", passed,
            note=f"{cap['voltage_multiplier']}x {v_work}V = {v_min}V required"
        ))

    # Irms
    irms_req  = requirements.get("Irms_min_A")
    irms_cand = candidate.get("irms_A")
    if irms_req is not None:
        if irms_cand is None:
            rules.append(_rule(
                "Irms", irms_req, irms_cand, "A", True,
                note="Ripple current not in vendor data — verify manually before ordering"
            ))
        else:
            passed = irms_cand >= irms_req
            rules.append(_rule(
                "Irms", irms_req, irms_cand, "A", passed,
                note="Ripple current — absolute thermal limit"
            ))

    # ESR
    esr_max  = requirements.get("ESR_max_mOhm")
    esr_cand = candidate.get("esr_mOhm")
    if esr_max is not None and esr_cand is not None:
        passed = esr_cand <= esr_max
        rules.append(_rule(
            "ESR", esr_max, esr_cand, "mOhm", passed,
            note=f"Must be <= {esr_max} mOhm — governs output voltage ripple"
        ))

    # Temperature
    temp_max    = requirements.get("temp_max_C")
    temp_rated  = candidate.get("temp_rating_C")
    if temp_max is not None and temp_rated is not None:
        temp_min = temp_max + cap["temp_margin_C"]
        passed = temp_rated >= temp_min
        rules.append(_rule(
            "Temperature", temp_min, temp_rated, "C", passed,
            note=f"{temp_max}C max + {cap['temp_margin_C']}C margin = {temp_min}C required"
        ))

    return _summary(rules)


# ---------------------------------------------------------------------------
# SCHOTTKY DIODE
# ---------------------------------------------------------------------------

def check_diode_schottky(requirements: dict, candidate: dict, M: dict) -> dict:
    """
    Validate a Schottky diode candidate.
    V_reverse is a hard safety rule — reject if data missing (it's always in the datasheet).
    I_avg and Vf — flag if missing, reject only if present and failing.
    """
    rules = []
    diode = M["diode_schottky"]

    # Reverse voltage — hard rule, always available, reject if missing
    vr_req  = requirements.get("V_reverse_min_V")
    vr_cand = candidate.get("v_reverse_V")
    if vr_req is not None:
        vr_min = diode["v_reverse_multiplier"] * vr_req
        if vr_cand is None:
            # V_reverse should always be in datasheet — reject if genuinely missing
            rules.append(_rule(
                "V_reverse", vr_min, vr_cand, "V", False,
                note=f"V_reverse not found — cannot verify {vr_min}V requirement. Reject."
            ))
        else:
            passed = vr_cand >= vr_min
            rules.append(_rule(
                "V_reverse", vr_min, vr_cand, "V", passed,
                note=f"{diode['v_reverse_multiplier']}x {vr_req}V = {vr_min}V required"
            ))

    # Average forward current — flag if missing
    if_req  = requirements.get("I_avg_min_A")
    if_cand = candidate.get("i_avg_A")
    if if_req is not None:
        if_min = diode["i_avg_multiplier"] * if_req
        if if_cand is None:
            rules.append(_rule(
                "I_avg", if_min, if_cand, "A", True,
                note=f"I_avg not in vendor data — verify datasheet: need >= {if_min}A"
            ))
        else:
            passed = if_cand >= if_min
            rules.append(_rule(
                "I_avg", if_min, if_cand, "A", passed,
                note=f"{diode['i_avg_multiplier']}x {if_req}A = {if_min}A required"
            ))

    # Forward voltage — flag if missing, reject if present and exceeds limit
    vf_max  = requirements.get("Vf_max_V")
    vf_cand = candidate.get("vf_V")
    if vf_max is not None:
        if vf_cand is None:
            rules.append(_rule(
                "Vf", vf_max, vf_cand, "V", True,
                note=f"Vf not in vendor data — verify datasheet: need <= {vf_max}V"
            ))
        else:
            passed = vf_cand <= vf_max
            rules.append(_rule(
                "Vf", vf_max, vf_cand, "V", passed,
                note=f"Must be <= {vf_max}V — affects efficiency directly (no multiplier)"
            ))

    return _summary(rules)


# ---------------------------------------------------------------------------
# RESISTOR
# ---------------------------------------------------------------------------

def check_resistor(requirements: dict, candidate: dict, M: dict) -> dict:
    """
    Validate a resistor candidate.

    Args:
        requirements: tolerance_pct, is_feedback_or_timing (bool),
                      P_actual_W (optional), V_actual_V (optional)
        candidate:    tolerance_pct, tempco_ppm (optional),
                      p_rated_W (optional), v_rated_V (optional)
        M:            profile dict from load_profile()
    """
    rules = []
    res = M["resistor"]

    # Tolerance — candidate must be equal or tighter than spec
    tol_req  = requirements.get("tolerance_pct")
    tol_cand = candidate.get("tolerance_pct")
    if tol_req is not None and tol_cand is not None:
        passed = tol_cand <= tol_req
        rules.append(_rule(
            "Tolerance", tol_req, tol_cand, "%", passed,
            note=f"Candidate tolerance must be <= specified {tol_req}%"
        ))

    # Power derating
    p_actual = requirements.get("P_actual_W")
    p_rated  = candidate.get("p_rated_W")
    if p_actual is not None and p_rated is not None:
        p_min = res["power_multiplier"] * p_actual
        passed = p_rated >= p_min
        rules.append(_rule(
            "Power", p_min, p_rated, "W", passed,
            note=f"{res['power_multiplier']}x {p_actual}W = {p_min}W required"
        ))

    # Voltage derating
    v_actual = requirements.get("V_actual_V")
    v_rated  = candidate.get("v_rated_V")
    if v_actual is not None and v_rated is not None:
        v_min = res["voltage_multiplier"] * v_actual
        passed = v_rated >= v_min
        rules.append(_rule(
            "Voltage", v_min, v_rated, "V", passed,
            note=f"{res['voltage_multiplier']}x {v_actual}V = {v_min}V required"
        ))

    # Tempco — feedback and timing resistors only
    is_fb = requirements.get("is_feedback_or_timing", False)
    if is_fb:
        tempco = candidate.get("tempco_ppm")
        if tempco is not None:
            tc_max = res["tempco_max_ppm"]
            passed = tempco <= tc_max
            rules.append(_rule(
                "Tempco", tc_max, tempco, "ppm/C", passed,
                note=f"Feedback/timing resistor: must be <= {tc_max} ppm/C"
            ))

    return _summary(rules)


# ---------------------------------------------------------------------------
# LIFECYCLE CHECK
# ---------------------------------------------------------------------------

def check_lifecycle(lifecycle_str) -> dict:
    """
    Check component lifecycle status.

    Returns:
        dict with status: PASS / FAIL / FLAG and a note
    """
    if lifecycle_str is None:
        return {"status": "FLAG", "note": "Lifecycle not provided — verify with manufacturer"}

    s = lifecycle_str.lower().strip()

    if any(r in s for r in LIFECYCLE_REJECTED):
        return {"status": "FAIL",  "note": f"REJECTED: '{lifecycle_str}' — do not use for new design"}
    if any(f in s for f in LIFECYCLE_FLAGGED):
        return {"status": "FLAG",  "note": f"NRND: '{lifecycle_str}' — use only if no alternative exists"}

    return {"status": "PASS", "note": f"Lifecycle OK: '{lifecycle_str}'"}


# ---------------------------------------------------------------------------
# LEAD TIME CHECK
# ---------------------------------------------------------------------------

def check_lead_time(lead_time_weeks, M: dict) -> dict:
    """
    Flag components with lead time exceeding profile threshold.
    Does not reject — flags for review.

    Args:
        lead_time_weeks: int or None
        M: profile dict from load_profile()
    """
    max_weeks = M["general"]["lead_time_max_weeks"]

    if lead_time_weeks is None:
        return {"status": "FLAG", "note": "Lead time not provided — verify with distributor"}
    if lead_time_weeks > max_weeks:
        return {"status": "FLAG", "note": f"Lead time {lead_time_weeks}wk exceeds {max_weeks}wk threshold"}

    return {"status": "PASS", "note": f"Lead time {lead_time_weeks}wk — within {max_weeks}wk limit"}
