"""AlgoPilot 系统评测指标计算。

覆盖 iCAN 比赛关注的六类指标：
  1. Bug 定位准确率（Top-1 / Top-3）
  2. Bug 类型识别准确率
  3. 反例/测试用例生成质量（Bug Trigger Rate）
  4. AI 可靠性（Hallucination Rate / Evidence Coverage）
  5. 教学效果（Fix Success Rate / Debug Time / Hint Usage / Repeated Bug Rate）
  6. 系统性能（P50 / P95 / P99 延迟）

数据来源：后端数据库 oj_submissions / learning_event_logs / student_learning_memories。
当缺乏人工标注或真实实验数据时，指标返回 None 并标注 reason，绝不伪造数值。
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MetricResult:
    """单个评测指标的结果。"""

    name: str
    value: float | None
    unit: str = ""
    sample_size: int = 0
    reason: str = ""

    @property
    def is_available(self) -> bool:
        return self.value is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "sample_size": self.sample_size,
            "reason": self.reason,
            "available": self.is_available,
        }


@dataclass
class EvaluationReport:
    """完整评测报告。"""

    bug_localization: list[MetricResult] = field(default_factory=list)
    bug_classification: list[MetricResult] = field(default_factory=list)
    counterexample: list[MetricResult] = field(default_factory=list)
    ai_reliability: list[MetricResult] = field(default_factory=list)
    teaching_effect: list[MetricResult] = field(default_factory=list)
    system_performance: list[MetricResult] = field(default_factory=list)

    def all_metrics(self) -> list[MetricResult]:
        return (
            self.bug_localization
            + self.bug_classification
            + self.counterexample
            + self.ai_reliability
            + self.teaching_effect
            + self.system_performance
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "bug_localization": [m.to_dict() for m in self.bug_localization],
            "bug_classification": [m.to_dict() for m in self.bug_classification],
            "counterexample": [m.to_dict() for m in self.counterexample],
            "ai_reliability": [m.to_dict() for m in self.ai_reliability],
            "teaching_effect": [m.to_dict() for m in self.teaching_effect],
            "system_performance": [m.to_dict() for m in self.system_performance],
        }


def _percentile(sorted_values: list[float], p: float) -> float:
    """计算已排序列表的 p 分位数（p ∈ [0, 100]）。"""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    k = (len(sorted_values) - 1) * p / 100.0
    f = int(k)
    c = f + 1
    if c >= len(sorted_values):
        return sorted_values[f]
    return sorted_values[f] + (k - f) * (sorted_values[c] - sorted_values[f])


def compute_top_k_accuracy(
    predictions: list[set[int]],
    ground_truths: list[int],
    k: int,
) -> MetricResult:
    """Bug 定位 Top-K Accuracy。

    Args:
        predictions: 每个样本系统预测的疑似行号集合
        ground_truths: 每个样本人工标注的真实 Bug 行号
        k: Top-K

    当无标注数据时返回 None。
    """
    if not ground_truths:
        return MetricResult(
            name=f"top_{k}_accuracy",
            value=None,
            unit="%",
            reason="尚无人工标注的 Bug 行号数据",
        )
    correct = 0
    for pred, gt in zip(predictions, ground_truths):
        top_k = sorted(pred)[:k]
        if gt in top_k:
            correct += 1
    acc = correct / len(ground_truths) * 100
    return MetricResult(
        name=f"top_{k}_accuracy",
        value=round(acc, 2),
        unit="%",
        sample_size=len(ground_truths),
    )


def compute_classification_accuracy(
    predictions: list[str],
    ground_truths: list[str],
) -> MetricResult:
    """Bug 类型识别准确率。"""
    if not ground_truths:
        return MetricResult(
            name="classification_accuracy",
            value=None,
            unit="%",
            reason="尚无人工标注的 Bug 类型数据",
        )
    correct = sum(1 for p, g in zip(predictions, ground_truths) if p == g)
    acc = correct / len(ground_truths) * 100
    return MetricResult(
        name="classification_accuracy",
        value=round(acc, 2),
        unit="%",
        sample_size=len(ground_truths),
    )


def compute_bug_trigger_rate(
    generated_cases: list[dict[str, Any]],
) -> MetricResult:
    """反例生成 Bug Trigger Rate：生成的测试用例中能触发 Bug 的比例。

    每个 case 应含 triggered: bool 字段。
    """
    valid = [c for c in generated_cases if "triggered" in c]
    if not valid:
        return MetricResult(
            name="bug_trigger_rate",
            value=None,
            unit="%",
            reason="尚无反例生成执行记录",
        )
    triggered = sum(1 for c in valid if c["triggered"])
    rate = triggered / len(valid) * 100
    return MetricResult(
        name="bug_trigger_rate",
        value=round(rate, 2),
        unit="%",
        sample_size=len(valid),
    )


def compute_hallucination_rate(
    diagnosis_results: list[dict[str, Any]],
) -> MetricResult:
    """AI 诊断幻觉率：被标记为 hallucination 的诊断比例。"""
    if not diagnosis_results:
        return MetricResult(
            name="hallucination_rate",
            value=None,
            unit="%",
            reason="尚无 AI 诊断记录",
        )
    flagged = sum(1 for d in diagnosis_results if d.get("hallucination_detected"))
    rate = flagged / len(diagnosis_results) * 100
    return MetricResult(
        name="hallucination_rate",
        value=round(rate, 2),
        unit="%",
        sample_size=len(diagnosis_results),
    )


def compute_evidence_coverage(
    diagnosis_results: list[dict[str, Any]],
) -> MetricResult:
    """证据覆盖率：携带结构化执行证据（非纯文本）的诊断比例。"""
    if not diagnosis_results:
        return MetricResult(
            name="evidence_coverage",
            value=None,
            unit="%",
            reason="尚无 AI 诊断记录",
        )
    with_evidence = sum(
        1
        for d in diagnosis_results
        if d.get("has_execution_evidence") or d.get("has_trace_evidence")
    )
    rate = with_evidence / len(diagnosis_results) * 100
    return MetricResult(
        name="evidence_coverage",
        value=round(rate, 2),
        unit="%",
        sample_size=len(diagnosis_results),
    )


def compute_fix_success_rate(
    sessions: list[dict[str, Any]],
) -> MetricResult:
    """修复成功率：诊断后最终 AC 的会话比例。"""
    if not sessions:
        return MetricResult(
            name="fix_success_rate",
            value=None,
            unit="%",
            reason="尚无完整诊断-修复会话记录",
        )
    fixed = sum(1 for s in sessions if s.get("eventually_accepted"))
    rate = fixed / len(sessions) * 100
    return MetricResult(
        name="fix_success_rate",
        value=round(rate, 2),
        unit="%",
        sample_size=len(sessions),
    )


def compute_hint_usage(
    sessions: list[dict[str, Any]],
) -> list[MetricResult]:
    """分层提示使用统计。"""
    if not sessions:
        return [
            MetricResult(
                name="avg_hint_level_used",
                value=None,
                unit="level",
                reason="尚无提示使用记录",
            )
        ]
    levels = [s.get("hint_level_used", 0) for s in sessions if s.get("hint_level_used")]
    if not levels:
        return [
            MetricResult(
                name="avg_hint_level_used",
                value=None,
                unit="level",
                reason="尚无提示使用记录",
            )
        ]
    avg = statistics.mean(levels)
    return [
        MetricResult(
            name="avg_hint_level_used",
            value=round(avg, 2),
            unit="level",
            sample_size=len(levels),
        )
    ]


def compute_repeated_bug_rate(
    user_bug_histories: list[list[str]],
) -> MetricResult:
    """重复 Bug 率：同一用户再次出现相同 Bug 类型的比例。"""
    if not user_bug_histories:
        return MetricResult(
            name="repeated_bug_rate",
            value=None,
            unit="%",
            reason="尚无用户 Bug 历史记录",
        )
    repeated = 0
    total = 0
    for history in user_bug_histories:
        if len(history) < 2:
            continue
        total += 1
        if len(set(history)) < len(history):
            repeated += 1
    if total == 0:
        return MetricResult(
            name="repeated_bug_rate",
            value=None,
            unit="%",
            reason="尚无用户有足够 Bug 历史",
        )
    rate = repeated / total * 100
    return MetricResult(
        name="repeated_bug_rate",
        value=round(rate, 2),
        unit="%",
        sample_size=total,
    )


def compute_latency_percentiles(
    latencies_ms: list[float],
) -> list[MetricResult]:
    """系统延迟分位数 P50 / P95 / P99。"""
    if not latencies_ms:
        reason = "尚无请求延迟记录"
        return [
            MetricResult(name="p50_latency_ms", value=None, unit="ms", reason=reason),
            MetricResult(name="p95_latency_ms", value=None, unit="ms", reason=reason),
            MetricResult(name="p99_latency_ms", value=None, unit="ms", reason=reason),
        ]
    sorted_lat = sorted(latencies_ms)
    return [
        MetricResult(
            name="p50_latency_ms",
            value=round(_percentile(sorted_lat, 50), 2),
            unit="ms",
            sample_size=len(latencies_ms),
        ),
        MetricResult(
            name="p95_latency_ms",
            value=round(_percentile(sorted_lat, 95), 2),
            unit="ms",
            sample_size=len(latencies_ms),
        ),
        MetricResult(
            name="p99_latency_ms",
            value=round(_percentile(sorted_lat, 99), 2),
            unit="ms",
            sample_size=len(latencies_ms),
        ),
    ]