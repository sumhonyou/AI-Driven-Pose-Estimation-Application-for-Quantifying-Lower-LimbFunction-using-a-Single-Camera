"""Deterministic knee-flexion segmentation for a side-view squat set."""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from typing import Any

from app.module_b.core.fsm import HysteresisRepFSM, HysteresisState, Rep
from app.module_b.core.geometry import knee_flexion_deg
from app.module_b.squat.config import SQUAT_CONFIG


class SquatState(str, Enum):
    """Exercise-level phases layered over the generic threshold collector."""

    STANDING = "STANDING"
    DESCENDING = "DESCENDING"
    BOTTOM = "BOTTOM"
    ASCENDING = "ASCENDING"


class SquatSegmentationFSM:
    """Maps knee-flexion frames to completed reps and interpretable squat phases."""

    def __init__(self) -> None:
        config = SQUAT_CONFIG["segmentation"]
        self._rep_fsm = HysteresisRepFSM(
            enter_threshold=config["enter_descending_deg"],
            exit_threshold=config["exit_standing_deg"],
            refractory_s=config["refractory_s"],
            min_rep_duration_s=config["min_rep_duration_s"],
        )
        self.state = SquatState.STANDING
        self._previous_flexion: float | None = None

    def update(self, frame: Any) -> Rep | None:
        """Process one frame, returning a confirmed rep only at standing exit."""
        timestamp_s = float(_frame_value(frame, "timestampMs")) / 1000.0
        flexion = mean_knee_flexion_deg(frame)
        previous_generic_state = self._rep_fsm.state
        rep = self._rep_fsm.update(timestamp_s, flexion, frame)

        if rep is not None:
            # The generic peak is squat's bottom: it is discovered from the local
            # maximum inside the completed rep, not from a fixed depth threshold.
            self.state = SquatState.STANDING
            self._previous_flexion = None
            return rep

        if self._rep_fsm.state is HysteresisState.ACTIVE:
            if previous_generic_state is not HysteresisState.ACTIVE:
                self.state = SquatState.DESCENDING
            elif (
                self.state is SquatState.DESCENDING
                and self._previous_flexion is not None
                and flexion < self._previous_flexion
            ):
                self.state = SquatState.BOTTOM
            elif self.state is SquatState.BOTTOM:
                self.state = SquatState.ASCENDING
            self._previous_flexion = flexion
        elif self._rep_fsm.state is HysteresisState.READY:
            self.state = SquatState.STANDING
            self._previous_flexion = None
        return None

    def flush(self) -> Rep | None:
        """Close a final rep the capture ended on, before it crossed back to standing.

        Config-gated so the behaviour is a deliberate, revertible choice; the ceiling
        is the existing enter threshold, so no new tuned number is introduced.
        """
        config = SQUAT_CONFIG["segmentation"]
        if not config.get("flush_trailing_rep", False):
            return None
        rep = self._rep_fsm.flush(max_signal_to_close=config["enter_descending_deg"])
        if rep is not None:
            self.state = SquatState.STANDING
            self._previous_flexion = None
        return rep


def segment_squat_frames(frames: list[dict[str, Any]]) -> list[Rep]:
    """Return all confirmed squat reps from a chronologically ordered frame stream."""
    fsm = SquatSegmentationFSM()
    reps = []
    for frame in frames:
        rep = fsm.update(frame)
        if rep is not None:
            reps.append(rep)
    trailing_rep = fsm.flush()
    if trailing_rep is not None:
        reps.append(trailing_rep)
    return reps


def mean_knee_flexion_deg(frame: Any) -> float:
    """Return bilateral mean knee flexion from the pose's world landmarks."""
    landmarks = _frame_value(frame, "worldLandmarks")
    if len(landmarks) <= 28:
        raise ValueError(
            "Squat segmentation requires MediaPipe landmarks through index 28"
        )
    left = knee_flexion_deg(landmarks[23], landmarks[25], landmarks[27])
    right = knee_flexion_deg(landmarks[24], landmarks[26], landmarks[28])
    return (left + right) / 2.0


def _frame_value(frame: Any, name: str) -> Any:
    if isinstance(frame, Mapping):
        return frame[name]
    return getattr(frame, name)
