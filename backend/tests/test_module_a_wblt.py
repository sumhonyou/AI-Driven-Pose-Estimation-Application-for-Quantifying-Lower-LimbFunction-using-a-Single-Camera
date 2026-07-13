import unittest

from app.module_a.wblt import analysis, config, geometry
from app.module_a.wblt.age_band import age_to_band, resolve_ageband_sex

RIGHT_KNEE, RIGHT_ANKLE, RIGHT_HEEL, RIGHT_FOOT_INDEX = 26, 28, 30, 32
LEFT_KNEE, LEFT_ANKLE, LEFT_HEEL, LEFT_FOOT_INDEX = 25, 27, 29, 31
HIP_LEFT, HIP_RIGHT = 23, 24

_LEG_INDICES = {
    "right": (RIGHT_KNEE, RIGHT_ANKLE, RIGHT_HEEL, RIGHT_FOOT_INDEX),
    "left": (LEFT_KNEE, LEFT_ANKLE, LEFT_HEEL, LEFT_FOOT_INDEX),
}


def _landmark(x, y, z=0.0, visibility=1.0):
    return {"x": x, "y": y, "z": z, "visibility": visibility}


def _frame(t_ms, leg, knee, ankle, heel, foot_index, hip_x_sep=0.0):
    knee_idx, ankle_idx, heel_idx, foot_idx = _LEG_INDICES[leg]
    world = [_landmark(0.0, 0.0) for _ in range(33)]
    world[knee_idx] = knee
    world[ankle_idx] = ankle
    world[heel_idx] = heel
    world[foot_idx] = foot_index
    # hip_x_sep=0 -> hips overlap in x, as seen from a true side-on camera.
    # A larger value simulates a more frontal camera (§8 lateral_alignment).
    world[HIP_LEFT] = _landmark(-hip_x_sep / 2, 0.3)
    world[HIP_RIGHT] = _landmark(hip_x_sep / 2, 0.3)
    return {"timestampMs": t_ms, "worldLandmarks": world}


def _build_frames(
    knee_xy_offset, heel_rise, leg="right", n_calibration=30, n_hold=15, hip_x_sep=0.0
):
    """Builds a calibration window (foot flat) followed by a hold window.

    `knee_xy_offset` shifts the knee forward (x) relative to the ankle during
    the hold, simulating more/less dorsiflexion. `heel_rise` shifts the heel
    up (smaller y, since y increases downward) during the hold, simulating a
    heel lift. `hip_x_sep` simulates camera lateral alignment (0 = side-on).
    """
    ankle = _landmark(0.0, 0.5)
    heel_flat = _landmark(0.0, 0.5)
    foot_index = _landmark(0.15, 0.5)  # forward of the heel -> defines "forward"
    knee_flat = _landmark(0.0, 0.0)  # directly above the ankle -> ~vertical shank

    frames = []
    t = 0.0
    # Pack the calibration frames into the first ~0.8s of the calibration window
    # (which is config.CALIBRATION_SECONDS long) so they all land inside it.
    step_ms = 800.0 / n_calibration
    for _ in range(n_calibration):
        frames.append(
            _frame(t, leg, knee_flat, ankle, heel_flat, foot_index, hip_x_sep)
        )
        t += step_ms

    # Hold starts just after the calibration window closes.
    t = config.CALIBRATION_SECONDS * 1000.0 + 200.0
    knee_hold = _landmark(knee_xy_offset, 0.0)
    heel_hold = _landmark(0.0, 0.5 - heel_rise)
    for _ in range(n_hold):
        frames.append(
            _frame(t, leg, knee_hold, ankle, heel_hold, foot_index, hip_x_sep)
        )
        t += 33.0

    return frames


