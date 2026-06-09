from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from statistics import mean
from typing import Any

from sqlalchemy.orm import Session

from models.db_models import (
    GeneratedResource,
    LearningProgress,
    StudentLearningMemory,
    StudentProfile,
    User,
)
from schemas.teacher_dashboard import (
    ClassLearningOverview,
    ErrorTypeStat,
    RecommendedOjProblem,
    ReinforcementPack,
    TeacherDashboardSummaryResponse,
    TeachingSuggestion,
    WeakKnowledgePoint,
)

COURSE_ID = "data_structures_algorithms"

MODULE_LABELS = {
    "array": "数组",
    "linked-list": "链表",
    "stack-queue": "栈与队列",
    "string": "字符串",
    "two-pointers": "双指针",
    "hash-table": "哈希表",
    "binary-tree": "二叉树",
    "graph": "图",
    "sorting": "排序",
    "greedy": "贪心",
    "dp": "动态规划",
    "backtracking": "回溯",
    "monotonic-stack": "单调栈",
}

CHAPTER_TO_MODULE = {
    "ch02-linear-list": "linked-list",
    "ch03-stack-queue": "stack-queue",
    "ch04-string-two-pointers": "string",
    "ch05-tree-binary-tree": "binary-tree",
    "ch06-graph": "graph",
    "ch07-search": "hash-table",
    "ch08-sorting": "sorting",
    "ch09-recursion-divide-conquer": "backtracking",
    "ch10-greedy": "greedy",
    "ch11-dynamic-programming": "dp",
    "ch12-backtracking": "backtracking",
    "ch13-advanced": "monotonic-stack",
}

ERROR_TYPES = (
    ("boundary_condition", "边界条件错误"),
    ("pointer_update", "指针更新错误"),
    ("complexity", "复杂度过高"),
    ("null_access", "空栈/空指针"),
)

PACK_CONFIG: dict[str, tuple[list[str], list[tuple[str, str]]]] = {
    "linked-list": (
        ["指针过程图解", "Trace 动画", "分层练习"],
        [("reverse-linked-list", "反转链表"), ("swap-nodes-in-pairs", "两两交换链表节点")],
    ),
    "binary-tree": (
        ["遍历对照讲义", "递归调用栈动画", "课堂练习"],
        [
            ("binary-tree-inorder-traversal", "二叉树中序遍历"),
            ("max-depth-of-binary-tree", "二叉树的最大深度"),
        ],
    ),
    "dp": (
        ["状态转移讲义", "填表动画", "梯度题单"],
        [("climbing-stairs", "爬楼梯"), ("unique-paths", "不同路径")],
    ),
    "sorting": (
        ["算法对比表", "排序过程动画", "复杂度练习"],
        [("sort-colors", "颜色分类"), ("merge-sorted-array", "合并两个有序数组")],
    ),
    "stack-queue": (
        ["结构操作图解", "边界检查清单", "分层练习"],
        [("valid-parentheses", "有效的括号"), ("implement-queue-using-stacks", "用栈实现队列")],
    ),
    "graph": (
        ["BFS/DFS 对照讲义", "搜索过程动画", "实操案例"],
        [("number-of-islands", "岛屿数量"), ("course-schedule-topological", "课程表拓扑排序")],
    ),
}

