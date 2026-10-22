"""
tests/test_derating.py
Component Selector — Derating Rules Test Suite
v1.0 | May 2026

Driven entirely from JSON fixture files in tests/fixtures/.
Adding a new test case = adding a JSON file. No Python edits required.

Run from project root:
    pytest tests/test_derating.py -v
"""

import json
import os
import sys
import pytest

# Make sure project root is on the path so derating_rules imports cleanly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
# FIXTURE LOADER
# ---------------------------------------------------------------------------

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

DISPATCHER = {
    "inductor":           check_inductor,
    "cap_ceramic":        check_capacitor_ceramic,
    "cap_electrolytic":   check_capacitor_electrolytic,
    "diode_schottky":     check_diode_schottky,
    "resistor":           check_resistor,
}


def load_fixtures():
    """Load all JSON fixture files from tests/fixtures/. Returns list of (name, data) tuples."""
    fixtures = []
    if not os.path.exists(FIXTURES_DIR):
        return fixtures
    for filename in sorted(os.listdir(FIXTURES_DIR)):
        if filename.endswith(".json") and not filename.startswith("digikey_v4_"):
            path = os.path.join(FIXTURES_DIR, filename)
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            fixtures.append((filename, data))
    return fixtures


def pytest_generate_tests(metafunc):
    """Dynamically parametrise test_fixture with every JSON file found."""
    if "fixture_name" in metafunc.fixturenames and "fixture_data" in metafunc.fixturenames:
        fixtures = load_fixtures()
        metafunc.parametrize(
            "fixture_name,fixture_data",
            fixtures,
            ids=[f[0].replace(".json", "") for f in fixtures]
        )


# ---------------------------------------------------------------------------
# MAIN PARAMETRISED TEST
# ---------------------------------------------------------------------------

def test_fixture(fixture_name, fixture_data):
    """
    Run a single fixture file through the derating engine.
    Asserts overall PASS/FAIL and failed_rules match expected values.
    """
    component_type   = fixture_data["component_type"]
    profile_name     = fixture_data["derating_profile"]
    requirements     = fixture_data["requirements"]
    candidate        = fixture_data["candidate"]
    expected         = fixture_data["expected"]

    assert component_type in DISPATCHER, (
        f"[{fixture_name}] Unknown component_type '{component_type}'. "
        f"Valid types: {list(DISPATCHER.keys())}"
    )

    M      = load_profile(profile_name)
    check  = DISPATCHER[component_type]
    result = check(requirements, candidate, M)

    assert result["overall"] == expected["overall"], (
        f"\n[{fixture_name}] Overall result mismatch.\n"
        f"  Expected : {expected['overall']}\n"
        f"  Got      : {result['overall']}\n"
        f"  Description: {fixture_data.get('description', '')}\n"
        f"  Failed rules: {result['failed_rules']}\n"
        f"  All rules:\n" +
        "\n".join(
            f"    {r['rule']:12s} {r['status']}  required={r['required']}  actual={r['actual']}"
            for r in result["rules"]
        )
    )

    assert sorted(result["failed_rules"]) == sorted(expected["failed_rules"]), (
        f"\n[{fixture_name}] Failed rules mismatch.\n"
        f"  Expected failed : {sorted(expected['failed_rules'])}\n"
        f"  Got failed      : {sorted(result['failed_rules'])}\n"
        f"  Description: {fixture_data.get('description', '')}"
    )


# ---------------------------------------------------------------------------
# LIFECYCLE TESTS  (not fixture-driven — simple and stable)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("lifecycle,expected_status", [
    ("Active",                        "PASS"),
    ("active",                        "PASS"),
    ("EOL",                           "FAIL"),
    ("End of Life",                   "FAIL"),
    ("Obsolete",                      "FAIL"),
    ("NRND",                          "FLAG"),
    ("Not Recommended for New Design","FLAG"),
    (None,                            "FLAG"),
])
def test_lifecycle(lifecycle, expected_status):
    result = check_lifecycle(lifecycle)
    assert result["status"] == expected_status, (
        f"Lifecycle '{lifecycle}': expected {expected_status}, got {result['status']}"
    )


# ---------------------------------------------------------------------------
# LEAD TIME TESTS
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("weeks,profile,expected_status", [
    (4,    "industrial", "PASS"),
    (12,   "industrial", "PASS"),
    (13,   "industrial", "FLAG"),
    (16,   "hobby",      "PASS"),   # hobby threshold is 16 weeks
    (17,   "hobby",      "FLAG"),
    (None, "industrial", "FLAG"),
])
def test_lead_time(weeks, profile, expected_status):
    M = load_profile(profile)
    result = check_lead_time(weeks, M)
    assert result["status"] == expected_status, (
        f"Lead time {weeks}wk / profile '{profile}': "
        f"expected {expected_status}, got {result['status']}"
    )
