from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from api.deps import get_current_user
from core.database import Base, get_db
from main import app
from models.db_models import (
    GeneratedResource,
    OjSubmission,
    StudentLearningMemory,
    StudentProfile,
    User,
)


@pytest.fixture
def dashboard_db() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _request_summary(db: Session, current_user: User) -> dict:
    def override_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: current_user
    try:
        response = TestClient(app).get("/api/teacher/dashboard-summary")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    return response.json()


def test_dashboard_summary_returns_empty_state_without_class_data(
    dashboard_db: Session,
) -> None:
    teacher = User(
        username="teacher_empty",
        hashed_password="not-used",
        role="teacher",
    )
    dashboard_db.add(teacher)
    dashboard_db.commit()

    data = _request_summary(dashboard_db, teacher)

    assert data["overview"] == {
        "student_count": 0,
        "profile_count": 0,
        "average_mastery": 0.0,
        "resource_count": 0,
        "oj_submission_count": 0,
    }
    assert data["weak_knowledge_points"] == []
    assert data["error_types"] == []
    assert data["teaching_suggestions"] == []
    assert data["reinforcement_packs"] == []
    assert data["data_note"]


def test_dashboard_summary_aggregates_existing_learning_records(
    dashboard_db: Session,
) -> None:
    teacher = User(username="teacher_real", hashed_password="not-used", role="teacher")
    student_a = User(username="student_a", hashed_password="not-used", role="student")
    student_b = User(username="student_b", hashed_password="not-used", role="student")
    dashboard_db.add_all([teacher, student_a, student_b])
    dashboard_db.flush()

    dashboard_db.add_all(
        [
            StudentProfile(
                user_id=student_a.id,
                summary="",
                dimensions={
                    "_mastery_cache": {
                        "_course": {"mastery_score": 60},
                    }
                },
                chat_history=[],
            ),
            StudentProfile(
                user_id=student_b.id,
                summary="",
                dimensions={
                    "_evaluation_history": [
                        {"overall_score": 80},
                    ]
                },
                chat_history=[],
            ),
            GeneratedResource(
                user_id=student_a.id,
                resource_type="document",
                agent_name="ConceptAgent",
                title="链表补强",
                content="content",
                meta={"module_key": "linked-list"},
            ),
            StudentLearningMemory(
                user_id=student_a.id,
                course_id="data_structures_algorithms",
                chapter_id="ch02-linear-list",
                skill_id="linear-list-operation",
                problem_slug="reverse-linked-list",
                event_type="oj_submit_fail",
                observed_error_pattern="指针更新错误，next 指针覆盖导致断链",
                failed_strategy="WA",
                evidence_json={
                    "module_key": "linked-list",
                    "verdict": "WA",
                    "error_type": "pointer_update_error",
                },
            ),
            StudentLearningMemory(
                user_id=student_b.id,
                course_id="data_structures_algorithms",
                chapter_id="ch11-dynamic-programming",
                skill_id="dp-state-design",
                problem_slug="climbing-stairs",
                event_type="oj_submit_fail",
                observed_error_pattern="边界初始化遗漏",
                failed_strategy="WA",
                evidence_json={
                    "module_key": "dp",
                    "verdict": "WA",
                    "error_type": "boundary_condition_error",
                },
            ),
            StudentLearningMemory(
                user_id=student_b.id,
                course_id="data_structures_algorithms",
                chapter_id="ch11-dynamic-programming",
                skill_id="dp-state-design",
                problem_slug="climbing-stairs",
                event_type="oj_submit_success",
                observed_error_pattern="",
                failed_strategy="",
                evidence_json={"module_key": "dp", "verdict": "AC"},
            ),
            # H1 修复后：OJ 提交数从 OjSubmission 表查询，需创建对应真实提交记录
            OjSubmission(
                user_id=student_a.id,
                problem_slug="reverse-linked-list",
                language="python",
                code="",
                verdict="WA",
                passed=0,
                total=2,
                compile_error="",
                cases=[],
                runtime_ms_avg=0,
            ),
            OjSubmission(
                user_id=student_b.id,
                problem_slug="climbing-stairs",
                language="python",
                code="",
                verdict="WA",
                passed=0,
                total=3,
                compile_error="",
                cases=[],
                runtime_ms_avg=0,
            ),
            OjSubmission(
                user_id=student_b.id,
                problem_slug="climbing-stairs",
                language="python",
                code="",
                verdict="AC",
                passed=3,
                total=3,
                compile_error="",
                cases=[],
                runtime_ms_avg=0,
            ),
        ]
    )
    dashboard_db.commit()

    data = _request_summary(dashboard_db, teacher)

    assert data["overview"] == {
        "student_count": 2,
        "profile_count": 2,
        "average_mastery": 70.0,
        "resource_count": 1,
        "oj_submission_count": 3,
    }
    assert {item["module_key"] for item in data["weak_knowledge_points"]} == {
        "linked-list",
        "dp",
    }
    assert len(data["teaching_suggestions"]) == 3
    assert {item["module_key"] for item in data["reinforcement_packs"]} == {
        "linked-list",
        "dp",
    }


