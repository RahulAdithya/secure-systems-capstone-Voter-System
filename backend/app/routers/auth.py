# backend/app/routers/auth.py
import io
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import qrcode
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, Header
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.db_models import User as DBUser
from app.core.settings import get_settings
from jose import JWTError, jwt

from app.security.captcha_guard import clear, needs_captcha, record_failed, verify_captcha_token
from app.security.attempts import store
from app.security.mfa import (
    enroll as mfa_enroll,
    is_enrolled as mfa_is_enrolled,
    latest_backup_codes,
    provisioning_uri as mfa_provisioning_uri,
    try_backup_code as mfa_try_backup_code,
    verify_totp as mfa_verify_totp,
)
from app.security.passwords import hash_password, verify_password
from app.security.logger import auth_logger as logger

try:
    from app.main import limiter  # type: ignore
except Exception:  # fallback if limiter import fails
    limiter = None

# ---- Demo credentials ----
DEMO_ADMIN_EMAIL = "admin@evp-demo.com"
DEMO_USERNAME = "admin"
DEMO_PASSWORD = "secret123"

ACCESS_TOKEN_EXPIRE_MINUTES = 1   # ~1 minute for testing
IDLE_TIMEOUT_MINUTES = 0.5        # ~30 seconds idle timeout

router = APIRouter(prefix="/auth", tags=["auth"])

# ---------------- Payloads ----------------
class LoginPayload(BaseModel):
    email: EmailStr
    password: str = Field(min_length=3, max_length=128)
    otp: Optional[str] = Field(default=None, min_length=3, max_length=12)
    backup_code: Optional[str] = Field(default=None, min_length=3, max_length=16)
    captcha_token: Optional[str] = None

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class SignupPayload(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def _username_rules(cls, v: str) -> str:
        import re
        v2 = v.strip()
        if v2 != v:
            raise ValueError("username must not have surrounding spaces")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_]*", v):
            raise ValueError("username must be alphanumeric with underscores")
        return v

    @field_validator("password")
    @classmethod
    def _password_rules(cls, v: str) -> str:
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

class MfaEnrollPayload(BaseModel):
    email: EmailStr
    password: str = Field(min_length=3, max_length=128)

class MfaEnrollResponse(BaseModel):
    otpauth_uri: str
    backup_codes: List[str]

class MfaVerifyPayload(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=3, max_length=12)

class MfaQrPayload(BaseModel):
    email: EmailStr
    password: str = Field(min_length=3, max_length=128)

class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ---------------- UX Event payload ----------------
class UxEventPayload(BaseModel):
    name: str
    sid: str
    ts: Optional[str] = None
    details: Optional[Dict[str, str]] = None

# ---------------- Idle session tracking ----------------
idle_sessions = {}

def update_activity(username: str):
    idle_sessions[username] = datetime.utcnow()

def check_idle(username: str) -> bool:
    last = idle_sessions.get(username)
    if not last:
        return False
    return (datetime.utcnow() - last) > timedelta(minutes=IDLE_TIMEOUT_MINUTES)

# ---------------- JWT helpers ----------------
def _jwt_config() -> tuple[str, str]:
    settings = get_settings()
    secret = settings.jwt_secret or "your-secret-key"
    algorithm = settings.jwt_algorithm or "HS256"
    return secret, algorithm


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    secret, algorithm = _jwt_config()
    encoded_jwt = jwt.encode(to_encode, secret, algorithm=algorithm)
    return encoded_jwt

def verify_token(token: str):
    try:
        secret, algorithm = _jwt_config()
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="token_expired_or_invalid")

# ---------------- Utilities ----------------
def _client_ip(request: Request) -> str:
    client = request.client
    return client.host if client and client.host else "0.0.0.0"

def _guard_key(email: str, ip: str) -> str:
    return store.key(email, ip)


@router.get("/captcha/status")
def captcha_status(request: Request, email: EmailStr = Query(...)):
    """
    Report whether the caller must complete a captcha challenge before logging in.
    Works for both the new login guards (default) and the legacy in-memory guard.
    """
    settings = get_settings()
    ip = _client_ip(request)
    if settings.enable_login_guards:
        key = _guard_key(str(email), ip)
        state = store.get(key, window_seconds=settings.login_lockout_seconds)
        required = state.fails >= settings.login_captcha_fail_threshold
        return {"captcha_required": required}
    return {"captcha_required": needs_captcha(str(email), ip)}


