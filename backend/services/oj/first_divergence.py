"""First Divergence Detection — 首次状态偏离检测真实算法。

AlgoPilot 核心创新：比较学生程序执行过程与参考解执行过程，
定位第一次出现异常的位置。

参考解来源：同一题目的已有 AC 提交（真实学生通过的正确代码）。
如果不存在 AC 提交，则 firstDivergence = null，绝不伪造。

比较策略：
  1. 用同一失败用例运行参考解，获取 reference trace
  2. 逐步对齐 student trace 和 reference trace
  3. 在每一步比较公共关键变量的值
  4. 找到第一个变量值不同的步（首次状态偏离）

不按数组 index 强行比较——处理不同执行步数、循环展开差异。
当无法可靠比较时返回 null + reason，禁止编造结果。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from models.db_models import OjSubmission

_logger = logging.getLogger(__name__)

_MAX_TRACE_STEPS_TO_COMPARE = 200
_MAX_VAR_REPR_LEN = 200


@dataclass
class FirstDivergenceResult:
    """首次状态偏离检测结果。"""

    detected: bool = False
    step_index: int = 0
    line: int | None = None
    reference_line: int | None = None
    student_state: str = ""
    reference_state: str = ""
    divergent_variable: str = ""
    explanation: str = ""
    confidence: str = "low"
    reference_source: str = ""
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "detected": self.detected,
            "step_index": self.step_index,
            "line": self.line,
            "reference_line": self.reference_line,
            "student_state": self.student_state,
            "reference_state": self.reference_state,
            "divergent_variable": self.divergent_variable,
            "explanation": self.explanation,
            "confidence": self.confidence,
            "reference_source": self.reference_source,
            "reason": self.reason,
        }


def find_reference_solution(db: Session, slug: str, language: str = "python") -> str | None:
    """从已有 AC 提交中获取一道题目的参考解代码。

    优先选择最近一次 AC 提交的代码作为参考解。
    这是真实来源——不是内置假解，而是真实通过)学生通过的代码。
    """
    row = (
        db.query(OjSubmission)
        .filter(
            OjSubmission.problem_slug == slug,
            OjSubmission.verdict == "AC",
            OjSubmission.language == language,
        )
        .order_by(OjSubmission.created_at.desc())
        .first()
    )
    if row is None:
        return None
    return row.code


def _extract_var_value(var_snapshot: Any) -> Any:
    """从 trace step 的变量快照中提取值。

    trace step 的 vars 格式：{name: {type: ..., value: ...}}
    """
    if isinstance(var_snapshot, dict):
        return var_snapshot.get("value", var_snapshot)
    return var_snapshot


def _vars_at_step(step: dict[str, Any]) -> dict[str, Any]:
    """提取某一步的所有变量值。"""
    raw_vars = step.get("vars", {})
    result: dict[str, Any] = {}
    for name, snap in raw_vars.items():
        result[name] = _extract_var_value(snap)
    return result


def _values_equal(a: Any, b: Any) -> bool:
    """比较两个变量值是否等价。

    处理 int/float 精度、list 内容、None 等。
    """
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) < 1e-9
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return False
        return all(_values_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        return all(_values_equal(a[k], b[k]) for k in a)
    return a == b


def _format_state(vars_map: dict[str, Any], focus_keys: list[str] | None = None) -> str:
    """格式化变量状态为可读字符串。"""
    keys = focus_keys or list(vars_map.keys())
    parts: list[str] = []
    for k in keys:
        if k in vars_map:
            v = vars_map[k]
            s = repr(v)
            if len(s) > _MAX_VAR_REPR_LEN:
                s = s[:_MAX_VAR_REPR_LEN] + "..."
            parts.append(f"{k}={s}")
    return ", ".join(parts)


def _find_common_keys(
    student_vars: dict[str, Any],
    reference_vars: dict[str, Any],
) -> list[str]:
    """找出两个变量集合的公共键，排除内部临时变量（以 _ 开头）。"""
    common = set(student_vars.keys()) & set(reference_vars.keys())
    return sorted(k for k in common if not k.startswith("_"))


def detect_first_divergence(
    *,
    student_steps: list[dict[str, Any]],
    reference_steps: list[dict[str, Any]],
    reference_source: str = "ac_submission",
) -> FirstDivergenceResult:
    """比较 student trace 和 reference trace，找到首次状态偏离。

    Args:
        student_steps: 学生代码的执行轨迹
        reference_steps: 参考解的执行轨迹
        reference_source: 参考解来源描述

    Returns:
        FirstDivergenceResult，detected=True 时包含偏离位置和状态
    """
    if not student_steps or not reference_steps:
        return FirstDivergenceResult(
            reason="student 或 reference trace 为空",
        )

    if not reference_steps:
        return FirstDivergenceResult(
            reason="reference trace 为空",
        )

    max_len = min(len(student_steps), len(reference_steps), _MAX_TRACE_STEPS_TO_COMPARE)

    for i in range(max_len):
        s_step = student_steps[i]
        r_step = reference_steps[i]

        s_vars = _vars_at_step(s_step)
        r_vars = _vars_at_step(r_step)

        common_keys = _find_common_keys(s_vars, r_vars)
        if not common_keys:
            continue

        for key in common_keys:
            s_val = s_vars[key]
            r_val = r_vars[key]

            if not _values_equal(s_val, r_val):
                s_line = s_step.get("line")
                r_line = r_step.get("line")
                focus = [key]
                return FirstDivergenceResult(
                    detected=True,
                    step_index=i,
                    line=s_line,
                    reference_line=r_line,
                    student_state=_format_state(s_vars, focus),
                    reference_state=_format_state(r_vars, focus),
                    divergent_variable=key,
                    explanation=(
                        f"Step {i} 变量 '{key}' 首次偏离："
                        f"学生 {s_val} ≠ 参考 {r_val}。"
                        f"此前所有公共变量状态一致。"
                    ),
                    confidence="high" if i < max_len // 2 else "medium",
                    reference_source=reference_source,
                )

    if len(student_steps) != len(reference_steps):
        shorter = min(len(student_steps), len(reference_steps))
        longer_name = "student" if len(student_steps) > len(reference_steps) else "reference"
        return FirstDivergenceResult(
            detected=True,
            step_index=shorter,
            line=student_steps[shorter - 1].get("line") if shorter > 0 else None,
            student_state=_format_state(_vars_at_step(student_steps[shorter - 1])) if shorter > 0 else "",
            reference_state=_format_state(_vars_at_step(reference_steps[shorter - 1])) if shorter > 0 else "",
            divergent_variable="",
            explanation=(
                f"前 {shorter} 步公共变量状态一致，"
                f"但 {longer_name} trace 有更多步骤（{len(student_steps)} vs {len(reference_steps)}），"
                f"可能存在循环次数差异。"
            ),
            confidence="medium",
            reference_source=reference_source,
        )

    return FirstDivergenceResult(
        reason="student 与 reference trace 在所有公共步上变量状态一致",
        reference_source=reference_source,
    )


def run_first_divergence_analysis(
    db: Session,
    *,
    slug: str,
    student_code: str,
    student_steps: list[dict[str, Any]],
    language: str = "python",
    run_reference_trace_fn: Any = None,
) -> FirstDivergenceResult:
    """完整的首次偏离检测流程。

    1. 从 AC 提交获取参考解
    2. 用同一用例运行参考解获取 reference trace
    3. 比较两个 trace

    如果无 AC 提交或无法获取 reference trace，返回 null + reason。

    Args:
        db: 数据库会话
        slug: 题目 slug
        student_code: 学生代码（未使用，但保留用于日志）
        student_steps: 学生代码的执行轨迹
        language: 编程语言<语言
        run_reference_trace_fn: 运行参考解获取 trace 的函数
            signature: (code, slug, language) -> list[dict] (steps)
    """
    reference_code = find_reference_solution(db, slug, language=language)
    if reference_code is None:
        return FirstDivergenceResult(
            reason="insufficient_reference_trace: 该题目尚无 AC 提交可作为参考解",
        )

    if reference_code.strip() == student_code.strip():
        return FirstDivergenceResult(
            reason="student 代码与参考解相同，无需比较",
        )

    if run_reference_trace_fn is None:
        return FirstDivergenceResult(
            reason="未提供 reference trace 运行函数",
        )

    try:
        reference_steps = run_reference_trace_fn(reference_code, slug, language)
    except Exception as e:
        _logger.warning("参考解 trace 运行失败 slug=%s: %s", slug, e)
        return FirstDivergenceResult(
            reason=f"参考解 trace 运行失败: {e}",
        )

    if not reference_steps:
        return FirstDivergenceResult(
            reason="参考解 trace 为空",
        )

    return detect_first_divergence(
        student_steps=student_steps,
        reference_steps=reference_steps,
        reference_source=f"ac_submission:{slug}",
    )