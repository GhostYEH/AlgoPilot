from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.db_models import (
    GeneratedResource,
    LearningPathPlan,
    StudentLearningMemory,
    StudentProfile,
    User,
)


DEMO_SUMMARY: dict[str, Any] = {
    "demo_mode": True,
    "data_source": "rule_fallback",
    "profile_summary": {
        "summary": "演示学生：知识基础中等偏弱，偏好可视化讲解，代码边界处理仍需强化。",
        "dimension_scores": {
            "knowledge_base": 5,
            "cognitive_style": 7,
            "coding_ability": 4,
            "learning_goals": 7,
            "error_preference": 5,
            "grit_level": 4,
        },
        "weak_points": ["动态规划状态设计", "图 BFS visited 标记", "数组边界条件"],
    },
    "current_path": {
        "summary": "依据六维画像与先修 DAG 生成，检测到连续受挫后插入数组巩固。",
        "ordered_keys": [
            "array",
            "linked-list",
            "stack-queue",
            "sorting",
            "binary-tree",
            "graph",
            "dp",
        ],
        "next_module_key": "array",
        "next_route": "/learn/array",
        "remediation_inserted": True,
    },
    "generated_resources_count": 6,
    "recent_oj_status": {
        "status": "diagnosed",
        "verdict": "WA",
        "problem_slug": "demo-dp-grid-0",
        "module_key": "dp",
        "error": "状态转移遗漏边界初始化，连续 3 次未通过。",
        "route": "/practice/climbing-stairs",
    },
    "recent_trace_summary": {
        "status": "completed",
        "problem_slug": "demo-dp-grid-0",
        "summary": "Trace 在第 3 步定位 dp[0] 未初始化，已生成分层提示与修复建议。",
        "route": "/practice/climbing-stairs",
    },
    "evaluation_summary": {
        "overall_score": 38,
        "weak_module_keys": ["dp", "graph"],
        "narrative": "进阶模块掌握度偏低，应先完成数组与排序基础巩固。",
        "push_strategy": "优先推送概念讲解、分层题单和 Trace 动画。",
    },
    "replan_suggestion": {
        "status": "ready",
        "recommended_module_key": "array",
        "action": "先完成数组边界巩固，再回到动态规划状态设计。",
        "reason": "EvaluationAgent 检测到连续 OJ 失败，LearningPathAgent 已生成降级路径。",
        "route": "/learning-path",
    },
}


def _module_route(module_key: str) -> str:
    return f"/learn/{module_key}" if module_key else "/learning-path"


def _latest_memory(
    db: Session,
    user_id: int,
    *,
    event_types: tuple[str, ...] | None = None,
) -> StudentLearningMemory | None:
    stmt = select(StudentLearningMemory).where(
        StudentLearningMemory.user_id == user_id
    )
    if event_types:
        stmt = stmt.where(StudentLearningMemory.event_type.in_(event_types))
    return db.scalar(stmt.order_by(StudentLearningMemory.created_at.desc()).limit(1))


def _recent_oj_failure(db: Session, user_id: int) -> StudentLearningMemory | None:
    rows = db.scalars(
        select(StudentLearningMemory)
        .where(StudentLearningMemory.user_id == user_id)
        .where(StudentLearningMemory.event_type.like("oj_%"))
        .order_by(StudentLearningMemory.created_at.desc())
        .limit(20)
    ).all()
    for row in rows:
        evidence = row.evidence_json or {}
        verdict = str(evidence.get("verdict") or row.failed_strategy or "").upper()
        if verdict and verdict != "AC":
            return row
        if row.event_type in {"oj_submit_fail", "oj_diagnosis"}:
            return row
    return None


