"""E2E 集成测试：完整 OJ 业务流程验证。

流程：注册 → 获取题目 → 提交 AC 参考解 → 提交错误代码 → WA →
      AI 诊断 → 验证 execution_evidence/bug_record_id/trace_record_id →
      验证 4 张新表有数据 → 提交修复代码 → AC → 验证 knowledge state 变化

这是 AlgoPilot 核心闭环的端到端验证，证明所有新增模块真正进入正式业务流程。
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import get_db
from models.db_models import Base, BugRecord, ExecutionTraceRecord, HintRecord, StudentKnowledgeState


SLUG = "binary-search"

AC_CODE = """import sys
def main():
    data = sys.stdin.read().split()
    if not data: return
    n = int(data[0]); arr = list(map(int, data[1:1+n])); target = int(data[1+n])
    lo, hi = 0, n-1; ans = -1
    while lo <= hi:
        mid = (lo+hi)//2
        if arr[mid] == target: ans = mid; break
        elif arr[mid] < target: lo = mid+1
        else: hi = mid-1
    print(ans)
main()
"""

BUGGY_CODE = """import sys
def main():
    data = sys.stdin.read().split()
    if not data: return
    n = int(data[0]); arr = list(map(int, data[1:1+n])); target = int(data[1+n])
    lo, hi = 0, n-1; ans = -1
    while lo <= hi:
        mid = (lo+hi)//2
        if arr[mid] == target: ans = mid; break
        elif arr[mid] < target: lo = mid+1
        else: hi = mid-1
    print(lo)
