"""A3 赛题核心能力轻量健康检查（不执行耗时任务、不暴露密钥）。"""

from __future__ import annotations

from sqlalchemy import text

from core.config import settings
from schemas.a3_health import A3HealthResponse, ReadinessLevel

_MIN_SKILL_CARDS = 4
_DEFAULT_COURSE_ID = "data_structures_algorithms"


def _append_warning(warnings: list[str], actions: list[str], warning: str, action: str) -> None:
    if warning not in warnings:
        warnings.append(warning)
    if action not in actions:
        actions.append(action)


def _append_blocker(
    blockers: list[str],
    actions: list[str],
    blocker: str,
    action: str,
) -> None:
    if blocker not in blockers:
        blockers.append(blocker)
    if action not in actions:
        actions.append(action)


def _probe_trace_cpp() -> tuple[bool, bool]:
    trace_cpp = False
    cpp_compiler = False
    try:
        from services.oj.cpp_runner import _find_gpp
        from services.oj.cpp_trace_runner import gdb_available

        cpp_compiler = _find_gpp() is not None
        trace_cpp = cpp_compiler and gdb_available()
    except Exception:
        pass
    return trace_cpp, cpp_compiler


def _check_graph_catalog_consistency() -> str | None:
    """检测课程 manifest 与模块 catalog 中 graph 状态是否一致。"""
    try:
        from services.agents.learning_path_catalog import MODULE_CATALOG
        from services.knowledge.course_loader import load_manifest

        graph_entry = next((m for m in MODULE_CATALOG if m["key"] == "graph"), None)
        if graph_entry is None:
            return "模块 catalog 缺少 graph 条目"

        manifest = load_manifest(_DEFAULT_COURSE_ID)
        chapters = manifest.get("chapters") or []
        graph_chapter = next((c for c in chapters if c.get("id") == "ch06-graph"), None)
        manifest_has_graph = graph_chapter is not None and bool(
            graph_chapter.get("module_keys")
        )
        catalog_available = bool(graph_entry.get("available"))

        if manifest_has_graph and not catalog_available:
            return "课程 manifest 已包含图论章节，但路径 catalog 将 graph 标为不可用"
        if catalog_available and not manifest_has_graph:
            return "路径 catalog 将 graph 标为可用，但课程 manifest 缺少 ch06-graph"
    except Exception as exc:
        return f"图论模块状态校验失败：{exc}"
    return None


def _compute_readiness(
    *,
    flags: dict[str, bool],
    blockers: list[str],
    warnings: list[str],
) -> tuple[int, ReadinessLevel]:
    if blockers:
        score = max(0, 35 - len(blockers) * 8)
        return score, "blocked"

    score = 100
    deductions: list[tuple[bool, int]] = [
        (not flags["oj_trace_ready"], 15),
        (not flags["student_memory_ready"], 15),
        (not flags["mastery_ready"], 15),
        (not flags["resource_generation_ready"], 12),
        (not flags["profile_chat_ready"], 5),
        (not flags["learning_path_ready"], 5),
        (not flags["event_bus_ready"], 5),
        (not flags["verifier_ready"], 4),
        (not flags["safety_ready"], 4),
        (not flags["persona_patch_ready"], 3),
        (not flags["llm_configured"], 5),
        (not flags["tts_configured"], 2),
        (not flags["trace_cpp"], 3),
    ]
    for condition, penalty in deductions:
        if condition:
            score -= penalty

    score = max(0, min(100, score))

    core_loop_ready = (
        flags["oj_trace_ready"]
        and flags["student_memory_ready"]
        and flags["mastery_ready"]
    )
    if not core_loop_ready:
        return score, "risky"

    if score >= 90 and not warnings and flags["llm_configured"]:
        return score, "excellent"
    if score >= 75:
        return score, "ready"
    return score, "risky"


def _build_demo_path_recommendation(
    *,
    level: ReadinessLevel,
    blockers: list[str],
    llm_configured: bool,
    trace_cpp: bool,
    resource_generation_ready: bool,
) -> str:
    if level == "blocked":
        hint = "；".join(blockers[:2]) if blockers else "修复课程知识库与 SkillCard"
        return f"当前不适合录屏演示，请先处理阻断项：{hint}"

    parts: list[str] = []
    if not llm_configured:
        parts.append("画像/资源使用离线模板兜底")
    if resource_generation_ready and not llm_configured:
        parts.append("工作台可走 generate-all 模板流程")
    parts.extend(
        [
            "登录 a3_demo（可选 python backend/scripts/seed_a3_demo_data.py）",
            "/learning-path 画像与路径",
            "/agent-workbench 资源生成",
            "/practice/reverse-linked-list OJ+Trace（Python）",
            "/my-learning 掌握度评估",
            "/learning-path 路径重排",
        ]
    )
    if not trace_cpp:
        parts.insert(-2, "OJ 演示请选 Python，勿依赖 C++ Trace")
    return " → ".join(parts)


