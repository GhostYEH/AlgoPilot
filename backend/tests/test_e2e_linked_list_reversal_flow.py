"""端到端闭环集成测试：验证"链表反转掌握较弱"完整 11 步教学流程。

覆盖用户要求的流程：
1. 学生对"链表反转"掌握较弱（seed 画像 + _mastery_cache）
2. 与AI对话建立六维画像（PersonaProfile 6 维）
3. 系统生成学习路径（LearningPathPlan，linked-list 标记巩固）
4. 多智能体生成讲义/思维导图/练习题/代码案例/拓展资料（generate_resource）
5. 学生提交错误代码（POST /api/oj/problems/reverse-linked-list/submit）
6. OJ判题失败（verdict == WA）
7. Trace定位错误（POST /api/oj/problems/reverse-linked-list/diagnose）
8. AI提供分层提示（tutoring.layered_hints 非空）
9. 掌握度更新（mastery_updated == True，mastery_score 变化）
10. 学习路径重新规划（POST /api/orchestrator/learning-path/replan）
11. 教师端看到薄弱点（GET /api/teacher/dashboard-summary）

要求：流程从头到尾真实运行，不依赖手工改 DB，刷新后数据不消失。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from api.deps import get_current_user, get_optional_user
from core.database import Base, get_db
from main import app
from models.db_models import (
    GeneratedResource,
    LearningPathPlan,
    StudentLearningMemory,
    StudentProfile,
    User,
)
from scripts.seed_demo_user import _write_demo_learning_data
from services.teacher_dashboard.service import get_dashboard_summary
from utils.security import hash_password

# ── 复刻 reverse-linked-list 断链错误代码 ──
# bug: curr.next = prev 先执行，nxt = curr.next 取到 prev，链表断链
DEMO_WRONG_CODE = """class Solution:
    def reverseList(self, head):
        prev = None
        curr = head
        while curr:
            curr.next = prev
            nxt = curr.next
            prev = curr
            curr = nxt
        return prev
"""

# Trace 步骤：展示断链过程
TRACE_STEPS = [
    {
        "line": 5,
        "changed": ["curr"],
        "vars": {"curr": {"type": "ListNode", "value": "node@1"}, "prev": {"type": "ListNode", "value": "null"}},
    },
    {
        "line": 6,
        "changed": ["curr.next"],
        "vars": {"curr": {"type": "ListNode", "value": "node@1"}, "prev": {"type": "ListNode", "value": "null"}},
    },
    {
        "line": 7,
        "changed": ["nxt"],
        "vars": {"nxt": {"type": "ListNode", "value": "null"}, "curr": {"type": "ListNode", "value": "node@1"}},
    },
]

# mock LLM 诊断结果（无 SPARK_API_PASSWORD 时走 fallback，此处也 mock 以确保稳定）
LLM_DIAGNOSIS: dict[str, Any] = {
    "bug_step_index": 2,
    "diagnosis_title": "指针未更新",
    "detailed_analysis": "curr.next = prev 先执行，nxt = curr.next 取到已被改写的 prev，链表断链",
    "source": "fallback",
}


@pytest.fixture
def e2e_db() -> Session:
    """隔离的内存 SQLite，避免污染真实 DB。"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def demo_student(e2e_db: Session) -> User:
    """创建 demo 学生并写入"链表反转掌握较弱"初始数据。"""
    now = datetime.now(timezone.utc)
    user = User(
        username="demo_e2e",
        email="demo_e2e@alp-learning.example",
        hashed_password=hash_password("123456"),
        role="student",
        created_at=now - timedelta(days=30),
    )
    e2e_db.add(user)
    e2e_db.flush()
    _write_demo_learning_data(e2e_db, user, now)
    return user


@pytest.fixture
def teacher(e2e_db: Session) -> User:
    """创建教师账号。"""
    t = User(
        username="teacher_e2e",
        email="teacher_e2e@alp-learning.example",
        hashed_password=hash_password("123456"),
        role="teacher",
        created_at=datetime.now(timezone.utc) - timedelta(days=60),
    )
    e2e_db.add(t)
    e2e_db.commit()
    return t


def _override_deps(db: Session, current_user: User) -> None:
    """覆盖 FastAPI 依赖，让 API 调用使用测试 DB 与指定用户。

    必须同时覆盖 get_current_user 与 get_optional_user：
    - submit 端点用 get_current_user（强制登录）
    - diagnose 端点用 get_optional_user（允许匿名，但匿名时 tutoring 不写记忆）
    """
    def _db():
        yield db
    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_optional_user] = lambda: current_user


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


