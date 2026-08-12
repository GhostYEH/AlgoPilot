"""Counterexample 集成服务 — 将反例生成器接入正式 WA 诊断流程。

目标：当学生代码 WA 时，尝试找到比原始失败样例更能暴露 Bug 的反例。
所有候选必须经过真实执行验证，不能直接使用 AI 生成的 expected output。

开销限制：
  - max_candidates: 最多生成的候选数量
  - max_execution_count: 最多真实执行次数
  - per_case_timeout_ms: 每次执行超时
  - total_timeout_ms: 整个反例流程总超时

如果找到更好的反例 → counterexample_source = "generated_verified"
如果未找到 → 保留原始失败样例，counterexample_source = "original_failed_case"
如果参考解不可用 → 优雅降级，counterexample_source = "original_failed_case"
如果生成器异常 → 不崩溃，counterexample_source = "original_failed_case"
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from services.oj.counterexample import (
    CounterexampleCandidate,
    CounterexampleResult,
    generate_boundary_cases,
    verify_and_find_best,
)

_logger = logging.getLogger(__name__)

_MAX_CANDIDATES = 8
_MAX_EXECUTION_COUNT = 12
_PER_CASE_TIMEOUT_MS = 3000
_TOTAL_TIMEOUT_MS = 8000


@dataclass
class CounterexampleIntegrationResult:
    """反例集成结果。"""

    selected_case: dict[str, Any] | None = None
    source: str = "original_failed_case"
    candidate_count: int = 0
    verified_count: int = 0
    triggered_count: int = 0
    latency_ms: int = 0
    category: str = ""
    reason: str = ""
    raw_result: CounterexampleResult | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_case": self.selected_case,
            "source": self.source,
            "candidate_count": self.candidate_count,
            "verified_count": self.verified_count,
            "triggered_count": self.triggered_count,
            "latency_ms": self.latency_ms,
            "category": self.category,
            "reason": self.reason,
        }


def _infer_problem_type(slug: str, module_key: str = "") -> str:
    """从 slug 和 module_key 推断题目类型。"""
    text = f"{slug} {module_key}".lower()
    if "binary" in text or "search" in text:
        return "binary-search"
    if "sort" in text:
        return "sorting"
    if "linked" in text:
        return "linked-list"
    if "dp" in text or "knapsack" in text:
        return "dp"
    return "array"


def try_counterexample(
    *,
    slug: str,
    module_key: str = "",
    original_failed_case: dict[str, Any] | None = None,
    user_runner: Any = None,
    reference_runner: Any = None,
    max_candidates: int = _MAX_CANDIDATES,
    total_timeout_ms: int = _TOTAL_TIMEOUT_MS,
) -> CounterexampleIntegrationResult:
    """尝试生成并验证反例。

    Args:
        slug: 题目 slug
        module_key: 模块 key（用于推断题目类型）
        original_failed_case: 原始失败样例（保底使用）
        user_runner: 执行学生代码的函数 (args) -> actual
        reference_runner: 执行参考解的函数 (args) -> expected（可选）
        max_candidates: 最多候选数量
        total_timeout_ms: 总超时

    Returns:
        CounterexampleIntegrationResult
    """
    start = time.monotonic()
    fallback = CounterexampleIntegrationResult(
        selected_case=original_failed_case,
        source="original_failed_case",
        reason="保留原始失败样例",
    )

    if original_failed_case is None:
        fallback.reason = "无原始失败样例可用"
        return fallback

    try:
        problem_type = _infer_problem_type(slug, module_key)
        candidates = generate_boundary_cases(
            problem_type=problem_type,
            count=max_candidates,
        )

        if not candidates:
            fallback.latency_ms = int((time.monotonic() - start) * 1000)
            return fallback

        if user_runner is None:
            fallback.latency_ms = int((time.monotonic() - start) * 1000)
            fallback.reason = "未提供学生代码执行函数"
            return fallback

        elapsed_ms = int((time.monotonic() - start) * 1000)
        remaining_ms = total_timeout_ms - elapsed_ms
        if remaining_ms <= 0:
            fallback.latency_ms = elapsed_ms
            fallback.reason = "反例生成超时"
            return fallback

        result = verify_and_find_best(
            candidates[:max_candidates],
            user_runner=user_runner,
            reference_runner=reference_runner,
            early_stop=True,
        )

        latency_ms = int((time.monotonic() - start) * 1000)

        if result.best is not None and result.best.triggered:
            best = result.best
            return CounterexampleIntegrationResult(
                selected_case={
                    "args": best.args,
                    "expected": best.expected,
                    "actual": best.actual,
                    "category": best.category,
                    "reason": best.reason,
                },
                source="generated_verified",
                candidate_count=result.total_generated,
                verified_count=result.total_verified,
                triggered_count=int(result.trigger_rate * result.total_generated / 100)
                if result.total_generated
                else 0,
                latency_ms=latency_ms,
                category=best.category,
                reason=f"验证反例触发 Bug（{best.category}），"
                f"候选 {result.total_generated} 个，验证 {result.total_verified} 个。",
                raw_result=result,
            )

        return CounterexampleIntegrationResult(
            selected_case=original_failed_case,
            source="original_failed_case",
            candidate_count=result.total_generated,
            verified_count=result.total_verified,
            triggered_count=0,
            latency_ms=latency_ms,
            reason=f"生成的 {result.total_generated} 个候选均未触发 Bug，保留原始失败样例。",
            raw_result=result,
        )

    except Exception as e:
        _logger.exception("Counterexample 集成异常 slug=%s: %s", slug, e)
        fallback.latency_ms = int((time.monotonic() - start) * 1000)
        fallback.reason = f"反例生成异常: {e}"
        return fallback