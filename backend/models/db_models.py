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