def _request_student_detail(db: Session, current_user: User, user_id: int) -> dict:
    def override_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: current_user
    try:
        response = TestClient(app).get(f"/api/teacher/students/{user_id}")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200, response.text
    return response.json()


def test_student_detail_returns_complete_visualization_fields(
    dashboard_db: Session,
) -> None:
    """验证学生详情接口返回所有可视化扩展字段，并能处理真实数据。"""
    teacher = User(username="teacher_detail", hashed_password="not-used", role="teacher")
    student = User(username="student_detail", hashed_password="not-used", role="student")
    dashboard_db.add_all([teacher, student])
    dashboard_db.flush()

    dashboard_db.add_all(
        [
            StudentProfile(
                user_id=student.id,
                summary="该学生擅长链表但二叉树较弱。",
                dimensions={
                    "knowledge_base": "线性表基础扎实，树结构较薄弱。",
                    "cognitive_style": "偏好图示讲解。",
                    "_dimension_scores": {
                        "knowledge_base": 7,
                        "cognitive_style": 6,
                    },
                    "_mastery_cache": {
                        "ch02-linear-list": {"mastery_score": 72},
                        "ch05-tree-binary-tree": {"mastery_score": 38},
                    },
                },
                chat_history=[],
            ),
            StudentLearningMemory(
                user_id=student.id,
                course_id="data_structures_algorithms",
                chapter_id="ch05-tree-binary-tree",
                skill_id="binary-tree-traversal",
                problem_slug="binary-tree-inorder-traversal",
                event_type="oj_submit_fail",
                observed_error_pattern="递归终止条件遗漏",
                failed_strategy="WA",
                evidence_json={
                    "module_key": "binary-tree",
                    "verdict": "WA",
                    "error_type": "boundary_condition",
                    "mastery_score": 35,
                },
            ),
            OjSubmission(
                user_id=student.id,
                problem_slug="binary-tree-inorder-traversal",
                language="python",
                code="",
                verdict="WA",
                passed=1,
                total=3,
                compile_error="",
                cases=[],
                runtime_ms_avg=12,
            ),
            OjSubmission(
                user_id=student.id,
                problem_slug="reverse-linked-list",
                language="python",
                code="",
                verdict="AC",
                passed=2,
                total=2,
                compile_error="",
                cases=[],
                runtime_ms_avg=8,
            ),
            GeneratedResource(
                user_id=student.id,
                resource_type="trace",
                agent_name="TraceAgent",
                title="中序遍历过程动画",
                content="",
                meta={},
            ),
        ]
    )
    dashboard_db.commit()

    data = _request_student_detail(dashboard_db, teacher, student.id)

    # 基础字段
    assert data["user_id"] == student.id
    assert data["username"] == "student_detail"
    assert data["oj_submissions"] == 2
    assert data["oj_accepted"] == 1
    assert data["resource_count"] == 1

    # 可视化扩展字段全部存在
    expected_fields = [
        "dimension_stats",
        "oj_verdict_breakdown",
        "oj_recent_submissions",
        "error_type_breakdown",
        "resource_type_breakdown",
        "activity_timeline",
        "skill_mastery",
        "learning_streak_days",
        "profile_completeness",
        "data_completeness_note",
    ]
    for field in expected_fields:
        assert field in data, f"缺少字段 {field}"

    # 六维画像必为 6 项
    assert len(data["dimension_stats"]) == 6
    labels = {dim["label"] for dim in data["dimension_stats"]}
    assert "知识基础" in labels and "抗挫折心理" in labels

    # explicit 维度（knowledge_base/cognitive_style）应标记为 explicit
    kb = next(d for d in data["dimension_stats"] if d["key"] == "knowledge_base")
    assert kb["score"] == 7
    # confidence 字段在 _dimension_confidence 缺失时，已填文本默认按 explicit 处理
    assert kb["confidence"] in ("explicit", "inferred")

    # 缺失维度应标记为 inferred 且分数 < 5
    coding = next(d for d in data["dimension_stats"] if d["key"] == "coding_ability")
    assert coding["confidence"] == "inferred"
    assert coding["score"] < 5

    # 完成度应 < 50（只有 2 个 explicit 维度，2/6≈33.3%）
    assert data["profile_completeness"] < 50
    assert data["profile_completeness"] > 0

    # OJ verdict 分布：AC=1, WA=1, 其他=0
    verdict_map = {v["verdict"]: v["count"] for v in data["oj_verdict_breakdown"]}
    assert verdict_map.get("AC") == 1
    assert verdict_map.get("WA") == 1
    assert verdict_map.get("TLE") == 0

    # 最近 OJ 提交按时间倒序，最多 8 条
    assert len(data["oj_recent_submissions"]) == 2
    assert data["oj_recent_submissions"][0]["verdict"] in ("AC", "WA")

    # 错误类型分布应包含 boundary_condition
    error_types = [e["error_type"] for e in data["error_type_breakdown"]]
    assert "boundary_condition" in error_types

    # 资源类型分布应包含 trace
    resource_types = [r["resource_type"] for r in data["resource_type_breakdown"]]
    assert "trace" in resource_types

    # 活跃时间线应合并多源数据
    assert len(data["activity_timeline"]) >= 2
    for item in data["activity_timeline"]:
        assert item["label"]
        assert item["icon"]

    # 技能掌握度应包含 binary-tree-traversal
    skill_ids = [s["skill_id"] for s in data["skill_mastery"]]
    assert "binary-tree-traversal" in skill_ids

    # 学习连续天数应为正整数
    assert data["learning_streak_days"] >= 1

    # 数据完整度说明应非空
    assert data["data_completeness_note"]


