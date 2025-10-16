# backend/app/main.py
import os
from typing import List

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response

from app.routers import auth, ballots, users

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
STRICT_TRANSPORT_SECURITY = "max-age=31536000; includeSubDomains"  # enable behind HTTPS

app = FastAPI(title="Electronic Voting Platform (Base)")

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
    # Add HSTS (only meaningful over HTTPS; fine in dev too)
    response.headers.setdefault("Strict-Transport-Security", STRICT_TRANSPORT_SECURITY)
    return response

# ---- Health ----
@app.get("/health")
def health():
    return {"ok": True, "service": "backend"}

# ---- Routers ----
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(ballots.router)
