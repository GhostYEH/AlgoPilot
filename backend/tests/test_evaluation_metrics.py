"""Integrity tests for ground-truth-dependent evaluation metrics."""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from evaluation import data_loader  # noqa: E402
from evaluation.metrics import (  # noqa: E402
    compute_classification_accuracy,
    compute_hallucination_rate,
    compute_top_k_accuracy,
)


def test_missing_ground_truth_is_unavailable_not_zero() -> None:
    top1 = compute_top_k_accuracy([], [], 1)
    classification = compute_classification_accuracy([], [])
    assert top1.value is None and not top1.is_available
    assert classification.value is None and not classification.is_available


def test_mismatched_ground_truth_lengths_are_rejected() -> None:
    top1 = compute_top_k_accuracy([{3}], [3, 7], 1)
    classification = compute_classification_accuracy(["boundary"], ["boundary", "loop"])
    assert top1.value is None
    assert classification.value is None
    assert "不一致" in top1.reason
    assert "不一致" in classification.reason


def test_valid_ground_truth_is_calculated() -> None:
    top1 = compute_top_k_accuracy([{3}, {9}], [3, 7], 1)
    classification = compute_classification_accuracy(
        ["boundary", "loop"], ["boundary", "pointer"]
    )
    assert top1.value == 50.0 and top1.sample_size == 2
    assert classification.value == 50.0 and classification.sample_size == 2


def test_unannotated_diagnoses_do_not_create_fake_zero_hallucination_rate() -> None:
    result = compute_hallucination_rate([
        {"has_execution_evidence": True},
        {"has_execution_evidence": False},
    ])
    assert result.value is None
    assert result.sample_size == 0


def test_hallucination_rate_uses_only_annotated_records() -> None:
    result = compute_hallucination_rate([
        {"hallucination_detected": True},
        {"hallucination_detected": False},
        {"hallucination_detected": None},
        {"has_execution_evidence": True},
    ])
    assert result.value == 50.0
    assert result.sample_size == 2


def test_evidence_coverage_loader_uses_persisted_trace_not_submission_cases(
    monkeypatch,
) -> None:
    from models.db_models import Base, BugRecord, ExecutionTraceRecord

    engine = create_engine("sqlite://", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, future=True)
    with session_factory() as session:
        session.add_all([
            BugRecord(id=1, submission_id=10, user_id=1, problem_slug="with-trace"),
            BugRecord(id=2, submission_id=20, user_id=1, problem_slug="without-trace"),
            ExecutionTraceRecord(
                submission_id=10,
                total_steps=1,
                steps=[{"line": 1, "vars": {}, "changed": []}],
            ),
        ])
        session.commit()

    monkeypatch.setattr(data_loader, "_get_session", session_factory)
    records = data_loader.fetch_diagnosis_evidence()
    assert records == [
        {"diagnosis_id": 1, "submission_id": 10, "has_execution_evidence": True},
        {"diagnosis_id": 2, "submission_id": 20, "has_execution_evidence": False},
    ]
