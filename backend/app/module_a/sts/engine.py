"""Sit-to-Stand (STS) rule-based session engine.

Consumes a list of raw world-landmark frames and produces metrics using a
deterministic knee-angle hysteresis FSM. The same engine is used by the live
REST endpoint and the replay harness, guaranteeing determinism: same frames ->
same result.
"""

from app.module_a.core.config import CALIBRATION_SECONDS, MAX_SESSION_SECONDS
from app.module_a.core.geometry import knee_angle, trunk_lean_deg
from app.module_a.core.quality import (
    average_visibility,
    is_frame_valid,
    session_quality,
)
from app.module_a.core.smoothing import LandmarkSmoother
from app.module_a.sts import config

LEFT_HIP, RIGHT_HIP = 23, 24
LEFT_KNEE, RIGHT_KNEE = 25, 26
LEFT_ANKLE, RIGHT_ANKLE = 27, 28
LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12

CHAIN_BY_LEG = {
    "left": (LEFT_SHOULDER, LEFT_HIP, LEFT_KNEE, LEFT_ANKLE),
    "right": (RIGHT_SHOULDER, RIGHT_HIP, RIGHT_KNEE, RIGHT_ANKLE),
}


def _leg_visibility(world: list[dict], knee_idx: int, ankle_idx: int) -> float:
    if len(world) <= ankle_idx:
        return 0.0
    return (
        world[knee_idx].get("visibility", 0.0) + world[ankle_idx].get("visibility", 0.0)
    ) / 2


def _pick_tracked_leg(frames: list[dict]) -> str:
    """Picks whichever side MediaPipe tracked better across the whole session.

    A side-view camera structurally occludes the far leg's knee/ankle behind the
    near leg, so we commit to one side's full shoulder-hip-knee-ankle chain for
    the whole session instead of averaging both (which mixes a good and a
    unreliable reading together). Deterministic: same frames -> same choice.
    """
    left_total = right_total = 0.0
    for frame in frames:
        world = frame.get("worldLandmarks") or []
        left_total += _leg_visibility(world, LEFT_KNEE, LEFT_ANKLE)
        right_total += _leg_visibility(world, RIGHT_KNEE, RIGHT_ANKLE)
    return "left" if left_total >= right_total else "right"


def _rep_durations(rep_event_times: list[float]) -> list[float]:
    durations = []
    prev = 0.0
    for t in rep_event_times:
        durations.append(round(t - prev, 3))
        prev = t
    return durations


def _empty_result() -> dict:
    return {
        "metrics": {
            "rep_count": 0,
            "target_rep_count": config.TARGET_REP_COUNT,
            "completion_time_sec": None,
            "rep_durations_sec": [],
            "avg_rep_time_sec": None,
            "fastest_rep_time_sec": None,
            "slowest_rep_time_sec": None,
            "knee_rom_deg": None,
            "avg_trunk_lean_deg": None,
            "max_trunk_lean_deg": None,
            "wobble_count": 0,
            "session_duration_sec": 0.0,
            "stopped_early": False,
            "tracked_leg": None,
        },
        "quality": {
            "valid_frame_ratio": 0.0,
            "average_visibility": 0.0,
            "quality_band": "poor",
        },
    }


