"""
ranker.py
Component Selector — Candidate Filter and Ranker
v1.0 | May 2026

Takes raw candidates from search_digikey.py, applies derating rules from
derating_rules.py, and returns a ranked list of valid candidates.

Ranking priority (highest to lowest):
    1. Derating PASS — rejected candidates never appear in output
    2. Lifecycle — Active > NRND (flagged but allowed if no alternative)
    3. Stock availability — higher stock ranked higher
    4. Lead time — shorter ranked higher
    5. Unit price — lower ranked higher

Usage (imported by select_components.py):
    from ranker import rank_candidates
    ranked = rank_candidates(ref, spec, candidates, profile)

Usage (standalone test):
    python ranker.py
"""

import os
import sys
import json
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from derating_rules import (
    load_profile,
    check_inductor,
    check_capacitor_ceramic,
    check_capacitor_electrolytic,
    check_diode_schottky,
    check_resistor,
    check_lifecycle,
    check_lead_time,
)

# ---------------------------------------------------------------------------
# LOGGER
# ---------------------------------------------------------------------------

log = logging.getLogger("component_selector")
if not log.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

# ---------------------------------------------------------------------------
# DERATING DISPATCHER
# ---------------------------------------------------------------------------

def _apply_derating(component_type: str, requirements: dict,
                    candidate: dict, M: dict) -> dict:
    """
    Dispatch to the correct derating check function based on component type.

    Returns derating summary dict with overall PASS/FAIL and per-rule breakdown.
    If component_type is unknown, returns a PASS with a warning note.
    """
    if component_type == "inductor":
        return check_inductor(requirements, candidate, M)

    if component_type == "cap_ceramic":
        return check_capacitor_ceramic(requirements, candidate, M)

    if component_type == "cap_electrolytic":
        return check_capacitor_electrolytic(requirements, candidate, M)

    if component_type == "diode_schottky":
        return check_diode_schottky(requirements, candidate, M)

    if component_type == "resistor":
        return check_resistor(requirements, candidate, M)

    # Unknown type — pass through with flag
    return {
        "overall":      "PASS",
        "rules":        [],
        "failed_rules": [],
        "_note":        f"No derating rules defined for type '{component_type}'"
    }


# ---------------------------------------------------------------------------
# SCORING
# ---------------------------------------------------------------------------

_LIFECYCLE_SCORE = {
    "active":                           0,
    "last time buy":                    10,
    "nrnd":                             20,
    "not recommended for new designs":  20,
    "obsolete":                         9999,   # should never reach ranker
    "eol":                              9999,
}


def _score_candidate(candidate: dict, M: dict) -> float:
    """
    Compute a ranking score for a candidate. Lower is better.

    Scoring criteria (lead time intentionally excluded — informational only):
        lifecycle penalty  0–20  (Active=0, NRND=20)
        stock penalty      0–50  (high stock = low penalty)
        price penalty      0–10  (low price = low penalty)
    """
    score = 0.0

    # --- Lifecycle ---
    lc = (candidate.get("lifecycle") or "").lower().strip()
    score += _LIFECYCLE_SCORE.get(lc, 5)

    # --- Stock ---
    stock = candidate.get("stock") or 0
    if stock == 0:
        score += 50
    elif stock < 100:
        score += 40
    elif stock < 500:
        score += 30
    elif stock < 1000:
        score += 20
    elif stock < 5000:
        score += 10
    else:
        score += 0

    # --- Price ---
    price = candidate.get("unit_price_usd")
    if price is None:
        score += 5
    elif price > 10:
        score += 10
    elif price > 5:
        score += 7
    elif price > 1:
        score += 4
    elif price > 0.5:
        score += 2
    else:
        score += 0

    return score


# ---------------------------------------------------------------------------
# MAIN RANKER
# ---------------------------------------------------------------------------

_TOP_N = 3   # number of ranked candidates to return per component


