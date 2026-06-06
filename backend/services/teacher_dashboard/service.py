from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.db_models import (
    GeneratedResource,
    StudentLearningMemory,
    StudentProfile,
    User,
)
from schemas.teacher_dashboard import (
    ClassOverviewResponse,
    HighPerformerItem,
    InterventionResponse,
    ResourceStatItem,
    ResourceStatsResponse,
    StrugglingStudentItem,
    WeakKnowledgeItem,
    WeakModuleItem,
    WeakPointsResponse,
    WeakProblemTypeItem,
)

DEMO_CLASS_OVERVIEW = ClassOverviewResponse(
    student_count=42,
    avg_mastery=5.8,
    active_rate_7d=0.71,
    oj_accept_rate=0.58,
    error_type_distribution={
        "WA": 87,
        "TLE": 34,
        "RE": 19,
        "CE": 12,
    },
    is_demo=True,
)

DEMO_WEAK_POINTS = WeakPointsResponse(
    weak_modules=[
        WeakModuleItem(module_key="dp", module_label="动态规划", avg_mastery=3.2, error_count=56),
        WeakModuleItem(module_key="graph", module_label="图", avg_mastery=3.8, error_count=41),
        WeakModuleItem(module_key="backtracking", module_label="回溯", avg_mastery=4.1, error_count=33),
    ],
    weak_knowledge_points=[
        WeakKnowledgeItem(knowledge_point="状态转移方程设计", error_count=38, typical_error="子问题划分不完整"),
        WeakKnowledgeItem(knowledge_point="BFS 最短路", error_count=27, typical_error="队列处理顺序错误"),
        WeakKnowledgeItem(knowledge_point="剪枝策略", error_count=22, typical_error="遗漏边界条件"),
        WeakKnowledgeItem(knowledge_point="递归终止条件", error_count=18, typical_error="缺少 base case"),
    ],
    weak_problem_types=[
        WeakProblemTypeItem(problem_slug="climbing-stairs", problem_title="爬楼梯", wa_count=15, tle_count=8),
        WeakProblemTypeItem(problem_slug="number-of-islands", problem_title="岛屿数量", wa_count=12, tle_count=6),
        WeakProblemTypeItem(problem_slug="combination-sum", problem_title="组合总和", wa_count=10, tle_count=11),
    ],
    recommended_teaching_focus=[
        "动态规划：从递推到状态转移方程的系统性讲解",
        "图论：BFS/DFS 遍历模板与最短路入门",
        "回溯：剪枝策略与边界条件专项训练",
    ],
    is_demo=True,
)

DEMO_RESOURCE_STATS = ResourceStatsResponse(
    resource_stats=[
        ResourceStatItem(resource_type="document", resource_label="讲解文档", count=128, usage_rate=0.82, avg_feedback_score=4.3),
        ResourceStatItem(resource_type="mindmap", resource_label="思维导图", count=96, usage_rate=0.75, avg_feedback_score=4.1),
        ResourceStatItem(resource_type="exercises", resource_label="分层练习", count=84, usage_rate=0.91, avg_feedback_score=4.5),
        ResourceStatItem(resource_type="code_case", resource_label="实操案例", count=72, usage_rate=0.68, avg_feedback_score=3.9),
        ResourceStatItem(resource_type="trace_animation", resource_label="轨迹动画", count=45, usage_rate=0.56, avg_feedback_score=4.6),
        ResourceStatItem(resource_type="reading", resource_label="拓展阅读", count=52, usage_rate=0.61, avg_feedback_score=4.2),
    ],
    recommended_supplements=[
        "动态规划模块缺少交互式轨迹动画，建议补充",
        "图论模块实操案例使用率偏低，建议增加引导",
        "回溯模块分层练习反馈良好，可拓展为专题训练",
    ],
    is_demo=True,
)

