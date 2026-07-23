"""feedback_texts: add fallback_reason for LLM-fallback diagnostics.

UAT remediation (Stage R3, T11, S5 "keeps showing template fallback"): the safety
filter (`feedback_safety.check_llm_feedback`) and the LLM client
(`llm_client.GroqClient`) both already compute a precise reason whenever a rewrite
isn't used -- a rejected phrase, an invented tag, a 429, a timeout -- but
`router._build_and_save_feedback` only logged it, never stored it. Without a stored
reason, diagnosing why a report is template-sourced requires re-reading server logs
for that exact session; `fallback_reason` makes it queryable per row.

Revision ID: 20260724_0013
Revises: 20260720_0012
Create Date: 2026-07-24
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260724_0013"
down_revision: str | None = "20260720_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("feedback_texts", sa.Column("fallback_reason", sa.String(length=80)))


def downgrade() -> None:
    op.drop_column("feedback_texts", "fallback_reason")
