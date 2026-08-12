from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), default="student", server_default="student")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    learning_progress: Mapped[LearningProgress | None] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    student_profile: Mapped[StudentProfile | None] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    generated_resources: Mapped[list[GeneratedResource]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    learning_path_plan: Mapped[LearningPathPlan | None] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    learning_memories: Mapped[list[StudentLearningMemory]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    learning_events: Mapped[list[LearningEventLog]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    oj_submissions: Mapped[list[OjSubmission]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class LearningProgress(Base):
    """每个用户一条记录，JSON 存各前端 localStorage 键对应的进度对象。"""

    __tablename__ = "learning_progress"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, insert_default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="learning_progress")


class StudentProfile(Base):
    """对话式学习画像（≥6 维，JSON 存储）。"""

    __tablename__ = "student_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    summary: Mapped[str] = mapped_column(String(2000), default="", server_default="")
    dimensions: Mapped[dict] = mapped_column(JSON, nullable=False, insert_default=dict)
    chat_history: Mapped[list] = mapped_column(JSON, nullable=False, insert_default=list)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="student_profile")


class GeneratedResource(Base):
    """多智能体生成的个性化学习资源。"""

    __tablename__ = "generated_resources"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    resource_type: Mapped[str] = mapped_column(String(32), index=True)
    agent_name: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(256))
    content: Mapped[str] = mapped_column(String(50000), default="")
    meta: Mapped[dict] = mapped_column(JSON, nullable=False, insert_default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="generated_resources")


class LearningPathPlan(Base):
    """学习路径 Agent 输出的个性化模块顺序。"""

    __tablename__ = "learning_path_plans"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    summary: Mapped[str] = mapped_column(String(500), default="", server_default="")
    rationale: Mapped[str] = mapped_column(String(2000), default="", server_default="")
    next_module_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ordered_keys: Mapped[list] = mapped_column(JSON, nullable=False, insert_default=list)
    steps: Mapped[list] = mapped_column(JSON, nullable=False, insert_default=list)
    progress_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, insert_default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="learning_path_plan")


class StudentLearningMemory(Base):
    """学生学习记忆：错因、Trace 摘要、有效提示与薄弱技能证据。"""

    __tablename__ = "student_learning_memories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[str] = mapped_column(String(64), default="data_structures_algorithms", index=True)
    chapter_id: Mapped[str] = mapped_column(String(80), default="", index=True)
    skill_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    problem_slug: Mapped[str] = mapped_column(String(128), default="", index=True)
    event_type: Mapped[str] = mapped_column(String(32), index=True)
    observed_error_pattern: Mapped[str] = mapped_column(String(500), default="")
    trace_summary: Mapped[str] = mapped_column(String(2000), default="")
    failed_strategy: Mapped[str] = mapped_column(String(500), default="")
    successful_hint: Mapped[str] = mapped_column(String(500), default="")
    mastery_delta: Mapped[int] = mapped_column(default=0)
    evidence_json: Mapped[dict] = mapped_column(JSON, nullable=False, insert_default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="learning_memories")


class LearningEventLog(Base):
    """可审计的学习事件与多智能体处理日志。"""

    __tablename__ = "learning_event_logs"

    event_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    course_id: Mapped[str] = mapped_column(String(64), default="data_structures_algorithms", index=True)
    chapter_id: Mapped[str] = mapped_column(String(80), default="", index=True)
    skill_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, insert_default=dict)
    handled_by: Mapped[list] = mapped_column(JSON, nullable=False, insert_default=list)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    agent_logs: Mapped[list] = mapped_column(JSON, nullable=False, insert_default=list)
    handler_errors: Mapped[list] = mapped_column(JSON, nullable=False, insert_default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    user: Mapped[User] = relationship(back_populates="learning_events")


class OjSubmission(Base):
    """OJ 题目真实提交记录：每次提交保存代码、判题结果与用例详情。"""

    __tablename__ = "oj_submissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    problem_slug: Mapped[str] = mapped_column(String(128), index=True)
    language: Mapped[str] = mapped_column(String(16), default="python")
    code: Mapped[str] = mapped_column(Text, default="")
    verdict: Mapped[str] = mapped_column(String(8), index=True)
    passed: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer, default=0)
    compile_error: Mapped[str] = mapped_column(Text, default="")
    cases: Mapped[list] = mapped_column(JSON, nullable=False, insert_default=list)
    runtime_ms_avg: Mapped[int] = mapped_column(Integer, default=0)
    event_id: Mapped[str | None] = mapped_column(
        String(32),
        ForeignKey("learning_event_logs.event_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    user: Mapped[User] = relationship(back_populates="oj_submissions")
    learning_event: Mapped[LearningEventLog | None] = relationship(foreign_keys=[event_id])


class ExecutionTraceRecord(Base):
    """执行轨迹独立持久化——AlgoPilot Execution Evidence Engine。

    将 Trace 从 oj_submissions.cases JSON 中提升为独立表，
    便于高效查询、对比和评测 Bug 定位准确率。
    """

    __tablename__ = "execution_traces"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("oj_submissions.id", ondelete="CASCADE"), index=True
    )
    language: Mapped[str] = mapped_column(String(16), default="python")
    verdict: Mapped[str] = mapped_column(String(8), default="OK")
    user_line_count: Mapped[int] = mapped_column(Integer, default=0)
    total_steps: Mapped[int] = mapped_column(Integer, default=0)
    steps: Mapped[list] = mapped_column(JSON, nullable=False, insert_default=list)
    key_variable_changes: Mapped[list] = mapped_column(JSON, nullable=False, insert_default=list)
    narrations: Mapped[list] = mapped_column(JSON, nullable=False, insert_default=list)
    first_divergence_step: Mapped[int] = mapped_column(Integer, default=0)
    first_divergence_line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    scene: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)


