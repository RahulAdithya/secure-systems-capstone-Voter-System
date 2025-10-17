# backend/app/routers/auth.py
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status, Depends
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.security.captcha_guard import (
    clear,
    needs_captcha,
    record_failed,
    verify_captcha_token,
)
from app.db import get_db
from app.db_models import User as DBUser
from app.security.passwords import hash_password

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


# --------- Signup with input validation and SQL injection‑safe persistence ---------

class SignupPayload(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def _username_rules(cls, v: str) -> str:
        # allow letters, digits, underscore; no spaces; must start with letter or digit
        import re

        v2 = v.strip()
        if v2 != v:
            # Disallow leading/trailing spaces
            raise ValueError("username must not have surrounding spaces")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_]*", v):
            raise ValueError("username must be alphanumeric with underscores")
        return v

    @field_validator("password")
    @classmethod
    def _password_rules(cls, v: str) -> str:
        # Basic strong password policy
        import re

        if any(ord(ch) < 32 for ch in v):
            raise ValueError("password contains control characters")
        if v.strip() != v:
            raise ValueError("password must not have surrounding spaces")
        if not re.search(r"[a-z]", v):
            raise ValueError("password must include a lowercase letter")
        if not re.search(r"[A-Z]", v):
            raise ValueError("password must include an uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("password must include a digit")
        if not re.search(r"[^A-Za-z0-9]", v):
            raise ValueError("password must include a special character")
        return v


class SignupResponse(BaseModel):
    id: int
    username: str
    email: EmailStr


@router.post("/signup", response_model=SignupResponse, status_code=201)
def signup(payload: SignupPayload, db: Session = Depends(get_db)) -> SignupResponse:
    # Normalize
    username = payload.username
    email = payload.email

    # Check uniqueness using SQLAlchemy parameter binding (prevents SQL injection)
    stmt = select(DBUser).where(or_(DBUser.username == username, DBUser.email == email))
    existing = db.execute(stmt).scalars().first()
    if existing:
        # Choose specific message without leaking which field exists
        raise HTTPException(status_code=409, detail="username_or_email_already_exists")

    user = DBUser(
        username=username,
        email=str(email),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return SignupResponse(id=user.id, username=user.username, email=user.email)
