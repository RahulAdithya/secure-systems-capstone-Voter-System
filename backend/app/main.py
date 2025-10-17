import os
from typing import List

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.responses import Response

DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def _load_allowed_origins() -> List[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "")
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return origins or DEFAULT_ALLOWED_ORIGINS


ALLOWED_ORIGINS = _load_allowed_origins()

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
STRICT_TRANSPORT_SECURITY = "max-age=31536000; includeSubDomains"

app = FastAPI(title="Electronic Voting Platform (Base)")

# If behind a proxy later, we can switch to X-Forwarded-For parsing.
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


# Hardened CORS configuration for the frontend UI.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["authorization", "content-type", "x-requested-with"],
    expose_headers=[],
    max_age=3600,
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    for header, value in SECURITY_HEADERS.items():
        response.headers.setdefault(header, value)
    response.headers.setdefault("Strict-Transport-Security", STRICT_TRANSPORT_SECURITY)
    return response


@app.get("/health")
def health():
    return {"ok": True}


from app.routers import auth, ballots, users  # noqa: E402

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(ballots.router)
