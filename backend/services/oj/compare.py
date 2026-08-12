from __future__ import annotations

import math
from typing import Any


def _norm_list_node_chain(value: Any) -> Any:
    """将 ListNode 链转为 list（判题脚本内已定义 ListNode）。"""
    if value is None:
        return None
    if isinstance(value, list):
        return value
    cls_name = type(value).__name__
    if cls_name != "ListNode":
        return value
    out: list[int] = []
    cur = value
    seen = 0
    while cur is not None and seen < 10000:
        out.append(cur.val)
        cur = cur.next
        seen += 1
    return out


def _norm_tree(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, list):
        return value
    cls_name = type(value).__name__
    if cls_name != "TreeNode":
        return value
    if value is None:
        return []
    from collections import deque

    root = value
    if root is None:
        return []
    q: deque = deque([root])
    out: list[int | None] = []
    while q:
        node = q.popleft()
        if node is None:
            out.append(None)
            continue
        out.append(node.val)
        q.append(node.left)
        q.append(node.right)
    while out and out[-1] is None:
        out.pop()
    return out


def normalize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, list):
        return [normalize_value(v) for v in value]
    if isinstance(value, tuple):
        return [normalize_value(v) for v in value]
    cls = type(value).__name__
    if cls == "ListNode":
        return _norm_list_node_chain(value)
    if cls == "TreeNode":
        return _norm_tree(value)
    return value


def values_equal(actual: Any, expected: Any, *, order_insensitive: bool = False) -> bool:
    actual = normalize_value(actual)
    expected = normalize_value(expected)

    if isinstance(actual, float) and isinstance(expected, (int, float)):
        return math.isclose(actual, float(expected), rel_tol=1e-9, abs_tol=1e-9)
    if isinstance(expected, float) and isinstance(actual, (int, float)):
        return math.isclose(float(actual), expected, rel_tol=1e-9, abs_tol=1e-9)

    if isinstance(actual, list) and isinstance(expected, list):
        if order_insensitive and len(actual) == len(expected):
            try:
                return sorted(actual) == sorted(expected)
            except TypeError:
                pass
        if len(actual) != len(expected):
            return False
        return all(values_equal(a, e, order_insensitive=order_insensitive) for a, e in zip(actual, expected))

    return actual == expected
