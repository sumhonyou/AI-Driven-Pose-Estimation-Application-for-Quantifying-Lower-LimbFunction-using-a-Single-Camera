"""Stage 5.12 — interpretable squat fault gates (depth / lean / heel-rise).

Covers each gate individually against the Phase A thresholds
(ml/reports/SQUAT_FAULT_GATE_ANALYSIS.md), the multi-rep aggregator (the direct
regression proof that a bad rep anywhere in the set is caught even when rep 0 is
clean — the ML only scores rep 0), and the router's band-override + tag composition.
"""

from __future__ import annotations

import math
import unittest
from types import SimpleNamespace

from app.module_b.core.features import FeatureVector
from app.module_b.core.fusion import FusionResult
from app.module_b.core.router import _fault_gate_tags
from app.module_b.squat.config import SQUAT_CONFIG
from app.module_b.squat.exercise import SquatExercise
from app.module_b.squat.fault_gates import (
    FaultGateResult,
    GateCheck,
    depth_gate,
    evaluate_fault_gates,
    heel_rise_gate,
    lean_gate,
)
from app.module_b.squat.features import SQUAT_FEATURE_NAMES, extract_squat_features

GATES = SQUAT_CONFIG["fault_gates"]
DEPTH_MIN = GATES["depth"]["min_knee_flex_peak_deg"]
LEAN_MAX = GATES["lean"]["fault_trunk_lean_peak_deg"]
HEEL_MAX = GATES["heel_rise"]["fault_heel_rise_peak_norm"]


def _feature_vector(**overrides: float) -> FeatureVector:
    """A schema-valid squat FeatureVector with benign defaults, selectively overridden.

    Defaults clear every gate (deep enough, upright, heels down) so a test only has to
    push the one feature it is exercising across its threshold.
    """
    base = {name: 1.0 for name in SQUAT_FEATURE_NAMES}
    base["knee_flex_peak_deg"] = 100.0  # well above the depth floor
    base["trunk_lean_peak_deg"] = 10.0  # well below the lean threshold
    base.update(overrides)
    return FeatureVector(
        schema_version="test",
        names=SQUAT_FEATURE_NAMES,
        values=tuple(base[name] for name in SQUAT_FEATURE_NAMES),
    )


def _landmark(x: float, y: float, z: float = 0.0) -> dict[str, float]:
    return {"x": x, "y": y, "z": z, "visibility": 1.0}


def _frame(
    timestamp_ms: float,
    flexion_deg: float,
    trunk_lean: float = 0.0,
    heel_lift: float = 0.0,
) -> dict:
    """Metric bilateral pose with requested knee flexion, trunk lean, and heel lift.

    ``heel_lift`` raises both heels (landmarks 29/30) above the grounded toes (31/32);
    since world-y increases downward, a lifted heel sits at ``-heel_lift``.
    """
    landmarks = [_landmark(0.0, 0.0) for _ in range(33)]
    flexion_rad = math.radians(flexion_deg)
    lean_rad = math.radians(trunk_lean)
    for shoulder_index, hip_index, knee_index, ankle_index, x in (
        (11, 23, 25, 27, -0.15),
        (12, 24, 26, 28, 0.15),
    ):
        landmarks[hip_index] = _landmark(x, 0.0)
        landmarks[shoulder_index] = _landmark(
            x + math.sin(lean_rad), -math.cos(lean_rad)
        )
        landmarks[knee_index] = _landmark(x, 1.0)
        landmarks[ankle_index] = _landmark(
            x + math.sin(flexion_rad), 1.0 + math.cos(flexion_rad)
        )
    for heel_index, toe_index, x in ((29, 31, -0.15), (30, 32, 0.15)):
        landmarks[toe_index] = _landmark(x, 0.0)
        landmarks[heel_index] = _landmark(x, -heel_lift)
    return {"timestampMs": timestamp_ms, "worldLandmarks": landmarks}


def _clean_rep() -> SimpleNamespace:
    """A deep, upright, heels-down rep — clears all three gates."""
    return SimpleNamespace(
        frames=[
            _frame(0.0, 0.0),
            _frame(100.0, 100.0),
            _frame(200.0, 0.0),
        ]
    )


