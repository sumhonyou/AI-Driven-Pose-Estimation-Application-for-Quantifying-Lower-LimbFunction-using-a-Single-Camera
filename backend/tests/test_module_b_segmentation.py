"""Deterministic synthetic-stream tests for Stage 4.3 squat segmentation."""

from __future__ import annotations

import math
import unittest

from app.module_b.squat.segmentation import (
    SquatSegmentationFSM,
    SquatState,
    segment_squat_frames,
)


def _landmark(x: float, y: float, z: float = 0.0) -> dict[str, float]:
    return {"x": x, "y": y, "z": z, "visibility": 1.0}


def _frame(timestamp_ms: float, flexion_deg: float) -> dict:
    """Build a symmetric world-landmark pose with one requested knee flexion.

    Shoulders sit one unit above the hips (-y is up in this convention) so the pose
    has a real trunk. Segmentation itself only reads hip/knee/ankle, but this fixture
    is shared with feature-extraction tests, and a pose whose shoulders coincide with
    the hip midpoint has a zero-length trunk — anatomically impossible, and it makes
    `norm_ref_strategy="trunk_length"` divide by zero.
    """
    landmarks = [_landmark(0.0, 0.0) for _ in range(33)]
    flexion_rad = math.radians(flexion_deg)
    for shoulder_index, hip_index, knee_index, ankle_index, x in (
        (11, 23, 25, 27, -0.15),
        (12, 24, 26, 28, 0.15),
    ):
        landmarks[shoulder_index] = _landmark(x, -1.0)
        landmarks[hip_index] = _landmark(x, 0.0)
        landmarks[knee_index] = _landmark(x, 1.0)
        landmarks[ankle_index] = _landmark(
            x + math.sin(flexion_rad), 1.0 + math.cos(flexion_rad)
        )
    return {"timestampMs": timestamp_ms, "worldLandmarks": landmarks}


def _append_flexions(
    frames: list[dict], start_ms: float, flexions: list[float], step_ms: float = 100.0
) -> float:
    for index, flexion in enumerate(flexions):
        frames.append(_frame(start_ms + index * step_ms, flexion))
    return start_ms + len(flexions) * step_ms


def _five_clean_reps(start_ms: float = 0.0) -> list[dict]:
    frames: list[dict] = []
    timestamp_ms = start_ms
    for _ in range(5):
        timestamp_ms = _append_flexions(
            frames,
            timestamp_ms,
            [0.0, 15.0, 31.0, 60.0, 100.0, 60.0, 31.0, 19.0, 0.0],
        )
        # More than the 0.5 s refractory period at a confirmed standing signal.
        timestamp_ms = _append_flexions(frames, timestamp_ms, [0.0] * 6)
    return frames


class SquatSegmentationTests(unittest.TestCase):
    def test_clean_five_rep_stream_has_exactly_five_reps(self) -> None:
        reps = segment_squat_frames(_five_clean_reps())

        self.assertEqual(len(reps), 5)
        self.assertAlmostEqual(reps[0].duration_s, 0.5)
        self.assertEqual(reps[0].peak_signal_frame_index, 2)
        self.assertAlmostEqual(reps[0].peak_signal_value, 100.0)

    def test_jitter_at_enter_threshold_does_not_create_a_phantom_rep(self) -> None:
        frames: list[dict] = []
        timestamp_ms = _append_flexions(
            frames,
            0.0,
            [0.0, 29.0, 31.0, 29.0, 31.0, 19.0, 0.0],
        )
        _append_flexions(frames, timestamp_ms, [0.0] * 6)
        frames.extend(_five_clean_reps(timestamp_ms + 600.0))

        self.assertEqual(len(segment_squat_frames(frames)), 5)

    def test_partial_descent_that_never_enters_has_no_reps(self) -> None:
        frames: list[dict] = []
        _append_flexions(
            frames,
            0.0,
            [0.0, 10.0, 20.0, 29.9, 27.0, 10.0, 0.0],
        )

        self.assertEqual(segment_squat_frames(frames), [])

    def test_squat_phase_fsm_reaches_bottom_from_local_peak(self) -> None:
        fsm = SquatSegmentationFSM()
        states = []
        for index, flexion in enumerate([0.0, 31.0, 60.0, 100.0, 60.0, 31.0, 19.0]):
            fsm.update(_frame(index * 100.0, flexion))
            states.append(fsm.state)

        self.assertEqual(
            states,
            [
                SquatState.STANDING,
                SquatState.DESCENDING,
                SquatState.DESCENDING,
                SquatState.DESCENDING,
                SquatState.BOTTOM,
                SquatState.ASCENDING,
                SquatState.STANDING,
            ],
        )

    def test_same_frames_twice_have_identical_rep_boundaries(self) -> None:
        frames = _five_clean_reps()

        self.assertEqual(segment_squat_frames(frames), segment_squat_frames(frames))


if __name__ == "__main__":
    unittest.main()
