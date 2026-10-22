"""
tests/test_digikey_v4.py
Offline tests (no network): digikey_v4.py HTTP client and the V4 -> candidate mapping
in search_digikey.py. All HTTP is mocked; the fixture is hand-written [A], not a real response.
"""

import json
import os
import sys
from unittest import mock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import digikey_v4
import search_digikey

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "digikey_v4_keyword_response.json")


def _load():
    with open(FIXTURE, encoding="utf-8") as f:
        return json.load(f)


def _resp(status=200, body=None, headers=None):
    r = mock.Mock()
    r.status_code = status
    r.headers = headers or {}
    r.json.return_value = body if body is not None else {}
    return r


@pytest.fixture(autouse=True)
def _env_and_token(monkeypatch):
    monkeypatch.setenv("DIGIKEY_CLIENT_ID", "test-id")
    monkeypatch.setenv("DIGIKEY_CLIENT_SECRET", "test-secret")
    digikey_v4._token.update(value=None, expires_at=0.0)
    yield
    digikey_v4._token.update(value=None, expires_at=0.0)


# --- token ------------------------------------------------------------------

def test_token_request_shape_and_cache():
    with mock.patch.object(digikey_v4.requests, "post",
                           return_value=_resp(200, {"access_token": "tok1", "expires_in": 599, "token_type": "Bearer"})) as post:
        assert digikey_v4.get_token() == "tok1"
        assert digikey_v4.get_token() == "tok1"      # cached: no second POST
    assert post.call_count == 1
    args, kwargs = post.call_args
    assert args[0] == "https://api.digikey.com/v1/oauth2/token"
    assert kwargs["data"] == {"client_id": "test-id", "client_secret": "test-secret", "grant_type": "client_credentials"}


def test_token_renewed_before_expiry():
    with mock.patch.object(digikey_v4.requests, "post",
                           side_effect=[_resp(200, {"access_token": "a", "expires_in": 599}),
                                        _resp(200, {"access_token": "b", "expires_in": 599})]):
        assert digikey_v4.get_token() == "a"
        digikey_v4._token["expires_at"] = 0.0         # simulate expiry
        assert digikey_v4.get_token() == "b"


def test_missing_credentials_named_without_values(monkeypatch):
    monkeypatch.delenv("DIGIKEY_CLIENT_ID")
    with pytest.raises(digikey_v4.DigiKeyAuthError) as e:
        digikey_v4.get_token()
    assert "DIGIKEY_CLIENT_ID" in str(e.value)


# --- API calls --------------------------------------------------------------

def _prime_token():
    digikey_v4._token.update(value="tok", expires_at=1e18)


def test_keyword_search_request_shape():
    _prime_token()
    with mock.patch.object(digikey_v4.requests, "request", return_value=_resp(200, {"Products": []})) as req:
        out = digikey_v4.keyword_search("inductor 4.7uH", limit=5, offset=2)
    assert out == {"Products": []}
    args, kwargs = req.call_args
    assert args == ("POST", "https://api.digikey.com/products/v4/search/keyword")
    assert kwargs["json"] == {"Keywords": "inductor 4.7uH", "Limit": 5, "Offset": 2}
    assert kwargs["headers"]["Authorization"] == "Bearer tok"
    assert kwargs["headers"]["X-DIGIKEY-Client-Id"] == "test-id"


def test_product_details_path_is_quoted():
    _prime_token()
    with mock.patch.object(digikey_v4.requests, "request", return_value=_resp(200, {"Product": {}})) as req:
        digikey_v4.product_details("A/B 1")
    assert req.call_args[0] == ("GET", "https://api.digikey.com/products/v4/search/A%2FB%201/productdetails")


@pytest.mark.parametrize("status,exc", [
    (401, digikey_v4.DigiKeyAuthError),
    (403, digikey_v4.DigiKeyForbiddenError),
])
def test_error_statuses(status, exc):
    _prime_token()
    with mock.patch.object(digikey_v4.requests, "request", return_value=_resp(status, {"ErrorMessage": "nope"})):
        with pytest.raises(exc) as e:
            digikey_v4.keyword_search("x")
    msg = str(e.value)
    assert str(status) in msg
    assert "tok" not in msg and "test-secret" not in msg and "Bearer" not in msg


def test_429_one_retry_with_retry_after():
    _prime_token()
    with mock.patch.object(digikey_v4.requests, "request",
                           side_effect=[_resp(429, {}, {"Retry-After": "3"}), _resp(200, {"Products": []})]) as req, \
         mock.patch.object(digikey_v4.time, "sleep") as sleep:
        digikey_v4.keyword_search("x")
    assert req.call_count == 2
    sleep.assert_called_once_with(3.0)


def test_429_twice_raises_no_third_try():
    _prime_token()
    with mock.patch.object(digikey_v4.requests, "request", return_value=_resp(429, {}, {"Retry-After": "1"})) as req, \
         mock.patch.object(digikey_v4.time, "sleep"):
        with pytest.raises(digikey_v4.DigiKeyRateLimitError):
            digikey_v4.keyword_search("x")
    assert req.call_count == 2


# --- V4 -> candidate mapping ------------------------------------------------

def test_mapping_full_inductor():
    p = _load()["Products"][0]
    c = search_digikey._normalise_product(p, "inductor")
    assert c["mpn"] == "EX-L-4R7"
    assert c["manufacturer"] == "Example Maker"
    assert c["description"].startswith("4.7 uH Shielded")
    assert c["lifecycle"] == "Active"
    assert c["datasheet"] == "https://example.invalid/ex-l-4r7.pdf"
    assert c["digikey_pn"] == "EX-L-4R7CT-ND"
    assert c["product_url"].startswith("https://www.digikey.com/")
    assert c["unit_price_usd"] == pytest.approx(0.42)
    assert c["stock"] == 1200
    assert c["lead_time_weeks"] == 12
    assert c["inductance_uH"] == pytest.approx(4.7)
    assert c["isat_A"] == pytest.approx(3.5)
    assert c["irms_A"] == pytest.approx(3.0)
    assert c["dcr_mOhm"] == pytest.approx(60 * 1e-3)   # existing _extract_float scaling, unchanged
    assert c["_raw_params"]["_raw_shielding"] == "Shielded"


def test_mapping_sparse_product_gives_none_not_invented():
    p = _load()["Products"][1]
    c = search_digikey._normalise_product(p, "inductor")
    assert c["mpn"] == "OT-0001"
    assert c["lifecycle"] is None
    assert c["datasheet"] is None
    assert c["digikey_pn"] is None
    assert c["unit_price_usd"] is None
    assert c["stock"] == 0
    assert c["lead_time_weeks"] is None
    assert c["description"] == "PARAMETER NOT AVAILABLE"
    assert c["inductance_uH"] is None


def test_search_component_uses_v4_client_and_returns_candidates():
    spec = {"type": "inductor", "inductance_uH": 4.7}
    with mock.patch.object(search_digikey.digikey_v4, "keyword_search", return_value=_load()) as ks:
        out = search_digikey.search_component("L1", spec)
    assert [c["mpn"] for c in out] == ["EX-L-4R7", "OT-0001"]
    assert ks.call_args[0][0] == "inductor 4.7uH"


def test_search_component_api_error_returns_empty():
    spec = {"type": "inductor", "inductance_uH": 4.7}
    with mock.patch.object(search_digikey.digikey_v4, "keyword_search",
                           side_effect=digikey_v4.DigiKeyAuthError("HTTP 401")):
        assert search_digikey.search_component("L1", spec) == []