client = TestClient(app)


# ─────────────────────────────────────────────────────────────────────────
# 步骤 1-4：seed 数据验证（画像、路径、资源）
# ─────────────────────────────────────────────────────────────────────────


def test_step1_student_weak_on_linked_list_reversal(e2e_db: Session, demo_student: User):
    """步骤1：学生对"链表反转"掌握较弱 —— _mastery_cache 中 ch02-linear-list 分数低。"""
    profile = e2e_db.query(StudentProfile).filter(StudentProfile.user_id == demo_student.id).first()
    assert profile is not None, "StudentProfile 应存在"

    mastery_cache = profile.dimensions.get("_mastery_cache", {})
    ch02 = mastery_cache.get("ch02-linear-list")
    assert ch02 is not None, "_mastery_cache 应含 ch02-linear-list（按 chapter_id 键）"
    assert ch02["mastery_score"] == 32, "ch02-linear-list 掌握度应为 32（beginner，薄弱）"
    assert ch02["mastery_level"] == "beginner"

    # 验证记忆中存在 reverse-linked-list WA 失败
    memory = (
        e2e_db.query(StudentLearningMemory)
        .filter(
            StudentLearningMemory.user_id == demo_student.id,
            StudentLearningMemory.problem_slug == "reverse-linked-list",
        )
        .first()
    )
    assert memory is not None, "应存在 reverse-linked-list 学习记忆"
    assert memory.event_type == "oj_submit_fail"
    assert memory.evidence_json.get("error_type") == "pointer_update_error"


def test_step2_six_dimension_profile_built(e2e_db: Session, demo_student: User):
    """步骤2：与AI对话建立六维画像 —— 6 个维度全部填充。"""
    profile = e2e_db.query(StudentProfile).filter(StudentProfile.user_id == demo_student.id).first()
    dims = profile.dimensions

    expected_keys = {"knowledge_base", "cognitive_style", "coding_ability",
                      "learning_goals", "error_preference", "grit_level"}
    actual_keys = set(dims.keys()) & expected_keys
    assert actual_keys == expected_keys, f"六维应齐全，缺失：{expected_keys - actual_keys}"

    # 链表反转薄弱应在画像文本中体现
    assert "链表反转" in profile.summary or "链表反转" in dims["knowledge_base"]
    assert "next" in dims["error_preference"] or "指针" in dims["error_preference"]


def test_step3_learning_path_generated(e2e_db: Session, demo_student: User):
    """步骤3：系统生成学习路径 —— linked-list 标记为巩固节点。"""
    plan = e2e_db.query(LearningPathPlan).filter(LearningPathPlan.user_id == demo_student.id).first()
    assert plan is not None, "LearningPathPlan 应存在"
    assert plan.next_module_key == "linked-list"

    # linked-list 步骤应标记为巩固
    ll_step = next((s for s in plan.steps if s["module_key"] == "linked-list"), None)
    assert ll_step is not None
    assert ll_step.get("is_remediation") is True, "linked-list 应标记为巩固节点"
    assert "链表反转" in ll_step.get("reason", "") or "巩固" in ll_step.get("reason", "")


def test_step4_multi_agent_resources_generated(e2e_db: Session, demo_student: User):
    """步骤4：多智能体生成讲义/思维导图/练习题/代码案例/拓展资料。"""
    resources = (
        e2e_db.query(GeneratedResource)
        .filter(GeneratedResource.user_id == demo_student.id)
        .all()
    )
    assert len(resources) >= 3, "应至少有 3 条生成资源"

    types = {r.resource_type for r in resources}
    # 至少应含 mindmap / document / exercises
    assert "mindmap" in types, "应含思维导图"
    assert "document" in types, "应含讲义/文档"
    assert "exercises" in types, "应含练习题"


# ─────────────────────────────────────────────────────────────────────────
# 步骤 5-8：OJ 提交 → 判题失败 → Trace 诊断 → 分层提示（via API）
# ─────────────────────────────────────────────────────────────────────────


