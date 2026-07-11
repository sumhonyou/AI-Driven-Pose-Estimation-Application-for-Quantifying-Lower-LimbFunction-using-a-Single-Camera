"""users: avatar_image column

Revision ID: 20260710_0004
Revises: 20260706_0003
Create Date: 2026-07-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260710_0004"
down_revision: str | None = "20260706_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("avatar_image", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "avatar_image")
