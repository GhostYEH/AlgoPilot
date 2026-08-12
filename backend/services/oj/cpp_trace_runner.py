

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Literal

from services.oj.cpp_runner import (
    _build_cpp_source,
    _compile_timeout_message,
    _find_gpp,
    _toolchain_roots,
    cpp_compile_timeout_seconds,
    ensure_toolchain_on_path,
)
from services.oj.trace_runner import TraceStepOut, TraceSummary
from utils.security import CPP_SECURITY_MESSAGE, CppSecurityViolation, check_cpp_security
from services.oj.trace_steps_filter import (
    collapse_consecutive_same_line_steps,
    compress_initialization_phase,
    filter_meaningful_steps,
)
from services.oj.trace_line_refine import refine_trace_step_lines

TraceVerdict = Literal["OK", "RE", "TLE", "CE"]
MAX_CPP_TRACE_STEPS = 200
# 用户代码 GDB 追踪子进程硬上限（秒），防止死循环拖垮沙箱
CPP_TRACE_SUBPROCESS_CAP_S = 30.0


def _trace_subprocess_timeout(time_limit_ms: int) -> float:
    """动态追踪 GDB 超时：在用户请求与硬上限之间取较小值，避免死循环占满 worker。"""
    requested = max(1.0, time_limit_ms / 1000)
    return min(CPP_TRACE_SUBPROCESS_CAP_S, requested)

_GDB_STL_SCRIPT = Path(__file__).with_name("gdb_stl_extract.py")
_TRACE_VIZ_MARKER_START = "@@TRACE_VIZ_JSON@@"
_TRACE_VIZ_MARKER_END = "@@END@@"

_GDB_NOISE_NAMES = frozenset(
    {
        "lock_free",
        "fiberid",
        "nested",
        "startinfo",
        "ret",
        "__saved_mask",
        "__unguarded",
        "__atomic",
    }
)


def _normalize_gdb_expr(expr: str) -> str:
    """GDB MI / console 转义 → 可解析表达式。"""
    expr = expr.strip()
    if '\\"' in expr:
        expr = expr.replace('\\"', '"')
    return expr


def _find_gdb() -> str | None:
    ensure_toolchain_on_path()
    for name in ("gdb", "gdb.exe"):
        p = shutil.which(name)
        if p:
            return p
    import os

    for env_key in ("GDB", "MINGW_GDB"):
        p = os.environ.get(env_key)
        if p and Path(p).is_file():
            return p
    for base in _toolchain_roots():
        cand = base / "bin" / "gdb.exe"
        if cand.is_file():
            return str(cand)
    return None


def gdb_available() -> bool:
    return _find_gdb() is not None


def _parse_mi_line(line: str) -> tuple[str | None, dict[str, Any]]:
    line = line.strip()
    if not line:
        return None, {}
    if line.startswith("@"):
        return "result", {"raw": line}
    if line.startswith("^"):
        m = re.match(r"\^(\w+)", line)
        kind = m.group(1) if m else "done"
        payload: dict[str, Any] = {"raw": line}
        if ",nr_rows=" in line or "rows=" in line:
            payload["has_table"] = True
        return kind, payload
    if line.startswith("*"):
        return "notify", {"raw": line}
    return "console", {"raw": line}


def _gdb_script_path(work_dir: Path) -> Path | None:
    """将 gdb_stl_extract.py 复制到调试目录并返回路径。"""
    if not _GDB_STL_SCRIPT.is_file():
        return None
    dest = work_dir / "gdb_stl_extract.py"
    shutil.copy2(_GDB_STL_SCRIPT, dest)
    return dest


def _gdb_bootstrap_commands(script: Path | None) -> list[str]:
    cmds = ["-gdb-set mi-async off", "-gdb-set python print-stack none"]
    if script and script.is_file():
        p = script.as_posix().replace("\\", "/")
        cmds.append(f'-interpreter-exec console "source {p}"')
    return cmds


def _gdb_step_capture_commands() -> list[str]:
    return [
        '-interpreter-exec console "trace-viz-dump-locals"',
        "-stack-list-variables --all-values",
        '-interpreter-exec console "info locals"',
    ]


def _run_gdb_mi(exe: Path, commands: list[str], timeout_s: float) -> tuple[int, str]:
    gdb = _find_gdb()
    if not gdb:
        return 1, "未找到 gdb，请安装 MinGW gdb 并加入 PATH"
    script = "\n".join(commands) + "\n"
    try:
        proc = subprocess.run(
            [gdb, "-i=mi", "--quiet", str(exe)],
            input=script,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            cwd=str(exe.parent),
        )
    except subprocess.TimeoutExpired:
        return (
            124,
            "GDB 追踪超时：疑似死循环或单步过慢，已强制终止（上限 "
            f"{timeout_s:.0f}s）。请检查 while/for 中指针/计数器是否更新。",
        )
    out = (proc.stdout or "") + "\n" + (proc.stderr or "")
    return proc.returncode, out


