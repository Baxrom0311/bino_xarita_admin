import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, Tuple

from fastapi import HTTPException, Request, status

from app.core.config import settings


def _client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # first IP is the original client in typical proxy setups
        ip = forwarded_for.split(",")[0].strip()
        if ip:
            return ip
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


@dataclass
class _LockState:
    until: float
    failures: Deque[float]


class LoginSecurity:
    """
    In-memory rate limiting + brute-force lockout for /api/auth/login.

    This project targets a small deployment (single admin). In-memory protection
    is enough and keeps the stack simple (no Redis).
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._rate: Dict[Tuple[str, str], Deque[float]] = {}
        self._bf: Dict[Tuple[str, str], _LockState] = {}

    def reset(self) -> None:
        with self._lock:
            self._rate.clear()
            self._bf.clear()

    def _now(self) -> float:
        return time.monotonic()

    def _cleanup_deque(self, dq: Deque[float], window_seconds: int, now: float) -> None:
        cutoff = now - window_seconds
        while dq and dq[0] < cutoff:
            dq.popleft()

    def check_rate_limit(self, request: Request, bucket: str = "auth_login") -> None:
        """
        Window limiter: allow N requests per 60s per IP per bucket.
        """
        ip = _client_ip(request)
        now = self._now()
        window_seconds = 60
        limit = int(getattr(settings, "LOGIN_RATE_LIMIT_PER_MINUTE", 10))

        key = (bucket, ip)
        with self._lock:
            dq = self._rate.get(key)
            if dq is None:
                dq = deque()
                self._rate[key] = dq
            self._cleanup_deque(dq, window_seconds, now)
            if len(dq) >= limit:
                retry_after = max(1, int(window_seconds - (now - dq[0])))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Try again later.",
                    headers={"Retry-After": str(retry_after)},
                )
            dq.append(now)

    def check_lockout(self, request: Request, username: str) -> None:
        ip = _client_ip(request)
        now = self._now()
        key = (ip, username)
        with self._lock:
            state = self._bf.get(key)
            if not state:
                return
            if state.until <= now:
                # lock expired; keep failures deque but unlock
                state.until = 0.0
                return
            retry_after = max(1, int(state.until - now))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Try again later.",
                headers={"Retry-After": str(retry_after)},
            )

    def register_failure(self, request: Request, username: str) -> None:
        ip = _client_ip(request)
        now = self._now()
        key = (ip, username)

        max_attempts = int(getattr(settings, "LOGIN_MAX_FAILED_ATTEMPTS", 5))
        window_seconds = int(getattr(settings, "LOGIN_FAILURE_WINDOW_SECONDS", 900))  # 15m
        lock_seconds = int(getattr(settings, "LOGIN_LOCK_SECONDS", 300))  # 5m

        with self._lock:
            state = self._bf.get(key)
            if not state:
                state = _LockState(until=0.0, failures=deque())
                self._bf[key] = state
            self._cleanup_deque(state.failures, window_seconds, now)
            state.failures.append(now)
            if len(state.failures) >= max_attempts:
                state.until = now + lock_seconds

    def register_success(self, request: Request, username: str) -> None:
        ip = _client_ip(request)
        key = (ip, username)
        with self._lock:
            self._bf.pop(key, None)


login_security = LoginSecurity()