class WbltAnalysisTests(unittest.TestCase):
    def test_vertical_shank_gives_near_zero_angle(self):
        frames = _build_frames(knee_xy_offset=0.0, heel_rise=0.0)
        result = analysis.analyze_attempt(
            frames,
            "right",
            target_distance_cm=10.0,
            touched=True,
            exact_age=30,
            gender="male",
        )

        self.assertTrue(result["attempt_valid"])
        self.assertFalse(result["heel_lift_detected"])
        self.assertLess(result["theta_peak_deg"], 5.0)
        self.assertIsNone(
            result["q_limiting_factor"]
        )  # good side-on view, Q not tripped

    def test_forward_lean_gives_larger_angle(self):
        frames = _build_frames(knee_xy_offset=0.3, heel_rise=0.0)
        result = analysis.analyze_attempt(
            frames,
            "right",
            target_distance_cm=10.0,
            touched=True,
            exact_age=30,
            gender="male",
        )

        self.assertTrue(result["attempt_valid"])
        self.assertGreater(result["theta_peak_deg"], 15.0)

    def test_raised_heel_invalidates_the_attempt(self):
        # Rise well beyond heel_lift_tol_ratio * shank_len for the whole hold.
        shank_len = 0.5
        rise = config.WBLT_CONFIG["heel_lift_tol_ratio"] * shank_len * 3
        frames = _build_frames(knee_xy_offset=0.0, heel_rise=rise)
        result = analysis.analyze_attempt(
            frames,
            "right",
            target_distance_cm=10.0,
            touched=True,
            exact_age=30,
            gender="male",
        )

        self.assertTrue(result["heel_lift_detected"])
        self.assertFalse(result["attempt_valid"])
        self.assertIsNone(result["theta_peak_deg"])

    def test_touched_but_heel_lifted_overrides_self_report(self):
        shank_len = 0.5
        rise = config.WBLT_CONFIG["heel_lift_tol_ratio"] * shank_len * 3
        frames = _build_frames(knee_xy_offset=0.0, heel_rise=rise)
        result = analysis.analyze_attempt(
            frames,
            "right",
            target_distance_cm=10.0,
            touched=True,
            exact_age=30,
            gender="male",
        )

        self.assertFalse(result["valid_touch"])
        self.assertIn("heel_lifted_at_touch_override", result["warning_tags"])

    def test_valid_touch_resolves_a_distance_band(self):
        frames = _build_frames(knee_xy_offset=0.0, heel_rise=0.0)
        result = analysis.analyze_attempt(
            frames,
            "right",
            target_distance_cm=12.0,
            touched=True,
            exact_age=35,
            gender="male",
        )

        self.assertTrue(result["valid_touch"])
        self.assertEqual(result["band"], "Good")  # 30-39_male good_min_cm = 8.8
        self.assertIsNotNone(result["score_0_10"])

    def test_missing_profile_blocks_band_but_keeps_angle(self):
        frames = _build_frames(knee_xy_offset=0.0, heel_rise=0.0)
        result = analysis.analyze_attempt(
            frames,
            "right",
            target_distance_cm=12.0,
            touched=True,
            exact_age=None,
            gender=None,
        )

        self.assertTrue(result["valid_touch"])
        self.assertIsNone(result["band"])
        self.assertIsNotNone(result["theta_peak_deg"])
        self.assertIn("profile_incomplete_no_band", result["warning_tags"])

    def test_not_touched_is_incomplete_not_banded(self):
        frames = _build_frames(knee_xy_offset=0.0, heel_rise=0.0)
        result = analysis.analyze_attempt(
            frames,
            "right",
            target_distance_cm=12.0,
            touched=False,
            exact_age=30,
            gender="male",
        )

        self.assertFalse(result["valid_touch"])
        self.assertIsNone(result["band"])
        self.assertEqual(result["session_status"], "incomplete")

    def test_left_leg_geometry_mirrors_right(self):
        """§7 gate: left-leg indices (25,27,29,31) + mirrored plane construction."""
        frames = _build_frames(knee_xy_offset=0.3, heel_rise=0.0, leg="left")
        result = analysis.analyze_attempt(
            frames,
            "left",
            target_distance_cm=10.0,
            touched=True,
            exact_age=30,
            gender="male",
        )

        self.assertTrue(result["attempt_valid"])
        self.assertFalse(result["heel_lift_detected"])
        self.assertGreater(result["theta_peak_deg"], 15.0)

    def test_too_few_calibration_frames_is_a_no_cost_retry(self):
        """Fewer than heel_min_calibration_frames foot-flat frames -> can't trust a
        baseline; surfaced as a low-Q-style retry, not a bracket-stepping attempt."""
        frames = _build_frames(
            knee_xy_offset=0.0,
            heel_rise=0.0,
            n_calibration=config.WBLT_CONFIG["heel_min_calibration_frames"] - 1,
        )
        result = analysis.analyze_attempt(
            frames,
            "right",
            target_distance_cm=10.0,
            touched=True,
            exact_age=30,
            gender="male",
        )

        self.assertFalse(result["attempt_valid"])
        self.assertIsNone(result["theta_peak_deg"])
        self.assertIsNotNone(result["q_limiting_factor"])
        self.assertIn("calibration_failed", result["warning_tags"])


