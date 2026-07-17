"""Deterministic synthetic-stream tests for Stage 4.3 (Lunge) segmentation."""

from __future__ import annotations

import math
import unittest

from app.module_b.lunge.segmentation import (
    LungeSegmentationFSM,
    LungeState,
    segment_lunge_frames,
)


def _landmark(x: float, y: float, z: float = 0.0) -> dict[str, float]:
    return {"x": x, "y": y, "z": z, "visibility": 1.0}


def _frame(
    timestamp_ms: float, left_flexion_deg: float, right_flexion_deg: float
) -> dict:
    """Build an asymmetric world-landmark pose: one knee per side, independently set.

    Mirrors squat's fixture (shoulders one unit above the hips so trunk_length is
    non-zero) but allows left/right flexion to differ, matching a lunge's
    front/back knee split -- unlike squat, the two sides are not required to move
    together.
    """
    landmarks = [_landmark(0.0, 0.0) for _ in range(33)]
    for shoulder_index, hip_index, knee_index, ankle_index, x, flexion_deg in (
        (11, 23, 25, 27, -0.15, left_flexion_deg),
        (12, 24, 26, 28, 0.15, right_flexion_deg),
    ):
        flexion_rad = math.radians(flexion_deg)
        landmarks[shoulder_index] = _landmark(x, -1.0)
        landmarks[hip_index] = _landmark(x, 0.0)
        landmarks[knee_index] = _landmark(x, 1.0)
        landmarks[ankle_index] = _landmark(
            x + math.sin(flexion_rad), 1.0 + math.cos(flexion_rad)
        )
    return {"timestampMs": timestamp_ms, "worldLandmarks": landmarks}


def _append_flexions(
    frames: list[dict],
    start_ms: float,
    left_flexions: list[float],
    right_flexions: list[float],
    step_ms: float = 100.0,
) -> float:
    for index, (left, right) in enumerate(zip(left_flexions, right_flexions)):
        frames.append(_frame(start_ms + index * step_ms, left, right))
    return start_ms + len(left_flexions) * step_ms


def _front_back_split(target_mean: list[float]) -> tuple[list[float], list[float]]:
    """Split one target bilateral-mean sequence into distinct front/back legs.

    front = 1.2x, back = 0.8x the target at every sample, so (front+back)/2
    reproduces target_mean exactly -- letting these fixtures reuse squat's own
    proven enter/exit crossing indices and durations while still exercising two
    genuinely different per-leg values, unlike squat's symmetric fixture.
    """
    front = [value * 1.2 for value in target_mean]
    back = [value * 0.8 for value in target_mean]
    return front, back


def _five_clean_reps(front_side: str = "left", start_ms: float = 0.0) -> list[dict]:
    """Five lunge reps whose bilateral mean matches squat's own validated fixture."""
    target_mean = [0.0, 15.0, 31.0, 60.0, 100.0, 60.0, 31.0, 19.0, 0.0]
    front, back = _front_back_split(target_mean)
    left, right = (front, back) if front_side == "left" else (back, front)
    frames: list[dict] = []
    timestamp_ms = start_ms
    for _ in range(5):
        timestamp_ms = _append_flexions(frames, timestamp_ms, left, right)
        # More than the 0.5 s refractory period at a confirmed standing signal.
        timestamp_ms = _append_flexions(frames, timestamp_ms, [0.0] * 6, [0.0] * 6)
    return frames


class LungeSegmentationTests(unittest.TestCase):
    def test_clean_five_rep_stream_has_exactly_five_reps(self) -> None:
        reps = segment_lunge_frames(_five_clean_reps())

        self.assertEqual(len(reps), 5)
        self.assertAlmostEqual(reps[0].duration_s, 0.5)
        self.assertEqual(reps[0].peak_signal_frame_index, 2)
        # Bilateral mean at the peak frame reproduces squat's own 100deg peak
        # even though front (120deg) and back (80deg) individually differ.
        self.assertAlmostEqual(reps[0].peak_signal_value, 100.0)

    def test_jitter_at_enter_threshold_does_not_create_a_phantom_rep(self) -> None:
        jitter_front, jitter_back = _front_back_split(
            [0.0, 29.0, 31.0, 29.0, 31.0, 19.0, 0.0]
        )
        frames: list[dict] = []
        timestamp_ms = _append_flexions(frames, 0.0, jitter_front, jitter_back)
        _append_flexions(frames, timestamp_ms, [0.0] * 6, [0.0] * 6)
        frames.extend(_five_clean_reps(start_ms=timestamp_ms + 600.0))

        self.assertEqual(len(segment_lunge_frames(frames)), 5)

    def test_partial_descent_that_never_enters_has_no_reps(self) -> None:
        front, back = _front_back_split([0.0, 10.0, 20.0, 29.9, 27.0, 10.0, 0.0])
        frames: list[dict] = []
        _append_flexions(frames, 0.0, front, back)

        self.assertEqual(segment_lunge_frames(frames), [])

    def test_lunge_phase_fsm_reaches_bottom_from_local_peak(self) -> None:
        fsm = LungeSegmentationFSM()
        states = []
        left, right = _front_back_split([0.0, 31.0, 60.0, 100.0, 60.0, 31.0, 19.0])
        for index, (left_flex, right_flex) in enumerate(zip(left, right)):
            fsm.update(_frame(index * 100.0, left_flex, right_flex))
            states.append(fsm.state)

        self.assertEqual(
            states,
            [
                LungeState.STANDING,
                LungeState.DESCENDING,
                LungeState.DESCENDING,
                LungeState.DESCENDING,
                LungeState.BOTTOM,
                LungeState.ASCENDING,
                LungeState.STANDING,
            ],
        )

    def test_same_frames_twice_have_identical_rep_boundaries(self) -> None:
        frames = _five_clean_reps()

        self.assertEqual(segment_lunge_frames(frames), segment_lunge_frames(frames))

    def test_rep_boundaries_are_invariant_to_which_leg_leads(self) -> None:
        """No lunge-specific delta (task.md): the bilateral-mean signal doesn't
        need to know which leg is front, so swapping which side leads must not
        change a single rep boundary, duration, or peak value."""
        left_leads = segment_lunge_frames(_five_clean_reps(front_side="left"))
        right_leads = segment_lunge_frames(_five_clean_reps(front_side="right"))

        self.assertEqual(len(left_leads), len(right_leads))
        for left_rep, right_rep in zip(left_leads, right_leads):
            self.assertAlmostEqual(left_rep.duration_s, right_rep.duration_s)
            self.assertAlmostEqual(
                left_rep.peak_signal_value, right_rep.peak_signal_value
            )
            self.assertEqual(
                left_rep.peak_signal_frame_index, right_rep.peak_signal_frame_index
            )


if __name__ == "__main__":
    unittest.main()
