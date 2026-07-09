import math
import unittest

from app.module_a.core.quality import average_visibility
from app.module_a.sts.engine import run_sts


def _landmark(x, y, z=0.0, vis=1.0):
    return {"x": x, "y": y, "z": z, "visibility": vis}


def _sts_frame(t_ms, knee_angle_deg, hip_y, occluded_ankle_vis):
    """One side-view STS frame: left leg always well tracked, right leg
    (the far leg from the camera) has its knee/ankle visibility degraded."""
    lm = [_landmark(0, 0) for _ in range(33)]
    knee_rad = math.radians(knee_angle_deg)
    hip = (0.0, hip_y, 0.0)
    knee = (0.0, hip_y + 0.5, 0.0)
    ankle = (
        0.5 * math.sin(math.pi - knee_rad),
        knee[1] + 0.5 * math.cos(math.pi - knee_rad),
        0.0,
    )
    shoulder = (0.0, hip_y - 0.5, 0.0)
    lm[23] = _landmark(*hip)  # left hip
    lm[24] = _landmark(*hip)  # right hip
    lm[25] = _landmark(*knee)  # left knee
    lm[26] = _landmark(*knee, vis=occluded_ankle_vis)  # right knee
    lm[27] = _landmark(*ankle)  # left ankle
    lm[28] = _landmark(*ankle, vis=occluded_ankle_vis)  # right ankle
    lm[11] = _landmark(*shoulder)  # left shoulder
    lm[12] = _landmark(*shoulder)  # right shoulder
    return {"timestampMs": t_ms, "worldLandmarks": lm}


class ModuleAQualityTests(unittest.TestCase):
    def test_average_visibility_counts_missing_required_landmarks_as_zero(self):
        landmarks = [{"visibility": 1.0} for _ in range(24)]

        # Left chain = shoulder(11), hip(23), knee(25), ankle(27). Only the first
        # two indices exist in a 24-landmark list; knee/ankle count as 0.0.
        self.assertEqual(average_visibility(landmarks, "left"), 2 / 4)

    def test_session_engine_handles_short_landmark_frames(self):
        frames = [
            {
                "timestampMs": 0,
                "worldLandmarks": [{"visibility": 1.0} for _ in range(10)],
            }
        ]

        result = run_sts(frames)

        self.assertEqual(result["metrics"]["rep_count"], 0)
        self.assertEqual(result["quality"]["valid_frame_ratio"], 0.0)
        self.assertEqual(result["quality"]["quality_band"], "poor")

    def test_session_engine_tracks_the_visible_leg_when_the_other_is_occluded(self):
        """Reproduces a pure side-view capture: the far leg's knee/ankle stay
        below MIN_VISIBILITY almost the whole session, like a real recording
        where only one leg is angled toward the camera."""
        frames = []
        t = 0
        for _ in range(75):  # 2.5s calibration, sitting
            frames.append(_sts_frame(t, 90, hip_y=0.0, occluded_ankle_vis=0.3))
            t += 33
        for i in range(30):  # rise
            frac = i / 29
            frames.append(
                _sts_frame(
                    t, 90 + frac * 85, hip_y=0.0 - frac * 0.5, occluded_ankle_vis=0.3
                )
            )
            t += 33
        for _ in range(15):  # hold standing
            frames.append(_sts_frame(t, 175, hip_y=-0.5, occluded_ankle_vis=0.3))
            t += 33
        for i in range(30):  # sit back down
            frac = i / 29
            frames.append(
                _sts_frame(
                    t, 175 - frac * 85, hip_y=-0.5 + frac * 0.5, occluded_ankle_vis=0.3
                )
            )
            t += 33

        result = run_sts(frames)

        self.assertEqual(result["metrics"]["tracked_leg"], "left")
        self.assertEqual(result["metrics"]["rep_count"], 1)
        self.assertNotEqual(result["quality"]["quality_band"], "poor")


if __name__ == "__main__":
    unittest.main()
