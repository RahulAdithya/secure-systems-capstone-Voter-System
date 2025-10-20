from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass
class AttemptState:
    fails: int
    lock_until: float
    first_failed_at: Optional[float]
    window_seconds: int


class AttemptsStore:
    """In-memory default store for login guard attempts."""

    def __init__(self) -> None:
        self._store: Dict[str, AttemptState] = {}

    def _now(self) -> float:
        return time.time()

    def key(self, email: str, ip: str) -> str:
        e = (email or "").strip().lower()
        return f"login:{e}:{ip}"

    def _fresh_state(self) -> AttemptState:
        return AttemptState(fails=0, lock_until=0.0, first_failed_at=None, window_seconds=0)

    def get(self, key: str, window_seconds: Optional[int] = None) -> AttemptState:
        state = self._store.get(key)
        if state is None:
            st = self._fresh_state()
            if window_seconds:
                st.window_seconds = window_seconds
            return st

        now = self._now()
        if state.lock_until and state.lock_until <= now:
            # Lock expired; clear stored state.
            self.clear(key)
            return self._fresh_state()

        window = window_seconds or state.window_seconds
        if window and state.first_failed_at is not None and now - state.first_failed_at > window:
            # Rolling window expired; clear and return fresh.
            self.clear(key)
            fresh = self._fresh_state()
            fresh.window_seconds = window
            return fresh

        if window_seconds:
            state.window_seconds = window_seconds
        return state

    def set(self, key: str, state: AttemptState) -> None:
        self._store[key] = state

    def clear(self, key: str) -> None:
        if key in self._store:
            del self._store[key]

    def is_locked(self, key: str) -> Tuple[bool, int]:
        state = self._store.get(key)
        if state is None:
            return False, 0
        now = self._now()
        if state.lock_until > now:
            retry_after = int(max(0.0, state.lock_until - now))
            return True, retry_after

        expired_lock = state.lock_until and state.lock_until <= now
        window = state.window_seconds
        expired_window = (
            window
            and state.first_failed_at is not None
            and now - state.first_failed_at > window
        )
        if expired_lock or expired_window:
            self.clear(key)
        return False, 0

    def register_fail(self, key: str, fail_limit: int, lockout_seconds: int) -> Tuple[int, bool, int]:
        """
        Register a failed attempt.

        Returns (fails, locked_now, retry_after).
        """
        now = self._now()
        state = self.get(key, window_seconds=lockout_seconds)
        state.fails += 1
        if state.first_failed_at is None:
            state.first_failed_at = now
        state.window_seconds = lockout_seconds

        locked_now = False
        retry_after = 0

        if state.fails >= fail_limit:
            state.lock_until = now + lockout_seconds
            locked_now = True
            retry_after = lockout_seconds

        self._store[key] = state

        if locked_now:
            # Reuse is_locked to normalize retry_after.
            _, retry_after = self.is_locked(key)
        return state.fails, locked_now, retry_after

    def register_success(self, key: str) -> None:
        self.clear(key)


store = AttemptsStore()

__all__ = ["AttemptState", "AttemptsStore", "store"]