def _extract_line_from_mi(output: str) -> int | None:
    for line in output.splitlines():
        m = re.search(r'line="(\d+)"', line)
        if m:
            return int(m.group(1))
        m2 = re.search(r"line=(\d+)", line)
        if m2:
            return int(m2.group(1))
    return None


def _parse_info_locals(text: str) -> dict[str, dict[str, Any]]:
    """解析 GDB console `info locals`（~"var = …"）输出。"""
    vars_out: dict[str, dict[str, Any]] = {}
    for raw in text.splitlines():
        line = raw.strip()
        m = re.match(r'^~"(.+)"$', line)
        if not m:
            m2 = re.search(r'~"(.+)"', line)
            body = m2.group(1).replace("\\n", "\n").strip() if m2 else None
        else:
            body = m.group(1).replace("\\n", "\n").strip()
        if body:
            eq = body.find("=")
            if eq <= 0:
                continue
            name, expr = body[:eq].strip(), body[eq + 1 :].strip()
        else:
            if not line or line.startswith("&") or line.startswith("^"):
                continue
            plain = re.match(r"(\w+)\s*=\s*(.+)$", line)
            if not plain:
                continue
            name, expr = plain.group(1), plain.group(2).strip()
        if expr in ("void", "..."):
            continue
        payload = _cpp_expr_to_payload(expr)
        if payload:
            vars_out[name] = payload
    return vars_out


def _parse_mi_variables_line(line: str) -> dict[str, dict[str, Any]]:
    """解析 ^done,variables=[{name=\"n\",value=\"4\"},…]。"""
    if "variables=" not in line:
        return {}
    start = line.index("variables=[") + len("variables=[")
    end = line.rfind("]")
    if end <= start:
        return {}
    body = line[start:end]
    vars_out: dict[str, dict[str, Any]] = {}
    pos = 0
    while pos < len(body):
        head = re.match(r'\{name="([^"]+)",value="', body[pos:])
        if not head:
            break
        name = head.group(1)
        val_start = pos + head.end()
        val_end = body.find('"}', val_start)
        if val_end < 0:
            break
        expr = body[val_start:val_end]
        payload = _cpp_expr_to_payload(expr)
        if payload:
            vars_out[name] = payload
        pos = val_end + 2
    return vars_out


def _unescape_gdb_string(raw: str) -> str:
  """GDB MI / console 中的 C 字符串字面量 → Python str。"""
  if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
    body = raw[1:-1]
    return (
      body.replace("\\n", "\n")
      .replace("\\t", "\t")
      .replace('\\"', '"')
      .replace("\\\\", "\\")
    )
  return raw


def _parse_gdb_char_items(body: str) -> list[str]:
    """解析 GDB deque/stack 元素列表中的 char 项（如 40 '(', 2 '\\002'）。"""
    out: list[str] = []
    for m in re.finditer(r"(?:\d+\s+)?'((?:\\.|[^'\\])*)'", body):
        raw = m.group(1)
        if not raw:
            continue
        if raw[0] == "\\" and len(raw) >= 2:
            esc = {"n": "\n", "t": "\t", "r": "\r", "'": "'", "\\": "\\", "0": "\0"}
            tail = raw[1:]
            if tail in esc:
                out.append(esc[tail])
            elif tail.isdigit():
                try:
                    out.append(chr(int(tail, 8) if len(tail) == 3 else int(tail)))
                except (ValueError, OverflowError):
                    out.append("?")
            else:
                out.append(tail[:1] if tail else "?")
        else:
            out.append(raw)
    return out


def _parse_sequence_body(body: str) -> list[str]:
    """deque/stack 花括号内元素 → 展示用字符串列表（栈底→栈顶）。"""
    chars = _parse_gdb_char_items(body)
    if chars:
        return chars
    nums = [int(x) for x in re.findall(r"-?\d+", body)]
    if nums and "'" not in body and "\\" not in body:
        return [str(n) for n in nums]
    return chars


