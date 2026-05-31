"""OJ Trace 智能辅导闭环：错因分类 · Memory · Mastery · 题目上下文。"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.orm import Session

from core.database import SessionLocal
from models.db_models import StudentProfile, User
from services.agents.persona_learning import (
    apply_oj_diagnosis_patch,
    dimensions_for_error_type,
)
from services.mastery.mastery_service import MasteryService
from services.memory.memory_service import MemoryService
from services.oj.error_patterns import classify_error_type
from services.oj.problem_context import resolve_problem_context
from services.oj.problem_store import get_public_problem
from services.oj.tutoring_pipeline import apply_oj_tutoring
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
    name = f"ojt_{uuid.uuid4().hex[:10]}"
    user = User(username=name, email=f"{name}@test.local", hashed_password=hash_password("pass"))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_classify_dp_initialization_error():
    err = classify_error_type(
        slug="unique-paths",
        title="不同路径",
        analysis="dp[0][0] 未初始化，边界条件处理错误",
        trace_summary="Step 2：初始化遗漏",
        edge_category="edge",
        verdict="WA",
    )
    assert err in ("initialization_error", "state_transition_error", "boundary_condition_error")


def test_classify_dp_state_transition():
    err = classify_error_type(
        slug="climbing-stairs",
        title="爬楼梯",
        analysis="状态转移方程写反，dp[i] 依赖方向错误",
        trace_summary="Step 4：转移方向",
        verdict="WA",
    )
    assert err in ("state_transition_error", "initialization_error")


def test_classify_linked_list_pointer_error():
    err = classify_error_type(
        slug="reverse-linked-list",
        title="反转链表",
        analysis="curr.next 未更新，指针停滞导致断链",
        trace_summary="Step 3：next 指针未移动",
        verdict="WA",
    )
    assert err == "pointer_update_error"


def test_problem_context_maps_dp_slug():
    ctx = resolve_problem_context("unique-paths", title="不同路径")
    assert ctx["module_key"] == "dp"
    assert ctx["course_id"] == "data_structures_algorithms"


def test_problem_context_maps_linked_list_slug():
    ctx = resolve_problem_context("reverse-linked-list", title="反转链表")
    assert ctx["module_key"] == "linked-list"


def test_public_problem_includes_course_fields():
    try:
        detail = get_public_problem("reverse-linked-list")
    except Exception:
        pytest.skip("reverse-linked-list 未在 catalog 中")
    assert detail.get("module_key") == "linked-list"
    assert "course_id" in detail


def test_apply_tutoring_writes_memory(db: Session, test_user: User):
    problem = {"title": "反转链表", "description": "反转单链表"}
    tutoring = apply_oj_tutoring(
        db,
        test_user,
        slug="reverse-linked-list",
        problem=problem,
        bug_step_index=2,
        diagnosis_title="指针未更新",
        detailed_analysis="curr.next 未保存，链表断链",
        edge_verdict="WA",
        code="while curr: curr.next = prev",
    )
    assert tutoring.error_pattern == "pointer_update_error"
    assert tutoring.matched_skill is not None
    assert tutoring.memory_event_id is not None
    assert tutoring.memory_recorded is True
    assert tutoring.persona_updated is True
    assert tutoring.profile_updated is True
    assert tutoring.profile_updated == tutoring.persona_updated
    assert tutoring.persona_patch_summary
    assert len(tutoring.layered_hints) >= 1
    assert len(tutoring.recommended_resources) >= 1

    recent = MemoryService(db).list_recent(test_user.id, limit=5)
    assert any(m.event_type == "oj_diagnosis" for m in recent)


def test_apply_tutoring_updates_mastery(db: Session, test_user: User):
    tutoring = apply_oj_tutoring(
        db,
        test_user,
        slug="unique-paths",
        problem={"title": "不同路径"},
        bug_step_index=1,
        diagnosis_title="dp 边界未初始化",
        detailed_analysis="首行首列 dp 初始化错误，边界条件遗漏",
        edge_verdict="WA",
    )
    assert tutoring.error_pattern in (
        "initialization_error",
        "state_transition_error",
        "boundary_condition_error",
    )
    assert tutoring.mastery_update_summary
    assert tutoring.mastery_updated is True

    overview = MasteryService(db).recalculate(
        test_user.id,
        course_id="data_structures_algorithms",
        chapter_id="ch11-dynamic-programming",
    )
    report = overview.report
    assert report is not None
    sources = [e.source for e in report.evidence]
    assert any("oj_diagnosis" in (s or "") or "memory" in (s or "") for s in sources)
    assert report.recommended_actions


def test_state_transition_error_maps_to_knowledge_and_cognitive():
    dims = dimensions_for_error_type("state_transition_error")
    assert "knowledge_base" in dims
    assert "cognitive_style" in dims


def test_apply_oj_diagnosis_patch_updates_dimensions(db: Session, test_user: User):
    result = apply_oj_diagnosis_patch(
        db,
        test_user.id,
        problem_slug="climbing-stairs",
        error_type="state_transition_error",
        error_pattern_label="状态转移错误",
        trace_summary="Step 4：dp 转移方向写反",
        module_key="dp",
        chapter_id="ch11-dynamic-programming",
    )
    assert result.updated is True
    assert "状态转移" in result.summary or "知识基础" in result.summary

    row = db.get(StudentProfile, test_user.id)
    assert row is not None
    dims = row.dimensions or {}
    assert dims.get("knowledge_base")
    assert dims.get("cognitive_style")


def test_apply_tutoring_patches_persona_on_state_transition(db: Session, test_user: User):
    tutoring = apply_oj_tutoring(
        db,
        test_user,
        slug="climbing-stairs",
        problem={"title": "爬楼梯"},
        bug_step_index=3,
        diagnosis_title="状态转移方程错误",
        detailed_analysis="dp[i] 依赖方向写反，状态转移方程错误",
        edge_verdict="WA",
    )
    assert tutoring.error_pattern in ("state_transition_error", "initialization_error")
    assert tutoring.persona_patch_summary
    assert tutoring.persona_updated is True
    assert tutoring.profile_updated is True
    assert tutoring.profile_updated == tutoring.persona_updated

    row = db.get(StudentProfile, test_user.id)
    assert row is not None
    dims = row.dimensions or {}
    if tutoring.error_pattern == "state_transition_error":
        assert dims.get("knowledge_base")
        assert dims.get("cognitive_style")


def test_persona_patch_failure_does_not_break_tutoring(db: Session, test_user: User, monkeypatch):
    def _boom(*_a, **_k):
        raise RuntimeError("patch unavailable")

    monkeypatch.setattr(
        "services.agents.persona_learning.apply_oj_diagnosis_patch",
        _boom,
    )
    tutoring = apply_oj_tutoring(
        db,
        test_user,
        slug="reverse-linked-list",
        problem={"title": "反转链表"},
        bug_step_index=1,
        diagnosis_title="指针未更新",
        detailed_analysis="curr.next 未保存",
        edge_verdict="WA",
    )
    assert tutoring.memory_event_id is not None
    assert tutoring.memory_recorded is True
    assert tutoring.persona_updated is False
    assert tutoring.profile_updated is False
    assert "patch" in (tutoring.persona_patch_warning or "").lower() or tutoring.persona_patch_warning
    assert tutoring.matched_skill is not None


def test_memory_recorded_without_persona_updated(db: Session, test_user: User, monkeypatch):
    from services.agents.persona_learning import OjPersonaPatchResult

    monkeypatch.setattr(
        "services.agents.persona_learning.apply_oj_diagnosis_patch",
        lambda *_a, **_k: OjPersonaPatchResult(updated=False, summary="", warning="画像 patch 跳过"),
    )
    tutoring = apply_oj_tutoring(
        db,
        test_user,
        slug="reverse-linked-list",
        problem={"title": "反转链表"},
        bug_step_index=1,
        diagnosis_title="指针未更新",
        detailed_analysis="curr.next 未保存",
        edge_verdict="WA",
    )
    assert tutoring.memory_recorded is True
    assert tutoring.persona_updated is False
    assert tutoring.profile_updated is False
    assert tutoring.profile_updated == tutoring.persona_updated
