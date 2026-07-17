"""Deterministic synthetic-stream tests for lunge cycle segmentation.

Rewritten at Stage 5.3 (Lunge) as a **deliberate contract change**, not bent to pass.
The previous suite encoded the borrowed-from-squat threshold model (an
`enter_descending_deg` a rep had to cross and an `exit_standing_deg` it had to fall
back under). That model was measured at 50/88 = 56.8% rep recall against REHAB24-6's
physio-verified boundaries and replaced with cycle detection, so tests asserting
enter/exit behaviour were asserting behaviour that no longer exists:

- `test_jitter_at_enter_threshold_does_not_create_a_phantom_rep` and
  `test_partial_descent_that_never_enters_has_no_reps` both hinged on a 30 deg enter
  threshold. There is no enter threshold now; the equivalent contract is
  "a swing shallower than `cycle_prominence_deg` is not a rep", and that is what the
  replacements below assert.
- `test_lunge_phase_fsm_reaches_bottom_from_local_peak` tested `LungeSegmentationFSM`
  /`LungeState`, both removed with the threshold FSM (a cycle detector has no
  per-frame "standing" state). Grepped for callers first: none outside this test.
- Rep windows are now the **full cycle** (trough to trough) rather than the
  threshold-crossing sub-window, so durations and peak indices legitimately changed.
  That is the point: the full cycle is what the dataset annotates.

`test_continuous_reps_without_returning_to_standing` is the regression guard for the
bug this replaced, and it fails against the old threshold model.
"""

from __future__ import annotations

import math
import unittest

from app.module_b.lunge.config import LUNGE_CONFIG
from app.module_b.lunge.segmentation import segment_lunge_frames


def _landmark(x: float, y: float, z: float = 0.0) -> dict[str, float]:
    return {"x": x, "y": y, "z": z, "visibility": 1.0}


def _frame(
    timestamp_ms: float, left_flexion_deg: float, right_flexion_deg: float
) -> dict:
    """Build an asymmetric world-landmark pose: one knee per side, independently set.

    Mirrors squat's fixture (shoulders one unit above the hips so trunk_length is
    non-zero) but allows left/right flexion to differ, matching a lunge's front/back
    knee split -- unlike squat, the two sides are not required to move together.
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

    front = 1.2x, back = 0.8x the target at every sample, so (front+back)/2 reproduces
    target_mean exactly -- letting these fixtures state one intended mean signal while
    still exercising two genuinely different per-leg values, unlike squat's symmetric
    fixture.
    """
    front = [value * 1.2 for value in target_mean]
    back = [value * 0.8 for value in target_mean]
    return front, back


def _five_clean_reps(front_side: str = "left", start_ms: float = 0.0) -> list[dict]:
    """Five lunge reps, each returning fully to standing in between."""
    target_mean = [0.0, 15.0, 31.0, 60.0, 100.0, 60.0, 31.0, 19.0, 0.0]
    front, back = _front_back_split(target_mean)
    left, right = (front, back) if front_side == "left" else (back, front)
    frames: list[dict] = []
    timestamp_ms = start_ms
    for _ in range(5):
        timestamp_ms = _append_flexions(frames, timestamp_ms, left, right)
        timestamp_ms = _append_flexions(frames, timestamp_ms, [0.0] * 6, [0.0] * 6)
    return frames


