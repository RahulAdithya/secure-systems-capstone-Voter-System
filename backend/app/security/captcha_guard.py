"""
Simple in-memory CAPTCHA guard used for rate limiting login attempts.

The implementation is intentionally lightweight: it keeps counters keyed by
``(username, ip)`` pairs in process memory, expiring entries after a configurable
TTL.  It is sufficient for unit/integration tests and local development.
"""

from __future__ import annotations

import os
import time
from typing import Dict, Optional, Tuple

FailureKey = Tuple[str, str]
FailureRecord = Dict[str, float]

_failures: Dict[FailureKey, FailureRecord] = {}


def _normalize(username: str, ip: str) -> FailureKey:
    return (username.lower(), ip or "0.0.0.0")


def _config() -> Tuple[int, int, str]:
    threshold = int(os.getenv("CAPTCHA_THRESHOLD", "3"))
    ttl = int(os.getenv("FAILED_TTL_SECONDS", "900"))
    token = os.getenv("CAPTCHA_VALID_TOKEN", "1234")
    return threshold, ttl, token


def _expired(record: FailureRecord, ttl: int, now: float) -> bool:
    return now - record["last"] > ttl


def record_failed(username: str, ip: str) -> int:
    """Increment failure count for ``(username, ip)`` and return the new total."""
    _, ttl, _ = _config()
    key = _normalize(username, ip)
    now = time.monotonic()
    record = _failures.get(key)
    if record and _expired(record, ttl, now):
        record = None
    if not record:
        record = {"count": 0, "last": now}
    record["count"] += 1
    record["last"] = now
    _failures[key] = record
    return int(record["count"])


def clear(username: str, ip: str) -> None:
    """Clear failure tracking for ``(username, ip)``."""
    key = _normalize(username, ip)
    _failures.pop(key, None)


def needs_captcha(username: str, ip: str) -> bool:
    """Return ``True`` if the caller must supply a valid CAPTCHA token."""
    threshold, ttl, _ = _config()
    key = _normalize(username, ip)
    record = _failures.get(key)
    if not record:
        return False
    now = time.monotonic()
    if _expired(record, ttl, now):
        _failures.pop(key, None)
        return False
    return record["count"] >= threshold


def verify_captcha_token(token: Optional[str]) -> bool:
    """Check the supplied token against the configured CAPTCHA value."""
    _, _, expected = _config()
    return token is not None and token == expected


__all__ = [
    "record_failed",
    "clear",
    "needs_captcha",
    "verify_captcha_token",
]
