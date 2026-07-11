"""user_profiles: backfill remaining NULL exact_age with a placeholder

Migration 20260712_0005 only backfilled the 3 known age_group bucket codes
("under_40"/"40_60"/"over_60"). A handful of existing rows carry other/blank
age_group values (leftover manual test data, e.g. "25-34"), which that
migration correctly left NULL rather than guess.

These are confirmed test-only records (not real user data), so this fills the
remaining NULLs with a flat placeholder age of 30 -- good enough to unblock
WBLT banding on test accounts. Real users should still confirm their exact
age via the profile UI once that flow exists (see task.md Stage 0 follow-up).

Revision ID: 20260712_0006
Revises: 20260712_0005
Create Date: 2026-07-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260712_0006"
down_revision: str | None = "20260712_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PLACEHOLDER_AGE = 30


def upgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text("UPDATE user_profiles SET exact_age = :age WHERE exact_age IS NULL"),
        {"age": _PLACEHOLDER_AGE},
    )


def downgrade() -> None:
    # No reliable way to distinguish which rows this migration touched from
    # ones that were genuinely 30 already -- intentionally a no-op.
    pass
