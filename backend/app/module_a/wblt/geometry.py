"""WBLT world-landmark geometry: dorsiflexion angle (§5.1), heel-lift detection
(§5.2), and the lateral-alignment capture-quality sub-check (§8).

All measures use MediaPipe WORLD landmarks (metric, scale-invariant). Vertical axis
convention matches the rest of Module A: Y increases DOWNWARD (see sls/geometry.py),
so "world up" is (0, -1, 0).
"""

import math

# MediaPipe landmark indices, per side (blueprint §5.1).
KNEE = {"left": 25, "right": 26}
ANKLE = {"left": 27, "right": 28}
HEEL = {"left": 29, "right": 30}
FOOT_INDEX = {"left": 31, "right": 32}
HIP = {"left": 23, "right": 24}

_UP = (0.0, -1.0, 0.0)


def _sub(a: dict, b: dict) -> tuple[float, float, float]:
    return (a["x"] - b["x"], a["y"] - b["y"], a["z"] - b["z"])


def _dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(
    a: tuple[float, float, float], b: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _norm(a: tuple[float, float, float]) -> float:
    return math.sqrt(_dot(a, a))


def _normalize(a: tuple[float, float, float]) -> tuple[float, float, float]:
    n = _norm(a)
    if n < 1e-9:
        return (0.0, 0.0, 0.0)
    return (a[0] / n, a[1] / n, a[2] / n)


def _scale(a: tuple[float, float, float], s: float) -> tuple[float, float, float]:
    return (a[0] * s, a[1] * s, a[2] * s)


def _vsub(
    a: tuple[float, float, float], b: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def sagittal_side_axis(heel: dict, foot_index: dict) -> tuple[float, float, float]:
    """Lateral (side) axis normal to the leg's sagittal plane.

    forward = FOOT_INDEX - HEEL, orthogonalised against world-up so the plane is
    exactly vertical even if the foot isn't perfectly level; side = up x forward.
    Robust to small camera yaw since only the lateral component is discarded.
    """
    forward_raw = _sub(foot_index, heel)
    forward_orth = _vsub(forward_raw, _scale(_UP, _dot(forward_raw, _UP)))
    forward = _normalize(forward_orth)
    if forward == (0.0, 0.0, 0.0):
        # Degenerate (foot_index directly above/below heel) -- no reliable
        # sagittal direction; caller should treat the frame as unusable.
        return (0.0, 0.0, 0.0)
    return _normalize(_cross(_UP, forward))


def dorsiflexion_angle_deg(
    knee: dict, ankle: dict, heel: dict, foot_index: dict
) -> float | None:
    """Ankle dorsiflexion angle (§5.1): angle between the in-plane shank and vertical.

    Larger angle = more dorsiflexion (knee travels further forward over the ankle).
    Returns None if the sagittal plane can't be determined from this frame.
    """
    side = sagittal_side_axis(heel, foot_index)
    if side == (0.0, 0.0, 0.0):
        return None
    shank = _sub(knee, ankle)
    shank_inplane = _vsub(shank, _scale(side, _dot(shank, side)))
    shank_unit = _normalize(shank_inplane)
    if shank_unit == (0.0, 0.0, 0.0):
        return None
    cos_theta = max(-1.0, min(1.0, _dot(shank_unit, _UP)))
    return math.degrees(math.acos(cos_theta))


def shank_length(knee: dict, ankle: dict) -> float:
    return _norm(_sub(knee, ankle))


def hip_x_separation_norm(left_hip: dict, right_hip: dict, shank_len: float) -> float:
    """§8 lateral_alignment raw signal: hip world-x separation / shank length.

    World landmarks are estimated in the camera's own coordinate frame, so a
    true side-on camera sees the anatomical left-right hip axis foreshortened
    onto the camera's depth (z) axis -- x separation stays small. A frontal
    camera sees that same axis face-on, so x separation approaches the real
    anatomical hip width (a sizeable fraction of leg length). This needs no
    raw 2D image landmarks -- only WORLD landmarks already collected for §5.1.
    """
    if shank_len < 1e-9:
        return 0.0
    return abs(left_hip["x"] - right_hip["x"]) / shank_len


class HeelLiftDetector:
    """Stateful heel-lift validity gate (§5.2), debounced hysteresis on rise_ratio.

    Feed foot-flat frames via `feed_calibration()` during the calibration window,
    then call `finalize()` once (at the window boundary) to lock the baseline from
    whatever frames were collected -- as long as at least `min_calibration_frames`
    arrived. This is deliberately NOT tied to an exact frame count at an assumed
    frame rate: the old "need 30 frames in 1s" rule silently never calibrated on
    sub-30fps webcams, discarding otherwise-valid attempts.

    After calibration, feed frames one at a time via `update()`. A lift is only
    flagged once rise_ratio stays above tolerance for `lift_debounce_frames`
    consecutive frames, so a single noisy world-landmark frame can't invalidate an
    honest attempt. `frame_valid` is False whenever the heel is judged lifted --
    those frames are excluded from theta_peak.
    """

    def __init__(
        self,
        lift_tol_ratio: float,
        hysteresis_ratio: float,
        leg: str,
        min_calibration_frames: int = 5,
        lift_debounce_frames: int = 1,
    ) -> None:
        self._lift_tol_ratio = lift_tol_ratio
        self._hysteresis_ratio = hysteresis_ratio
        self._leg = leg
        self._min_calibration_frames = max(1, min_calibration_frames)
        self._lift_debounce_frames = max(1, lift_debounce_frames)
        self._cal_heel_y: list[float] = []
        self._cal_shank_len: list[float] = []
        self._lift_streak = 0
        self.baseline_heel_y: float | None = None
        self.shank_len: float | None = None
        self.lifted = False

    @property
    def calibrated(self) -> bool:
        return self.baseline_heel_y is not None

    def feed_calibration(self, world: list[dict]) -> None:
        heel = world[HEEL[self._leg]]
        knee = world[KNEE[self._leg]]
        ankle = world[ANKLE[self._leg]]
        self._cal_heel_y.append(heel["y"])
        self._cal_shank_len.append(shank_length(knee, ankle))

    def finalize(self) -> bool:
        """Lock the baseline from collected calibration frames. Returns whether
        calibration succeeded (enough foot-flat frames were seen). Idempotent."""
        if self.calibrated:
            return True
        if len(self._cal_heel_y) < self._min_calibration_frames:
            return False
        ys = sorted(self._cal_heel_y)
        lens = sorted(self._cal_shank_len)
        self.baseline_heel_y = ys[len(ys) // 2]
        self.shank_len = lens[len(lens) // 2] or 1e-6
        return True

    def update(self, world: list[dict]) -> bool:
        """Feed one frame. Returns True if THIS frame's heel is DOWN (rise within
        tolerance) so it may contribute to theta. Separately, `self.lifted` latches
        the debounced attempt-level lift (raised for `lift_debounce_frames` in a
        row) -- that's what invalidates the attempt / triggers the abort, so a
        single noisy above-tolerance frame excludes only itself from theta without
        condemning the whole attempt."""
        if self.baseline_heel_y is None or self.shank_len is None:
            return False
        heel_y = world[HEEL[self._leg]]["y"]
        # Y increases downward -> a raised heel has a SMALLER y than baseline.
        rise_ratio = (self.baseline_heel_y - heel_y) / self.shank_len
        if rise_ratio > self._lift_tol_ratio:
            self._lift_streak += 1
        elif rise_ratio < self._hysteresis_ratio:
            self._lift_streak = 0
        # else: dead zone between hysteresis and tolerance -- hold the streak as-is.
        if not self.lifted:
            if self._lift_streak >= self._lift_debounce_frames:
                self.lifted = True
        elif rise_ratio < self._hysteresis_ratio:
            self.lifted = False
        return rise_ratio <= self._lift_tol_ratio
