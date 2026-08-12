"""推荐理由引擎：基于六维画像、掌握度、OJ 表现、学习行为等生成个性化推荐理由。

优先使用规则模板（稳定、可解释），LLM 可选增强但必须有 fallback。
"""

from __future__ import annotations

from dataclasses import dataclass

from schemas.persona import PROFILE_DIMENSION_KEYS

_MODULE_LABELS: dict[str, str] = {
    "array": "数组",
    "linked-list": "链表",
    "hash-table": "哈希表",
    "string": "字符串",
    "two-pointers": "双指针法",
    "stack-queue": "栈与队列",
    "binary-tree": "二叉树",
    "backtracking": "回溯算法",
    "greedy": "贪心算法",
    "dp": "动态规划",
    "monotonic-stack": "单调栈",
    "graph": "图论",
}

_RESOURCE_TYPE_LABELS: dict[str, str] = {
    "document": "概念讲解",
    "mindmap": "知识图谱",
    "exercises": "个性化题单",
    "code_case": "剧本沙盒",
    "trace_animation": "轨迹动画",
    "reading": "分层拓展阅读",
    "ppt": "课程讲义 PPT",
    "video_script": "教学短视频脚本",
}

_RESOURCE_TYPE_FEATURES: dict[str, list[str]] = {
    "document": ["系统讲解", "概念梳理", "例题分析"],
    "mindmap": ["Mermaid 图谱", "结构化理解", "知识关联"],
    "exercises": ["专项练习", "边界条件", "易错点训练"],
    "code_case": ["代码实操", "交互式沙盒", "调试练习"],
    "trace_animation": ["Trace 动画", "执行过程可视化", "逐步跟踪"],
    "reading": ["拓展阅读", "分层深入", "学术/工程视角"],
    "ppt": ["课程讲义", "结构化大纲", "可下载 PPTX"],
    "video_script": ["分镜脚本", "字幕+配音文案", "TTS 语音讲解"],
}

_DIMENSION_LABELS: dict[str, str] = {
    "knowledge_base": "知识基础",
    "cognitive_style": "认知风格",
    "coding_ability": "代码实操能力",
    "learning_goals": "学习目标",
    "error_preference": "易错点偏好",
    "grit_level": "抗挫折心理",
}

_VISUAL_MARKERS = ("视觉", "图", "动画", "Mermaid", "图谱", "可视化")
_HANDS_ON_MARKERS = ("动手", "实操", "写代码", "调试", "上机")
_TEXT_MARKERS = ("文本", "阅读", "理论", "纸笔", "推导")

_ERROR_TYPE_LABELS: dict[str, str] = {
    "boundary_condition_error": "边界条件错误",
    "pointer_update_error": "指针更新错误",
    "initialization_error": "初始化错误",
    "recursion_base_case_error": "递归基线错误",
    "state_transition_error": "状态转移错误",
    "time_complexity_issue": "时间复杂度问题",
    "loop_condition_error": "循环条件错误",
    "data_structure_misuse": "数据结构误用",
}


@dataclass
class ExplainContext:
    dimensions: dict[str, str]
    dimension_scores: dict[str, int]
    module_key: str
    module_mastery: int
    oj_error_types: list[str]
    recent_wa_count: int
    recent_learning_modules: list[str]
    resource_type: str
    prerequisites: list[str]
    is_remediation: bool
    is_next_module: bool


def build_explain_context(
    *,
    profile_row=None,
    path_row=None,
    module_key: str = "",
    resource_type: str = "",
    prerequisites: list[str] | None = None,
    is_remediation: bool = False,
    is_next_module: bool = False,
    mastery_by_chapter: dict[str, int] | None = None,
) -> ExplainContext:
    dimensions: dict[str, str] = {}
    dimension_scores: dict[str, int] = {}
    oj_error_types: list[str] = []
    recent_wa_count = 0
    recent_learning_modules: list[str] = []

    if profile_row and profile_row.dimensions:
        raw = profile_row.dimensions
        if isinstance(raw, dict):
            for k in PROFILE_DIMENSION_KEYS:
                val = raw.get(k)
                if val and isinstance(val, str):
                    dimensions[k] = val
            scores_raw = raw.get("_dimension_scores") or {}
            if isinstance(scores_raw, dict):
                for k in PROFILE_DIMENSION_KEYS:
                    v = scores_raw.get(k)
                    if isinstance(v, (int, float)):
                        dimension_scores[k] = max(1, min(10, int(v)))
            last_oj = raw.get("_last_oj_patch") or {}
            if isinstance(last_oj, dict):
                et = last_oj.get("error_type", "")
                if et:
                    oj_error_types.append(et)

    module_mastery = 100
    if mastery_by_chapter and module_key:
        try:
            from services.knowledge.course_loader import chapter_id_for_module, load_manifest

            cid = chapter_id_for_module(load_manifest(), module_key)
            if cid:
                module_mastery = mastery_by_chapter.get(cid, 100)
        except Exception:
            pass

    return ExplainContext(
        dimensions=dimensions,
        dimension_scores=dimension_scores,
        module_key=module_key,
        module_mastery=module_mastery,
        oj_error_types=oj_error_types,
        recent_wa_count=recent_wa_count,
        recent_learning_modules=recent_learning_modules,
        resource_type=resource_type,
        prerequisites=prerequisites or [],
        is_remediation=is_remediation,
        is_next_module=is_next_module,
    )