class DepthGateTests(unittest.TestCase):
    def test_shallow_rep_fails_depth(self) -> None:
        features = _feature_vector(knee_flex_peak_deg=DEPTH_MIN - 5.0)
        check = depth_gate(features, GATES["depth"], rep_index=3)
        self.assertIsNotNone(check)
        self.assertEqual(check.tag, "insufficient_depth")
        self.assertEqual(check.rep_index, 3)
        self.assertAlmostEqual(check.metric_value, DEPTH_MIN - 5.0)

    def test_deep_rep_passes_depth(self) -> None:
        features = _feature_vector(knee_flex_peak_deg=DEPTH_MIN + 5.0)
        self.assertIsNone(depth_gate(features, GATES["depth"], rep_index=0))

    def test_exactly_at_threshold_passes(self) -> None:
        # Gate fires strictly below the floor; the floor itself is acceptable depth.
        features = _feature_vector(knee_flex_peak_deg=DEPTH_MIN)
        self.assertIsNone(depth_gate(features, GATES["depth"], rep_index=0))

    def test_the_message_quotes_the_actual_threshold(self) -> None:
        """Stage 5.20 made the advice actionable by naming the angle to reach. The number
        is written into the copy by hand (and duplicated in the frontend's i18n bundle,
        per Stage 6.2's deliberate-duplication note), so nothing but this test stops the
        threshold and the advice drifting apart."""
        self.assertIn(f"{DEPTH_MIN:.0f}°", GATES["depth"]["message"])


class LeanGateTests(unittest.TestCase):
    def test_excessive_lean_fails(self) -> None:
        features = _feature_vector(trunk_lean_peak_deg=LEAN_MAX + 5.0)
        check = lean_gate(features, GATES["lean"], rep_index=1)
        self.assertIsNotNone(check)
        self.assertEqual(check.tag, "excessive_forward_lean")
        self.assertEqual(check.rep_index, 1)

    def test_upright_passes(self) -> None:
        features = _feature_vector(trunk_lean_peak_deg=LEAN_MAX - 5.0)
        self.assertIsNone(lean_gate(features, GATES["lean"], rep_index=0))

    def test_exactly_at_threshold_fails(self) -> None:
        # Youden cut classifies value >= threshold as the fault, so the edge fails.
        features = _feature_vector(trunk_lean_peak_deg=LEAN_MAX)
        self.assertIsNotNone(lean_gate(features, GATES["lean"], rep_index=0))


class HeelRiseGateTests(unittest.TestCase):
    def test_heel_lift_fails(self) -> None:
        # trunk_length ~= 1.0 in this rig, so heel_lift ~= the normalized metric.
        rep = SimpleNamespace(
            frames=[
                _frame(0.0, 0.0, heel_lift=0.0),
                _frame(100.0, 100.0, heel_lift=HEEL_MAX + 0.05),
                _frame(200.0, 0.0, heel_lift=0.0),
            ]
        )
        check = heel_rise_gate(rep, GATES["heel_rise"], rep_index=2)
        self.assertIsNotNone(check)
        self.assertEqual(check.tag, "heel_lift")
        self.assertGreaterEqual(check.metric_value, HEEL_MAX)

    def test_heels_down_passes(self) -> None:
        self.assertIsNone(heel_rise_gate(_clean_rep(), GATES["heel_rise"], rep_index=0))

    def test_requires_foot_landmarks(self) -> None:
        short_frame = {
            "timestampMs": 0.0,
            "worldLandmarks": [_landmark(0.0, 0.0) for _ in range(29)],
        }
        with self.assertRaises(ValueError):
            heel_rise_gate(
                SimpleNamespace(frames=[short_frame]), GATES["heel_rise"], rep_index=0
            )


