# backend/tests/test_cors.py
import os
from starlette.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_cors_preflight_allowed_origin():
    # Simulate frontend origin (allowed)
    headers = {
        "Origin": os.getenv("TEST_ALLOWED_ORIGIN", "http://localhost:5173"),
        "Access-Control-Request-Method": "POST",
    }
    res = client.options("/health", headers=headers)
    # Starlette returns 200 by default for preflight. If you enabled the optional middleware, expect 204.
    assert res.status_code in (200, 204)
    # Must include CORS headers
    assert res.headers.get("access-control-allow-origin") == headers["Origin"]
    allow_methods = res.headers.get("access-control-allow-methods", "").upper()
    assert "GET" in allow_methods and "POST" in allow_methods and "OPTIONS" in allow_methods

def test_cors_preflight_disallowed_origin():
    headers = {
        "Origin": "https://evil.com",
        "Access-Control-Request-Method": "POST",
    }
    res = client.options("/health", headers=headers)
    # Disallowed origin preflight is rejected by Starlette with 400
    # or served without ACAO (browser would block actual request). Accept either outcome:
    assert res.status_code in (400, 200, 204)
    # If status is not 400, ensure header is NOT present (so browser blocks it).
    if res.status_code != 400:
        assert "access-control-allow-origin" not in {k.lower(): v for k, v in res.headers.items()}

def test_simple_get_allowed_origin_has_acao():
    headers = {
        "Origin": os.getenv("TEST_ALLOWED_ORIGIN", "http://localhost:5173")
    }
    res = client.get("/health", headers=headers)
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == headers["Origin"]

def test_simple_get_disallowed_origin_omits_acao():
    headers = {"Origin": "https://evil.com"}
    res = client.get("/health", headers=headers)
    assert res.status_code == 200
    # No ACAO header => browsers will block cross-origin access
    assert "access-control-allow-origin" not in {k.lower(): v for k, v in res.headers.items()}
