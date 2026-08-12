"""Python 执行追踪：按行记录变量快照，供前端动画回放。"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from services.oj.runner import LIST_NODE_HELPERS, _detect_helpers
from services.oj.trace_steps_filter import compress_initialization_phase, filter_meaningful_steps
from services.oj.trace_line_refine import refine_trace_step_lines
from utils import python_exec_args

TraceVerdict = Literal["OK", "RE", "TLE", "CE"]
MAX_TRACE_STEPS = 200

_TRACE_SERIALIZE_PATH = Path(__file__).with_name("trace_serialize.py")


def _trace_engine_tail() -> str:
    return textwrap.dedent(
        f"""
        TRACE_STEPS = []
        _PREV_SNAP = {{}}
        USER_FILENAME = "<user>"
        MAX_TRACE_STEPS = {MAX_TRACE_STEPS}

        def _is_tree_node(val):
            return val is not None and hasattr(val, "val") and hasattr(val, "left") and hasattr(val, "right")

        def _collect_vars(frame):
            skip = {{
                "self", "inst", "ListNode", "TreeNode", "Optional", "List",
                "json", "sys", "time", "deque", "_args", "result", "elapsed_ms",
                "TRACE_STEPS", "_PREV_SNAP", "USER_FILENAME", "MAX_TRACE_STEPS",
            }}
            raw = collect_frame_vars(dict(frame.f_locals), skip)
            for k, v in list(raw.items()):
                loc_val = frame.f_locals.get(k)
                if v.get("type") == "other":
                    continue
                if v.get("type") not in ("linked_list", "node_ref", "tree", "tree_node_ref",
                                         "matrix", "matrix_overflow",
                                         "list", "queue", "stack", "dict",
                                         "int", "float", "bool", "str", "none"):
                    raw[k] = {{"type": "other", "value": str(loc_val)[:120]}}
            return raw

        def _snap_key(payload):
            try:
                return json.dumps(payload, sort_keys=True, ensure_ascii=False)
            except TypeError:
                return repr(payload)

        def _trace(frame, event, arg):
            if event != "line":
                return _trace
            if frame.f_code.co_filename != USER_FILENAME:
                return _trace
            if len(TRACE_STEPS) >= MAX_TRACE_STEPS:
                return _trace
            lineno = frame.f_lineno
            vars_snap = _collect_vars(frame)
            changed = [k for k, v in vars_snap.items() if _PREV_SNAP.get(k) != _snap_key(v)]
            TRACE_STEPS.append({{"line": lineno, "vars": vars_snap, "changed": changed}})
            for k, v in vars_snap.items():
                _PREV_SNAP[k] = _snap_key(v)
            return _trace
        """
    )


@dataclass
class TraceStepOut:
    line: int
    vars: dict[str, Any]
    changed: list[str]


@dataclass
class TraceSummary:
    verdict: TraceVerdict
    message: str
    user_line_count: int
    steps: list[TraceStepOut]
    result_preview: str | None = None
    static_rejection: dict[str, Any] | None = None


def _build_trace_script(
    user_code: str,
    *,
    entry: dict[str, Any],
    class_name: str,
    method_name: str,
    args: list[Any],
    needs_list_node: bool,
    needs_tree_node: bool,
) -> str:
    args_json = json.dumps(args, ensure_ascii=False)
    list_idx = entry.get("list_arg_indices") or []
    tree_idx = entry.get("tree_arg_indices") or []
    helpers = (
        LIST_NODE_HELPERS
        if (needs_list_node or needs_tree_node or list_idx or tree_idx)
        else ""
    )
    convert_lines = []
    for i in list_idx:
        convert_lines.append(
            f"if isinstance(_args[{i}], list): _args[{i}] = _g['list_to_nodes'](_args[{i}])"
        )
    for i in tree_idx:
        convert_lines.append(
            f"if isinstance(_args[{i}], list): _args[{i}] = _g['list_to_tree'](_args[{i}])"
        )
    convert_block = "\n".join(convert_lines) if convert_lines else "pass"

    user_src = user_code.strip()
    engine = _trace_engine_tail().strip()
    runner = (
        "import json\n"
        "import sys\n"
        "import time\n"
        "from trace_serialize import collect_frame_vars, is_list_node\n\n"
        f"{engine}\n\n"
        f"_args = json.loads({json.dumps(args_json)})\n"
        "_g = {}\n"
        "_ns = {}\n"
        f"exec({json.dumps(helpers)}, _g)\n"
        f"exec({json.dumps(helpers)}, _ns)\n"
        f"{convert_block}\n"
        "sys.settrace(_trace)\n"
        "try:\n"
        f"    exec(compile({json.dumps(user_src)}, USER_FILENAME, 'exec'), _ns)\n"
        f"    _cls = _ns.get({json.dumps(class_name)})\n"
        f"    if _cls is None:\n"
        f"        raise RuntimeError('未找到 class {class_name}')\n"
        "    inst = _cls()\n"
        "    t0 = time.perf_counter()\n"
        f"    result = inst.{method_name}(*_args)\n"
        "finally:\n"
        "    sys.settrace(None)\n"
        "elapsed_ms = int((time.perf_counter() - t0) * 1000)\n"
        "_ser = _ns.get('serialize_for_json')\n"
        "_out = _ser(result) if _ser else result\n"
        "print(json.dumps({\n"
        '    "ok": True,\n'
        '    "steps": TRACE_STEPS,\n'
        f'    "user_line_count": len({json.dumps(user_src)}.splitlines()),\n'
        '    "result": _out,\n'
        '    "ms": elapsed_ms,\n'
        "}, ensure_ascii=False))\n"
    )
    return runner


def _build_trace_stdio_script(user_code: str, *, stdin: str) -> str:
    """洛谷风格：追踪用户完整程序（stdin 注入，捕获 stdout）。"""
    user_src = user_code.strip()
    has_main_guard = "if __name__" in user_src
    has_main_fn = bool(re.search(r"def\s+main\s*\(", user_src))
    engine = _trace_engine_tail().strip()
    runner = (
        "import json\n"
        "import sys\n"
        "import io\n"
        "import time\n"
        "from trace_serialize import collect_frame_vars, is_list_node\n\n"
        f"{engine}\n\n"
        f"_stdin = {json.dumps(stdin)}\n"
        f"_HAS_MAIN_GUARD = {repr(has_main_guard)}\n"
        f"_HAS_MAIN_FN = {repr(has_main_fn)}\n"
        "sys.stdin = io.StringIO(_stdin)\n"
        "_stdout_buf = io.StringIO()\n"
        "_real_stdout = sys.stdout\n"
        "sys.stdout = _stdout_buf\n"
        "sys.settrace(_trace)\n"
        "_ns = {'__name__': '__main__'}\n"
        "t0 = time.perf_counter()\n"
        "try:\n"
        f"    exec(compile({json.dumps(user_src)}, USER_FILENAME, 'exec'), _ns)\n"
        "    if _HAS_MAIN_FN and not _HAS_MAIN_GUARD and callable(_ns.get('main')):\n"
        "        _ns['main']()\n"
        "finally:\n"
        "    sys.settrace(None)\n"
        "    sys.stdout = _real_stdout\n"
        "elapsed_ms = int((time.perf_counter() - t0) * 1000)\n"
        "_out_text = _stdout_buf.getvalue()\n"
        "print(json.dumps({\n"
        '    "ok": True,\n'
        '    "steps": TRACE_STEPS,\n'
        f'    "user_line_count": len({json.dumps(user_src)}.splitlines()),\n'
        '    "result": _out_text,\n'
        '    "ms": elapsed_ms,\n'
        "}, ensure_ascii=False))\n"
    )
    return runner


def _steps_from_payload(
    raw_steps: list[dict[str, Any]],
    *,
    user_lines: int,
    min_steps: int = 2,
    source: str = "",
) -> tuple[list[TraceStepOut], str | None]:
    """解析子进程 JSON steps 并过滤；步数过少时返回错误说明。"""
    steps = [
        TraceStepOut(
            line=int(s.get("line", 0)),
            vars=s.get("vars") or {},
            changed=list(s.get("changed") or []),
        )
        for s in raw_steps
    ]
    refine_trace_step_lines(steps, source)
    steps = compress_initialization_phase(steps, source=source)
    steps = filter_meaningful_steps(steps, max_steps=MAX_TRACE_STEPS)
    if len(steps) < min_steps:
        return (
            [],
            "未捕获到有效执行步骤：请编写解题逻辑后再试（当前可能仅为模板或 pass）",
        )
    for s in steps:
        if s.line < 1 or s.line > user_lines:
            s.line = max(1, min(user_lines, s.line))
    return steps, None


def run_trace_stdio(
    user_code: str,
    *,
    case: dict[str, Any],
    time_limit_ms: int = 3000,
    language: str = "python",
) -> TraceSummary:
    """洛谷 stdin/stdout：对首个样例追踪用户 main 程序。"""
    from services.oj.static_audit import audit_user_code, trace_summary_rejected
    from services.oj.stdio_io import case_input_text

    audit = audit_user_code(user_code, language=language)
    if not audit.passed:
        return trace_summary_rejected(audit)

    stdin = case_input_text(case)

    user_lines = len(user_code.strip().splitlines()) or 1

    try:
        compile(user_code.strip(), "<user>", "exec")
    except SyntaxError as e:
        return TraceSummary(
            verdict="CE",
            message=str(e),
            user_line_count=user_lines,
            steps=[],
        )

    script = _build_trace_stdio_script(user_code, stdin=stdin)

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(script)
        path = Path(f.name)
    shutil.copy2(_TRACE_SERIALIZE_PATH, path.parent / "trace_serialize.py")

    try:
        try:
            proc = subprocess.run(
                python_exec_args(str(path)),
                capture_output=True,
                text=True,
                timeout=max(1, time_limit_ms / 1000),
                cwd=str(path.parent),
            )
        except subprocess.TimeoutExpired:
            return TraceSummary(
                verdict="TLE",
                message=f"追踪超时（>{time_limit_ms}ms）",
                user_line_count=user_lines,
                steps=[],
            )
    finally:
        path.unlink(missing_ok=True)
        (path.parent / "trace_serialize.py").unlink(missing_ok=True)

    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "运行错误").strip()
        return TraceSummary(
            verdict="RE",
            message=err[:800],
            user_line_count=user_lines,
            steps=[],
        )

    stdout = proc.stdout.strip()
    try:
        payload = json.loads(stdout.splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return TraceSummary(
            verdict="RE",
            message=f"无法解析追踪输出: {stdout[:400]}",
            user_line_count=user_lines,
            steps=[],
        )

    raw_steps = payload.get("steps") or []
    steps, err = _steps_from_payload(raw_steps, user_lines=user_lines, source=user_code.strip())
    if err:
        return TraceSummary(
            verdict="RE",
            message=err,
            user_line_count=user_lines,
            steps=[],
            result_preview=str(payload.get("result") or "")[:300],
        )

    result_preview = str(payload.get("result") or "")[:300]

    return TraceSummary(
        verdict="OK",
        message="追踪完成（按你提交的代码逐步执行）",
        user_line_count=int(payload.get("user_line_count") or user_lines),
        steps=steps,
        result_preview=result_preview,
    )


def run_trace(
    user_code: str,
    *,
    entry: dict[str, Any],
    case: dict[str, Any],
    time_limit_ms: int = 3000,
    language: str = "python",
) -> TraceSummary:
    """对首个样例运行并返回逐步追踪（仅 Python 力扣风格）。"""
    from services.oj.static_audit import audit_user_code, trace_summary_rejected

    audit = audit_user_code(user_code, language=language)
    if not audit.passed:
        return trace_summary_rejected(audit)

    class_name = entry.get("class") or "Solution"
    method_name = entry["method"]
    args = case.get("args", [])
    entry_run = {**entry}
    needs_list, needs_tree = _detect_helpers([case], entry_run)

    user_lines = len(user_code.strip().splitlines()) or 1

    try:
        compile(user_code.strip(), "<user>", "exec")
    except SyntaxError as e:
        return TraceSummary(
            verdict="CE",
            message=str(e),
            user_line_count=user_lines,
            steps=[],
        )

    script = _build_trace_script(
        user_code,
        entry=entry_run,
        class_name=class_name,
        method_name=method_name,
        args=args,
        needs_list_node=needs_list,
        needs_tree_node=needs_tree,
    )

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(script)
        path = Path(f.name)
    shutil.copy2(_TRACE_SERIALIZE_PATH, path.parent / "trace_serialize.py")

    try:
        proc = subprocess.run(
            python_exec_args(str(path)),
            capture_output=True,
            text=True,
            timeout=max(1, time_limit_ms / 1000),
            cwd=str(path.parent),
        )
    except subprocess.TimeoutExpired:
        path.unlink(missing_ok=True)
        (path.parent / "trace_serialize.py").unlink(missing_ok=True)
        return TraceSummary(
            verdict="TLE",
            message=f"追踪超时（>{time_limit_ms}ms）",
            user_line_count=user_lines,
            steps=[],
        )

    path.unlink(missing_ok=True)
    (path.parent / "trace_serialize.py").unlink(missing_ok=True)

    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "运行错误").strip()
        return TraceSummary(
            verdict="RE",
            message=err[:800],
            user_line_count=user_lines,
            steps=[],
        )

    stdout = proc.stdout.strip()
    try:
        payload = json.loads(stdout.splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return TraceSummary(
            verdict="RE",
            message=f"无法解析追踪输出: {stdout[:400]}",
            user_line_count=user_lines,
            steps=[],
        )

    raw_steps = payload.get("steps") or []
    steps, err = _steps_from_payload(raw_steps, user_lines=user_lines, source=user_code.strip())
    if err:
        return TraceSummary(
            verdict="RE",
            message=err,
            user_line_count=user_lines,
            steps=[],
        )

    try:
        result_preview = json.dumps(payload.get("result"), ensure_ascii=False)[:300]
    except TypeError:
        result_preview = str(payload.get("result"))[:300]

    return TraceSummary(
        verdict="OK",
        message="追踪完成（按你提交的代码逐步执行）",
        user_line_count=int(payload.get("user_line_count") or user_lines),
        steps=steps,
        result_preview=result_preview,
    )
