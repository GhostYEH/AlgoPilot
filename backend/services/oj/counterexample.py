"""Counterexample Generator — 反例生成器。

AlgoPilot 核心创新二：当代码出现 Wrong Answer 时，
系统主动寻找最能暴露当前 Bug 的测试输入。

候选来源：
  1. 边界样例（空输入/单元素/最小值/最大值/重复/有序/逆序）
  2. 官方样例中已失败的
  3. AI 生成候选（需经 OJ/Reference 验证）

关键原则：AI 生成的测试用例不能直接当作正确结果，
必须经过 OJ / Reference Solution / Validator 验证。
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable

_logger = logging.getLogger(__name__)


@dataclass
class CounterexampleCandidate:
    """反例候选。"""

    args: list[Any]
    expected: Any = None
    category: str = ""
    reason: str = ""
    source: str = "boundary"
    triggered: bool = False
    actual: Any = None
    verified: bool = False


@dataclass
class CounterexampleResult:
    """反例生成结果。"""

    candidates: list[CounterexampleCandidate] = field(default_factory=list)
    best: CounterexampleCandidate | None = None
    total_generated: int = 0
    total_verified: int = 0
    trigger_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidates": [
                {
                    "args": c.args,
                    "expected": c.expected,
                    "category": c.category,
                    "reason": c.reason,
                    "source": c.source,
                    "triggered": c.triggered,
                    "actual": c.actual,
                    "verified": c.verified,
                }
                for c in self.candidates
            ],
            "best": None if not self.best else {
                "args": self.best.args,
                "category": self.best.category,
                "reason": self.best.reason,
                "actual": self.best.actual,
                "expected": self.best.expected,
            },
            "total_generated": self.total_generated,
            "total_verified": self.total_verified,
            "trigger_rate": self.trigger_rate,
        }


def generate_boundary_cases(
    *,
    problem_type: str = "array",
    max_value: int = 100,
    count: int = 8,
) -> list[CounterexampleCandidate]:
    """生成边界测试用例候选。

    覆盖：空输入、单元素、最小值、最大值、重复元素、有序、逆序、极端规模。
    """
    cases: list[CounterexampleCandidate] = []

    if problem_type in ("array", "two-pointers", "sorting"):
        cases.append(CounterexampleCandidate(
            args=[[]], category="empty", reason="空输入是最常见的边界遗漏",
        ))
        cases.append(CounterexampleCandidate(
            args=[[1]], category="single", reason="单元素数组",
        ))
        cases.append(CounterexampleCandidate(
            args=[[1, 1, 1, 1]], category="duplicate", reason="全重复元素",
        ))
        cases.append(CounterexampleCandidate(
            args=[list(range(1, 11))], category="sorted", reason="已排序数组",
        ))
        cases.append(CounterexampleCandidate(
            args=[list(range(10, 0, -1))], category="reverse_sorted", reason="逆序数组",
        ))
        cases.append(CounterexampleCandidate(
            args=[[max_value]], category="max_value", reason="最大值边界",
        ))
        cases.append(CounterexampleCandidate(
            args=[[0, max_value, 0, max_value]], category="extreme_alternating", reason="极值交替",
        ))
        cases.append(CounterexampleCandidate(
            args=[[-max_value, -1, 0, 1, max_value]], category="full_range", reason="完整值域",
        ))

    elif problem_type in ("binary-search",):
        cases.append(CounterexampleCandidate(
            args=[[1, 3, 5, 7], 7], category="last_element", reason="搜索最后一个元素",
        ))
        cases.append(CounterexampleCandidate(
            args=[[1, 3, 5, 7], 1], category="first_element", reason="搜索第一个元素",
        ))
        cases.append(CounterexampleCandidate(
            args=[[1, 3, 5, 7], 8], category="not_found_upper", reason="大于所有元素",
        ))
        cases.append(CounterexampleCandidate(
            args=[[1, 3, 5, 7], 0], category="not_found_lower", reason="小于所有元素",
        ))
        cases.append(CounterexampleCandidate(
            args=[[1], 1], category="single_found", reason="单元素命中",
        ))
        cases.append(CounterexampleCandidate(
            args=[[1], 2], category="single_not_found", reason="单元素未命中",
        ))
        cases.append(CounterexampleCandidate(
            args=[[], 0], category="empty_search", reason="空数组搜索",
        ))
        cases.append(CounterexampleCandidate(
            args=[[1, 2, 2, 2, 3], 2], category="duplicate_target", reason="重复目标值",
        ))

    elif problem_type in ("linked-list",):
        cases.append(CounterexampleCandidate(
            args=[[]], category="empty_list", reason="空链表",
        ))
        cases.append(CounterexampleCandidate(
            args=[[1]], category="single_node", reason="单节点",
        ))
        cases.append(CounterexampleCandidate(
            args=[[1, 2]], category="two_nodes", reason="两节点",
        ))
        cases.append(CounterexampleCandidate(
            args=[list(range(1, 11))], category="long_list", reason="较长链表",
        ))

    elif problem_type in ("dp",):
        cases.append(CounterexampleCandidate(
            args=[0], category="zero_input", reason="零输入",
        ))
        cases.append(CounterexampleCandidate(
            args=[1], category="one_input", reason="最小正输入",
        ))
        cases.append(CounterexampleCandidate(
            args=[2], category="two_input", reason="二输入",
        ))

    return cases[:count]


def generate_random_cases(
    *,
    problem_type: str = "array",
    count: int = 5,
    max_size: int = 20,
    max_value: int = 100,
    seed: int | None = None,
) -> list[CounterexampleCandidate]:
    """生成随机测试用例候选。"""
    rng = random.Random(seed)
    cases: list[CounterexampleCandidate] = []

    for i in range(count):
        size = rng.randint(0, max_size)
        if problem_type == "binary-search":
            arr = sorted(rng.sample(range(-max_value, max_value + 1), min(size, 2 * max_value)))
            target = rng.randint(-max_value, max_value)
            cases.append(CounterexampleCandidate(
                args=[arr, target], category=f"random_{i}", reason="随机生成", source="random",
            ))
        else:
            arr = [rng.randint(-max_value, max_value) for _ in range(size)]
            cases.append(CounterexampleCandidate(
                args=[arr], category=f"random_{i}", reason="随机生成", source="random",
            ))

    return cases


def _deduplicate(candidates: list[CounterexampleCandidate]) -> list[CounterexampleCandidate]:
    """去除 args 完全相同的候选，避免重复 subprocess 调用。"""
    seen: set[str] = set()
    result: list[CounterexampleCandidate] = []
    for c in candidates:
        key = repr(c.args)
        if key not in seen:
            seen.add(key)
            result.append(c)
    return result


def verify_and_find_best(
    candidates: list[CounterexampleCandidate],
    *,
    user_runner: Callable[[list[Any]], Any],
    reference_runner: Callable[[list[Any]], Any] | None = None,
    expected_override: Callable[[list[Any]], Any] | None = None,
    early_stop: bool = False,
    deadline: float | None = None,
    max_execution_count: int | None = None,
) -> CounterexampleResult:
    """验证候选反例，找出最能暴露 Bug 的。

    Args:
        candidates: 反例候选列表
        user_runner: 执行学生代码的函数，接受 args 返回 actual
        reference_runner: 执行参考解的函数（可选）
        expected_override: 直接计算期望值的函数（可选，优先于 reference_runner）
        early_stop: 找到第一个触发 Bug 的候选后立即停止，减少 subprocess 开销

    一个候选"触发 Bug"当且仅当：
      - 能成功执行（不抛异常）
      - actual != expected
    """
    candidates = _deduplicate(candidates)
    verified_count = 0
    triggered_count = 0
    best: CounterexampleCandidate | None = None
    execution_count = 0

    for c in candidates:
        if deadline is not None and time.monotonic() >= deadline:
            break
        expected_runner = expected_override or reference_runner
        required_executions = 1 + int(expected_runner is not None)
        if (
            max_execution_count is not None
            and execution_count + required_executions > max_execution_count
        ):
            break
        try:
            c.actual = user_runner(c.args)
            execution_count += 1
            if deadline is not None and time.monotonic() >= deadline:
                break
            if expected_runner is None:
                continue
            c.expected = expected_runner(c.args)
            execution_count += 1
            if c.expected is None:
                continue
            c.verified = True
            verified_count += 1
            if c.actual != c.expected:
                c.triggered = True
                triggered_count += 1
                if best is None:
                    best = c
                    if early_stop:
                        break
        except Exception as exc:
            c.verified = False
            _logger.debug(
                "counterexample candidate rejected category=%s error_type=%s",
                c.category,
                type(exc).__name__,
            )

    total = len(candidates)
    rate = (triggered_count / total * 100) if total else 0.0

    return CounterexampleResult(
        candidates=candidates,
        best=best,
        total_generated=total,
        total_verified=verified_count,
        trigger_rate=round(rate, 2),
    )