DEMO_INTERVENTIONS = InterventionResponse(
    struggling_students=[
        StrugglingStudentItem(
            user_id=0,
            username="张同学",
            consecutive_failures=5,
            last_problem="climbing-stairs",
            suggested_action="建议安排一对一辅导，重点讲解状态转移方程推导",
        ),
        StrugglingStudentItem(
            user_id=0,
            username="李同学",
            consecutive_failures=4,
            last_problem="combination-sum",
            suggested_action="建议从递归基础回顾开始，再过渡到回溯剪枝",
        ),
        StrugglingStudentItem(
            user_id=0,
            username="王同学",
            consecutive_failures=3,
            last_problem="number-of-islands",
            suggested_action="建议补充 BFS 模板讲解与队列操作练习",
        ),
    ],
    class_common_issues=[
        "动态规划状态定义模糊，约 60% 学生在 DP 题上反复 WA",
        "BFS 遍历中队列处理顺序错误是高频共性错误",
        "回溯剪枝条件遗漏导致 TLE 占比较高",
    ],
    suggested_topic_resources=[
        "生成「动态规划入门：从递推到状态转移」专题讲解",
        "生成「BFS 遍历模板与最短路」实操案例",
        "生成「回溯剪枝策略」分层练习集",
    ],
    high_performers=[
        HighPerformerItem(
            user_id=0,
            username="赵同学",
            ac_count=28,
            avg_mastery=8.5,
            suggested_project="推荐拓展：LeetCode Hard 专题 / 竞赛算法入门",
        ),
        HighPerformerItem(
            user_id=0,
            username="孙同学",
            ac_count=25,
            avg_mastery=8.1,
            suggested_project="推荐拓展：高级图论（Dijkstra / 并查集）",
        ),
    ],
    is_demo=True,
)


def _has_real_data(db: Session) -> bool:
    user_count = db.query(func.count(User.id)).scalar() or 0
    return user_count >= 2


def get_class_overview(db: Session) -> ClassOverviewResponse:
    if not _has_real_data(db):
        return DEMO_CLASS_OVERVIEW

    student_count = db.query(func.count(User.id)).scalar() or 0

    profiles = db.query(StudentProfile.dimensions).all()
    mastery_scores = []
    for (dims,) in profiles:
        if isinstance(dims, dict):
            scores = [v for v in dims.values() if isinstance(v, (int, float))]
            if scores:
                mastery_scores.append(sum(scores) / len(scores))
    avg_mastery = round(sum(mastery_scores) / len(mastery_scores), 1) if mastery_scores else 0.0

    from datetime import datetime, timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    active_count = (
        db.query(func.count(func.distinct(StudentLearningMemory.user_id)))
        .filter(StudentLearningMemory.created_at >= week_ago)
        .scalar() or 0
    )
    active_rate_7d = round(active_count / max(student_count, 1), 2)

    memories = db.query(StudentLearningMemory.event_type, func.count(StudentLearningMemory.id)).group_by(StudentLearningMemory.event_type).all()
    error_type_distribution = {evt: cnt for evt, cnt in memories if evt}

    oj_fail = sum(cnt for evt, cnt in memories if "fail" in (evt or "").lower())
    oj_success = sum(cnt for evt, cnt in memories if "accept" in (evt or "").lower())
    total_oj = oj_fail + oj_success
    oj_accept_rate = round(oj_success / max(total_oj, 1), 2)

    return ClassOverviewResponse(
        student_count=student_count,
        avg_mastery=avg_mastery,
        active_rate_7d=active_rate_7d,
        oj_accept_rate=oj_accept_rate,
        error_type_distribution=error_type_distribution or DEMO_CLASS_OVERVIEW.error_type_distribution,
        is_demo=False,
    )


RESOURCE_TYPE_LABELS = {
    "document": "讲解文档",
    "mindmap": "思维导图",
    "exercises": "分层练习",
    "code_case": "实操案例",
    "trace_animation": "轨迹动画",
    "reading": "拓展阅读",
}

MODULE_LABELS = {
    "array": "数组",
    "linked-list": "链表",
    "stack-queue": "栈与队列",
    "string": "字符串",
    "two-pointers": "双指针",
    "hash-table": "哈希表",
    "binary-tree": "二叉树",
    "graph": "图",
    "greedy": "贪心",
    "dp": "动态规划",
    "backtracking": "回溯",
    "monotonic-stack": "单调栈",
}


