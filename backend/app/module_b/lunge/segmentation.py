"""Deterministic knee-flexion segmentation for a side-view lunge set.

No lunge-specific delta from squat's Stage 4.3 (task.md). The driving signal is
still the bilateral MEAN knee flexion, not a front-leg-only signal, deliberately:

- The front and back knee both flex and extend in near-synchrony through one
  continuous lunge rep (they cycle together even though their peak magnitudes
  differ), so the mean still rises on descent and falls on return-to-standing --
  the only thing this phase FSM needs.
- Which leg is "front" is a per-set stance property (REHAB24-6's own
  `exercise_subtype` never changes within one video), not something available
  per-frame in the not-yet-segmented stream this function consumes -- resolving
  it here would duplicate Stage 4.2's front-leg inference for no segmentation
  benefit.
- A mean is more robust to single-leg landmark noise/occlusion than a max: in a
  side-view capture the far leg is the more occlusion-prone one, and a max
  signal would let a single noisy leg trigger a false rep boundary; the mean
  halves that impact, matching why squat averages both legs at all.

`mean_knee_flexion_deg` only needs landmarks through index 28 (hip/knee/ankle) --
Stage 4.2's toe-tip requirement is a feature-extraction concern, not this one.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from typing import Any

from app.module_b.core.fsm import HysteresisRepFSM, HysteresisState, Rep
from app.module_b.core.geometry import knee_flexion_deg
from app.module_b.lunge.config import LUNGE_CONFIG


class LungeState(str, Enum):
    """Exercise-level phases layered over the generic threshold collector."""

    STANDING = "STANDING"
    DESCENDING = "DESCENDING"
    BOTTOM = "BOTTOM"
    ASCENDING = "ASCENDING"


class LungeSegmentationFSM:
    """Maps knee-flexion frames to completed reps and interpretable lunge phases."""

    def __init__(self) -> None:
        config = LUNGE_CONFIG["segmentation"]
        self._rep_fsm = HysteresisRepFSM(
            enter_threshold=config["enter_descending_deg"],
            exit_threshold=config["exit_standing_deg"],
            refractory_s=config["refractory_s"],
            min_rep_duration_s=config["min_rep_duration_s"],
        )
        self.state = LungeState.STANDING
        self._previous_flexion: float | None = None

    def update(self, frame: Any) -> Rep | None:
        """Process one frame, returning a confirmed rep only at standing exit."""
        timestamp_s = float(_frame_value(frame, "timestampMs")) / 1000.0
        flexion = mean_knee_flexion_deg(frame)
        previous_generic_state = self._rep_fsm.state
        rep = self._rep_fsm.update(timestamp_s, flexion, frame)

        if rep is not None:
            # The generic peak is the lunge's bottom: it is discovered from the
            # local maximum inside the completed rep, not a fixed depth threshold.
            self.state = LungeState.STANDING
            self._previous_flexion = None
            return rep

        if self._rep_fsm.state is HysteresisState.ACTIVE:
            if previous_generic_state is not HysteresisState.ACTIVE:
                self.state = LungeState.DESCENDING
            elif (
                self.state is LungeState.DESCENDING
                and self._previous_flexion is not None
                and flexion < self._previous_flexion
            ):
                self.state = LungeState.BOTTOM
            elif self.state is LungeState.BOTTOM:
                self.state = LungeState.ASCENDING
            self._previous_flexion = flexion
        elif self._rep_fsm.state is HysteresisState.READY:
            self.state = LungeState.STANDING
            self._previous_flexion = None
        return None


def segment_lunge_frames(frames: list[dict[str, Any]]) -> list[Rep]:
    """Return all confirmed lunge reps from a chronologically ordered frame stream."""
    fsm = LungeSegmentationFSM()
    reps = []
    for frame in frames:
        rep = fsm.update(frame)
        if rep is not None:
            reps.append(rep)
    return reps


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
