"""Add Execution Evidence Engine persistent tables.

新增 4 张表，将 Trace / KnowledgeState / BugRecord / HintRecord
从 JSON 字段提升为独立持久化，便于高效查询与评测。

Revision ID: 20260812_0003
Revises: 20260718_0002
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260812_0003"
down_revision = "20260718_0002"
branch_labels = None
depends_on = None


def _table_exists(name: str) -> bool:
    return name in sa.inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    if not _table_exists("execution_traces"):
        op.create_table(
            "execution_traces",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column(
                "submission_id",
                sa.Integer,
                sa.ForeignKey("oj_submissions.id", ondelete="CASCADE"),
                index=True,
            ),
            sa.Column("language", sa.String(16), server_default="python"),
            sa.Column("verdict", sa.String(8), server_default="OK"),
            sa.Column("user_line_count", sa.Integer, server_default="0"),
            sa.Column("total_steps", sa.Integer, server_default="0"),
            sa.Column("steps", sa.JSON, nullable=False, server_default="[]"),
            sa.Column("key_variable_changes", sa.JSON, nullable=False, server_default="[]"),
            sa.Column("narrations", sa.JSON, nullable=False, server_default="[]"),
            sa.Column("first_divergence_step", sa.Integer, server_default="0"),
            sa.Column("first_divergence_line", sa.Integer, nullable=True),
            sa.Column("scene", sa.String(64), server_default=""),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), index=True),
        )

    if not _table_exists("student_knowledge_states"):
        op.create_table(
            "student_knowledge_states",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column(
                "user_id",
                sa.Integer,
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                index=True,
            ),
            sa.Column("module_key", sa.String(64), server_default="", index=True),
            sa.Column("concept_id", sa.String(80), server_default="", index=True),
            sa.Column("knowledge_point", sa.String(128), server_default=""),
            sa.Column("mastery", sa.Float, server_default="0"),
            sa.Column("confidence", sa.Float, server_default="0"),
            sa.Column("attempt_count", sa.Integer, server_default="0"),
            sa.Column("success_count", sa.Integer, server_default="0"),
            sa.Column("independent_success_count", sa.Integer, server_default="0"),
            sa.Column("hint_usage", sa.Integer, server_default="0"),
            sa.Column("recent_bug_types", sa.JSON, nullable=False, server_default="[]"),
            sa.Column("last_updated", sa.DateTime, server_default=sa.func.now(), index=True),
        )

    if not _table_exists("bug_records"):
        op.create_table(
            "bug_records",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column(
                "submission_id",
                sa.Integer,
                sa.ForeignKey("oj_submissions.id", ondelete="SET NULL"),
                nullable=True,
                index=True,
            ),
            sa.Column(
                "user_id",
                sa.Integer,
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                index=True,
            ),
            sa.Column("problem_slug", sa.String(128), server_default="", index=True),
            sa.Column("bug_type", sa.String(64), server_default="unknown", index=True),
            sa.Column("bug_type_label", sa.String(128), server_default=""),
            sa.Column("suspicious_lines", sa.JSON, nullable=False, server_default="[]"),
            sa.Column("first_divergence_step", sa.Integer, server_default="0"),
            sa.Column("first_divergence_line", sa.Integer, nullable=True),
            sa.Column("root_cause", sa.String(2000), server_default=""),
            sa.Column("confidence", sa.String(16), server_default="low"),
            sa.Column("confidence_source", sa.String(32), server_default="rule_based"),
            sa.Column("related_module_key", sa.String(64), server_default="", index=True),
            sa.Column("related_concept_id", sa.String(80), server_default=""),
            sa.Column("diagnosis_source", sa.String(32), server_default="fallback"),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), index=True),
        )

    if not _table_exists("hint_records"):
        op.create_table(
            "hint_records",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column(
                "submission_id",
                sa.Integer,
                sa.ForeignKey("oj_submissions.id", ondelete="SET NULL"),
                nullable=True,
                index=True,
            ),
            sa.Column(
                "user_id",
                sa.Integer,
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                index=True,
            ),
            sa.Column("problem_slug", sa.String(128), server_default="", index=True),
            sa.Column("hint_level_used", sa.Integer, server_default="0"),
            sa.Column("hint_count", sa.Integer, server_default="0"),
            sa.Column("eventually_accepted", sa.Boolean, server_default="0"),
            sa.Column("bug_type", sa.String(64), server_default="", index=True),
            sa.Column("module_key", sa.String(64), server_default="", index=True),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), index=True),
        )


def downgrade() -> None:
    for table in ("hint_records", "bug_records", "student_knowledge_states", "execution_traces"):
        if _table_exists(table):
            op.drop_table(table)