def generate_resource_explain(ctx: ExplainContext) -> str:
    reasons: list[str] = []

    if ctx.is_remediation:
        reasons.append(_explain_remediation(ctx))
        return _pick_best(reasons)

    reasons.append(_explain_error_preference(ctx))
    reasons.append(_explain_cognitive_style(ctx))
    reasons.append(_explain_mastery(ctx))
    reasons.append(_explain_oj_performance(ctx))
    reasons.append(_explain_prerequisite(ctx))
    reasons.append(_explain_resource_type_feature(ctx))
    reasons.append(_explain_learning_goal(ctx))
    reasons.append(_explain_knowledge_base(ctx))

    return _pick_best(reasons)


def generate_path_step_explain(ctx: ExplainContext) -> str:
    reasons: list[str] = []

    if ctx.is_remediation:
        reasons.append(_explain_remediation(ctx))
        return _pick_best(reasons)

    reasons.append(_explain_error_preference_for_path(ctx))
    reasons.append(_explain_mastery_for_path(ctx))
    reasons.append(_explain_oj_performance_for_path(ctx))
    reasons.append(_explain_prerequisite_for_path(ctx))
    reasons.append(_explain_knowledge_base_for_path(ctx))
    reasons.append(_explain_coding_ability_for_path(ctx))
    reasons.append(_explain_grit_for_path(ctx))

    return _pick_best(reasons)


def _pick_best(reasons: list[str]) -> str:
    valid = [r for r in reasons if r]
    if not valid:
        return _fallback_explain()
    return valid[0]


def _fallback_explain() -> str:
    return "根据你的学习画像与当前进度推荐"


def _explain_error_preference(ctx: ExplainContext) -> str:
    ep = ctx.dimensions.get("error_preference", "")
    if not ep:
        return ""
    module_label = _MODULE_LABELS.get(ctx.module_key, ctx.module_key)
    for et_label in _ERROR_TYPE_LABELS.values():
        if et_label in ep:
            resource_label = _RESOURCE_TYPE_LABELS.get(ctx.resource_type, "")
            features = _RESOURCE_TYPE_FEATURES.get(ctx.resource_type, [])
            if ctx.resource_type == "trace_animation":
                return f"你在{module_label}模块的{et_label}较多，因此优先推荐这份带 Trace 动画的{module_label}讲解。"
            if ctx.resource_type == "exercises":
                return f"你的易错点偏好包含{et_label}，建议先完成这组{module_label}专项练习。"
            if features:
                return f"你的易错点偏好包含{et_label}，本资源包含{'、'.join(features[:2])}，适合针对性巩固。"
            return f"你的易错点偏好包含{et_label}，推荐此{resource_label}资源帮助你巩固。"
    if "边界" in ep:
        if ctx.resource_type == "exercises":
            return "你在边界条件上容易出错，建议先完成这组边界条件专项练习。"
        return "你在边界条件上容易出错，本资源可帮助你针对性巩固。"
    if "指针" in ep or "链表" in ep:
        if ctx.resource_type == "trace_animation":
            return "你在指针/链表操作上容易出错，推荐这份带 Trace 动画的链表讲解。"
        return "你在指针/链表操作上容易出错，推荐此资源帮助你巩固。"
    return ""


