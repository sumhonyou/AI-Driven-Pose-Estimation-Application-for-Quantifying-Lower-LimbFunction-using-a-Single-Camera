import unittest

from app.module_a.quality import average_visibility
from app.module_a.session_engine import SessionEngine


class ModuleAQualityTests(unittest.TestCase):
    def test_average_visibility_counts_missing_required_landmarks_as_zero(self):
        landmarks = [{"visibility": 1.0} for _ in range(24)]

        self.assertEqual(average_visibility(landmarks), 3 / 8)

    def test_session_engine_handles_short_landmark_frames(self):
        frames = [
            {
                "timestampMs": 0,
                "worldLandmarks": [{"visibility": 1.0} for _ in range(10)],
            }
        ]

        result = SessionEngine().run(frames)

        self.assertEqual(result["metrics"]["rep_count"], 0)
        self.assertEqual(result["quality"]["valid_frame_ratio"], 0.0)
        self.assertEqual(result["quality"]["quality_band"], "poor")


if __name__ == "__main__":
    unittest.main()
