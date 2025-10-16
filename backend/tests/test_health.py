from fastapi.testclient import TestClient

from app.main import (
    ALLOWED_ORIGINS,
    SECURITY_HEADERS,
    STRICT_TRANSPORT_SECURITY,
    app,
)

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_security_headers_present():
    response = client.get("/health")
    for header, value in SECURITY_HEADERS.items():
        assert response.headers.get(header) == value
    assert response.headers.get("Strict-Transport-Security") == STRICT_TRANSPORT_SECURITY


def test_cors_preflight_allows_known_origin():
    origin = ALLOWED_ORIGINS[0]
    response = client.options(
        "/health",
        headers={
            "origin": origin,
            "access-control-request-method": "GET",
            "access-control-request-headers": "authorization",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    assert response.headers.get("access-control-allow-credentials") == "true"
