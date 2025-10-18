# backend/app/routers/auth.py
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from app.security.captcha_guard import (
    clear,
    needs_captcha,
    record_failed,
    verify_captcha_token,
)

try:
    # Reuse rate limiter from main when available.
    from app.main import limiter  # type: ignore
except Exception:  # pragma: no cover - fallback for tests if limiter import fails
    limiter = None


# ---- Demo credentials for assignment/testing ----
DEMO_USERNAME = "admin"
DEMO_PASSWORD = "secret123"
DEMO_TOKEN = "demo.jwt.token"


class LoginPayload(BaseModel):
    """REQ-15 payload: username/password with optional captcha_token."""
    username: str
    password: str
    captcha_token: Optional[str] = None


class LoginResponse(BaseModel):
    """Standard bearer token response."""
    access_token: str
    token_type: str = "bearer"


router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str:
    client = request.client
    return client.host if client and client.host else "0.0.0.0"


def _credentials_valid(username: str, password: str) -> bool:
    # TODO: integrate with real user store (REQ-04 Argon2id) later
    return username == DEMO_USERNAME and password == DEMO_PASSWORD


def _handle_login(request: Request, payload: LoginPayload) -> LoginResponse:
    ip = _client_ip(request)
    username = payload.username

    # If threshold reached, enforce CAPTCHA
    if needs_captcha(username, ip) and not verify_captcha_token(payload.captcha_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="captcha_required_or_invalid",
        )

    # Validate credentials
    if not _credentials_valid(payload.username, payload.password):
        failed = record_failed(username, ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_credentials", "failed_attempts": failed},
        )

    # Success → clear counters and issue token
    clear(username, ip)
    return LoginResponse(access_token=DEMO_TOKEN)


# Route with optional limiter
if limiter:
    # Rate limit: 3 requests per 10s + 5 per minute, per client IP
    @router.post("/login", response_model=LoginResponse)
    @limiter.limit("3/10seconds;5/minute")
    async def login(request: Request, payload: LoginPayload) -> LoginResponse:
        return _handle_login(request, payload)
else:
    @router.post("/login", response_model=LoginResponse)
    async def login(request: Request, payload: LoginPayload) -> LoginResponse:
        return _handle_login(request, payload)