def _detector_world(heel_y):
    """A minimal world-landmark list for HeelLiftDetector: knee above ankle
    (shank_len 0.5), heel at the given y. Only the right-leg indices matter."""
    world = [_landmark(0.0, 0.0) for _ in range(33)]
    world[RIGHT_KNEE] = _landmark(0.0, 0.0)
    world[RIGHT_ANKLE] = _landmark(0.0, 0.5)
    world[RIGHT_HEEL] = _landmark(0.0, heel_y)
    world[RIGHT_FOOT_INDEX] = _landmark(0.15, 0.5)
    return world


class HeelLiftDetectorTests(unittest.TestCase):
    def _calibrated_detector(self, debounce=3):
        det = geometry.HeelLiftDetector(
            lift_tol_ratio=0.10,
            hysteresis_ratio=0.06,
            leg="right",
            min_calibration_frames=5,
            lift_debounce_frames=debounce,
        )
        for _ in range(10):
            det.feed_calibration(_detector_world(0.5))  # foot-flat baseline
        self.assertTrue(det.finalize())
        return det

    def test_too_few_frames_never_calibrates(self):
        det = geometry.HeelLiftDetector(
            lift_tol_ratio=0.10,
            hysteresis_ratio=0.06,
            leg="right",
            min_calibration_frames=5,
        )
        for _ in range(4):  # one short of the floor
            det.feed_calibration(_detector_world(0.5))
        self.assertFalse(det.finalize())
        self.assertFalse(det.calibrated)

    def test_single_raised_frame_does_not_latch(self):
        det = self._calibrated_detector(debounce=3)
        det.update(_detector_world(0.2))  # clearly raised, but only one frame
        self.assertFalse(det.lifted)
        det.update(_detector_world(0.5))  # back down -> streak resets
        det.update(_detector_world(0.5))
        self.assertFalse(det.lifted)

    def test_sustained_raise_latches_after_debounce(self):
        det = self._calibrated_detector(debounce=3)
        for _ in range(3):
            det.update(_detector_world(0.2))
        self.assertTrue(det.lifted)


def _attempt(
    target_distance_cm,
    valid_touch,
    theta_peak_deg=20.0,
    band=None,
    score=None,
    borderline=False,
):
    return {
        "target_distance_cm": target_distance_cm,
        "valid_touch": valid_touch,
        "theta_peak_deg": theta_peak_deg,
        "band": band,
        "score_0_10": score,
        "borderline": borderline,
        "warning_tags": [],
        "quality": {
            "average_visibility": 0.9,
            "valid_frame_ratio": 0.9,
            "quality_band": "good",
        },
    }


