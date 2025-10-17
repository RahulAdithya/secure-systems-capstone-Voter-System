# backend/app/main.py
import os
from typing import List

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response

from app.routers import auth, ballots, users

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

# ---- CORS (REQ-18: hardened to specific origin + methods) ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],   # strictly limited
    allow_headers=["authorization", "content-type", "x-requested-with"],
    max_age=3600,
)

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

# ---- Include routers (uncomment/change prefixes as per your actual routers) ----
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(ballots.router, prefix="/ballots", tags=["ballots"])
