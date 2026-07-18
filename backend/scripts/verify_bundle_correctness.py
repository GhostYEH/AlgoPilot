"""验证 tests_bundle.json 中所有题目的判题正确性。

对每道题：
1. 用参考解法运行 args，验证与 expected 一致；
2. 验证 stdin/stdout 与 args/expected 的洛谷化一致；
3. 统计隐藏用例数量，标记不足 5 个的题目。

用法（在后端根目录）:
  H:\\App\\python.exe scripts\\verify_bundle_correctness.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

from services.oj.stdio_io import (  # noqa: E402
    ensure_stdio_fields,
    leetcode_case_to_stdio,
    stdout_equal,
)
from verify_test_cases import (  # noqa: E402
    SOLUTIONS,
    compare_result,
)

BUNDLE_PATH = BACKEND / "data" / "oj" / "tests_bundle.json"
MIN_HIDDEN = 5


def verify_problem(slug: str, cfg: dict) -> list[str]:
    issues: list[str] = []
    solver = SOLUTIONS.get(slug)
    samples = cfg.get("samples") or []
    hidden = cfg.get("hidden") or []
    insens = bool(cfg.get("order_insensitive", False))

    # 检查隐藏用例数量
    if len(hidden) < MIN_HIDDEN:
        issues.append(
            f"hidden 不足 {MIN_HIDDEN} 个: 仅 {len(hidden)} 个"
        )

    if solver is None:
        # 没有参考解法，仅做格式检查
        for label, cases in (("samples", samples), ("hidden", hidden)):
            for i, case in enumerate(cases):
                # 检查 stdin/stdout 字段一致性
                fixed = ensure_stdio_fields(case)
                exp_stdin = fixed.get("stdin")
                exp_stdout = fixed.get("stdout")
                if case.get("stdin") is not None and case["stdin"] != exp_stdin:
                    issues.append(
                        f"{label}[{i}] stdin 与 args 不一致: "
                        f"实际={case['stdin']!r} 期望={exp_stdin!r}"
                    )
                if case.get("stdout") is not None and case["stdout"] != exp_stdout:
                    issues.append(
                        f"{label}[{i}] stdout 与 expected 不一致: "
                        f"实际={case['stdout']!r} 期望={exp_stdout!r}"
                    )
        return issues

    # 用参考解法验证每个用例
    for label, cases in (("samples", samples), ("hidden", hidden)):
        for i, case in enumerate(cases):
            args = case.get("args", [])
            expected = case.get("expected")

            # 1. 运行参考解法，验证 expected 正确
            try:
                actual = solver(args)
            except Exception as e:
                issues.append(
                    f"{label}[{i}] 参考解法异常: {type(e).__name__}: {e}"
                )
                continue
            if not compare_result(expected, actual, slug):
                issues.append(
                    f"{label}[{i}] expected 错误: "
                    f"args={args!r} expected={expected!r} actual={actual!r}"
                )

            # 2. 验证 stdin/stdout 与 args/expected 的一致性
            fixed = ensure_stdio_fields(case)
            exp_stdin = fixed["stdin"]
            exp_stdout = fixed["stdout"]
            case_stdin = case.get("stdin")
            case_stdout = case.get("stdout")
            if case_stdin is not None and case_stdin != exp_stdin:
                issues.append(
                    f"{label}[{i}] stdin 不一致: 实际={case_stdin!r} 期望={exp_stdin!r}"
                )
            if case_stdout is not None and case_stdout != exp_stdout:
                # stdout 字符串可能差异只是末尾换行，再宽容对比一次
                if not stdout_equal(case_stdout or "", exp_stdout or "", order_insensitive=insens):
                    issues.append(
                        f"{label}[{i}] stdout 不一致: 实际={case_stdout!r} 期望={exp_stdout!r}"
                    )

    return issues


def main() -> int:
    bundle = json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))
    all_issues: dict[str, list[str]] = {}
    no_solver: list[str] = []
    insufficient_hidden: list[str] = []

    total_cases_checked = 0
    for slug in sorted(bundle.keys()):
        cfg = bundle[slug]
        hidden_count = len(cfg.get("hidden") or [])
        samples_count = len(cfg.get("samples") or [])
        total_cases_checked += samples_count + hidden_count
        if hidden_count < MIN_HIDDEN:
            insufficient_hidden.append(slug)
        if slug not in SOLUTIONS:
            no_solver.append(slug)
        issues = verify_problem(slug, cfg)
        if issues:
            all_issues[slug] = issues

    print(f"=== tests_bundle.json 判题正确性验证 ===")
    print(f"题目总数:        {len(bundle)}")
    print(f"用例总数:        {total_cases_checked}")
    print(f"有参考解法题目:  {len(bundle) - len(no_solver)}")
    print(f"无参考解法题目:  {len(no_solver)}")
    if no_solver:
        print(f"  无解法: {no_solver}")
    print(f"隐藏用例不足 {MIN_HIDDEN} 个: {len(insufficient_hidden)}")
    if insufficient_hidden:
        for s in insufficient_hidden:
            print(f"  - {s}")
    print(f"有问题的题目数:  {len(all_issues)}")

    if all_issues:
        print("\n=== 问题详情 ===")
        for slug, issues in all_issues.items():
            print(f"\n[{slug}]")
            for iss in issues:
                print(f"  - {iss}")
        return 1
    print("\n所有有参考解法的题目均通过验证；stdin/stdout 与 args/expected 一致。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