def _authenticate_user(db: Session, identifier: str, password: str) -> Optional[Tuple[str, bool]]:
    try:
        stmt = select(DBUser).where(or_(DBUser.email == identifier, DBUser.username == identifier))
        user = db.execute(stmt).scalars().first()
        if user and verify_password(password, user.password_hash):
            is_admin = user.email.lower() == DEMO_ADMIN_EMAIL.lower() or user.username == DEMO_USERNAME
            return user.email, is_admin
    except Exception:
        pass

    ident_lower = identifier.lower()
    if ident_lower in {DEMO_ADMIN_EMAIL.lower(), DEMO_USERNAME.lower()} and password == DEMO_PASSWORD:
        return DEMO_ADMIN_EMAIL, True
    return None

# ---------------- Login handler ----------------
def _handle_login(request: Request, payload: LoginPayload, db: Session, *, force_fail: bool = False) -> LoginResponse:
    settings = get_settings()
    guards_enabled = settings.enable_login_guards
    ip = _client_ip(request)
    identifier = payload.email
    logger.info(f"Login attempt for {identifier} from IP {ip} Email:{payload.email} Password:[REDACTED]")

    guard_key = _guard_key(str(identifier), ip) if guards_enabled else None
    state = store.get(guard_key, window_seconds=settings.login_lockout_seconds) if guards_enabled and guard_key else None

    # Handle locked account
    if guards_enabled and guard_key:
        locked, retry_after = store.is_locked(guard_key)
        if locked:
            headers: Dict[str, str] = {}
            if state and state.fails >= settings.login_captcha_fail_threshold:
                headers["X-Captcha-Required"] = "true"
            if retry_after:
                headers["Retry-After"] = str(retry_after)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"error": "locked", "retry_after": retry_after},
                headers=headers or None,
            )

    # Legacy captcha guard if login guards disabled
    if not guards_enabled and needs_captcha(identifier, ip) and not verify_captcha_token(payload.captcha_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="captcha_required_or_invalid",
        )

    simulate_fail = bool(force_fail) if guards_enabled else False

    # Simulate fail if requested
    subject = None if simulate_fail else _authenticate_user(db, identifier, payload.password)
    if not subject:
        headers: Dict[str, str] = {}
        retry_after = 0
        captcha_required = False
        if guards_enabled and guard_key:
            fails, locked_now, retry_after = store.register_fail(
                guard_key,
                settings.login_fail_limit,
                settings.login_lockout_seconds,
            )
            if fails >= settings.login_captcha_fail_threshold:
                headers["X-Captcha-Required"] = "true"
                captcha_required = True
            if locked_now:
                if retry_after:
                    headers["Retry-After"] = str(retry_after)
                logger.warning(f"Failed login for {identifier} from IP {ip}  Email:{payload.email} Password:[REDACTED]")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"error": "locked", "retry_after": retry_after},
                    headers=headers or None,
                )

        failed = record_failed(identifier, ip)
        logger.warning(f"Failed login for {identifier} from IP {ip}  Email:{payload.email} Password:[REDACTED]")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_credentials", "failed_attempts": failed},
            headers=headers or None,
        )

    if guards_enabled and guard_key:
        current_state = state or store.get(guard_key, window_seconds=settings.login_lockout_seconds)
        captcha_required = current_state.fails >= settings.login_captcha_fail_threshold
        if captcha_required and not verify_captcha_token(payload.captcha_token):
            headers = {"X-Captcha-Required": "true"}
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="captcha_required_or_invalid",
                headers=headers,
            )

    canonical_email, is_admin = subject

    # MFA checks for admin
    if is_admin:
        if not mfa_is_enrolled(canonical_email):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="mfa_required")
        if payload.otp:
            if not mfa_verify_totp(canonical_email, payload.otp):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_otp")
        elif payload.backup_code:
            if not mfa_try_backup_code(canonical_email, payload.backup_code):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_backup_code")
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="mfa_required")

    logger.info(f"Successful login for {identifier} from IP {ip}  Email:{payload.email} Password:[REDACTED]")

    # Success → clear counters, register success, update idle
    clear(identifier, ip)
    if guards_enabled and guard_key:
        store.register_success(guard_key)
    update_activity(identifier)

    role = "admin" if is_admin else "voter"
    token = create_access_token({"sub": canonical_email, "role": role})
    return LoginResponse(access_token=token)

