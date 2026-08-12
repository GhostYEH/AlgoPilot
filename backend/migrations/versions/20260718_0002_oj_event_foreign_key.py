"""Add the OJ submission to learning-event foreign key.

Revision ID: 20260718_0002
Revises: 20260718_0001
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260718_0002"
down_revision = "20260718_0001"
branch_labels = None
depends_on = None

_FK_NAME = "fk_oj_submissions_event_id_learning_event_logs"


def _event_foreign_key_exists() -> bool:
    return any(
        fk.get("referred_table") == "learning_event_logs" and fk.get("constrained_columns") == ["event_id"]
        for fk in sa.inspect(op.get_bind()).get_foreign_keys("oj_submissions")
    )


def upgrade() -> None:
    if _event_foreign_key_exists():
        return

    # Old application versions allowed an event id even when event persistence
    # failed. Clear those orphan values before enforcing referential integrity.
    op.execute(
        sa.text(
            """
            UPDATE oj_submissions
            SET event_id = NULL
            WHERE event_id IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM learning_event_logs
                  WHERE learning_event_logs.event_id = oj_submissions.event_id
              )
            """
        )
    )
    with op.batch_alter_table("oj_submissions", recreate="auto") as batch_op:
        batch_op.alter_column(
            "event_id",
            existing_type=sa.String(64),
            type_=sa.String(32),
            existing_nullable=True,
        )
        batch_op.create_foreign_key(
            _FK_NAME,
            "learning_event_logs",
            ["event_id"],
            ["event_id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_oj_submissions_event_id", ["event_id"])


def downgrade() -> None:
    if not _event_foreign_key_exists():
        return
    with op.batch_alter_table("oj_submissions", recreate="auto") as batch_op:
        batch_op.drop_index("ix_oj_submissions_event_id")
        batch_op.drop_constraint(_FK_NAME, type_="foreignkey")
        batch_op.alter_column(
            "event_id",
            existing_type=sa.String(32),
            type_=sa.String(64),
            existing_nullable=True,
        )
