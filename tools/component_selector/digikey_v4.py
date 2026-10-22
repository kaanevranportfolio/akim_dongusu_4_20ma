"""
digikey_v4.py
DigiKey Product Information V4 — direct HTTP client (2-legged OAuth, client credentials).

Replaces the v3-only `digikey` python library. requests only.
Token is kept in memory (never written to disk). Credentials come from the
environment variables DIGIKEY_CLIENT_ID / DIGIKEY_CLIENT_SECRET (.env via python-dotenv).
Headers, tokens and secrets are never logged and never put into error messages.

Contract: tools/component_selector/README.md ("DigiKey Product Information V4").
"""

try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

import os
import time
import logging

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

log = logging.getLogger("component_selector")

TOKEN_URL = "https://api.digikey.com/v1/oauth2/token"
API_BASE = "https://api.digikey.com/products/v4"
_TIMEOUT_S = 30
_EXPIRY_MARGIN_S = 60          # renew this long before expires_in runs out
_DEFAULT_RETRY_WAIT_S = 5      # when 429 carries no usable Retry-After
_MAX_RETRY_WAIT_S = 60


class DigiKeyError(Exception):
    """Base class. Messages never contain tokens, secrets or request headers."""


class DigiKeyAuthError(DigiKeyError):
    """401: credentials, or the app is not subscribed to Product Information V4."""


class DigiKeyForbiddenError(DigiKeyError):
    """403: the app has no access to this resource."""


class DigiKeyRateLimitError(DigiKeyError):
    """429 after the single allowed retry."""


_token = {"value": None, "expires_at": 0.0}


def _credentials() -> tuple:
    cid = os.environ.get("DIGIKEY_CLIENT_ID", "")
    secret = os.environ.get("DIGIKEY_CLIENT_SECRET", "")
    if not cid:
        raise DigiKeyAuthError("DIGIKEY_CLIENT_ID is not set (.env or environment)")
    if not secret:
        raise DigiKeyAuthError("DIGIKEY_CLIENT_SECRET is not set (.env or environment)")
    return cid, secret


def _error_detail(resp) -> str:
    """Short server-side reason, never the request. Truncated; body only."""
    try:
        body = resp.json()
        if isinstance(body, dict):
            for k in ("ErrorMessage", "error_description", "detail", "title", "message"):
                if body.get(k):
                    return str(body[k])[:200]
    except ValueError:
        pass
    return ""


def _raise_for_status(resp, what: str) -> None:
    code = resp.status_code
    if code < 400:
        return
    detail = _error_detail(resp)
    msg = f"{what}: HTTP {code}" + (f" - {detail}" if detail else "")
    if code == 401:
        raise DigiKeyAuthError(msg)
    if code == 403:
        raise DigiKeyForbiddenError(msg)
    if code == 429:
        raise DigiKeyRateLimitError(msg)
    raise DigiKeyError(msg)


def get_token(force: bool = False) -> str:
    """Return a valid access token, fetching a new one when missing or about to expire."""
    now = time.monotonic()
    if not force and _token["value"] and now < _token["expires_at"]:
        return _token["value"]

    cid, secret = _credentials()
    resp = requests.post(
        TOKEN_URL,
        data={"client_id": cid, "client_secret": secret, "grant_type": "client_credentials"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=_TIMEOUT_S,
    )
    _raise_for_status(resp, "token request")
    try:
        body = resp.json()
        token = body["access_token"]
        expires_in = float(body.get("expires_in", 600))
    except (ValueError, KeyError, TypeError):
        raise DigiKeyError("token request: response has no usable access_token")
    _token["value"] = token
    _token["expires_at"] = now + max(expires_in - _EXPIRY_MARGIN_S, 0.0)
    return token


def _retry_wait(resp) -> float:
    try:
        wait = float(resp.headers.get("Retry-After", _DEFAULT_RETRY_WAIT_S))
    except (TypeError, ValueError):
        wait = _DEFAULT_RETRY_WAIT_S
    return min(max(wait, 0.0), _MAX_RETRY_WAIT_S)


def _request(method: str, path: str, **kwargs) -> dict:
    cid, _ = _credentials()
    url = API_BASE + path
    resp = None
    for attempt in (1, 2):
        headers = {
            "Authorization": f"Bearer {get_token()}",
            "X-DIGIKEY-Client-Id": cid,
            "Accept": "application/json",
        }
        resp = requests.request(method, url, headers=headers, timeout=_TIMEOUT_S, **kwargs)
        if resp.status_code == 429 and attempt == 1:
            wait = _retry_wait(resp)
            log.warning("DigiKey 429: waiting %.0f s, one retry", wait)
            time.sleep(wait)
            continue
        break
    _raise_for_status(resp, f"{method} {path.split('?')[0].rsplit('/', 1)[-1] or path}")
    try:
        return resp.json()
    except ValueError:
        raise DigiKeyError(f"{method} {path}: response is not JSON")


def keyword_search(keywords: str, limit: int = 10, offset: int = 0, **filters) -> dict:
    """
    POST /products/v4/search/keyword. Returns the raw JSON dict (Products, ProductsCount, ...).
    `filters` are passed through as KeywordRequest fields (FilterOptionsRequest, SortOptions).
    """
    body = {"Keywords": keywords, "Limit": limit, "Offset": offset}
    body.update(filters)
    return _request("POST", "/search/keyword", json=body)


def product_details(product_number: str) -> dict:
    """GET /products/v4/search/{productNumber}/productdetails. Returns raw JSON (key: Product)."""
    from urllib.parse import quote
    return _request("GET", f"/search/{quote(product_number, safe='')}/productdetails")
