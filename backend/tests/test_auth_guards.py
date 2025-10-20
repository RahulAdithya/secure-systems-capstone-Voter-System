import os
import time

from fastapi.testclient import TestClient

from app.core.settings import get_settings
from app.main import app

client = TestClient(app)


def _reset_limits() -> None:
    limiter = getattr(app.state, "limiter", None)
    if limiter is not None:
        limiter.reset()


def setup_module(_):
    os.environ["ENABLE_LOGIN_GUARDS"] = "1"
    get_settings.cache_clear()


def teardown_module(_):
    os.environ["ENABLE_LOGIN_GUARDS"] = "0"
    get_settings.cache_clear()


def test_first_failure_sets_captcha_header():
    email = "guard-one@example.com"
    response = client.post("/auth/login?force_fail=1", json={"email": email, "password": "irrelevant"})
    assert response.status_code == 401
    assert response.headers.get("X-Captcha-Required") == "true"
    _reset_limits()

    status_resp = client.get(f"/auth/captcha/status?email={email}")
    assert status_resp.status_code == 200
    assert status_resp.json() == {"captcha_required": True}


def test_three_failures_lock_for_30s(monkeypatch):
    settings = get_settings()
    assert settings.login_fail_limit == 3
    assert settings.login_lockout_seconds == 30

    email = "admin@evp-demo.com"
    # Ensure MFA enrolled so a valid login is possible.
    enroll_response = client.post("/auth/mfa/enroll", json={"email": email, "password": "secret123"})
    assert enroll_response.status_code == 201
    backup_codes = enroll_response.json()["backup_codes"]
    assert backup_codes
    backup_code = backup_codes[0]

    # Failures using the dev helper flag.
    for _ in range(2):
        res = client.post("/auth/login?force_fail=1", json={"email": email, "password": "secret123"})
        assert res.status_code == 401
        assert res.headers.get("X-Captcha-Required") == "true"
        _reset_limits()

    locked = client.post("/auth/login?force_fail=1", json={"email": email, "password": "secret123"})
    assert locked.status_code == 429
    body = locked.json()
    assert body["error"] == "locked"
    assert body["retry_after"] <= 30
    assert locked.headers.get("X-Captcha-Required") == "true"
    _reset_limits()

    real_time = time.time
    monkeypatch.setattr("app.security.attempts.time.time", lambda: real_time() + 31)

    ok = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "secret123",
            "backup_code": backup_code,
        },
    )
    assert ok.status_code == 200
    _reset_limits()


def test_guards_off_by_default():
    os.environ["ENABLE_LOGIN_GUARDS"] = "0"
    get_settings.cache_clear()

    email = "admin@evp-demo.com"
    enroll_response = client.post("/auth/mfa/enroll", json={"email": email, "password": "secret123"})
    assert enroll_response.status_code == 201
    backup_codes = enroll_response.json()["backup_codes"]
    assert backup_codes
    backup_code = backup_codes[0]

    resp = client.post(
        "/auth/login?force_fail=1",
        json={
            "email": email,
            "password": "secret123",
            "backup_code": backup_code,
        },
    )
    assert resp.status_code == 200
    assert resp.headers.get("X-Captcha-Required") is None
    _reset_limits()

    os.environ["ENABLE_LOGIN_GUARDS"] = "1"
    get_settings.cache_clear()
