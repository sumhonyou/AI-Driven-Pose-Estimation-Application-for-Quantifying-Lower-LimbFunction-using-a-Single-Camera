"""Pure aggregation helpers for the dashboard endpoints.

Kept separate from the router so the grouping logic is unit-testable with plain
objects (no DB), matching the project's existing test style. Every function
takes already-fetched Session-like objects and returns response schemas keyed by
`exercise_type`.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from typing import Any

from app.db.schemas import (
    DashboardErrorTag,
    ExerciseLatest,
    ExerciseTrend,
    TrendPoint,
)


def _to_float(value: Any) -> float | None:
    # Numeric columns come back as Decimal; charts want plain floats.
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def module_b_types(sessions: Iterable[Any]) -> set[str]:
    """Exercise types that own a Module B result -> they carry error tags + confidence."""
    return {
        s.exercise_type
        for s in sessions
        if getattr(s, "module_b_result", None) is not None
    }


def build_latest(sessions: Iterable[Any]) -> dict[str, ExerciseLatest]:
    """Latest session per exercise_type. `sessions` must be newest-first."""
    latest: dict[str, ExerciseLatest] = {}
    for s in sessions:
        if s.exercise_type in latest:
            continue  # first seen == newest, given the ordering contract
        latest[s.exercise_type] = ExerciseLatest(
            score=_to_float(s.score),
            band=s.band,
            capture_quality=_to_float(s.capture_quality),
        )
    return latest


def _leg_metric(
    metrics: dict | None, container: str, leg: str, key: str
) -> float | None:
    """Pull one per-leg value out of a Module A `metrics_json` blob, safely.

    SLS stores `perLeg.{left,right}.holdSeconds` and WBLT stores
    `legs.{left,right}.best_distance_cm`; any missing layer just yields None so a
    partial or legacy row never raises here.
    """
    if not metrics:
        return None
    leg_data = (metrics.get(container) or {}).get(leg) or {}
    return _to_float(leg_data.get(key))


def build_trends(sessions: Iterable[Any]) -> dict[str, ExerciseTrend]:
    """Score/quality/confidence points per exercise_type. `sessions` oldest-first."""
    grouped: dict[str, list[TrendPoint]] = {}
    for s in sessions:
        mb = getattr(s, "module_b_result", None)
        # Stage R12: the per-exercise raw-metric series come off the Module A
        # result -- a queryable column for STS finish time, JSON for the rest.
        ma = getattr(s, "module_a_result", None)
        ma_metrics = getattr(ma, "metrics_json", None) if ma is not None else None
        point = TrendPoint(
            session_id=str(s.id),
            date=s.started_at,
            score=_to_float(s.score),
            band=s.band,
            capture_quality=_to_float(s.capture_quality),
            confidence=_to_float(mb.confidence) if mb is not None else None,
            rep_count=s.rep_count,
            completion_time_sec=_to_float(getattr(ma, "completion_time_sec", None)),
            avg_rep_time_sec=(
                _to_float(ma_metrics.get("avg_rep_time_sec")) if ma_metrics else None
            ),
            hold_left_sec=_leg_metric(ma_metrics, "perLeg", "left", "holdSeconds"),
            hold_right_sec=_leg_metric(ma_metrics, "perLeg", "right", "holdSeconds"),
            distance_left_cm=_leg_metric(
                ma_metrics, "legs", "left", "best_distance_cm"
            ),
            distance_right_cm=_leg_metric(
                ma_metrics, "legs", "right", "best_distance_cm"
            ),
        )
        grouped.setdefault(s.exercise_type, []).append(point)
    # mdc stays default "none": no published MDC on the 0-10 score (see schema).
    return {
        ex_type: ExerciseTrend(points=points) for ex_type, points in grouped.items()
    }


def build_error_tags(sessions: Iterable[Any]) -> dict[str, list[DashboardErrorTag]]:
    """Error-tag frequency per Module B exercise_type; Module A types are absent.

    A Module B type with zero tags is present with an empty list, so the frontend
    can tell "no tags this period" apart from "not a tagging exercise".
    """
    mb_types = module_b_types(sessions)
    counts: dict[str, dict[str, dict[str, Any]]] = {t: {} for t in mb_types}
    for s in sessions:
        if s.exercise_type not in mb_types:
            continue
        for tag in getattr(s, "module_b_error_tags", []) or []:
            bucket = counts[s.exercise_type].setdefault(
                tag.tag, {"severity": tag.severity, "count": 0}
            )
            bucket["count"] += 1
    return {
        ex_type: [
            DashboardErrorTag(
                tag_code=tag_code,
                severity=info["severity"],
                count=info["count"],
            )
            # Most frequent first so the UI bar chart reads top-down.
            for tag_code, info in sorted(
                tag_map.items(), key=lambda kv: kv[1]["count"], reverse=True
            )
        ]
        for ex_type, tag_map in counts.items()
    }
