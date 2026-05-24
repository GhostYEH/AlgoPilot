"""根据追踪步骤中的真实变量快照生成旁白（与用户代码执行一致，非题号模板）。"""

from __future__ import annotations

import re
from typing import Any


def _parse_gdb_char_text(text: str) -> str | None:
    text = text.strip()
    m = re.match(r"^(-?\d+)\s+'((?:\\.|[^'\\])*)'$", text)
    if not m:
        return None
    code = int(m.group(1))
    literal = m.group(2)
    if code == 0 or literal in ("\\000", "\\0"):
        return None
    if 32 <= code <= 126:
        return repr(chr(code))
    return None


def _preview_value(snap: dict[str, Any], *, max_len: int = 48) -> str | None:
    t = snap.get("type") or "other"
    v = snap.get("value")
    if t == "none" or v is None:
        return "空"
    if t == "str":
        s = str(v)
        if not s:
            return '""'
        if len(s) == 1:
            return repr(s)
        if any(ord(c) < 32 and c not in "\t\n\r" for c in s):
            return None
        return s if len(s) <= max_len else s[: max_len - 1] + "…"
    if t in ("int", "float", "bool"):
        return str(v)
    if t in ("sequence", "stack", "queue"):
        if not isinstance(v, list):
            return str(v)[:max_len]
        if not v:
            return "[]（空）"
        items: list[str] = []
        for x in v[:8]:
            if isinstance(x, str) and len(x) == 1:
                items.append(repr(x))
            elif isinstance(x, int) and 32 <= x <= 126:
                items.append(repr(chr(x)))
            else:
                items.append(str(x))
        suffix = "…" if len(v) > 8 else ""
        hint = snap.get("view_hint") or t
        label = "栈" if hint == "stack" else "序列"
        return f"{label}[{', '.join(items)}{suffix}]"
    if t == "list":
        if not isinstance(v, list):
            return str(v)[:max_len]
        inner = ", ".join(str(x) for x in v[:8])
        suffix = "…" if len(v) > 8 else ""
        return f"[{inner}{suffix}]"
    if t == "matrix":
        if isinstance(v, dict):
            rows = v.get("rows", 0)
            cols = v.get("cols", 0)
            return f"{rows}×{cols} 矩阵"
        return "矩阵"
    if t == "matrix_overflow":
        return "矩阵过大"
    if t in ("linked_list", "node_ref"):
        return "链表结点"
    if t == "tree":
        return "二叉树"
    if t in ("dict", "map", "associative"):
        if isinstance(v, list):
            return f"{{{len(v)} 项}}"
        if isinstance(v, dict):
            keys = list(v.keys())[:4]
            return "{" + ", ".join(str(k) for k in keys) + ("…" if len(v) > 4 else "") + "}"
        return "字典"
    if t == "other" and isinstance(v, str):
        char = _parse_gdb_char_text(v)
        if char:
            return char
        if re.match(r"^(-?\d+)\s+'", v):
            return None
        if any(x in v for x in ("\\000", "\\002", "140732")):
            return None
        return v if len(v) <= max_len else v[: max_len - 1] + "…"
    return str(v)[:max_len]


def _describe_change(name: str, snap: dict[str, Any]) -> str | None:
    preview = _preview_value(snap)
    if preview is None:
        return None
    return f"{name} → {preview}"


def generate_step_narration(steps: list[dict[str, Any]]) -> list[dict[str, int | str]]:
    """按每步 changed 变量生成中文旁白，索引与 steps 对齐。"""
    out: list[dict[str, int | str]] = []
    for i, s in enumerate(steps):
        changed = s.get("changed") or []
        if not changed:
            continue
        vars_map = s.get("vars") or {}
        line = int(s.get("line") or 0)
        parts: list[str] = []
        for n in changed[:8]:
            desc = _describe_change(n, vars_map.get(n) or {})
            if desc:
                parts.append(desc)
        if not parts:
            continue
        if len(changed) > len(parts):
            parts.append(f"等 {len(changed)} 项")
        text = f"第 {line} 行：{'；'.join(parts)}"
        out.append({"step_index": i, "text": text[:240]})
    return out
