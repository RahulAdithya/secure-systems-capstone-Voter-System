from fastapi import APIRouter, Depends

from app.security_utils import User, require_role

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/ballots")
def list_admin_ballots(user: User = Depends(require_role("admin"))):
    return {"managed_by": user.email, "ballots": ["Q1-2025", "Q2-2025"]}