def build_a3_health_report() -> A3HealthResponse:
    warnings: list[str] = []
    blockers: list[str] = []
    actions: list[str] = []

    course_knowledge_ready = False
    try:
        from services.knowledge.course_loader import load_manifest, manifest_path

        manifest_file = manifest_path(_DEFAULT_COURSE_ID)
        if manifest_file.is_file():
            manifest = load_manifest(_DEFAULT_COURSE_ID)
            chapters = manifest.get("chapters") or []
            course_knowledge_ready = len(chapters) >= 1
            if not course_knowledge_ready:
                _append_blocker(
                    blockers,
                    actions,
                    "课程 manifest 存在但 chapters 为空",
                    f"补全 {manifest_file} 中的 chapters 配置",
                )
        else:
            _append_blocker(
                blockers,
                actions,
                "《数据结构与算法》课程 manifest 不存在",
                "确认 backend/knowledge/courses/data_structures_algorithms/course_manifest.yaml 已部署",
            )
    except Exception as exc:
        _append_blocker(
            blockers,
            actions,
            f"课程知识库加载失败：{exc}",
            "检查 course_manifest.yaml 格式与 course_id 是否一致",
        )

    profile_chat_ready = False
    try:
        from services.agents.persona import PersonaAgent
        from services.orchestrator.core import Orchestrator

        PersonaAgent()
        Orchestrator()
        profile_chat_ready = True
    except Exception as exc:
        _append_warning(
            warnings,
            actions,
            f"画像对话服务不可用：{exc}",
            "检查 ProfilingAgent 与 /api/orchestrator/persona 相关模块是否正常导入",
        )

    persona_patch_ready = False
    try:
        from services.agents.persona_learning import apply_oj_diagnosis_patch

        persona_patch_ready = callable(apply_oj_diagnosis_patch)
    except Exception as exc:
        _append_warning(
            warnings,
            actions,
            f"画像 patch 服务不可用：{exc}",
            "检查 services/agents/persona_learning.py 是否可导入",
        )

    skill_cards_ready = False
    try:
        from services.skills.registry import get_registry

        card_count = len(get_registry())
        skill_cards_ready = card_count >= _MIN_SKILL_CARDS
        if not skill_cards_ready:
            _append_blocker(
                blockers,
                actions,
                f"SkillCard 数量不足（当前 {card_count}，需要 ≥{_MIN_SKILL_CARDS}）",
                "在 backend/services/skills/cards/ 下补充 YAML 技能卡",
            )
    except Exception as exc:
        _append_blocker(
            blockers,
            actions,
            f"SkillCard 注册表不可用：{exc}",
            "检查 services/skills/registry.py 与 cards 目录",
        )

    resource_generation_ready = False
    try:
        from services.agents.template_fallback import generate_fallback_resource
        from services.orchestrator.core import Orchestrator
        from services.orchestrator.fallback_workflow import (
            FallbackResourceWorkflow,
            fallback_resource_workflow,
        )

        Orchestrator()
        resource_generation_ready = callable(generate_fallback_resource) and isinstance(
            fallback_resource_workflow, FallbackResourceWorkflow
        )
    except Exception as exc:
        _append_warning(
            warnings,
            actions,
            f"资源生成编排不可用：{exc}",
            "检查 orchestrator 与 template_fallback 模块",
        )

    verifier_ready = False
    try:
        from services.agents.verifier import verifier_agent
        from services.verification.builder import build_verification_result

        verifier_ready = verifier_agent is not None and callable(build_verification_result)
    except Exception as exc:
        _append_warning(
            warnings,
            actions,
            f"ContentVerifier 不可用：{exc}",
            "检查 services/agents/verifier.py 与 verification/builder.py",
        )

    safety_ready = False
    try:
        from services.safety.content_filter import SafetyAgent, content_filter

        probe = content_filter.check("A3 健康检查探针文本")
        SafetyAgent()
        safety_ready = not probe.blocked
    except Exception as exc:
        _append_warning(
            warnings,
            actions,
            f"SafetyAgent 不可用：{exc}",
            "检查 services/safety/content_filter.py",
        )

    oj_trace_ready = False
    try:
        from services.oj.ai_diagnosis import diagnose_trace_bug
        from services.oj.trace_runner import run_trace

        oj_trace_ready = callable(run_trace) and callable(diagnose_trace_bug)
    except Exception as exc:
        _append_warning(
            warnings,
            actions,
            f"OJ Trace 子系统不可用：{exc}",
            "检查 services/oj/trace_runner.py；演示时优先使用 Python 语言 Trace",
        )

    student_memory_ready = False
    mastery_ready = False
    try:
        from core.database import SessionLocal
        from services.memory.memory_service import MemoryService
        from services.mastery.mastery_service import MasteryService

        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            MemoryService(db)
            MasteryService(db)
            student_memory_ready = True
            mastery_ready = True
        finally:
            db.close()
    except Exception as exc:
        _append_warning(
            warnings,
            actions,
            f"StudentMemory / Mastery 服务不可用：{exc}",
            "检查数据库连接与 models/db_models.py 中的 ORM 表是否已创建",
        )

    learning_path_ready = False
    try:
        from services.agents.learning_path import LearningPathAgent
        from services.agents.learning_path_catalog import MODULE_CATALOG

        LearningPathAgent()
        learning_path_ready = len(MODULE_CATALOG) >= 1
    except Exception as exc:
        _append_warning(
            warnings,
            actions,
            f"LearningPath 服务不可用：{exc}",
            "检查 learning_path 与 learning_path_catalog 模块",
        )

    event_bus_ready = False
    try:
        from services.events import event_bus

        handler_count = sum(len(items) for items in event_bus._handlers.values())
        event_bus_ready = handler_count >= 1
        if not event_bus_ready:
            _append_warning(
                warnings,
                actions,
                "EventBus 未注册任何 handler",
                "确认 services/events/handlers.py 已在启动时 register_handlers",
            )
    except Exception as exc:
        _append_warning(
            warnings,
            actions,
            f"EventBus 不可用：{exc}",
            "检查 services/events/event_bus.py 与 handlers 注册逻辑",
        )

    trace_cpp, _cpp_compiler = _probe_trace_cpp()
    trace_python = True

    graph_issue = _check_graph_catalog_consistency()
    if graph_issue:
        _append_warning(
            warnings,
            actions,
            graph_issue,
            "对齐 course_manifest.yaml 与 learning_path_catalog.py 中 graph 的 available 状态",
        )

    llm_configured = bool(settings.llm_configured)
    tts_configured = bool(settings.tts_configured)

    if not llm_configured:
        _append_warning(
            warnings,
            actions,
            "未配置 LLM Key：画像对话与 LLM 资源生成将降级为模板/规则兜底",
            "在 backend/.env 中设置 SPARK_API_PASSWORD，或演示时使用 TemplatePersonaFallbackAgent",
        )
    if not tts_configured:
        _append_warning(
            warnings,
            actions,
            "未配置 TTS：视频脚本试听与语音合成不可用",
            "在 backend/.env 中设置 IFLYTEK_TTS_APP_ID / API_KEY / API_SECRET",
        )
    if resource_generation_ready and not llm_configured:
        _append_warning(
            warnings,
            actions,
            "资源生成处于模板兜底模式（partially_ready），质量低于 LLM 多智能体生成",
            "配置 SPARK_API_PASSWORD 后可在工作台启用完整 generate-all 流程",
        )
    if not trace_cpp:
        _append_warning(
            warnings,
            actions,
            "C++ Trace 不可用：请使用 Python 语言进行 OJ / Trace 演示",
            "演示 OJ 时选择 Python；或在环境中安装 g++/gdb 以启用 C++ Trace",
        )

    if not oj_trace_ready:
        _append_warning(
            warnings,
            actions,
            "辅导闭环风险：OJ Trace 未就绪，智能辅导演示将受限",
            "修复 trace_runner / ai_diagnosis 后重试",
        )
    if not student_memory_ready:
        _append_warning(
            warnings,
            actions,
            "辅导闭环风险：StudentMemory 未就绪，证据链可能为空",
            "检查数据库与 student_learning_memories 表",
        )
    if not mastery_ready:
        _append_warning(
            warnings,
            actions,
            "辅导闭环风险：Mastery 未就绪，掌握度评估不可用",
            "检查 mastery_service 与数据库连接",
        )

    flags = {
        "course_knowledge_ready": course_knowledge_ready,
        "skill_cards_ready": skill_cards_ready,
        "oj_trace_ready": oj_trace_ready,
        "student_memory_ready": student_memory_ready,
        "mastery_ready": mastery_ready,
        "resource_generation_ready": resource_generation_ready,
        "profile_chat_ready": profile_chat_ready,
        "learning_path_ready": learning_path_ready,
        "event_bus_ready": event_bus_ready,
        "verifier_ready": verifier_ready,
        "safety_ready": safety_ready,
        "persona_patch_ready": persona_patch_ready,
        "llm_configured": llm_configured,
        "tts_configured": tts_configured,
        "trace_cpp": trace_cpp,
    }
    readiness_score, readiness_level = _compute_readiness(
        flags=flags,
        blockers=blockers,
        warnings=warnings,
    )
    demo_path = _build_demo_path_recommendation(
        level=readiness_level,
        blockers=blockers,
        llm_configured=llm_configured,
        trace_cpp=trace_cpp,
        resource_generation_ready=resource_generation_ready,
    )

    return A3HealthResponse(
        course_knowledge_ready=course_knowledge_ready,
        profile_chat_ready=profile_chat_ready,
        persona_patch_ready=persona_patch_ready,
        skill_cards_ready=skill_cards_ready,
        resource_generation_ready=resource_generation_ready,
        verifier_ready=verifier_ready,
        safety_ready=safety_ready,
        oj_trace_ready=oj_trace_ready,
        student_memory_ready=student_memory_ready,
        mastery_ready=mastery_ready,
        learning_path_ready=learning_path_ready,
        event_bus_ready=event_bus_ready,
        llm_configured=llm_configured,
        tts_configured=tts_configured,
        trace_python=trace_python,
        trace_cpp=trace_cpp,
        readiness_score=readiness_score,
        readiness_level=readiness_level,
        blockers=blockers,
        warnings=warnings,
        recommended_actions=actions,
        demo_path_recommendation=demo_path,
    )