class EvaluateFaultGatesTests(unittest.TestCase):
    def test_clean_set_passes_all(self) -> None:
        reps = [_clean_rep(), _clean_rep()]
        features = [_feature_vector(), _feature_vector()]
        result = evaluate_fault_gates(reps, features, GATES)
        self.assertTrue(result.all_passed)
        self.assertEqual(result.failed, ())

    def test_bad_second_rep_is_caught_even_when_first_is_clean(self) -> None:
        # The direct regression: the ML only scores rep 0, so a fault in a later rep
        # must still be caught. Rep 0 is clean; rep 1 leans too far.
        reps = [_clean_rep(), _clean_rep()]
        features = [
            _feature_vector(),
            _feature_vector(trunk_lean_peak_deg=LEAN_MAX + 8.0),
        ]
        result = evaluate_fault_gates(reps, features, GATES)
        self.assertFalse(result.all_passed)
        self.assertEqual(len(result.failed), 1)
        self.assertEqual(result.failed[0].tag, "excessive_forward_lean")
        self.assertEqual(result.failed[0].rep_index, 1)

    def test_multiple_faults_on_one_rep_all_reported(self) -> None:
        reps = [_clean_rep()]
        features = [
            _feature_vector(
                knee_flex_peak_deg=DEPTH_MIN - 5.0,
                trunk_lean_peak_deg=LEAN_MAX + 5.0,
            )
        ]
        result = evaluate_fault_gates(reps, features, GATES)
        tags = {check.tag for check in result.failed}
        self.assertEqual(tags, {"insufficient_depth", "excessive_forward_lean"})

    def test_disabled_gate_is_skipped(self) -> None:
        config = {
            "depth": {**GATES["depth"], "enabled": False},
            "lean": GATES["lean"],
            "heel_rise": GATES["heel_rise"],
        }
        reps = [_clean_rep()]
        features = [_feature_vector(knee_flex_peak_deg=DEPTH_MIN - 20.0)]
        result = evaluate_fault_gates(reps, features, config)
        self.assertTrue(result.all_passed)

    def test_length_mismatch_raises(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_fault_gates([_clean_rep()], [], GATES)


class SquatExerciseFaultGateTests(unittest.TestCase):
    def test_exercise_runs_real_extraction_and_flags_a_leaning_rep(self) -> None:
        exercise = SquatExercise()
        # A deep but heavily leaning rep, built through the REAL feature extractor.
        leaning = SimpleNamespace(
            frames=[
                _frame(0.0, 0.0, trunk_lean=0.0),
                _frame(100.0, 100.0, trunk_lean=55.0),
                _frame(200.0, 0.0, trunk_lean=0.0),
            ]
        )
        features = exercise.extract_features(leaning)
        result = exercise.evaluate_fault_gates([leaning], [features])
        self.assertIsNotNone(result)
        self.assertFalse(result.all_passed)
        self.assertEqual(result.failed[0].tag, "excessive_forward_lean")

    def test_exercise_passes_a_clean_rep(self) -> None:
        exercise = SquatExercise()
        rep = _clean_rep()
        features = exercise.extract_features(rep)
        result = exercise.evaluate_fault_gates([rep], [features])
        self.assertIsNotNone(result)
        self.assertTrue(result.all_passed)


class RouterFaultGateWiringTests(unittest.TestCase):
    def _fusion(self, band: str) -> FusionResult:
        return FusionResult(
            score=9.0,
            band=band,
            rule_score=5.0,
            ml_score=9.0,
            confidence=0.9,
            q=0.9,
            w_rule=0.0,
            w_ml=1.0,
            flags=(),
            model_version="test",
            is_placeholder_model=False,
            placeholder_model_notice=False,
        )

    def test_tags_none_for_passing_or_absent_gates(self) -> None:
        self.assertEqual(_fault_gate_tags(None), [])
        self.assertEqual(
            _fault_gate_tags(FaultGateResult(all_passed=True, failed=())), []
        )

    def test_failed_gates_become_rule_tags_with_reasons(self) -> None:
        result = FaultGateResult(
            all_passed=False,
            failed=(
                GateCheck("excessive_forward_lean", "Lean msg", 50.0, 1),
                GateCheck("heel_lift", "Heel msg", 0.2, 0),
            ),
        )
        tags = _fault_gate_tags(result)
        self.assertEqual([t.tag for t in tags], ["excessive_forward_lean", "heel_lift"])
        self.assertTrue(all(t.source == "rule" for t in tags))
        self.assertTrue(all(t.severity == "high" for t in tags))
        self.assertEqual(tags[0].message, "Lean msg")

    def test_repeated_fault_across_reps_surfaces_once(self) -> None:
        result = FaultGateResult(
            all_passed=False,
            failed=(
                GateCheck("insufficient_depth", "Depth msg", 60.0, 0),
                GateCheck("insufficient_depth", "Depth msg", 62.0, 2),
            ),
        )
        tags = _fault_gate_tags(result)
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0].tag, "insufficient_depth")

    def test_override_replaces_band_only(self) -> None:
        import dataclasses

        good = self._fusion("Good")
        overridden = dataclasses.replace(good, band="Poor")
        self.assertEqual(overridden.band, "Poor")
        # Everything else (score, ml_score, flags) is preserved — the gate changes the
        # verdict, not the underlying measurements.
        self.assertEqual(overridden.score, good.score)
        self.assertEqual(overridden.ml_score, good.ml_score)


if __name__ == "__main__":
    unittest.main()
