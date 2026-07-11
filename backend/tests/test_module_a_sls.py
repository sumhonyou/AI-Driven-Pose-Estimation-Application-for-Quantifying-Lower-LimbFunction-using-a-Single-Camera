"""Unit + replay tests for the Single-Leg Stance (rebuild) core.

Covers geometry (scale-invariance), the lift/hold FSM (timer + hysteresis), the
scoring band boundaries, and a deterministic end-to-end replay through analysis.
"""

import unittest

from app.module_a.sls import analysis, config
from app.module_a.sls import geometry as geo
from app.module_a.sls import scoring
from app.module_a.sls.fsm import (HOLDING, STOPPED, WAITING, CircleDebouncer,
                                  LiftHoldFSM)


def _lm(x=0.0, y=0.0, z=0.0, visibility=1.0):
    return {"x": x, "y": y, "z": z, "visibility": visibility}


def make_world(
    hip_mid_x=0.0,
    right_ankle_y=0.8,
    left_ankle_y=0.8,
    scale=1.0,
    vis=1.0,
    left_ankle_x=None,
):
    """A minimal 33-landmark world pose with controllable hips and ankle heights.

    Hips are 0.2 apart (width), ankles hang below at ~0.8. Everything is multiplied
    by `scale` to test scale-invariance. Y is DOWN, so a smaller ankle y = lifted.

    `left_ankle_x` optionally overrides the left (often stance) foot's planted x
    position; it defaults to hip-width apart from centre (normal double-stance foot
    placement). Pass 0.0 to model a properly weight-shifted stance foot (planted
    under the body midline), which is the realistic "well balanced" geometry --
    without this override, even zero hip sway produces a nonzero ball offset purely
    from the fixture's own foot placement, which is not what "centred" should mean.
    """
    world = [_lm() for _ in range(33)]
    world[geo.HIP["left"]] = _lm((hip_mid_x - 0.1) * scale, 0.0, 0.0, vis)
    world[geo.HIP["right"]] = _lm((hip_mid_x + 0.1) * scale, 0.0, 0.0, vis)
    world[geo.KNEE["left"]] = _lm(-0.1 * scale, 0.4 * scale, 0.0, vis)
    world[geo.KNEE["right"]] = _lm(0.1 * scale, 0.4 * scale, 0.0, vis)
    ankle_left_x = (-0.1 * scale) if left_ankle_x is None else left_ankle_x
    world[geo.ANKLE["left"]] = _lm(ankle_left_x, left_ankle_y * scale, 0.0, vis)
    world[geo.ANKLE["right"]] = _lm(0.1 * scale, right_ankle_y * scale, 0.0, vis)
    return world


def make_frames(
    right_ankle_y_at, dt=0.1, total_sec=8.0, hip_mid_x_at=None, stance_ankle_x=None
):
    """Build a frame sequence; `right_ankle_y_at(t)` returns the right ankle height."""
    frames = []
    t = 0.0
    while t <= total_sec + 1e-9:
        ay = right_ankle_y_at(t)
        hx = hip_mid_x_at(t) if hip_mid_x_at else 0.0
        frames.append(
            {
                "timestampMs": t * 1000.0,
                "worldLandmarks": make_world(
                    hip_mid_x=hx, right_ankle_y=ay, left_ankle_x=stance_ankle_x
                ),
            }
        )
        t += dt
    return frames


