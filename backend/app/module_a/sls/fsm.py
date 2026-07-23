"""Per-leg lift/hold state machine: WAITING -> LIFTING -> HOLDING -> STOPPED.

Deterministic: fed the same frame sequence it always produces the same hold time
and stop reason. Hysteresis (a separate drop margin) plus a minimum dwell time
absorb noisy foot landmarks so the timer never flickers around the lift-line.
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
        lift_min_dwell_sec: float = config.SLS_LIFT_MIN_DWELL_SEC,
        drop_min_dwell_sec: float = config.SLS_DROP_MIN_DWELL_SEC,
    ):
        self.max_hold_sec = max_hold_sec
        self.lift_min_dwell_sec = lift_min_dwell_sec
        self.drop_min_dwell_sec = drop_min_dwell_sec

        self.state = WAITING
        self.hold_start_t: float | None = None
        self.hold_seconds = 0.0
        self.stop_reason: str | None = None
        self.capped_at_max = False
        self._above_since: float | None = None
        self._below_since: float | None = None

    def update(self, t: float, above_lift_line: bool, above_hold_line: bool) -> str:
        """Advance the FSM by one frame. Returns the current state.

        Two thresholds implement the hysteresis: to START a hold the foot must be
        above the strict lift-line (`above_lift_line`); to KEEP holding it only has
        to stay above the lower drop-line (`above_hold_line`, = line + margin). This
        gap stops the timer flickering when the foot hovers right at the line. Each
        transition additionally requires a minimum real-time dwell (not a frame
        count) so a brief, noisy crossing can't confirm a lift or a drop by itself.
        """
        if self.state == STOPPED:
            return self.state

        if self.state == WAITING:
            if above_lift_line:
                if self._above_since is None:
                    self._above_since = t
                if t - self._above_since >= self.lift_min_dwell_sec:
                    self.state = HOLDING
                    self.hold_start_t = t
                    self._below_since = None
            else:
                self._above_since = None
        elif self.state == HOLDING:
            if above_hold_line:
                # Only advance the timer while the foot is confirmed up, so the
                # drop-confirmation window below never inflates the hold time.
                self._below_since = None
                self.hold_seconds = t - (self.hold_start_t or t)
                if self.hold_seconds >= self.max_hold_sec:
                    self.hold_seconds = self.max_hold_sec
                    self.capped_at_max = True
                    self.state = STOPPED
                    self.stop_reason = "max_duration_reached"
            else:
                if self._below_since is None:
                    self._below_since = t
                if t - self._below_since >= self.drop_min_dwell_sec:
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