def _parse_stl_deque(expr: str, *, as_stack: bool = False) -> dict[str, Any] | None:
    """std::deque with N elements = {...}（GDB 常见格式，非 of length）。"""
    m = re.match(
        r"std::deque with (-?\d+) element(?:s)?(?:\s*=\s*\{(.+)\})?\s*$",
        expr,
        re.DOTALL,
    )
    if not m:
        return None
    n = int(m.group(1))
    if n < 0 or n > 64:
        kind = "stack" if as_stack else "queue"
        return _normalize_var_payload({"type": kind, "value": []})
    body = m.group(2)
    if not body:
        kind = "stack" if as_stack else "queue"
        return _normalize_var_payload({"type": kind, "value": []})
    items = _parse_sequence_body(body)
    kind = "stack" if as_stack or ("'" in body or "\\" in body) else "queue"
    if kind == "queue" and items and all(x.isdigit() or (x.startswith("-") and x[1:].isdigit()) for x in items):
        return _normalize_var_payload({"type": "queue", "value": [int(x) for x in items][:n]})
    if kind == "queue" and items:
        return _normalize_var_payload(
            {"type": "queue", "value": [int(x) if str(x).lstrip("-").isdigit() else x for x in items][:n]}
        )
    return _normalize_var_payload(
        {"type": "stack" if kind == "stack" else "queue", "value": items[:n] if items else []}
    )


def _parse_stl_stack(expr: str) -> dict[str, Any] | None:
    """std::stack 底层 deque 的 GDB 输出 → stack 快照。"""
    m = re.search(
        r"std::stack\s+wrapping:\s+std::deque\s+with\s+(-?\d+)\s+element",
        expr,
    )
    if not m:
        return None
    n = int(m.group(1))
    if n < 0 or n > 64:
        return _normalize_var_payload({"type": "stack", "value": []})
    inner = re.search(r"=\s*\{(.+)\}\s*$", expr, re.DOTALL)
    if not inner:
        return _normalize_var_payload({"type": "stack", "value": []})
    items = _parse_sequence_body(inner.group(1))
    if n == 0:
        return _normalize_var_payload({"type": "stack", "value": []})
    return _normalize_var_payload({"type": "stack", "value": items[:n] if items else []})


def _parse_quoted_string(expr: str) -> dict[str, Any] | None:
  expr = expr.strip()
  if len(expr) >= 2 and expr[0] == '"' and expr[-1] == '"':
    return {"type": "str", "value": _unescape_gdb_string(expr)}
  std_str = re.match(
    r'(?:std::(?:basic_)?string(?:<[^>]+>)?)\s*(?:=\s*)?"(.*)"\s*$',
    expr,
  )
  if std_str:
    return {"type": "str", "value": _unescape_gdb_string(f'"{std_str.group(1)}"')}
  return None


def _parse_gdb_char_text(text: str) -> dict[str, Any] | None:
    text = text.strip()
    m = re.match(r"^(-?\d+)\s+'((?:\\.|[^'\\])*)'$", text)
    if not m:
        return None
    code = int(m.group(1))
    literal = m.group(2)
    if code == 0 or literal in ("\\000", "\\0"):
        return None
    if 32 <= code <= 126:
        return {"type": "str", "value": chr(code)}
    return None


def _normalize_stack_char_items(items: list[Any]) -> list[Any]:
    out: list[Any] = []
    for x in items:
        if isinstance(x, int) and 32 <= x <= 126:
            out.append(chr(x))
        else:
            out.append(x)
    return out


def _normalize_var_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """统一为 sequence / associative 协议，并保留标量、矩阵、链表等专用类型。"""
    t = payload.get("type")
    if t == "list":
        return {"type": "sequence", "view_hint": "vector", "value": payload.get("value") or []}
    if t == "stack":
        return {"type": "sequence", "view_hint": "stack", "value": payload.get("value") or []}
    if t == "queue":
        hint = payload.get("view_hint") or "queue"
        return {"type": "sequence", "view_hint": hint, "value": payload.get("value") or []}
    if t == "dict":
        raw = payload.get("value")
        entries: list[Any] = []
        if isinstance(raw, dict) and isinstance(raw.get("entries"), list):
            entries = raw["entries"]
        return {"type": "associative", "view_hint": "map", "value": entries}
    if t == "sequence" and "view_hint" not in payload:
        payload = {**payload, "view_hint": "vector"}
    if t == "associative" and "view_hint" not in payload:
        payload = {**payload, "view_hint": "map"}
    hint = payload.get("view_hint")
    if payload.get("type") == "sequence" and hint == "stack" and isinstance(payload.get("value"), list):
        payload = {**payload, "value": _normalize_stack_char_items(payload["value"])}
    return payload


