from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from services.oj.compare import values_equal

Verdict = Literal["AC", "WA", "TLE", "RE", "CE"]

LIST_NODE_HELPERS = textwrap.dedent(
    """
    from typing import Optional, List

    class ListNode:
        def __init__(self, val=0, next=None):
            self.val = val
            self.next = next

    def list_to_nodes(arr):
        if not arr:
            return None
        head = ListNode(arr[0])
        cur = head
        for x in arr[1:]:
            cur.next = ListNode(x)
            cur = cur.next
        return head

    def build_intersect_heads(prefix_a, prefix_b, common):
        tail = list_to_nodes(common) if common else None

        def attach(prefix, tail_node):
            if not prefix:
                return tail_node
            head = list_to_nodes(prefix)
            cur = head
            while cur.next:
                cur = cur.next
            cur.next = tail_node
            return head

        return attach(prefix_a, tail), attach(prefix_b, tail)

    def serialize_for_json(val):
        if val is None:
            return None
        if type(val).__name__ == "ListNode":
            out = []
            cur = val
            n = 0
            while cur is not None and n < 10000:
                out.append(cur.val)
                cur = cur.next
                n += 1
            return out
        if isinstance(val, (bool, int, float, str)):
            return val
        if isinstance(val, list):
            return [serialize_for_json(v) for v in val]
        return val

    class TreeNode:
        def __init__(self, val=0, left=None, right=None):
            self.val = val
            self.left = left
            self.right = right

    def list_to_tree(arr):
        if not arr:
            return None
        from collections import deque
        nodes = [TreeNode(v) if v is not None else None for v in arr]
        root = nodes[0]
        q = deque([root])
        i = 1
        while q and i < len(nodes):
            node = q.popleft()
            if node is None:
                continue
            if i < len(nodes):
                node.left = nodes[i]
                i += 1
            if i < len(nodes):
                node.right = nodes[i]
                i += 1
            if node.left is not None:
                q.append(node.left)
            if node.right is not None:
                q.append(node.right)
        return root
    """
)


@dataclass
class CaseResult:
    index: int
    verdict: Verdict
    message: str
    input_preview: str
    expected_preview: str
    actual_preview: str | None
    runtime_ms: int | None = None


@dataclass
class RunSummary:
    verdict: Verdict
    passed: int
    total: int
    cases: list[CaseResult]
    compile_error: str | None = None


def _preview_args(args: list[Any]) -> str:
    try:
        s = json.dumps(args, ensure_ascii=False)
    except TypeError:
        s = repr(args)
    return s[:500]


def _preview_value(val: Any) -> str:
    try:
        s = json.dumps(val, ensure_ascii=False)
    except TypeError:
        s = repr(val)
    return s[:500]


