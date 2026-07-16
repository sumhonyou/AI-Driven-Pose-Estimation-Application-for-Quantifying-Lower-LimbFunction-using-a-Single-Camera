"""Contract tests for the shared, runtime-reused Module B lunge features."""

from __future__ import annotations

import math
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.module_a.core.schemas import FrameIn
from app.module_b.core.config import MODULE_B_CORE_CONFIG
from app.module_b.lunge.config import LUNGE_CONFIG
from app.module_b.lunge.features import (LUNGE_FEATURE_NAMES,
                                         extract_lunge_features)

# Feet are clearly separated along +x so the front (more-forward) foot is
# unambiguous; the sign convention here makes +x the anterior (forward) direction.
_FRONT_BASE_X = 0.6
_BACK_BASE_X = -0.6
_FOOT_LEN = 0.15


def _landmark(x: float, y: float, z: float = 0.0) -> dict[str, float]:
    return {"x": x, "y": y, "z": z, "visibility": 1.0}


def _leg(
    landmarks: list, side: str, base_x: float, flex_deg: float, lean: float
) -> None:
    """Place one squat-style leg so knee_flexion_deg == flex_deg exactly."""
    if side == "left":
        shoulder_i, hip_i, knee_i, ankle_i, toe_i = 11, 23, 25, 27, 31
    else:
        shoulder_i, hip_i, knee_i, ankle_i, toe_i = 12, 24, 26, 28, 32
    flex_rad = math.radians(flex_deg)
    lean_rad = math.radians(lean)
    landmarks[hip_i] = _landmark(base_x, 0.0)
    landmarks[shoulder_i] = _landmark(base_x + math.sin(lean_rad), -math.cos(lean_rad))
    landmarks[knee_i] = _landmark(base_x, 1.0)
    ankle_x = base_x + math.sin(flex_rad)
    landmarks[ankle_i] = _landmark(ankle_x, 1.0 + math.cos(flex_rad))
    # Toe ahead of the ankle (+x): the foot points forward.
    landmarks[toe_i] = _landmark(ankle_x + _FOOT_LEN, 1.0 + math.cos(flex_rad))


def _lunge_frame(
    timestamp_ms: float,
    front_side: str,
    front_flex: float,
    back_flex: float,
    trunk_lean: float = 0.0,
) -> dict:
    """Build a lunge pose: front_side is planted forward with front_flex flexion."""
    landmarks = [_landmark(0.0, 0.0) for _ in range(33)]
    back_side = "right" if front_side == "left" else "left"
    _leg(landmarks, front_side, _FRONT_BASE_X, front_flex, trunk_lean)
    _leg(landmarks, back_side, _BACK_BASE_X, back_flex, trunk_lean)
    return {"timestampMs": timestamp_ms, "worldLandmarks": landmarks}


def _descent_ascent(front_side: str, peak: float) -> list[dict]:
    return [
        _lunge_frame(0.0, front_side, 0.0, 0.0),
        _lunge_frame(100.0, front_side, peak / 2.0, peak / 4.0),
        _lunge_frame(200.0, front_side, peak, peak / 2.0),
        _lunge_frame(300.0, front_side, peak / 2.0, peak / 4.0),
        _lunge_frame(400.0, front_side, 0.0, 0.0),
    ]


class LungeFeatureSchemaTests(unittest.TestCase):
    def test_feature_vector_schema_names_and_metadata(self) -> None:
        rep = SimpleNamespace(frames=_descent_ascent("left", 90.0))
        vector = extract_lunge_features(rep)

        self.assertEqual(
            vector.schema_version, MODULE_B_CORE_CONFIG["feature_schema_version"]
        )
        self.assertEqual(vector.names, LUNGE_FEATURE_NAMES)
        self.assertEqual(len(vector.values), len(LUNGE_FEATURE_NAMES))
        # Lead leg is metadata, not a numeric feature.
        self.assertEqual(vector.lead_leg, "left")
        features = vector.as_dict()
        self.assertAlmostEqual(features["front_knee_flex_peak_deg"], 90.0)
        self.assertAlmostEqual(features["front_knee_flex_min_deg"], 0.0)
        self.assertAlmostEqual(features["front_knee_rom_deg"], 90.0)
        self.assertAlmostEqual(features["back_knee_flex_peak_deg"], 45.0)
        self.assertAlmostEqual(features["rep_duration_s"], 0.4)
        self.assertAlmostEqual(features["descent_ascent_ratio"], 1.0)

    def test_within_rep_symmetry_and_valgus_are_absent_by_design(self) -> None:
        self.assertNotIn("symmetry_index_pct", LUNGE_FEATURE_NAMES)
        self.assertNotIn("knee_valgus_proxy", LUNGE_FEATURE_NAMES)

    def test_extractor_accepts_validated_request_frames(self) -> None:
        vector = extract_lunge_features(
            [FrameIn(**_lunge_frame(0.0, "left", 90.0, 40.0))]
        )

        self.assertAlmostEqual(vector.as_dict()["front_knee_flex_peak_deg"], 90.0)

    def test_requires_full_mediapipe_33_landmarks_for_foot_tips(self) -> None:
        frame = _lunge_frame(0.0, "left", 90.0, 40.0)
        frame["worldLandmarks"] = frame["worldLandmarks"][:31]  # drop the toe joints
        with self.assertRaises(ValueError):
            extract_lunge_features([frame])


