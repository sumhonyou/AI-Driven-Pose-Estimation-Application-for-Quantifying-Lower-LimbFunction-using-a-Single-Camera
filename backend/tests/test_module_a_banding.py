import unittest

from app.module_a import banding


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


# Single-Leg Stance (SLS) banding tests
def _sls_metrics(
    hold_duration_sec=25.0,
    target_hold_sec=30.0,
    max_sway_m=0.1,
):
    return {
        "rep_count": 1 if hold_duration_sec > 0 else 0,
        "target_rep_count": 1,
        "hold_duration_sec": hold_duration_sec,
        "target_hold_sec": target_hold_sec,
        "max_sway_m": max_sway_m,
        "session_duration_sec": hold_duration_sec,
        "stopped_early": False,
    }


# Weight-Bearing Lunge Test (WBLT) banding tests
def _wblt_metrics(
    trial_count=3,
    target_trials=3,
    avg_dorsiflexion_deg=18.0,
    avg_symmetry_diff_deg=6.0,
):
    return {
        "rep_count": trial_count,
        "target_rep_count": target_trials,
        "trial_count": trial_count,
        "target_trials": target_trials,
        "avg_dorsiflexion_deg": avg_dorsiflexion_deg,
        "max_dorsiflexion_deg": avg_dorsiflexion_deg + 2,
        "avg_symmetry_diff_deg": avg_symmetry_diff_deg,
        "session_duration_sec": 30.0,
        "stopped_early": False,
    }


class ModuleASlsBandingTests(unittest.TestCase):
    def test_sls_good_hold_is_complete_and_good(self):
        """30-second hold with good tracking and minimal sway is a good, complete result."""
        result = banding.compute_band(
            _sls_metrics(hold_duration_sec=30.0),
            _quality("good"),
            exercise_type="supported_single_leg_stance",
        )

        self.assertEqual(result["session_status"], "complete")
        self.assertEqual(result["band"], "good")
        self.assertFalse(result["is_partial_score"])
        self.assertEqual(result["hold_band"], "good")

    def test_sls_fair_hold_is_incomplete_fair(self):
        """15-second hold (fair duration) with good tracking is fair, incomplete."""
        result = banding.compute_band(
            _sls_metrics(hold_duration_sec=15.0),
            _quality("good"),
            exercise_type="supported_single_leg_stance",
        )

        self.assertEqual(result["session_status"], "incomplete")
        self.assertEqual(result["band"], "fair")
        self.assertTrue(result["is_partial_score"])
        self.assertEqual(result["hold_band"], "fair")

    def test_sls_poor_hold_is_incomplete_poor(self):
        """5-second hold (poor duration) with good tracking is poor, incomplete."""
        result = banding.compute_band(
            _sls_metrics(hold_duration_sec=5.0),
            _quality("good"),
            exercise_type="supported_single_leg_stance",
        )

        self.assertEqual(result["session_status"], "incomplete")
        self.assertEqual(result["band"], "poor")
        self.assertTrue(result["is_partial_score"])
        self.assertEqual(result["hold_band"], "poor")

    def test_sls_zero_hold_is_invalid(self):
        """No hold detected (0 seconds) is invalid with no score."""
        result = banding.compute_band(
            _sls_metrics(hold_duration_sec=0.0),
            _quality("good"),
            exercise_type="supported_single_leg_stance",
        )

        self.assertEqual(result["session_status"], "incomplete")
        self.assertEqual(result["band"], "invalid")
        self.assertEqual(result["score"], 0.0)
        self.assertFalse(result["is_partial_score"])

    def test_sls_good_hold_poor_quality_is_low_confidence(self):
        """30-second hold with poor tracking is marked low_confidence, not complete."""
        result = banding.compute_band(
            _sls_metrics(hold_duration_sec=30.0),
            _quality("poor"),
            exercise_type="supported_single_leg_stance",
        )

        self.assertEqual(result["session_status"], "low_confidence")
        self.assertIn("poor_capture_quality", result["warning_tags"])

    def test_sls_excessive_sway_deduction(self):
        """High sway (>0.15m) applies a deduction."""
        good_sway = banding.compute_band(
            _sls_metrics(hold_duration_sec=30.0, max_sway_m=0.1),
            _quality("good"),
            exercise_type="supported_single_leg_stance",
        )
        bad_sway = banding.compute_band(
            _sls_metrics(hold_duration_sec=30.0, max_sway_m=0.20),
            _quality("good"),
            exercise_type="supported_single_leg_stance",
        )

        self.assertLess(bad_sway["score"], good_sway["score"])
        self.assertIn("excessive_sway", bad_sway["warning_tags"])


class ModuleAWbltBandingTests(unittest.TestCase):
    def test_wblt_good_rom_good_symmetry_is_complete_good(self):
        """Good ROM (18°) with good symmetry (6°) is a good, complete result."""
        result = banding.compute_band(
            _wblt_metrics(avg_dorsiflexion_deg=18.0, avg_symmetry_diff_deg=6.0),
            _quality("good"),
            exercise_type="weight_bearing_lunge_test",
        )

        self.assertEqual(result["session_status"], "complete")
        self.assertEqual(result["band"], "good")
        self.assertFalse(result["is_partial_score"])
        self.assertEqual(result["rom_band"], "good")
        self.assertEqual(result["symmetry_band"], "good")

    def test_wblt_fair_rom_with_poor_symmetry_is_fair(self):
        """Fair ROM (12°) with poor symmetry (15°) is fair, complete."""
        result = banding.compute_band(
            _wblt_metrics(avg_dorsiflexion_deg=12.0, avg_symmetry_diff_deg=15.0),
            _quality("good"),
            exercise_type="weight_bearing_lunge_test",
        )

        self.assertEqual(result["session_status"], "complete")
        self.assertEqual(result["band"], "fair")
        self.assertFalse(result["is_partial_score"])
        self.assertIn("poor_ankle_symmetry", result["warning_tags"])

    def test_wblt_poor_rom_is_poor(self):
        """Poor ROM (<10°) is poor, complete."""
        result = banding.compute_band(
            _wblt_metrics(avg_dorsiflexion_deg=7.0, avg_symmetry_diff_deg=3.0),
            _quality("good"),
            exercise_type="weight_bearing_lunge_test",
        )

        self.assertEqual(result["session_status"], "complete")
        self.assertEqual(result["band"], "poor")
        self.assertFalse(result["is_partial_score"])
        self.assertIn("limited_ankle_dorsiflexion", result["warning_tags"])

    def test_wblt_incomplete_trials(self):
        """Fewer than 3 trials is incomplete."""
        result = banding.compute_band(
            _wblt_metrics(trial_count=2, target_trials=3),
            _quality("good"),
            exercise_type="weight_bearing_lunge_test",
        )

        self.assertEqual(result["session_status"], "incomplete")
        self.assertTrue(result["is_partial_score"])
        self.assertIn("incomplete_trials", result["warning_tags"])

    def test_wblt_zero_trials_is_invalid(self):
        """No trials detected is invalid."""
        result = banding.compute_band(
            _wblt_metrics(trial_count=0),
            _quality("good"),
            exercise_type="weight_bearing_lunge_test",
        )

        self.assertEqual(result["band"], "invalid")
        self.assertEqual(result["score"], 0.0)


if __name__ == "__main__":
    unittest.main()
