"""Per-leg lift/hold state machine: WAITING -> LIFTING -> HOLDING -> STOPPED.

Deterministic: fed the same frame sequence it always produces the same hold time
and stop reason. Hysteresis (a separate drop margin) plus persistence frames absorb
noisy foot landmarks so the timer never flickers around the lift-line.
"""

from app.module_a.sls import config

WAITING = "WAITING"
LIFTING = "LIFTING"
HOLDING = "HOLDING"
STOPPED = "STOPPED"


class LiftHoldFSM:
    """Tracks a single valid hold gated on the lifted foot staying above the line."""

    def __init__(
        self,
        max_hold_sec: float = config.SLS_MAX_HOLD_SEC,
        lift_persist_frames: int = config.SLS_LIFT_PERSIST_FRAMES,
        drop_persist_frames: int = config.SLS_DROP_PERSIST_FRAMES,
    ):
        self.max_hold_sec = max_hold_sec
        self.lift_persist_frames = lift_persist_frames
        self.drop_persist_frames = drop_persist_frames

        self.state = WAITING
        self.hold_start_t: float | None = None
        self.hold_seconds = 0.0
        self.stop_reason: str | None = None
        self.capped_at_max = False
        self._above_streak = 0
        self._below_streak = 0

    def update(self, t: float, above_lift_line: bool, above_hold_line: bool) -> str:
        """Advance the FSM by one frame. Returns the current state.

        Two thresholds implement the hysteresis: to START a hold the foot must be
        above the strict lift-line (`above_lift_line`); to KEEP holding it only has
        to stay above the lower drop-line (`above_hold_line`, = line + margin). This
        gap stops the timer flickering when the foot hovers right at the line.
        """
        if self.state == STOPPED:
            return self.state

        if self.state == WAITING:
            self._above_streak = self._above_streak + 1 if above_lift_line else 0
            if self._above_streak >= self.lift_persist_frames:
                self.state = HOLDING
                self.hold_start_t = t
                self._below_streak = 0
        elif self.state == HOLDING:
            if above_hold_line:
                # Only advance the timer while the foot is confirmed up, so the
                # drop-confirmation window below never inflates the hold time.
                self._below_streak = 0
                self.hold_seconds = t - (self.hold_start_t or t)
                if self.hold_seconds >= self.max_hold_sec:
                    self.hold_seconds = self.max_hold_sec
                    self.capped_at_max = True
                    self.state = STOPPED
                    self.stop_reason = "max_duration_reached"
            else:
                self._below_streak += 1
                if self._below_streak >= self.drop_persist_frames:
                    self.state = STOPPED
                    self.stop_reason = "foot_dropped_below_line"

        return self.state

    def finalize(self, reason_if_holding: str = "manual_stop") -> None:
        """Close out a hold that was still running when the frames ran out."""
        if self.state == HOLDING:
            self.state = STOPPED
            self.stop_reason = reason_if_holding
        elif self.state == WAITING and self.stop_reason is None:
            # Never crossed the line — no valid hold happened.
            self.stop_reason = "unknown"


class CircleDebouncer:
    """Debounces the raw ball-in-circle signal so a single noisy frame can't flip
    the inside/outside state -- used for both the persisted stability score and
    the live gauge colour/combo. The first sample sets the state directly (no
    startup delay); after that a new side only takes effect once it has held for
    `persist_frames` consecutive frames.
    """

    def __init__(self, persist_frames: int = config.SLS_CIRCLE_PERSIST_FRAMES):
        self.persist_frames = persist_frames
        self.inside: bool | None = None
        self._streak = 0

    def update(self, raw_inside: bool) -> bool:
        if self.inside is None:
            self.inside = raw_inside
            return self.inside

        if raw_inside == self.inside:
            self._streak = 0
            return self.inside

        self._streak += 1
        if self._streak >= self.persist_frames:
            self.inside = raw_inside
            self._streak = 0
        return self.inside
