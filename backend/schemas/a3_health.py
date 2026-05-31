"""A3 核心流程健康检查响应结构。"""



from __future__ import annotations



from typing import Literal



from pydantic import BaseModel, Field



ReadinessLevel = Literal["blocked", "risky", "ready", "excellent"]





class A3HealthResponse(BaseModel):

    course_knowledge_ready: bool = False

    profile_chat_ready: bool = False

    persona_patch_ready: bool = False

    skill_cards_ready: bool = False

    resource_generation_ready: bool = False

    verifier_ready: bool = False

    safety_ready: bool = False

    oj_trace_ready: bool = False

    student_memory_ready: bool = False

    mastery_ready: bool = False

    learning_path_ready: bool = False

    event_bus_ready: bool = False

    llm_configured: bool = False

    tts_configured: bool = False

    trace_python: bool = True

    trace_cpp: bool = False

    readiness_score: int = Field(default=0, ge=0, le=100)

    readiness_level: ReadinessLevel = "blocked"

    blockers: list[str] = Field(default_factory=list)

    warnings: list[str] = Field(default_factory=list)

    recommended_actions: list[str] = Field(default_factory=list)

    demo_path_recommendation: str = ""

