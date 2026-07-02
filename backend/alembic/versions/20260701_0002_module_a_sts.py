"""module a: sts score/band columns + landmark log table

Revision ID: 20260701_0002
Revises: 20260605_0001
Create Date: 2026-07-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260701_0002"
down_revision: str | None = "20260605_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column("score", sa.Numeric(4, 2), nullable=True))
    op.add_column("sessions", sa.Column("band", sa.String(length=50), nullable=True))
    op.add_column(
        "module_a_results", sa.Column("score", sa.Numeric(4, 2), nullable=True)
    )

    op.create_table(
        "module_a_landmark_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("frame_index", sa.Integer(), nullable=False),
        sa.Column("timestamp_ms", sa.Numeric(12, 3), nullable=False),
        sa.Column(
            "world_landmarks", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_module_a_landmark_log_session_id"),
        "module_a_landmark_log",
        ["session_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_module_a_landmark_log_session_id"), table_name="module_a_landmark_log"
    )
    op.drop_table("module_a_landmark_log")
    op.drop_column("module_a_results", "score")
    op.drop_column("sessions", "band")
    op.drop_column("sessions", "score")
