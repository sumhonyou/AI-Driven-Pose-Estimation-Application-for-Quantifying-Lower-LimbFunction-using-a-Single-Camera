"""feedback_texts: replace llm_used/safety_disclaimer with source tracking.

Phase 6 Stage 6.5 (architecture doc §13, resolved 2026-07-16): `llm_used BOOLEAN`
collapsed two different situations into one bit -- "the LLM was never called" and "the
LLM was called but Stage 6.3's safety filter rejected the output" both read as FALSE,
losing exactly what an examiner would ask about. Replaced with `feedback_source` +
`llm_attempted` so both are distinguishable. `safety_disclaimer` is dropped as stored
free text -- the disclaimer the user sees always comes from the current i18n render
(rules.md #19); `disclaimer_version` gives audit-grade traceability without duplicating
that text per row. Also adds the one-result-per-session unique constraint the hybrid
`module_b_results` table already has (20260716_0008), since `crud.save_feedback` upserts
by `session_id` the same way `crud.save_result` does.

Revision ID: 20260719_0010
Revises: 20260717_0009
Create Date: 2026-07-19
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260719_0010"
down_revision: str | None = "20260717_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "feedback_texts",
        sa.Column(
            "feedback_source",
            sa.String(length=20),
            nullable=False,
            server_default="template",
        ),
    )
    op.add_column(
        "feedback_texts",
        sa.Column(
            "llm_attempted", sa.Boolean(), nullable=False, server_default="false"
        ),
    )
    op.add_column("feedback_texts", sa.Column("provider", sa.String(length=50)))
    op.add_column("feedback_texts", sa.Column("model_version", sa.String(length=100)))
    op.add_column(
        "feedback_texts", sa.Column("disclaimer_version", sa.String(length=20))
    )
    op.execute(
        """
        UPDATE feedback_texts
        SET feedback_source = CASE WHEN llm_used THEN 'llm' ELSE 'template' END,
            llm_attempted = llm_used
        """
    )
    op.drop_column("feedback_texts", "llm_used")
    op.drop_column("feedback_texts", "safety_disclaimer")
    op.create_unique_constraint(
        "uq_feedback_texts_session_id", "feedback_texts", ["session_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_feedback_texts_session_id", "feedback_texts", type_="unique")
    op.add_column(
        "feedback_texts",
        sa.Column("llm_used", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column("feedback_texts", sa.Column("safety_disclaimer", sa.Text()))
    op.execute("UPDATE feedback_texts SET llm_used = (feedback_source = 'llm')")
    op.drop_column("feedback_texts", "disclaimer_version")
    op.drop_column("feedback_texts", "model_version")
    op.drop_column("feedback_texts", "provider")
    op.drop_column("feedback_texts", "llm_attempted")
    op.drop_column("feedback_texts", "feedback_source")