def _explain_cognitive_style(ctx: ExplainContext) -> str:
    cs = ctx.dimensions.get("cognitive_style", "")
    if not cs:
        return ""
    features = _RESOURCE_TYPE_FEATURES.get(ctx.resource_type, [])
    is_visual = any(m in cs for m in _VISUAL_MARKERS)
    is_hands_on = any(m in cs for m in _HANDS_ON_MARKERS)
    is_text = any(m in cs for m in _TEXT_MARKERS)
    if is_visual:
        if ctx.resource_type in ("mindmap", "trace_animation"):
            feature_str = "、".join(features[:2])
            return f"你的认知风格偏视觉化，本资源包含{feature_str}，适合先建立结构化理解。"
        return ""
    if is_hands_on:
        if ctx.resource_type in ("code_case", "exercises", "trace_animation"):
            return "你的认知风格偏动手实践，本资源提供交互式实操环境，适合边做边学。"
        return ""
    if is_text:
        if ctx.resource_type in ("document", "reading"):
            return "你的认知风格偏文本阅读，本资源提供系统讲解与分层阅读，适合深度理解。"
        return ""
    return ""


def _explain_mastery(ctx: ExplainContext) -> str:
    if ctx.module_mastery >= 80:
        return ""
    module_label = _MODULE_LABELS.get(ctx.module_key, ctx.module_key)
    if ctx.module_mastery < 45:
        return f"你在{module_label}模块掌握度较低（{ctx.module_mastery}%），建议优先学习此资源巩固基础。"
    if ctx.module_mastery < 65:
        return f"你在{module_label}模块掌握度中等（{ctx.module_mastery}%），此资源可帮助你提升。"
    return ""


def _explain_oj_performance(ctx: ExplainContext) -> str:
    if not ctx.oj_error_types:
        return ""
    for et in ctx.oj_error_types:
        label = _ERROR_TYPE_LABELS.get(et, "")
        if label:
            if ctx.resource_type == "exercises":
                return f"你最近在 OJ 中出现{label}，建议先完成这组专项练习。"
            if ctx.resource_type == "trace_animation":
                return f"你最近在 OJ 中出现{label}，推荐这份 Trace 动画帮助理解执行过程。"
            return f"你最近在 OJ 中出现{label}，此资源可帮助你针对性改进。"
    return ""


def _explain_prerequisite(ctx: ExplainContext) -> str:
    if not ctx.prerequisites:
        return ""
    prereq_labels = [_MODULE_LABELS.get(p, p) for p in ctx.prerequisites[:2]]
    module_label = _MODULE_LABELS.get(ctx.module_key, ctx.module_key)
    if len(prereq_labels) == 1:
        return f"当前{module_label}模块是{prereq_labels[0]}的后续延伸，建议先完成先修内容。"
    return f"当前{module_label}模块依赖{'、'.join(prereq_labels)}，建议先完成先修基础。"


def _explain_resource_type_feature(ctx: ExplainContext) -> str:
    features = _RESOURCE_TYPE_FEATURES.get(ctx.resource_type, [])
    if not features:
        return ""
    kb_score = ctx.dimension_scores.get("knowledge_base", 5)
    coding_score = ctx.dimension_scores.get("coding_ability", 5)
    if ctx.resource_type == "trace_animation" and coding_score <= 4:
        return f"你的代码实操能力偏弱，本资源的{'、'.join(features[:2])}可帮助理解代码执行流程。"
    if ctx.resource_type == "exercises" and coding_score <= 5:
        return f"你的代码实操能力有待提升，本资源提供{'、'.join(features[:2])}帮助强化。"
    if ctx.resource_type == "mindmap" and kb_score <= 4:
        return f"你的知识基础偏弱，本资源的{'、'.join(features[:2])}适合先建立整体认知框架。"
    if ctx.resource_type == "reading" and kb_score >= 7:
        return f"你的知识基础扎实，本资源的{'、'.join(features[:2])}适合拓展深度。"
    return ""


def _explain_learning_goal(ctx: ExplainContext) -> str:
    lg = ctx.dimensions.get("learning_goals", "")
    if not lg:
        return ""
    if "竞赛" in lg or "ACM" in lg or "蓝桥" in lg:
        if ctx.resource_type == "exercises":
            return "你的学习目标偏竞赛，本资源提供专项题单帮助备赛。"
        return ""
    if "考研" in lg:
        if ctx.resource_type in ("document", "reading"):
            return "你的学习目标偏考研，本资源提供系统讲解与深度阅读，适合应试复习。"
        return ""
    if "就业" in lg or "面试" in lg:
        if ctx.resource_type in ("code_case", "exercises"):
            return "你的学习目标偏就业面试，本资源提供实操练习帮助应对手写代码。"
        return ""
    return ""


