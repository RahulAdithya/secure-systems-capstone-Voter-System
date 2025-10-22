from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from pydantic import BaseModel, Field


class Settings(BaseModel):
    enable_login_guards: bool = Field(default=True)
    login_fail_limit: int = Field(default=3)
    login_lockout_seconds: int = Field(default=30)
    login_captcha_fail_threshold: int = Field(default=1)
    redis_url: Optional[str] = Field(default=None)


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name, default)
    if value is None:
        return None
    return value


def _load_settings() -> Settings:
    env = os.getenv
    enable_login_guards = env("ENABLE_LOGIN_GUARDS", "1") == "1"
    login_fail_limit = int(env("LOGIN_FAIL_LIMIT", "3"))
    login_lockout_seconds = int(env("LOGIN_LOCKOUT_SECONDS", "30"))
    login_captcha_fail_threshold = int(env("LOGIN_CAPTCHA_FAIL_THRESHOLD", "1"))
    redis = env("REDIS_URL")
    if redis == "":
        redis = None
    return Settings(
        enable_login_guards=enable_login_guards,
        login_fail_limit=login_fail_limit,
        login_lockout_seconds=login_lockout_seconds,
        login_captcha_fail_threshold=login_captcha_fail_threshold,
        redis_url=redis,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return _load_settings()


def reload_settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()


__all__ = ["Settings", "get_settings", "reload_settings"]
