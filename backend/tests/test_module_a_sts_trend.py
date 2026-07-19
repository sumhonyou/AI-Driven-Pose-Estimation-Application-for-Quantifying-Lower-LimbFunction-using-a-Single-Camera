"""Stage 7.2: STS "vs last session" trend -- no MDC, deltas reported plainly."""

import unittest

from app.module_a.sts import trend


class StsTrendTests(unittest.TestCase):
    def test_no_previous_session_is_none(self):
        current = {"score": 7.5, "band": "Good", "completion_time_sec": 12.0}
        self.assertIsNone(trend.compute_trend(current, None))

    def test_computes_score_and_time_deltas(self):
        current = {"score": 7.5, "band": "Good", "completion_time_sec": 10.0}
        previous = {"score": 6.0, "band": "Fair", "completion_time_sec": 12.5}
        result = trend.compute_trend(current, previous)
        self.assertEqual(result["score_delta"], 1.5)
        self.assertEqual(result["completion_time_delta_sec"], -2.5)
        self.assertEqual(result["previous_band"], "Fair")

    def test_no_meaningful_flag_is_ever_present(self):
        # Explicit guard against inventing an MDC claim for STS (task.md Stage 7.2).
        current = {"score": 7.5, "band": "Good", "completion_time_sec": 10.0}
        previous = {"score": 7.4, "band": "Good", "completion_time_sec": 10.1}
        result = trend.compute_trend(current, previous)
        self.assertNotIn("score_meaningful", result)
        self.assertNotIn("completion_time_meaningful", result)
        self.assertNotIn("meaningful", result)

    def test_missing_score_in_either_session_yields_no_score_delta(self):
        current = {"score": None, "band": None, "completion_time_sec": 10.0}
        previous = {"score": 6.0, "band": "Fair", "completion_time_sec": 12.0}
        result = trend.compute_trend(current, previous)
        self.assertIsNone(result["score_delta"])
        self.assertEqual(result["completion_time_delta_sec"], -2.0)

    def test_both_deltas_unavailable_yields_none(self):
        current = {"score": None, "band": None, "completion_time_sec": None}
        previous = {"score": None, "band": "Fair", "completion_time_sec": None}
        self.assertIsNone(trend.compute_trend(current, previous))


if __name__ == "__main__":
    unittest.main()