def _decode_trace_viz_blob(blob: str) -> str:
    """Unescape GDB MI console JSON (quotes become backslash-quote)."""
    blob = blob.strip()
    if '\\"' in blob:
        blob = blob.replace('\\"', '"')
    return blob


def _extract_trace_viz_blob(text: str) -> str | None:
    """从 GDB 段（含 MI ~\"…\" 行）提取 JSON  blob。"""
    chunks: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        m = re.match(r'^~"(.+)"\s*$', line)
        if m:
            chunks.append(m.group(1).replace("\\n", "\n"))
    merged = "".join(chunks) if chunks else text
    idx = 0
    last_blob: str | None = None
    while True:
        start_m = merged.find(_TRACE_VIZ_MARKER_START, idx)
        if start_m < 0:
            break
        start = start_m + len(_TRACE_VIZ_MARKER_START)
        end_m = merged.find(_TRACE_VIZ_MARKER_END, start)
        if end_m < 0:
            break
        last_blob = merged[start:end_m]
        idx = end_m + len(_TRACE_VIZ_MARKER_END)
    return last_blob


def _parse_trace_viz_marker(text: str) -> dict[str, dict[str, Any]] | None:
    """从 GDB 段中解析 @@TRACE_VIZ_JSON@@…@@END@@（取最后一次 dump）。"""
    blob = _extract_trace_viz_blob(text)
    if not blob:
        return None
    blob = _decode_trace_viz_blob(blob)
    try:
        raw = json.loads(blob)
    except json.JSONDecodeError:
        return None
    if not isinstance(raw, dict):
        return None
    if "__error" in raw and len(raw) == 1:
        return None
    out: dict[str, dict[str, Any]] = {}
    for name, snap in raw.items():
        if not isinstance(snap, dict):
            continue
        out[name] = _normalize_var_payload(snap)
    return out or None


def _cpp_expr_to_payload(expr: str) -> dict[str, Any] | None:
    expr = _normalize_gdb_expr(expr.strip().rstrip(","))
    if expr in ("<optimized out>", "..."):
        return None
    str_payload = _parse_quoted_string(expr)
    if str_payload:
        return str_payload
    if expr in ("true", "false"):
        return {"type": "bool", "value": expr == "true"}
    char_payload = _parse_gdb_char_text(expr)
    if char_payload:
        return char_payload
    if re.fullmatch(r"-?\d+", expr):
        return {"type": "int", "value": int(expr)}
    if re.fullmatch(r"-?\d+\.\d+(?:[eE][+-]?\d+)?", expr):
        return {"type": "float", "value": float(expr)}
    if expr == "0x0" or expr == "nullptr" or expr == "0":
        return {"type": "node_ref", "value": {"node": None, "nodes": {}}}
    std_str_len = re.match(
        r'(?:std::(?:basic_)?string(?:<[^>]+>)?)\s*(?:with length \d+)?[^"]*"(.*)"\s*$',
        expr,
    )
    if std_str_len:
        return {"type": "str", "value": _unescape_gdb_string(f'"{std_str_len.group(1)}"')}
    std_vec = re.match(r"std::vector of length (\d+)[^=]*=\s*\{([^}]*)\}", expr)
    if std_vec:
        n = int(std_vec.group(1))
        vals = [int(x) for x in re.findall(r"-?\d+", std_vec.group(2))][:n]
        return _normalize_var_payload({"type": "list", "value": vals})
    std_q = re.search(
        r"std::queue\s+wrapping:\s*std::deque\s+with\s+(\d+)\s+elements?(?:\s*=\s*\{([^}]*)\})?",
        expr,
    )
    if std_q:
        n = int(std_q.group(1))
        body = std_q.group(2) or ""
        if n == 0:
            return _normalize_var_payload(
                {"type": "sequence", "view_hint": "tree_build_queue", "value": []}
            )
        ptrs = re.findall(r"0x[0-9a-fA-F]+", body)
        if ptrs:
            return _normalize_var_payload(
                {
                    "type": "sequence",
                    "view_hint": "tree_build_queue",
                    "value": [f"节点@{p[-4:]}" for p in ptrs],
                }
            )
    st_stack = _parse_stl_stack(expr)
    if st_stack:
        return _normalize_var_payload(st_stack)
    st_deque = _parse_stl_deque(expr, as_stack=False)
    if st_deque:
        return _normalize_var_payload(st_deque)
    std_deque = re.match(r"std::deque of length (\d+)[^=]*=\s*\{([^}]*)\}", expr)
    if std_deque:
        n = int(std_deque.group(1))
        if n < 0 or n > 64:
            return _normalize_var_payload({"type": "queue", "value": []})
        items = _parse_sequence_body(std_deque.group(2))
        if items and ("'" in std_deque.group(2) or "\\" in std_deque.group(2)):
            return _normalize_var_payload({"type": "stack", "value": items[:n]})
        vals = [int(x) for x in re.findall(r"-?\d+", std_deque.group(2))][:n]
        return _normalize_var_payload({"type": "queue", "value": vals})
    deque_plain = re.match(r"deque\s*<\s*int\s*>\s*=\s*\{(.+)\}", expr)
    if deque_plain:
        vals = [int(x) for x in re.findall(r"-?\d+", deque_plain.group(1))]
        if vals:
            return _normalize_var_payload({"type": "queue", "value": vals})
    std_map_full = re.match(
        r"std::unordered_map with (\d+) element(?:s)? = \{(.*)\}\s*$",
        expr,
        re.DOTALL,
    )
    if std_map_full:
        entries = [
            {"key": int(m.group(1)), "value": int(m.group(2))}
            for m in re.finditer(r"\[(-?\d+)\]\s*=\s*(-?\d+)", std_map_full.group(2))
        ]
        return _normalize_var_payload({"type": "dict", "value": {"entries": entries}})
    std_map = re.match(r"std::unordered_map with (\d+) element(?:s)?", expr)
    if std_map:
        cnt = int(std_map.group(1))
        if cnt > 64:
            return {"type": "other", "value": f"unordered_map（{cnt} 项，过大未展开）"}
        if cnt == 0:
            return _normalize_var_payload({"type": "dict", "value": {"entries": []}})
        return {"type": "other", "value": f"unordered_map（{cnt} 项）"}
    vec_m = re.match(r"vector\s*<\s*vector\s*<\s*int\s*>\s*>\s*=\s*\{(.+)\}", expr)
    if vec_m:
        return _parse_nested_vector(vec_m.group(1))
    vec1 = re.match(r"vector\s*<\s*int\s*>\s*=\s*\{(.+)\}", expr)
    if vec1:
        nums = [int(x) for x in re.findall(r"-?\d+", vec1.group(1))]
        return _normalize_var_payload({"type": "list", "value": nums})
    arr = re.match(r"\{([-\d,\s]+)\}", expr)
    if arr and "," in arr.group(1):
        nums = [int(x) for x in re.findall(r"-?\d+", arr.group(1))]
        if nums:
            return _normalize_var_payload({"type": "list", "value": nums})
    return {"type": "other", "value": expr[:120]}