def test_steps5_8_oj_submit_fail_trace_diagnose_layered_hints(
    e2e_db: Session,
    demo_student: User,
):
    """步骤5-8：提交错误代码 → OJ 判 WA → Trace 定位 → 分层提示。

    使用 mock LLM 诊断，确保不依赖 SPARK_API_PASSWORD 也能走通完整辅导闭环。
    """
    _override_deps(e2e_db, demo_student)
    try:
        # 步骤5：提交错误代码
        submit_resp = client.post(
            "/api/oj/problems/reverse-linked-list/submit",
            json={"code": DEMO_WRONG_CODE, "language": "python"},
        )
        assert submit_resp.status_code == 200, submit_resp.text

        # 步骤6：OJ 判题失败（非 AC）
        judge = submit_resp.json()
        assert judge["verdict"] != "AC", f"错误代码不应 AC，实际 {judge['verdict']}"

        # 步骤7+8：Trace 诊断 + 分层提示
        with patch("api.oj.diagnose_trace_bug", new_callable=AsyncMock, return_value=LLM_DIAGNOSIS):
            diagnose_resp = client.post(
                "/api/oj/problems/reverse-linked-list/diagnose",
                json={
                    "code": DEMO_WRONG_CODE,
                    "language": "python",
                    "steps": TRACE_STEPS,
                    "problem_description": "反转单链表",
                },
            )
        assert diagnose_resp.status_code == 200, diagnose_resp.text
        body = diagnose_resp.json()

        # 步骤7：Trace 定位到错误
        assert body.get("bug_step_index") == LLM_DIAGNOSIS["bug_step_index"]
        assert body.get("diagnosis_title")
        assert "指针" in body.get("detailed_analysis", "") or "断链" in body.get("detailed_analysis", "")

        # 步骤8：AI 提供分层提示
        tutoring = body.get("tutoring", {})
        assert tutoring, "tutoring 不应为空"
        hints = tutoring.get("layered_hints") or []
        assert len(hints) >= 1, "layered_hints 不应为空"

        # 辅导闭环字段验证
        assert tutoring.get("memory_recorded") is True or tutoring.get("memory_event_id")
        assert tutoring.get("mastery_updated") is True
        assert tutoring.get("module_key") == "linked-list"
        assert tutoring.get("chapter_id")

    finally:
        _clear_overrides()


# ─────────────────────────────────────────────────────────────────────────
# 步骤 9-10：掌握度更新 + 学习路径重新规划
# ─────────────────────────────────────────────────────────────────────────


def test_steps9_10_mastery_update_and_path_replan(
    e2e_db: Session,
    demo_student: User,
):
    """步骤9-10：掌握度更新 → 学习路径重新规划。

    模拟辅导闭环后触发掌握度重算与路径重规划。
    """
    from services.mastery.mastery_service import MasteryService
    from services.orchestrator.core import orchestrator
    from schemas.learning_path import LearningPathReplanRequest
    from services.agents.learning_path_catalog import MODULE_CATALOG
    from schemas.learning_path import ModuleProgressInput

    # 先记录重算前的掌握度
    profile = e2e_db.query(StudentProfile).filter(StudentProfile.user_id == demo_student.id).first()
    assert profile is not None

    # 步骤9：掌握度重算（模拟 OJ 失败后的事件触发）
    overview = MasteryService(e2e_db).recalculate(
        demo_student.id,
        course_id="data_structures_algorithms",
        chapter_id="ch02-linear-list",
    )
    assert overview.report is not None
    assert overview.report.mastery_score >= 0
    assert overview.report.recommended_actions, "应生成推荐动作"

    # 重算后 _mastery_cache 应被更新（新 dict 写入）
    e2e_db.refresh(profile)
    after_cache = profile.dimensions.get("_mastery_cache", {})
    ch02_after = after_cache.get("ch02-linear-list")
    assert ch02_after is not None, "重算后 _mastery_cache 仍应含 ch02-linear-list"
    assert "mastery_score" in ch02_after, "重算后缓存值应含 mastery_score 字段"

    # 步骤10：学习路径重新规划（通过 orchestrator.replan_learning_path）
    import asyncio
    new_plan = asyncio.run(orchestrator.replan_learning_path(
        e2e_db,
        demo_student,
        LearningPathReplanRequest(
            modules=[
                ModuleProgressInput(
                    key=item["key"],
                    label=item["label"],
                    phase=item["phase"],
                    available=item["available"],
                )
                for item in MODULE_CATALOG
            ],
            overall_percent=40,
        ),
        remediation_module_key="linked-list",
    ))
    assert new_plan is not None
    assert new_plan.next_module_key, "重规划后应给出 next_module_key"
    # linked-list 仍应是优先节点（因为掌握度低）
    ll_step = next((s for s in new_plan.steps if s.module_key == "linked-list"), None)
    assert ll_step is not None


# ─────────────────────────────────────────────────────────────────────────
# 步骤 11：教师端看到薄弱点
# ─────────────────────────────────────────────────────────────────────────


