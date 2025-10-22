import pyotp
from fastapi.testclient import TestClient

from app.main import app


def _reset_limits():
    limiter = getattr(app.state, "limiter", None)
    if limiter is not None:
        limiter.reset()


def test_admin_mfa_flow(monkeypatch):
    # Ensure CAPTCHA threshold is high enough that MFA tests are not blocked.
    monkeypatch.setenv("CAPTCHA_THRESHOLD", "10")
    monkeypatch.setenv("CAPTCHA_VALID_TOKEN", "1234")
    monkeypatch.setenv("FAILED_TTL_SECONDS", "900")

    client = TestClient(app)
    email = "admin@evp-demo.com"

    enroll_response = client.post("/auth/mfa/enroll", json={"email": email, "password": "secret123"})
    assert enroll_response.status_code == 201
    data = enroll_response.json()
    assert "otpauth_uri" in data
    assert "backup_codes" in data
    backup_codes = data["backup_codes"]
    assert len(backup_codes) == 10
    _reset_limits()

    # QR endpoint now requires admin password, returns PNG bytes.
    qr_response = client.post(
        "/auth/mfa/qrcode",
        json={"email": email, "password": "secret123"},
    )
    assert qr_response.status_code == 200
    assert qr_response.headers["content-type"] == "image/png"
    _reset_limits()

    totp = pyotp.parse_uri(data["otpauth_uri"])

    # Optional verification endpoint
    verify_response = client.post("/auth/mfa/verify-setup", json={"email": email, "otp": totp.now()})
    assert verify_response.status_code == 204

    # Login without OTP should fail with mfa_required.
    response = client.post("/auth/login", json={"email": email, "password": "secret123"})
    assert response.status_code == 401
    assert response.json() == {"detail": "mfa_required"}
    _reset_limits()

    # Login with an invalid OTP should be rejected.
    response = client.post(
        "/auth/login",
        json={"email": email, "password": "secret123", "otp": "123000"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "invalid_otp"}
    _reset_limits()

    # Correct OTP yields access token.
    valid_otp = totp.now()
    response = client.post(
        "/auth/login",
        json={"email": email, "password": "secret123", "otp": valid_otp},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body.get("access_token"), str) and body["access_token"]
    _reset_limits()

    # Backup codes work exactly once.
    backup_code = backup_codes[0]
    response = client.post(
        "/auth/login",
        json={"email": email, "password": "secret123", "backup_code": backup_code},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body.get("access_token"), str) and body["access_token"]
    _reset_limits()

    response = client.post(
        "/auth/login",
        json={"email": email, "password": "secret123", "backup_code": backup_code},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "invalid_backup_code"}
    _reset_limits()

    # Wrong password for QR retrieval is rejected.
    bad_qr = client.post(
        "/auth/mfa/qrcode",
        json={"email": email, "password": "bad"},
    )
    assert bad_qr.status_code == 401