def _parse_nested_vector(inner: str) -> dict[str, Any]:
    rows_raw = re.findall(r"\{([^{}]*)\}", inner)
    cells: list[list[int]] = []
    for row in rows_raw:
        cells.append([int(x) for x in re.findall(r"-?\d+", row)])
    if not cells:
        return {"type": "matrix", "value": {"rows": 0, "cols": 0, "cells": []}}
    cols = max(len(r) for r in cells)
    return {
        "type": "matrix",
        "value": {"rows": len(cells), "cols": cols, "cells": cells},
    }


def _user_line_stdio(abs_line: int, user_line_count: int) -> int:
    """洛谷完整程序：行号与用户源码一致。"""
    if abs_line < 1:
        return 1
    return min(user_line_count, abs_line)


def _is_garbage_str_value(val: Any) -> bool:
    if not isinstance(val, str):
        return False
    if not val:
        return False
    if any(ord(c) < 32 and c not in "\t\n\r" for c in val):
        return True
    if re.search(r"\\0\d{2,3}", val):
        return True
    return False


def _sanitize_gdb_vars(
    vars_snap: dict[str, dict[str, Any]], line: int
) -> dict[str, dict[str, Any]]:
    """去掉 GDB 未初始化阶段的脏 map/vector 快照。"""
    out: dict[str, dict[str, Any]] = {}
    for name, snap in vars_snap.items():
        if name in _GDB_NOISE_NAMES or name.startswith("__"):
            continue
        if snap.get("type") == "other":
            text = str(snap.get("value", ""))
            if text in ("<optimized out>", "..."):
                continue
            if "Cannot access memory" in text or (
                text.startswith("<") and (":" in text or text.endswith("?>"))
            ):
                continue
            if name in ("root", "curr") and re.match(r"^0x[0-9a-fA-F]+", text.strip()):
                continue
            if name == "q" and "std::queue" in text:
                parsed_q = _cpp_expr_to_payload(text)
                if parsed_q:
                    snap = _normalize_var_payload(parsed_q)
                else:
                    continue
            char_snap = _parse_gdb_char_text(text)
            if char_snap:
                snap = char_snap
            elif re.match(r"^(-?\d+)\s+'", text):
                continue
            if "std::stack" in text:
                parsed = _parse_stl_stack(text)
                if parsed:
                    snap = _normalize_var_payload(parsed)
            elif "std::deque" in text:
                parsed = _parse_stl_deque(text, as_stack=False)
                if parsed:
                    snap = _normalize_var_payload(parsed)
            if "unordered_map" in text and ("过大" in text or "140732" in text):
                snap = _normalize_var_payload({"type": "dict", "value": {"entries": []}})
        if snap.get("type") == "str" and _is_garbage_str_value(snap.get("value")):
            continue
        if snap.get("type") == "other" and name in ("s", "str", "input"):
            text = str(snap.get("value", ""))
            if _is_garbage_str_value(text) or re.search(r"\\0\d{2,3}", text):
                continue
        seq_types = ("list", "sequence")
        if name == "nums" and snap.get("type") in seq_types:
            arr = snap.get("value") or []
            if isinstance(arr, list) and len(arr) > 64 and line < 16:
                continue
        out[name] = snap
    return out


