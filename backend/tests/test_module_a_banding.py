import unittest

from app.module_a.core import banding


def _metrics(
    rep_count,
    target=5,
    completion_time_sec=10.0,
    wobble_count=0,
    avg_trunk_lean_deg=15.0,
):
    return {
        "rep_count": rep_count,
        "target_rep_count": target,
        "completion_time_sec": completion_time_sec,
        "wobble_count": wobble_count,
        "avg_trunk_lean_deg": avg_trunk_lean_deg,
    }


def _quality(quality_band):
    return {"quality_band": quality_band}


class ModuleABandingTests(unittest.TestCase):
    def test_complete_clean_session_is_good_and_complete(self):
        result = banding.compute_band(_metrics(rep_count=5), _quality("good"))

        self.assertEqual(result["session_status"], "complete")
        self.assertEqual(result["band"], "good")
        self.assertEqual(result["score"], 10.0)
        self.assertFalse(result["is_partial_score"])

    def test_incomplete_but_clean_reps_are_not_force_capped(self):
        result = banding.compute_band(
            _metrics(rep_count=3, completion_time_sec=None), _quality("good")
        )

        self.assertEqual(result["session_status"], "incomplete")
        self.assertTrue(result["is_partial_score"])
        self.assertEqual(result["band"], "good")
        self.assertEqual(result["score"], 10.0)
        self.assertIn("incomplete_reps", result["warning_tags"])

    def test_zero_reps_has_no_data_to_grade(self):
        result = banding.compute_band(
            _metrics(rep_count=0, completion_time_sec=None), _quality("good")
        )

        self.assertEqual(result["session_status"], "incomplete")
        self.assertEqual(result["band"], "invalid")
        self.assertEqual(result["score"], 0.0)
        self.assertFalse(result["is_partial_score"])

    def test_poor_capture_quality_is_low_confidence_not_forced_poor(self):
        result = banding.compute_band(_metrics(rep_count=5), _quality("poor"))

        self.assertEqual(result["session_status"], "low_confidence")
        # Movement quality is still computed, not suppressed or zeroed just
        # because tracking was unreliable -- session_status carries that signal.
        self.assertEqual(result["score"], 10.0)
        self.assertEqual(result["band"], "good")
        self.assertIn("poor_capture_quality", result["warning_tags"])

    def test_degraded_form_with_good_tracking_is_a_real_band_not_incomplete(self):
        """A genuinely worse movement-quality result (slow, wobbly, leaning) must
        still be reported as `session_status="complete"` -- the deductions should
        lower `band`, never get relabeled as incomplete/low-confidence just
        because the score happened to drop."""
        clean = banding.compute_band(_metrics(rep_count=5), _quality("good"))
        degraded = banding.compute_band(
            _metrics(
                rep_count=5,
                wobble_count=3,
                avg_trunk_lean_deg=40.0,
                completion_time_sec=25.0,
            ),
            _quality("good"),
        )

        self.assertLess(degraded["score"], clean["score"])
        self.assertEqual(degraded["session_status"], "complete")
        self.assertFalse(degraded["is_partial_score"])


# WBLT no longer runs through this shared dispatcher -- it has its own dedicated
# router/analysis/banding (app/module_a/wblt/*), tested in test_module_a_wblt.py.
# compute_band() now only ever raises for exercise_type="weight_bearing_lunge_test".
class ModuleABandingUnknownExerciseTests(unittest.TestCase):
    def test_wblt_exercise_type_is_no_longer_accepted_here(self):
        with self.assertRaises(ValueError):
            banding.compute_band(
                _metrics(rep_count=3),
                _quality("good"),
                exercise_type="weight_bearing_lunge_test",
            )


if __name__ == "__main__":
    unittest.main()