def _build_script(
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
    helpers = ""
    if needs_list_node or needs_tree_node:
        helpers = LIST_NODE_HELPERS

    list_idx = entry.get("list_arg_indices") or []
    tree_idx = entry.get("tree_arg_indices") or []
    convert_lines = []
    for i in list_idx:
        convert_lines.append(
            f"if isinstance(_args[{i}], list): _args[{i}] = list_to_nodes(_args[{i}])"
        )
    for i in tree_idx:
        convert_lines.append(
            f"if isinstance(_args[{i}], list): _args[{i}] = list_to_tree(_args[{i}])"
        )
    convert_block = "\n        ".join(convert_lines) if convert_lines else "pass"
    intersect_block = "\n        ".join(
        [
            "if len(_args) == 1 and isinstance(_args[0], dict) and 'a' in _args[0] and 'b' in _args[0]:",
            "    _spec = _args[0]",
            "    _a, _b = build_intersect_heads(_spec.get('a') or [], _spec.get('b') or [], _spec.get('common') or [])",
            "    _args = [_a, _b]",
        ]
    )

    invoke = f"result = inst.{method_name}(*_args)"
    in_place_idx = entry.get("_in_place_arg")
    in_place_line = ""
    if in_place_idx is not None:
        in_place_line = f', "in_place": _args[{in_place_idx}]'

    tail = textwrap.dedent(
        f"""
        import json
        import time

        _args = json.loads({json.dumps(args_json)})
        {intersect_block}
        {convert_block}
        inst = {class_name}()
        t0 = time.perf_counter()
        {invoke}
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        print(json.dumps({{"ok": True, "result": serialize_for_json(result){in_place_line}, "ms": elapsed_ms}}))
        """
    )
    return f"{helpers}\n{user_code.strip()}\n{tail}"


def _detect_helpers(test_cases: list[dict[str, Any]], entry: dict[str, str]) -> tuple[bool, bool]:
    """根据题目 slug / 方法粗略判断是否需要链表/树辅助（可由题目元数据覆盖）。"""
    needs_list = entry.get("needs_list_node", False)
    needs_tree = entry.get("needs_tree_node", False)
    slug = entry.get("_slug", "")
    if "linked-list" in slug or "list-cycle" in slug or slug in {
        "reverse-linked-list",
        "remove-nth-node-from-end-of-list",
        "middle-of-the-linked-list",
        "merge-two-sorted-lists",
        "intersection-of-two-linked-lists",
        "palindrome-linked-list",
        "remove-linked-list-elements",
        "swap-nodes-in-pairs",
        "design-linked-list",
    }:
        needs_list = True
    if "binary-tree" in slug or "tree" in slug or slug in {
        "invert-binary-tree",
        "symmetric-tree",
        "maximum-depth-of-binary-tree",
        "binary-tree-level-order-traversal",
    }:
        needs_tree = True
    return bool(needs_list), bool(needs_tree)


def run_cases(
    user_code: str,
    *,
    entry: dict[str, Any],
    cases: list[dict[str, Any]],
    time_limit_ms: int = 3000,
    order_insensitive: bool = False,
) -> RunSummary:
    class_name = entry.get("class") or "Solution"
    method_name = entry["method"]
    entry_with_slug = {**entry}
    needs_list, needs_tree = _detect_helpers(cases, entry_with_slug)

    results: list[CaseResult] = []
    passed = 0

    for idx, case in enumerate(cases):
        args = case.get("args", [])
        expected = case["expected"]
        entry_run = {**entry_with_slug, "_in_place_arg": case.get("in_place_arg")}
        script = _build_script(
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

        try:
            proc = subprocess.run(
                [sys.executable, str(path)],
                capture_output=True,
                text=True,
                timeout=max(1, time_limit_ms / 1000),
                cwd=str(path.parent),
            )
        except subprocess.TimeoutExpired:
            results.append(
                CaseResult(
                    index=idx,
                    verdict="TLE",
                    message=f"超出时间限制 {time_limit_ms}ms",
                    input_preview=_preview_args(args),
                    expected_preview=_preview_value(expected),
                    actual_preview=None,
                )
            )
            path.unlink(missing_ok=True)
            return RunSummary(verdict="TLE", passed=passed, total=len(cases), cases=results)

        path.unlink(missing_ok=True)

        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "运行错误").strip()
            results.append(
                CaseResult(
                    index=idx,
                    verdict="RE",
                    message=err[:800],
                    input_preview=_preview_args(args),
                    expected_preview=_preview_value(expected),
                    actual_preview=None,
                )
            )
            return RunSummary(verdict="RE", passed=passed, total=len(cases), cases=results)

        stdout = proc.stdout.strip()
        try:
            payload = json.loads(stdout.splitlines()[-1])
            actual = payload.get("result")
            if case.get("in_place_arg") is not None and "in_place" in payload:
                actual = payload.get("in_place")
            runtime_ms = payload.get("ms")
        except (json.JSONDecodeError, IndexError):
            results.append(
                CaseResult(
                    index=idx,
                    verdict="RE",
                    message=f"无法解析输出: {stdout[:400]}",
                    input_preview=_preview_args(args),
                    expected_preview=_preview_value(expected),
                    actual_preview=stdout[:400] or None,
                )
            )
            return RunSummary(verdict="RE", passed=passed, total=len(cases), cases=results)

        if values_equal(actual, expected, order_insensitive=order_insensitive):
            passed += 1
            results.append(
                CaseResult(
                    index=idx,
                    verdict="AC",
                    message="通过",
                    input_preview=_preview_args(args),
                    expected_preview=_preview_value(expected),
                    actual_preview=_preview_value(actual),
                    runtime_ms=runtime_ms,
                )
            )
        else:
            results.append(
                CaseResult(
                    index=idx,
                    verdict="WA",
                    message="答案错误",
                    input_preview=_preview_args(args),
                    expected_preview=_preview_value(expected),
                    actual_preview=_preview_value(actual),
                    runtime_ms=runtime_ms,
                )
            )
            return RunSummary(verdict="WA", passed=passed, total=len(cases), cases=results)

    return RunSummary(verdict="AC", passed=passed, total=len(cases), cases=results)
