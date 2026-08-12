"""Execution Evidence 持久化服务。

将诊断结果真实写入 execution_traces / bug_records / hint_records 表。
AlgoPilot 核心闭环的数据层：诊断 → 持久化 → 评测可查。
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from models.db_models import BugRecord, ExecutionTraceRecord, HintRecord

_logger = logging.getLogger(__name__)

_MAX_TRACE_STEPS_PERSIST = 500
_MAX_PAYLOAD_CHARS = 50000


def _truncate_steps(steps: list[dict[str, Any]], max_steps: int = _MAX_TRACE_STEPS_PERSIST) -> tuple[list[dict[str, Any]], bool]:
    """截断过长的 trace，返回 (truncated_steps, was_truncated)。"""
    if len(steps) <= max_steps:
        return steps, False
    return steps[:max_steps], True


def persist_execution_trace(
    db: Session,
    *,
    submission_id: int,
    trace_summary: Any = None,
    steps: list[dict[str, Any]] | None = None,
    language: str = "python",
    first_divergence_step: int = 0,
    first_divergence_line: int | None = None,
) -> ExecutionTraceRecord | None:
    """持久化执行轨迹到 execution_traces 表。

    Args:
        submission_id: 关联的 OJ 提交 ID
        trace_summary: TraceSummary 对象（可选）
        steps: trace 步骤列表（可选，优先于 trace_summary.steps）
    """
    try:
        if steps is None and trace_summary is not None:
            steps = [
                {
                    "line": getattr(s, "line", 0),
                    "vars": getattr(s, "vars", {}),
                    "changed": getattr(s, "changed", []),
                }
                for s in getattr(trace_summary, "steps", [])
            ]

        if steps is None:
            steps = []

        truncated_steps, was_truncated = _truncate_steps(steps)

        record = ExecutionTraceRecord(
            submission_id=submission_id,
            language=language,
            verdict=getattr(trace_summary, "verdict", "OK") if trace_summary else "OK",
            user_line_count=getattr(trace_summary, "user_line_count", 0) if trace_summary else 0,
            total_steps=len(steps),
            steps=truncated_steps,
            key_variable_changes=[],
            narrations=[],
            first_divergence_step=first_divergence_step,
            first_divergence_line=first_divergence_line,
            scene=getattr(trace_summary, "scene", "") if hasattr(trace_summary, "scene") else "",
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    except Exception:
        db.rollback()
        _logger.exception("persist_execution_trace 失败 submission_id=%s", submission_id)
        return None


def persist_bug_record(
    db: Session,
    *,
    user_id: int,
    problem_slug: str,
    bug_type: str = "unknown",
    bug_type_label: str = "",
    suspicious_lines: list[int] | None = None,
    first_divergence_step: int = 0,
    first_divergence_line: int | None = None,
    root_cause: str = "",
    confidence: str = "low",
    confidence_source: str = "rule_based",
    related_module_key: str = "",
    related_concept_id: str = "",
    diagnosis_source: str = "fallback",
    submission_id: int | None = None,
) -> BugRecord | None:
    """持久化 Bug 记录到 bug_records 表。"""
    try:
        record = BugRecord(
            submission_id=submission_id,
            user_id=user_id,
            problem_slug=problem_slug,
            bug_type=bug_type,
            bug_type_label=bug_type_label,
            suspicious_lines=suspicious_lines or [],
            first_divergence_step=first_divergence_step,
            first_divergence_line=first_divergence_line,
            root_cause=root_cause[:2000],
            confidence=confidence,
            confidence_source=confidence_source,
            related_module_key=related_module_key,
            related_concept_id=related_concept_id,
            diagnosis_source=diagnosis_source,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    except Exception:
        db.rollback()
        _logger.exception("persist_bug_record 失败 user_id=%s slug=%s", user_id, problem_slug)
        return None


def persist_hint_record(
    db: Session,
    *,
    user_id: int,
    problem_slug: str,
    hint_level_used: int = 0,
    hint_count: int = 0,
    eventually_accepted: bool = False,
    bug_type: str = "",
    module_key: str = "",
    submission_id: int | None = None,
) -> HintRecord | None:
    """持久化分层提示使用记录到 hint_records 表。"""
    try:
        record = HintRecord(
            submission_id=submission_id,
            user_id=user_id,
            problem_slug=problem_slug,
            hint_level_used=hint_level_used,
            hint_count=hint_count,
            eventually_accepted=eventually_accepted,
            bug_type=bug_type,
            module_key=module_key,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    except Exception:
        db.rollback()
        _logger.exception("persist_hint_record 失败 user_id=%s slug=%s", user_id, problem_slug)
        return None