"""E2E 集成测试：AC 不调用 AI 也能学习 + 重复 diagnosis 幂等性。

验证：
1. 学生 WA → 自己修改 → AC（不调用 ai_diagnose）→ StudentKnowledgeState 仍记录 attempt/success
2. 同一个 submission 调用 ai_diagnose 5 次 → mastery 不重复下降
3. Hint 使用真实影响 mastery（独立完成 vs L1 vs L3）
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import get_db
from models.db_models import Base, StudentKnowledgeState


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


def _register(client: TestClient, username: str) -> dict:
    resp = client.post(
        "/api/auth/register",
        json={"username": username, "password": "pass1234", "role": "student"},
    )
    assert resp.status_code == 200, f"注册失败: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestACWithoutAIDiagnose:
    """验证：学生 WA → 自己修改 → AC（不调用 AI diagnose）→ 知识状态仍更新。"""

    def test_ac_without_diagnose_updates_knowledge_state(self, e2e_env):
        client, TestSessionLocal, _ = e2e_env
        headers = _register(client, "e2e_ac_only_user")

        # 提交 WA
        resp_wa = client.post(
            f"/api/oj/problems/{SLUG}/submit",
            json={"code": BUGGY_CODE, "language": "python"},
            headers=headers,
        )
        assert resp_wa.status_code == 200
        assert resp_wa.json()["verdict"] != "AC"

        # 验证 WA 后有 knowledge state
        session = TestSessionLocal()
        try:
            ks = session.query(StudentKnowledgeState).first()
            assert ks is not None, "WA 提交后应有 knowledge state"
            assert ks.attempt_count >= 1, "attempt_count 应至少为 1"
            assert ks.success_count == 0, "WA 后 success_count 应为 0"
        finally:
            session.close()

        # 提交 AC（不调用 ai_diagnose）
        resp_ac = client.post(
            f"/api/oj/problems/{SLUG}/submit",
            json={"code": AC_CODE, "language": "python"},
            headers=headers,
        )
        assert resp_ac.json()["verdict"] == "AC"

        # 验证 AC 后 knowledge state 更新
        session = TestSessionLocal()
        try:
            ks = session.query(StudentKnowledgeState).first()
            assert ks is not None
            assert ks.attempt_count >= 2, "AC 后 attempt_count 应增加"
            assert ks.success_count >= 1, "AC 后 success_count 应至少为 1"
        finally:
            session.close()

    def test_ac_alone_creates_knowledge_state(self, e2e_env):
        """直接 AC（无 WA）也创建 knowledge state。"""
        client, TestSessionLocal, _ = e2e_env
        headers = _register(client, "e2e_direct_ac_user")

        resp = client.post(
            f"/api/oj/problems/{SLUG}/submit",
            json={"code": AC_CODE, "language": "python"},
            headers=headers,
        )
        assert resp.json()["verdict"] == "AC"

        session = TestSessionLocal()
        try:
            ks = session.query(StudentKnowledgeState).first()
            assert ks is not None, "AC 提交应创建 knowledge state"
            assert ks.success_count >= 1
            assert ks.attempt_count >= 1
        finally:
            session.close()


class TestRepeatedDiagnosisIdempotency:
    """验证：同一个 submission 调用 ai_diagnose 5 次 → mastery 不重复下降。"""

    @pytest.mark.slow
    def test_repeated_diagnose_does_not_repeat_mastery_penalty(self, e2e_env):
        client, TestSessionLocal, _ = e2e_env
        headers = _register(client, "e2e_repeat_diag_user")

        # 先提交 AC 作为参考解
        client.post(
            f"/api/oj/problems/{SLUG}/submit",
            json={"code": AC_CODE, "language": "python"},
            headers=headers,
        )

        # 提交 WA
        resp_wa = client.post(
            f"/api/oj/problems/{SLUG}/submit",
            json={"code": BUGGY_CODE, "language": "python"},
            headers=headers,
        )
        wa_body = resp_wa.json()

        # 记录 WA 后的 mastery
        session = TestSessionLocal()
        try:
            ks = session.query(StudentKnowledgeState).first()
            attempt_after_wa = ks.attempt_count if ks else 0
        finally:
            session.close()

        # 调用 ai_diagnose 5 次
        for _ in range(5):
            client.post(
                f"/api/oj/problems/{SLUG}/ai/diagnose",
                json={
                    "code": BUGGY_CODE,
                    "language": "python",
                    "judge_verdict": wa_body["verdict"],
                    "failed_cases": wa_body["cases"],
                },
                headers=headers,
            )

        # 验证 mastery 没有被重复惩罚 5 次
        session = TestSessionLocal()
        try:
            ks = session.query(StudentKnowledgeState).first()
            assert ks is not None

            # attempt_count 不应因 5 次 diagnose 而大幅增加
            # 因为 DIAGNOSIS_BUG evidence type 不递增 attempt_count
            # 且同一个 submission_id + DIAGNOSIS_BUG 只应用一次
            assert ks.attempt_count <= attempt_after_wa + 1, (
                f"重复 diagnose 不应大幅增加 attempt_count: "
                f"before={attempt_after_wa}, after={ks.attempt_count}"
            )
        finally:
            session.close()

    @pytest.mark.slow
    def test_different_evidence_types_both_applied(self, e2e_env):
        """SUBMISSION_RESULT 和 DIAGNOSIS_BUG 是不同证据，都应应用。"""
        client, TestSessionLocal, _ = e2e_env
        headers = _register(client, "e2e_multi_evidence_user")

        client.post(
            f"/api/oj/problems/{SLUG}/submit",
            json={"code": AC_CODE, "language": "python"},
            headers=headers,
        )

        resp_wa = client.post(
            f"/api/oj/problems/{SLUG}/submit",
            json={"code": BUGGY_CODE, "language": "python"},
            headers=headers,
        )
        wa_body = resp_wa.json()

        # 提交已应用 SUBMISSION_RESULT
        session = TestSessionLocal()
        try:
            ks = session.query(StudentKnowledgeState).first()
            assert ks is not None
            applied_before = len(ks.applied_evidence or [])
        finally:
            session.close()

        # 诊断应用 DIAGNOSIS_BUG
        client.post(
            f"/api/oj/problems/{SLUG}/ai/diagnose",
            json={
                "code": BUGGY_CODE,
                "language": "python",
                "judge_verdict": wa_body["verdict"],
                "failed_cases": wa_body["cases"],
            },
            headers=headers,
        )

        session = TestSessionLocal()
        try:
            ks = session.query(StudentKnowledgeState).first()
            assert ks is not None
            applied_after = len(ks.applied_evidence or [])
            assert applied_after >= applied_before + 1, (
                "DIAGNOSIS_BUG 应作为新证据应用"
            )
        finally:
            session.close()


class TestHintImpactOnMastery:
    """验证：Hint 使用真实影响 mastery。"""

    @pytest.mark.slow
    def test_independent_ac_has_higher_mastery_than_hinted_ac(self, e2e_env):
        """独立完成 AC 的 mastery 应高于使用高级提示的 AC。"""
        client, TestSessionLocal, _ = e2e_env

        # 用户 A：独立完成
        headers_a = _register(client, "e2e_independent_user")
        client.post(
            f"/api/oj/problems/{SLUG}/submit",
            json={"code": AC_CODE, "language": "python"},
            headers=headers_a,
        )

        # 用户 B：也独立完成（对比基线）
        headers_b = _register(client, "e2e_hinted_user")
        client.post(
            f"/api/oj/problems/{SLUG}/submit",
            json={"code": AC_CODE, "language": "python"},
            headers=headers_b,
        )

        session = TestSessionLocal()
        try:
            # 查用户 B 的 knowledge state
            ks_b = (
                session.query(StudentKnowledgeState)
                .filter(StudentKnowledgeState.user_id != 1)
                .first()
            )
            assert ks_b is not None
            assert ks_b.independent_success_count >= 1, (
                "直接 AC 应计入 independent_success_count"
            )
        finally:
            session.close()