def _explain_knowledge_base(ctx: ExplainContext) -> str:
    kb = ctx.dimensions.get("knowledge_base", "")
    kb_score = ctx.dimension_scores.get("knowledge_base", 5)
    if not kb or kb_score >= 7:
        return ""
    module_label = _MODULE_LABELS.get(ctx.module_key, ctx.module_key)
    if kb_score <= 3:
        return f"你的知识基础偏弱，建议从{module_label}的基础概念开始系统学习。"
    return ""


def _explain_remediation(ctx: ExplainContext) -> str:
    module_label = _MODULE_LABELS.get(ctx.module_key, ctx.module_key)
    if ctx.oj_error_types:
        for et in ctx.oj_error_types:
            label = _ERROR_TYPE_LABELS.get(et, "")
            if label:
                return f"检测到你在{module_label}连续出错（{label}），已插入巩固关卡帮助你补强基础。"
    return f"检测到你在{module_label}模块受挫，已插入巩固关卡帮助你补强基础。"


def _explain_error_preference_for_path(ctx: ExplainContext) -> str:
    ep = ctx.dimensions.get("error_preference", "")
    if not ep:
        return ""
    module_label = _MODULE_LABELS.get(ctx.module_key, ctx.module_key)
    for et_label in _ERROR_TYPE_LABELS.values():
        if et_label in ep and module_label in ep:
            return f"你的易错点偏好包含{et_label}，优先安排{module_label}模块。"
    if "边界" in ep:
        return f"你在边界条件上容易出错，优先安排{module_label}模块巩固。"
    return ""


def _explain_mastery_for_path(ctx: ExplainContext) -> str:
    module_label = _MODULE_LABELS.get(ctx.module_key, ctx.module_key)
    if ctx.module_mastery < 45:
        return f"你在{module_label}模块掌握度较低（{ctx.module_mastery}%），建议优先学习。"
    if ctx.module_mastery < 65:
        return f"你在{module_label}模块掌握度中等（{ctx.module_mastery}%），建议继续推进。"
    return ""


def _explain_oj_performance_for_path(ctx: ExplainContext) -> str:
    if not ctx.oj_error_types:
        return ""
    module_label = _MODULE_LABELS.get(ctx.module_key, ctx.module_key)
    for et in ctx.oj_error_types:
        label = _ERROR_TYPE_LABELS.get(et, "")
        if label:
            return f"你最近在 OJ 中出现{label}，建议先完成{module_label}模块。"
    return ""


def _explain_prerequisite_for_path(ctx: ExplainContext) -> str:
    if not ctx.prerequisites:
        return ""
    prereq_labels = [_MODULE_LABELS.get(p, p) for p in ctx.prerequisites[:2]]
    module_label = _MODULE_LABELS.get(ctx.module_key, ctx.module_key)
    if len(prereq_labels) == 1:
        return f"当前{module_label}模块是后续学习的先修基础，建议先完成。"
    return f"当前{module_label}模块依赖{'、'.join(prereq_labels)}，建议先完成先修基础。"


def _explain_knowledge_base_for_path(ctx: ExplainContext) -> str:
    kb_score = ctx.dimension_scores.get("knowledge_base", 5)
    module_label = _MODULE_LABELS.get(ctx.module_key, ctx.module_key)
    if kb_score <= 3:
        return f"你的知识基础偏弱，优先安排{module_label}夯实基础。"
    if kb_score <= 5:
        return f"你的知识基础中等，建议按顺序推进{module_label}。"
    return ""


def _explain_coding_ability_for_path(ctx: ExplainContext) -> str:
    coding_score = ctx.dimension_scores.get("coding_ability", 5)
    module_label = _MODULE_LABELS.get(ctx.module_key, ctx.module_key)
    if coding_score <= 3:
        return f"你的代码实操能力偏弱，优先安排{module_label}模块加强练习。"
    return ""


def _explain_grit_for_path(ctx: ExplainContext) -> str:
    grit_score = ctx.dimension_scores.get("grit_level", 5)
    module_label = _MODULE_LABELS.get(ctx.module_key, ctx.module_key)
    if grit_score <= 3:
        return f"你的抗挫折能力偏弱，建议先完成{module_label}建立信心。"
    return ""
