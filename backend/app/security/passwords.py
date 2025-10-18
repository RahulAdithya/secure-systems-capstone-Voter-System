from __future__ import annotations

import os
import hmac
import hashlib
from passlib.hash import argon2


# Explicit Argon2id configuration
_argon = argon2.using(type="ID", time_cost=3, memory_cost=65536, parallelism=2)


def _pepper_bytes() -> bytes:
    """Return the application-wide secret pepper as bytes.

    Load from env var PASSWORD_PEPPER. Keep this secret outside the DB.
    """
    val = os.getenv("PASSWORD_PEPPER", "")
    try:
        return val.encode("utf-8") if val else b""
    except Exception:
        return b""


def _pepperize(password: str) -> str:
    key = _pepper_bytes()
    if not key:
        return password
    # Use HMAC-SHA256 to combine the password with the pepper
    return hmac.new(key, password.encode("utf-8"), hashlib.sha256).hexdigest()


def hash_password(password: str) -> str:
    return _argon.hash(_pepperize(password))


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _argon.verify(_pepperize(password), password_hash)
    except Exception:
        return False

