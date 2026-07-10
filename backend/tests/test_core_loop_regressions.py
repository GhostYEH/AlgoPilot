from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from core.config import settings
from main import app


client = TestClient(app)


def _register_user() -> dict[str, str]:
    name = f"core_loop_{uuid.uuid4().hex[:10]}"
    response = client.post(
        "/api/auth/register",
        json={
            "username": name,
            "password": "secret123",
            "email": f"{name}@example.com",
        },
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_new_student_gets_baseline_profile_and_initial_path() -> None:
    headers = _register_user()
    profile_response = client.get(
        "/api/orchestrator/persona/profile",
        headers=headers,
    )
    assert profile_response.status_code == 200, profile_response.text
    profile = profile_response.json()
    assert profile["updated_at"] is None
    assert profile["fallback"] is True
    assert len(profile["dimensions"]) == 6
    assert all(profile["dimensions"].values())
    assert len(profile["dimension_scores"]) == 6
    assert len(profile["coverage_missing"]) == 6

    with patch.object(settings, "spark_api_password", ""):
        path_response = client.get(
            "/api/orchestrator/learning-path/plan",
            headers=headers,
        )
    assert path_response.status_code == 200, path_response.text
    plan = path_response.json()["plan"]
    assert plan is not None
    required = {"sorting", "linked-list", "binary-tree", "graph", "dp"}
    assert required.issubset(set(plan["ordered_keys"]))
    steps = {step["module_key"]: step for step in plan["steps"]}
    assert steps["sorting"]["prerequisites"]
    assert "binary-tree" in steps["graph"]["prerequisites"]


def test_single_resource_generation_falls_back_without_llm_key() -> None:
    headers = _register_user()
    with patch.object(settings, "spark_api_password", ""):
        response = client.post(
            "/api/orchestrator/resources/generate",
            headers=headers,
            json={
                "resource_type": "document",
                "topic": "linked list",
                "module_key": "linked-list",
            },
        )
    assert response.status_code == 200, response.text
    resource = response.json()["resource"]
    assert resource["meta"]["fallback"] is True
    assert resource["meta"]["generated_by"] == "TemplateFallbackAgent"
    assert resource["meta"]["module_key"] == "linked-list"


def test_failed_submit_carries_problem_learning_context() -> None:
    headers = _register_user()
    response = client.post(
        "/api/oj/problems/reverse-linked-list/submit",
        headers=headers,
        json={
            "language": "python",
            "code": "class Solution:\n    def reverseList(self, head):\n        return head",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["verdict"] != "AC"
    assert body["event_id"]
    details = " ".join(log.get("detail", "") for log in body["event_logs"])
    assert "memory_id=" in details


def test_trace_diagnosis_preserves_judge_verdict() -> None:
    diagnosis = {
        "bug_step_index": 0,
        "diagnosis_title": "runtime failure",
        "detailed_analysis": "invalid access",
        "source": "fallback",
    }
    with patch(
        "api.oj.diagnose_trace_bug",
        new_callable=AsyncMock,
        return_value=diagnosis,
    ) as mocked:
        response = client.post(
            "/api/oj/problems/two-sum/diagnose",
            json={
                "code": (
                    "class Solution:\n"
                    "    def twoSum(self, nums, target):\n"
                    "        return []"
                ),
                "language": "python",
                "judge_verdict": "RE",
                "steps": [{"line": 2, "changed": [], "vars": {}}],
            },
        )
    assert response.status_code == 200, response.text
    assert mocked.await_args.kwargs["judge_verdict"] == "RE"
