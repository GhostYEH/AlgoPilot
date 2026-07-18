"""学习路径 replan API 与掌握度/薄弱点驱动调整测试。"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.database import SessionLocal
from main import app
from models.db_models import LearningPathPlan, StudentProfile, User
from schemas.learning_path import LearningPathReplanRequest, ModuleProgressInput
from services.agents.learning_path import LearningPathAgent, _heuristic_plan
from services.agents.learning_path_catalog import MODULE_CATALOG
from services.mastery.mastery_service import MasteryService, get_cached_mastery_by_chapter
from services.memory.memory_service import MemoryService
from services.memory.schemas import MemoryEventInput
from services.orchestrator.core import (
    Orchestrator,
    _path_plan_response,
    migrate_legacy_learning_path_plans,
)
from utils.security import hash_password

client = TestClient(app)
_orchestrator = Orchestrator()


def _default_modules() -> list[ModuleProgressInput]:
    return [
        ModuleProgressInput(
            key=m["key"],
            label=m["label"],
            phase=m["phase"],
            available=m["available"],
            percent=0,
            done_count=0,
            total_count=5,
        )
        for m in MODULE_CATALOG
    ]


def _replan_request(**kwargs) -> LearningPathReplanRequest:
    return LearningPathReplanRequest(
        modules=kwargs.pop("modules", _default_modules()),
        overall_percent=kwargs.pop("overall_percent", 8),
        **kwargs,
    )


@pytest.fixture
def db() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user(db: Session) -> User:
    name = f"replan_{uuid.uuid4().hex[:10]}"
    user = User(username=name, email=f"{name}@example.com", hashed_password=hash_password("pass"))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    reg = client.post(
        "/api/auth/register",
        json={
            "username": f"hdr_{uuid.uuid4().hex[:8]}",
            "password": "pass123",
            "email": f"hdr_{uuid.uuid4().hex[:8]}@example.com",
        },
    )
    assert reg.status_code == 200
    return {"Authorization": f"Bearer {reg.json()['access_token']}"}


def _seed_low_mastery(
    db: Session,
    user_id: int,
    *,
    chapter_id: str,
    skill_id: str,
    pattern: str,
    count: int = 5,
) -> None:
    svc = MemoryService(db)
    for i in range(count):
        svc.record_event(
            user_id,
            MemoryEventInput(
                event_type="oj_submit_fail",
                chapter_id=chapter_id,
                skill_id=skill_id,
                problem_slug=f"prob-{chapter_id}-{i}",
                observed_error_pattern=pattern,
                mastery_delta=-1,
                evidence_json={"verdict": "WA"},
            ),
        )
    MasteryService(db).recalculate(user_id, chapter_id=chapter_id)


def _set_weak_profile(db: Session, user: User, *, summary: str) -> None:
    row = db.get(StudentProfile, user.id)
    if row is None:
        row = StudentProfile(user_id=user.id, summary=summary, dimensions={})
        db.add(row)
    else:
        row.summary = summary
    db.commit()


def test_replan_api_returns_ordered_keys(auth_headers: dict[str, str]):
    resp = client.post(
        "/api/orchestrator/learning-path/replan",
        headers=auth_headers,
        json={
            "overall_percent": 10,
            "modules": [m.model_dump() for m in _default_modules()],
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body.get("ordered_keys")
    assert len(body["ordered_keys"]) >= 8
    assert body.get("rationale")
    assert body.get("steps")
    assert body.get("agent_name")


@pytest.mark.parametrize(
    "chapter_id, module_key, skill_id, pattern",
    [
        ("ch11-dynamic-programming", "dp", "dp-state-design", "dp 状态转移边界错误"),
        ("ch06-graph", "graph", "graph-bfs-dfs", "BFS visited 未标记重复入队"),
    ],
)
def test_low_mastery_reorders_weak_chapter(
    db: Session,
    test_user: User,
    chapter_id: str,
    module_key: str,
    skill_id: str,
    pattern: str,
):
    """掌握度 <45 时，相关模块在启发式路径中提前。"""
    request = _replan_request()
    baseline = _heuristic_plan("", request, {}, mastery_by_chapter={})
    baseline_idx = baseline["ordered_keys"].index(module_key)

    _seed_low_mastery(
        db,
        test_user.id,
        chapter_id=chapter_id,
        skill_id=skill_id,
        pattern=pattern,
    )
    cached = get_cached_mastery_by_chapter(db, test_user.id)
    assert cached.get(chapter_id, 100) < 45, f"{chapter_id} mastery 应低于 45"

    adjusted = _heuristic_plan(
        "",
        request,
        {},
        mastery_by_chapter={chapter_id: cached[chapter_id]},
    )
    adjusted_idx = adjusted["ordered_keys"].index(module_key)
    assert adjusted_idx < baseline_idx, f"{module_key} 应因低掌握度提前"

    report = MasteryService(db).recalculate(test_user.id, chapter_id=chapter_id).report
    assert report is not None
    assert report.mastery_score < 45
    assert report.recommended_actions
    assert report.path_adjustment_suggestion
    joined = " ".join(report.recommended_actions) + report.path_adjustment_suggestion
    assert "掌握" in joined or "巩固" in joined or module_key in joined.lower()


def test_weak_skills_in_profile_prioritize_modules(db: Session, test_user: User):
    """画像摘要中的薄弱模块会影响推荐顺序。"""
    request = _replan_request()
    neutral = _heuristic_plan("摘要：学习进度正常", request, {})

    _set_weak_profile(
        db,
        test_user,
        summary="摘要：动态规划（dp）掌握薄弱，图论仍需巩固，建议先强化 dp-state-design",
    )
    weak_block = f"摘要：{test_user.id} 动态规划薄弱 dp 图论 graph"
    weak = _heuristic_plan(weak_block, request, {})

    dp_neutral = neutral["ordered_keys"].index("dp")
    dp_weak = weak["ordered_keys"].index("dp")
    assert dp_weak <= dp_neutral

    rationale = weak.get("rationale") or ""
    assert "薄弱" in rationale or any(
        "薄弱" in (s.get("reason") or "") or "优先" in (s.get("reason") or "")
        for s in weak.get("steps") or []
    )


@pytest.mark.asyncio
async def test_remediation_insertion_for_dp_struggle(db: Session, test_user: User):
    """受挫降级：在路径前插入巩固节点。"""
    body = _replan_request()
    plan = await _orchestrator.replan_learning_path(
        db,
        test_user,
        body,
        remediation_module_key="array",
    )
    assert plan.remediation_inserted is True
    assert plan.ordered_keys[0] == "array"
    remed_step = next(s for s in plan.steps if s.module_key == "array")
    assert remed_step.is_remediation is True
    assert remed_step.reason
    assert plan.summary


def test_replan_api_without_llm_key(auth_headers: dict[str, str]):
    """无 LLM Key 时 replan 仍返回启发式路径。"""
    with patch(
        "services.llm.client.chat_completion",
        new_callable=AsyncMock,
        side_effect=RuntimeError("no api key"),
    ):
        resp = client.post(
            "/api/orchestrator/learning-path/replan",
            headers=auth_headers,
            json={
                "overall_percent": 5,
                "modules": [m.model_dump() for m in _default_modules()],
            },
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body.get("ordered_keys")
    assert body.get("summary")
    assert body.get("rationale")
    assert "拓扑" in body["rationale"] or "依赖" in body["rationale"] or body["summary"]


@pytest.mark.asyncio
async def test_learning_path_agent_plan_heuristic_without_llm(db: Session, test_user: User):
    """LearningPathAgent.plan 在 LLM 失败时降级为启发式结果。"""
    agent = LearningPathAgent()
    body = _replan_request()

    with patch(
        "services.llm.client.chat_completion",
        new_callable=AsyncMock,
        side_effect=RuntimeError("no api key"),
    ):
        plan = await agent.plan(
            profile_block="摘要：动态规划薄弱",
            request=body,
            dimension_scores={"knowledge_base": 4, "coding_ability": 4},
            mastery_by_chapter={"ch11-dynamic-programming": 38},
        )

    assert plan.get("ordered_keys")
    assert plan.get("steps")
    assert plan.get("summary")
    assert "dp" in plan["ordered_keys"]


def test_mastery_driven_replan_via_api(db: Session, test_user: User):
    """API replan 结合已缓存的低掌握度章节调整路径。"""
    _seed_low_mastery(
        db,
        test_user.id,
        chapter_id="ch11-dynamic-programming",
        skill_id="dp-state-design",
        pattern="初始化错误",
    )

    login = client.post(
        "/api/auth/login",
        json={"username": test_user.username, "password": "pass"},
    )
    if login.status_code != 200:
        reg = client.post(
            "/api/auth/register",
            json={
                "username": test_user.username,
                "password": "pass",
                "email": test_user.email,
            },
        )
        assert reg.status_code == 200, reg.text
        token = reg.json()["access_token"]
    else:
        token = login.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post(
        "/api/orchestrator/learning-path/replan",
        headers=headers,
        json={
            "overall_percent": 6,
            "modules": [m.model_dump() for m in _default_modules()],
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "dp" in body["ordered_keys"]

    overview = MasteryService(db).recalculate(
        test_user.id,
        chapter_id="ch11-dynamic-programming",
    )
    assert overview.report
    assert overview.report.weak_skills or overview.report.mastery_score < 50
    evidence_text = " ".join(
        [overview.report.path_adjustment_suggestion]
        + overview.report.recommended_actions
        + [e.detail for e in overview.report.evidence]
    )
    assert (
        str(overview.report.mastery_score) in evidence_text
        or "掌握" in evidence_text
        or "dp" in " ".join(overview.report.weak_skills).lower()
    )


# --- 旧格式数据兼容与启动迁移 ---


_LEGACY_STEPS = [
    {"key": "array", "label": "数组", "status": "done", "phase": "foundation"},
    {"key": "linked-list", "label": "链表", "status": "in_progress", "phase": "foundation"},
    {"key": "dp", "label": "动态规划", "status": "locked", "phase": "advanced"},
]


def _seed_legacy_plan(db: Session, user: User) -> LearningPathPlan:
    """写入一份旧格式（key/label/status，无 module_key/rank）的学习路径计划。"""
    row = db.get(LearningPathPlan, user.id)
    if row is None:
        row = LearningPathPlan(user_id=user.id)
        db.add(row)
    row.summary = "旧格式测试计划"
    row.ordered_keys = ["array", "linked-list", "dp"]
    row.steps = [dict(s) for s in _LEGACY_STEPS]
    row.next_module_key = "linked-list"
    db.commit()
    db.refresh(row)
    return row


def test_path_plan_response_handles_legacy_steps(db: Session, test_user: User):
    """旧格式 steps 存库时，_path_plan_response 不应抛 ValidationError。"""
    row = _seed_legacy_plan(db, test_user)
    # 关键断言：不抛异常
    resp = _path_plan_response(row)
    assert len(resp.steps) == 3
    assert resp.steps[0].module_key == "array"
    assert resp.steps[1].module_key == "linked-list"
    assert resp.steps[2].module_key == "dp"
    # rank 按序号补全
    assert resp.steps[0].rank == 1
    assert resp.steps[2].rank == 3
    assert resp.next_module_key == "linked-list"


def test_migrate_legacy_learning_path_plans_converts_and_is_idempotent(
    db: Session, test_user: User
):
    """启动迁移把旧格式 steps 升级为新格式，且幂等。"""
    _seed_legacy_plan(db, test_user)

    migrated = migrate_legacy_learning_path_plans(db)
    assert migrated >= 1

    db.expire_all()
    row = db.get(LearningPathPlan, test_user.id)
    for step in row.steps:
        assert "module_key" in step
        assert "rank" in step
    assert row.steps[0]["module_key"] == "array"

    # 再次迁移应返回 0（已全部为新格式）
    migrated_again = migrate_legacy_learning_path_plans(db)
    assert migrated_again == 0


def test_get_learning_path_plan_endpoint_with_legacy_data(db: Session, test_user: User):
    """端到端：旧格式数据下 GET /learning-path/plan 不再返回 500。"""
    _seed_legacy_plan(db, test_user)

    login = client.post(
        "/api/auth/login",
        json={"username": test_user.username, "password": "pass"},
    )
    if login.status_code != 200:
        reg = client.post(
            "/api/auth/register",
            json={
                "username": test_user.username,
                "password": "pass",
                "email": test_user.email,
            },
        )
        assert reg.status_code == 200, reg.text
        token = reg.json()["access_token"]
    else:
        token = login.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/orchestrator/learning-path/plan", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()["plan"]
    assert body is not None
    assert len(body["steps"]) == 3
    assert body["steps"][0]["module_key"] == "array"
