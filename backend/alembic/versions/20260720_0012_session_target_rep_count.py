"""sessions: add target_rep_count

The rep goal the user picked before starting a set. Previously this lived only in
React state on the live page and was never transmitted, so the report could not show
what the user had actually aimed for, and "16 reps" was indistinguishable from
"attempted 16 while targeting 10".

Denormalized onto the session row alongside rep_count/score/band, same convention.
NULL for sessions recorded before this migration, for exercises with no rep target,
and whenever the user leaves the goal unset (it is optional in the UI).

⚠ Written by the Module B analyze endpoint, not by session/start: the target is chosen
on the live page *after* the session row already exists, so it arrives with the frames.

Revision ID: 20260720_0012
Revises: 20260719_0011
Create Date: 2026-07-20
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260720_0012"
down_revision: str | None = "20260719_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "sessions", sa.Column("target_rep_count", sa.Integer(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("sessions", "target_rep_count")
