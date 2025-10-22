import pyotp
from fastapi.testclient import TestClient

from app.main import app


def _reset_limits():
    limiter = getattr(app.state, "limiter", None)
    if limiter is not None:
        limiter.reset()


def _login(
    client: TestClient,
    email: str,
    password: str,
    captcha_token: str | None = None,
    otp: str | None = None,
    backup_code: str | None = None,
):
    payload = {"email": email, "password": password}
    if captcha_token is not None:
        payload["captcha_token"] = captcha_token
    if otp is not None:
        payload["otp"] = otp
    if backup_code is not None:
        payload["backup_code"] = backup_code
    return client.post("/auth/login", json=payload)


def test_login_requires_captcha_after_failures(monkeypatch):
    monkeypatch.setenv("CAPTCHA_THRESHOLD", "3")
    monkeypatch.setenv("CAPTCHA_VALID_TOKEN", "1234")
    monkeypatch.setenv("FAILED_TTL_SECONDS", "900")

    client = TestClient(app)
    email = "admin@evp-demo.com"

    # Enroll MFA to obtain a TOTP secret for the admin account.
    enroll_response = client.post("/auth/mfa/enroll", json={"email": email, "password": "secret123"})
    assert enroll_response.status_code == 201
    otpauth_uri = enroll_response.json()["otpauth_uri"]
    totp = pyotp.parse_uri(otpauth_uri)

    # Three failed attempts -> still only credential error, but counter increases.
    for attempt in range(1, 4):
        response = _login(client, email, "wrong-password")
        assert response.status_code == 401
        body = response.json()
        assert body["detail"]["error"] == "invalid_credentials"
        assert body["detail"]["failed_attempts"] == attempt
        _reset_limits()

    # Correct password but missing captcha once failures >= threshold -> blocked.
    response = _login(client, email, "secret123")
    assert response.status_code == 401
    assert response.json() == {"detail": "captcha_required_or_invalid"}
    _reset_limits()

    # Wrong captcha token keeps blocking.
    response = _login(client, email, "secret123", captcha_token="9999")
    assert response.status_code == 401
    assert response.json() == {"detail": "captcha_required_or_invalid"}
    _reset_limits()

    # Providing the correct captcha allows authentication to succeed.
    valid_otp = totp.now()
    response = _login(
        client,
        email,
        "secret123",
        captcha_token="1234",
        otp=valid_otp,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body.get("access_token"), str) and body["access_token"]
    _reset_limits()

    # Counter resets after success: next failure is counted as 1 and does not
    # require a captcha on the subsequent legitimate attempt.
    response = _login(client, email, "wrong-password")
    assert response.status_code == 401
    body = response.json()
    assert body["detail"]["error"] == "invalid_credentials"
    assert body["detail"]["failed_attempts"] == 1
    _reset_limits()

    response = _login(client, email, "secret123", otp=totp.now())
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body.get("access_token"), str) and body["access_token"]
    _reset_limits()