class WbltBracketStateTests(unittest.TestCase):
    def test_first_attempt_uses_seed(self):
        state = analysis.bracket_state([], seed_cm=11.2)
        self.assertEqual(state["attempt_number"], 1)
        self.assertEqual(state["next_target_distance_cm"], 11.2)
        self.assertFalse(state["leg_complete"])

    def test_first_attempt_falls_back_when_seed_unresolvable(self):
        state = analysis.bracket_state([], seed_cm=None)
        self.assertEqual(
            state["next_target_distance_cm"],
            config.WBLT_CONFIG["fallback_seed_distance_cm"],
        )

    def test_steps_out_on_valid_touch(self):
        state = analysis.bracket_state([_attempt(10.0, True)], seed_cm=None)
        self.assertEqual(state["attempt_number"], 2)
        self.assertEqual(state["next_target_distance_cm"], 12.0)
        self.assertFalse(state["leg_complete"])

    def test_steps_in_on_fail(self):
        state = analysis.bracket_state([_attempt(10.0, False)], seed_cm=None)
        self.assertEqual(state["next_target_distance_cm"], 8.0)

    def test_floor_respected_on_repeated_fails(self):
        attempts = [_attempt(2.5, False)]
        state = analysis.bracket_state(attempts, seed_cm=None)
        self.assertEqual(
            state["next_target_distance_cm"],
            config.WBLT_CONFIG["bracket_min_distance_cm"],
        )

    def test_completes_after_attempts_per_leg_with_a_fail(self):
        attempts = [_attempt(10.0, True), _attempt(12.0, True), _attempt(11.0, False)]
        state = analysis.bracket_state(attempts, seed_cm=None)
        self.assertTrue(state["leg_complete"])
        self.assertIsNone(state["next_target_distance_cm"])
        self.assertEqual(state["attempt_number"], 3)

    def test_offers_one_extra_attempt_when_all_base_attempts_valid(self):
        attempts = [_attempt(10.0, True), _attempt(12.0, True), _attempt(14.0, True)]
        state = analysis.bracket_state(attempts, seed_cm=None)
        self.assertFalse(state["leg_complete"])
        self.assertEqual(state["attempt_number"], 4)
        self.assertEqual(state["next_target_distance_cm"], 16.0)

    def test_completes_after_the_extra_attempt_regardless_of_outcome(self):
        attempts = [
            _attempt(10.0, True),
            _attempt(12.0, True),
            _attempt(14.0, True),
            _attempt(16.0, False),  # the bonus attempt failed
        ]
        state = analysis.bracket_state(attempts, seed_cm=None)
        self.assertTrue(state["leg_complete"])


class WbltSummarizeLegTests(unittest.TestCase):
    def test_picks_largest_valid_touch_distance(self):
        attempts = [
            _attempt(8.0, True, band="Fair", score=5.0),
            _attempt(10.0, True, band="Good", score=8.0),
            _attempt(6.0, False),
        ]
        summary = analysis.summarize_leg(attempts)
        self.assertEqual(summary["best_distance_cm"], 10.0)
        self.assertEqual(summary["band"], "Good")
        self.assertFalse(summary["floor_flag"])

    def test_attempt_number_offers_bonus_after_three_valid_touches(self):
        # analyze success must expose next slot (4), not completed count (3)
        attempts = [_attempt(10.0, True), _attempt(12.0, True), _attempt(14.0, True)]
        summary = analysis.summarize_leg(attempts)
        self.assertEqual(summary["attempt_number"], 4)
        self.assertEqual(summary["next_target_distance_cm"], 16.0)
        self.assertFalse(summary["leg_complete"])

    def test_attempt_number_stays_completed_when_no_bonus(self):
        attempts = [_attempt(10.0, True), _attempt(12.0, True), _attempt(11.0, False)]
        summary = analysis.summarize_leg(attempts)
        self.assertEqual(summary["attempt_number"], 3)
        self.assertIsNone(summary["next_target_distance_cm"])
        self.assertTrue(summary["leg_complete"])

    def test_floor_flag_when_every_attempt_fails(self):
        attempts = [_attempt(10.0, False), _attempt(8.0, False), _attempt(6.0, False)]
        summary = analysis.summarize_leg(attempts)
        self.assertIsNone(summary["best_distance_cm"])
        self.assertTrue(summary["floor_flag"])

    def test_leg_angle_uses_any_heel_valid_attempt_not_only_touches(self):
        attempts = [
            _attempt(10.0, False, theta_peak_deg=22.0),  # heel-valid but not touched
            _attempt(8.0, True, theta_peak_deg=15.0, band="Fair", score=5.0),
        ]
        summary = analysis.summarize_leg(attempts)
        self.assertEqual(summary["leg_angle_deg"], 22.0)


