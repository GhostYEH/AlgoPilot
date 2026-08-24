"""Small in-process rate limiter for expensive authenticated endpoints.

This is deliberately a defence-in-depth layer for the single-process desktop
deployment.  A horizontally scaled deployment must additionally enforce the
same policy at the gateway or use a shared store such as Redis.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, status

from core.config import settings
from models.db_models import User

_WINDOW_SECONDS = 60.0
_hits: dict[tuple[int, str, str], deque[float]] = defaultdict(deque)
_lock = threading.Lock()


def enforce_oj_rate_limit(user: User, operation: str) -> None:
    """Apply a per-user sliding-window request limit to OJ operations."""
    limit = (
        settings.oj_ai_requests_per_minute
        if operation in {"ai_diagnose", "trace_diagnose", "trace_narrate", "trace_report"}
        else settings.oj_run_requests_per_minute
    )
    now = time.monotonic()
    # 用户名纳入键以避免独立测试数据库复用自增 ID 时相互污染；生产中两者
    # 均稳定且用户名全局唯一。
    key = (user.id, user.username, operation)
    with _lock:
        bucket = _hits[key]
        while bucket and now - bucket[0] >= _WINDOW_SECONDS:
            bucket.popleft()
        if len(bucket) >= limit:
            retry_after = max(1, int(_WINDOW_SECONDS - (now - bucket[0])) + 1)
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"请求过于频繁，请在 {retry_after} 秒后重试",
                headers={"Retry-After": str(retry_after)},
            )
        bucket.append(now)


def reset_rate_limits_for_tests() -> None:
    """Keep deterministic API tests isolated without exposing a production API."""
    with _lock:
        _hits.clear()
