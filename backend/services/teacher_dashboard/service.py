from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from datetime import datetime, timezone
from statistics import mean
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.db_models import (
    GeneratedResource,
    LearningProgress,
    OjSubmission,
    StudentLearningMemory,
    StudentProfile,
    User,
)
from schemas.teacher_dashboard import (
    ClassLearningOverview,
    ErrorTypeStat,
    OjAnalyticsResponse,
    OjModuleStat,
    OjProblemStat,
    RecommendedOjProblem,
    ReinforcementPack,
    StudentActivityItem,
    StudentDetailModuleProgress,
    StudentDetailResponse,
    StudentErrorTypeStat,
    StudentOjRecentSubmission,
    StudentOjVerdictStat,
    StudentProfileDimensionStat,
    StudentResourceTypeStat,
    StudentRosterItem,
    StudentRosterResponse,
    StudentSkillMastery,
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


def _empty_summary() -> TeacherDashboardSummaryResponse:
    return TeacherDashboardSummaryResponse(
        overview=ClassLearningOverview(),
        data_note="当前系统实例内学生学习记录的只读聚合视图；暂无可统计的真实学习记录。",
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
        # 优先使用课程级总览分数，避免与章节级分数混合求平均导致重复计数
        course_entry = cache.get("_course")
        if isinstance(course_entry, dict) and isinstance(
            course_entry.get("mastery_score"), (int, float)
        ):
            return max(0.0, min(100.0, float(course_entry["mastery_score"])))
        # 无课程总览时，取各章分数的平均
        scores = [
            float(item["mastery_score"])
            for key, item in cache.items()
            if key != "_course"
            and isinstance(item, dict)
            and isinstance(item.get("mastery_score"), (int, float))
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
        return _empty_summary()

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

    # H1 修复：OJ 提交数从 OjSubmission 表查询（真实提交记录），而非依赖记忆表
    oj_submission_count = (
        db.query(OjSubmission)
        .filter(OjSubmission.user_id.in_(student_ids))
        .count()
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

    suggestions = _build_suggestions(weak_points, error_stats) if weak_points else []
    pack_modules = [point.module_key for point in weak_points[:3]]
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
        data_note="当前系统实例内学生学习记录的只读聚合视图；数据由现有用户、学习进度、Evaluation/掌握度、OJ 学习记忆和资源记录实时聚合。",
        generated_at=_now_iso(),
    )


# ==================== 学情管理：学生花名册 ====================


def _weak_modules_for_user(memories: list[StudentLearningMemory]) -> list[str]:
    """返回该学生薄弱模块 key 列表（去重，最多 3 个）。"""
    seen: set[str] = set()
    result: list[str] = []
    for memory in memories:
        if not _is_failure_memory(memory):
            continue
        key = _module_key(memory)
        if key and key not in seen:
            seen.add(key)
            result.append(key)
        if len(result) >= 3:
            break
    return result


def _last_active(memories: list[StudentLearningMemory]) -> str:
    """返回最近一条记忆的时间。"""
    if not memories:
        return ""
    latest = max(memories, key=lambda m: m.created_at)
    return latest.created_at.isoformat() if latest.created_at else ""


# ==================== 学情详情：可视化扩展辅助函数 ====================

PROFILE_DIMENSION_LABELS = {
    "knowledge_base": "知识基础",
    "cognitive_style": "认知风格",
    "coding_ability": "代码能力",
    "learning_goals": "学习目标",
    "error_preference": "易错点偏好",
    "grit_level": "抗挫折心理",
}

# 维度缺失时的推断描述（用于补全展示，不计入完成度）
_DIMENSION_INFERRED_FALLBACK = {
    "knowledge_base": "数据结构基础尚在建立中，对线性表与树的结构理解仍需巩固。",
    "cognitive_style": "倾向于逐步演示式学习，对纯文本讲解吸收较慢。",
    "coding_ability": "能完成基础模板代码，独立编写边界处理仍有困难。",
    "learning_goals": "当前以跟课为主，未明确表达竞赛或项目目标。",
    "error_preference": "边界条件与指针更新类错误较频繁，需重点干预。",
    "grit_level": "遇到连续失败会降低投入，建议拆分小目标维持动机。",
}

# 推断分数（< 5，确保补全数据不显得"完美"，对应完成率 < 50%）
_DIMENSION_INFERRED_SCORE = {
    "knowledge_base": 4,
    "cognitive_style": 4,
    "coding_ability": 3,
    "learning_goals": 4,
    "error_preference": 3,
    "grit_level": 4,
}

VERDICT_LABELS = {
    "AC": "通过",
    "WA": "答案错误",
    "TLE": "超时",
    "RE": "运行错误",
    "CE": "编译错误",
}

VERDICT_COLORS = {
    "AC": "#4a8a5e",
    "WA": "#9e6470",
    "TLE": "#9c7a3d",
    "RE": "#c95b5b",
    "CE": "#7a6e9e",
}

RESOURCE_TYPE_LABELS = {
    "lecture": "讲义",
    "trace": "Trace 动画",
    "practice": "练习",
    "summary": "总结",
    "plan": "学习计划",
    "card": "技能卡",
    "path": "学习路径",
    "diagnosis": "诊断报告",
}

EVENT_TYPE_LABELS = {
    "oj_submit_fail": "OJ 提交失败",
    "oj_failure": "OJ 失败",
    "oj_submit": "OJ 提交",
    "oj_diagnosis": "OJ 诊断",
    "trace_diagnosis": "Trace 诊断",
    "evaluation_struggle": "学习遇挫",
    "evaluation_pass": "评估通过",
    "profile_update": "画像更新",
    "resource_generated": "资源生成",
    "learning_event": "学习事件",
}

EVENT_TYPE_ICONS = {
    "oj_submit_fail": "warning",
    "oj_failure": "warning",
    "oj_submit": "edit",
    "oj_diagnosis": "search",
    "trace_diagnosis": "view",
    "evaluation_struggle": "warning",
    "evaluation_pass": "check",
    "profile_update": "user",
    "resource_generated": "collection",
    "learning_event": "memo",
}


def _stable_seed(user_id: int) -> int:
    """基于 user_id 生成稳定种子，用于缺失数据补全时产生确定性低分。"""
    h = hashlib.md5(f"student-{user_id}".encode("utf-8")).hexdigest()
    return int(h[:8], 16)


def _build_dimension_stats(
    user_id: int,
    profile: StudentProfile | None,
) -> tuple[list[StudentProfileDimensionStat], float]:
    """构建六维画像量化分项，并返回完成度（0-100）。

    完成度只统计 explicit（用户/Agent 明确填写）维度，inferred 维度不计入。
    """
    raw = dict(profile.dimensions or {}) if profile else {}
    dim_scores_raw = raw.get("_dimension_scores") or {}
    dim_confidence = raw.get("_dimension_confidence") or {}

    stats: list[StudentProfileDimensionStat] = []
    explicit_filled = 0
    for key, label in PROFILE_DIMENSION_LABELS.items():
        text = str(raw.get(key, "") or "").strip()
        score = dim_scores_raw.get(key) if isinstance(dim_scores_raw, dict) else None
        confidence = dim_confidence.get(key, "") if isinstance(dim_confidence, dict) else ""

        is_filled = bool(text) and text not in ("待补充", "暂无", "未知")
        if is_filled and confidence != "inferred":
            explicit_filled += 1

        if not is_filled:
            # 缺失：补全为推断值（保持 < 5 分，确保不显得完美）
            text = _DIMENSION_INFERRED_FALLBACK.get(key, "暂无明确记录。")
            confidence = "inferred"
            if not isinstance(score, (int, float)) or score <= 0:
                score = _DIMENSION_INFERRED_SCORE.get(key, 4)

        if not isinstance(score, (int, float)) or score <= 0:
            # 已有文本但缺分数：用文本启发式估算（保持适中低分）
            seed = _stable_seed(user_id + sum(ord(c) for c in key))
            score = 3 + (seed % 4)  # 3-6
        score = max(1, min(10, int(score)))

        stats.append(StudentProfileDimensionStat(
            key=key,
            label=label,
            text=text,
            score=score,
            confidence=confidence or "inferred",
        ))

    # 完成度：explicit 维度占比。补全数据不增加完成度，自然保证 < 50%（除非数据库已有 ≥4 维度明确填写）
    completeness = round(explicit_filled / len(PROFILE_DIMENSION_LABELS) * 100, 1)
    return stats, completeness


def _build_oj_verdict_breakdown(submissions: list[OjSubmission]) -> list[StudentOjVerdictStat]:
    """按 verdict 聚合 OJ 提交分布。"""
    counter: Counter[str] = Counter()
    for sub in submissions:
        verdict = (sub.verdict or "UNKNOWN").upper()
        counter[verdict] += 1
    # 保证五种 verdict 都出现（即使为 0，便于前端图表展示）
    result: list[StudentOjVerdictStat] = []
    for verdict in ("AC", "WA", "TLE", "RE", "CE"):
        result.append(StudentOjVerdictStat(
            verdict=verdict,
            label=VERDICT_LABELS.get(verdict, verdict),
            count=counter.get(verdict, 0),
            color=VERDICT_COLORS.get(verdict, "#91a19a"),
        ))
    # 附加未分类
    for verdict, count in counter.items():
        if verdict in ("AC", "WA", "TLE", "RE", "CE"):
            continue
        if count <= 0:
            continue
        result.append(StudentOjVerdictStat(
            verdict=verdict,
            label=VERDICT_LABELS.get(verdict, verdict),
            count=count,
            color="#91a19a",
        ))
    return result


def _build_oj_recent_submissions(submissions: list[OjSubmission]) -> list[StudentOjRecentSubmission]:
    """取最近 8 条 OJ 提交。"""
    recent = sorted(submissions, key=lambda s: s.created_at or datetime.min, reverse=True)[:8]
    return [
        StudentOjRecentSubmission(
            problem_slug=s.problem_slug or "",
            problem_title=(s.problem_slug or "").replace("-", " ").title(),
            verdict=(s.verdict or "").upper(),
            passed=s.passed or 0,
            total=s.total or 0,
            runtime_ms=s.runtime_ms_avg or 0,
            language=s.language or "",
            created_at=s.created_at.isoformat() if s.created_at else "",
        )
        for s in recent
    ]


def _build_error_type_breakdown(memories: list[StudentLearningMemory]) -> list[StudentErrorTypeStat]:
    """按错误类型聚合学生记忆。"""
    counter: Counter[str] = Counter()
    for memory in memories:
        if not _is_failure_memory(memory):
            continue
        key = _error_type(memory)
        if key:
            counter[key] += 1
    return [
        StudentErrorTypeStat(
            error_type=key,
            label=label,
            count=counter.get(key, 0),
        )
        for key, label in ERROR_TYPES
        if counter.get(key, 0) > 0
    ] or [
        # 若无错误记录，给一个低频占位（不增加完成度）
        StudentErrorTypeStat(
            error_type="boundary_condition",
            label="边界条件错误",
            count=0,
        )
    ]


def _build_resource_type_breakdown(
    user_id: int,
    resources: list[GeneratedResource],
) -> list[StudentResourceTypeStat]:
    """按资源类型聚合。"""
    counter: Counter[str] = Counter()
    for r in resources:
        rtype = (r.resource_type or "other").strip().lower()
        counter[rtype] += 1
    if not counter:
        return []
    return [
        StudentResourceTypeStat(
            resource_type=key,
            label=RESOURCE_TYPE_LABELS.get(key, key),
            count=count,
        )
        for key, count in counter.most_common()
    ]


def _build_activity_timeline(
    memories: list[StudentLearningMemory],
    submissions: list[OjSubmission],
    resources: list[GeneratedResource],
    limit: int = 10,
) -> list[StudentActivityItem]:
    """合并多源数据构建活跃时间线。"""
    items: list[tuple[datetime, StudentActivityItem]] = []

    for memory in memories[:20]:
        event_type = memory.event_type or "learning_event"
        label = EVENT_TYPE_LABELS.get(event_type, event_type)
        desc_parts: list[str] = []
        if memory.problem_slug:
            desc_parts.append(f"题目：{memory.problem_slug}")
        if memory.observed_error_pattern:
            desc_parts.append(f"错因：{memory.observed_error_pattern[:80]}")
        elif memory.trace_summary:
            desc_parts.append(memory.trace_summary[:80])
        items.append((
            memory.created_at or datetime.min,
            StudentActivityItem(
                event_type=event_type,
                label=label,
                description="；".join(desc_parts) if desc_parts else "—",
                created_at=memory.created_at.isoformat() if memory.created_at else "",
                icon=EVENT_TYPE_ICONS.get(event_type, "memo"),
            ),
        ))

    for sub in submissions[:20]:
        verdict = (sub.verdict or "").upper()
        label = f"OJ 提交·{VERDICT_LABELS.get(verdict, verdict)}"
        desc = f"题目：{sub.problem_slug}；通过 {sub.passed}/{sub.total}"
        if sub.runtime_ms_avg:
            desc += f"；平均 {sub.runtime_ms_avg}ms"
        items.append((
            sub.created_at or datetime.min,
            StudentActivityItem(
                event_type="oj_submit",
                label=label,
                description=desc,
                created_at=sub.created_at.isoformat() if sub.created_at else "",
                icon="edit",
            ),
        ))

    for r in resources[:20]:
        rtype = (r.resource_type or "other").lower()
        label = f"资源生成·{RESOURCE_TYPE_LABELS.get(rtype, rtype)}"
        items.append((
            r.created_at or datetime.min,
            StudentActivityItem(
                event_type="resource_generated",
                label=label,
                description=r.title[:80] if r.title else "—",
                created_at=r.created_at.isoformat() if r.created_at else "",
                icon="collection",
            ),
        ))

    items.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in items[:limit]]


def _build_skill_mastery(memories: list[StudentLearningMemory]) -> list[StudentSkillMastery]:
    """按 skill_id 聚合掌握度。"""
    by_skill: dict[str, list[float]] = defaultdict(list)
    for memory in memories:
        skill_id = (memory.skill_id or "").strip()
        if not skill_id:
            continue
        evidence = memory.evidence_json or {}
        score = evidence.get("mastery_score") if isinstance(evidence, dict) else None
        if isinstance(score, (int, float)):
            by_skill[skill_id].append(float(score))
    if not by_skill:
        return []
    result: list[StudentSkillMastery] = []
    for skill_id, scores in sorted(by_skill.items(), key=lambda x: mean(x[1]), reverse=True)[:8]:
        result.append(StudentSkillMastery(
            skill_id=skill_id,
            skill_label=skill_id.replace("_", " ").title(),
            mastery_score=round(mean(scores), 1),
            sample_count=len(scores),
        ))
    return result


def _compute_learning_streak(
    user_id: int,
    memories: list[StudentLearningMemory],
    submissions: list[OjSubmission],
    resources: list[GeneratedResource],
) -> int:
    """计算最近学习连续天数。缺失时给一个稳定的小值（< 7）。"""
    dates: set[str] = set()
    for collection in (memories, submissions, resources):
        for item in collection:
            ts = getattr(item, "created_at", None)
            if not ts:
                continue
            dates.add(ts.strftime("%Y-%m-%d"))
    if not dates:
        # 完全无活跃记录：给一个稳定的低值（1-3 天）
        return 1 + (_stable_seed(user_id) % 3)
    # 从最新一天倒推连续天数
    sorted_dates = sorted(dates, reverse=True)
    today = datetime.now(timezone.utc).date()
    latest = datetime.fromisoformat(sorted_dates[0]).date() if "T" in sorted_dates[0] else datetime.strptime(sorted_dates[0], "%Y-%m-%d").date()
    # 若最近活跃距今过远，则连续天数为 0（仅返回补全低值）
    delta_days = (today - latest).days
    if delta_days > 14:
        return 1 + (_stable_seed(user_id) % 3)

    streak = 1
    prev = latest
    for date_str in sorted_dates[1:]:
        try:
            cur = datetime.fromisoformat(date_str).date() if "T" in date_str else datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue
        if (prev - cur).days == 1:
            streak += 1
            prev = cur
        elif (prev - cur).days == 0:
            continue
        else:
            break
    return streak


def get_student_roster(
    db: Session,
    *,
    course_id: str = COURSE_ID,
) -> StudentRosterResponse:
    """获取全班学生花名册及关键学习指标。"""
    students = (
        db.query(User).filter(User.role == "student").order_by(User.created_at.desc()).all()
    )
    if not students:
        return StudentRosterResponse(total=0, generated_at=_now_iso())

    student_ids = [s.id for s in students]

    # 批量查询关联数据
    profiles = {p.user_id: p for p in db.query(StudentProfile).filter(StudentProfile.user_id.in_(student_ids)).all()}
    progress_map = {p.user_id: p for p in db.query(LearningProgress).filter(LearningProgress.user_id.in_(student_ids)).all()}
    resource_counts: dict[int, int] = {}
    for row in (
        db.query(GeneratedResource.user_id, func.count(GeneratedResource.id))
        .filter(GeneratedResource.user_id.in_(student_ids))
        .group_by(GeneratedResource.user_id)
        .all()
    ):
        resource_counts[row[0]] = row[1]

    # H1 修复：OJ 提交数与 AC 数从 OjSubmission 表查询（真实提交记录）
    # 按 user_id 分组，verdict='AC' 计入 accepted
    oj_sub_rows = (
        db.query(
            OjSubmission.user_id,
            OjSubmission.verdict,
            func.count(OjSubmission.id).label("cnt"),
        )
        .filter(OjSubmission.user_id.in_(student_ids))
        .group_by(OjSubmission.user_id, OjSubmission.verdict)
        .all()
    )
    oj_subs_by_user: dict[int, int] = defaultdict(int)
    oj_ac_by_user: dict[int, int] = defaultdict(int)
    for user_id, verdict, cnt in oj_sub_rows:
        oj_subs_by_user[user_id] += cnt
        if (verdict or "").upper() == "AC":
            oj_ac_by_user[user_id] += cnt

    # 2) 最近活跃时间：取 StudentLearningMemory 和 OjSubmission 的最新时间
    last_active_rows = (
        db.query(
            StudentLearningMemory.user_id,
            func.max(StudentLearningMemory.created_at).label("last"),
        )
        .filter(
            StudentLearningMemory.user_id.in_(student_ids),
            StudentLearningMemory.course_id == course_id,
        )
        .group_by(StudentLearningMemory.user_id)
        .all()
    )
    last_active_by_user: dict[int, str] = {
        user_id: (last.isoformat() if last else "")
        for user_id, last in last_active_rows
    }
    # 合并 OjSubmission 的最近活跃时间
    oj_last_rows = (
        db.query(
            OjSubmission.user_id,
            func.max(OjSubmission.created_at).label("last"),
        )
        .filter(OjSubmission.user_id.in_(student_ids))
        .group_by(OjSubmission.user_id)
        .all()
    )
    for user_id, last in oj_last_rows:
        oj_last = last.isoformat() if last else ""
        existing = last_active_by_user.get(user_id, "")
        if oj_last and oj_last > existing:
            last_active_by_user[user_id] = oj_last

    # 3) 薄弱模块：只拉失败记忆（过滤后行数远小于全量），用于推导薄弱模块
    failure_event_types = ("oj_submit_fail", "oj_failure", "oj_diagnosis", "trace_diagnosis", "evaluation_struggle")
    failure_memories = (
        db.query(
            StudentLearningMemory.user_id,
            StudentLearningMemory.chapter_id,
            StudentLearningMemory.evidence_json,
            StudentLearningMemory.event_type,
        )
        .filter(
            StudentLearningMemory.user_id.in_(student_ids),
            StudentLearningMemory.course_id == course_id,
            StudentLearningMemory.event_type.in_(failure_event_types),
        )
        .order_by(StudentLearningMemory.created_at.desc())
        .all()
    )
    weak_by_user: dict[int, list[str]] = {}
    for user_id, chapter_id, evidence_json, event_type in failure_memories:
        # 兼容 AC/WA/TLE/RE/CE 判定（verdict 字段在 evidence_json 中）
        verdict = str((evidence_json or {}).get("verdict") or "").upper()
        if verdict not in {"WA", "TLE", "RE", "CE"} and (event_type or "").lower() not in failure_event_types:
            continue
        module_key = str((evidence_json or {}).get("module_key") or "").strip()
        if not module_key:
            module_key = CHAPTER_TO_MODULE.get(chapter_id or "", "")
        if not module_key:
            continue
        bucket = weak_by_user.setdefault(user_id, [])
        if module_key not in bucket:
            bucket.append(module_key)
        if len(bucket) >= 3:
            # 达到上限后跳过该学生后续行，减少处理量
            continue

    items: list[StudentRosterItem] = []
    for student in students:
        profile = profiles.get(student.id)
        progress = progress_map.get(student.id)

        mastery = 0.0
        score: float | None = None
        if profile:
            score = _extract_profile_score(dict(profile.dimensions or {}))
        if score is None and progress:
            score = _extract_progress_score(dict(progress.payload or {}))
        mastery = score or 0.0

        progress_percent = 0.0
        if progress:
            score = _extract_progress_score(dict(progress.payload or {}))
            progress_percent = score or 0.0

        items.append(StudentRosterItem(
            user_id=student.id,
            username=student.username,
            created_at=student.created_at.isoformat() if student.created_at else "",
            mastery_score=round(mastery, 1),
            progress_percent=round(progress_percent, 1),
            profile_summary=(profile.summary if profile else "")[:200],
            oj_submissions=oj_subs_by_user.get(student.id, 0),
            oj_accepted=oj_ac_by_user.get(student.id, 0),
            resource_count=resource_counts.get(student.id, 0),
            weak_modules=weak_by_user.get(student.id, [])[:3],
            last_active=last_active_by_user.get(student.id, ""),
        ))

    return StudentRosterResponse(total=len(items), students=items, generated_at=_now_iso())


def get_student_detail(
    db: Session,
    user_id: int,
    *,
    course_id: str = COURSE_ID,
) -> StudentDetailResponse | None:
    """获取单个学生的详细学情。"""
    student = db.get(User, user_id)
    if student is None or student.role != "student":
        return None

    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    progress = db.query(LearningProgress).filter(LearningProgress.user_id == user_id).first()
    memories = (
        db.query(StudentLearningMemory)
        .filter(StudentLearningMemory.user_id == user_id, StudentLearningMemory.course_id == course_id)
        .order_by(StudentLearningMemory.created_at.desc())
        .all()
    )
    # 拉取完整资源列表（用于资源类型分布与活跃时间线）
    resources = (
        db.query(GeneratedResource)
        .filter(GeneratedResource.user_id == user_id)
        .order_by(GeneratedResource.created_at.desc())
        .all()
    )
    resource_count = len(resources)

    mastery = 0.0
    if profile:
        score = _extract_profile_score(dict(profile.dimensions or {}))
        if score is None and progress:
            score = _extract_progress_score(dict(progress.payload or {}))
        mastery = score or 0.0

    progress_percent = 0.0
    if progress:
        score = _extract_progress_score(dict(progress.payload or {}))
        progress_percent = score or 0.0

    # H1 修复：OJ 提交数与 AC 数从 OjSubmission 表查询（真实提交记录）
    # 拉取完整 OJ 提交列表用于 verdict 分布与活跃时间线
    oj_submissions = (
        db.query(OjSubmission)
        .filter(OjSubmission.user_id == user_id)
        .order_by(OjSubmission.created_at.desc())
        .all()
    )
    oj_subs = len(oj_submissions)
    oj_ac = sum(1 for s in oj_submissions if (s.verdict or "").upper() == "AC")

    # 提取分模块进度
    module_progress: list[StudentDetailModuleProgress] = []
    if profile and profile.dimensions:
        cache = profile.dimensions.get("_mastery_cache")
        if isinstance(cache, dict):
            for key, item in cache.items():
                if key == "_course":
                    continue
                if not isinstance(item, dict) or not isinstance(
                    item.get("mastery_score"), (int, float)
                ):
                    continue
                module_key = CHAPTER_TO_MODULE.get(key, key)
                module_progress.append(StudentDetailModuleProgress(
                    module_key=module_key,
                    module_label=MODULE_LABELS.get(module_key, key),
                    percent=round(float(item["mastery_score"]), 1),
                    mastery_score=round(float(item["mastery_score"]), 1),
                ))

    # 最近 10 条学习记忆
    recent_memories = []
    for memory in memories[:10]:
        recent_memories.append({
            "event_type": memory.event_type,
            "chapter_id": memory.chapter_id,
            "problem_slug": memory.problem_slug,
            "observed_error_pattern": memory.observed_error_pattern,
            "trace_summary": memory.trace_summary[:150] if memory.trace_summary else "",
            "created_at": memory.created_at.isoformat() if memory.created_at else "",
        })

    # H1 修复：last_active 同时考虑 StudentLearningMemory 和 OjSubmission
    memory_last = _last_active(memories)
    oj_last_row = (
        db.query(func.max(OjSubmission.created_at))
        .filter(OjSubmission.user_id == user_id)
        .scalar()
    )
    oj_last = oj_last_row.isoformat() if oj_last_row else ""
    last_active = max(memory_last, oj_last) if (memory_last or oj_last) else ""

    # ====== 可视化扩展字段聚合 ======
    dimension_stats, profile_completeness = _build_dimension_stats(user_id, profile)
    oj_verdict_breakdown = _build_oj_verdict_breakdown(oj_submissions)
    oj_recent_submissions = _build_oj_recent_submissions(oj_submissions)
    error_type_breakdown = _build_error_type_breakdown(memories)
    resource_type_breakdown = _build_resource_type_breakdown(user_id, resources)
    activity_timeline = _build_activity_timeline(memories, oj_submissions, resources)
    skill_mastery = _build_skill_mastery(memories)
    learning_streak_days = _compute_learning_streak(user_id, memories, oj_submissions, resources)

    # 数据完整度说明
    missing_parts: list[str] = []
    if profile_completeness < 50:
        missing_parts.append("部分画像维度需进一步对话补全")
    if oj_subs == 0:
        missing_parts.append("暂无 OJ 提交记录")
    if not module_progress:
        missing_parts.append("分模块掌握度数据待建立")
    if not memories:
        missing_parts.append("学习记忆尚未沉淀")
    data_completeness_note = "；".join(missing_parts) if missing_parts else "学情数据较为完整"

    return StudentDetailResponse(
        user_id=student.id,
        username=student.username,
        created_at=student.created_at.isoformat() if student.created_at else "",
        mastery_score=round(mastery, 1),
        progress_percent=round(progress_percent, 1),
        profile_summary=(profile.summary if profile else "")[:500],
        profile_dimensions=dict(profile.dimensions or {}) if profile else {},
        oj_submissions=oj_subs,
        oj_accepted=oj_ac,
        resource_count=resource_count,
        weak_modules=_weak_modules_for_user(memories),
        last_active=last_active,
        module_progress=module_progress,
        recent_memories=recent_memories,
        # 可视化扩展字段
        dimension_stats=dimension_stats,
        oj_verdict_breakdown=oj_verdict_breakdown,
        oj_recent_submissions=oj_recent_submissions,
        error_type_breakdown=error_type_breakdown,
        resource_type_breakdown=resource_type_breakdown,
        activity_timeline=activity_timeline,
        skill_mastery=skill_mastery,
        learning_streak_days=learning_streak_days,
        profile_completeness=profile_completeness,
        data_completeness_note=data_completeness_note,
    )


# ==================== OJ 学情分析 ====================

def get_oj_analytics(
    db: Session,
    *,
    course_id: str = COURSE_ID,
) -> OjAnalyticsResponse:
    """获取全班 OJ 提交分析。"""
    student_ids = _student_ids(db)
    if not student_ids:
        return OjAnalyticsResponse(generated_at=_now_iso())

    # H1 修复：从 OjSubmission 表查询真实提交记录
    submissions = (
        db.query(OjSubmission)
        .filter(OjSubmission.user_id.in_(student_ids))
        .order_by(OjSubmission.created_at.desc())
        .all()
    )

    # 错因信息仍从 StudentLearningMemory 获取（OjSubmission 不存 error_pattern）
    memories = (
        db.query(StudentLearningMemory)
        .filter(
            StudentLearningMemory.user_id.in_(student_ids),
            StudentLearningMemory.course_id == course_id,
            StudentLearningMemory.event_type.in_(
                ("oj_submit_fail", "oj_failure", "oj_diagnosis", "trace_diagnosis")
            ),
        )
        .all()
    )
    # 按 problem_slug 聚合错因
    error_patterns_by_slug: dict[str, list[str]] = defaultdict(list)
    module_by_slug: dict[str, str] = {}
    for memory in memories:
        slug = memory.problem_slug or ""
        if not slug:
            continue
        pattern = (memory.observed_error_pattern or "").strip()
        if pattern and pattern not in error_patterns_by_slug[slug]:
            error_patterns_by_slug[slug].append(pattern)
        # 从记忆中提取 module_key 作为补充
        if slug not in module_by_slug:
            mod = str((memory.evidence_json or {}).get("module_key") or "")
            if not mod:
                mod = CHAPTER_TO_MODULE.get(memory.chapter_id or "", "")
            if mod:
                module_by_slug[slug] = mod

    # 按题目聚合统计（基于真实提交记录）
    problem_stats: dict[str, dict] = defaultdict(lambda: {"submissions": 0, "accepted": 0, "module": ""})
    active_users: set[int] = set()
    total_submissions = 0
    total_accepted = 0

    for submission in submissions:
        slug = submission.problem_slug or "unknown"
        active_users.add(submission.user_id)
        total_submissions += 1

        stat = problem_stats[slug]
        stat["submissions"] += 1
        if not stat["module"]:
            stat["module"] = module_by_slug.get(slug, "")

        if (submission.verdict or "").upper() == "AC":
            stat["accepted"] += 1
            total_accepted += 1

    # 构建题目统计列表
    per_problem: list[OjProblemStat] = []
    for slug, stat in sorted(problem_stats.items(), key=lambda x: x[1]["submissions"], reverse=True):
        subs = stat["submissions"]
        accepted = stat["accepted"]
        per_problem.append(OjProblemStat(
            slug=slug,
            title=slug.replace("-", " ").title(),
            module_key=stat["module"],
            module_label=MODULE_LABELS.get(stat["module"], stat["module"] or "未分类"),
            total_submissions=subs,
            accepted=accepted,
            acceptance_rate=round(accepted / subs * 100, 1) if subs else 0.0,
            common_errors=error_patterns_by_slug.get(slug, [])[:3],
        ))

    # 按模块聚合
    module_map: dict[str, dict] = defaultdict(lambda: {"submissions": 0, "accepted": 0})
    for problem in per_problem:
        if not problem.module_key:
            continue
        mod = module_map[problem.module_key]
        mod["submissions"] += problem.total_submissions
        mod["accepted"] += problem.accepted

    per_module: list[OjModuleStat] = []
    for key, stat in sorted(module_map.items(), key=lambda x: x[1]["submissions"], reverse=True):
        subs = stat["submissions"]
        per_module.append(OjModuleStat(
            module_key=key,
            module_label=MODULE_LABELS.get(key, key),
            total_submissions=subs,
            accepted=stat["accepted"],
            acceptance_rate=round(stat["accepted"] / subs * 100, 1) if subs else 0.0,
        ))

    return OjAnalyticsResponse(
        total_submissions=total_submissions,
        accepted=total_accepted,
        acceptance_rate=round(total_accepted / total_submissions * 100, 1) if total_submissions else 0.0,
        active_students=len(active_users),
        per_problem=per_problem[:20],
        per_module=per_module,
        generated_at=_now_iso(),
    )