def _is_plausible_step(vars_snap: dict[str, dict[str, Any]], line: int) -> bool:
    """跳过 main 入口尚未读入 stdin 时的未初始化局部变量。"""
    n_snap = vars_snap.get("n") or {}
    if n_snap.get("type") == "int":
        v = int(n_snap["value"])
        if line < 14 and (v < -1_000_000 or v > 1_000_000):
            return False
    nums_snap = vars_snap.get("nums") or {}
    if nums_snap.get("type") in ("list", "sequence"):
        arr = nums_snap.get("value") or []
        if line < 14 and len(arr) > 128:
            return False
    return True


def _collect_gdb_steps(
    full_out: str,
    *,
    map_line: Any,
) -> list[TraceStepOut]:
    steps: list[TraceStepOut] = []
    prev_snap: dict[str, str] = {}

    segments = re.split(r"(?=\*stopped)", full_out)
    for seg in segments:
        if "line=\"" not in seg:
            continue
        stop_m = re.search(r'line="(\d+)"', seg)
        if not stop_m:
            continue
        abs_line = int(stop_m.group(1))
        if "exited-normally" in seg or "exited normally" in seg.lower():
            break

        vars_snap = _parse_trace_viz_marker(seg)
        if not vars_snap:
            vars_snap = _parse_info_locals(seg)
        mi_line = next((ln for ln in seg.splitlines() if "^done,variables=" in ln), "")
        if mi_line:
            for k, v in _parse_mi_variables_line(mi_line).items():
                if k not in vars_snap:
                    vars_snap[k] = v
        if not vars_snap:
            continue

        line = map_line(abs_line)
        if not _is_plausible_step(vars_snap, line):
            continue

        vars_snap = _sanitize_gdb_vars(vars_snap, line)
        if not vars_snap:
            continue

        changed: list[str] = []
        for k, v in vars_snap.items():
            key = json.dumps(v, sort_keys=True, ensure_ascii=False)
            if prev_snap.get(k) != key:
                changed.append(k)
            prev_snap[k] = key
        steps.append(TraceStepOut(line=line, vars=vars_snap, changed=changed))

    return steps


def _finalize_cpp_steps(
    steps: list[TraceStepOut],
    *,
    user_lines: int,
    empty_msg: str,
    source: str = "",
) -> TraceSummary:
    steps = collapse_consecutive_same_line_steps(steps)
    refine_trace_step_lines(steps, source)
    steps = compress_initialization_phase(steps, source=source)
    steps = filter_meaningful_steps(steps, max_steps=MAX_CPP_TRACE_STEPS)
    if len(steps) < 2:
        return TraceSummary(
            verdict="RE",
            message=empty_msg,
            user_line_count=user_lines,
            steps=[],
        )
    return TraceSummary(
        verdict="OK",
        message="C++ 追踪完成（按你提交的代码逐步执行）",
        user_line_count=user_lines,
        steps=steps,
        result_preview=None,
    )


def _gdb_stdio_commands(input_path: str, *, max_steps: int, bootstrap: list[str]) -> list[str]:
    inp = input_path
    cmds = [
        *bootstrap,
        "-break-insert main",
        f'-interpreter-exec console "run < {inp}"',
    ]
    for _ in range(max_steps):
        cmds.extend([*_gdb_step_capture_commands(), "-exec-next"])
    cmds.append("-gdb-exit")
    return cmds


