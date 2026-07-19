"""reminders: exercise_code + last_completed_at columns

Revision ID: 20260719_0011
Revises: 20260719_0010
Create Date: 2026-07-19
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260719_0011"
down_revision: str | None = "20260719_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "reminders",
        sa.Column("exercise_code", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "reminders",
        sa.Column("last_completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("reminders", "last_completed_at")
    op.drop_column("reminders", "exercise_code")
