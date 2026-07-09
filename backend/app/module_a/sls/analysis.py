"""Official SLS per-leg analysis — pure function over a posted landmark sequence.

Called directly by POST /api/sls/analyze and, unchanged, by the replay harness
(no HTTP dependency here). Deterministic: same frames -> same metrics. This is the
single source of truth for the stored per-leg result; the frontend's live numbers
are only a helper that should agree closely.
"""

from app.module_a.core.quality import session_quality
from app.module_a.core.smoothing import LandmarkSmoother
from app.module_a.sls import config
from app.module_a.sls import geometry as geo
from app.module_a.sls import scoring
from app.module_a.sls.fsm import HOLDING, LiftHoldFSM


def _frame_valid_for_sls(world: list[dict], stance_leg: str) -> bool:
    """SLS needs both hips + the stance ankle visible (front view, balance on one leg)."""
    if not world or len(world) < 33:
        return False
    idxs = [geo.HIP["left"], geo.HIP["right"], geo.ANKLE[stance_leg]]
    return all(world[i].get("visibility", 0.0) >= config.MIN_VISIBILITY for i in idxs)


def _empty_leg(leg: str, stop_reason: str = "landmarks_missing") -> dict:
    """Invalid/empty per-leg result (no valid hold happened)."""
    metrics = {
        "leg": leg,
        "holdSeconds": 0.0,
        "cappedAtMax": False,
        "stopReason": stop_reason,
        "holdScore": 0.0,
        "stabilityScore": 0.0,
        "combinedScore": 0.0,
        "band": "invalid",
        "validFrameRatio": 0.0,
        "percentFramesInsideCircle": 0.0,
        "meanBallExcursionNorm": 0.0,
        "warningTags": [stop_reason],
    }
    quality = {
        "valid_frame_ratio": 0.0,
        "average_visibility": 0.0,
        "quality_band": "poor",
    }
    return {"metrics": metrics, "quality": quality}


def analyze_leg(frames: list[dict], leg: str) -> dict:
    """Analyse one leg's buffered hold. `leg` is the LIFTED (prompted) leg.

    Returns {"metrics": <per-leg dict>, "quality": <session quality dict>}.
    """
    if leg not in ("left", "right"):
        raise ValueError(f"leg must be 'left' or 'right', got {leg!r}")
    if not frames:
        return _empty_leg(leg)

    stance_leg = geo.other_leg(leg)
    smoother = LandmarkSmoother()
    t0 = frames[0]["timestampMs"] / 1000.0

    # Single smoothing pass (the smoother is stateful, so frames must flow through
    # it once, in order). Keep the smoothed frames for the calibration + FSM passes.
    processed: list[tuple[float, list[dict], bool]] = []
    frame_validity: list[bool] = []
    frame_avg_visibility: list[float] = []

    for frame in frames:
        t = frame["timestampMs"] / 1000.0 - t0
        world = frame.get("worldLandmarks") or []
        valid = _frame_valid_for_sls(world, stance_leg)
        frame_validity.append(valid)
        if len(world) >= 33:
            smoothed = smoother.smooth_frame(t, world)
            vis = (
                sum(
                    smoothed[i].get("visibility", 0.0)
                    for i in (geo.HIP["left"], geo.HIP["right"], geo.ANKLE[stance_leg])
                )
                / 3
            )
        else:
            smoothed = world
            vis = 0.0
        frame_avg_visibility.append(vis)
        processed.append((t, smoothed, valid))

    # Baseline from the calibration window (both feet planted): lifted-ankle height
    # and stance-leg length, both from valid frames only.
    cal_ankle_y: list[float] = []
    cal_leg_len: list[float] = []
    for t, world, valid in processed:
        if t <= config.CALIBRATION_SECONDS and valid:
            cal_ankle_y.append(geo.lifted_ankle_y(world, leg))
            cal_leg_len.append(geo.stance_leg_length(world, stance_leg))
    if not cal_ankle_y:
        # No usable calibration frames — can't place the lift-line reliably.
        return _empty_leg(leg, stop_reason="poor_capture_quality")

    baseline_ankle_y = sum(cal_ankle_y) / len(cal_ankle_y)
    leg_len = sum(cal_leg_len) / len(cal_leg_len)
    line_y = geo.lift_line_y(baseline_ankle_y, leg_len, config.SLS_LIFT_LINE_NORM)
    drop_margin = config.SLS_LIFT_HYSTERESIS_NORM * leg_len

    fsm = LiftHoldFSM()
    holding_frames = 0
    inside_frames = 0
    excursion_sum = 0.0

    for t, world, valid in processed:
        if t <= config.CALIBRATION_SECONDS or len(world) < 33:
            continue
        ankle_y = geo.lifted_ankle_y(world, leg)
        above_lift = geo.is_above_line(ankle_y, line_y)
        above_hold = geo.is_above_line(ankle_y, line_y + drop_margin)
        state = fsm.update(t, above_lift, above_hold)
        if state == HOLDING:
            holding_frames += 1
            ball_x = geo.ball_x_norm(world, stance_leg)
            excursion_sum += abs(ball_x)
            if geo.is_inside_circle(ball_x, config.SLS_CIRCLE_RADIUS_NORM):
                inside_frames += 1

    fsm.finalize()
    quality = session_quality(frame_validity, frame_avg_visibility)

    hold_seconds = round(fsm.hold_seconds, 2)
    if hold_seconds <= 0 or holding_frames == 0:
        # Line never validly crossed -> no scoreable hold.
        return _empty_leg(leg, stop_reason=fsm.stop_reason or "unknown")

    percent_inside = inside_frames / holding_frames
    mean_excursion = excursion_sum / holding_frames
    scores = scoring.score_leg(hold_seconds, percent_inside)

    warning_tags: list[str] = []
    if quality["quality_band"] == "moderate":
        warning_tags.append("moderate_capture_quality")
    elif quality["quality_band"] == "poor":
        warning_tags.append("poor_capture_quality")
    if not fsm.capped_at_max and fsm.stop_reason == "foot_dropped_below_line":
        warning_tags.append("incomplete_hold")

    metrics = {
        "leg": leg,
        "holdSeconds": hold_seconds,
        "cappedAtMax": fsm.capped_at_max,
        "stopReason": fsm.stop_reason or "unknown",
        "holdScore": scores["holdScore"],
        "stabilityScore": scores["stabilityScore"],
        "combinedScore": scores["combinedScore"],
        "band": scores["band"],
        "validFrameRatio": round(quality["valid_frame_ratio"], 3),
        "percentFramesInsideCircle": round(percent_inside, 3),
        "meanBallExcursionNorm": round(mean_excursion, 3),
        "warningTags": warning_tags,
    }
    return {"metrics": metrics, "quality": quality}
