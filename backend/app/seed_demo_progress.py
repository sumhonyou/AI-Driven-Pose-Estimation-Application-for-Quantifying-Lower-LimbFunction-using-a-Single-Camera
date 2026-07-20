"""Phase 7 Stage 7.4 — seed a demo account with multi-session, multi-exercise
history so the dashboard/progress charts have real data to render against.

Separate from app/seed.py (which seeds the exercise catalog + a single demo
login from env vars) because this creates *session history*, not account
scaffolding, and is meant to be run/purged independently during Phase 7 work.

Usage:
    python -m app.seed_demo_progress            # create/refresh demo data
    python -m app.seed_demo_progress --purge     # delete the demo account entirely
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.core.security import hash_password
from app.db.database import SessionLocal
from app.db.models import (
    ExerciseCatalog,
    ModuleBErrorTag,
    ModuleBResult,
)
from app.db.models import Session as SessionModel
from app.db.models import (
    User,
    UserProfile,
)
from app.module_a.core.quality import quality_band

DEMO_EMAIL = "demo-progress@physiofit-demo.com"
DEMO_PASSWORD = "DemoProgress123!"
DEMO_FULL_NAME = "Demo Progress Account"

_NOW = datetime(2026, 7, 19, 9, 0, tzinfo=UTC)

# (days_ago, score 0-10, band, capture_quality 0-1, rep_count)
# Upward drift on both exercises so the trend charts show visible improvement,
# with realistic noise rather than a perfectly straight line.
STS_SESSIONS = [
    (26, 4.2, "Poor", 0.62, 6),
    (22, 4.8, "Poor", 0.68, 7),
    (18, 5.6, "Fair", 0.74, 8),
    (14, 6.1, "Fair", 0.79, 8),
    (9, 6.9, "Fair", 0.86, 9),
    (4, 7.8, "Good", 0.91, 10),
]

# (days_ago, score 0-10, band, capture_quality, confidence, rep_count, tags)
# Squat is a committed binary Good/Poor classifier (Stage 5.11) -- no "Fair"
# band is ever emitted, so seed data must not invent one.
#
# ⚠ Stage 5.18 invariant: the squat score is the share of clean reps and the band is a
# strict majority of the same per-rep verdicts, so `band == "Good"` iff `score > 5.0`.
# This data is written straight to the DB and bypasses the scoring pipeline, so nothing
# enforces that for it -- keep every row on the correct side of 5.0 by hand. (The 11-days
# -ago row was 5.2/"Poor" before this stage, which would render as a contradictory
# 5.2-with-Needs-Improvement report: exactly the defect Stage 5.18 removed everywhere else.)
SQUAT_SESSIONS = [
    (25, 3.1, "Poor", 0.58, 0.81, 5, ["insufficient_depth", "excessive_forward_lean"]),
    (20, 3.6, "Poor", 0.65, 0.77, 5, ["insufficient_depth"]),
    (16, 4.4, "Poor", 0.71, 0.83, 6, ["excessive_forward_lean", "heel_lift"]),
    (11, 4.8, "Poor", 0.80, 0.88, 6, ["heel_lift"]),
    (6, 6.9, "Good", 0.87, 0.92, 7, ["inconsistent_tempo"]),
    (2, 7.5, "Good", 0.93, 0.95, 7, []),
]

# Guard: the fixture above is hand-maintained, so assert the Stage 5.18 invariant at import
# rather than let a future edit reintroduce a contradictory demo report.
for _row in SQUAT_SESSIONS:
    _score, _band = _row[1], _row[2]
    assert (_band == "Good") == (_score > 5.0), (
        f"SQUAT_SESSIONS row {_row[0]} days ago violates the Stage 5.18 invariant: "
        f"score={_score} cannot band {_band!r} (Good iff score > 5.0)"
    )

_TAG_SEVERITY = {
    "insufficient_depth": "high",
    "excessive_forward_lean": "high",
    "heel_lift": "high",
    "inconsistent_tempo": "low",
}


def _get_exercise(db, code: str) -> ExerciseCatalog:
    exercise = db.scalar(select(ExerciseCatalog).where(ExerciseCatalog.code == code))
    if exercise is None:
        raise RuntimeError(
            f"Exercise catalog is missing '{code}' -- run app.seed first."
        )
    return exercise


def _make_sts_session(db, user: User, exercise: ExerciseCatalog, row: tuple) -> None:
    days_ago, score, band, quality, reps = row
    started = _NOW - timedelta(days=days_ago)
    db.add(
        SessionModel(
            user_id=user.id,
            exercise_id=exercise.id,
            mode=exercise.mode,
            exercise_type=exercise.code,
            started_at=started,
            ended_at=started + timedelta(minutes=2),
            status="completed",
            capture_quality=Decimal(str(quality)),
            valid_frame_ratio=Decimal(str(round(min(quality + 0.03, 1.0), 3))),
            score=Decimal(str(score)),
            band=band,
            rep_count=reps,
        )
    )


def _squat_metrics_json(score: float, quality: float, reps: int) -> dict:
    """A realistic Module B metrics snapshot matching the shape the real /analyze
    pipeline writes (app/module_b/core/crud.py::_metrics_json), so the squat Report
    page can read metrics.capture_quality / rule_subscores / ml_score without the
    seed data diverging from production shape. Values are representative, not derived
    from a real capture (this data never passed through the ML pipeline)."""
    valid_frame_ratio = round(min(quality + 0.03, 1.0), 3)
    return {
        "rule_score": score,
        "rule_subscores": [
            {"code": "rom_completeness", "score": score, "notes": [], "metrics": {}},
            {"code": "tempo_consistency", "score": score, "notes": [], "metrics": {}},
            {"code": "stability_control", "score": score, "notes": [], "metrics": {}},
        ],
        "ml_score": score,
        "fusion_weights": {"w_rule": 0.0, "w_ml": 1.0},
        "fusion_flags": [],
        "placeholder_model_notice": False,
        "capture_quality": {
            "q": round(min(quality + 0.02, 1.0), 4),
            "valid_frame_ratio": valid_frame_ratio,
            "capture_quality_band": quality_band(valid_frame_ratio),
        },
        "feature_vectors": [],
        "per_rep_summaries": [],
    }


def _make_squat_session(db, user: User, exercise: ExerciseCatalog, row: tuple) -> None:
    days_ago, score, band, quality, confidence, reps, tags = row
    started = _NOW - timedelta(days=days_ago)
    session = SessionModel(
        user_id=user.id,
        exercise_id=exercise.id,
        mode=exercise.mode,
        exercise_type=exercise.code,
        started_at=started,
        ended_at=started + timedelta(minutes=3),
        status="completed",
        capture_quality=Decimal(str(quality)),
        valid_frame_ratio=Decimal(str(round(min(quality + 0.03, 1.0), 3))),
        score=Decimal(str(score)),
        band=band,
        rep_count=reps,
    )
    db.add(session)
    db.flush()  # need session.id for the FK rows below

    db.add(
        ModuleBResult(
            session_id=session.id,
            exercise_code=exercise.code,
            score=Decimal(str(score)),
            band=band,
            confidence=Decimal(str(confidence)),
            # Clearly-labeled seed marker -- not a real trained-model version,
            # since this data never passed through the actual ML pipeline.
            model_version="demo-seed",
            feature_schema_version="1.0.0",
            q=Decimal(str(round(min(quality + 0.02, 1.0), 4))),
            metrics_json=_squat_metrics_json(score, quality, reps),
            # Pin created_at to the session date (not the seeding instant) so the
            # Stage 7.4 "vs last session" trend has a real chronological order to
            # compare against -- get_previous_result filters on created_at.
            created_at=started,
        )
    )
    for tag in tags:
        db.add(
            ModuleBErrorTag(
                session_id=session.id,
                tag=tag,
                severity=_TAG_SEVERITY.get(tag, "medium"),
                source="rule",
            )
        )


def purge() -> bool:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == DEMO_EMAIL))
        if user is None:
            return False
        db.delete(user)  # cascades to sessions -> module_b_result/error_tags
        db.commit()
    return True


def seed() -> str:
    with SessionLocal() as db:
        sts = _get_exercise(db, "sit_to_stand")
        squat = _get_exercise(db, "squat")

        user = db.scalar(select(User).where(User.email == DEMO_EMAIL))
        if user is None:
            user = User(
                email=DEMO_EMAIL,
                password_hash=hash_password(DEMO_PASSWORD),
                full_name=DEMO_FULL_NAME,
            )
            user.profile = UserProfile(user_type="patient", focus_area="general")
            db.add(user)
            db.flush()
        else:
            # Idempotent re-run: clear prior demo sessions before recreating them
            # so running this twice doesn't double up trend points.
            existing = list(
                db.scalars(select(SessionModel).where(SessionModel.user_id == user.id))
            )
            for s in existing:
                db.delete(s)
            db.flush()

        for row in STS_SESSIONS:
            _make_sts_session(db, user, sts, row)
        for row in SQUAT_SESSIONS:
            _make_squat_session(db, user, squat, row)

        db.commit()
    return DEMO_EMAIL


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--purge", action="store_true", help="Delete the demo account and exit."
    )
    args = parser.parse_args()

    if args.purge:
        removed = purge()
        print(f"Demo progress account removed: {removed}.")
        return

    email = seed()
    print(
        f"Seeded demo progress account '{email}' / password '{DEMO_PASSWORD}' "
        f"with {len(STS_SESSIONS)} STS + {len(SQUAT_SESSIONS)} squat sessions."
    )


if __name__ == "__main__":
    main()
