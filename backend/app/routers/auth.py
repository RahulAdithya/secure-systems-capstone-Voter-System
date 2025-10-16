from fastapi import APIRouter
from app.models import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    # NOTE: No security yet. Always returns a static token.
    return LoginResponse(token="dummy-token")