class LungeSegmentationTests(unittest.TestCase):
    def test_clean_five_rep_stream_has_exactly_five_reps(self) -> None:
        reps = segment_lunge_frames(_five_clean_reps())

        self.assertEqual(len(reps), 5)
        # The window is the whole cycle: trough (0 deg) -> bottom (100 deg) -> trough,
        # i.e. frames 0..8 at 100 ms each. Under the old threshold model this was the
        # narrower 0.5 s enter-to-exit sub-window.
        self.assertAlmostEqual(reps[0].duration_s, 0.8)
        self.assertEqual(reps[0].peak_signal_frame_index, 4)
        # Bilateral mean at the bottom reproduces the intended 100 deg peak even
        # though front (120 deg) and back (80 deg) individually differ.
        self.assertAlmostEqual(reps[0].peak_signal_value, 100.0)

    def test_continuous_reps_without_returning_to_standing(self) -> None:
        """The regression guard for the bug cycle detection was adopted to fix.

        REHAB24-6 annotates lunge reps back-to-back (median 1-frame gap) and several
        subjects only partially extend at the top of each cycle -- one topped out at
        ~46 deg, never returning near standing. The old threshold FSM closed a rep only
        below `exit_standing_deg = 20`, so it merged that subject's 20 reps into 2
        detections. Here the signal never drops below 40 deg, far above any plausible
        standing threshold, and all four reps must still be found.
        """
        cycle = [40.0, 70.0, 95.0, 70.0]
        target_mean = cycle * 4 + [40.0]
        front, back = _front_back_split(target_mean)
        frames: list[dict] = []
        # 200 ms/frame puts each trough-to-trough cycle at 0.8 s, clear of the 0.5 s
        # `min_rep_duration_s` floor, so this tests the merge behaviour and not the
        # duration guard.
        _append_flexions(frames, 0.0, front, back, step_ms=200.0)

        reps = segment_lunge_frames(frames)

        self.assertEqual(len(reps), 4)
        for rep in reps:
            self.assertAlmostEqual(rep.peak_signal_value, 95.0)

    def test_swing_shallower_than_cycle_prominence_is_not_a_rep(self) -> None:
        """Replaces the old enter-threshold test: prominence is what rejects noise."""
        prominence = LUNGE_CONFIG["segmentation"]["cycle_prominence_deg"]
        peak = prominence - 2.0
        front, back = _front_back_split([0.0, peak / 2, peak, peak / 2, 0.0])
        frames: list[dict] = []
        _append_flexions(frames, 0.0, front, back)

        self.assertEqual(segment_lunge_frames(frames), [])

    def test_jitter_below_cycle_prominence_does_not_create_a_phantom_rep(self) -> None:
        """Small oscillation around a held posture must not register as reps."""
        front, back = _front_back_split([0.0, 6.0, 2.0, 8.0, 3.0, 7.0, 0.0])
        frames: list[dict] = []
        timestamp_ms = _append_flexions(frames, 0.0, front, back)
        frames.extend(_five_clean_reps(start_ms=timestamp_ms))

        self.assertEqual(len(segment_lunge_frames(frames)), 5)

    def test_cycle_shorter_than_min_duration_is_rejected(self) -> None:
        """`min_rep_duration_s` still guards against very brief spurious cycles."""
        front, back = _front_back_split([0.0, 60.0, 0.0])
        frames: list[dict] = []
        # 3 frames at 10 ms = 0.02 s total, far under the 0.5 s minimum.
        _append_flexions(frames, 0.0, front, back, step_ms=10.0)

        self.assertEqual(segment_lunge_frames(frames), [])

    def test_same_frames_twice_have_identical_rep_boundaries(self) -> None:
        frames = _five_clean_reps()

        self.assertEqual(segment_lunge_frames(frames), segment_lunge_frames(frames))

    def test_rep_boundaries_are_invariant_to_which_leg_leads(self) -> None:
        """The bilateral-mean signal doesn't need to know which leg is front, so
        swapping which side leads must not change a single rep boundary, duration, or
        peak value. Retained unchanged: the signal is not what Stage 5.3 replaced."""
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

    def test_non_monotonic_timestamps_are_rejected(self) -> None:
        frames = [_frame(100.0, 0.0, 0.0), _frame(50.0, 0.0, 0.0)]

        with self.assertRaises(ValueError):
            segment_lunge_frames(frames)

    def test_empty_stream_has_no_reps(self) -> None:
        self.assertEqual(segment_lunge_frames([]), [])


if __name__ == "__main__":
    unittest.main()
