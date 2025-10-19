# backend/app/routers/auth.py
from typing import Optional
from datetime import datetime, timedelta
from jose import jwt, JWTError

from fastapi import APIRouter, HTTPException, Request, status, Depends, Header
from pydantic import BaseModel

SECRET_KEY = "your-secret-key"  # should be in .env
ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 10  # REQ-03: ≤10 minutes

ACCESS_TOKEN_EXPIRE_MINUTES = 1  # ~12 seconds for testing
IDLE_TIMEOUT_MINUTES = 0.5          # ~6 seconds idle timeout

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



def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



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
    # return LoginResponse(access_token=DEMO_TOKEN)
    # Initialize idle session
    update_activity(username)
    
    access_token = create_access_token({"sub": username})
    return LoginResponse(access_token=access_token)


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



idle_sessions = {}


def update_activity(username: str):
    idle_sessions[username] = datetime.utcnow()

def check_idle(username: str) -> bool:
    last = idle_sessions.get(username)
    if not last:
        return False
    # return (datetime.utcnow() - last) > timedelta(minutes=2)
    return (datetime.utcnow() - last) > timedelta(minutes=IDLE_TIMEOUT_MINUTES)

class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  # token valid
    except JWTError as e:
        raise HTTPException(status_code=401, detail="token_expired_or_invalid")

from fastapi import Header

@router.post("/refresh", response_model=RefreshResponse)
async def refresh(payload: LoginPayload, authorization: str = Header(...)):
    # Expecting header: Authorization: Bearer <token>
    token = authorization.split(" ")[1]  # extract token
    
    # --- JWT check ---
    try:
        verify_token(token)
        # jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="token_expired_or_invalid")
    
    username = payload.username
    
    # --- Idle timeout check ---
    if check_idle(username):
        raise HTTPException(status_code=401, detail="idle_timeout")
    
    # Reset activity and issue new token
    update_activity(username)
    access_token = create_access_token({"sub": username})
    return RefreshResponse(access_token=access_token)
