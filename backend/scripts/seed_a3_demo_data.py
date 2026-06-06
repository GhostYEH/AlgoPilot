"""A3 比赛演示数据预热：幂等写入 demo 用户画像、记忆、路径、掌握度与模板资源。

运行（仓库根目录或 backend 目录均可）：
    python backend/scripts/seed_a3_demo_data.py
    cd backend && python -m scripts.seed_a3_demo_data

不依赖 LLM Key；仅更新 username=a3_demo 的演示账号，不触碰其他用户。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.exc import IntegrityError  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

import models.db_models  # noqa: F401,E402
from core.database import Base, SessionLocal, engine  # noqa: E402
from models.db_models import (  # noqa: E402
    GeneratedResource,
    LearningPathPlan,
    LearningProgress,
    StudentLearningMemory,
    StudentProfile,
    User,
)
from schemas.learning_path import LearningPathReplanRequest, ModuleProgressInput  # noqa: E402
from services.agents.learning_path import (  # noqa: E402
    _heuristic_plan,
    _insert_remediation_step,
)
from services.agents.learning_path_catalog import MODULE_CATALOG  # noqa: E402
from services.agents.template_fallback import (  # noqa: E402
    GENERATED_BY as FALLBACK_AGENT,
    generate_fallback_resource,
)
from services.knowledge.retriever import retriever  # noqa: E402
from services.memory.memory_service import (  # noqa: E402
    MemoryService,
    record_oj_diagnosis,
    record_oj_submit_failure,
    record_evaluation_struggle,
)
from services.memory.schemas import MemoryEventInput  # noqa: E402
from services.memory.memory_summarizer import (  # noqa: E402
    build_dimension_evidence,
    build_recent_evidence_items,
    build_update_reason,
)
from services.mastery.mastery_service import MasteryService  # noqa: E402
from services.orchestrator.core import _format_profile_block  # noqa: E402
from services.verification.builder import build_verification_result, chunks_to_grounded  # noqa: E402
from utils.security import hash_password  # noqa: E402

DEMO_USERNAME = "a3_demo"
DEMO_EMAIL = "a3_demo@example.local"
DEMO_PASSWORD = "Demo1234!"
DEMO_SEED_SOURCE = "a3_demo_seed"
COURSE_ID = "data_structures_algorithms"
DP_CHAPTER_ID = "ch11-dynamic-programming"
GRAPH_CHAPTER_ID = "ch06-graph"
LINKED_LIST_CHAPTER_ID = "ch02-linear-list"
STACK_QUEUE_CHAPTER_ID = "ch03-stack-queue"
BINARY_TREE_CHAPTER_ID = "ch05-tree-binary-tree"

_PROFILE_TEMPLATE_PATH = (
    BACKEND_ROOT / "knowledge_base" / "student_profiles" / "oj_struggling.json"
)

_DEMO_RESOURCES: list[tuple[str, str, str]] = [
    ("document", "动态规划状态设计与转移方程", "dp"),
    ("mindmap", "图论 BFS 与 DFS 知识图谱", "graph"),
    ("exercises", "链表指针与边界练习", "linked-list"),
    ("code_case", "栈与队列实操案例", "stack-queue"),
    ("trace_animation", "二叉树遍历轨迹动画", "binary-tree"),
    ("reading", "图论算法拓展阅读", "graph"),
]

_MODULE_TO_CHAPTER_ID: dict[str, str] = {
    "dp": DP_CHAPTER_ID,
    "graph": GRAPH_CHAPTER_ID,
    "linked-list": LINKED_LIST_CHAPTER_ID,
    "stack-queue": STACK_QUEUE_CHAPTER_ID,
    "binary-tree": BINARY_TREE_CHAPTER_ID,
    "array": LINKED_LIST_CHAPTER_ID,
}


@dataclass
class SeedResult:
    user_id: int
    username: str
    course_id: str
    memories_count: int
    resources_count: int
    mastery_report_id: str
    mastery_score: int
    recommended_next_route: str
    next_module_key: str
    evaluation_count: int = 0
    replan_count: int = 0
    password: str = DEMO_PASSWORD

    def as_dict(self) -> dict[str, object]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "course_id": self.course_id,
            "memories_count": self.memories_count,
            "resources_count": self.resources_count,
            "mastery_report_id": self.mastery_report_id,
            "mastery_score": self.mastery_score,
            "recommended_next_route": self.recommended_next_route,
            "next_module_key": self.next_module_key,
            "evaluation_count": self.evaluation_count,
            "replan_count": self.replan_count,
            "password": self.password,
            "demo": True,
            "source": DEMO_SEED_SOURCE,
        }


def _demo_marker() -> dict[str, object]:
    return {"demo": True, "source": DEMO_SEED_SOURCE}


def _default_modules() -> list[ModuleProgressInput]:
    return [
        ModuleProgressInput(
            key=m["key"],
            label=m["label"],
            phase=m["phase"],
            available=m["available"],
            percent=12 if m["key"] in ("array", "linked-list") else 0,
            done_count=1 if m["key"] in ("array", "linked-list") else 0,
            total_count=5,
        )
        for m in MODULE_CATALOG
    ]


def _replan_request() -> LearningPathReplanRequest:
    return LearningPathReplanRequest(modules=_default_modules(), overall_percent=12)


def ensure_demo_user(db: Session) -> User:
    user = db.scalar(select(User).where(User.username == DEMO_USERNAME))
    if user is not None:
        if user.email != DEMO_EMAIL:
            user.email = DEMO_EMAIL
            db.commit()
        return user

    user = User(
        username=DEMO_USERNAME,
        email=DEMO_EMAIL,
        hashed_password=hash_password(DEMO_PASSWORD),
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        found = db.scalar(select(User).where(User.username == DEMO_USERNAME))
        if found is None:
            raise
        return found


def clear_demo_seed_artifacts(db: Session, user_id: int) -> tuple[int, int]:
    """仅删除 demo 种子写入的记忆与资源，保留用户与其他数据。"""
    mem_deleted = 0
    for row in db.scalars(
        select(StudentLearningMemory).where(StudentLearningMemory.user_id == user_id)
    ):
        ev = row.evidence_json or {}
        if ev.get("source") == DEMO_SEED_SOURCE or ev.get("demo") is True:
            db.delete(row)
            mem_deleted += 1

    res_deleted = 0
    for row in db.scalars(
        select(GeneratedResource).where(GeneratedResource.user_id == user_id)
    ):
        meta = row.meta or {}
        if meta.get("source") == DEMO_SEED_SOURCE or meta.get("demo") is True:
            db.delete(row)
            res_deleted += 1

    profile_row = db.get(StudentProfile, user_id)
    if profile_row is not None and profile_row.dimensions:
        payload = dict(profile_row.dimensions)
        hist = list(payload.get("_evaluation_history") or [])
        cleaned = [
            h for h in hist
            if not (isinstance(h, dict) and (h.get("source") == DEMO_SEED_SOURCE or h.get("demo") is True))
        ]
        if len(cleaned) != len(hist):
            payload["_evaluation_history"] = cleaned
            profile_row.dimensions = payload

    plan_row = db.get(LearningPathPlan, user_id)
    if plan_row is not None and plan_row.progress_snapshot:
        snap = dict(plan_row.progress_snapshot)
        if snap.get("replan_triggered_by_evaluation") is True and snap.get("demo") is True:
            snap.pop("replan_triggered_by_evaluation", None)
            plan_row.progress_snapshot = snap

    db.commit()
    return mem_deleted, res_deleted


def seed_persona(db: Session, user: User) -> StudentProfile:
    template = json.loads(_PROFILE_TEMPLATE_PATH.read_text(encoding="utf-8"))
    dims = dict(template.get("dimensions") or {})
    payload = dict(dims)
    payload["_dimension_scores"] = {
        "knowledge_base": 5,
        "cognitive_style": 6,
        "coding_ability": 4,
        "learning_goals": 7,
        "error_preference": 5,
        "grit_level": 3,
    }
    payload["_confidence"] = {k: "explicit" for k in dims}
    payload["_coverage_missing"] = ["cognitive_style"]
    payload["_update_reason"] = "A3 demo seed：根据 OJ 受挫与 DP/图薄弱记录初始化画像"
    payload["_generated_by"] = DEMO_SEED_SOURCE
    payload["_persona_fallback"] = False
    payload.update(_demo_marker())

    chat_history = [
        {
            "role": "user",
            "content": "我是大二计科，链表和动态规划比较薄弱，想准备蓝桥杯。",
        },
        {
            "role": "assistant",
            "content": "收到！你目前在链表指针和 DP 状态设计上容易受挫，我们会优先巩固基础。",
        },
        {
            "role": "user",
            "content": "reverse-linked-list 经常 WA，图论 BFS 也不太会写。",
        },
    ]

    row = db.get(StudentProfile, user.id)
    if row is None:
        row = StudentProfile(user_id=user.id)
        db.add(row)
    row.summary = str(
        template.get("summary")
        or "A3 演示学生：知识基础偏弱、视觉化学习偏好明显，OJ 连续受挫后需要降级巩固与 Trace 辅导。"
    )
    row.dimensions = payload
    row.chat_history = chat_history
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return row


def _tag_latest_memory(db: Session, user_id: int, marker: dict[str, object]) -> None:
    last = db.scalars(
        select(StudentLearningMemory)
        .where(StudentLearningMemory.user_id == user_id)
        .order_by(StudentLearningMemory.id.desc())
        .limit(1)
    ).first()
    if last is None:
        return
    ev = dict(last.evidence_json or {})
    ev.update(marker)
    last.evidence_json = ev
    db.commit()


def seed_memories(db: Session, user_id: int) -> int:
    marker = _demo_marker()

    record_oj_submit_failure(
        db,
        user_id,
        problem_slug="reverse-linked-list",
        verdict="WA",
        message="链表反转时 next 指针未正确保存，尾结点未置空",
        module_key="linked-list",
        consecutive_failures=2,
    )
    _tag_latest_memory(db, user_id, marker)

    record_oj_diagnosis(
        db,
        user_id,
        problem_slug="reverse-linked-list",
        module_key="linked-list",
        skill_id="linear-list-operation",
        edge_category="pointer",
        error_type="pointer_update_error",
        diagnosis={
            "bug_step_index": 3,
            "diagnosis_title": "指针更新顺序错误",
            "detailed_analysis": "在反转链表时未保存 next 就覆盖 curr.next，导致链断裂。",
            "source": "fallback",
        },
    )
    _tag_latest_memory(db, user_id, marker)

    svc = MemoryService(db)
    for i in range(4):
        svc.record_event(
            user_id,
            MemoryEventInput(
                course_id=COURSE_ID,
                chapter_id=DP_CHAPTER_ID,
                skill_id="dp-state-design",
                problem_slug=f"demo-dp-grid-{i}",
                event_type="oj_submit_fail",
                observed_error_pattern="DP 状态转移方程遗漏边界初始化",
                failed_strategy="WA",
                mastery_delta=-1,
                evidence_json={
                    "verdict": "WA",
                    "module_key": "dp",
                    "persona_dimension": "coding_ability",
                    **marker,
                },
            ),
        )

    for i in range(2):
        svc.record_event(
            user_id,
            MemoryEventInput(
                course_id=COURSE_ID,
                chapter_id=GRAPH_CHAPTER_ID,
                skill_id="graph-bfs-dfs",
                problem_slug=f"demo-graph-bfs-{i}",
                event_type="oj_submit_fail",
                observed_error_pattern="图 BFS 队列未正确入队或 visited 遗漏",
                failed_strategy="TLE",
                mastery_delta=-1,
                evidence_json={
                    "verdict": "TLE",
                    "module_key": "graph",
                    "persona_dimension": "coding_ability",
                    **marker,
                },
            ),
        )

    svc.record_event(
        user_id,
        MemoryEventInput(
            course_id=COURSE_ID,
            chapter_id=LINKED_LIST_CHAPTER_ID,
            skill_id="linear-list-operation",
            problem_slug="valid-parentheses",
            event_type="oj_submit_success",
            observed_error_pattern="",
            trace_summary="AC：使用栈维护左括号，遇到右括号时检查栈顶匹配关系。",
            successful_hint="先处理空栈边界，再维护循环不变量：栈中只保存尚未匹配的左括号。",
            mastery_delta=1,
            evidence_json={
                "verdict": "AC",
                "module_key": "stack-queue",
                "persona_dimension": "coding_ability",
                **marker,
            },
        ),
    )

    svc.record_event(
        user_id,
        MemoryEventInput(
            course_id=COURSE_ID,
            chapter_id=DP_CHAPTER_ID,
            skill_id="dp-state-design",
            problem_slug="climbing-stairs",
            event_type="oj_submit_success",
            observed_error_pattern="",
            trace_summary="AC：正确写出 dp[i]=dp[i-1]+dp[i-2]，边界 dp[1]=1, dp[2]=2。",
            successful_hint="从最小子问题开始填表，先确认边界再写转移。",
            mastery_delta=1,
            evidence_json={
                "verdict": "AC",
                "module_key": "dp",
                "persona_dimension": "coding_ability",
                **marker,
            },
        ),
    )

    svc.record_event(
        user_id,
        MemoryEventInput(
            course_id=COURSE_ID,
            chapter_id=DP_CHAPTER_ID,
            skill_id="dp-state-design",
            event_type="trace_diagnosis",
            trace_summary="Trace 诊断：dp-grid-0 在 step 3 处状态转移遗漏边界初始化，dp[0] 未设为 1。",
            successful_hint="检查 dp 数组初始化，确保 dp[0]=1 作为递推起点。",
            mastery_delta=0,
            evidence_json={
                "module_key": "dp",
                "diagnosis_source": "trace",
                **marker,
            },
        ),
    )

    svc.record_event(
        user_id,
        MemoryEventInput(
            course_id=COURSE_ID,
            chapter_id=DP_CHAPTER_ID,
            skill_id="dp-state-design",
            event_type="resource_complete",
            trace_summary="完成资源：动态规划状态设计与转移方程（document）",
            successful_hint="状态转移方程的边界条件是关键",
            mastery_delta=1,
            evidence_json={
                "resource_type": "document",
                "module_key": "dp",
                **marker,
            },
        ),
    )

    svc.record_event(
        user_id,
        MemoryEventInput(
            course_id=COURSE_ID,
            chapter_id=GRAPH_CHAPTER_ID,
            skill_id="graph-bfs-dfs",
            event_type="resource_complete",
            trace_summary="完成资源：图论 BFS 与 DFS 知识图谱（mindmap）",
            successful_hint="BFS 用队列逐层扩展，DFS 用栈/递归深入",
            mastery_delta=1,
            evidence_json={
                "resource_type": "mindmap",
                "module_key": "graph",
                **marker,
            },
        ),
    )

    svc.record_event(
        user_id,
        MemoryEventInput(
            course_id=COURSE_ID,
            chapter_id=LINKED_LIST_CHAPTER_ID,
            skill_id="linear-list-operation",
            event_type="resource_complete",
            trace_summary="完成资源：链表指针与边界练习（exercises）",
            successful_hint="画图跟踪指针变化是链表题的核心技巧",
            mastery_delta=1,
            evidence_json={
                "resource_type": "exercises",
                "module_key": "linked-list",
                **marker,
            },
        ),
    )

    record_evaluation_struggle(
        db,
        user_id,
        module_key="dp",
        knowledge_point="动态规划",
        verdict="WA",
        error_pattern="连续 3 次 DP 状态设计错误",
        consecutive_failures=3,
        skill_ids=["dp-state-design"],
    )
    _tag_latest_memory(db, user_id, marker)

    svc.record_event(
        user_id,
        MemoryEventInput(
            course_id=COURSE_ID,
            chapter_id=DP_CHAPTER_ID,
            skill_id="dp-state-design",
            event_type="path_adjusted",
            observed_error_pattern="EvaluationAgent 检测到 DP 连续受挫后触发路径重排",
            trace_summary="LearningPathAgent 已在 dp 前插入 array 降级巩固节点。",
            mastery_delta=0,
            evidence_json={
                "module_key": "dp",
                "remediation_module_key": "array",
                "trigger": "evaluation",
                **marker,
            },
        ),
    )

    return len(
        [
            r
            for r in db.scalars(
                select(StudentLearningMemory).where(
                    StudentLearningMemory.user_id == user_id
                )
            )
            if (r.evidence_json or {}).get("source") == DEMO_SEED_SOURCE
        ]
    )


def _patch_persona_evidence(db: Session, user_id: int) -> None:
    row = db.get(StudentProfile, user_id)
    if row is None:
        return
    payload = dict(row.dimensions or {})
    payload["_dimension_evidence"] = build_dimension_evidence(db, user_id)
    payload["_update_reason"] = (
        build_update_reason(db, user_id) or payload.get("_update_reason", "")
    )
    payload["_recent_evidence"] = build_recent_evidence_items(db, user_id, limit=3)
    row.dimensions = payload
    db.commit()


def seed_mastery(db: Session, user_id: int) -> tuple[str, int]:
    modules = _default_modules()
    overview = MasteryService(db).recalculate(
        user_id,
        course_id=COURSE_ID,
        chapter_id=DP_CHAPTER_ID,
        modules=modules,
    )
    report = overview.report
    if report is None and overview.chapters:
        report = overview.chapters[0]
    report_id = report.chapter_id if report else DP_CHAPTER_ID
    score = report.mastery_score if report else 50
    return report_id, score


def seed_learning_path(db: Session, user: User) -> LearningPathPlan:
    profile_row = db.get(StudentProfile, user.id)
    profile_block = _format_profile_block(profile_row, db=db, user_id=user.id)
    request = _replan_request()
    scores = dict((profile_row.dimensions or {}).get("_dimension_scores") or {})
    from services.mastery.mastery_service import get_cached_mastery_by_chapter

    plan_data = _heuristic_plan(
        profile_block,
        request,
        scores,
        mastery_by_chapter=get_cached_mastery_by_chapter(db, user.id),
    )
    plan_data = _insert_remediation_step(plan_data, "array", request)
    plan_data["summary"] = (
        f"{plan_data.get('summary', '')}（{DEMO_SEED_SOURCE}）"
    ).strip()
    plan_data["rationale"] = (
        f"{plan_data.get('rationale', '')} 演示种子：DP 受挫后插入数组巩固。"
    ).strip()

    row = db.get(LearningPathPlan, user.id)
    if row is None:
        row = LearningPathPlan(user_id=user.id)
        db.add(row)
    row.summary = plan_data["summary"]
    row.rationale = plan_data["rationale"]
    row.next_module_key = plan_data.get("next_module_key")
    row.ordered_keys = plan_data["ordered_keys"]
    row.steps = plan_data["steps"]
    row.progress_snapshot = {
        "overall_percent": request.overall_percent,
        "modules": [m.model_dump() for m in request.modules],
        "remediation_inserted": True,
        "seed_source": DEMO_SEED_SOURCE,
        "demo": True,
    }
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return row


def seed_learning_progress(db: Session, user_id: int) -> None:
    row = db.get(LearningProgress, user_id)
    if row is None:
        row = LearningProgress(user_id=user_id, payload={})
        db.add(row)
    row.payload = {
        "alp_module_progress": {
            "array": {"percent": 25, "done": 1, "total": 4},
            "linked-list": {"percent": 15, "done": 1, "total": 5},
            "dp": {"percent": 0, "done": 0, "total": 5},
            "graph": {"percent": 0, "done": 0, "total": 5},
        },
        "seed_source": DEMO_SEED_SOURCE,
        "demo": True,
    }
    row.updated_at = datetime.now(timezone.utc)
    db.commit()


def seed_resources(db: Session, user: User) -> int:
    profile_row = db.get(StudentProfile, user.id)
    profile_block = _format_profile_block(profile_row, db=db, user_id=user.id)
    fallback_reason = f"A3 demo seed（{DEMO_SEED_SOURCE}），无 LLM Key"
    created = 0

    for resource_type, topic, module_key in _DEMO_RESOURCES:
        try:
            chunks = retriever.search(topic, module_key=module_key, top_k=5)
            title, content, meta = generate_fallback_resource(
                resource_type,  # type: ignore[arg-type]
                topic=topic,
                profile_block=profile_block,
                module_key=module_key,
                chunks=chunks,
                fallback_reason=fallback_reason,
            )
        except Exception:
            continue
        meta.update(
            {
                "demo": True,
                "source": DEMO_SEED_SOURCE,
                "topic": topic,
                "module_key": module_key,
            }
        )
        verification = build_verification_result(
            resource_type=resource_type,
            chapter_id=_MODULE_TO_CHAPTER_ID.get(module_key, ""),
            grounded_chunks=chunks_to_grounded(chunks),
            verifier_status="passed",
            safety_status="passed",
            final_decision="publish",
        )
        meta["verification"] = verification.model_dump()

        row = GeneratedResource(
            user_id=user.id,
            resource_type=resource_type,
            agent_name=FALLBACK_AGENT,
            title=title,
            content=content,
            meta=meta,
        )
        db.add(row)
        created += 1

    db.commit()
    return created


def seed_evaluation_snapshot(db: Session, user: User) -> int:
    profile_row = db.get(StudentProfile, user.id)
    if profile_row is None:
        return 0
    payload = dict(profile_row.dimensions or {})
    hist = list(payload.get("_evaluation_history") or [])
    snapshot = {
        "at": datetime.now(timezone.utc).isoformat(),
        "overall_score": 38,
        "dimensions": {
            "mastery": 30,
            "consistency": 35,
            "practice": 40,
            "resource_usage": 48,
        },
        "weak_module_keys": ["dp", "graph"],
        "narrative": "DP 与图论掌握度偏低，建议先巩固数组与链表基础再回攻进阶模块。",
        "push_strategy": "优先推送 document + exercises 类资源，暂停 trace_animation 推送直到基础稳固。",
        **_demo_marker(),
    }
    hist.append(snapshot)
    hist = hist[-10:]
    payload["_evaluation_history"] = hist
    profile_row.dimensions = payload
    db.commit()
    return 1


def seed_replan_record(db: Session, user: User) -> int:
    plan_row = db.get(LearningPathPlan, user.id)
    if plan_row is None:
        return 0
    snap = dict(plan_row.progress_snapshot or {})
    snap["replan_triggered_by_evaluation"] = True
    snap.update(_demo_marker())
    plan_row.progress_snapshot = snap
    db.commit()
    return 1


def _recommended_route(next_module_key: str | None) -> str:
    if next_module_key == "array":
        return "/learning-path"
    if next_module_key in ("linked-list", "dp", "graph"):
        return "/practice/reverse-linked-list"
    return "/learning-path"


def run_seed(db: Session) -> SeedResult:
    Base.metadata.create_all(bind=engine)
    user = ensure_demo_user(db)
    clear_demo_seed_artifacts(db, user.id)

    seed_persona(db, user)
    memories_count = seed_memories(db, user.id)
    _patch_persona_evidence(db, user.id)
    mastery_report_id, mastery_score = seed_mastery(db, user.id)
    path_row = seed_learning_path(db, user)
    seed_learning_progress(db, user.id)
    resources_count = seed_resources(db, user)
    evaluation_count = seed_evaluation_snapshot(db, user)
    replan_count = seed_replan_record(db, user)

    next_key = path_row.next_module_key or "array"
    return SeedResult(
        user_id=user.id,
        username=user.username,
        course_id=COURSE_ID,
        memories_count=memories_count,
        resources_count=resources_count,
        mastery_report_id=mastery_report_id,
        mastery_score=mastery_score,
        recommended_next_route=_recommended_route(next_key),
        next_module_key=next_key,
        evaluation_count=evaluation_count,
        replan_count=replan_count,
    )


def _print_result(result: SeedResult) -> None:
    print("=== A3 Demo Seed 完成 ===")
    for key, value in result.as_dict().items():
        print(f"  {key}: {value}")
    print()
    print("登录演示账号：")
    print(f"  username: {DEMO_USERNAME}")
    print(f"  password: {DEMO_PASSWORD}")
    print(f"  推荐入口: {result.recommended_next_route}")
    print(f"  评估快照数: {result.evaluation_count}")
    print(f"  重排记录数: {result.replan_count}")


def _seed_enabled() -> bool:
    return os.getenv("ALGO_DEMO_SEED_ENABLED", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="预热 A3 比赛演示数据（幂等）")
    parser.add_argument(
        "--force",
        action="store_true",
        help="绕过 ALGO_DEMO_SEED_ENABLED 检查，仅用于本地临时演示。",
    )
    args = parser.parse_args()
    if not args.force and not _seed_enabled():
        print(
            "Demo seed 默认关闭。请设置 ALGO_DEMO_SEED_ENABLED=1 后重试，"
            "或在本地演示环境使用 --force。"
        )
        return 2

    db = SessionLocal()
    try:
        result = run_seed(db)
        _print_result(result)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
