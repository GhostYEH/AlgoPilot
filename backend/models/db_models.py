from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
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
