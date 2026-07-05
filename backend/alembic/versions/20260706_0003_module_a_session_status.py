"""module a: session_status / is_partial_score columns

Revision ID: 20260706_0003
Revises: 20260701_0002
Create Date: 2026-07-06
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260706_0003"
down_revision: str | None = "20260701_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "module_a_results",
        sa.Column("session_status", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "module_a_results",
        sa.Column(
            "is_partial_score",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )


def downgrade() -> None:
    op.drop_column("module_a_results", "is_partial_score")
    op.drop_column("module_a_results", "session_status")
