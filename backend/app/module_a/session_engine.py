"""Sit-to-Stand (STS) rule-based session engine.

Consumes a list of raw world-landmark frames and produces rep count, timing,
and geometry metrics using a hysteresis finite-state machine (calibrate ->
smooth -> knee angle -> FSM). The same engine instance/code path is used by
the live REST endpoint and the replay harness, so a stored session always
reproduces the exact same result (determinism requirement).
"""

from app.module_a import config
from app.module_a.geometry import knee_angle, trunk_lean_deg
from app.module_a.quality import (average_visibility, is_frame_valid,
                                  session_quality)
from app.module_a.smoothing import LandmarkSmoother

LEFT_HIP, RIGHT_HIP = 23, 24
LEFT_KNEE, RIGHT_KNEE = 25, 26
LEFT_ANKLE, RIGHT_ANKLE = 27, 28
LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12


def _midpoint(a: dict, b: dict) -> dict:
    return {
        "x": (a["x"] + b["x"]) / 2,
        "y": (a["y"] + b["y"]) / 2,
        "z": (a["z"] + b["z"]) / 2,
        "visibility": min(a.get("visibility", 0), b.get("visibility", 0)),
    }


class SessionEngine:
    """Runs the STS FSM over a full frame list and returns metrics + band inputs."""

    def __init__(self):
        self.smoother = LandmarkSmoother()

    def run(self, frames: list[dict]) -> dict:
        if not frames:
            return self._empty_result()

        t0 = frames[0]["timestampMs"] / 1000.0
        frame_validity: list[bool] = []
        frame_avg_visibility: list[float] = []

        posture = "sitting"
        baseline_sit_hip_y: float | None = None
        baseline_locked = False
        left_full_stand = False  # tracks a partial rise that fell back (wobble)
        wobble_count = 0

        rep_count = 0
        rep_event_times: list[float] = (
            []
        )  # seconds, relative to t0, when each rep completed
        last_rep_time = -config.MIN_REP_GAP_MS / 1000.0

        knee_angles: list[float] = []
        trunk_leans: list[float] = []
        calibration_hip_ys: list[float] = []
        calibration_knee_angles: list[float] = []
        session_end_time = 0.0
        stopped_early = False

        for frame in frames:
            t = frame["timestampMs"] / 1000.0 - t0
            world = frame.get("worldLandmarks") or []

            valid = is_frame_valid(world)
            frame_validity.append(valid)
            frame_avg_visibility.append(average_visibility(world))
            session_end_time = t

            if not valid or len(world) < 33:
                continue

            smoothed = self.smoother.smooth_frame(t, world)
            hip = _midpoint(smoothed[LEFT_HIP], smoothed[RIGHT_HIP])
            knee_l = knee_angle(
                smoothed[LEFT_HIP], smoothed[LEFT_KNEE], smoothed[LEFT_ANKLE]
            )
            knee_r = knee_angle(
                smoothed[RIGHT_HIP], smoothed[RIGHT_KNEE], smoothed[RIGHT_ANKLE]
            )
            angle = (knee_l + knee_r) / 2
            shoulder = _midpoint(smoothed[LEFT_SHOULDER], smoothed[RIGHT_SHOULDER])
            lean = trunk_lean_deg(shoulder, hip)

            if t <= config.CALIBRATION_SECONDS:
                calibration_hip_ys.append(hip["y"])
                calibration_knee_angles.append(angle)
                if baseline_sit_hip_y is None:
                    baseline_sit_hip_y = hip["y"]
                continue

            # First frame past calibration: lock the sit baseline from the calibration window.
            if not baseline_locked and calibration_hip_ys:
                baseline_sit_hip_y = sum(calibration_hip_ys) / len(calibration_hip_ys)
                baseline_locked = True

            knee_angles.append(angle)
            trunk_leans.append(lean)

            if posture == "sitting":
                if angle < config.KNEE_STAND_EXIT:
                    left_full_stand = False
                if angle >= config.KNEE_STAND_ENTER and baseline_sit_hip_y is not None:
                    hip_rise = (
                        baseline_sit_hip_y - hip["y"]
                    )  # Y is down; rise = decrease
                    if hip_rise >= config.HIP_RISE_CONFIRM_M:
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
                        baseline_sit_hip_y = hip["y"]
                        posture = "sitting"
                        left_full_stand = False

            if rep_count >= config.TARGET_REP_COUNT:
                stopped_early = True
                break
            if t >= config.MAX_SESSION_SECONDS:
                stopped_early = True
                break

        rep_durations = self._rep_durations(rep_event_times)
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
        }

        return {"metrics": metrics, "quality": quality}

    @staticmethod
    def _rep_durations(rep_event_times: list[float]) -> list[float]:
        durations = []
        prev = 0.0
        for t in rep_event_times:
            durations.append(round(t - prev, 3))
            prev = t
        return durations

    @staticmethod
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
            },
            "quality": {
                "valid_frame_ratio": 0.0,
                "average_visibility": 0.0,
                "quality_band": "poor",
            },
        }
