"""API 健康检查与基础路由测试。

使用 FastAPI TestClient 验证核心端点可达，不依赖外部 LLM 服务。
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from main import app

    with TestClient(app) as c:
        yield c


class TestHealthEndpoint:
    def test_health_returns_ok(self, client: TestClient):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"

    def test_health_reports_subsystem_flags(self, client: TestClient):
        resp = client.get("/api/health")
        body = resp.json()
        assert "llm_configured" in body
        assert "trace_python" in body
        assert body["trace_python"] is True

    def test_health_hints_is_list(self, client: TestClient):
        resp = client.get("/api/health")
        body = resp.json()
        assert isinstance(body["hints"], list)


class TestAuthEndpoint:
    def test_login_missing_credentials_returns_422(self, client: TestClient):
        resp = client.post("/api/auth/login", json={})
        assert resp.status_code == 422

    def test_login_nonexistent_user_returns_401(self, client: TestClient):
        resp = client.post(
            "/api/auth/login",
            json={"username": "__nonexistent_user__", "password": "wrong"},
        )
        assert resp.status_code in (401, 400)

    def test_oj_run_requires_authentication(self, client: TestClient):
        resp = client.post(
            "/api/oj/problems/binary-search/run",
            json={"code": "print(1)", "language": "python"},
        )
        assert resp.status_code == 401


class TestApiNotFound:
    def test_unknown_api_route_returns_404(self, client: TestClient):
        resp = client.get("/api/__nonexistent_route__")
        assert resp.status_code == 404
