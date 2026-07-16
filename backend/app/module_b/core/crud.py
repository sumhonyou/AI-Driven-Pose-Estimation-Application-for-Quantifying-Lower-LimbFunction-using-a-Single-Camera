"""Generic hybrid persistence and deterministic read-back for Module B results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session as DbSession

from app.db.models import ModuleBErrorTag, ModuleBResult
from app.db.models import Session as SessionModel
from app.module_b.core.features import FeatureVector
from app.module_b.core.fsm import Rep
from app.module_b.core.fusion import FusionResult
from app.module_b.core.rules import RuleScores


@dataclass(frozen=True)
class ErrorTagWrite:
    """One source-labelled tag to store with a Module B session."""

    tag: str
    severity: str | None
    source: str
    message: str | None = None


def save_result(
    db: DbSession,
    *,
    session: SessionModel,
    exercise_code: str,
    fusion: FusionResult,
    rule_scores: RuleScores,
    feature_vectors: list[FeatureVector],
    reps: list[Rep],
    quality: dict[str, float | str],
    error_tags: list[ErrorTagWrite],
) -> ModuleBResult:
    """Upsert the exact analyzed snapshot without persisting browser frames/video."""
    result = get_result_by_session(db, session.id)
    if result is None:
        result = ModuleBResult(session_id=session.id, exercise_code=exercise_code)
        db.add(result)

    session.status = "completed"
    session.score = fusion.score
    session.band = fusion.band
    session.capture_quality = float(quality["q"])
    session.valid_frame_ratio = float(quality["valid_frame_ratio"])
    session.rep_count = len(reps)

    result.exercise_code = exercise_code
    result.score = fusion.score
    result.band = fusion.band
    result.confidence = fusion.confidence
    result.model_version = fusion.model_version
    result.feature_schema_version = feature_vectors[0].schema_version
    result.q = fusion.q
    result.metrics_json = _metrics_json(
        fusion=fusion,
        rule_scores=rule_scores,
        feature_vectors=feature_vectors,
        reps=reps,
        quality=quality,
    )

    db.execute(delete(ModuleBErrorTag).where(ModuleBErrorTag.session_id == session.id))
    for error_tag in error_tags:
        db.add(
            ModuleBErrorTag(
                session_id=session.id,
                tag=error_tag.tag,
                severity=error_tag.severity,
                source=error_tag.source,
                message=error_tag.message,
            )
        )
    db.add(session)
    db.commit()
    db.refresh(result)
    return result


def get_result_by_session(db: DbSession, session_id: UUID) -> ModuleBResult | None:
    """Return the one hybrid result row for a session, if it exists."""
    return db.scalar(
        select(ModuleBResult).where(ModuleBResult.session_id == session_id)
    )


def get_error_tags(db: DbSession, session_id: UUID) -> list[ModuleBErrorTag]:
    """Read tags in a stable order so repeated GET payloads stay byte-identical."""
    return list(
        db.scalars(
            select(ModuleBErrorTag)
            .where(ModuleBErrorTag.session_id == session_id)
            .order_by(ModuleBErrorTag.tag, ModuleBErrorTag.severity, ModuleBErrorTag.id)
        )
    )


def result_summary(
    result: ModuleBResult, tags: list[ModuleBErrorTag]
) -> dict[str, Any]:
    """Build a stable API payload from the persisted snapshot, never re-deriving it."""
    return {
        "session_id": str(result.session_id),
        "exercise_code": result.exercise_code,
        "score": _number(result.score),
        "band": result.band,
        "confidence": _number(result.confidence),
        "model_version": result.model_version,
        "feature_schema_version": result.feature_schema_version,
        "q": _number(result.q),
        "metrics": result.metrics_json or {},
        "error_tags": [
            {
                "tag": tag.tag,
                "severity": tag.severity,
                "source": tag.source,
                "message": tag.message,
            }
            for tag in sorted(
                tags,
                key=lambda tag: (tag.tag, tag.severity or "", str(tag.id or "")),
            )
        ],
        "created_at": result.created_at.isoformat() if result.created_at else None,
    }


def _metrics_json(
    *,
    fusion: FusionResult,
    rule_scores: RuleScores,
    feature_vectors: list[FeatureVector],
    reps: list[Rep],
    quality: dict[str, float | str],
) -> dict[str, Any]:
    if len(feature_vectors) != len(reps):
        raise ValueError("Each persisted Module B rep requires one FeatureVector")
    return {
        "rule_score": rule_scores.score,
        "rule_subscores": [
            {
                "code": sub_score.code,
                "score": sub_score.score,
                "notes": list(sub_score.notes),
                "metrics": dict(sub_score.metrics),
            }
            for sub_score in rule_scores.sub_scores
        ],
        "ml_score": fusion.ml_score,
        "fusion_weights": {"w_rule": fusion.w_rule, "w_ml": fusion.w_ml},
        "fusion_flags": list(fusion.flags),
        "placeholder_model_notice": fusion.placeholder_model_notice,
        "capture_quality": quality,
        "feature_vectors": [
            {
                "schema_version": features.schema_version,
                "names": list(features.names),
                "values": list(features.values),
            }
            for features in feature_vectors
        ],
        "per_rep_summaries": [
            {
                "start_timestamp_s": rep.start_timestamp_s,
                "end_timestamp_s": rep.end_timestamp_s,
                "duration_s": rep.duration_s,
                "bottom_frame_index": rep.peak_signal_frame_index,
                "bottom_knee_flexion_deg": rep.peak_signal_value,
            }
            for rep in reps
        ],
    }


def _number(value: Any) -> float | None:
    return float(value) if value is not None else None
