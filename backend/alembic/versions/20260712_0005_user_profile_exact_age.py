"""user_profiles: exact_age column, backfilled from age_group bucket midpoint

WBLT (blueprint §1.1) needs the user's real age to resolve a McBride age band —
the existing `age_group` column only has 3 buckets ("under_40", "40_60",
"over_60"), too coarse for a band lookup. This adds `exact_age` and backfills
every existing row with its bucket's midpoint (30 / 50 / 70) as an interim
estimate. It is NOT a substitute for the real value: WBLT banding is blocked
per-user until they confirm their exact age (see app/module_a/wblt/age_band.py
and the profile-completion prompt this migration does not implement itself).

Revision ID: 20260712_0005
Revises: 20260710_0004
Create Date: 2026-07-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260712_0005"
down_revision: str | None = "20260710_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Matches the exact codes used by the Register/Profile age_group <select> —
# see frontend/src/pages/Register.tsx and Profile.tsx. Not decade ranges.
_AGE_GROUP_MIDPOINTS = {
    "under_40": 30,
    "40_60": 50,
    "over_60": 70,
}


def upgrade() -> None:
    op.add_column(
        "user_profiles",
        sa.Column("exact_age", sa.Integer(), nullable=True),
    )

    connection = op.get_bind()
    for age_group, midpoint in _AGE_GROUP_MIDPOINTS.items():
        connection.execute(
            sa.text(
                "UPDATE user_profiles SET exact_age = :midpoint "
                "WHERE age_group = :age_group AND exact_age IS NULL"
            ),
            {"midpoint": midpoint, "age_group": age_group},
        )


def downgrade() -> None:
    op.drop_column("user_profiles", "exact_age")
