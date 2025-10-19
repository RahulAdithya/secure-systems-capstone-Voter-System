from typing import Literal, Optional

from fastapi import Depends, HTTPException, Request, status

Role = Literal["admin", "voter"]


class User:
    def __init__(self, email: str, role: Role):
        self.email = email
        self.role = role


def _parse_token(token: str) -> tuple[Optional[str], Optional[Role]]:
    # Accept legacy fixed tokens and new role:email tokens
    if token == "admin-token":
        return ("admin@example.com", "admin")
    if token == "voter-token":
        return ("voter@example.com", "voter")
    if ":" in token:
        prefix, email = token.split(":", 1)
        if prefix in {"admin", "voter"} and email:
            return (email, "admin" if prefix == "admin" else "voter")
    return (None, None)


def get_current_user(request: Request) -> User:
    auth = request.headers.get("authorization", "")
    parts = auth.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        email, role = _parse_token(parts[1])
        if role and email:
            return User(email=email, role=role)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthenticated")


def require_role(need: Role):
    def _dep(user: User = Depends(get_current_user)) -> User:
        if user.role != need:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
        return user

    return _dep

