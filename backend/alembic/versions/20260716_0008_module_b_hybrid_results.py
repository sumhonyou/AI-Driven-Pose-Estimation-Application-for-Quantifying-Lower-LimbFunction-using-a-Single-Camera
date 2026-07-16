"""Replace legacy flat Module B tables with the Phase 4 hybrid persistence shape.

Revision ID: 20260716_0008
Revises: 20260713_0007
Create Date: 2026-07-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260716_0008"
down_revision: str | None = "20260713_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Keep the small, dashboard-queryable Module B summary flat.
    op.add_column(
        "module_b_results",
        sa.Column("exercise_code", sa.String(length=100), nullable=True),
    )
    op.add_column("module_b_results", sa.Column("score", sa.Numeric(5, 2)))
    op.add_column("module_b_results", sa.Column("band", sa.String(length=50)))
    op.add_column("module_b_results", sa.Column("confidence", sa.Numeric(5, 4)))
    op.add_column("module_b_results", sa.Column("model_version", sa.String(length=100)))
    op.add_column(
        "module_b_results", sa.Column("feature_schema_version", sa.String(length=20))
    )
    op.add_column("module_b_results", sa.Column("q", sa.Numeric(5, 4)))
    op.add_column(
        "module_b_results",
        sa.Column("metrics_json", postgresql.JSONB(astext_type=sa.Text())),
    )
    op.execute(
        """
        UPDATE module_b_results AS result
        SET exercise_code = session.exercise_type,
            score = result.final_score,
            band = result.final_band,
            confidence = result.ml_confidence,
            model_version = 'legacy-unversioned',
            feature_schema_version = 'legacy-unversioned',
            metrics_json = jsonb_strip_nulls(jsonb_build_object(
                'rule_score', result.rule_score,
                'ml_score', result.ml_score,
                'ml_label', result.ml_label,
                'sub_scores', jsonb_build_object(
                    'rom_completeness', result.rom_score,
                    'tempo_consistency', result.tempo_score,
                    'stability_control', result.stability_score
                ),
                'fusion_weights', result.fusion_weights_json,
                'feature_summary', result.feature_summary_json
            ))
        FROM sessions AS session
        WHERE session.id = result.session_id
        """
    )
    op.alter_column("module_b_results", "exercise_code", nullable=False)
    op.create_unique_constraint(
        "uq_module_b_results_session_id", "module_b_results", ["session_id"]
    )
    op.create_index(
        "ix_module_b_results_exercise_created_at",
        "module_b_results",
        ["exercise_code", "created_at"],
    )
    # Sessions owns the user relationship; this index is the user/timestamp
    # path used by Phase 7's result-history joins.
    op.create_index(
        "ix_sessions_user_started_at", "sessions", ["user_id", "started_at"]
    )
    for column in (
        "rule_score",
        "ml_score",
        "final_score",
        "final_band",
        "ml_label",
        "ml_confidence",
        "rom_score",
        "tempo_score",
        "stability_score",
        "fusion_weights_json",
        "feature_summary_json",
    ):
        op.drop_column("module_b_results", column)

    # Tags now hang directly from sessions, so future low-Q attempts and
    # cross-session aggregation do not depend on a result-row join.
    op.rename_table("error_tags", "module_b_error_tags")
    op.add_column(
        "module_b_error_tags",
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "module_b_error_tags", sa.Column("source", sa.String(length=20), nullable=True)
    )
    op.execute(
        """
        UPDATE module_b_error_tags AS tag
        SET session_id = result.session_id
        FROM module_b_results AS result
        WHERE result.id = tag.module_b_result_id
        """
    )
    op.alter_column("module_b_error_tags", "session_id", nullable=False)
    op.drop_constraint(
        "error_tags_module_b_result_id_fkey",
        "module_b_error_tags",
        type_="foreignkey",
    )
    op.drop_column("module_b_error_tags", "module_b_result_id")
    op.alter_column("module_b_error_tags", "tag_code", new_column_name="tag")
    op.create_foreign_key(
        "fk_module_b_error_tags_session_id",
        "module_b_error_tags",
        "sessions",
        ["session_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_module_b_error_tags_session_tag",
        "module_b_error_tags",
        ["session_id", "tag"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_module_b_error_tags_session_tag", table_name="module_b_error_tags"
    )
    op.drop_constraint(
        "fk_module_b_error_tags_session_id",
        "module_b_error_tags",
        type_="foreignkey",
    )
    op.alter_column("module_b_error_tags", "tag", new_column_name="tag_code")
    op.add_column(
        "module_b_error_tags",
        sa.Column("module_b_result_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.execute(
        """
        UPDATE module_b_error_tags AS tag
        SET module_b_result_id = result.id
        FROM module_b_results AS result
        WHERE result.session_id = tag.session_id
        """
    )
    op.alter_column("module_b_error_tags", "module_b_result_id", nullable=False)
    op.create_foreign_key(
        "error_tags_module_b_result_id_fkey",
        "module_b_error_tags",
        "module_b_results",
        ["module_b_result_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_column("module_b_error_tags", "source")
    op.drop_column("module_b_error_tags", "session_id")
    op.rename_table("module_b_error_tags", "error_tags")

    for column in (
        sa.Column("rule_score", sa.Numeric(5, 2)),
        sa.Column("ml_score", sa.Numeric(5, 2)),
        sa.Column("final_score", sa.Numeric(5, 2)),
        sa.Column("final_band", sa.String(length=50)),
        sa.Column("ml_label", sa.String(length=50)),
        sa.Column("ml_confidence", sa.Numeric(5, 4)),
        sa.Column("rom_score", sa.Numeric(5, 2)),
        sa.Column("tempo_score", sa.Numeric(5, 2)),
        sa.Column("stability_score", sa.Numeric(5, 2)),
        sa.Column("fusion_weights_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("feature_summary_json", postgresql.JSONB(astext_type=sa.Text())),
    ):
        op.add_column("module_b_results", column)
    op.execute(
        """
        UPDATE module_b_results
        SET rule_score = (metrics_json->>'rule_score')::numeric,
            ml_score = (metrics_json->>'ml_score')::numeric,
            final_score = score,
            final_band = band,
            ml_label = metrics_json->>'ml_label',
            ml_confidence = confidence,
            fusion_weights_json = metrics_json->'fusion_weights',
            feature_summary_json = metrics_json->'feature_summary'
        """
    )
    op.drop_index("ix_sessions_user_started_at", table_name="sessions")
    op.drop_index(
        "ix_module_b_results_exercise_created_at", table_name="module_b_results"
    )
    op.drop_constraint(
        "uq_module_b_results_session_id", "module_b_results", type_="unique"
    )
    for column in (
        "metrics_json",
        "q",
        "feature_schema_version",
        "model_version",
        "confidence",
        "band",
        "score",
        "exercise_code",
    ):
        op.drop_column("module_b_results", column)