def _gdb_leetcode_commands(breakpoint: str, *, max_steps: int, bootstrap: list[str]) -> list[str]:
    cmds = [
        *bootstrap,
        f"-break-insert {breakpoint}",
        "-exec-run",
    ]
    for _ in range(max_steps):
        cmds.extend([*_gdb_step_capture_commands(), "-exec-next"])
    cmds.append("-gdb-exit")
    return cmds


def _user_line_from_abs(abs_line: int, user_line_count: int, src: str) -> int:
    """将 main.cpp 绝对行号映射到用户代码相对行（粗略：跳过 include/helpers 后的 Solution 区）。"""
    lines = src.splitlines()
    user_start = 0
    for i, ln in enumerate(lines):
        if re.search(r"\bclass\s+Solution\b", ln):
            user_start = i
            break
    rel = abs_line - user_start
    if 1 <= rel <= user_line_count:
        return rel
    return max(1, min(user_line_count, rel))


def run_trace_cpp(
    user_code: str,
    *,
    entry: dict[str, Any],
    case: dict[str, Any],
    time_limit_ms: int = 5000,
) -> TraceSummary:
    from services.oj.static_audit import audit_user_code, trace_summary_rejected

    audit = audit_user_code(user_code, language="cpp")
    if not audit.passed:
        return trace_summary_rejected(audit)

    gpp = _find_gpp()
    if not gpp:
        return TraceSummary(
            verdict="CE",
            message="未找到 g++，无法编译 C++ 追踪",
            user_line_count=len(user_code.strip().splitlines()) or 1,
            steps=[],
        )
    gdb = _find_gdb()
    if not gdb:
        return TraceSummary(
            verdict="CE",
            message="未找到 gdb。请安装 MinGW 并确保 gdb 在 PATH 中（C++ 可视化调试依赖 GDB）",
            user_line_count=len(user_code.strip().splitlines()) or 1,
            steps=[],
        )

    class_name = entry.get("class") or "Solution"
    method_name = entry["method"]
    args = case.get("args", [])
    expected = case.get("expected")
    user_lines = len(user_code.strip().splitlines()) or 1

    try:
        check_cpp_security(user_code)
    except CppSecurityViolation:
        return TraceSummary(
            verdict="CE",
            message=CPP_SECURITY_MESSAGE,
            user_line_count=user_lines,
            steps=[],
        )

    try:
        src = _build_cpp_source(
            user_code,
            class_name=class_name,
            method_name=method_name,
            args=args,
            entry=entry,
            expected=expected,
            in_place_arg=case.get("in_place_arg"),
        )
    except TypeError as e:
        return TraceSummary(verdict="RE", message=str(e), user_line_count=user_lines, steps=[])

    timeout_s = _trace_subprocess_timeout(time_limit_ms)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        cpp_file = tmp_path / "main.cpp"
        exe_file = tmp_path / "main.exe"
        cpp_file.write_text(src, encoding="utf-8")

        compile_timeout = cpp_compile_timeout_seconds()
        try:
            compile = subprocess.run(
                [gpp, "-std=c++17", "-g", "-O0", str(cpp_file), "-o", str(exe_file)],
                capture_output=True,
                text=True,
                errors="replace",
                timeout=compile_timeout,
            )
        except subprocess.TimeoutExpired:
            return TraceSummary(
                verdict="CE",
                message=_compile_timeout_message(compile_timeout),
                user_line_count=user_lines,
                steps=[],
            )
        except OSError as exc:
            return TraceSummary(
                verdict="CE",
                message=f"无法启动 C++ 编译器 {gpp}: {exc}"[:800],
                user_line_count=user_lines,
                steps=[],
            )
        if compile.returncode != 0:
            err = (compile.stderr or compile.stdout or "编译失败").strip()
            return TraceSummary(verdict="CE", message=err[:800], user_line_count=user_lines, steps=[])

        bp = f"{class_name}::{method_name}"
        gdb_script = _gdb_script_path(tmp_path)
        bootstrap = _gdb_bootstrap_commands(gdb_script)
        gdb_cmds = _gdb_leetcode_commands(bp, max_steps=MAX_CPP_TRACE_STEPS, bootstrap=bootstrap)

        ret, full_out = _run_gdb_mi(exe_file, gdb_cmds, timeout_s)
        if ret == 124:
            return TraceSummary(
                verdict="TLE",
                message=(
                    "动态追踪超时：程序可能在死循环中运行。"
                    " 请结合 ASTAnalyzer 静态提示检查 while/for 内 left/right 等是否更新。"
                ),
                user_line_count=user_lines,
                steps=[],
            )

        steps = _collect_gdb_steps(
            full_out,
            map_line=lambda abs_line: _user_line_from_abs(abs_line, user_lines, src),
        )

        if not steps:
            return TraceSummary(
                verdict="RE",
                message="GDB 未采集到有效步骤，请确认 Solution 方法名正确且 gdb 可调试",
                user_line_count=user_lines,
                steps=[],
            )

        return _finalize_cpp_steps(
            steps,
            user_lines=user_lines,
            empty_msg="未捕获到有效执行步骤：请编写解题逻辑后再试（当前可能仅为模板）",
            source=src,
        )