def test_student_detail_handles_completely_empty_student(
    dashboard_db: Session,
) -> None:
    """验证学生无任何学习数据时也能稳定返回（全推断补全）。"""
    teacher = User(username="teacher_empty_detail", hashed_password="not-used", role="teacher")
    student = User(username="student_empty", hashed_password="not-used", role="student")
    dashboard_db.add_all([teacher, student])
    dashboard_db.commit()

    data = _request_student_detail(dashboard_db, teacher, student.id)

    # 全空学生也应返回完整的 6 维推断画像
    assert len(data["dimension_stats"]) == 6
    for dim in data["dimension_stats"]:
        assert dim["confidence"] == "inferred"
        assert dim["score"] < 5  # 推断分应 < 5
        assert dim["text"]  # 应有推断描述

    # 完成度应为 0
    assert data["profile_completeness"] == 0

    # OJ verdict 分布 5 个 verdict 都为 0
    assert len(data["oj_verdict_breakdown"]) == 5
    assert all(v["count"] == 0 for v in data["oj_verdict_breakdown"])

    # 最近提交为空
    assert data["oj_recent_submissions"] == []

    # 错误类型分布有占位项（count=0）
    assert len(data["error_type_breakdown"]) == 1
    assert data["error_type_breakdown"][0]["count"] == 0

    # 资源类型分布为空
    assert data["resource_type_breakdown"] == []

    # 活跃时间线为空
    assert data["activity_timeline"] == []

    # 技能掌握度为空
    assert data["skill_mastery"] == []

    # 学习连续天数为 1-3
    assert 1 <= data["learning_streak_days"] <= 3

    # 数据完整度说明应提示数据缺失
    assert "OJ" in data["data_completeness_note"] or "暂无" in data["data_completeness_note"]
