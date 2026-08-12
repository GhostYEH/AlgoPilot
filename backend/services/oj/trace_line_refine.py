"""追踪步骤行号修正（全题型通用）。

调试器停在「即将执行的行」，但变量变化通常来自「上一行已执行完」；
分支条件行需要跳到实际进入的 if / elif / else 体。
"""

from __future__ import annotations

import re
from typing import Any

_BRANCH_HEAD_RE = re.compile(r"^\s*(?:if|elif|else\s+if)\b")
_LOOP_HEAD_RE = re.compile(r"^\s*(?:for|while)\b")
_ELSE_RE = re.compile(r"^\s*else\s*(?::|\{|$)")

# 循环下标 / 扫描指针：变化时优先显示循环头或分支，而非上一行副作用
_INDEX_LIKE_VARS = frozenset({
    "c", "ch", "char", "i", "j", "k", "n", "m", "lo", "hi", "low", "high",
    "left", "right", "l", "r", "start", "end", "mid", "idx", "index",
    "row", "col", "u", "v", "a", "b", "p", "q", "x", "y",
})


def _line_text(lines: list[str], line_no: int) -> str:
    if line_no < 1 or line_no > len(lines):
        return ""
    return lines[line_no - 1]


def is_branch_condition_line(text: str) -> bool:
    return bool(_BRANCH_HEAD_RE.match(text.strip()))


def is_loop_header_line(text: str) -> bool:
    return bool(_LOOP_HEAD_RE.match(text.strip()))


def _base_name(var: str) -> str:
    return var.split("[", 1)[0].split(".", 1)[0]


def is_index_like_var(name: str) -> bool:
    return _base_name(name) in _INDEX_LIKE_VARS


def is_index_only_change(changed: list[str]) -> bool:
    return bool(changed) and all(is_index_like_var(c) for c in changed)


def has_state_change(changed: list[str]) -> bool:
    return any(not is_index_like_var(c) for c in changed)


def _line_mutates_var(text: str, var: str) -> bool:
    t = text.strip()
    base = _base_name(var)
    if re.search(rf"\b{re.escape(base)}\s*(?:=|\+=|-=|\*=|/=)", t):
        return True
    if base in ("st", "stack") and re.search(r"\b(?:push|pop|emplace|append)\b", t):
        return True
    if base in ("seen", "map", "num_map", "m") and re.search(r"\[|\=", t):
        return True
    return False


def _state_effect_line(
    stop_line: int,
    last_exec_line: int,
    changed: list[str],
    lines: list[str],
) -> int:
    stop_text = _line_text(lines, stop_line)
    last_text = _line_text(lines, last_exec_line)
    state_vars = [c for c in changed if not is_index_like_var(c)]
    stop_mut = any(_line_mutates_var(stop_text, c) for c in state_vars)
    last_mut = any(_line_mutates_var(last_text, c) for c in state_vars)
    if last_mut:
        return last_exec_line
    if stop_mut:
        return stop_line
    return last_exec_line


def _char_literal(code: str) -> str | None:
    m = re.match(r"^'((?:\\.|[^'\\])*)'$", code.strip())
    if not m:
        return None
    raw = m.group(1)
    if raw == "\\n":
        return "\n"
    if raw == "\\t":
        return "\t"
    if len(raw) == 1:
        return raw
    return raw


def _parse_int_literal(text: str) -> int | None:
    text = text.strip()
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    return None


def _scalar_from_vars(name: str, vars_map: dict[str, dict[str, Any]]) -> Any:
    snap = vars_map.get(name) or {}
    t = snap.get("type")
    v = snap.get("value")
    if t == "str" and isinstance(v, str):
        return v
    if t == "bool":
        return v
    if t in ("int", "float") and isinstance(v, (int, float)):
        return v
    if t in ("sequence", "stack", "queue", "list") and isinstance(v, list):
        return v
    if t in ("dict", "associative", "map") and v is not None:
        return v
    return None