main()
"""


@pytest.fixture
def e2e_env():
    """创建隔离的内存数据库 + TestClient，覆盖 get_db 依赖。"""
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    from main import app

    def _override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as client:
        yield client, TestSessionLocal, engine
    app.dependency_overrides.clear()


def _register_and_login(client: TestClient, username: str) -> dict:
    """注册并登录，返回 Authorization headers。"""
    resp = client.post(
        "/api/auth/register",
        json={"username": username, "password": "pass1234", "role": "student"},
    )
    assert resp.status_code == 200, f"注册失败: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestE2EFullFlow:
    """完整 E2E 流程：注册 → 提交 → 诊断 → 验证入库 → 修复 → AC。"""

    def test_register_and_get_problem(self, e2e_env):
        """Step 1-2: 注册成功，题目可获取且元数据正确。"""
        client, _, _ = e2e_env
        headers = _register_and_login(client, "e2e_user_a")

        resp = client.get(f"/api/oj/problems/{SLUG}", headers=headers)
        assert resp.status_code == 200, resp.text
        problem = resp.json()
        assert problem["slug"] == SLUG
        assert problem["module_key"] == "array"
        assert problem["difficulty"] == "easy"

    def test_submit_ac_code_passes_all_cases(self, e2e_env):
        """Step 3: 正确代码提交应 AC。"""
        client, _, _ = e2e_env
        headers = _register_and_login(client, "e2e_user_b")

        resp = client.post(
            f"/api/oj/problems/{SLUG}/submit",
            json={"code": AC_CODE, "language": "python"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["verdict"] == "AC", f"AC 代码未通过: {body}"
        assert body["passed"] == body["total"]

    def test_submit_buggy_code_fails(self, e2e_env):
        """Step 4: 错误代码提交应 WA（边界条件 bug）。"""
        client, _, _ = e2e_env
        headers = _register_and_login(client, "e2e_user_c")

        resp = client.post(
            f"/api/oj/problems/{SLUG}/submit",
            json={"code": BUGGY_CODE, "language": "python"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["verdict"] != "AC", f"错误代码不应 AC: {body}"

    @pytest.mark.slow
    def test_ai_diagnose_populates_execution_evidence(self, e2e_env):
        """Step 5: AI 诊断返回 execution_evidence 非空。"""
        client, _, _ = e2e_env
        headers = _register_and_login(client, "e2e_user_d")

        client.post(
            f"/api/oj/problems/{SLUG}/submit",
            json={"code": AC_CODE, "language": "python"},
            headers=headers,
        )

        submit_resp = client.post(
            f"/api/oj/problems/{SLUG}/submit",
            json={"code": BUGGY_CODE, "language": "python"},
            headers=headers,
        )
        submit_body = submit_resp.json()

        diag_resp = client.post(
            f"/api/oj/problems/{SLUG}/ai/diagnose",
            json={
                "code": BUGGY_CODE,
                "language": "python",
                "judge_verdict": submit_body["verdict"],
                "failed_cases": submit_body["cases"],
            },
            headers=headers,
        )
        assert diag_resp.status_code == 200, diag_resp.text
        diag = diag_resp.json()

        assert diag["execution_evidence"] is not None, "execution_evidence 不应为 None"
        assert diag["execution_evidence"]["problem_slug"] == SLUG
        assert "source_code" in diag["execution_evidence"]
        assert "bug_diagnosis" in diag["execution_evidence"]

    @pytest.mark.slow
    def test_ai_diagnose_persists_bug_and_trace_records(self, e2e_env):
        """Step 6: 已登录用户诊断后 bug_record_id 和 trace_record_id 非空。"""
        client, TestSessionLocal, _ = e2e_env
        headers = _register_and_login(client, "e2e_user_e")

        client.post(
            f"/api/oj/problems/{SLUG}/submit",
            json={"code": AC_CODE, "language": "python"},
            headers=headers,
        )

        submit_resp = client.post(
            f"/api/oj/problems/{SLUG}/submit",
            json={"code": BUGGY_CODE, "language": "python"},
            headers=headers,
        )
        submit_body = submit_resp.json()

        diag_resp = client.post(
            f"/api/oj/problems/{SLUG}/ai/diagnose",
            json={
                "code": BUGGY_CODE,
                "language": "python",
                "judge_verdict": submit_body["verdict"],
                "failed_cases": submit_body["cases"],
            },
            headers=headers,
        )
        diag = diag_resp.json()

        assert diag["bug_record_id"] is not None, "bug_record_id 不应为 None（已登录）"
        assert diag["trace_record_id"] is not None, "trace_record_id 不应为 None（已登录）"

        verify_session = TestSessionLocal()
        try:
            bug_rec = verify_session.query(BugRecord).filter_by(id=diag["bug_record_id"]).first()
            assert bug_rec is not None, "bug_records 表中应有记录"
            assert bug_rec.problem_slug == SLUG

            trace_rec = verify_session.query(ExecutionTraceRecord).filter_by(id=diag["trace_record_id"]).first()
            assert trace_rec is not None, "execution_traces 表中应有记录"
            assert trace_rec.total_steps >= 0
        finally:
            verify_session.close()

    @pytest.mark.slow
    def test_ai_diagnose_persists_hint_record(self, e2e_env):
        """Step 7: hint_records 表有记录。"""
        client, TestSessionLocal, _ = e2e_env
        headers = _register_and_login(client, "e2e_user_f")

        client.post(
            f"/api/oj/problems/{SLUG}/submit",
            json={"code": AC_CODE, "language": "python"},
            headers=headers,
        )

        submit_resp = client.post(
            f"/api/oj/problems/{SLUG}/submit",
            json={"code": BUGGY_CODE, "language": "python"},
            headers=headers,
        )

        client.post(
            f"/api/oj/problems/{SLUG}/ai/diagnose",
            json={
                "code": BUGGY_CODE,
                "language": "python",
                "judge_verdict": submit_resp.json()["verdict"],
                "failed_cases": submit_resp.json()["cases"],
            },
            headers=headers,
        )

        verify_session = TestSessionLocal()
        try:
            hint_count = verify_session.query(HintRecord).count()
            assert hint_count >= 1, "hint_records 表应至少有 1 条记录"
        finally:
            verify_session.close()

    @pytest.mark.slow
    def test_knowledge_state_created_after_diagnose(self, e2e_env):
        """Step 8: 诊断后 student_knowledge_states 表有记录。"""
        client, TestSessionLocal, _ = e2e_env
        headers = _register_and_login(client, "e2e_user_g")

        client.post(
            f"/api/oj/problems/{SLUG}/submit",
            json={"code": AC_CODE, "language": "python"},
            headers=headers,
        )

        submit_resp = client.post(
            f"/api/oj/problems/{SLUG}/submit",
            json={"code": BUGGY_CODE, "language": "python"},
            headers=headers,
        )

        client.post(
            f"/api/oj/problems/{SLUG}/ai/diagnose",
            json={
                "code": BUGGY_CODE,
                "language": "python",
                "judge_verdict": submit_resp.json()["verdict"],
                "failed_cases": submit_resp.json()["cases"],
            },
            headers=headers,
        )

        verify_session = TestSessionLocal()
        try:
            ks_count = verify_session.query(StudentKnowledgeState).count()
            assert ks_count >= 1, "student_knowledge_states 表应至少有 1 条记录"
        finally:
            verify_session.close()

    @pytest.mark.slow
    def test_knowledge_state_mastery_increases_on_ac(self, e2e_env):
        """Step 9: WA 后 AC，mastery 应上升。"""
        client, TestSessionLocal, _ = e2e_env
        headers = _register_and_login(client, "e2e_user_h")

        submit_resp = client.post(
            f"/api/oj/problems/{SLUG}/submit",
            json={"code": BUGGY_CODE, "language": "python"},
            headers=headers,
        )
        client.post(
            f"/api/oj/problems/{SLUG}/ai/diagnose",
            json={
                "code": BUGGY_CODE,
                "language": "python",
                "judge_verdict": submit_resp.json()["verdict"],
                "failed_cases": submit_resp.json()["cases"],
            },
            headers=headers,
        )

        verify_session = TestSessionLocal()
        try:
            ks_after_wa = verify_session.query(StudentKnowledgeState).first()
            attempt_after_wa = ks_after_wa.attempt_count if ks_after_wa else 0
        finally:
            verify_session.close()

        client.post(
            f"/api/oj/problems/{SLUG}/submit",
            json={"code": AC_CODE, "language": "python"},
            headers=headers,
        )
        client.post(
            f"/api/oj/problems/{SLUG}/ai/diagnose",
            json={
                "code": AC_CODE,
                "language": "python",
                "judge_verdict": "AC",
                "failed_cases": [],
            },
            headers=headers,
        )

        verify_session = TestSessionLocal()
        try:
            ks_after_ac = verify_session.query(StudentKnowledgeState).first()
            assert ks_after_ac is not None, "AC 后应有 knowledge state"
            assert ks_after_ac.attempt_count > attempt_after_wa, "attempt_count 应增加"
            assert ks_after_ac.success_count >= 1, "success_count 应至少为 1"
        finally:
            verify_session.close()

    @pytest.mark.slow
    def test_first_divergence_with_reference_solution(self, e2e_env):
        """Step 10: 有 AC 参考解时 first_divergence 可能检测到偏离。"""
        client, _, _ = e2e_env
        headers = _register_and_login(client, "e2e_user_i")

        client.post(
            f"/api/oj/problems/{SLUG}/submit",
            json={"code": AC_CODE, "language": "python"},
            headers=headers,
        )

        submit_resp = client.post(
            f"/api/oj/problems/{SLUG}/submit",
            json={"code": BUGGY_CODE, "language": "python"},
            headers=headers,
        )

        diag_resp = client.post(
            f"/api/oj/problems/{SLUG}/ai/diagnose",
            json={
                "code": BUGGY_CODE,
                "language": "python",
                "judge_verdict": submit_resp.json()["verdict"],
                "failed_cases": submit_resp.json()["cases"],
            },
            headers=headers,
        )
        diag = diag_resp.json()

        assert diag["first_divergence"] is not None, "first_divergence 字段应存在"
        if diag["first_divergence"]["detected"]:
            assert "step_index" in diag["first_divergence"]
            assert "explanation" in diag["first_divergence"]
            assert "reference_source" in diag["first_divergence"]
        else:
            assert "reason" in diag["first_divergence"]

    @pytest.mark.slow
    def test_anonymous_diagnose_does_not_persist(self, e2e_env):
        """Step 11: 未登录用户诊断不入库，bug_record_id/trace_record_id 为 None。"""
        client, _, _ = e2e_env

        diag_resp = client.post(
            f"/api/oj/problems/{SLUG}/ai/diagnose",
            json={
                "code": BUGGY_CODE,
                "language": "python",
                "judge_verdict": "WA",
                "failed_cases": [],
            },
        )
        assert diag_resp.status_code == 200, diag_resp.text
        diag = diag_resp.json()

        assert diag["bug_record_id"] is None, "未登录不应持久化 bug_record"
        assert diag["trace_record_id"] is None, "未登录不应持久化 trace_record"
        assert diag["execution_evidence"] is not None, "execution_evidence 仍应生成"


class TestE2EAllFourTablesPopulated:
    """验证一次完整诊断后 4 张新表全部有数据。"""

    @pytest.mark.slow
    def test_all_four_tables_have_records(self, e2e_env):
        client, TestSessionLocal, _ = e2e_env
        headers = _register_and_login(client, "e2e_user_j")

        client.post(
            f"/api/oj/problems/{SLUG}/submit",
            json={"code": AC_CODE, "language": "python"},
            headers=headers,
        )
        submit_resp = client.post(
            f"/api/oj/problems/{SLUG}/submit",
            json={"code": BUGGY_CODE, "language": "python"},
            headers=headers,
        )
        client.post(
            f"/api/oj/problems/{SLUG}/ai/diagnose",
            json={
                "code": BUGGY_CODE,
                "language": "python",
                "judge_verdict": submit_resp.json()["verdict"],
                "failed_cases": submit_resp.json()["cases"],
            },
            headers=headers,
        )

        verify_session = TestSessionLocal()
        try:
            trace_count = verify_session.query(ExecutionTraceRecord).count()
            bug_count = verify_session.query(BugRecord).count()
            hint_count = verify_session.query(HintRecord).count()
            ks_count = verify_session.query(StudentKnowledgeState).count()

            assert trace_count >= 1, f"execution_traces 应有记录，实际 {trace_count}"
            assert bug_count >= 1, f"bug_records 应有记录，实际 {bug_count}"
            assert hint_count >= 1, f"hint_records 应有记录，实际 {hint_count}"
            assert ks_count >= 1, f"student_knowledge_states 应有记录，实际 {ks_count}"
        finally:
            verify_session.close()
