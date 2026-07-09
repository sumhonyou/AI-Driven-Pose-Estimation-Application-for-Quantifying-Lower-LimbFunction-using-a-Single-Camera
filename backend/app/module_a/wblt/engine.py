"""Weight-Bearing Lunge Test (WBLT) rule-based session engine.

Tracks trials, measures ankle dorsiflexion ROM and symmetry. Returns trial
count, avg dorsiflexion angle, and symmetry proxy (angle difference L-R).

KNOWN BUG (carried over from the pre-reorg session_engine.py, not fixed here —
see task.md): this calls `angleDeg(...)`, which is not defined anywhere and is
never imported. Any WBLT session that reaches this code path will raise
NameError. Nothing has exercised WBLT end-to-end yet, which is why this has
gone unnoticed.
"""

from app.module_a.core.config import CALIBRATION_SECONDS, MAX_SESSION_SECONDS
from app.module_a.core.quality import average_visibility, session_quality
from app.module_a.core.smoothing import LandmarkSmoother
from app.module_a.wblt import config


def _empty_wblt_result() -> dict:
    return {
        "metrics": {
            "rep_count": 0,
            "target_rep_count": config.TARGET_WBLT_TRIALS,
            "trial_count": 0,
            "target_trials": config.TARGET_WBLT_TRIALS,
            "avg_dorsiflexion_deg": 0.0,
            "max_dorsiflexion_deg": 0.0,
            "avg_symmetry_diff_deg": 0.0,
            "session_duration_sec": 0.0,
            "stopped_early": False,
        },
        "quality": {
            "valid_frame_ratio": 0.0,
            "average_visibility": 0.0,
            "quality_band": "poor",
        },
    }


def run_wblt(frames: list[dict], smoother: LandmarkSmoother | None = None) -> dict:
    smoother = smoother or LandmarkSmoother()

    if not frames:
        return _empty_wblt_result()

    t0 = frames[0]["timestampMs"] / 1000.0
    frame_validity: list[bool] = []
    frame_avg_visibility: list[float] = []

    ankle_l_idx, ankle_r_idx = 27, 28  # LEFT_ANKLE, RIGHT_ANKLE
    knee_l_idx, knee_r_idx = 25, 26  # LEFT_KNEE, RIGHT_KNEE

    trial_count = 0
    in_lunge = False
    lunge_start_time = None
    min_ankle_angle_this_trial = 180.0
    max_ankle_angle_this_trial = 0.0
    trial_dorsiflexion_angles: list[float] = []
    trial_symmetry_diffs: list[float] = []
    session_end_time = 0.0
    stopped_early = False

    for frame in frames:
        t = frame["timestampMs"] / 1000.0 - t0
        world = frame.get("worldLandmarks") or []
        session_end_time = t

        valid = len(world) >= 33
        frame_validity.append(valid)

        if len(world) >= 33:
            frame_avg_visibility.append(average_visibility(world, "left"))
        else:
            frame_avg_visibility.append(0.0)

        if len(world) < 33 or t <= CALIBRATION_SECONDS:
            continue

        smoothed = smoother.smooth_frame(t, world)

        # Measure knee angle (bent = lunge position, straight = standing)
        knee_l = angleDeg(
            smoothed[knee_l_idx + 1],  # hip
            smoothed[knee_l_idx],  # knee
            smoothed[ankle_l_idx],  # ankle
        )
        knee_r = angleDeg(
            smoothed[knee_r_idx + 1],  # hip
            smoothed[knee_r_idx],  # knee
            smoothed[ankle_r_idx],  # ankle
        )
        avg_knee_angle = (knee_l + knee_r) / 2

        # Measure ankle dorsiflexion (angle between foot and lower leg)
        # Simplified: use ankle-to-toe vector angle from vertical
        ankle_l = smoothed[ankle_l_idx]
        ankle_r = smoothed[ankle_r_idx]

        # Dorsiflexion is vertical (negative Y) movement of the foot
        # Proxy: ankle Y position relative to knee (negative = dorsiflexion)
        knee_l_y = smoothed[knee_l_idx].get("y", 0)
        knee_r_y = smoothed[knee_r_idx].get("y", 0)
        ankle_l_y = ankle_l.get("y", 0)
        ankle_r_y = ankle_r.get("y", 0)

        # Dorsiflexion angle proxy: larger Y diff = more dorsiflexion
        dorsi_l = max(0, (knee_l_y - ankle_l_y) * 100)  # Scale to degrees-like range
        dorsi_r = max(0, (knee_r_y - ankle_r_y) * 100)
        avg_dorsiflexion = (dorsi_l + dorsi_r) / 2
        symmetry_diff = abs(dorsi_l - dorsi_r)

        # Detect lunge: knee angle bends below threshold
        if not in_lunge and avg_knee_angle < config.LUNGE_ENTRY_KNEE_ANGLE:
            in_lunge = True
            lunge_start_time = t
            min_ankle_angle_this_trial = 180.0
            max_ankle_angle_this_trial = 0.0

        elif in_lunge:
            min_ankle_angle_this_trial = min(
                min_ankle_angle_this_trial, avg_dorsiflexion
            )
            max_ankle_angle_this_trial = max(
                max_ankle_angle_this_trial, avg_dorsiflexion
            )
            trial_symmetry_diffs.append(symmetry_diff)

            # Exit lunge: knee straightens back up
            if avg_knee_angle >= config.LUNGE_ENTRY_KNEE_ANGLE:
                if lunge_start_time is not None and (t - lunge_start_time) > 0.3:
                    # Valid lunge trial completed
                    trial_count += 1
                    trial_dorsiflexion_angles.append(max_ankle_angle_this_trial)
                in_lunge = False
                lunge_start_time = None

        if trial_count >= config.TARGET_WBLT_TRIALS:
            stopped_early = True
            break
        if t >= MAX_SESSION_SECONDS:
            stopped_early = True
            break

    quality = session_quality(frame_validity, frame_avg_visibility)

    avg_dorsiflexion = (
        (sum(trial_dorsiflexion_angles) / len(trial_dorsiflexion_angles))
        if trial_dorsiflexion_angles
        else 0.0
    )
    avg_symmetry_diff = (
        (sum(trial_symmetry_diffs) / len(trial_symmetry_diffs))
        if trial_symmetry_diffs
        else 0.0
    )

    metrics = {
        "rep_count": trial_count,  # Reuse rep_count to store trial_count for compatibility
        "target_rep_count": config.TARGET_WBLT_TRIALS,
        "trial_count": trial_count,
        "target_trials": config.TARGET_WBLT_TRIALS,
        "avg_dorsiflexion_deg": round(avg_dorsiflexion, 2),
        "max_dorsiflexion_deg": (
            round(max_ankle_angle_this_trial, 2) if trial_dorsiflexion_angles else 0.0
        ),
        "avg_symmetry_diff_deg": round(avg_symmetry_diff, 2),
        "session_duration_sec": session_end_time,
        "stopped_early": stopped_early,
    }

    return {"metrics": metrics, "quality": quality}