def run_trace_cpp_stdio(
    user_code: str,
    *,
    case: dict[str, Any],
    time_limit_ms: int = 5000,
) -> TraceSummary:
    """洛谷风格：对用户 main 程序 GDB 单步追踪。"""
    from services.oj.static_audit import audit_user_code, trace_summary_rejected
    from services.oj.stdio_io import case_input_text

    audit = audit_user_code(user_code, language="cpp")
    if not audit.passed:
        return trace_summary_rejected(audit)

    gpp = _find_gpp()
    if not gpp:
        return TraceSummary(
            verdict="CE",
            message="未找到 g++，无法编译 C++ 追踪",
            user_line_count=len(user_code.strip().splitlines()) or 1,
            steps=[],
        )
    if not gdb_available():
        return TraceSummary(
            verdict="CE",
            message="未找到 gdb。请安装 MinGW 并确保 gdb 在 PATH 中",
            user_line_count=len(user_code.strip().splitlines()) or 1,
            steps=[],
        )

    stdin = case_input_text(case)
    user_lines = len(user_code.strip().splitlines()) or 1
    timeout_s = _trace_subprocess_timeout(time_limit_ms)

    try:
        check_cpp_security(user_code)
    except CppSecurityViolation:
        return TraceSummary(
            verdict="CE",
            message=CPP_SECURITY_MESSAGE,
            user_line_count=user_lines,
            steps=[],
        )

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        cpp_file = tmp_path / "main.cpp"
        exe_file = tmp_path / "main.exe"
        input_file = tmp_path / "input.txt"
        cpp_file.write_text(user_code.strip(), encoding="utf-8")
        input_file.write_text(stdin, encoding="utf-8")

        compile_timeout = cpp_compile_timeout_seconds()
        try:
            compile = subprocess.run(
                [gpp, "-std=c++17", "-g", "-O0", str(cpp_file), "-o", str(exe_file)],
                capture_output=True,
                text=True,
                errors="replace",
                timeout=compile_timeout,
            )
        except subprocess.TimeoutExpired:
            return TraceSummary(
                verdict="CE",
                message=_compile_timeout_message(compile_timeout),
                user_line_count=user_lines,
                steps=[],
            )
        except OSError as exc:
            return TraceSummary(
                verdict="CE",
                message=f"无法启动 C++ 编译器 {gpp}: {exc}"[:800],
                user_line_count=user_lines,
                steps=[],
            )
        if compile.returncode != 0:
            err = (compile.stderr or compile.stdout or "编译失败").strip()
            return TraceSummary(verdict="CE", message=err[:800], user_line_count=user_lines, steps=[])

        inp = input_file.as_posix()
        gdb_script = _gdb_script_path(tmp_path)
        bootstrap = _gdb_bootstrap_commands(gdb_script)
        gdb_cmds = _gdb_stdio_commands(inp, max_steps=MAX_CPP_TRACE_STEPS, bootstrap=bootstrap)

        ret, full_out = _run_gdb_mi(exe_file, gdb_cmds, timeout_s)
        if ret == 124:
            return TraceSummary(
                verdict="TLE",
                message=(
                    "动态追踪超时：疑似死循环。建议检查 while/for 循环变量是否推进，"
                    "或先根据静态分析报告修正后再运行可视化调试。"
                ),
                user_line_count=user_lines,
                steps=[],
            )

        steps = _collect_gdb_steps(
            full_out,
            map_line=lambda abs_line: _user_line_stdio(abs_line, user_lines),
        )

        if not steps:
            return TraceSummary(
                verdict="RE",
                message="GDB 未采集到有效步骤，请确认已编写 main 且逻辑可运行",
                user_line_count=user_lines,
                steps=[],
            )

        return _finalize_cpp_steps(
            steps,
            user_lines=user_lines,
            empty_msg="未捕获到有效执行步骤：请编写解题逻辑后再试",
            source=user_code.strip(),
        )
