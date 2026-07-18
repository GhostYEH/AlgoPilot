"""修复 tests_bundle.json 中 Array/String/Sorting 类题目的错误测试用例。

对每个目标题目：
1. 使用 verify_test_cases.py 中的参考解法重新计算 expected。
2. 若 expected 与参考解法结果不一致，则更新 expected。
3. 用 services.oj.stdio_io.leetcode_case_to_stdio 重新生成 stdin/stdout。
4. 写回 tests_bundle.json，并打印每道题修改了哪些用例。

特殊处理：
- sorting-basic-output / sorting-inversion-count / sorting-kth-largest 的 samples
  及早期 hidden 用例可能只有 stdin/stdout 而无 args/expected，需要从 stdin
  解析出 args 并补充 expected 字段。
- longest-happy-prefix 的 hidden[1] 原为 args=[""]，参考解法会因空字符串崩溃，
  改为 args=["abcabc"]（expected="abc"）。
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
    "two-sum",
    "two-sum-ii-input-array-is-sorted",
    "reverse-words-in-a-string-ii",
    "reverse-string-ii",
    "reverse-vowels-of-a-string",
    "replace-space-lcof",
    "squares-of-a-sorted-array",
    "binary-search",
    "minimum-size-subarray-sum",
    "fruit-into-baskets",
    "backspace-string-compare",
    "remove-all-adjacent-duplicates-in-string",
    "longest-happy-prefix",
    "spiral-matrix-ii",
    "sorting-basic-output",
    "sorting-inversion-count",
    "sorting-kth-largest",
]


def _parse_sorting_basic(stdin: str) -> list[Any]:
    """stdin: 'n\\n a1 a2 ... an\\n' -> args=[[a1, ..., an]]"""
    lines = [ln for ln in stdin.split("\n") if ln.strip() != ""]
    if len(lines) < 2:
        return [[]]
    arr = [int(x) for x in lines[1].split()]
    return [arr]


def _parse_sorting_inversion(stdin: str) -> list[Any]:
    """同 sorting-basic"""
    return _parse_sorting_basic(stdin)


def _parse_sorting_kth_largest(stdin: str) -> list[Any]:
    """stdin 可能是两种格式：
    旧: 'n k\\n a1 ... an\\n'  （第一行含两个数）
    新: 'n\\n a1 ... an\\n k\\n' （leetcode 风格，k 单独一行）
    """
    lines = [ln for ln in stdin.split("\n") if ln.strip() != ""]
    if not lines:
        return [[], 1]
    first_tokens = lines[0].split()
    if len(first_tokens) == 2:
        # 旧格式
        n, k = int(first_tokens[0]), int(first_tokens[1])
        arr = [int(x) for x in lines[1].split()] if len(lines) > 1 else []
        return [arr, k]
    # 新格式：第一行是 n，第二行是数组，第三行是 k
    arr = [int(x) for x in lines[1].split()] if len(lines) > 1 else []
    k = int(lines[2]) if len(lines) > 2 else 1
    return [arr, k]


# 针对没有 args 字段的 sorting 题目，从 stdin 解析出 args
STDIN_PARSERS = {
    "sorting-basic-output": _parse_sorting_basic,
    "sorting-inversion-count": _parse_sorting_inversion,
    "sorting-kth-largest": _parse_sorting_kth_largest,
}


def _slug_special_args(slug: str, label: str, idx: int, case: dict) -> bool:
    """对特殊用例做 args 调整（如 longest-happy-prefix 的空字符串）。

    返回 True 表示已修改 args。
    """
    if slug == "longest-happy-prefix" and label == "hidden" and idx == 1:
        # 原为 args=[""]，参考解法会崩溃；改为 args=["abcabc"] -> "abc"
        old_args = case.get("args")
        if old_args == [""]:
            case["args"] = ["abcabc"]
            return True
    return False


def _format_value(v: Any) -> str:
    """用于打印的可读表示。"""
    return json.dumps(v, ensure_ascii=False)


def fix_case(slug: str, label: str, idx: int, case: dict, solver) -> list[str]:
    """修复单个用例，返回变更描述列表。"""
    changes: list[str] = []
    args = case.get("args")

    # 对 sorting 类没有 args 的用例，从 stdin 解析
    if args is None and slug in STDIN_PARSERS:
        stdin = case.get("stdin", "")
        args = STDIN_PARSERS[slug](stdin)
        case["args"] = args
        changes.append(f"args 缺失，从 stdin 解析为 {_format_value(args)}")

    # 对特殊用例调整 args
    if _slug_special_args(slug, label, idx, case):
        changes.append(
            f"args 调整: {_format_value(args)} -> {_format_value(case['args'])}"
        )
        args = case["args"]

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
        changes.append(
            f"stdin 修复: {_format_value(old_stdin)} -> {_format_value(new_stdin)}"
        )
        case["stdin"] = new_stdin
    if old_stdout != new_stdout:
        changes.append(
            f"stdout 修复: {_format_value(old_stdout)} -> {_format_value(new_stdout)}"
        )
        case["stdout"] = new_stdout

    return changes


def main() -> int:
    bundle = json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))
    total_changes = 0
    changed_cases = 0

    for slug in TARGET_SLUGS:
        cfg = bundle.get(slug)
        if cfg is None:
            print(f"[警告] 题目 {slug} 不存在，跳过")
            continue
        solver = SOLUTIONS.get(slug)
        if solver is None:
            print(f"[警告] 题目 {slug} 无参考解法，跳过")
            continue

        print(f"\n=== [{slug}] ===")
        slug_changed_cases = 0
        for label in ("samples", "hidden"):
            cases = cfg.get(label) or []
            for i, case in enumerate(cases):
                changes = fix_case(slug, label, i, case, solver)
                if changes:
                    print(f"  {label}[{i}]:")
                    for ch in changes:
                        print(f"    - {ch}")
                    slug_changed_cases += 1
                    changed_cases += 1
        if slug_changed_cases == 0:
            print("  无变更")
        total_changes += slug_changed_cases

    # 写回
    BUNDLE_PATH.write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n=== 总结 ===")
    print(f"共修改 {changed_cases} 个用例")
    print(f"已写回 {BUNDLE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
