from fastapi.testclient import TestClient

from app.main import app


def _reset_limits():
    limiter = getattr(app.state, "limiter", None)
    if limiter is not None:
        limiter.reset()


def _login(client: TestClient, username: str, password: str, captcha_token: str | None = None):
    payload = {"username": username, "password": password}
    if captcha_token is not None:
        payload["captcha_token"] = captcha_token
    return client.post("/auth/login", json=payload)


def test_login_requires_captcha_after_failures(monkeypatch):
    monkeypatch.setenv("CAPTCHA_THRESHOLD", "3")
    monkeypatch.setenv("CAPTCHA_VALID_TOKEN", "1234")
    monkeypatch.setenv("FAILED_TTL_SECONDS", "900")

    client = TestClient(app)
    username = "admin"

    # Three failed attempts -> still only credential error, but counter increases.
    for attempt in range(1, 4):
        response = _login(client, username, "wrong-password")
        assert response.status_code == 401
        body = response.json()
        assert body["detail"]["error"] == "invalid_credentials"
        assert body["detail"]["failed_attempts"] == attempt
        _reset_limits()

    # Correct password but missing captcha once failures >= threshold -> blocked.
    response = _login(client, username, "secret123")
    assert response.status_code == 401
    assert response.json() == {"detail": "captcha_required_or_invalid"}
    _reset_limits()

    # Wrong captcha token keeps blocking.
    response = _login(client, username, "secret123", captcha_token="9999")
    assert response.status_code == 401
    assert response.json() == {"detail": "captcha_required_or_invalid"}
    _reset_limits()

    # Providing the correct captcha allows authentication to succeed.
    response = _login(client, username, "secret123", captcha_token="1234")
    assert response.status_code == 200
    assert response.json() == {"access_token": "demo.jwt.token", "token_type": "bearer"}
    _reset_limits()

    # Counter resets after success: next failure is counted as 1 and does not
    # require a captcha on the subsequent legitimate attempt.
    response = _login(client, username, "wrong-password")
    assert response.status_code == 401
    body = response.json()
    assert body["detail"]["error"] == "invalid_credentials"
    assert body["detail"]["failed_attempts"] == 1
    _reset_limits()

    response = _login(client, username, "secret123")
    assert response.status_code == 200
    assert response.json() == {"access_token": "demo.jwt.token", "token_type": "bearer"}
    _reset_limits()