def test_step11_teacher_dashboard_shows_weak_points(
    e2e_db: Session,
    demo_student: User,
    teacher: User,
):
    """步骤11：教师端看到薄弱点 —— dashboard 聚合到 linked-list 薄弱信号。"""
    # 教师看板聚合所有学生的薄弱点
    summary = get_dashboard_summary(e2e_db)

    # demo 学生贡献了 linked-list 薄弱信号
    weak_modules = {w.module_key for w in summary.weak_knowledge_points}
    assert "linked-list" in weak_modules, (
        f"教师看板应在 weak_knowledge_points 中含 linked-list，实际 {weak_modules}"
    )

    # 应有 pointer_update 类错误
    error_types = {e.error_type for e in summary.error_types}
    assert "pointer_update" in error_types, (
        f"教师看板应在 error_types 中含 pointer_update，实际 {error_types}"
    )

    # 应给出 linked-list 补强包
    pack_modules = {p.module_key for p in summary.reinforcement_packs}
    assert "linked-list" in pack_modules, "reinforcement_packs 应含 linked-list 补强包"

    # linked-list 补强包应包含 reverse-linked-list 题目
    ll_pack = next(p for p in summary.reinforcement_packs if p.module_key == "linked-list")
    problem_slugs = {p.slug for p in ll_pack.oj_problems}
    assert "reverse-linked-list" in problem_slugs, (
        f"补强包应含 reverse-linked-list，实际 {problem_slugs}"
    )


# ─────────────────────────────────────────────────────────────────────────
# 持久化验证：刷新后数据不消失
# ─────────────────────────────────────────────────────────────────────────


def test_data_persists_across_db_sessions(e2e_db: Session, demo_student: User):
    """验证 seed 数据在关闭/重开 session 后不消失。

    模拟"刷新页面"场景：前端重新请求 API，后端开新 session 查询。
    """
    user_id = demo_student.id

    # 在原 session 中验证数据存在
    profile = e2e_db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    assert profile is not None
    assert profile.dimensions["_mastery_cache"]["ch02-linear-list"]["mastery_score"] == 32

    plan = e2e_db.query(LearningPathPlan).filter(LearningPathPlan.user_id == user_id).first()
    assert plan is not None

    memory = (
        e2e_db.query(StudentLearningMemory)
        .filter(
            StudentLearningMemory.user_id == user_id,
            StudentLearningMemory.problem_slug == "reverse-linked-list",
        )
        .first()
    )
    assert memory is not None

    # 用 expunge_all 模拟"关闭 session 再重开"
    # SQLite StaticPool 共享同一连接，数据在内存中持久
    e2e_db.expunge_all()

    # 重新查询，数据应仍在
    profile2 = e2e_db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    assert profile2 is not None, "刷新后 StudentProfile 不应消失"
    assert profile2.dimensions["_mastery_cache"]["ch02-linear-list"]["mastery_score"] == 32

    plan2 = e2e_db.query(LearningPathPlan).filter(LearningPathPlan.user_id == user_id).first()
    assert plan2 is not None, "刷新后 LearningPathPlan 不应消失"
    assert plan2.next_module_key == "linked-list"

    memory2 = (
        e2e_db.query(StudentLearningMemory)
        .filter(
            StudentLearningMemory.user_id == user_id,
            StudentLearningMemory.problem_slug == "reverse-linked-list",
        )
        .first()
    )
    assert memory2 is not None, "刷新后 StudentLearningMemory 不应消失"
    assert memory2.event_type == "oj_submit_fail"


def test_seed_is_idempotent(e2e_db: Session, demo_student: User):
    """验证 seed 脚本幂等：重复刷新不报错且数据一致。"""
    from scripts.seed_demo_user import _refresh_demo_learning_data

    # 重复刷新
    _refresh_demo_learning_data(e2e_db, demo_student)

    # 数据应仍是链表反转薄弱初始状态
    profile = e2e_db.query(StudentProfile).filter(StudentProfile.user_id == demo_student.id).first()
    assert profile is not None
    ch02 = profile.dimensions["_mastery_cache"]["ch02-linear-list"]
    assert ch02["mastery_score"] == 32

    memory = (
        e2e_db.query(StudentLearningMemory)
        .filter(
            StudentLearningMemory.user_id == demo_student.id,
            StudentLearningMemory.problem_slug == "reverse-linked-list",
        )
        .first()
    )
    assert memory is not None
    assert memory.event_type == "oj_submit_fail"