# ---------------- Login route ----------------
if limiter:
    @router.post("/login", response_model=LoginResponse)
    @limiter.limit("3/10seconds;5/minute")
    async def login(request: Request, payload: LoginPayload, force_fail: int = Query(0, include_in_schema=False), db: Session = Depends(get_db)) -> LoginResponse:
        return _handle_login(request, payload, db, force_fail=bool(force_fail))
else:
    @router.post("/login", response_model=LoginResponse)
    async def login(request: Request, payload: LoginPayload, force_fail: int = Query(0, include_in_schema=False), db: Session = Depends(get_db)) -> LoginResponse:
        return _handle_login(request, payload, db, force_fail=bool(force_fail))

# ---------------- Signup ----------------
@router.post("/signup", response_model=SignupResponse, status_code=201)
def signup(payload: SignupPayload, db: Session = Depends(get_db)) -> SignupResponse:
    username = payload.username
    email = payload.email

    if username.lower() == DEMO_USERNAME.lower() or str(email).lower() == DEMO_ADMIN_EMAIL.lower():
        raise HTTPException(status_code=403, detail="reserved_identity")

    stmt = select(DBUser).where(or_(DBUser.username == username, DBUser.email == email))
    existing = db.execute(stmt).scalars().first()
    if existing:
        raise HTTPException(status_code=409, detail="username_or_email_already_exists")

    user = DBUser(username=username, email=str(email), password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    return SignupResponse(id=user.id, username=user.username, email=user.email)

# ---------------- MFA routes ----------------
@router.post("/mfa/enroll", response_model=MfaEnrollResponse, status_code=status.HTTP_201_CREATED)
def enroll_mfa(payload: MfaEnrollPayload, db: Session = Depends(get_db)) -> MfaEnrollResponse:
    subject = _authenticate_user(db, payload.email, payload.password)
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

    canonical_email, is_admin = subject
    if not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="only_admin_can_enroll_mfa")

    record = mfa_enroll(canonical_email)
    otpauth_uri = mfa_provisioning_uri(canonical_email)
    backup_codes = latest_backup_codes(canonical_email)
    return MfaEnrollResponse(otpauth_uri=otpauth_uri, backup_codes=backup_codes)

@router.post("/mfa/verify-setup", status_code=status.HTTP_204_NO_CONTENT)
def verify_mfa_setup(payload: MfaVerifyPayload) -> Response:
    if not mfa_is_enrolled(payload.email):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="mfa_not_enrolled")
    if not mfa_verify_totp(payload.email, payload.otp):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_otp")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/mfa/qrcode")
def get_mfa_qrcode(payload: MfaQrPayload, db: Session = Depends(get_db)) -> Response:
    subject = _authenticate_user(db, payload.email, payload.password)
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

    canonical_email, is_admin = subject
    if not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="only_admin_can_view_qr")

    if not mfa_is_enrolled(canonical_email):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="mfa_not_enrolled")

    otpauth_uri = mfa_provisioning_uri(canonical_email)
    img = qrcode.make(otpauth_uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")

# ---------------- Refresh JWT / Idle ----------------
@router.post("/refresh", response_model=RefreshResponse)
async def refresh(payload: LoginPayload, authorization: str = Header(...)):
    token = authorization.split(" ")[1]  # extract token
    verify_token(token)

    username = payload.email
    if check_idle(username):
        logger.info(f"Auto-logout triggered for user: {username} due to inactivity.")
        raise HTTPException(status_code=401, detail="idle_timeout")

    update_activity(username)
    access_token = create_access_token({"sub": username})
    logger.info(f"Session refreshed for {username}")
    return RefreshResponse(access_token=access_token)

# ---------------- UX events (REQ-16 simple) ----------------
@router.post("/ux", status_code=status.HTTP_204_NO_CONTENT)
def ux_event(event: UxEventPayload, authorization: str = Header(...)) -> Response:
    token = authorization.split(" ")[1]
    claims = verify_token(token)
    subject = claims.get("sub", "unknown")
    # Append to same auth logger for easy correlation
    logger.info(
        f"UX_EVENT name={event.name} sid={event.sid} ts={event.ts} user={subject}"
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

    