class WbltSymmetryTests(unittest.TestCase):
    def test_symmetric_when_angles_are_close(self):
        legs = {
            "right": {"leg_angle_deg": 20.0},
            "left": {"leg_angle_deg": 21.0},
        }
        result = analysis.compute_symmetry(legs)
        self.assertEqual(result["status"], "symmetric")

    def test_asymmetry_flag_when_angles_diverge(self):
        legs = {
            "right": {"leg_angle_deg": 30.0},
            "left": {"leg_angle_deg": 15.0},
        }
        result = analysis.compute_symmetry(legs)
        self.assertEqual(result["status"], "asymmetry_flag")

    def test_none_when_only_one_leg_present(self):
        legs = {"right": {"leg_angle_deg": 20.0}}
        result = analysis.compute_symmetry(legs)
        self.assertIsNone(result["status"])
        self.assertIsNone(result["asym_deg"])


class WbltSessionSummaryTests(unittest.TestCase):
    def test_both_legs_complete_computes_overall_band(self):
        legs = {
            "right": {"leg_complete": True, "score_0_10": 8.0},
            "left": {"leg_complete": True, "score_0_10": 6.0},
        }
        summary = analysis.compute_session_summary(legs)
        self.assertTrue(summary["both_legs_done"])
        self.assertEqual(summary["overall_score"], 7.0)
        self.assertEqual(summary["session_status"], "complete")

    def test_one_leg_incomplete_is_session_incomplete(self):
        legs = {
            "right": {"leg_complete": True, "score_0_10": 8.0},
            "left": {"leg_complete": False, "score_0_10": None},
        }
        summary = analysis.compute_session_summary(legs)
        self.assertFalse(summary["both_legs_done"])
        self.assertEqual(summary["session_status"], "incomplete")

    def test_both_legs_floor_flagged_is_low_confidence_not_a_fake_band(self):
        legs = {
            "right": {"leg_complete": True, "score_0_10": None},
            "left": {"leg_complete": True, "score_0_10": None},
        }
        summary = analysis.compute_session_summary(legs)
        self.assertTrue(summary["both_legs_done"])
        self.assertIsNone(summary["overall_band"])
        self.assertEqual(summary["session_status"], "low_confidence")


class WbltCaptureQualityTests(unittest.TestCase):
    """§8: Q = min(lateral_alignment, leg_visibility, landmark_conf)."""

    def test_frontal_camera_blocks_band_and_flags_retry(self):
        # hip_x_sep=0.3 against shank_len=0.5 -> hip_x_norm=0.6, well past the
        # 0.45 "definitely frontal" cutoff -> lateral_alignment clamps to 0.
        frames = _build_frames(knee_xy_offset=0.0, heel_rise=0.0, hip_x_sep=0.3)
        result = analysis.analyze_attempt(
            frames,
            "right",
            target_distance_cm=10.0,
            touched=True,
            exact_age=30,
            gender="male",
        )

        self.assertEqual(result["q_limiting_factor"], "lateral_alignment")
        self.assertLess(result["q"], config.WBLT_CONFIG["q_min"])
        self.assertEqual(result["session_status"], "low_confidence")
        self.assertIsNone(result["band"])
        self.assertIsNone(result["distance_cm"])
        self.assertIn("poor_capture_quality", result["warning_tags"])
        self.assertIn("retry_lateral_alignment", result["warning_tags"])

    def test_side_on_camera_never_trips_lateral_alignment(self):
        frames = _build_frames(knee_xy_offset=0.0, heel_rise=0.0, hip_x_sep=0.0)
        result = analysis.analyze_attempt(
            frames,
            "right",
            target_distance_cm=10.0,
            touched=True,
            exact_age=30,
            gender="male",
        )

        self.assertAlmostEqual(result["quality"]["lateral_alignment"], 1.0, places=2)
        self.assertIsNone(result["q_limiting_factor"])

    def test_moderately_off_angle_degrades_but_may_not_block(self):
        # hip_x_norm = 0.15/0.5 = 0.3, below the 0.45 cutoff -> some penalty,
        # not a full zero -- lateral_alignment should sit strictly between 0 and 1.
        frames = _build_frames(knee_xy_offset=0.0, heel_rise=0.0, hip_x_sep=0.15)
        result = analysis.analyze_attempt(
            frames,
            "right",
            target_distance_cm=10.0,
            touched=True,
            exact_age=30,
            gender="male",
        )

        self.assertGreater(result["quality"]["lateral_alignment"], 0.0)
        self.assertLess(result["quality"]["lateral_alignment"], 1.0)


