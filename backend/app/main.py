# backend/app/main.py
import os
from typing import List

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import Response

# rate limiting
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

# ---- Allowed origins (env-overridable) ----
DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
]

def _load_allowed_origins() -> List[str]:
    """
    Optionally override via:
      ALLOWED_ORIGINS="https://localhost:5173"
      (comma-separated list if multiple)
    """
    raw = os.getenv("ALLOWED_ORIGINS", "")
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    return origins or DEFAULT_ALLOWED_ORIGINS

ALLOWED_ORIGINS = _load_allowed_origins()

# ---- Default security headers (REQ-17) ----
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "frame-ancestors 'none'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    ),
}
# NOTE: HSTS only takes effect when served over HTTPS (enable at your reverse proxy in prod)
STRICT_TRANSPORT_SECURITY = "max-age=31536000; includeSubDomains"

app = FastAPI(title="Electronic Voting Platform (Base)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["authorization", "content-type", "x-requested-with"],
    max_age=3600,
)

# If later behind a proxy, parse X-Forwarded-For here.
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    response = JSONResponse(
        status_code=429,
        content={"error": "too_many_requests", "detail": "Try again later."},
    )
    for header, value in (getattr(exc, "headers", {}) or {}).items():
        response.headers.setdefault(header, value)
    return response

# ---- Security headers middleware (REQ-17) ----
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    for header, value in SECURITY_HEADERS.items():
        response.headers.setdefault(header, value)
    # HSTS (effective only when behind HTTPS)
    response.headers.setdefault("Strict-Transport-Security", STRICT_TRANSPORT_SECURITY)
    return response

# ---- HTTP Hardening Middleware (REQ-06) ----
@app.middleware("http")
async def check_http_hardening(request: Request, call_next):
    # Criteria 1: Block PUT/DELETE on public endpoints (405 Method Not Allowed)
    # This prevents using methods like PUT/DELETE on endpoints that should only be GET/POST.
    if request.method in ["PUT", "DELETE"]:
        return JSONResponse(
            status_code=405,
            content={"detail": "Method Not Allowed"},
            headers={"Allow": "GET, POST, OPTIONS"},
        )
    
    # Criteria 2: Block POST without application/json (415 Unsupported Media Type)
    # This enforces strict content-type for incoming data.
    if request.method == "POST":
        content_type = request.headers.get("content-type", "")
        # Check if Content-Type is missing or doesn't start with application/json
        if not content_type.lower().startswith("application/json"):
            return JSONResponse(
                status_code=415,
                content={"detail": "Unsupported Media Type. Must be application/json"},
            )

    response: Response = await call_next(request)
    return response

# ---- Health endpoint (used by tests and curl) ----
@app.get("/health")
def health():
    return {"ok": True}

# ---- Routers (import after limiter so auth can import limiter from app.main) ----
from app.routers import admin, auth, ballots, users  # noqa: E402
from app.models import User
from app.security_utils import require_role

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(ballots.router)
app.include_router(admin.router)