MODULE_FOCUS = {
    "linked-list": "用三指针过程图统一讲清保存 next、更新指向和推进当前位置的顺序。",
    "binary-tree": "对照递归栈与显式栈，补讲遍历次序、空节点处理和递归终止条件。",
    "dp": "从状态定义、边界初始化、转移方程到遍历顺序完成一轮板书推导。",
    "sorting": "通过稳定性、空间复杂度和最好/最坏复杂度对比建立算法选型依据。",
    "stack-queue": "强化入栈出栈前的空结构检查，并用不变量解释括号匹配过程。",
    "graph": "统一 BFS/DFS 模板，强调 visited 标记时机和队列/递归栈状态。",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _demo_summary() -> TeacherDashboardSummaryResponse:
    weak = [
        WeakKnowledgePoint(
            module_key="linked-list",
            module_label="链表",
            error_count=31,
            affected_students=18,
        ),
        WeakKnowledgePoint(
            module_key="binary-tree",
            module_label="二叉树",
            error_count=26,
            affected_students=15,
        ),
        WeakKnowledgePoint(
            module_key="dp",
            module_label="动态规划",
            error_count=24,
            affected_students=14,
        ),
        WeakKnowledgePoint(
            module_key="sorting",
            module_label="排序",
            error_count=17,
            affected_students=11,
        ),
    ]
    errors = [
        ErrorTypeStat(error_type="boundary_condition", label="边界条件错误", count=29, percentage=33.0),
        ErrorTypeStat(error_type="pointer_update", label="指针更新错误", count=24, percentage=27.3),
        ErrorTypeStat(error_type="complexity", label="复杂度过高", count=20, percentage=22.7),
        ErrorTypeStat(error_type="null_access", label="空栈/空指针", count=15, percentage=17.0),
    ]
    suggestions = [
        TeachingSuggestion(
            title="补讲链表指针更新顺序",
            reason="链表是当前影响学生人数最多的薄弱模块，指针更新错误集中出现。",
            focus=MODULE_FOCUS["linked-list"],
        ),
        TeachingSuggestion(
            title="补讲动态规划边界与状态转移",
            reason="边界条件错误位居首位，且动态规划模块错误频次较高。",
            focus=MODULE_FOCUS["dp"],
        ),
        TeachingSuggestion(
            title="组织复杂度与排序策略对比课",
            reason="复杂度过高问题占比较高，适合结合排序算法进行横向比较。",
            focus=MODULE_FOCUS["sorting"],
        ),
    ]
    return TeacherDashboardSummaryResponse(
        overview=ClassLearningOverview(
            student_count=42,
            profile_count=37,
            average_mastery=68.4,
            resource_count=128,
            oj_submission_count=356,
        ),
        weak_knowledge_points=weak,
        error_types=errors,
        teaching_suggestions=suggestions,
        reinforcement_packs=[_build_pack(item.module_key) for item in weak[:3]],
        is_demo=True,
        data_note="当前缺少可形成班级统计的真实记录，已自动展示比赛演示数据。",
        generated_at=_now_iso(),
    )


def _student_ids(db: Session) -> list[int]:
    return [
        row[0]
        for row in db.query(User.id).filter(User.role == "student").all()
    ]


def _extract_progress_score(payload: dict[str, Any]) -> float | None:
    explicit: list[float] = []
    completed = 0
    total = 0
    for value in payload.values():
        if not isinstance(value, dict):
            continue
        if isinstance(value.get("percent"), (int, float)):
            explicit.append(float(value["percent"]))
            continue
        for item in value.values():
            if isinstance(item, bool):
                total += 1
                completed += int(item)
            elif isinstance(item, dict) and isinstance(item.get("percent"), (int, float)):
                explicit.append(float(item["percent"]))
    if explicit:
        return max(0.0, min(100.0, mean(explicit)))
    if total:
        return completed / total * 100
    return None


def _extract_profile_score(dimensions: dict[str, Any]) -> float | None:
    cache = dimensions.get("_mastery_cache")
    if isinstance(cache, dict):
        scores = [
            float(item["mastery_score"])
            for item in cache.values()
            if isinstance(item, dict) and isinstance(item.get("mastery_score"), (int, float))
        ]
        if scores:
            return max(0.0, min(100.0, mean(scores)))

    history = dimensions.get("_evaluation_history")
    if isinstance(history, list):
        for item in reversed(history):
            if isinstance(item, dict) and isinstance(item.get("overall_score"), (int, float)):
                return max(0.0, min(100.0, float(item["overall_score"])))
    return None


def _average_mastery(
    profiles: list[StudentProfile],
    progress_rows: list[LearningProgress],
) -> float:
    progress_by_user = {row.user_id: row for row in progress_rows}
    scores: list[float] = []
    profile_users: set[int] = set()
    for profile in profiles:
        profile_users.add(profile.user_id)
        score = _extract_profile_score(dict(profile.dimensions or {}))
        if score is None:
            progress = progress_by_user.get(profile.user_id)
            score = _extract_progress_score(dict(progress.payload or {})) if progress else None
        if score is not None:
            scores.append(score)
    for row in progress_rows:
        if row.user_id in profile_users:
            continue
        score = _extract_progress_score(dict(row.payload or {}))
        if score is not None:
            scores.append(score)
    return round(mean(scores), 1) if scores else 0.0


def _is_failure_memory(memory: StudentLearningMemory) -> bool:
    event_type = (memory.event_type or "").lower()
    verdict = str((memory.evidence_json or {}).get("verdict") or "").upper()
    return (
        event_type in {"oj_submit_fail", "oj_failure", "oj_diagnosis", "trace_diagnosis", "evaluation_struggle"}
        or verdict in {"WA", "TLE", "RE", "CE"}
    )


def _module_key(memory: StudentLearningMemory) -> str:
    evidence = memory.evidence_json or {}
    module_key = str(evidence.get("module_key") or "").strip()
    if module_key:
        return module_key
    return CHAPTER_TO_MODULE.get(memory.chapter_id or "", "")


def _error_type(memory: StudentLearningMemory) -> str | None:
    evidence = memory.evidence_json or {}
    raw_type = str(evidence.get("error_type") or "").lower()
    verdict = str(evidence.get("verdict") or "").upper()
    text = " ".join(
        [
            raw_type,
            memory.observed_error_pattern or "",
            memory.failed_strategy or "",
            memory.trace_summary or "",
        ]
    ).lower()

    if any(token in text for token in ("空指针", "空栈", "nullptr", "null pointer", "stack empty")):
        return "null_access"
    if verdict == "RE" and any(token in text for token in ("空", "null", "栈", "stack")):
        return "null_access"
    if "pointer_update" in raw_type or any(
        token in text for token in ("指针更新", "指针移动", "断链", "next 指针", "pointer update")
    ):
        return "pointer_update"
    if verdict == "TLE" or "time_complexity" in raw_type or any(
        token in text for token in ("复杂度", "超时", "tle", "死循环")
    ):
        return "complexity"
    if "boundary_condition" in raw_type or "initialization_error" in raw_type or any(
        token in text for token in ("边界", "初始化", "越界", "下标", "base case")
    ):
        return "boundary_condition"
    return None


def _build_pack(module_key: str) -> ReinforcementPack:
    resource_types, problems = PACK_CONFIG.get(
        module_key,
        (
            ["知识点讲义", "Trace 动画", "分层练习"],
            [("two-sum", "两数之和"), ("valid-parentheses", "有效的括号")],
        ),
    )
    return ReinforcementPack(
        module_key=module_key,
        module_label=MODULE_LABELS.get(module_key, module_key),
        resource_types=resource_types,
        oj_problems=[
            RecommendedOjProblem(slug=slug, title=title) for slug, title in problems
        ],
    )


def _build_suggestions(
    weak_points: list[WeakKnowledgePoint],
    error_stats: list[ErrorTypeStat],
) -> list[TeachingSuggestion]:
    top_error = error_stats[0].label if error_stats and error_stats[0].count else "共性错误"
    suggestions: list[TeachingSuggestion] = []
    for index, point in enumerate(weak_points[:3]):
        reason = (
            f"{point.module_label}累计出现 {point.error_count} 次薄弱信号，"
            f"影响 {point.affected_students} 名学生。"
        )
        if index == 0:
            reason += f" 当前最高频错误为“{top_error}”。"
        suggestions.append(
            TeachingSuggestion(
                title=f"补讲{point.module_label}核心方法",
                reason=reason,
                focus=MODULE_FOCUS.get(
                    point.module_key,
                    "用典型错例、过程可视化和一组梯度练习完成概念回顾与当堂检验。",
                ),
            )
        )
    used_modules = {point.module_key for point in weak_points[:3]}
    for module_key in ("linked-list", "dp", "sorting", "binary-tree"):
        if len(suggestions) >= 3:
            break
        if module_key in used_modules:
            continue
        module_label = MODULE_LABELS[module_key]
        suggestions.append(
            TeachingSuggestion(
                title=f"补讲{module_label}核心方法",
                reason=f"结合当前“{top_error}”分布，建议安排一轮{module_label}典型错例复盘。",
                focus=MODULE_FOCUS[module_key],
            )
        )
    return suggestions


def get_dashboard_summary(
    db: Session,
    *,
    course_id: str = COURSE_ID,
) -> TeacherDashboardSummaryResponse:
    student_ids = _student_ids(db)
    if not student_ids:
        return _demo_summary()

    profiles = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id.in_(student_ids))
        .all()
    )
    progress_rows = (
        db.query(LearningProgress)
        .filter(LearningProgress.user_id.in_(student_ids))
        .all()
    )
    memories = (
        db.query(StudentLearningMemory)
        .filter(
            StudentLearningMemory.user_id.in_(student_ids),
            StudentLearningMemory.course_id == course_id,
        )
        .all()
    )
    resource_count = (
        db.query(GeneratedResource)
        .filter(GeneratedResource.user_id.in_(student_ids))
        .count()
    )

    learning_record_count = len(profiles) + len(progress_rows) + len(memories) + resource_count
    if len(student_ids) < 2 or learning_record_count < 3:
        return _demo_summary()

    oj_submission_count = sum(
        1
        for memory in memories
        if (memory.event_type or "").lower()
        in {"oj_submit_fail", "oj_submit_success", "oj_failure", "oj_accept"}
    )

    failure_memories = [memory for memory in memories if _is_failure_memory(memory)]
    module_counts: Counter[str] = Counter()
    module_students: dict[str, set[int]] = defaultdict(set)
    for memory in failure_memories:
        key = _module_key(memory)
        if not key:
            continue
        module_counts[key] += 1
        module_students[key].add(memory.user_id)

    weak_points = [
        WeakKnowledgePoint(
            module_key=key,
            module_label=MODULE_LABELS.get(key, key),
            error_count=count,
            affected_students=len(module_students[key]),
        )
        for key, count in module_counts.most_common(5)
    ]

    error_counts: Counter[str] = Counter()
    for memory in failure_memories:
        key = _error_type(memory)
        if key:
            error_counts[key] += 1
    classified_total = sum(error_counts.values())
    error_stats = [
        ErrorTypeStat(
            error_type=key,
            label=label,
            count=error_counts[key],
            percentage=round(error_counts[key] / classified_total * 100, 1)
            if classified_total
            else 0.0,
        )
        for key, label in ERROR_TYPES
    ]
    error_stats.sort(key=lambda item: item.count, reverse=True)

    suggestions = _build_suggestions(weak_points, error_stats)
    pack_modules = [point.module_key for point in weak_points[:3]]
    for module_key in ("linked-list", "dp", "sorting", "binary-tree"):
        if len(pack_modules) >= 3:
            break
        if module_key not in pack_modules:
            pack_modules.append(module_key)
    reinforcement_packs = [_build_pack(key) for key in pack_modules]

    return TeacherDashboardSummaryResponse(
        overview=ClassLearningOverview(
            student_count=len(student_ids),
            profile_count=len(profiles),
            average_mastery=_average_mastery(profiles, progress_rows),
            resource_count=resource_count,
            oj_submission_count=oj_submission_count,
        ),
        weak_knowledge_points=weak_points,
        error_types=error_stats,
        teaching_suggestions=suggestions,
        reinforcement_packs=reinforcement_packs,
        is_demo=False,
        data_note="统计结果由现有用户、学习进度、Evaluation/掌握度、OJ 学习记忆和资源记录实时聚合。",
        generated_at=_now_iso(),
    )
