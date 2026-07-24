"""Phase 7 Stage 7.0 tests for the exercise_type-keyed dashboard aggregation.

Unit-tests the pure builders in app.api.dashboard_service with plain fake rows
(no DB / HTTP), matching the project's existing test style.
"""

from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from app.api.dashboard_service import (
    build_error_tags,
    build_latest,
    build_trends,
    module_b_types,
)

_BASE = datetime(2026, 7, 1, tzinfo=UTC)


def _tag(tag: str, severity: str = "med") -> SimpleNamespace:
    return SimpleNamespace(tag=tag, severity=severity)


def _session(
    exercise_type: str,
    *,
    day: int = 0,
    score=None,
    band=None,
    capture_quality=None,
    confidence=None,
    is_module_b: bool = False,
    tags: list | None = None,
    rep_count: int | None = None,
    completion_time_sec=None,
    metrics_json: dict | None = None,
) -> SimpleNamespace:
    # A Module B session always carries a module_b_result (even if confidence is
    # None); that presence is how the builders classify the exercise type.
    module_b_result = SimpleNamespace(confidence=confidence) if is_module_b else None
    # Stage R12: Module A result is the source of the per-exercise raw-metric
    # series (STS finish time column + avg_rep_time_sec/perLeg/legs JSON). Absent
    # for Module B / unscored sessions, so build_trends must tolerate None.
    module_a_result = (
        SimpleNamespace(
            completion_time_sec=completion_time_sec, metrics_json=metrics_json
        )
        if (completion_time_sec is not None or metrics_json is not None)
        else None
    )
    return SimpleNamespace(
        id=uuid4(),
        exercise_type=exercise_type,
        started_at=_BASE + timedelta(days=day),
        score=score,
        band=band,
        capture_quality=capture_quality,
        module_b_result=module_b_result,
        module_a_result=module_a_result,
        module_b_error_tags=tags or [],
        rep_count=rep_count,
    )


class ModuleBDetectionTests(unittest.TestCase):
    def test_only_sessions_with_module_b_result_are_module_b(self) -> None:
        sessions = [
            _session("sit_to_stand", score=8),
            _session("squat", is_module_b=True, score=7),
        ]
        self.assertEqual(module_b_types(sessions), {"squat"})


class BuildLatestTests(unittest.TestCase):
    def test_picks_first_seen_per_type_given_newest_first(self) -> None:
        # Caller passes newest-first; builder must keep the first occurrence.
        newest_first = [
            _session("sit_to_stand", day=3, score=Decimal("9.0"), band="Good"),
            _session("sit_to_stand", day=1, score=Decimal("4.0"), band="Poor"),
            _session("squat", day=2, score=Decimal("6.5"), band="Fair"),
        ]
        latest = build_latest(newest_first)
        self.assertEqual(set(latest), {"sit_to_stand", "squat"})
        self.assertEqual(latest["sit_to_stand"].score, 9.0)
        self.assertEqual(latest["sit_to_stand"].band, "Good")
        self.assertEqual(latest["squat"].score, 6.5)

    def test_empty_account_returns_empty(self) -> None:
        self.assertEqual(build_latest([]), {})