class GeometryTests(unittest.TestCase):
    def test_hip_width_and_ball_centre(self):
        world = make_world()
        self.assertAlmostEqual(geo.hip_width(world), 0.2, places=6)
        # Hip midpoint x = 0, stance (left) ankle x = -0.1 -> ball offset +0.1/0.2 = 0.5
        self.assertAlmostEqual(geo.ball_x_norm(world, "left"), 0.5, places=6)

    def test_ball_norm_scale_invariant(self):
        small = geo.ball_x_norm(make_world(hip_mid_x=0.05, scale=1.0), "left")
        big = geo.ball_x_norm(make_world(hip_mid_x=0.05, scale=10.0), "left")
        self.assertAlmostEqual(small, big, places=6)

    def test_inside_circle(self):
        radius = config.SLS_CIRCLE_RADIUS_NORM
        self.assertTrue(geo.is_inside_circle(0.0, radius))
        self.assertTrue(geo.is_inside_circle(radius, radius))
        self.assertFalse(geo.is_inside_circle(radius + 0.01, radius))

    def test_lift_line_and_above(self):
        # baseline ankle y = 0.8, leg length 0.8, norm 0.15 -> line at 0.68
        line = geo.lift_line_y(0.8, 0.8, 0.15)
        self.assertAlmostEqual(line, 0.68, places=6)
        self.assertTrue(geo.is_above_line(0.5, line))  # raised foot (smaller y)
        self.assertFalse(geo.is_above_line(0.8, line))  # planted foot


class ScoringTests(unittest.TestCase):
    def test_hold_score_boundaries(self):
        self.assertAlmostEqual(scoring.hold_score(9.9), 3.96, places=2)
        self.assertAlmostEqual(scoring.hold_score(10.0), 4.0, places=2)
        self.assertAlmostEqual(scoring.hold_score(24.9), 6.98, places=2)
        self.assertAlmostEqual(scoring.hold_score(25.0), 7.0, places=2)
        self.assertAlmostEqual(scoring.hold_score(44.9), 9.985, places=2)
        self.assertAlmostEqual(scoring.hold_score(45.0), 10.0, places=2)

    def test_stability_score(self):
        self.assertAlmostEqual(scoring.stability_score(0.0), 0.0)
        self.assertAlmostEqual(scoring.stability_score(0.5), 5.0)
        self.assertAlmostEqual(scoring.stability_score(1.0), 10.0)

    def test_combined_and_band(self):
        good = scoring.score_leg(45.0, 1.0)
        self.assertEqual(good["band"], "good")
        self.assertAlmostEqual(good["combinedScore"], 10.0, places=2)
        poor = scoring.score_leg(9.9, 0.0)
        self.assertEqual(poor["band"], "poor")


class FsmTests(unittest.TestCase):
    def test_timer_starts_on_confirmed_lift_and_stops_on_drop(self):
        fsm = LiftHoldFSM(max_hold_sec=45, lift_persist_frames=3, drop_persist_frames=3)
        # 3 above frames confirm the lift; hold starts at the 3rd (t=0.2)
        for i in range(3):
            fsm.update(i * 0.1, True, True)
        self.assertEqual(fsm.state, HOLDING)
        # Hold until t=10.0
        t = 0.3
        while t <= 10.0 + 1e-9:
            fsm.update(t, True, True)
            t += 0.1
        # Then 3 below frames -> drop
        for i in range(1, 4):
            fsm.update(10.0 + i * 0.1, False, False)
        self.assertEqual(fsm.state, STOPPED)
        self.assertEqual(fsm.stop_reason, "foot_dropped_below_line")
        self.assertAlmostEqual(fsm.hold_seconds, 9.8, delta=0.2)

    def test_single_frame_dips_do_not_stop(self):
        fsm = LiftHoldFSM(lift_persist_frames=3, drop_persist_frames=3)
        for i in range(3):
            fsm.update(i * 0.1, True, True)
        self.assertEqual(fsm.state, HOLDING)
        # Alternate a single below frame with above frames -> streak never reaches 3
        t = 0.3
        for i in range(40):
            below = i % 4 == 0
            fsm.update(t, not below, not below)
            t += 0.1
        self.assertEqual(fsm.state, HOLDING)

    def test_cap_at_max(self):
        fsm = LiftHoldFSM(max_hold_sec=5, lift_persist_frames=3, drop_persist_frames=3)
        t = 0.0
        for _ in range(200):
            fsm.update(t, True, True)
            t += 0.1
        self.assertEqual(fsm.stop_reason, "max_duration_reached")
        self.assertTrue(fsm.capped_at_max)
        self.assertAlmostEqual(fsm.hold_seconds, 5.0, places=2)