def run_sts(frames: list[dict], smoother: LandmarkSmoother | None = None) -> dict:
    smoother = smoother or LandmarkSmoother()

    if not frames:
        return _empty_result()

    t0 = frames[0]["timestampMs"] / 1000.0
    frame_validity: list[bool] = []
    frame_avg_visibility: list[float] = []

    tracked_leg = _pick_tracked_leg(frames)
    shoulder_idx, hip_idx, knee_idx, ankle_idx = CHAIN_BY_LEG[tracked_leg]

    posture = "sitting"
    left_full_stand = False  # tracks a partial rise that fell back (wobble)
    wobble_count = 0

    rep_count = 0
    rep_event_times: list[float] = (
        []
    )  # seconds, relative to t0, when each rep completed
    last_rep_time = -config.MIN_REP_GAP_MS / 1000.0

    knee_angles: list[float] = []
    trunk_leans: list[float] = []
    session_end_time = 0.0
    stopped_early = False

    for frame in frames:
        t = frame["timestampMs"] / 1000.0 - t0
        world = frame.get("worldLandmarks") or []

        valid = is_frame_valid(world, tracked_leg)
        frame_validity.append(valid)
        frame_avg_visibility.append(average_visibility(world, tracked_leg))
        session_end_time = t

        # frame_validity/valid_frame_ratio (above) drives the session-level
        # capture-quality band; it deliberately requires the tracked leg's
        # whole chain visible at once. The FSM below is more permissive: it
        # only needs a full landmark set, and leans on the smoother's
        # per-landmark hold-last (smoothing.py) to ride out a single landmark
        # briefly dipping below MIN_VISIBILITY (e.g. the ankle at the bottom
        # of a rep) without losing frame-to-frame continuity.
        if len(world) < 33:
            continue

        smoothed = smoother.smooth_frame(t, world)
        hip = smoothed[hip_idx]
        angle = knee_angle(hip, smoothed[knee_idx], smoothed[ankle_idx])
        shoulder = smoothed[shoulder_idx]
        lean = trunk_lean_deg(shoulder, hip)

        if t <= CALIBRATION_SECONDS:
            continue

        knee_angles.append(angle)
        trunk_leans.append(lean)

        # Confirmed by knee-angle hysteresis alone (separate enter/exit bands
        # absorb jitter around the threshold). An earlier version also required
        # the hip to "rise" 8cm, but MediaPipe world landmarks are hip-centered
        # per frame -- the hip's own Y is ~0 by construction and can never show
        # a meaningful rise, so that gate silently blocked every rep.
        if posture == "sitting":
            if angle < config.KNEE_STAND_EXIT:
                left_full_stand = False
            if angle >= config.KNEE_STAND_ENTER:
                posture = "standing"
        elif posture == "standing":
            if angle < config.KNEE_STAND_EXIT and not left_full_stand:
                left_full_stand = True  # started descending from full stand
            if left_full_stand and angle >= config.KNEE_STAND_ENTER:
                # Bounced back up without confirming a sit — count as a wobble.
                wobble_count += 1
                left_full_stand = False
            if angle <= config.KNEE_SIT_ENTER:
                if t - last_rep_time >= config.MIN_REP_GAP_MS / 1000.0:
                    rep_count += 1
                    rep_event_times.append(t)
                    last_rep_time = t
                    posture = "sitting"
                    left_full_stand = False

        if rep_count >= config.TARGET_REP_COUNT:
            stopped_early = True
            break
        if t >= MAX_SESSION_SECONDS:
            stopped_early = True
            break

    rep_durations = _rep_durations(rep_event_times)
    quality = session_quality(frame_validity, frame_avg_visibility)

    metrics = {
        "rep_count": rep_count,
        "target_rep_count": config.TARGET_REP_COUNT,
        "completion_time_sec": rep_event_times[-1] if rep_event_times else None,
        "rep_durations_sec": rep_durations,
        "avg_rep_time_sec": (
            (sum(rep_durations) / len(rep_durations)) if rep_durations else None
        ),
        "fastest_rep_time_sec": min(rep_durations) if rep_durations else None,
        "slowest_rep_time_sec": max(rep_durations) if rep_durations else None,
        "knee_rom_deg": (
            (max(knee_angles) - min(knee_angles)) if knee_angles else None
        ),
        "avg_trunk_lean_deg": (
            (sum(trunk_leans) / len(trunk_leans)) if trunk_leans else None
        ),
        "max_trunk_lean_deg": max(trunk_leans) if trunk_leans else None,
        "wobble_count": wobble_count,
        "session_duration_sec": session_end_time,
        "stopped_early": stopped_early,
        "tracked_leg": tracked_leg,
    }

    return {"metrics": metrics, "quality": quality}