class WbltProfileSnapshotTests(unittest.TestCase):
    """§9: the persisted audit trail must record what the band was ACTUALLY
    computed from, not just re-derivable-later state."""

    def test_full_profile_resolves_age_band_and_sex(self):
        snapshot = analysis.resolve_profile_snapshot(43, "female")
        self.assertEqual(
            snapshot, {"exact_age": 43, "age_band_resolved": "40-49", "sex": "female"}
        )

    def test_missing_age_leaves_age_band_unresolved(self):
        snapshot = analysis.resolve_profile_snapshot(None, "male")
        self.assertIsNone(snapshot["age_band_resolved"])
        self.assertIsNone(snapshot["exact_age"])

    def test_prefer_not_to_say_resolves_sex_to_none(self):
        snapshot = analysis.resolve_profile_snapshot(30, "prefer_not_to_say")
        self.assertIsNone(snapshot["sex"])
        # age_band_resolved is independent of sex -- still resolvable.
        self.assertEqual(snapshot["age_band_resolved"], "30-39")


class WbltAgreementPairsTests(unittest.TestCase):
    """§9: per-leg (distance, angle) pairs for the Stage 7 Bland-Altman export."""

    def test_both_legs_banded_produces_two_pairs(self):
        legs = {
            "right": {"best_distance_cm": 12.0, "leg_angle_deg": 22.5},
            "left": {"best_distance_cm": 10.0, "leg_angle_deg": 18.0},
        }
        pairs = analysis.compute_agreement_pairs(legs)
        self.assertEqual(
            pairs,
            [
                {"leg": "right", "distance_cm": 12.0, "angle_deg": 22.5},
                {"leg": "left", "distance_cm": 10.0, "angle_deg": 18.0},
            ],
        )

    def test_floor_flagged_leg_has_no_pair(self):
        legs = {
            "right": {"best_distance_cm": None, "leg_angle_deg": 5.0},  # floor_flag
            "left": {"best_distance_cm": 10.0, "leg_angle_deg": 18.0},
        }
        pairs = analysis.compute_agreement_pairs(legs)
        self.assertEqual(
            pairs, [{"leg": "left", "distance_cm": 10.0, "angle_deg": 18.0}]
        )

    def test_incomplete_leg_missing_entirely_has_no_pair(self):
        legs = {"right": {"best_distance_cm": 12.0, "leg_angle_deg": 22.5}}
        pairs = analysis.compute_agreement_pairs(legs)
        self.assertEqual(
            pairs, [{"leg": "right", "distance_cm": 12.0, "angle_deg": 22.5}]
        )


class WbltDeterminismTests(unittest.TestCase):
    """§12 Stage 7 gate: re-running the official analysis on the SAME stored
    frames must reproduce the identical result -- required for the replay
    harness (replay_wblt_session.py) to be a meaningful proof of anything."""

    def test_same_frames_produce_identical_result(self):
        frames = _build_frames(knee_xy_offset=0.25, heel_rise=0.0)
        first = analysis.analyze_attempt(
            frames, "right", 10.0, True, exact_age=30, gender="male"
        )
        second = analysis.analyze_attempt(
            frames, "right", 10.0, True, exact_age=30, gender="male"
        )
        self.assertEqual(first, second)

    def test_same_frames_produce_identical_result_when_invalid(self):
        shank_len = 0.5
        rise = config.WBLT_CONFIG["heel_lift_tol_ratio"] * shank_len * 3
        frames = _build_frames(knee_xy_offset=0.0, heel_rise=rise)
        first = analysis.analyze_attempt(
            frames, "right", 10.0, True, exact_age=30, gender="male"
        )
        second = analysis.analyze_attempt(
            frames, "right", 10.0, True, exact_age=30, gender="male"
        )
        self.assertEqual(first, second)


