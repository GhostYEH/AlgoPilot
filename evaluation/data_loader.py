"""从后端数据库提取评测所需的真实数据。

不伪造任何数据：当数据库为空或字段缺失时返回空列表，
metrics 模块会据此返回 None 并标注 reason。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))


def _get_session():
    from core.database import SessionLocal

    return SessionLocal()


def fetch_submissions_with_diagnosis() -> list[dict[str, Any]]:
    """提取所有有诊断信息的 OJ 提交记录。"""
    from models.db_models import OjSubmission

    records: list[dict[str, Any]] = []
    with _get_session() as session:
        rows = session.query(OjSubmission).filter(OjSubmission.verdict != "AC").all()
        for row in rows:
            cases = row.cases or []
            records.append(
                {
                    "submission_id": row.id,
                    "user_id": row.user_id,
                    "problem_slug": row.problem_slug,
                    "verdict": row.verdict,
                    "language": row.language,
                    "case_count": len(cases),
                    "runtime_ms_avg": row.runtime_ms_avg,
                    "has_cases": bool(cases),
                }
            )
    return records


def fetch_diagnosis_evidence() -> list[dict[str, Any]]:
    """Return one row per persisted diagnosis and its real trace evidence state."""
    from models.db_models import BugRecord, ExecutionTraceRecord

    records: list[dict[str, Any]] = []
    with _get_session() as session:
        rows = session.query(BugRecord).all()
        submission_ids = {
            row.submission_id for row in rows if row.submission_id is not None
        }
        traced_submission_ids: set[int] = set()
        if submission_ids:
            traced_submission_ids = {
                submission_id
                for (submission_id,) in (
                    session.query(ExecutionTraceRecord.submission_id)
                    .filter(ExecutionTraceRecord.submission_id.in_(submission_ids))
                    .distinct()
                    .all()
                )
            }
        for row in rows:
            records.append(
                {
                    "diagnosis_id": row.id,
                    "submission_id": row.submission_id,
                    "has_execution_evidence": row.submission_id in traced_submission_ids,
                }
            )
    return records


def fetch_event_latencies() -> list[float]:
    """从学习事件日志提取处理延迟（ms）。"""
    from models.db_models import LearningEventLog

    latencies: list[float] = []
    with _get_session() as session:
        rows = session.query(LearningEventLog).all()
        for row in rows:
            for log in row.agent_logs or []:
                if isinstance(log, dict) and "latency_ms" in log:
                    try:
                        latencies.append(float(log["latency_ms"]))
                    except (TypeError, ValueError):
                        pass
    return latencies


def fetch_bug_type_histories() -> list[list[str]]:
    """提取每个用户的 Bug 类型历史序列。"""
    from models.db_models import StudentLearningMemory

    by_user: dict[int, list[str]] = {}
    with _get_session() as session:
        rows = (
            session.query(StudentLearningMemory)
            .filter(StudentLearningMemory.observed_error_pattern != "")
            .order_by(StudentLearningMemory.created_at)
            .all()
        )
        for row in rows:
            by_user.setdefault(row.user_id, []).append(row.observed_error_pattern)
    return list(by_user.values())


def fetch_submission_count() -> int:
    """总提交数。"""
    from models.db_models import OjSubmission

    with _get_session() as session:
        return session.query(OjSubmission).count()
