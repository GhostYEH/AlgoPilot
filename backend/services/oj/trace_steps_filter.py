"""追踪步骤去噪：仅保留对用户可视化有意义的步。"""

from __future__ import annotations

from typing import TypeVar

T = TypeVar("T")


def _changed(s: T) -> list:
    if isinstance(s, dict):
        return list(s.get("changed") or [])
    return list(getattr(s, "changed", None) or [])


def _line(s: T) -> int:
    if isinstance(s, dict):
        return int(s.get("line") or 0)
    return int(getattr(s, "line", 0) or 0)


def _vars(s: T) -> dict:
    if isinstance(s, dict):
        return dict(s.get("vars") or {})
    return dict(getattr(s, "vars", None) or {})


def _set_changed(s: T, changed: list[str]) -> None:
    if isinstance(s, dict):
        s["changed"] = changed
    else:
        setattr(s, "changed", changed)


def collapse_consecutive_same_line_steps(steps: list[T]) -> list[T]:
    """Drop only the first pre-statement frame from each same-line GDB run."""
    if not steps:
        return []
    collapsed: list[T] = []
    index = 0
    while index < len(steps):
        end = index + 1
        while end < len(steps) and _line(steps[end]) == _line(steps[index]):
            end += 1
        run = steps[index:end]
        collapsed.extend(run[1:] if len(run) > 1 else run)
        index = end

    previous: dict = {}
    for step in collapsed:
        current = _vars(step)
        changed = [name for name, value in current.items() if previous.get(name) != value]
        _set_changed(step, changed)
        previous = current
    return collapsed


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
