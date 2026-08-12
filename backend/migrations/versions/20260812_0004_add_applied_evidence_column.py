"""Add applied_evidence column to student_knowledge_states.

为 StudentKnowledgeState 增加幂等追踪列。applied_evidence 是一个 JSON
数组，记录已经应用过的 (submission_id, evidence_type) 证据键，防止
重复诊断或重复提交导致 mastery 被多次扣分/加分。

Revision ID: 20260812_0004
Revises: 20260812_0003
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260812_0004"
down_revision = "20260812_0003"
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    return column_name in [col["name"] for col in inspector.get_columns(table_name)]


def upgrade() -> None:
    if not _column_exists("student_knowledge_states", "applied_evidence"):
        with op.batch_alter_table("student_knowledge_states", recreate="auto") as batch_op:
            batch_op.add_column(
                sa.Column(
                    "applied_evidence",
                    sa.JSON,
                    nullable=False,
                    server_default="[]",
                )
            )


def downgrade() -> None:
    if _column_exists("student_knowledge_states", "applied_evidence"):
        with op.batch_alter_table("student_knowledge_states", recreate="auto") as batch_op:
            batch_op.drop_column("applied_evidence")