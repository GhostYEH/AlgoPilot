"""Create the baseline application schema.

This revision is deliberately tolerant of databases created by the former
``Base.metadata.create_all`` startup path: existing tables are adopted, while
missing tables are created and the database starts receiving Alembic versions.

Revision ID: 20260718_0001
Revises: None
"""

from __future__ import annotations

from collections.abc import Callable

from alembic import op
import sqlalchemy as sa

revision = "20260718_0001"
down_revision = None
branch_labels = None
depends_on = None


def _create_if_missing(name: str, create: Callable[[], None]) -> None:
    if name not in sa.inspect(op.get_bind()).get_table_names():
        create()


def _users() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(16), server_default="student", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)


def _learning_progress() -> None:
    op.create_table(
        "learning_progress",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def _student_profiles() -> None:
    op.create_table(
        "student_profiles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("summary", sa.String(2000), server_default="", nullable=False),
        sa.Column("dimensions", sa.JSON(), nullable=False),
        sa.Column("chat_history", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def _generated_resources() -> None:
    op.create_table(
        "generated_resources",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("resource_type", sa.String(32), nullable=False),
        sa.Column("agent_name", sa.String(64), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("content", sa.String(50000), nullable=False),
        sa.Column("meta", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_generated_resources_resource_type", "generated_resources", ["resource_type"])
    op.create_index("ix_generated_resources_user_id", "generated_resources", ["user_id"])


def _learning_path_plans() -> None:
    op.create_table(
        "learning_path_plans",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("summary", sa.String(500), server_default="", nullable=False),
        sa.Column("rationale", sa.String(2000), server_default="", nullable=False),
        sa.Column("next_module_key", sa.String(64), nullable=True),
        sa.Column("ordered_keys", sa.JSON(), nullable=False),
        sa.Column("steps", sa.JSON(), nullable=False),
        sa.Column("progress_snapshot", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def _student_learning_memories() -> None:
    op.create_table(
        "student_learning_memories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.String(64), nullable=False),
        sa.Column("chapter_id", sa.String(80), nullable=False),
        sa.Column("skill_id", sa.String(64), nullable=False),
        sa.Column("problem_slug", sa.String(128), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("observed_error_pattern", sa.String(500), nullable=False),
        sa.Column("trace_summary", sa.String(2000), nullable=False),
        sa.Column("failed_strategy", sa.String(500), nullable=False),
        sa.Column("successful_hint", sa.String(500), nullable=False),
        sa.Column("mastery_delta", sa.Integer(), nullable=False),
        sa.Column("evidence_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("user_id", "course_id", "chapter_id", "skill_id", "problem_slug", "event_type", "created_at"):
        op.create_index(f"ix_student_learning_memories_{column}", "student_learning_memories", [column])


def _learning_event_logs() -> None:
    op.create_table(
        "learning_event_logs",
        sa.Column("event_id", sa.String(32), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("course_id", sa.String(64), nullable=False),
        sa.Column("chapter_id", sa.String(80), nullable=False),
        sa.Column("skill_id", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("handled_by", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("agent_logs", sa.JSON(), nullable=False),
        sa.Column("handler_errors", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("event_id"),
    )
    for column in ("user_id", "event_type", "course_id", "chapter_id", "skill_id", "status", "created_at"):
        op.create_index(f"ix_learning_event_logs_{column}", "learning_event_logs", [column])


def _oj_submissions() -> None:
    # The event foreign key belongs to the next revision so legacy databases and
    # fresh databases follow exactly the same tested upgrade path.
    op.create_table(
        "oj_submissions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("problem_slug", sa.String(128), nullable=False),
        sa.Column("language", sa.String(16), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("verdict", sa.String(8), nullable=False),
        sa.Column("passed", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("compile_error", sa.Text(), nullable=False),
        sa.Column("cases", sa.JSON(), nullable=False),
        sa.Column("runtime_ms_avg", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("user_id", "problem_slug", "verdict", "created_at"):
        op.create_index(f"ix_oj_submissions_{column}", "oj_submissions", [column])


def upgrade() -> None:
    for name, create in (
        ("users", _users),
        ("learning_progress", _learning_progress),
        ("student_profiles", _student_profiles),
        ("generated_resources", _generated_resources),
        ("learning_path_plans", _learning_path_plans),
        ("student_learning_memories", _student_learning_memories),
        ("learning_event_logs", _learning_event_logs),
        ("oj_submissions", _oj_submissions),
    ):
        _create_if_missing(name, create)


def downgrade() -> None:
    for table in (
        "oj_submissions",
        "learning_event_logs",
        "student_learning_memories",
        "learning_path_plans",
        "generated_resources",
        "student_profiles",
        "learning_progress",
        "users",
    ):
        op.drop_table(table)
