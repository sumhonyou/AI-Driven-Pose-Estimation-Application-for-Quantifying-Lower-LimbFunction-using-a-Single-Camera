"""user_profiles: drop age_group

Superseded by exact_age (migrated in 20260712_0005/0006), which is now
collected directly and required at signup alongside gender -- the 3-bucket
age_group column has no remaining reader anywhere in the app.

Revision ID: 20260713_0007
Revises: 20260712_0006
Create Date: 2026-07-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260713_0007"
down_revision: str | None = "20260712_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("user_profiles", "age_group")


def downgrade() -> None:
    op.add_column(
        "user_profiles",
        sa.Column("age_group", sa.String(length=50), nullable=True),
    )
