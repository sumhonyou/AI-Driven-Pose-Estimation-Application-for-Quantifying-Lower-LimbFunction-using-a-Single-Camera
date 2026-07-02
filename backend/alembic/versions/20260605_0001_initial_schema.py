"""initial schema

Revision ID: 20260605_0001
Revises:
Create Date: 2026-06-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260605_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "exercise_catalog",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("mode", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("view_guidance", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_exercise_catalog_code"), "exercise_catalog", ["code"], unique=True
    )

    op.create_table(
        "user_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("age_group", sa.String(length=50), nullable=True),
        sa.Column("gender", sa.String(length=50), nullable=True),
        sa.Column("height_cm", sa.Numeric(5, 2), nullable=True),
        sa.Column("weight_kg", sa.Numeric(5, 2), nullable=True),
        sa.Column("user_type", sa.String(length=50), nullable=True),
        sa.Column("focus_area", sa.String(length=50), nullable=True),
        sa.Column("self_reported_note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exercise_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mode", sa.String(length=50), nullable=False),
        sa.Column("exercise_type", sa.String(length=100), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("capture_quality", sa.Numeric(4, 3), nullable=True),
        sa.Column("valid_frame_ratio", sa.Numeric(4, 3), nullable=True),
        sa.Column("device_info", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercise_catalog.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "reminders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("reminder_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("frequency", sa.String(length=50), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "module_a_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("completion_time_sec", sa.Numeric(8, 3), nullable=True),
        sa.Column("hold_duration_sec", sa.Numeric(8, 3), nullable=True),
        sa.Column("rep_count", sa.Integer(), nullable=True),
        sa.Column("rom_band", sa.String(length=50), nullable=True),
        sa.Column("stability_proxy", sa.Numeric(8, 4), nullable=True),
        sa.Column("sway_proxy", sa.Numeric(8, 4), nullable=True),
        sa.Column("symmetry_proxy", sa.Numeric(8, 4), nullable=True),
        sa.Column("trunk_lean_proxy", sa.Numeric(8, 4), nullable=True),
        sa.Column("final_band", sa.String(length=50), nullable=False),
        sa.Column("confidence_level", sa.String(length=50), nullable=True),
        sa.Column(
            "metrics_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "module_b_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rule_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("ml_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("final_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("final_band", sa.String(length=50), nullable=True),
        sa.Column("ml_label", sa.String(length=50), nullable=True),
        sa.Column("ml_confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("rom_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("tempo_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("stability_score", sa.Numeric(5, 2), nullable=True),
        sa.Column(
            "fusion_weights_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "feature_summary_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "feedback_texts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("structured_feedback", sa.Text(), nullable=True),
        sa.Column("rewritten_feedback", sa.Text(), nullable=True),
        sa.Column("llm_used", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("safety_disclaimer", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "error_tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("module_b_result_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag_code", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["module_b_result_id"], ["module_b_results.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("error_tags")
    op.drop_table("feedback_texts")
    op.drop_table("module_b_results")
    op.drop_table("module_a_results")
    op.drop_table("reminders")
    op.drop_table("sessions")
    op.drop_table("user_profiles")
    op.drop_index(op.f("ix_exercise_catalog_code"), table_name="exercise_catalog")
    op.drop_table("exercise_catalog")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
