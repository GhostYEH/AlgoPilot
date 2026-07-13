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


def test_submit_persists_real_record_retrievable_via_submissions_api() -> None:
    """每次提交应将代码、判题结果与用例详情写入数据库，可通过列表/详情接口查回。"""
    headers = _register_user()
    code = "class Solution:\n    def reverseList(self, head):\n        return head"

    submit_resp = client.post(
        "/api/oj/problems/reverse-linked-list/submit",
        headers=headers,
        json={"language": "python", "code": code},
    )
    assert submit_resp.status_code == 200, submit_resp.text
    submit_body = submit_resp.json()
    assert submit_body["verdict"] != "AC"

    list_resp = client.get(
        "/api/oj/problems/reverse-linked-list/submissions",
        headers=headers,
    )
    assert list_resp.status_code == 200, list_resp.text
    rows = list_resp.json()
    assert rows, "应至少有一条提交记录"
    latest = rows[0]
    assert latest["problem_slug"] == "reverse-linked-list"
    assert latest["language"] == "python"
    assert latest["verdict"] == submit_body["verdict"]
    assert latest["passed"] == submit_body["passed"]
    assert latest["total"] == submit_body["total"]
    assert "code" not in latest  # 列表项不返回代码

    detail_resp = client.get(f"/api/oj/submissions/{latest['id']}", headers=headers)
    assert detail_resp.status_code == 200, detail_resp.text
    detail = detail_resp.json()
    assert detail["code"] == code
    assert detail["compile_error"] == (submit_body["compile_error"] or "")
    assert len(detail["cases"]) == len(submit_body["cases"])
    assert detail["event_id"] == submit_body["event_id"]

    other_headers = _register_user()
    forbidden = client.get(
        f"/api/oj/submissions/{latest['id']}",
        headers=other_headers,
    )
    assert forbidden.status_code == 404  # 不能查到他人提交


def test_submission_list_requires_auth() -> None:
    no_auth = client.get("/api/oj/problems/reverse-linked-list/submissions")
    assert no_auth.status_code == 401


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