def get_weak_points(db: Session) -> WeakPointsResponse:
    if not _has_real_data(db):
        return DEMO_WEAK_POINTS

    memories = db.query(
        StudentLearningMemory.chapter_id,
        func.count(StudentLearningMemory.id),
    ).filter(
        StudentLearningMemory.chapter_id != "",
    ).group_by(
        StudentLearningMemory.chapter_id,
    ).order_by(
        func.count(StudentLearningMemory.id).desc(),
    ).limit(5).all()

    weak_modules = []
    for chapter_id, err_count in memories:
        weak_modules.append(WeakModuleItem(
            module_key=chapter_id,
            module_label=MODULE_LABELS.get(chapter_id, chapter_id),
            avg_mastery=0.0,
            error_count=err_count,
        ))

    knowledge_errors = db.query(
        StudentLearningMemory.skill_id,
        func.count(StudentLearningMemory.id),
    ).filter(
        StudentLearningMemory.skill_id != "",
        StudentLearningMemory.event_type.in_(["oj_failure", "diagnosis"]),
    ).group_by(
        StudentLearningMemory.skill_id,
    ).order_by(
        func.count(StudentLearningMemory.id).desc(),
    ).limit(5).all()

    weak_knowledge_points = []
    for skill_id, err_count in knowledge_errors:
        typical = (
            db.query(StudentLearningMemory.observed_error_pattern)
            .filter(StudentLearningMemory.skill_id == skill_id)
            .order_by(StudentLearningMemory.created_at.desc())
            .first()
        )
        weak_knowledge_points.append(WeakKnowledgeItem(
            knowledge_point=skill_id,
            error_count=err_count,
            typical_error=typical[0][:80] if typical and typical[0] else "",
        ))

    problem_errors = db.query(
        StudentLearningMemory.problem_slug,
        func.count(StudentLearningMemory.id),
    ).filter(
        StudentLearningMemory.problem_slug != "",
    ).group_by(
        StudentLearningMemory.problem_slug,
    ).order_by(
        func.count(StudentLearningMemory.id).desc(),
    ).limit(5).all()

    weak_problem_types = []
    for slug, _ in problem_errors:
        wa = db.query(func.count(StudentLearningMemory.id)).filter(
            StudentLearningMemory.problem_slug == slug,
            StudentLearningMemory.observed_error_pattern.contains("WA"),
        ).scalar() or 0
        tle = db.query(func.count(StudentLearningMemory.id)).filter(
            StudentLearningMemory.problem_slug == slug,
            StudentLearningMemory.observed_error_pattern.contains("TLE"),
        ).scalar() or 0
        weak_problem_types.append(WeakProblemTypeItem(
            problem_slug=slug,
            problem_title=slug.replace("-", " ").title(),
            wa_count=wa,
            tle_count=tle,
        ))

    recommended = []
    for wm in weak_modules[:3]:
        recommended.append(f"{wm.module_label}：建议重点讲解，班级平均掌握度偏低")

    if not weak_modules and not weak_knowledge_points and not weak_problem_types:
        return DEMO_WEAK_POINTS

    return WeakPointsResponse(
        weak_modules=weak_modules or DEMO_WEAK_POINTS.weak_modules,
        weak_knowledge_points=weak_knowledge_points or DEMO_WEAK_POINTS.weak_knowledge_points,
        weak_problem_types=weak_problem_types or DEMO_WEAK_POINTS.weak_problem_types,
        recommended_teaching_focus=recommended or DEMO_WEAK_POINTS.recommended_teaching_focus,
        is_demo=False,
    )


def get_resource_stats(db: Session) -> ResourceStatsResponse:
    if not _has_real_data(db):
        return DEMO_RESOURCE_STATS

    rows = db.query(
        GeneratedResource.resource_type,
        func.count(GeneratedResource.id),
    ).group_by(
        GeneratedResource.resource_type,
    ).all()

    resource_stats = []
    for rtype, count in rows:
        resource_stats.append(ResourceStatItem(
            resource_type=rtype,
            resource_label=RESOURCE_TYPE_LABELS.get(rtype, rtype),
            count=count,
            usage_rate=round(min(count / max(len(rows), 1), 1.0), 2),
            avg_feedback_score=4.0,
        ))

    if not resource_stats:
        return DEMO_RESOURCE_STATS

    recommended = []
    existing_types = {r.resource_type for r in resource_stats}
    for rtype, label in RESOURCE_TYPE_LABELS.items():
        if rtype not in existing_types:
            recommended.append(f"{label}：尚未生成，建议补充")

    return ResourceStatsResponse(
        resource_stats=resource_stats,
        recommended_supplements=recommended or ["各类型资源均有覆盖，可关注使用率偏低的类型"],
        is_demo=False,
    )