def rank_candidates(ref: str, spec: dict, candidates: list,
                    profile_name: str) -> dict:
    """
    Filter candidates through derating rules and rank survivors.

    Args:
        ref:          reference designator e.g. "L1"
        spec:         component spec dict from component_specs.json
        candidates:   raw candidate list from search_digikey.search_component()
        profile_name: derating profile name e.g. "industrial"

    Returns dict:
        {
            "ref":          "L1",
            "type":         "inductor",
            "status":       "OK" | "NO_CANDIDATE" | "ALL_REJECTED",
            "selected":     { ...top candidate... },
            "alternatives": [ ...up to 2 more... ],
            "rejected":     [ ...rejected candidates with reasons... ],
            "flags":        [ ...lifecycle/lead time flags... ],
            "derating_applied": [ ...rules applied... ],
        }
    """
    ctype        = spec.get("type", "unknown")
    M            = load_profile(profile_name)
    passed       = []
    rejected     = []
    flags        = []

    log.info(f"  {ref}: ranking {len(candidates)} candidates — profile={profile_name}")

    for candidate in candidates:
        mpn = candidate.get("mpn", "?")

        # --- Lifecycle check ---
        lc_result = check_lifecycle(candidate.get("lifecycle"))
        if lc_result["status"] == "FAIL":
            rejected.append({
                "mpn":    mpn,
                "reason": lc_result["note"],
                "derating": None,
            })
            log.debug(f"    {mpn}: REJECTED — {lc_result['note']}")
            continue

        if lc_result["status"] == "FLAG":
            flags.append(f"{ref} / {mpn}: {lc_result['note']}")

        # --- Lead time check — informational only, never affects selection ---
        lt_result = check_lead_time(candidate.get("lead_time_weeks"), M)
        if lt_result["status"] == "FLAG":
            # Only flag the selected part's lead time — not every candidate
            candidate["_lt_flag"] = lt_result["note"]

        # --- Derating check ---
        derating = _apply_derating(ctype, spec, candidate, M)

        if derating["overall"] == "FAIL":
            rejected.append({
                "mpn":    mpn,
                "reason": f"Derating FAIL — rules: {derating['failed_rules']}",
                "derating": derating,
            })
            log.debug(f"    {mpn}: REJECTED — derating FAIL on {derating['failed_rules']}")
            continue

        # --- Candidate passed — add score ---
        candidate["_derating"] = derating
        candidate["_score"]    = _score_candidate(candidate, M)
        passed.append(candidate)
        log.debug(f"    {mpn}: PASS — score={candidate['_score']:.1f}")

    # --- Sort by score (lower is better) ---
    passed.sort(key=lambda c: c["_score"])

    # --- Build derating_applied summary from top candidate ---
    derating_applied = []
    if passed:
        for rule in passed[0]["_derating"].get("rules", []):
            derating_applied.append(
                f"{rule['rule']}: {rule['note']} → {rule['status']}"
            )

    # --- Build output ---
    if not passed:
        status = "NO_CANDIDATE" if not candidates else "ALL_REJECTED"
        log.warning(f"  {ref}: {status} — "
                    f"{len(rejected)} rejected, {len(candidates)} searched")
        return {
            "ref":             ref,
            "type":            ctype,
            "status":          status,
            "selected":        None,
            "alternatives":    [],
            "rejected":        rejected[:5],   # cap at 5 for readability
            "flags":           flags,
            "derating_applied": derating_applied,
        }

    selected     = passed[0]
    alternatives = passed[1:_TOP_N]

    # Surface lead time flag for selected part only
    if selected.get("_lt_flag"):
        flags.append(f"{ref} lead time: {selected['_lt_flag']}")

    log.info(f"  {ref}: selected {selected['mpn']} "
             f"(score={selected['_score']:.1f}, "
             f"{len(passed)} passed, {len(rejected)} rejected)")

    return {
        "ref":             ref,
        "type":            ctype,
        "status":          "OK",
        "selected":        selected,
        "alternatives":    alternatives,
        "rejected":        rejected[:5],
        "flags":           flags,
        "derating_applied": derating_applied,
    }


# ---------------------------------------------------------------------------
# STANDALONE TEST — runs against real DigiKey data
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    _BASE       = os.path.dirname(os.path.abspath(__file__))
    _SPECS_PATH = os.path.join(_BASE, "component_specs.json")

    parser = argparse.ArgumentParser(
        description="Test ranker against DigiKey live data."
    )
    parser.add_argument(
        "--ref",
        default=None,
        help="Reference designator to test e.g. --ref L1. Omit to test all."
    )
    args = parser.parse_args()

    # Load specs
    with open(_SPECS_PATH, encoding="utf-8") as f:
        specs_data = json.load(f)

    profile  = specs_data.get("derating_profile", "industrial")
    comps    = specs_data.get("components", {})

    if args.ref:
        if args.ref not in comps:
            print(f"ERROR: '{args.ref}' not found in component_specs.json")
            sys.exit(1)
        to_rank = {args.ref: comps[args.ref]}
    else:
        to_rank = {k: v for k, v in comps.items()
                   if v.get("type") != "ic_fixed"}

    # Import search
    try:
        from search_digikey import search_component
    except ImportError:
        print("ERROR: search_digikey.py not found.")
        sys.exit(1)

    print(f"\nRanker Test — {len(to_rank)} component(s) — profile: {profile}\n")
    print(f"{'─'*70}")

    all_ok    = True
    no_result = []

    for ref, spec in to_rank.items():
        ctype = spec.get("type")
        if ctype == "ic_fixed":
            continue

        candidates = search_component(ref, spec)
        result     = rank_candidates(ref, spec, candidates, profile)

        status = result["status"]
        print(f"\n  {ref} ({ctype})")

        if status == "OK":
            s = result["selected"]
            price = f"${s['unit_price_usd']:.4f}" if s.get("unit_price_usd") else "price N/A"
            stock = s.get("stock", 0)
            lc    = s.get("lifecycle", "?")
            lt    = f"{s.get('lead_time_weeks')}wk" if s.get("lead_time_weeks") else "lead N/A"
            print(f"    ✔  SELECTED : {s['mpn']:35s} {s['manufacturer']}")
            print(f"       Price    : {price}   Stock: {stock}   Lead: {lt}   Lifecycle: {lc}")
            print(f"       DK PN    : {s.get('digikey_pn', 'N/A')}")
            if result["alternatives"]:
                for i, alt in enumerate(result["alternatives"], 2):
                    ap = f"${alt['unit_price_usd']:.4f}" if alt.get("unit_price_usd") else "N/A"
                    print(f"    [{i}] ALT      : {alt['mpn']:35s} {ap}")
            if result["flags"]:
                for flag in result["flags"]:
                    print(f"    ⚠  FLAG     : {flag}")
            if result["rejected"]:
                print(f"       Rejected : {len(result['rejected'])} candidates")
                for r in result["rejected"][:2]:
                    print(f"         ✖ {r['mpn']:30s} {r['reason'][:60]}")
        else:
            all_ok = False
            no_result.append(ref)
            print(f"    ✖  {status}")
            for r in result["rejected"][:3]:
                print(f"       ✖ {r['mpn']:30s} {r['reason'][:60]}")

        if result["derating_applied"]:
            print(f"       Derating :")
            for d in result["derating_applied"]:
                print(f"         {d}")

    print(f"\n{'─'*70}")
    if all_ok:
        print(f"  ✔  All components selected successfully.")
    else:
        print(f"  ✖  No candidate found for: {', '.join(no_result)}")
    print()
