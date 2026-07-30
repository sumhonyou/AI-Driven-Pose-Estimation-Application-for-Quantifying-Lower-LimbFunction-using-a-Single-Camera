"""user_profiles + module_a_results: enforce the one-to-one FKs in the database.

Four relationships in the schema are conceptually one-to-one, but only two of them
(`module_b_results.session_id`, `feedback_texts.session_id`) actually carried a UNIQUE
constraint. `user_profiles.user_id` and `module_a_results.session_id` were one-to-one
in the ORM (`Mapped[X | None]`) and in every write path, but the database itself would
have accepted a second row -- so the ER diagram's 1:0..1 cardinality was an
application-level promise rather than a schema guarantee on those two.

Safe to add: every write path already upserts rather than blind-inserting.
`module_a/core/crud.save_result`, `module_a/sls/crud.save_sls_result` and
`module_a/wblt/crud.save_wblt_session` all look the row up with
`get_result_by_session` first, and both profile paths (`auth_routes.register`,
`user_routes._ensure_profile`) only build a profile for a user that has none.

The pre-flight check below fails loudly, and without deleting anything, if a target
database does contain legacy duplicates -- a raw Postgres unique-violation here would
not say which rows were at fault.

Revision ID: 20260730_0014
Revises: 20260724_0013
Create Date: 2026-07-30
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260730_0014"
down_revision: str | None = "20260724_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (table, column) pairs getting a UNIQUE constraint, named uq_<table>_<column> to
# match the existing uq_module_b_results_session_id / uq_feedback_texts_session_id.
_TARGETS = (
    ("user_profiles", "user_id"),
    ("module_a_results", "session_id"),
)


def _assert_no_duplicates(table: str, column: str) -> None:
    """Refuses to proceed if `column` already has repeats -- never deletes rows."""
    conn = op.get_bind()
    dupes = conn.execute(
        sa.text(
            f"SELECT {column} AS key, COUNT(*) AS n "  # noqa: S608 - fixed literals
            f"FROM {table} GROUP BY {column} HAVING COUNT(*) > 1"
        )
    ).fetchall()
    if dupes:
        detail = ", ".join(f"{row.key} x{row.n}" for row in dupes[:5])
        raise RuntimeError(
            f"Cannot add UNIQUE on {table}.{column}: {len(dupes)} duplicated "
            f"value(s) already present ({detail}"
            f"{', ...' if len(dupes) > 5 else ''}). Resolve these rows by hand "
            f"(keep the newest per key), then re-run this migration."
        )


def upgrade() -> None:
    for table, column in _TARGETS:
        _assert_no_duplicates(table, column)
        op.create_unique_constraint(f"uq_{table}_{column}", table, [column])


def downgrade() -> None:
    for table, column in _TARGETS:
        op.drop_constraint(f"uq_{table}_{column}", table, type_="unique")