def _resolve_operand(expr: str, vars_map: dict[str, dict[str, Any]]) -> Any:
    expr = expr.strip()
    lit = _parse_int_literal(expr)
    if lit is not None:
        return lit
    lit = _char_literal(expr) if expr.startswith("'") else None
    if lit is not None:
        return lit
    if expr.startswith('"') and expr.endswith('"'):
        return expr[1:-1]
    if re.fullmatch(r"-?\d+\.\d+", expr):
        return float(expr)
    base = _base_name(expr)
    if base != expr:
        seq = _scalar_from_vars(base, vars_map)
        if isinstance(seq, list):
            m = re.search(r"\[(\d+)\]", expr)
            if m:
                idx = int(m.group(1))
                if 0 <= idx < len(seq):
                    cell = seq[idx]
                    if isinstance(cell, (int, float, bool, str)):
                        return cell
                    return str(cell)
            m_var = re.search(r"\[(\w+)\]", expr)
            if m_var:
                idx_val = _scalar_from_vars(m_var.group(1), vars_map)
                if isinstance(idx_val, int) and 0 <= idx_val < len(seq):
                    cell = seq[idx_val]
                    if isinstance(cell, (int, float, bool, str)):
                        return cell
                    return str(cell)
        return None
    return _scalar_from_vars(base, vars_map)


def _dict_has_key(snap_val: Any, key: Any) -> bool:
    if isinstance(snap_val, dict):
        if isinstance(snap_val.get("entries"), list):
            key_s = str(key)
            return any(str(e.get("key")) == key_s for e in snap_val["entries"] if isinstance(e, dict))
        return str(key) in snap_val
    if isinstance(snap_val, list):
        key_s = str(key)
        return any(
            isinstance(e, dict) and str(e.get("key")) == key_s
            for e in snap_val
        )
    return False


def _eval_simple_condition(expr: str, vars_map: dict[str, dict[str, Any]]) -> bool | None:
    cond = expr.strip().rstrip(":")
    if not cond:
        return None

    if cond.startswith("!"):
        inner = _eval_simple_condition(cond[1:].strip(), vars_map)
        return None if inner is None else not inner
    if cond.startswith("not "):
        inner = _eval_simple_condition(cond[4:].strip(), vars_map)
        return None if inner is None else not inner

    m = re.match(r"^(.+?)\s+in\s+(\w+)\s*$", cond)
    if m:
        left = _resolve_operand(m.group(1).strip(), vars_map)
        container = _scalar_from_vars(m.group(2), vars_map)
        if left is not None and container is not None:
            return _dict_has_key(container, left)

    for op in ("==", "!=", "<=", ">=", "<", ">"):
        if op not in cond:
            continue
        parts = cond.split(op, 1)
        if len(parts) != 2:
            continue
        left = _resolve_operand(parts[0].strip(), vars_map)
        right = _resolve_operand(parts[1].strip(), vars_map)
        if left is not None and right is not None:
            try:
                if op == "==":
                    return left == right
                if op == "!=":
                    return left != right
                if op == "<=":
                    return left <= right
                if op == ">=":
                    return left >= right
                if op == "<":
                    return left < right
                if op == ">":
                    return left > right
            except TypeError:
                return None
        continue

    if re.search(r"\bempty\s*\(\s*\)", cond):
        m = re.match(r"^(\w+)\.empty\s*\(\s*\)", cond.strip())
        if m:
            seq = _scalar_from_vars(m.group(1), vars_map)
            if isinstance(seq, list):
                return len(seq) == 0

    m = re.match(r"^not\s+(\w+)\s*$", cond.strip())
    if m:
        val = _scalar_from_vars(m.group(1), vars_map)
        if isinstance(val, list):
            return len(val) == 0
        if isinstance(val, bool):
            return not val

    m = re.match(r"^(\w+)\s*$", cond.strip())
    if m:
        val = _scalar_from_vars(m.group(1), vars_map)
        if isinstance(val, list):
            return len(val) > 0
        if isinstance(val, bool):
            return bool(val)

    return None


