"""Exercise-agnostic hysteresis rep collector used by Module B plugins."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class HysteresisState(str, Enum):
    """Lifecycle of one threshold-based repetition candidate."""

    READY = "READY"
    ACTIVE = "ACTIVE"
    REFRACTORY = "REFRACTORY"


@dataclass(frozen=True)
class Rep:
    """One confirmed rep with deterministic boundaries and a peak-signal frame."""

    frames: tuple[Any, ...]
    start_timestamp_s: float
    end_timestamp_s: float
    peak_signal_frame_index: int
    peak_signal_value: float

    @property
    def duration_s(self) -> float:
        """Return the inclusive rep boundary duration in seconds."""
        return self.end_timestamp_s - self.start_timestamp_s


class HysteresisRepFSM:
    """Collect rising-signal reps with hysteresis, duration filtering and refractory.

    A plugin supplies a signal where a larger value means "inside a rep". The
    FSM enters at ``enter_threshold`` and only exits at ``exit_threshold``;
    this deadband prevents a noisy signal near the start threshold from creating
    multiple candidates.
    """

    def __init__(
        self,
        *,
        enter_threshold: float,
        exit_threshold: float,
        refractory_s: float,
        min_rep_duration_s: float,
    ) -> None:
        if exit_threshold >= enter_threshold:
            raise ValueError("exit_threshold must be lower than enter_threshold")
        if refractory_s < 0.0 or min_rep_duration_s < 0.0:
            raise ValueError("refractory_s and min_rep_duration_s must not be negative")
        self.enter_threshold = enter_threshold
        self.exit_threshold = exit_threshold
        self.refractory_s = refractory_s
        self.min_rep_duration_s = min_rep_duration_s
        self.state = HysteresisState.READY
        self._candidate_frames: list[Any] = []
        self._candidate_start_s: float | None = None
        self._peak_signal_value: float | None = None
        self._peak_signal_frame_index: int | None = None
        self._refractory_until_s = 0.0
        self._last_timestamp_s: float | None = None

    def update(self, timestamp_s: float, signal: float, frame: Any) -> Rep | None:
        """Advance the FSM with one frame and return a completed rep, if any."""
        if self._last_timestamp_s is not None and timestamp_s < self._last_timestamp_s:
            raise ValueError("Rep frames must be ordered by non-decreasing timestamp")
        self._last_timestamp_s = timestamp_s

        if self.state is HysteresisState.REFRACTORY:
            if timestamp_s < self._refractory_until_s:
                return None
            self.state = HysteresisState.READY

        if self.state is HysteresisState.READY:
            if signal >= self.enter_threshold:
                self._begin_candidate(timestamp_s, signal, frame)
            return None

        self._candidate_frames.append(frame)
        if signal > self._peak_signal_value:
            self._peak_signal_value = signal
            self._peak_signal_frame_index = len(self._candidate_frames) - 1
        if signal > self.exit_threshold:
            return None

        return self._close_candidate(timestamp_s)

    def _begin_candidate(self, timestamp_s: float, signal: float, frame: Any) -> None:
        self.state = HysteresisState.ACTIVE
        self._candidate_frames = [frame]
        self._candidate_start_s = timestamp_s
        self._peak_signal_value = signal
        self._peak_signal_frame_index = 0

    def _close_candidate(self, timestamp_s: float) -> Rep | None:
        if self._candidate_start_s is None:
            raise RuntimeError("Active rep candidate has no start timestamp")
        duration_s = timestamp_s - self._candidate_start_s
        completed_rep = None
        # Timestamp conversions can represent an exact decimal boundary a few
        # ulps below its mathematical value; retain deterministic boundary intent.
        if duration_s + 1e-9 >= self.min_rep_duration_s:
            completed_rep = Rep(
                frames=tuple(self._candidate_frames),
                start_timestamp_s=self._candidate_start_s,
                end_timestamp_s=timestamp_s,
                peak_signal_frame_index=self._peak_signal_frame_index or 0,
                peak_signal_value=self._peak_signal_value or 0.0,
            )
            self.state = HysteresisState.REFRACTORY
            self._refractory_until_s = timestamp_s + self.refractory_s
        else:
            self.state = HysteresisState.READY
        self._candidate_frames = []
        self._candidate_start_s = None
        self._peak_signal_value = None
        self._peak_signal_frame_index = None
        return completed_rep
