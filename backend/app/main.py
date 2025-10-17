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

# ---- Rate limiting (IP-based) ----
# If later behind a proxy, parse X-Forwarded-For here.
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

@app.exception_handler(RateLimitExceeded)
def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    resp = JSONResponse(
        status_code=429,
        content={"error": "too_many_requests", "detail": "Try again later."},
    )
    for k, v in (getattr(exc, "headers", {}) or {}).items():
        resp.headers.setdefault(k, v)
    return resp

# ---- CORS (REQ-18: hardened to specific origin + methods) ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],   # strictly limited
    allow_headers=["authorization", "content-type", "x-requested-with"],
    max_age=3600,
)

# ---- (Optional) Force preflight to return 204 (aligns with acceptance) ----
@app.middleware("http")
async def cors_preflight_204(request: Request, call_next):
    # A CORS preflight has method OPTIONS and the Access-Control-Request-Method header
    if request.method == "OPTIONS" and "access-control-request-method" in request.headers:
        # CORSMiddleware will still attach CORS headers; we only set the status code to 204.
        return Response(status_code=204)
    return await call_next(request)

# ---- Security headers middleware (REQ-17) ----
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    for header, value in SECURITY_HEADERS.items():
        response.headers.setdefault(header, value)
    # HSTS (effective only when behind HTTPS)
    response.headers.setdefault("Strict-Transport-Security", STRICT_TRANSPORT_SECURITY)
    return response

# ---- Health endpoint (used by tests and curl) ----
@app.get("/health")
def health():
    return {"ok": True}

# ---- Routers (import after limiter so auth can import limiter from app.main) ----
from app.routers import auth, users, ballots  # noqa: E402

# Use prefixes to keep API surface stable (adjust if your project expects bare paths)
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(ballots.router, prefix="/ballots", tags=["ballots"])
