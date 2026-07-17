"""Deterministic cycle segmentation for a side-view lunge set.

The driving signal is the bilateral MEAN knee flexion. What changed at Stage 5.3
(Lunge) is not the signal but the *model*: reps are found as movement **cycles**
(a flexion maximum bracketed by the flexion minima either side of it), not as
crossings of absolute standing/descending thresholds.

Why, measured rather than argued. Squat's hysteresis thresholds were borrowed for
lunge at Stage 4.3 on a rep-timing-similarity argument, recorded at the time as
transferring "pending Stage 5.4's own empirical check on real lunge reps". Stage 5.3
ran that check against REHAB24-6's physio-verified boundaries and the borrowed model
recovered only 50/88 (56.8%) of side-view reps, against squat's 93/98 (94.9%):

- REHAB24-6 annotates lunge reps **back-to-back** (median gap between consecutive
  reps = 1 frame). A set is a *continuous* sequence, so each boundary sits at the
  top of a cycle, not in a rest period.
- The old FSM closed a rep only when the mean fell back under `exit_standing_deg`.
  Subjects who only partially extend at the top of each cycle never sent it there,
  so consecutive reps merged into one long detection -- precision stayed high
  (94.1%) while recall collapsed. One subject's 20 reps became 2 detections.
- Retuning could not fix it: a single global (enter, exit) pair would need
  exit > 60.0 deg and enter < 14.8 deg simultaneously, with exit < enter.
  Front-knee-only was measured worse; a baseline-relative threshold also failed
  globally. Absolute posture thresholds cannot separate these subjects because rest
  posture and rep depth overlap *across* subjects. Cycle shape does separate them.

The bilateral mean is kept (it is not the problem, and the reasons for it still
stand): both knees cycle together through a rep, "which leg is front" is a per-set
stance property rather than a per-frame one, and a mean is more robust to far-limb
occlusion than a max.

This function is **batch** by contract -- `router.py` hands `exercise.segment()` the
whole preprocessed capture buffer at once -- so it may look at the full stream. The
live TypeScript estimator (`lungeLiveEstimate.ts`) needs a causal variant of the same
idea and carries its own; it is advisory UX only and never authoritative.

`mean_knee_flexion_deg` only needs landmarks through index 28 (hip/knee/ankle) --
Stage 4.2's toe-tip requirement is a feature-extraction concern, not this one.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.module_b.core.fsm import Rep
from app.module_b.core.geometry import knee_flexion_deg
from app.module_b.lunge.config import LUNGE_CONFIG

# The old `LungeState` phase enum (STANDING/DESCENDING/BOTTOM/ASCENDING) went with the
# threshold FSM: a cycle detector has no per-frame "standing" state to be in. Grepped
# for callers before removing -- it had none outside its own test (squat's equivalent
# is likewise consumed only by squat's segmentation and test, never by the API or UI),
# so nothing user-facing depended on it. A rep's shape is still recoverable from
# `Rep.peak_signal_frame_index`, which splits its window into descent and ascent.


def segment_lunge_frames(frames: list[dict[str, Any]]) -> list[Rep]:
    """Return all confirmed lunge reps from a chronologically ordered frame stream.

    One rep = one movement cycle: the flexion minimum before a confirmed flexion
    maximum, through to the flexion minimum after it.
    """
    if not frames:
        return []

    config = LUNGE_CONFIG["segmentation"]
    prominence = config["cycle_prominence_deg"]
    min_rep_duration_s = config["min_rep_duration_s"]

    timestamps_s = [float(_frame_value(f, "timestampMs")) / 1000.0 for f in frames]
    for previous, current in zip(timestamps_s, timestamps_s[1:]):
        if current < previous:
            raise ValueError("Rep frames must be ordered by non-decreasing timestamp")
    signal = [mean_knee_flexion_deg(f) for f in frames]

    reps: list[Rep] = []
    bottoms = _confirmed_maxima(signal, prominence)
    previous_end = 0
    for position, bottom_index in enumerate(bottoms):
        # Each trough search is bounded by the neighbouring bottoms, so it finds the
        # cycle top between two reps rather than the stream's global minimum.
        # Consecutive reps share that top: this rep starts where the last one ended,
        # which is exactly how the dataset annotates them (back-to-back).
        next_bottom = (
            bottoms[position + 1] if position + 1 < len(bottoms) else len(signal) - 1
        )
        start = _argmin(signal, previous_end, bottom_index)
        end = _argmin(signal, bottom_index, next_bottom)
        # Advance past this cycle even if it is rejected below: the trough is still a
        # trough, and leaving `previous_end` stale would let the next rep's start
        # search backwards across a cycle already accounted for.
        previous_end = end
        # Timestamp conversions can represent an exact decimal boundary a few ulps
        # below its mathematical value; retain deterministic boundary intent.
        duration_s = timestamps_s[end] - timestamps_s[start]
        if duration_s + 1e-9 < min_rep_duration_s:
            continue
        reps.append(
            Rep(
                frames=tuple(frames[start : end + 1]),
                start_timestamp_s=timestamps_s[start],
                end_timestamp_s=timestamps_s[end],
                peak_signal_frame_index=bottom_index - start,
                peak_signal_value=signal[bottom_index],
            )
        )
        previous_end = end
    return reps


def _confirmed_maxima(signal: list[float], prominence: float) -> list[int]:
    """Indices of flexion maxima confirmed by a `prominence`-deep swing either side.

    A zigzag/swing pass: a running extremum is only confirmed once the signal has
    reversed by at least `prominence` from it, which rejects jitter without needing
    an absolute threshold anywhere. `prominence` therefore does the job the old
    hysteresis deadband and refractory window used to do.
    """
    maxima: list[int] = []
    direction = 0  # 0 = not yet established, +1 = rising, -1 = falling
    min_index = max_index = 0

    for index in range(1, len(signal)):
        value = signal[index]
        if direction >= 0 and value > signal[max_index]:
            max_index = index
        if direction <= 0 and value < signal[min_index]:
            min_index = index

        if direction != -1 and value <= signal[max_index] - prominence:
            maxima.append(max_index)
            direction = -1
            min_index = index
        elif direction != 1 and value >= signal[min_index] + prominence:
            direction = 1
            max_index = index
    return maxima


def _argmin(signal: list[float], low: int, high: int) -> int:
    """Index of the smallest value in signal[low..high] inclusive, earliest on ties."""
    window = signal[low : high + 1]
    return low + window.index(min(window))


def mean_knee_flexion_deg(frame: Any) -> float:
    """Return bilateral mean knee flexion from the pose's world landmarks."""
    landmarks = _frame_value(frame, "worldLandmarks")
    if len(landmarks) <= 28:
        raise ValueError(
            "Lunge segmentation requires MediaPipe landmarks through index 28"
        )
    left = knee_flexion_deg(landmarks[23], landmarks[25], landmarks[27])
    right = knee_flexion_deg(landmarks[24], landmarks[26], landmarks[28])
    return (left + right) / 2.0


def _frame_value(frame: Any, name: str) -> Any:
    if isinstance(frame, Mapping):
        return frame[name]
    return getattr(frame, name)