class BuildTrendsTests(unittest.TestCase):
    def test_groups_by_exercise_type_and_preserves_order(self) -> None:
        sessions = [
            _session("sit_to_stand", day=0, score=Decimal("5.0")),
            _session(
                "squat",
                day=1,
                score=Decimal("6.0"),
                is_module_b=True,
                confidence=Decimal("0.90"),
            ),
            _session("sit_to_stand", day=2, score=Decimal("7.0")),
        ]
        trends = build_trends(sessions)
        self.assertEqual(set(trends), {"sit_to_stand", "squat"})
        sts_scores = [p.score for p in trends["sit_to_stand"].points]
        self.assertEqual(sts_scores, [5.0, 7.0])  # oldest-first preserved

    def test_confidence_only_for_module_b(self) -> None:
        sessions = [
            _session("sit_to_stand", score=Decimal("5.0")),
            _session("squat", is_module_b=True, confidence=Decimal("0.8125")),
        ]
        trends = build_trends(sessions)
        self.assertIsNone(trends["sit_to_stand"].points[0].confidence)
        self.assertEqual(trends["squat"].points[0].confidence, 0.8125)

    def test_rep_count_is_denormalized_onto_the_trend_point(self) -> None:
        # Stage 5.22: lets the frontend chart attempts vs counted reps per session
        # without a second endpoint. None for exercises with no rep concept (SLS/WBLT).
        sessions = [
            _session("squat", is_module_b=True, score=Decimal("6.7"), rep_count=9),
            _session(
                "supported_single_leg_stance", score=Decimal("8.0"), rep_count=None
            ),
        ]
        trends = build_trends(sessions)
        self.assertEqual(trends["squat"].points[0].rep_count, 9)
        self.assertIsNone(trends["supported_single_leg_stance"].points[0].rep_count)

    def test_sts_time_series_read_from_module_a_result(self) -> None:
        # Stage R12: STS finish time is a queryable column; avg rep time is JSON.
        sessions = [
            _session(
                "sit_to_stand",
                score=Decimal("7.0"),
                completion_time_sec=Decimal("13.4"),
                metrics_json={"avg_rep_time_sec": 2.2},
            )
        ]
        point = build_trends(sessions)["sit_to_stand"].points[0]
        self.assertEqual(point.completion_time_sec, 13.4)
        self.assertEqual(point.avg_rep_time_sec, 2.2)
        # Per-leg fields stay None for a non-per-leg exercise.
        self.assertIsNone(point.hold_left_sec)
        self.assertIsNone(point.distance_right_cm)

    def test_sls_best_hold_per_leg_read_from_metrics_json(self) -> None:
        sessions = [
            _session(
                "supported_single_leg_stance",
                score=Decimal("8.0"),
                metrics_json={
                    "perLeg": {
                        "left": {"holdSeconds": 12.5},
                        "right": {"holdSeconds": 9.0},
                    }
                },
            )
        ]
        point = build_trends(sessions)["supported_single_leg_stance"].points[0]
        self.assertEqual(point.hold_left_sec, 12.5)
        self.assertEqual(point.hold_right_sec, 9.0)
        self.assertIsNone(point.completion_time_sec)

    def test_wblt_best_distance_per_leg_read_from_metrics_json(self) -> None:
        sessions = [
            _session(
                "weight_bearing_lunge_test",
                score=Decimal("7.5"),
                metrics_json={
                    "legs": {
                        "left": {"best_distance_cm": 9.0},
                        "right": {"best_distance_cm": 11.5},
                    }
                },
            )
        ]
        point = build_trends(sessions)["weight_bearing_lunge_test"].points[0]
        self.assertEqual(point.distance_left_cm, 9.0)
        self.assertEqual(point.distance_right_cm, 11.5)

    def test_missing_module_a_result_leaves_metric_series_none(self) -> None:
        # A session that never produced a Module A result (e.g. squat/Module B, or
        # an unscored session) must not raise -- every new field is simply None.
        point = build_trends([_session("squat", is_module_b=True)])["squat"].points[0]
        self.assertIsNone(point.completion_time_sec)
        self.assertIsNone(point.avg_rep_time_sec)
        self.assertIsNone(point.hold_left_sec)
        self.assertIsNone(point.distance_left_cm)

    def test_score_trend_never_asserts_published_mdc(self) -> None:
        # No published MDC exists on the 0-10 score, even for WBLT.
        sessions = [
            _session("weight_bearing_lunge_test", score=Decimal("8.0")),
            _session("squat", is_module_b=True, score=Decimal("6.0")),
        ]
        trends = build_trends(sessions)
        for ex_type in ("weight_bearing_lunge_test", "squat"):
            self.assertEqual(trends[ex_type].mdc_source, "none")
            self.assertIsNone(trends[ex_type].mdc)


class BuildErrorTagsTests(unittest.TestCase):
    def test_module_a_types_are_absent_not_empty(self) -> None:
        sessions = [
            _session("sit_to_stand", score=8),
            _session("squat", is_module_b=True, tags=[_tag("insufficient_depth")]),
        ]
        result = build_error_tags(sessions)
        self.assertNotIn("sit_to_stand", result)  # Module A has no error-tag concept
        self.assertIn("squat", result)

    def test_module_b_with_zero_tags_is_present_and_empty(self) -> None:
        sessions = [_session("squat", is_module_b=True, tags=[])]
        result = build_error_tags(sessions)
        self.assertEqual(result, {"squat": []})

    def test_counts_and_ranks_tags_most_frequent_first(self) -> None:
        sessions = [
            _session(
                "squat",
                is_module_b=True,
                tags=[_tag("trunk_lean"), _tag("insufficient_depth")],
            ),
            _session("squat", is_module_b=True, tags=[_tag("insufficient_depth")]),
            _session("squat", is_module_b=True, tags=[_tag("insufficient_depth")]),
        ]
        tags = build_error_tags(sessions)["squat"]
        self.assertEqual(tags[0].tag_code, "insufficient_depth")
        self.assertEqual(tags[0].count, 3)
        self.assertEqual(tags[1].tag_code, "trunk_lean")
        self.assertEqual(tags[1].count, 1)

    def test_empty_account_returns_empty(self) -> None:
        self.assertEqual(build_error_tags([]), {})


if __name__ == "__main__":
    unittest.main()