class StudentKnowledgeState(Base):
    """学生知识状态独立持久化——AlgoPilot Student Knowledge Model。

    每个知识点一条记录，追踪掌握度历史变化，
    便于绘制学习曲线和计算 Repeated Bug Rate。
    """

    __tablename__ = "student_knowledge_states"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    module_key: Mapped[str] = mapped_column(String(64), default="", index=True)
    concept_id: Mapped[str] = mapped_column(String(80), default="", index=True)
    knowledge_point: Mapped[str] = mapped_column(String(128), default="")
    mastery: Mapped[float] = mapped_column(default=0.0)
    confidence: Mapped[float] = mapped_column(default=0.0)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    independent_success_count: Mapped[int] = mapped_column(Integer, default=0)
    hint_usage: Mapped[int] = mapped_column(Integer, default=0)
    recent_bug_types: Mapped[list] = mapped_column(JSON, nullable=False, insert_default=list)
    applied_evidence: Mapped[list] = mapped_column(JSON, nullable=False, insert_default=list)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
    )


class BugRecord(Base):
    """Bug 记录独立持久化——AlgoPilot Bug Taxonomy。

    每次诊断产生一条记录，便于聚合分析 Bug 类型分布
    和评测 Bug 分类准确率。
    """

    __tablename__ = "bug_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    submission_id: Mapped[int | None] = mapped_column(
        ForeignKey("oj_submissions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    problem_slug: Mapped[str] = mapped_column(String(128), default="", index=True)
    bug_type: Mapped[str] = mapped_column(String(64), default="unknown", index=True)
    bug_type_label: Mapped[str] = mapped_column(String(128), default="")
    suspicious_lines: Mapped[list] = mapped_column(JSON, nullable=False, insert_default=list)
    first_divergence_step: Mapped[int] = mapped_column(Integer, default=0)
    first_divergence_line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    root_cause: Mapped[str] = mapped_column(String(2000), default="")
    confidence: Mapped[str] = mapped_column(String(16), default="low")
    confidence_source: Mapped[str] = mapped_column(String(32), default="rule_based")
    related_module_key: Mapped[str] = mapped_column(String(64), default="", index=True)
    related_concept_id: Mapped[str] = mapped_column(String(80), default="")
    diagnosis_source: Mapped[str] = mapped_column(String(32), default="fallback")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)


class HintRecord(Base):
    """分层提示使用记录——AlgoPilot 分层提示系统。

    追踪每次诊断中提示的使用情况，
    评测 Hint Usage 和教学效果。
    """

    __tablename__ = "hint_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    submission_id: Mapped[int | None] = mapped_column(
        ForeignKey("oj_submissions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    problem_slug: Mapped[str] = mapped_column(String(128), default="", index=True)
    hint_level_used: Mapped[int] = mapped_column(Integer, default=0)
    hint_count: Mapped[int] = mapped_column(Integer, default=0)
    eventually_accepted: Mapped[bool] = mapped_column(default=False)
    bug_type: Mapped[str] = mapped_column(String(64), default="", index=True)
    module_key: Mapped[str] = mapped_column(String(64), default="", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
