from fastapi import APIRouter, Request

from app.models import LoginRequest, LoginResponse

try:
    # Reuse rate limiter from main when available.
    from app.main import limiter  # type: ignore
except Exception:  # pragma: no cover - fallback for tests if limiter import fails
    limiter = None

router = APIRouter(prefix="/auth", tags=["auth"])

# Demo policy: emails with "+admin" become admins.
if limiter:
    # Rate limit: 3 requests per 10s + 5 per minute, per client IP.
    # For production, configure: Limiter(storage_uri="redis://localhost:6379")
    @router.post("/login", response_model=LoginResponse)
    @limiter.limit("3/10seconds;5/minute")
    async def login(request: Request, payload: LoginRequest):
        local, _, _ = payload.email.partition("@")
        role = "admin" if local.endswith("+admin") else "voter"
        token = "admin-token" if role == "admin" else "voter-token"
        return LoginResponse(token=token)
else:

    @router.post("/login", response_model=LoginResponse)
    async def login(payload: LoginRequest):
        local, _, _ = payload.email.partition("@")
        role = "admin" if local.endswith("+admin") else "voter"
        token = "admin-token" if role == "admin" else "voter-token"
        return LoginResponse(token=token)
