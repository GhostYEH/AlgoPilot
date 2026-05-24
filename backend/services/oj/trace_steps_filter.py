"""追踪步骤去噪：仅保留对用户可视化有意义的步。"""

from __future__ import annotations

from typing import TypeVar

T = TypeVar("T")


def _changed(s: T) -> list:
    if isinstance(s, dict):
        return list(s.get("changed") or [])
    return list(getattr(s, "changed", None) or [])


def filter_meaningful_steps(steps: list[T], *, max_steps: int = 200) -> list[T]:
    """保留首步、末步，以及变量发生变化的步。"""
    if not steps:
        return []
    out: list[T] = []
    last = len(steps) - 1
    for i, s in enumerate(steps):
        if i == 0 or i == last or _changed(s):
            out.append(s)
    return out[:max_steps]