class CircleDebouncerTests(unittest.TestCase):
    def test_first_sample_sets_state_directly(self):
        self.assertTrue(CircleDebouncer(persist_frames=2).update(True))
        self.assertFalse(CircleDebouncer(persist_frames=2).update(False))

    def test_single_frame_dip_does_not_flip(self):
        deb = CircleDebouncer(persist_frames=2)
        deb.update(True)
        self.assertTrue(deb.update(False))  # streak=1, not yet flipped
        self.assertTrue(
            deb.update(True)
        )  # back inside before persisting -> streak resets

    def test_persistent_change_flips_state(self):
        deb = CircleDebouncer(persist_frames=2)
        deb.update(True)
        deb.update(False)  # streak=1
        self.assertFalse(deb.update(False))  # streak=2 -> flips to outside


class AnalysisReplayTests(unittest.TestCase):
    def test_clean_hold_is_scored_good_and_deterministic(self):
        # Planted for 2s (calibration), then lift the right foot and hold to the cap.
        # stance_ankle_x=0.0 models a properly weight-shifted stance foot (planted
        # under the body midline) -- realistic good technique -- rather than the
        # fixture's default double-stance foot width, which would read as a large
        # ball offset even with zero simulated sway.
        def ankle(t):
            return 0.8 if t < 2.0 else 0.45

        frames = make_frames(ankle, total_sec=50.0, stance_ankle_x=0.0)
        r1 = analysis.analyze_leg(frames, "right")
        r2 = analysis.analyze_leg(frames, "right")
        self.assertEqual(r1, r2)  # deterministic

        m = r1["metrics"]
        self.assertGreater(m["holdSeconds"], 25.0)  # long hold -> Good hold band
        self.assertIn(m["band"], ("good", "fair"))
        self.assertGreater(m["percentFramesInsideCircle"], 0.9)  # centred -> stable
        self.assertIn(
            m["stopReason"], ("max_duration_reached", "foot_dropped_below_line")
        )

    def test_swaying_hold_has_lower_stability(self):
        # Same clean lift/hold timing as the steady case above, but the hip midpoint
        # oscillates well beyond the tolerance circle around the (properly centred)
        # stance ankle -- this is the regression test for the ball-in-circle
        # tolerance actually catching real wobble, which was the reported bug.
        def ankle(t):
            return 0.8 if t < 2.0 else 0.45

        def sway(t):
            return 0.5 if int(t * 2) % 2 == 0 else -0.5

        frames = make_frames(
            ankle, total_sec=20.0, hip_mid_x_at=sway, stance_ankle_x=0.0
        )
        m = analysis.analyze_leg(frames, "right")["metrics"]
        self.assertLess(m["percentFramesInsideCircle"], 0.5)
        self.assertLess(m["stabilityScore"], 5.0)

    def test_early_drop_gives_short_hold(self):
        def ankle(t):
            if t < 2.0:
                return 0.8
            if t < 6.0:
                return 0.45  # ~4s hold
            return 0.8  # foot back down

        frames = make_frames(ankle, total_sec=10.0)
        m = analysis.analyze_leg(frames, "right")["metrics"]
        self.assertEqual(m["stopReason"], "foot_dropped_below_line")
        self.assertLess(m["holdSeconds"], 6.0)

    def test_never_lifted_is_invalid(self):
        frames = make_frames(lambda t: 0.8, total_sec=6.0)  # never lifts
        m = analysis.analyze_leg(frames, "right")["metrics"]
        self.assertEqual(m["band"], "invalid")
        self.assertEqual(m["holdSeconds"], 0.0)


if __name__ == "__main__":
    unittest.main()