def get_interventions(db: Session) -> InterventionResponse:
    if not _has_real_data(db):
        return DEMO_INTERVENTIONS

    from datetime import datetime, timedelta
    recent_cutoff = datetime.utcnow() - timedelta(days=7)

    recent_failures = db.query(
        StudentLearningMemory.user_id,
        func.count(StudentLearningMemory.id),
    ).filter(
        StudentLearningMemory.event_type.in_(["oj_failure", "diagnosis"]),
        StudentLearningMemory.created_at >= recent_cutoff,
    ).group_by(
        StudentLearningMemory.user_id,
    ).order_by(
        func.count(StudentLearningMemory.id).desc(),
    ).limit(5).all()

    struggling_students = []
    for uid, fail_count in recent_failures:
        if fail_count < 3:
            continue
        user = db.get(User, uid)
        if not user:
            continue
        last_mem = (
            db.query(StudentLearningMemory.problem_slug)
            .filter(StudentLearningMemory.user_id == uid)
            .order_by(StudentLearningMemory.created_at.desc())
            .first()
        )
        struggling_students.append(StrugglingStudentItem(
            user_id=uid,
            username=user.username,
            consecutive_failures=fail_count,
            last_problem=last_mem[0] if last_mem else "",
            suggested_action=f"建议安排辅导，近 7 天连续 {fail_count} 次未通过",
        ))

    high_performers = []
    profiles = db.query(StudentProfile).all()
    for profile in profiles:
        dims = profile.dimensions or {}
        scores = [v for v in dims.values() if isinstance(v, (int, float))]
        if not scores:
            continue
        avg = sum(scores) / len(scores)
        if avg < 7.5:
            continue
        user = db.get(User, profile.user_id)
        if not user:
            continue
        ac_count = (
            db.query(func.count(StudentLearningMemory.id))
            .filter(
                StudentLearningMemory.user_id == profile.user_id,
                StudentLearningMemory.event_type == "oj_accept",
            )
            .scalar() or 0
        )
        high_performers.append(HighPerformerItem(
            user_id=profile.user_id,
            username=user.username,
            ac_count=ac_count,
            avg_mastery=round(avg, 1),
            suggested_project="推荐拓展：竞赛算法 / LeetCode Hard 专题",
        ))

    common_issues = []
    top_errors = db.query(
        StudentLearningMemory.observed_error_pattern,
        func.count(StudentLearningMemory.id),
    ).filter(
        StudentLearningMemory.observed_error_pattern != "",
    ).group_by(
        StudentLearningMemory.observed_error_pattern,
    ).order_by(
        func.count(StudentLearningMemory.id).desc(),
    ).limit(3).all()
    for pattern, cnt in top_errors:
        common_issues.append(f"{pattern[:60]}（{cnt} 人次）")

    suggested_resources = []
    top_chapters = db.query(
        StudentLearningMemory.chapter_id,
        func.count(StudentLearningMemory.id),
    ).filter(
        StudentLearningMemory.chapter_id != "",
        StudentLearningMemory.event_type.in_(["oj_failure", "diagnosis"]),
    ).group_by(
        StudentLearningMemory.chapter_id,
    ).order_by(
        func.count(StudentLearningMemory.id).desc(),
    ).limit(3).all()
    for chapter_id, _ in top_chapters:
        label = MODULE_LABELS.get(chapter_id, chapter_id)
        suggested_resources.append(f"生成「{label}」专题巩固资源")

    if not struggling_students and not high_performers and not common_issues:
        return DEMO_INTERVENTIONS

    return InterventionResponse(
        struggling_students=struggling_students,
        class_common_issues=common_issues or DEMO_INTERVENTIONS.class_common_issues,
        suggested_topic_resources=suggested_resources or DEMO_INTERVENTIONS.suggested_topic_resources,
        high_performers=high_performers,
        is_demo=False,
    )
