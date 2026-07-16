"""sessions: add rep_count

Denormalized onto the session row, matching the existing score/band
convention, so the generic /api/sessions list and history table can show a
per-session rep count without pulling each exercise's own metrics_json shape.
NULL for every exercise that has no rep concept (SLS, WBLT) and for any
session recorded before this migration.

Revision ID: 20260717_0009
Revises: 20260716_0008
Create Date: 2026-07-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260717_0009"
down_revision: str | None = "20260716_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column("rep_count", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("sessions", "rep_count")
