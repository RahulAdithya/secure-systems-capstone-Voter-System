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

# ---- Allowed origins ----
DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

def _load_allowed_origins() -> List[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "")
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    return origins or DEFAULT_ALLOWED_ORIGINS

ALLOWED_ORIGINS = _load_allowed_origins()

# ---- Security headers ----
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
STRICT_TRANSPORT_SECURITY = "max-age=31536000; includeSubDomains"  # meaningful over HTTPS

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

# ---- CORS (hardened) ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["authorization", "content-type", "x-requested-with"],
    max_age=3600,
)

# ---- Security headers middleware ----
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    for k, v in SECURITY_HEADERS.items():
        response.headers.setdefault(k, v)
    response.headers.setdefault("Strict-Transport-Security", STRICT_TRANSPORT_SECURITY)
    return response

# ---- Health ----
@app.get("/health")
def health():
    return {"ok": True, "service": "backend"}

# ---- Routers (import after limiter so auth can import limiter from app.main) ----
from app.routers import auth, users, ballots  # noqa: E402

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(ballots.router)
