"""Contract tests for the shared, runtime-reused Module B squat features."""

from __future__ import annotations

import math
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.module_a.core.schemas import FrameIn
from app.module_b.core.config import MODULE_B_CORE_CONFIG
from app.module_b.core.features import FeatureVector
from app.module_b.core.geometry import (
    hip_flexion_deg,
    knee_flexion_deg,
    shank_vs_vertical_deg,
    trunk_lean_deg,
)
from app.module_b.squat.config import SQUAT_CONFIG
from app.module_b.squat.features import SQUAT_FEATURE_NAMES, extract_squat_features


def _landmark(x: float, y: float, z: float = 0.0) -> dict[str, float]:
    return {"x": x, "y": y, "z": z, "visibility": 1.0}


def _frame(timestamp_ms: float, flexion_deg: float, trunk_lean: float = 0.0) -> dict:
    """Build a metric bilateral pose with a requested knee flexion angle."""
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
    return {"timestampMs": timestamp_ms, "worldLandmarks": landmarks}


class ModuleBGeometryTests(unittest.TestCase):
    def test_hand_computed_joint_and_vertical_angles(self) -> None:
        hip = _landmark(0.0, 0.0)
        knee = _landmark(0.0, 1.0)
        ankle = _landmark(1.0, 1.0)
        shoulder = _landmark(0.5, -math.sqrt(3.0) / 2.0)

        self.assertAlmostEqual(knee_flexion_deg(hip, knee, ankle), 90.0)
        self.assertAlmostEqual(hip_flexion_deg(shoulder, hip, knee), 30.0)
        self.assertAlmostEqual(trunk_lean_deg(shoulder, hip), 30.0)
        self.assertAlmostEqual(shank_vs_vertical_deg(knee, ankle), 90.0)


class SquatFeatureTests(unittest.TestCase):
    def test_feature_vector_schema_and_names_are_stable(self) -> None:
        rep = SimpleNamespace(
            frames=[
                _frame(0.0, 0.0),
                _frame(100.0, 45.0),
                _frame(200.0, 90.0),
                _frame(300.0, 45.0),
                _frame(400.0, 0.0),
            ]
        )
        vector = extract_squat_features(rep)

        self.assertEqual(
            vector.schema_version, MODULE_B_CORE_CONFIG["feature_schema_version"]
        )
        self.assertEqual(vector.names, SQUAT_FEATURE_NAMES)
        self.assertEqual(len(vector.values), len(SQUAT_FEATURE_NAMES))
        self.assertEqual(vector.as_dict()["knee_flex_peak_deg"], 90.0)
        self.assertEqual(vector.as_dict()["knee_flex_min_deg"], 0.0)
        self.assertEqual(vector.as_dict()["knee_rom_deg"], 90.0)
        self.assertAlmostEqual(vector.as_dict()["rep_duration_s"], 0.4)
        self.assertAlmostEqual(vector.as_dict()["descent_ascent_ratio"], 1.0)
        self.assertAlmostEqual(vector.as_dict()["symmetry_index_pct"], 0.0)

    def test_deep_squat_has_higher_peak_flexion_than_shallow_squat(self) -> None:
        deep = extract_squat_features(
            [_frame(0.0, 0.0), _frame(100.0, 60.0), _frame(200.0, 120.0)]
        )
        shallow = extract_squat_features(
            [_frame(0.0, 0.0), _frame(100.0, 30.0), _frame(200.0, 60.0)]
        )

        self.assertGreater(
            deep.as_dict()["knee_flex_peak_deg"],
            shallow.as_dict()["knee_flex_peak_deg"],
        )

    def test_norm_ref_strategy_switches_between_thigh_and_trunk_length(self) -> None:
        frame = _frame(0.0, 0.0)
        # Make the trunk twice the thigh length without changing stance width.
        frame["worldLandmarks"][11]["y"] = -2.0
        frame["worldLandmarks"][12]["y"] = -2.0

        # Both strategies are patched explicitly rather than letting either one ride
        # on whatever SQUAT_CONFIG's default happens to be: this test is about the
        # switch working, so it must not silently re-point when the default changes
        # (as it did in Stage 5.4, thigh_length -> trunk_length).
        with patch.dict(SQUAT_CONFIG, {"norm_ref_strategy": "thigh_length"}):
            thigh_normalized = extract_squat_features([frame]).as_dict()[
                "stance_width_norm"
            ]
        with patch.dict(SQUAT_CONFIG, {"norm_ref_strategy": "trunk_length"}):
            trunk_normalized = extract_squat_features([frame]).as_dict()[
                "stance_width_norm"
            ]

        self.assertAlmostEqual(thigh_normalized, trunk_normalized * 2.0)

    def test_feature_vector_rejects_invalid_ordered_contracts(self) -> None:
        with self.assertRaises(ValueError):
            FeatureVector("1.0.0", ("a",), (1.0, 2.0))
        with self.assertRaises(ValueError):
            FeatureVector("1.0.0", ("a", "a"), (1.0, 2.0))

    def test_extractor_accepts_validated_request_frames(self) -> None:
        vector = extract_squat_features([FrameIn(**_frame(0.0, 90.0))])

        self.assertAlmostEqual(vector.as_dict()["knee_flex_peak_deg"], 90.0)


if __name__ == "__main__":
    unittest.main()
