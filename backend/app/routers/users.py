from fastapi import APIRouter
from app.models import User

router = APIRouter(prefix="/users", tags=["users"])

# simple in-memory current user
DEMO_USER = User(id=1, username="demo", full_name="Demo Voter")

@router.get("/me", response_model=User)
def me():
    return DEMO_USER
