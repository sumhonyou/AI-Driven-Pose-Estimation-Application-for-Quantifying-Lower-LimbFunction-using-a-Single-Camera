"""Tests for the shared confidence-filter -> gap-fill -> One-Euro pipeline."""

from __future__ import annotations

import unittest

from app.module_a.core.config import MIN_VISIBILITY
from app.module_b.core.preprocessing import preprocess_world_landmarks
from app.module_b.squat.features import extract_squat_features
from app.module_b.squat.segmentation import segment_squat_frames
from tests.test_module_b_segmentation import _five_clean_reps


def _landmark(x: float, y: float, z: float = 0.0, visibility: float = 1.0) -> dict:
    return {"x": x, "y": y, "z": z, "visibility": visibility}


def _frame(timestamp_ms: float, x: float, visibility: float = 1.0) -> dict:
    """One landmark (index 0) moving along x; the other 32 stay put and visible."""
    landmarks = [_landmark(0.0, 0.0) for _ in range(33)]
    landmarks[0] = _landmark(x, 0.0, visibility=visibility)
    return {"timestampMs": timestamp_ms, "worldLandmarks": landmarks}


class GapFillTests(unittest.TestCase):
    def test_empty_stream_returns_empty(self) -> None:
        self.assertEqual(preprocess_world_landmarks([]), [])

    def test_short_gap_is_linearly_interpolated(self) -> None:
        # Landmark 0 goes 0.0 -> (gap of 3, low visibility) -> 4.0 at 100ms steps.
        frames = [
            _frame(0.0, 0.0),
            _frame(100.0, 1.0, visibility=0.1),
            _frame(200.0, 2.0, visibility=0.1),
            _frame(300.0, 3.0, visibility=0.1),
            _frame(400.0, 4.0),
        ]

        result = preprocess_world_landmarks(frames)

        # The gap is short (3 <= interpolation_max_gap_frames=5), so each
        # filled point should sit close to its time-weighted interpolated
        # position rather than holding the pre-gap value (0.0).
        for i in (1, 2, 3):
            self.assertGreater(result[i]["worldLandmarks"][0]["x"], 0.5)
        self.assertLess(
            result[1]["worldLandmarks"][0]["x"], result[3]["worldLandmarks"][0]["x"]
        )

    def test_gap_longer_than_max_is_left_for_hold_last(self) -> None:
        max_gap = 5
        frames = [_frame(0.0, 0.0)]
        for i in range(1, max_gap + 2):  # a gap of max_gap + 1 frames
            frames.append(_frame(i * 100.0, float(i), visibility=0.1))
        frames.append(_frame((max_gap + 2) * 100.0, float(max_gap + 2)))

        result = preprocess_world_landmarks(frames)

        # Not interpolated -> LandmarkSmoother's own hold-last takes over,
        # so every gap frame keeps the pre-gap value (0.0), not a ramp.
        for i in range(1, max_gap + 2):
            self.assertEqual(result[i]["worldLandmarks"][0]["x"], 0.0)

    def test_leading_gap_has_no_anchor_and_is_left_untouched(self) -> None:
        frames = [
            _frame(0.0, 5.0, visibility=0.1),
            _frame(100.0, 5.0, visibility=0.1),
            _frame(200.0, 9.0),
        ]

        result = preprocess_world_landmarks(frames)

        # No valid frame before the gap to interpolate from; the raw (low
        # confidence) value passes through untouched at frame 0, and frame 1
        # only has an OnEuro-filtered value derived from raw inputs, no
        # synthetic interpolation should have been injected.
        self.assertEqual(result[0]["worldLandmarks"][0]["x"], 5.0)

    def test_trailing_gap_has_no_anchor_and_is_left_untouched(self) -> None:
        frames = [
            _frame(0.0, 1.0),
            _frame(100.0, 5.0, visibility=0.1),
            _frame(200.0, 5.0, visibility=0.1),
        ]

        result = preprocess_world_landmarks(frames)

        # No valid frame after the gap; LandmarkSmoother hold-lasts using the
        # last confident smoothed value (from frame 0) for frames 1 and 2.
        self.assertEqual(
            result[1]["worldLandmarks"][0]["x"], result[2]["worldLandmarks"][0]["x"]
        )

    def test_interpolated_point_visibility_is_bumped_to_threshold(self) -> None:
        frames = [
            _frame(0.0, 0.0),
            _frame(100.0, 1.0, visibility=0.1),
            _frame(200.0, 2.0),
        ]

        result = preprocess_world_landmarks(frames)

        self.assertGreaterEqual(
            result[1]["worldLandmarks"][0]["visibility"], MIN_VISIBILITY
        )


class StatefulFullStreamContractTests(unittest.TestCase):
    def test_splitting_the_stream_changes_the_result(self) -> None:
        """OneEuroFilter is stateful: preprocessing must run over the whole
        capture at once. Splitting it into two independently-preprocessed
        halves resets filter history at the split point, so the two
        approaches must diverge -- this is the exact bug X1 exists to
        prevent (an offline pipeline that windows-then-smooths would drift
        from a live pipeline that smooths-then-windows).
        """
        frames = [_frame(i * 100.0, float(i)) for i in range(10)]

        whole = preprocess_world_landmarks(frames)
        split = preprocess_world_landmarks(frames[:5]) + preprocess_world_landmarks(
            frames[5:]
        )

        self.assertNotEqual(
            [f["worldLandmarks"][0]["x"] for f in whole],
            [f["worldLandmarks"][0]["x"] for f in split],
        )


class SquatPipelineRegressionTests(unittest.TestCase):
    """Confirms the Phase 4 live squat flow (segment -> extract_features)
    still works once preprocessing runs in front of it."""

    def test_preprocessed_five_rep_stream_still_segments_and_extracts(self) -> None:
        frames = _five_clean_reps()

        preprocessed = preprocess_world_landmarks(frames)
        reps = segment_squat_frames(preprocessed)

        self.assertEqual(len(reps), 5)
        for rep in reps:
            feature_vector = extract_squat_features(rep)
            self.assertEqual(len(feature_vector.values), len(feature_vector.names))
            self.assertTrue(all(v == v for v in feature_vector.values))  # no NaNs


if __name__ == "__main__":
    unittest.main()
