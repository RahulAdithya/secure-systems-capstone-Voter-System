from fastapi import APIRouter, Request

from app.main import limiter  # reuse the limiter instance
from app.models import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# Rate limit: 3 requests per 10s + 5 per minute, per client IP.
# For production, configure: Limiter(storage_uri="redis://localhost:6379")
@router.post("/login", response_model=LoginResponse)
@limiter.limit("3/10seconds;5/minute")
async def login(request: Request, payload: LoginRequest):
    # NOTE: No security yet. Always returns a static token.
    return LoginResponse(token="dummy-token")
