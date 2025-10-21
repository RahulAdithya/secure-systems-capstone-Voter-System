from typing import Literal, Optional

from fastapi import Depends, HTTPException, Request, status

Role = Literal["admin", "voter"]


class User:
    def __init__(self, email: str, role: Role):
        self.email = email
        self.role = role


def _role_from_token(token: str) -> Optional[Role]:
    # Demo mapping for assignment evidence. Replace with JWT later.
    if token == "admin-token":
        return "admin"
    if token == "voter-token":
        return "voter"
    return None


def get_current_user(request: Request) -> User:
    auth = request.headers.get("authorization", "")
    parts = auth.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        role = _role_from_token(parts[1])
        if role:
            email = "admin@example.com" if role == "admin" else "voter@example.com"
            return User(email=email, role=role)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthenticated")


def require_role(need: Role):
    def _dep(user: User = Depends(get_current_user)) -> User:
        if user.role != need:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
        return user

    return _dep
