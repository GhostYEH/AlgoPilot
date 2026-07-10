"""MasteryAgent 掌握度评估测试。"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.database import SessionLocal
from main import app
from models.db_models import User
from services.mastery.mastery_service import build_report
from services.mastery.scoring import compute_component_scores, compute_mastery_score
from services.mastery.scoring import compute_bkt_lite
from services.mastery.models import MasterySignals
from services.memory.memory_service import MemoryService, record_gamified_practice
from services.memory.schemas import MemoryEventInput
from utils.security import hash_password


@pytest.fixture
def db() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user(db: Session) -> User:
    name = f"mst_{uuid.uuid4().hex[:10]}"
    user = User(username=name, email=f"{name}@example.com", hashed_password=hash_password("pass"))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_default_report_without_history(db: Session, test_user: User):
    report = build_report(
        db,
        test_user.id,
        course_id="data_structures_algorithms",
        chapter_id="ch02-linear-list",
        persist=False,
    )
    assert report.mastery_score == 50
    assert report.mastery_level == "beginner"
    assert any("默认" in e.detail for e in report.evidence)


def test_wa_lowers_mastery_and_suggests_remediation(db: Session, test_user: User):
    svc = MemoryService(db)
    for i in range(4):
        svc.record_event(
            test_user.id,
            MemoryEventInput(
                event_type="oj_submit_fail",
                chapter_id="ch11-dynamic-programming",
                skill_id="dp-state-design",
                problem_slug=f"dp-prob-{i}",
                observed_error_pattern="初始化错误 dp 边界",
                mastery_delta=-1,
                evidence_json={"verdict": "WA"},
            ),
        )
    report = build_report(
        db,
        test_user.id,
        chapter_id="ch11-dynamic-programming",
        persist=False,
    )
    assert report.mastery_score < 50
    assert report.recommended_actions
    assert "巩固" in report.path_adjustment_suggestion or "章节" in report.path_adjustment_suggestion


def test_completion_raises_mastery(db: Session, test_user: User):
    svc = MemoryService(db)
    for _ in range(3):
        svc.record_event(
            test_user.id,
            MemoryEventInput(
                event_type="resource_complete",
                chapter_id="ch05-tree-binary-tree",
                skill_id="tree-traversal",
                successful_hint="递归基线条件要写清",
                mastery_delta=1,
                evidence_json={"correct": True},
            ),
        )
    svc.record_event(
        test_user.id,
        MemoryEventInput(
            event_type="quiz_complete",
            chapter_id="ch05-tree-binary-tree",
            mastery_delta=1,
            evidence_json={"correct": True},
        ),
    )
    report = build_report(
        db,
        test_user.id,
        chapter_id="ch05-tree-binary-tree",
        persist=False,
    )
    assert report.mastery_score > 50
    assert report.mastery_level in ("improving", "competent", "advanced")


def test_gamified_practice_increases_mastery(db: Session, test_user: User):
    for _ in range(3):
        record_gamified_practice(
            db,
            test_user.id,
            game_id="binary-search",
            level="find",
            module_key="array",
            success=True,
            score=100,
            attempts=1,
            time_spent_seconds=30,
        )
    report = build_report(
        db,
        test_user.id,
        chapter_id="ch02-linear-list",
        persist=False,
    )
    assert report.mastery_score > 50
    assert any("游戏化练习" in c.note for c in report.component_scores if c.key == "resource_completion")


def test_gamified_practice_signals_count(db: Session, test_user: User):
    record_gamified_practice(
        db,
        test_user.id,
        game_id="knapsack-lite",
        level="knapsack",
        module_key="dp",
        success=True,
    )
    from services.mastery.mastery_service import extract_signals
    signals = extract_signals(db, test_user.id, course_id="data_structures_algorithms")
    assert signals.gamified_practice_count >= 1
    assert signals.resource_completions >= 1


def test_scoring_formula_weights_sum():
    signals = MasterySignals(
        quiz_total=10,
        quiz_correct=8,
        oj_failures=1,
        resource_completions=2,
        oj_diagnoses=1,
        self_report_score=70,
        memory_event_count=5,
        recent_fail_patterns=["边界"],
        older_fail_patterns=["边界", "指针"],
    )
    components = compute_component_scores(signals)
    score = compute_mastery_score(components)
    assert 0 <= score <= 100
    assert len(components) == 6
    total_weight = sum(c.weight for c in components)
    assert abs(total_weight - 1.0) < 0.01


def test_mastery_api_stable_structure():
    client = TestClient(app)
    uname = f"mstapi_{uuid.uuid4().hex[:8]}"
    reg = client.post(
        "/api/auth/register",
        json={"username": uname, "password": "secret123", "email": f"{uname}@example.com"},
    )
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    report = client.get("/api/mastery/report", headers=headers)
    assert report.status_code == 200
    body = report.json()
    assert "overall_score" in body
    assert "overall_level" in body
    assert "chapters" in body
    assert isinstance(body["chapters"], list)

    recalc = client.post(
        "/api/mastery/recalculate",
        headers=headers,
        json={"course_id": "data_structures_algorithms", "modules": []},
    )
    assert recalc.status_code == 200
    overview = recalc.json()["overview"]
    assert overview["course_id"] == "data_structures_algorithms"
    if overview.get("report"):
        rpt = overview["report"]
        for key in (
            "mastery_score",
            "mastery_level",
            "weak_skills",
            "strong_skills",
            "evidence",
            "recommended_actions",
            "path_adjustment_suggestion",
            "mastery_probability",
            "mastery_trend",
            "confidence_level",
            "probability_explanation",
        ):
            assert key in rpt


def test_bkt_lite_default_no_data():
    signals = MasterySignals()
    prob, trend, confidence, explanation = compute_bkt_lite(50, signals)
    assert abs(prob - 0.5) < 0.01
    assert confidence == "low"
    assert trend == "stable"
    assert "掌握概率" in explanation


def test_bkt_lite_falling_trend():
    signals = MasterySignals(
        negative_deltas=6,
        positive_deltas=1,
        oj_failures=5,
        recent_fail_patterns=["边界", "初始化", "递归"],
        memory_event_count=7,
    )
    components = compute_component_scores(signals)
    score = compute_mastery_score(components)
    prob, trend, confidence, explanation = compute_bkt_lite(score, signals)
    assert trend == "falling"
    assert prob < 0.5
    assert "下降" in explanation


def test_bkt_lite_rising_trend():
    signals = MasterySignals(
        positive_deltas=8,
        negative_deltas=1,
        quiz_total=5,
        quiz_correct=4,
        resource_completions=3,
        oj_diagnoses=2,
        trace_with_hints=2,
        self_report_score=75,
        memory_event_count=10,
        older_fail_patterns=["边界", "指针"],
        recent_fail_patterns=[],
    )
    components = compute_component_scores(signals)
    score = compute_mastery_score(components)
    prob, trend, confidence, explanation = compute_bkt_lite(score, signals)
    assert trend == "rising"
    assert prob > 0.5
    assert "上升" in explanation


def test_bkt_lite_confidence_high():
    signals = MasterySignals(
        quiz_total=5,
        quiz_correct=3,
        oj_failures=1,
        oj_diagnoses=2,
        trace_with_hints=1,
        resource_completions=4,
        section_completions=2,
        self_report_score=70,
        positive_deltas=6,
        memory_event_count=12,
    )
    components = compute_component_scores(signals)
    score = compute_mastery_score(components)
    prob, trend, confidence, explanation = compute_bkt_lite(score, signals)
    assert confidence == "high"
    assert "置信度高" in explanation


def test_bkt_lite_confidence_low():
    signals = MasterySignals(
        quiz_total=1,
        quiz_correct=1,
        memory_event_count=1,
    )
    components = compute_component_scores(signals)
    score = compute_mastery_score(components)
    prob, trend, confidence, explanation = compute_bkt_lite(score, signals)
    assert confidence == "low"
    assert "置信度低" in explanation


def test_bkt_lite_error_reduction_boosts_probability():
    signals_no_improve = MasterySignals(
        quiz_total=3,
        quiz_correct=2,
        memory_event_count=3,
        recent_fail_patterns=["边界"],
        older_fail_patterns=["边界"],
    )
    signals_improved = MasterySignals(
        quiz_total=3,
        quiz_correct=2,
        memory_event_count=3,
        recent_fail_patterns=[],
        older_fail_patterns=["边界", "指针", "初始化"],
    )
    components_no = compute_component_scores(signals_no_improve)
    score_no = compute_mastery_score(components_no)
    prob_no, _, _, _ = compute_bkt_lite(score_no, signals_no_improve)

    components_yes = compute_component_scores(signals_improved)
    score_yes = compute_mastery_score(components_yes)
    prob_yes, _, _, _ = compute_bkt_lite(score_yes, signals_improved)

    assert prob_yes >= prob_no


def test_bkt_lite_report_fields_populated(db: Session, test_user: User):
    svc = MemoryService(db)
    for _ in range(3):
        svc.record_event(
            test_user.id,
            MemoryEventInput(
                event_type="resource_complete",
                chapter_id="ch05-tree-binary-tree",
                skill_id="tree-traversal",
                mastery_delta=1,
            ),
        )
    report = build_report(
        db,
        test_user.id,
        chapter_id="ch05-tree-binary-tree",
        persist=False,
    )
    assert 0.0 <= report.mastery_probability <= 1.0
    assert report.mastery_trend in ("rising", "stable", "falling")
    assert report.confidence_level in ("low", "medium", "high")
    assert report.probability_explanation
    assert report.mastery_score > 50