def _extract_if_condition(text: str) -> str | None:
    t = text.strip()
    m = re.match(r"^(?:if|else\s+if|elif)\s*\(", t)
    if m:
        start = m.end()
        depth = 1
        i = start
        in_str: str | None = None
        while i < len(t):
            ch = t[i]
            if in_str:
                if ch == "\\" and i + 1 < len(t):
                    i += 2
                    continue
                if ch == in_str:
                    in_str = None
                i += 1
                continue
            if ch in ("'", '"'):
                in_str = ch
                i += 1
                continue
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    return t[start:i].strip()
            i += 1
        return None

    m = re.match(r"^(?:if|elif|else\s+if)\s+(.+?)\s*(?::\s*)?$", t)
    if m:
        return m.group(1).strip().rstrip(":")
    return None


def _find_next_branch_line(line_no: int, lines: list[str]) -> int:
    n = len(lines)
    i = line_no
    while i < n:
        i += 1
        t = lines[i - 1].strip()
        if not t or t.startswith("//") or t.startswith("#"):
            continue
        if t.startswith("else if") or t.startswith("elif ") or _ELSE_RE.match(t):
            return i
        if t.startswith("if ") or t.startswith("elif ") or t.startswith("for ") or t.startswith("while "):
            return line_no
        if not t.startswith("}"):
            return i
    return line_no


def resolve_branch_display_line(
    line_no: int,
    lines: list[str],
    vars_map: dict[str, dict[str, Any]],
) -> int:
    n = len(lines)
    line = line_no
    fallback = line_no
    visited = 0
    while 1 <= line <= n and visited < 16:
        visited += 1
        text = _line_text(lines, line)
        if not is_branch_condition_line(text):
            return line
        cond = _extract_if_condition(text)
        if not cond:
            return fallback
        verdict = _eval_simple_condition(cond, vars_map)
        if verdict is None:
            return fallback
        if verdict:
            return line
        nxt = _find_next_branch_line(line, lines)
        if nxt <= line:
            return fallback
        if is_branch_condition_line(_line_text(lines, nxt)):
            line = nxt
            continue
        return fallback
    return fallback


def refine_step_display_line(
    *,
    stop_line: int,
    changed: list[str],
    vars_map: dict[str, dict[str, Any]],
    lines: list[str],
    last_exec_line: int | None,
) -> int:
    """将调试停止行映射为用户应看到的「当前逻辑行」。"""
    n = len(lines) or 1
    stop_text = _line_text(lines, stop_line)
    display = stop_line

    if changed and last_exec_line is not None and has_state_change(changed):
        display = _state_effect_line(stop_line, last_exec_line, changed, lines)
    elif is_loop_header_line(stop_text) and changed:
        display = stop_line
    elif is_branch_condition_line(stop_text) and not has_state_change(changed):
        branch_line = resolve_branch_display_line(stop_line, lines, vars_map)
        cond = _extract_if_condition(stop_text)
        cond_true = _eval_simple_condition(cond, vars_map) if cond else None
        if branch_line != stop_line:
            display = branch_line
        elif cond_true is True:
            display = stop_line
        elif (
            changed
            and last_exec_line is not None
            and cond_true is False
            and is_loop_header_line(_line_text(lines, last_exec_line))
        ):
            display = last_exec_line
    elif changed and last_exec_line is not None:
        display = last_exec_line

    return max(1, min(n, display))


def refine_trace_step_lines(
    steps: list[Any],
    source: str,
) -> list[Any]:
    if not steps or not source.strip():
        return steps
    lines = source.splitlines()
    last_exec: int | None = None

    for s in steps:
        if isinstance(s, dict):
            stop = int(s.get("line") or 0)
            changed = list(s.get("changed") or [])
            vars_map = s.get("vars") or {}
            s["line"] = refine_step_display_line(
                stop_line=stop,
                changed=changed,
                vars_map=vars_map,
                lines=lines,
                last_exec_line=last_exec,
            )
            last_exec = stop
        else:
            stop = int(getattr(s, "line", 0) or 0)
            changed = list(getattr(s, "changed", None) or [])
            vars_map = getattr(s, "vars", None) or {}
            s.line = refine_step_display_line(
                stop_line=stop,
                changed=changed,
                vars_map=vars_map,
                lines=lines,
                last_exec_line=last_exec,
            )
            last_exec = stop
    return steps