class LungeLeadLegTests(unittest.TestCase):
    def test_features_are_lead_leg_invariant(self) -> None:
        """A left-lead and an identical right-lead rep yield the same numbers."""
        left_lead = extract_lunge_features(_descent_ascent("left", 90.0))
        right_lead = extract_lunge_features(_descent_ascent("right", 90.0))

        self.assertEqual(left_lead.lead_leg, "left")
        self.assertEqual(right_lead.lead_leg, "right")
        for name in LUNGE_FEATURE_NAMES:
            self.assertAlmostEqual(
                left_lead.as_dict()[name],
                right_lead.as_dict()[name],
                msg=f"{name} differs between left- and right-lead reps",
            )

    def test_inferred_front_leg_is_the_more_forward_foot(self) -> None:
        vector = extract_lunge_features(_descent_ascent("right", 90.0))
        # Right foot is planted forward, so the deep-flexing front leg is the right.
        self.assertEqual(vector.lead_leg, "right")
        self.assertAlmostEqual(vector.as_dict()["front_knee_flex_peak_deg"], 90.0)

    def test_lead_leg_override_forces_the_front_leg(self) -> None:
        """Offline training (Stage 5.3) passes the known exercise_subtype."""
        frames = _descent_ascent("left", 90.0)  # geometry says front = left (peak 90)
        forced = extract_lunge_features(frames, lead_leg="right")

        self.assertEqual(forced.lead_leg, "right")
        # Forcing right makes the shallow back leg the "front", so its peak wins.
        self.assertAlmostEqual(forced.as_dict()["front_knee_flex_peak_deg"], 45.0)


class LungeFeatureValueTests(unittest.TestCase):
    def test_deeper_front_lunge_has_higher_front_knee_peak(self) -> None:
        deep = extract_lunge_features(_descent_ascent("left", 110.0))
        shallow = extract_lunge_features(_descent_ascent("left", 60.0))

        self.assertGreater(
            deep.as_dict()["front_knee_flex_peak_deg"],
            shallow.as_dict()["front_knee_flex_peak_deg"],
        )

    def test_knee_passes_toe_sign_flips_with_knee_position(self) -> None:
        # Front (left) foot planted forward, flat; back (right) foot behind, flat.
        base = [_landmark(0.0, 0.0) for _ in range(33)]
        base[24] = _landmark(_BACK_BASE_X, 0.0)  # right hip (back)
        base[26] = _landmark(_BACK_BASE_X, 1.0)  # right knee
        base[28] = _landmark(_BACK_BASE_X, 2.0)  # right ankle (planted)
        base[32] = _landmark(_BACK_BASE_X + _FOOT_LEN, 2.0)  # right toe ahead
        base[23] = _landmark(_FRONT_BASE_X, 0.0)  # left hip (front)
        base[27] = _landmark(_FRONT_BASE_X, 2.0)  # left ankle (planted forward)
        base[31] = _landmark(_FRONT_BASE_X + _FOOT_LEN, 2.0)  # left toe ahead of ankle

        def frame_with_front_knee_x(knee_x: float) -> dict:
            landmarks = [dict(lm) for lm in base]
            landmarks[25] = _landmark(knee_x, 1.0)  # left knee (front)
            return {"timestampMs": 0.0, "worldLandmarks": landmarks}

        front_toe_x = _FRONT_BASE_X + _FOOT_LEN
        knee_behind_toe = extract_lunge_features(
            [frame_with_front_knee_x(front_toe_x - 0.2)]
        )
        knee_past_toe = extract_lunge_features(
            [frame_with_front_knee_x(front_toe_x + 0.2)]
        )

        self.assertLess(knee_behind_toe.as_dict()["knee_passes_toe_norm"], 0.0)
        self.assertGreater(knee_past_toe.as_dict()["knee_passes_toe_norm"], 0.0)

    def test_norm_ref_strategy_switches_between_thigh_and_trunk_length(self) -> None:
        frame = _lunge_frame(0.0, "left", 0.0, 0.0)
        # Make the trunk twice the thigh length without changing stance length.
        frame["worldLandmarks"][11]["y"] = -2.0
        frame["worldLandmarks"][12]["y"] = -2.0

        with patch.dict(LUNGE_CONFIG, {"norm_ref_strategy": "thigh_length"}):
            thigh_normalized = extract_lunge_features([frame]).as_dict()[
                "stance_length_norm"
            ]
        with patch.dict(LUNGE_CONFIG, {"norm_ref_strategy": "trunk_length"}):
            trunk_normalized = extract_lunge_features([frame]).as_dict()[
                "stance_length_norm"
            ]

        self.assertAlmostEqual(thigh_normalized, trunk_normalized * 2.0)

    def test_same_frames_produce_identical_vectors(self) -> None:
        frames = _descent_ascent("left", 90.0)
        first = extract_lunge_features(frames)
        second = extract_lunge_features(frames)

        self.assertEqual(first.values, second.values)
        self.assertEqual(first.lead_leg, second.lead_leg)


if __name__ == "__main__":
    unittest.main()
