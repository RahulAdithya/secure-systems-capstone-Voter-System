from fastapi import APIRouter, Request
from app.models import LoginRequest, LoginResponse

# reuse limiter defined in app.main (import after it's created there)
from app.main import limiter

router = APIRouter(prefix="/auth", tags=["auth"])

# Rate limit: 3 requests per 10s + 5 per minute, per client IP.
# For production, consider: Limiter(storage_uri="redis://localhost:6379")
@router.post("/login", response_model=LoginResponse)
@limiter.limit("3/10seconds;5/minute")
async def login(request: Request, payload: LoginRequest):
    # NOTE: No real auth yet. Always returns a static token.
    return LoginResponse(token="dummy-token")
