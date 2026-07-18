# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — AlgoPilot 算法智能学习平台"""

import os
from pathlib import Path

BACKEND = Path(SPECPATH)

# ---------- 数据文件 ----------
datas = []

# Alembic 配置与版本化数据库迁移
alembic_ini = BACKEND / "alembic.ini"
if alembic_ini.is_file():
    datas.append((str(alembic_ini), "."))
migrations = BACKEND / "migrations"
if migrations.is_dir():
    datas.append((str(migrations), "migrations"))

# 知识库 JSON — 整个 knowledge_base 目录
kb = BACKEND / "knowledge_base"
if kb.is_dir():
    datas.append((str(kb), "knowledge_base"))

# 课程知识库 — 整个 courses 目录
courses = BACKEND / "knowledge" / "courses"
if courses.is_dir():
    datas.append((str(courses), "knowledge/courses"))

# 技能卡 YAML — 整个 cards 目录打包
cards = BACKEND / "services" / "skills" / "cards"
if cards.is_dir():
    datas.append((str(cards), "services/skills/cards"))

# GDB STL 提取脚本（C++ 追踪时由 GDB source 加载）
gdb_script = BACKEND / "services" / "oj" / "gdb_stl_extract.py"
if gdb_script.is_file():
    datas.append((str(gdb_script), "services/oj/"))

# Python 追踪序列化脚本（运行时复制到临时目录）
trace_ser = BACKEND / "services" / "oj" / "trace_serialize.py"
if trace_ser.is_file():
    datas.append((str(trace_ser), "services/oj/"))

# OJ 题库数据（catalog.json + tests_bundle.json）
oj_data = BACKEND / "data" / "oj"
if oj_data.is_dir():
    datas.append((str(oj_data), "data/oj"))

# OJ 题库 bundle.json（前端 public 下的）
oj_bundle = BACKEND.parent / "frontend" / "public" / "oj" / "bundle.json"
if oj_bundle.is_file():
    datas.append((str(oj_bundle), "public/oj"))

# .env.example 作为默认配置参考
env_example = BACKEND / ".env.example"
if env_example.is_file():
    datas.append((str(env_example), "."))

# ---------- 隐式导入 ----------
hiddenimports = [
    "models.db_models",
    "services.oj.cpp_runner",
    "services.oj.cpp_trace_runner",
    "services.oj.trace_runner",
    "services.oj.runner",
    "services.oj.stdio_runner",
    "services.oj.static_audit",
    "services.oj.compare",
    "services.oj.error_patterns",
    "services.oj.problem_store",
    "services.oj.problem_context",
    "services.oj.tutoring_pipeline",
    "services.oj.trace_narration",
    "services.oj.trace_demo_narration",
    "services.oj.trace_step_narration",
    "services.oj.trace_steps_filter",
    "services.oj.trace_line_refine",
    "services.oj.trace_report",
    "services.oj.trace_serialize",
    "services.oj.gdb_stl_extract",
    "services.oj.ai_diagnosis",
    "services.agents.registry",
    "services.agents.resource_roles",
    "services.agents.verifier",
    "services.agents.evaluation",
    "services.agents.learning_path",
    "services.agents.learning_path_catalog",
    "services.agents.oj_assistant",
    "services.agents.persona",
    "services.agents.persona_fallback",
    "services.agents.persona_learning",
    "services.agents.tutor",
    "services.agents.base",
    "services.agents.explain_engine",
    "services.agents.template_fallback",
    "services.agents.resources",
    "services.agents.ast_analyzer",
    "services.orchestrator.core",
    "services.orchestrator.workflow",
    "services.orchestrator.fallback_workflow",
    "services.orchestrator.pipeline_context",
    "services.orchestrator.persona_fingerprint",
    "services.safety.content_filter",
    "services.knowledge.retriever",
    "services.knowledge.semantic_search",
    "services.knowledge.concept_clusters",
    "services.knowledge.course_loader",
    "services.llm.client",
    "services.mastery.mastery_service",
    "services.mastery.mastery_agent",
    "services.mastery.scoring",
    "services.mastery.models",
    "services.memory.memory_service",
    "services.memory.memory_summarizer",
    "services.memory.schemas",
    "services.skills.registry",
    "services.skills.recommend",
    "services.skills.skill_router",
    "services.skills.skill_context",
    "services.skills.models",
    "services.events.event_bus",
    "services.events.event_models",
    "services.events.handlers",
    "services.evidence.builder",
    "services.verification.builder",
    "services.analytics.effectiveness",
    "services.teacher_dashboard.service",
    "services.tts.iflytek_tts",
    "services.ai_chat",
    "services.ai_tutor_modules",
    "services.ai_tutor_prompt",
    "services.oj_assistant_prompt",
    "utils.security",
    "core.config",
    "core.database",
    "api.ai_tutor",
    "api.analytics",
    "api.auth",
    "api.deps",
    "api.events",
    "api.health",
    "api.learning",
    "api.mastery",
    "api.memory",
    "api.oj",
    "api.oj_assistant",
    "api.orchestrator",
    "api.search",
    "api.skills",
    "api.teacher_dashboard",
    "api.tts",
    "schemas.agent_outputs",
    "schemas.ai_tutor",
    "schemas.auth",
    "schemas.evaluation",
    "schemas.events",
    "schemas.evidence",
    "schemas.learning",
    "schemas.learning_path",
    "schemas.mastery",
    "schemas.memory",
    "schemas.oj",
    "schemas.oj_assistant",
    "schemas.persona",
    "schemas.resources",
    "schemas.search",
    "schemas.skills",
    "schemas.teacher_dashboard",
    "schemas.tts",
    "schemas.verification",
    # Pydantic / SQLAlchemy 隐式依赖
    "pydantic",
    "pydantic_settings",
    "sqlalchemy.dialects.sqlite",
    "sqlalchemy.orm",
    "email_validator",
    "httpx",
    "anyio",
    "sniffio",
]

a = Analysis(
    [str(BACKEND / "main.py")],
    pathex=[str(BACKEND)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter", "matplotlib", "numpy", "pandas", "scipy",
        "PIL", "cv2", "IPython", "jupyter", "notebook",
        "langchain", "langgraph", "openai",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name="AlgoPilot",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="AlgoPilot",
)