class WbltTrendTests(unittest.TestCase):
    """§11 Stage 6: per-leg distance/angle delta vs the previous session, MDC-suppressed."""

    def test_no_previous_session_is_none_per_leg(self):
        current = {
            "right": {"best_distance_cm": 12.0, "leg_angle_deg": 22.0, "band": "Good"}
        }
        trend = analysis.compute_trend(current, None)
        self.assertIsNone(trend["right"])
        self.assertIsNone(trend["left"])

    def test_above_mdc_change_is_meaningful(self):
        current = {
            "right": {"best_distance_cm": 12.0, "leg_angle_deg": 22.0, "band": "Good"},
        }
        previous = {
            "right": {"best_distance_cm": 9.0, "leg_angle_deg": 15.0, "band": "Fair"},
        }
        trend = analysis.compute_trend(current, previous)
        right = trend["right"]
        self.assertEqual(right["distance_delta_cm"], 3.0)
        self.assertTrue(right["distance_meaningful"])
        self.assertEqual(right["angle_delta_deg"], 7.0)
        self.assertTrue(right["angle_meaningful"])
        self.assertEqual(right["previous_band"], "Fair")

    def test_sub_mdc_change_is_suppressed(self):
        # distance_mdc_cm=1.5, angle_mdc_deg=4.6 -- both deltas below threshold.
        current = {
            "right": {"best_distance_cm": 10.5, "leg_angle_deg": 20.0, "band": "Fair"}
        }
        previous = {
            "right": {"best_distance_cm": 10.0, "leg_angle_deg": 18.0, "band": "Fair"}
        }
        trend = analysis.compute_trend(current, previous)
        right = trend["right"]
        self.assertEqual(right["distance_delta_cm"], 0.5)
        self.assertFalse(right["distance_meaningful"])
        self.assertEqual(right["angle_delta_deg"], 2.0)
        self.assertFalse(right["angle_meaningful"])

    def test_floor_flagged_leg_missing_distance_has_no_trend(self):
        current = {
            "right": {"best_distance_cm": None, "leg_angle_deg": None, "band": None}
        }
        previous = {
            "right": {"best_distance_cm": 10.0, "leg_angle_deg": 18.0, "band": "Fair"}
        }
        trend = analysis.compute_trend(current, previous)
        self.assertIsNone(trend["right"])

    def test_legs_are_independent(self):
        current = {
            "right": {"best_distance_cm": 12.0, "leg_angle_deg": 22.0, "band": "Good"},
            "left": {"best_distance_cm": 8.0, "leg_angle_deg": 14.0, "band": "Poor"},
        }
        previous = {
            "right": {"best_distance_cm": 9.0, "leg_angle_deg": 15.0, "band": "Fair"}
        }
        trend = analysis.compute_trend(current, previous)
        self.assertIsNotNone(trend["right"])
        self.assertIsNone(trend["left"])  # no previous data for left


class WbltAgeBandTests(unittest.TestCase):
    def test_age_bands_resolve_expected_buckets(self):
        self.assertEqual(age_to_band(17), "18-29")  # clamped up, not unbanded
        self.assertEqual(age_to_band(25), "18-29")
        self.assertEqual(age_to_band(30), "30-39")
        self.assertEqual(age_to_band(79), "70-79")
        self.assertEqual(age_to_band(85), "80+")

    def test_resolve_ageband_sex_blocks_on_prefer_not_to_say(self):
        self.assertIsNone(resolve_ageband_sex(30, "prefer_not_to_say"))
        self.assertIsNone(resolve_ageband_sex(None, "male"))
        self.assertEqual(resolve_ageband_sex(30, "male"), "30-39_male")


if __name__ == "__main__":
    unittest.main()
