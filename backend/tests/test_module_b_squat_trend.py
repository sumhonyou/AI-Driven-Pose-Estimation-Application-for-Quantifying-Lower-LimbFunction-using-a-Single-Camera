"""Stage 7.4: squat "vs last session" trend -- no MDC, deltas reported plainly."""

import unittest

from app.module_b.squat import trend


class SquatTrendTests(unittest.TestCase):
    def test_no_previous_session_is_none(self):
        current = {"score": 7.5, "band": "Good", "rep_count": 8}
        self.assertIsNone(trend.compute_trend(current, None))

    def test_computes_score_and_rep_deltas(self):
        current = {"score": 7.5, "band": "Good", "rep_count": 10}
        previous = {"score": 6.0, "band": "Poor", "rep_count": 8}
        result = trend.compute_trend(current, previous)
        self.assertEqual(result["score_delta"], 1.5)
        self.assertEqual(result["rep_count_delta"], 2)
        self.assertEqual(result["previous_band"], "Poor")

    def test_no_meaningful_flag_is_ever_present(self):
        # Explicit guard against inventing an MDC claim for squat (task.md Stage 7.2/7.4).
        current = {"score": 7.5, "band": "Good", "rep_count": 8}
        previous = {"score": 7.4, "band": "Good", "rep_count": 8}
        result = trend.compute_trend(current, previous)
        self.assertNotIn("score_meaningful", result)
        self.assertNotIn("rep_count_meaningful", result)
        self.assertNotIn("meaningful", result)

    def test_missing_score_in_either_session_yields_no_score_delta(self):
        current = {"score": None, "band": None, "rep_count": 10}
        previous = {"score": 6.0, "band": "Poor", "rep_count": 8}
        result = trend.compute_trend(current, previous)
        self.assertIsNone(result["score_delta"])
        self.assertEqual(result["rep_count_delta"], 2)

    def test_both_deltas_unavailable_yields_none(self):
        current = {"score": None, "band": None, "rep_count": None}
        previous = {"score": None, "band": "Poor", "rep_count": None}
        self.assertIsNone(trend.compute_trend(current, previous))


if __name__ == "__main__":
    unittest.main()
