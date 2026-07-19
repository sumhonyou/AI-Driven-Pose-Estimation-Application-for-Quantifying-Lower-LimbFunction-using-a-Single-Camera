"""Stage 7.2: SLS per-leg "vs last session" trend -- no MDC, deltas reported plainly."""

import unittest

from app.module_a.sls import trend


class SlsTrendTests(unittest.TestCase):
    def test_no_previous_session_is_none_per_leg(self):
        current = {"right": {"holdSeconds": 30.0, "combinedScore": 7.0, "band": "Good"}}
        result = trend.compute_trend(current, None)
        self.assertIsNone(result["right"])
        self.assertIsNone(result["left"])

    def test_computes_hold_and_score_deltas(self):
        current = {
            "right": {"holdSeconds": 30.0, "combinedScore": 7.0, "band": "Good"},
        }
        previous = {
            "right": {"holdSeconds": 22.0, "combinedScore": 5.5, "band": "Fair"},
        }
        result = trend.compute_trend(current, previous)
        right = result["right"]
        self.assertEqual(right["hold_delta_sec"], 8.0)
        self.assertEqual(right["score_delta"], 1.5)
        self.assertEqual(right["previous_band"], "Fair")

    def test_no_meaningful_flag_is_ever_present(self):
        current = {"right": {"holdSeconds": 30.0, "combinedScore": 7.0, "band": "Good"}}
        previous = {
            "right": {"holdSeconds": 29.5, "combinedScore": 6.9, "band": "Good"}
        }
        result = trend.compute_trend(current, previous)
        self.assertNotIn("hold_meaningful", result["right"])
        self.assertNotIn("score_meaningful", result["right"])
        self.assertNotIn("meaningful", result["right"])

    def test_leg_missing_from_either_session_is_none(self):
        current = {"right": {"holdSeconds": 30.0, "combinedScore": 7.0, "band": "Good"}}
        previous = {
            "right": {"holdSeconds": 22.0, "combinedScore": 5.5, "band": "Fair"}
        }
        result = trend.compute_trend(current, previous)
        self.assertIsNone(result["left"])

    def test_legs_are_independent(self):
        current = {
            "right": {"holdSeconds": 30.0, "combinedScore": 7.0, "band": "Good"},
            "left": {"holdSeconds": 18.0, "combinedScore": 4.0, "band": "Poor"},
        }
        previous = {
            "right": {"holdSeconds": 22.0, "combinedScore": 5.5, "band": "Fair"},
        }
        result = trend.compute_trend(current, previous)
        self.assertIsNotNone(result["right"])
        self.assertIsNone(result["left"])  # no previous data for left


if __name__ == "__main__":
    unittest.main()
