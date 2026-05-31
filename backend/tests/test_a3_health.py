"""A3 核心流程健康检查接口测试。"""



from __future__ import annotations



import json

from unittest.mock import patch



import pytest

from fastapi.testclient import TestClient



from core.config import settings

from main import app
from services.health import a3_health as a3_health_module



client = TestClient(app)



REQUIRED_FIELDS = (

    "course_knowledge_ready",

    "profile_chat_ready",

    "persona_patch_ready",

    "skill_cards_ready",

    "resource_generation_ready",

    "verifier_ready",

    "safety_ready",

    "oj_trace_ready",

    "student_memory_ready",

    "mastery_ready",

    "learning_path_ready",

    "event_bus_ready",

    "llm_configured",

    "tts_configured",

    "readiness_score",

    "readiness_level",

    "blockers",

    "warnings",

    "recommended_actions",

    "demo_path_recommendation",

)



SECRET_NEEDLES = (

    settings.spark_api_password,

    settings.iflytek_tts_app_id,

    settings.iflytek_tts_api_key,

    settings.iflytek_tts_api_secret,

    settings.jwt_secret,

)





def test_a3_health_returns_200_with_required_fields():

    resp = client.get("/api/a3/health")

    assert resp.status_code == 200

    data = resp.json()

    for field in REQUIRED_FIELDS:

        assert field in data, f"缺少字段 {field}"





def test_a3_health_does_not_expose_secrets():

    resp = client.get("/api/a3/health")

    assert resp.status_code == 200

    raw = json.dumps(resp.json(), ensure_ascii=False)

    for needle in SECRET_NEEDLES:

        if needle and len(needle.strip()) >= 8:

            assert needle not in raw

    lowered = raw.lower()

    for key in ("spark_api_password", "iflytek_tts_api_key", "iflytek_tts_api_secret", "jwt_secret"):

        assert f'"{key}"' not in lowered





def test_a3_health_llm_flag_without_key_does_not_fail():

    resp = client.get("/api/a3/health")

    assert resp.status_code == 200

    data = resp.json()

    assert isinstance(data["llm_configured"], bool)

    assert isinstance(data["tts_configured"], bool)

    if not settings.llm_configured:

        assert data["llm_configured"] is False

        assert data["readiness_level"] != "blocked"

        assert any("LLM" in w or "SPARK" in w or "模板" in w for w in data["warnings"])

        assert any(

            "SPARK_API_PASSWORD" in a or "TemplatePersonaFallbackAgent" in a

            for a in data["recommended_actions"]

        )





def test_a3_health_core_subsystems_ready_in_dev():

    """开发环境默认应加载课程 manifest、SkillCard 与 EventBus。"""

    resp = client.get("/api/a3/health")

    data = resp.json()

    assert data["course_knowledge_ready"] is True

    assert data["skill_cards_ready"] is True

    assert data["resource_generation_ready"] is True

    assert data["event_bus_ready"] is True

    assert data["oj_trace_ready"] is True

    assert data["student_memory_ready"] is True

    assert data["mastery_ready"] is True





def test_a3_health_all_ready_score_at_least_90_when_llm_configured():

    resp = client.get("/api/a3/health")

    data = resp.json()

    core_ready = (

        data["course_knowledge_ready"]

        and data["skill_cards_ready"]

        and data["oj_trace_ready"]

        and data["student_memory_ready"]

        and data["mastery_ready"]

        and data["resource_generation_ready"]

    )

    if core_ready and data["llm_configured"] and not data["blockers"]:

        assert data["readiness_score"] >= 90

        assert data["readiness_level"] in ("ready", "excellent")





def test_a3_health_missing_course_manifest_is_blocked():
    from pathlib import Path

    fake_path = Path("/nonexistent/course_manifest.yaml")
    with patch("services.knowledge.course_loader.manifest_path", return_value=fake_path):
        from services.health.a3_health import build_a3_health_report

        report = build_a3_health_report()
    assert report.readiness_level == "blocked"
    assert report.blockers
    assert report.readiness_score < 50
    assert report.course_knowledge_ready is False


def test_a3_health_warnings_imply_reasonable_level():

    resp = client.get("/api/a3/health")

    data = resp.json()

    if data["warnings"] and not data["blockers"]:

        assert data["readiness_level"] in ("risky", "ready")

        if len(data["warnings"]) >= 2:

            assert data["readiness_level"] != "excellent"





@pytest.mark.parametrize(

    "level,score,blockers,warnings,flags,expected",

    [

        (

            "blocked",

            25,

            ["课程 manifest 缺失"],

            [],

            {"oj_trace_ready": True, "student_memory_ready": True, "mastery_ready": True},

            "blocked",

        ),

        (

            "risky",

            68,

            [],

            ["OJ Trace 未就绪"],

            {"oj_trace_ready": False, "student_memory_ready": True, "mastery_ready": True},

            "risky",

        ),

    ],

)

def test_compute_readiness_levels(level, score, blockers, warnings, flags, expected):

    full_flags = {

        "course_knowledge_ready": True,

        "skill_cards_ready": True,

        "resource_generation_ready": True,

        "profile_chat_ready": True,

        "learning_path_ready": True,

        "event_bus_ready": True,

        "verifier_ready": True,

        "safety_ready": True,

        "persona_patch_ready": True,

        "llm_configured": False,

        "tts_configured": False,

        "trace_cpp": False,

        **flags,

    }

    computed_score, computed_level = a3_health_module._compute_readiness(

        flags=full_flags,

        blockers=blockers,

        warnings=warnings,

    )

    assert computed_level == expected

    if expected == "blocked":

        assert computed_score < 50

