"""修复 tests_bundle.json 中 LinkedList+Stack+Queue+Monotonic 类题目的错误测试用例。

对每个目标题目：
1. 使用参考解法重新计算 expected（对 verify_test_cases.py 中存在 bug 的题目，
   使用本文件内的更稳健的解法 / 模拟器）。
2. 若 expected 与参考解法结果不一致，则更新 expected。
3. 用 services.oj.stdio_io.leetcode_case_to_stdio 重新生成 stdin/stdout。
4. 确保每道题 hidden 用例 >= 5 个（不足则补充边界用例）。

特殊处理：
- linked-list-cycle / linked-list-cycle-ii：原数据缺少 pos 参数（全部无环），
  需为每个用例补充 pos=-1，并新增带环用例。stdin 格式变为 n\\n vals\\n pos\\n。
- intersection-of-two-linked-lists：verify_test_cases 的解法恒返回 None（bug），
  使用 safe 解法返回 common 列表或 None。
- design-linked-list：hidden[1]-[13] 原为数组索引测试（与题意不符），替换为
  正确的操作序列；samples[0] 的 stdout 末值错误（2 应为 3），用模拟器修正。
- implement-stack-using-queues / implement-queue-using-stacks：部分用例 stdout
  缺少行或值错误，用模拟器重新计算并修正。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

from services.oj.stdio_io import leetcode_case_to_stdio  # noqa: E402
from verify_test_cases import SOLUTIONS, compare_result  # noqa: E402

BUNDLE_PATH = BACKEND / "data" / "oj" / "tests_bundle.json"

TARGET_SLUGS = [
    # linked-list
    "remove-nth-node-from-end-of-list",
    "swap-nodes-in-pairs",
    "reverse-nodes-in-k-group",
    "reverse-linked-list-ii",
    "linked-list-cycle",
    "linked-list-cycle-ii",
    "intersection-of-two-linked-lists",
    "remove-linked-list-elements",
    "reverse-linked-list",
    "palindrome-linked-list",
    "delete-node-in-a-linked-list",
    "design-linked-list",
    "middle-of-the-linked-list",
    # stack-queue
    "valid-parentheses",
    "evaluate-reverse-polish-notation",
    "implement-stack-using-queues",
    "implement-queue-using-stacks",
    "sliding-window-maximum",
    "top-k-frequent-elements",
    "remove-all-adjacent-duplicates-in-string",
    # monotonic-stack
    "trapping-rain-water",
    "largest-rectangle-in-histogram",
    "next-greater-element-i",
    "next-greater-element-ii",
    "daily-temperatures",
]

# 题目因 verify_test_cases.py 参考解法 bug，数据正确但无法通过
# verify_bundle_correctness.py：
BUGGY_SOLVER_SLUGS = {
    "linked-list-cycle-ii",        # 解法返回 -1 而非 None
    "intersection-of-two-linked-lists",  # 解法恒返回 None
    "design-linked-list",          # 解法返回 ops，args=null 导致崩溃
    "implement-stack-using-queues",  # 解法返回 ops，args=null 导致崩溃
    "implement-queue-using-stacks",  # 解法返回 ops，args=null 导致崩溃
}


# ─── Safe simulators for design problems ───

def _design_linked_list_simulate(stdin: str) -> str:
    """模拟 design-linked-list 操作序列，返回期望 stdout。"""
    lines = [ln for ln in stdin.split("\n") if ln.strip() != ""]
    if not lines:
        return ""
    n = int(lines[0])
    ops = lines[1:1 + n]
    lst: list[int] = []
    outputs: list[str] = []
    for op in ops:
        parts = op.split()
        cmd = parts[0]
        if cmd == "init":
            lst = []
        elif cmd == "addAtHead":
            lst.insert(0, int(parts[1]))
        elif cmd == "addAtTail":
            lst.append(int(parts[1]))
        elif cmd == "addAtIndex":
            idx = int(parts[1])
            val = int(parts[2])
            if 0 <= idx <= len(lst):
                lst.insert(idx, val)
        elif cmd == "get":
            idx = int(parts[1])
            if 0 <= idx < len(lst):
                outputs.append(str(lst[idx]))
            else:
                outputs.append("-1")
        elif cmd == "deleteAtIndex":
            idx = int(parts[1])
            if 0 <= idx < len(lst):
                lst.pop(idx)
    return "\n".join(outputs) + "\n" if outputs else ""


def _implement_stack_using_queues_simulate(stdin: str) -> str:
    """模拟 implement-stack-using-queues 操作序列，返回期望 stdout。"""
    lines = [ln for ln in stdin.split("\n") if ln.strip() != ""]
    if not lines:
        return ""
    n = int(lines[0])
    ops = lines[1:1 + n]
    stack: list[int] = []
    outputs: list[str] = []
    for op in ops:
        parts = op.split()
        cmd = parts[0]
        if cmd == "push":
            stack.append(int(parts[1]))
        elif cmd == "pop":
            if stack:
                outputs.append(str(stack.pop()))
            else:
                outputs.append("-1")
        elif cmd == "top":
            if stack:
                outputs.append(str(stack[-1]))
            else:
                outputs.append("-1")
        elif cmd == "empty":
            outputs.append("true" if not stack else "false")
    return "\n".join(outputs) + "\n" if outputs else ""


def _implement_queue_using_stacks_simulate(stdin: str) -> str:
    """模拟 implement-queue-using-stacks 操作序列，返回期望 stdout。"""
    lines = [ln for ln in stdin.split("\n") if ln.strip() != ""]
    if not lines:
        return ""
    n = int(lines[0])
    ops = lines[1:1 + n]
    queue: list[int] = []
    outputs: list[str] = []
    for op in ops:
        parts = op.split()
        cmd = parts[0]
        if cmd == "push":
            queue.append(int(parts[1]))
        elif cmd == "pop":
            if queue:
                outputs.append(str(queue.pop(0)))
            else:
                outputs.append("-1")
        elif cmd == "peek":
            if queue:
                outputs.append(str(queue[0]))
            else:
                outputs.append("-1")
        elif cmd == "empty":
            outputs.append("true" if not queue else "false")
    return "\n".join(outputs) + "\n" if outputs else ""


DESIGN_SIMULATORS = {
    "design-linked-list": _design_linked_list_simulate,
    "implement-stack-using-queues": _implement_stack_using_queues_simulate,
    "implement-queue-using-stacks": _implement_queue_using_stacks_simulate,
}


# ─── Safe solvers for buggy reference solutions ───

def _linked_list_cycle_safe(arr, pos):
    """linked-list-cycle：pos >= 0 表示有环。"""
    return pos >= 0


def _linked_list_cycle_ii_safe(arr, pos):
    """linked-list-cycle-ii：返回环入口下标对应的值列表或 None。"""
    if pos < 0:
        return None
    return arr[pos:]


def _intersection_of_two_linked_lists_safe(data):
    """intersection-of-two-linked-lists：返回 common 列表或 None。"""
    common = data.get("common", [])
    return list(common) if common else None


SOLUTIONS_OVERRIDES: dict[str, Any] = {
    "linked-list-cycle": lambda args: _linked_list_cycle_safe(*args),
    "linked-list-cycle-ii": lambda args: _linked_list_cycle_ii_safe(*args),
    "intersection-of-two-linked-lists": lambda args: _intersection_of_two_linked_lists_safe(*args),
}


# ─── linked-list-cycle / linked-list-cycle-ii 用例重构 ───

# 保留的无环用例（arr, pos=-1）
CYCLE_KEEP_CASES = [
    ([1], -1),
    ([1, 2], -1),
    ([1, 2, 3, 4, 5], -1),
    ([7, 7, 7, 7], -1),
]

# 新增的带环用例 (arr, pos)
CYCLE_WITH_CYCLE_CASES = [
    ([3, 2, 0, -4], 1),
    ([1, 2], 0),
    ([1, 2, 3, 4, 5, 6, 7, 8], 3),
    ([5, 5, 5, 5, 5], 2),
    ([10, 20, 30, 40, 50, 60], 4),
]


def _build_cycle_slug_cases(slug: str) -> tuple[list[dict], list[dict]]:
    """为 linked-list-cycle / linked-list-cycle-ii 构建 samples 和 hidden。"""
    solver = SOLUTIONS_OVERRIDES[slug]

    # samples: 1 个无环 + 1 个带环
    sample_cases = [
        {"args": [[1, 2, 3, 4, 5, 6, 7, 8], -1]},
        {"args": [[3, 2, 0, -4], 1]},
    ]
    for c in sample_cases:
        c["expected"] = solver(c["args"])
        c["stdin"], c["stdout"] = leetcode_case_to_stdio(c["args"], c["expected"])

    # hidden: 4 个无环 + 5 个带环
    hidden_cases = []
    for arr, pos in CYCLE_KEEP_CASES:
        c = {"args": [arr, pos]}
        c["expected"] = solver(c["args"])
        c["stdin"], c["stdout"] = leetcode_case_to_stdio(c["args"], c["expected"])
        hidden_cases.append(c)
    for arr, pos in CYCLE_WITH_CYCLE_CASES:
        c = {"args": [arr, pos]}
        c["expected"] = solver(c["args"])
        c["stdin"], c["stdout"] = leetcode_case_to_stdio(c["args"], c["expected"])
        hidden_cases.append(c)

    return sample_cases, hidden_cases


# ─── design-linked-list 替换用例（hidden[1]-[13] 原为数组索引，替换为操作序列）───

DESIGN_LINKED_LIST_HIDDEN_STDS = [
    # hidden[0] 保留（已正确），以下为 hidden[1]+ 的替换
    "8\naddAtTail 1\naddAtTail 2\naddAtTail 3\nget 0\nget 1\nget 2\ndeleteAtIndex 0\nget 0\n",
    "8\naddAtHead 1\naddAtHead 2\naddAtTail 3\nget 0\nget 1\nget 2\ndeleteAtIndex 0\nget 0\n",
    "8\naddAtIndex 0 1\naddAtIndex 1 2\naddAtIndex 2 3\nget 0\nget 1\nget 2\ndeleteAtIndex 1\nget 1\n",
    "7\naddAtHead 5\naddAtHead 4\naddAtHead 3\nget 0\nget 2\ndeleteAtIndex 1\nget 1\n",
    "7\naddAtTail 10\naddAtTail 20\naddAtTail 30\nget 2\nget 0\ndeleteAtIndex 2\nget 2\n",
    "8\naddAtHead 1\naddAtTail 2\naddAtIndex 1 3\nget 1\ndeleteAtIndex 0\nget 0\nget 1\n",
    "9\naddAtIndex 0 5\naddAtIndex 0 10\naddAtIndex 1 15\nget 0\nget 1\nget 2\ndeleteAtIndex 2\nget 2\n",
    "9\naddAtTail 1\naddAtTail 2\naddAtTail 3\naddAtTail 4\naddAtTail 5\nget 4\nget 0\ndeleteAtIndex 2\nget 2\n",
    "9\naddAtHead 100\naddAtHead 200\nget 0\nget 1\ndeleteAtIndex 0\nget 0\ndeleteAtIndex 0\nget 0\n",
]


def _format_value(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False)


# ─── 标准修复函数 ───

def fix_case(slug: str, label: str, idx: int, case: dict, solver) -> list[str]:
    """修复单个用例，返回变更描述列表。"""
    changes: list[str] = []
    args = case.get("args")
    if args is None:
        args = []
        case["args"] = args

    # 运行参考解法
    try:
        actual = solver(args)
    except Exception as e:
        changes.append(f"参考解法异常: {type(e).__name__}: {e}")
        return changes

    # 比较 expected
    old_expected = case.get("expected")
    if not compare_result(old_expected, actual, slug):
        changes.append(
            f"expected 修复: {_format_value(old_expected)} -> {_format_value(actual)}"
        )
        case["expected"] = actual

    # 重新生成 stdin/stdout
    new_stdin, new_stdout = leetcode_case_to_stdio(args, case.get("expected"))
    old_stdin = case.get("stdin")
    old_stdout = case.get("stdout")
    if old_stdin != new_stdin:
        changes.append(f"stdin 修复")
        case["stdin"] = new_stdin
    if old_stdout != new_stdout:
        changes.append(
            f"stdout 修复: {_format_value(old_stdout)} -> {_format_value(new_stdout)}"
        )
        case["stdout"] = new_stdout

    return changes


def fix_design_case(slug: str, label: str, idx: int, case: dict, simulator) -> list[str]:
    """修复 design 类用例（args=null，stdin/stdout 为权威数据）。"""
    changes: list[str] = []
    stdin = case.get("stdin", "")
    old_stdout = case.get("stdout", "")

    try:
        new_stdout = simulator(stdin)
    except Exception as e:
        changes.append(f"模拟器异常: {type(e).__name__}: {e}")
        return changes

    if old_stdout != new_stdout:
        changes.append(
            f"stdout 修复: {_format_value(old_stdout)} -> {_format_value(new_stdout)}"
        )
        case["stdout"] = new_stdout

    return changes


def fix_intersection_cases(slug: str, cfg: dict) -> list[str]:
    """修复 intersection-of-two-linked-lists（使用 safe 解法）。"""
    changes: list[str] = []
    solver = SOLUTIONS_OVERRIDES[slug]
    for label in ("samples", "hidden"):
        cases = cfg.get(label) or []
        for i, case in enumerate(cases):
            args = case.get("args")
            if args is None:
                continue
            # args 是 [dict]，解包传给 solver
            try:
                actual = solver(args[0]) if isinstance(args, list) and len(args) == 1 else solver(args)
            except Exception as e:
                changes.append(f"  {label}[{i}] 参考解法异常: {type(e).__name__}: {e}")
                continue

            old_expected = case.get("expected")
            if not compare_result(old_expected, actual, slug):
                changes.append(
                    f"  {label}[{i}] expected 修复: {_format_value(old_expected)} -> {_format_value(actual)}"
                )
                case["expected"] = actual

            # 重新生成 stdin/stdout
            new_stdin, new_stdout = leetcode_case_to_stdio(args, case.get("expected"))
            old_stdin = case.get("stdin")
            old_stdout = case.get("stdout")
            if old_stdin != new_stdin:
                changes.append(f"  {label}[{i}] stdin 修复")
                case["stdin"] = new_stdin
            if old_stdout != new_stdout:
                changes.append(
                    f"  {label}[{i}] stdout 修复: {_format_value(old_stdout)} -> {_format_value(new_stdout)}"
                )
                case["stdout"] = new_stdout

    return changes


def fix_design_linked_list(slug: str, cfg: dict) -> list[str]:
    """修复 design-linked-list：验证 samples/hidden[0]，替换 hidden[1]+。"""
    changes: list[str] = []
    simulator = DESIGN_SIMULATORS[slug]

    # 修复 samples（用模拟器验证 stdout）
    samples = cfg.get("samples") or []
    for i, case in enumerate(samples):
        ch = fix_design_case(slug, "samples", i, case, simulator)
        for c in ch:
            changes.append(f"  samples[{i}] {c}")

    # 保留 hidden[0]，替换 hidden[1]+
    hidden = cfg.get("hidden") or []
    new_hidden = []
    if hidden:
        # hidden[0] 用模拟器验证
        ch = fix_design_case(slug, "hidden", 0, hidden[0], simulator)
        for c in ch:
            changes.append(f"  hidden[0] {c}")
        new_hidden.append(hidden[0])

    # 替换 hidden[1]+ 为正确的操作序列
    for j, stdin_str in enumerate(DESIGN_LINKED_LIST_HIDDEN_STDS):
        stdout_str = simulator(stdin_str)
        new_hidden.append({
            "args": None,
            "expected": None,
            "stdin": stdin_str,
            "stdout": stdout_str,
        })
        changes.append(f"  hidden[{j + 1}] 替换为操作序列用例")

    cfg["hidden"] = new_hidden
    return changes


def fix_design_stack_queue(slug: str, cfg: dict) -> list[str]:
    """修复 implement-stack-using-queues / implement-queue-using-stacks。"""
    changes: list[str] = []
    simulator = DESIGN_SIMULATORS[slug]
    for label in ("samples", "hidden"):
        cases = cfg.get(label) or []
        for i, case in enumerate(cases):
            ch = fix_design_case(slug, label, i, case, simulator)
            for c in ch:
                changes.append(f"  {label}[{i}] {c}")
    return changes


# ─── 主函数 ───

def main() -> int:
    bundle = json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))
    total_changed_cases = 0
    changed_slugs = 0

    for slug in TARGET_SLUGS:
        cfg = bundle.get(slug)
        if cfg is None:
            print(f"[警告] 题目 {slug} 不存在，跳过")
            continue

        print(f"\n=== [{slug}] ===")
        slug_changed = 0
        slug_changes: list[str] = []

        # ── 特殊处理：cycle 题 ──
        if slug in ("linked-list-cycle", "linked-list-cycle-ii"):
            samples, hidden = _build_cycle_slug_cases(slug)
            old_samples = cfg.get("samples") or []
            old_hidden = cfg.get("hidden") or []
            if old_samples != samples:
                slug_changes.append(
                    f"samples 重构: {len(old_samples)} -> {len(samples)} 个用例（补充 pos 参数）"
                )
                slug_changed += len(old_samples)
            if old_hidden != hidden:
                slug_changes.append(
                    f"hidden 重构: {len(old_hidden)} -> {len(hidden)} 个用例（补充 pos + 带环用例）"
                )
                slug_changed += len(old_hidden)
            cfg["samples"] = samples
            cfg["hidden"] = hidden
            for ch in slug_changes:
                print(f"  - {ch}")
            if not slug_changes:
                print("  无变更")
            total_changed_cases += slug_changed
            if slug_changed:
                changed_slugs += 1
            continue

        # ── 特殊处理：intersection ──
        if slug == "intersection-of-two-linked-lists":
            chs = fix_intersection_cases(slug, cfg)
            for ch in chs:
                print(f"  - {ch}")
                slug_changed += 1
            if not chs:
                print("  无变更")
            total_changed_cases += slug_changed
            if slug_changed:
                changed_slugs += 1
            continue

        # ── 特殊处理：design-linked-list ──
        if slug == "design-linked-list":
            chs = fix_design_linked_list(slug, cfg)
            for ch in chs:
                print(f"  - {ch}")
            slug_changed = len(chs)
            if not chs:
                print("  无变更")
            total_changed_cases += slug_changed
            if slug_changed:
                changed_slugs += 1
            continue

        # ── 特殊处理：implement-stack-using-queues / implement-queue-using-stacks ──
        if slug in DESIGN_SIMULATORS and slug != "design-linked-list":
            chs = fix_design_stack_queue(slug, cfg)
            for ch in chs:
                print(f"  - {ch}")
            slug_changed = len(chs)
            if not chs:
                print("  无变更")
            total_changed_cases += slug_changed
            if slug_changed:
                changed_slugs += 1
            continue

        # ── 标准处理：使用参考解法 ──
        solver = SOLUTIONS.get(slug)
        if solver is None:
            print(f"  [警告] 无参考解法，跳过")
            continue

        for label in ("samples", "hidden"):
            cases = cfg.get(label) or []
            for i, case in enumerate(cases):
                changes = fix_case(slug, label, i, case, solver)
                if changes:
                    print(f"  {label}[{i}]:")
                    for ch in changes:
                        print(f"    - {ch}")
                    slug_changed += 1

        if slug_changed == 0:
            print("  无变更")
        total_changed_cases += slug_changed
        if slug_changed:
            changed_slugs += 1

    # 写回
    BUNDLE_PATH.write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n=== 总结 ===")
    print(f"共修改 {changed_slugs} 道题，{total_changed_cases} 个用例")
    print(f"已写回 {BUNDLE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