def build_learning_loop_summary(
    db: Session,
    user: User | None,
) -> dict[str, Any]:
    if user is None:
        return dict(DEMO_SUMMARY)

    profile = db.get(StudentProfile, user.id)
    path = db.get(LearningPathPlan, user.id)
    resource_count = int(
        db.scalar(
            select(func.count(GeneratedResource.id)).where(
                GeneratedResource.user_id == user.id
            )
        )
        or 0
    )
    recent_oj = _recent_oj_failure(db, user.id)
    recent_trace = _latest_memory(db, user.id, event_types=("trace_diagnosis",))
    path_adjustment = _latest_memory(db, user.id, event_types=("path_adjusted",))

    dimensions = dict(profile.dimensions or {}) if profile else {}
    evaluation_history = list(dimensions.get("_evaluation_history") or [])
    evaluation = evaluation_history[-1] if evaluation_history else {}
    has_real_data = bool(
        profile
        or path
        or resource_count
        or recent_oj
        or recent_trace
        or evaluation
    )
    if not has_real_data:
        demo = dict(DEMO_SUMMARY)
        demo["profile_summary"] = {
            **DEMO_SUMMARY["profile_summary"],
            "summary": f"{user.username} 尚无完整学习记录，当前展示规则生成的比赛演示闭环。",
        }
        return demo

    weak_keys = [
        str(item)
        for item in (evaluation.get("weak_module_keys") or [])
        if str(item)
    ]
    weak_points = weak_keys or [
        str(item)
        for item in (dimensions.get("weak_points") or [])
        if str(item)
    ]
    dimension_scores = dimensions.get("_dimension_scores") or {}

    ordered_keys = list(path.ordered_keys or []) if path else []
    next_key = str(path.next_module_key or "") if path else ""
    progress_snapshot = dict(path.progress_snapshot or {}) if path else {}

    oj_evidence = dict(recent_oj.evidence_json or {}) if recent_oj else {}
    oj_verdict = str(
        oj_evidence.get("verdict")
        or (recent_oj.failed_strategy if recent_oj else "")
        or "待练习"
    ).upper()
    oj_module = str(oj_evidence.get("module_key") or "") if recent_oj else ""

    replan_evidence = (
        dict(path_adjustment.evidence_json or {}) if path_adjustment else {}
    )
    remediation_key = str(
        replan_evidence.get("remediation_module_key")
        or (next_key if progress_snapshot.get("replan_triggered_by_evaluation") else "")
    )

    return {
        "demo_mode": False,
        "data_source": "database_rule_aggregation",
        "profile_summary": {
            "summary": profile.summary if profile else "画像尚未完成，已根据学习行为生成临时摘要。",
            "dimension_scores": dimension_scores,
            "weak_points": weak_points,
        },
        "current_path": {
            "summary": path.summary if path else "尚未生成正式路径，建议先完成六维画像。",
            "ordered_keys": ordered_keys,
            "next_module_key": next_key,
            "next_route": _module_route(next_key),
            "remediation_inserted": bool(
                remediation_key
                or progress_snapshot.get("replan_triggered_by_evaluation")
            ),
        },
        "generated_resources_count": resource_count,
        "recent_oj_status": {
            "status": "diagnosed" if recent_oj else "pending",
            "verdict": oj_verdict,
            "problem_slug": recent_oj.problem_slug if recent_oj else "",
            "module_key": oj_module,
            "error": (
                recent_oj.observed_error_pattern
                if recent_oj
                else "暂无失败记录，可进入 OJ 完成一次编程实践。"
            ),
            "route": (
                f"/practice/{recent_oj.problem_slug}"
                if recent_oj and recent_oj.problem_slug
                else "/practice"
            ),
        },
        "recent_trace_summary": {
            "status": "completed" if recent_trace else "pending",
            "problem_slug": recent_trace.problem_slug if recent_trace else "",
            "summary": (
                recent_trace.trace_summary
                if recent_trace
                else "暂无 Trace 诊断，可在 OJ 题目页运行可视化调试。"
            ),
            "route": (
                f"/practice/{recent_trace.problem_slug}"
                if recent_trace and recent_trace.problem_slug
                else "/practice"
            ),
        },
        "evaluation_summary": {
            "overall_score": int(evaluation.get("overall_score") or 0),
            "weak_module_keys": weak_keys,
            "narrative": str(
                evaluation.get("narrative")
                or "学习证据仍在积累，完成 OJ 与资源学习后将生成效果评估。"
            ),
            "push_strategy": str(
                evaluation.get("push_strategy")
                or "优先推送当前路径下一模块的讲解与基础题单。"
            ),
        },
        "replan_suggestion": {
            "status": "ready" if remediation_key else "monitoring",
            "recommended_module_key": remediation_key or next_key,
            "action": (
                f"优先完成「{remediation_key}」巩固节点，再回到原学习路径。"
                if remediation_key
                else "继续当前路径；系统将根据下一次评估自动判断是否重排。"
            ),
            "reason": (
                path_adjustment.observed_error_pattern
                if path_adjustment
                else "依据画像、模块掌握度和 OJ 结果进行规则监测。"
            ),
            "route": "/learning-path",
        },
    }
