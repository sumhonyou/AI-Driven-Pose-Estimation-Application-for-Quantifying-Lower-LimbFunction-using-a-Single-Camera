"""Boundary and incentive tests for the Stage 4.4 (Lunge) rule sub-scores."""

from __future__ import annotations

import unittest

from app.module_b.core.config import MODULE_B_CORE_CONFIG
from app.module_b.core.features import FeatureVector
from app.module_b.lunge.features import LUNGE_FEATURE_NAMES
from app.module_b.lunge.rules import (
    ROM_CODE,
    STABILITY_CODE,
    SYMMETRY_CODE,
    rom_subscore,
    score_lunge_set,
    stability_subscore,
    symmetry_subscore,
    tempo_subscore,
)


def _features(lead_leg: str = "left", **overrides: float) -> FeatureVector:
    values = {name: 0.0 for name in LUNGE_FEATURE_NAMES}
    values.update(
        {
            "front_ankle_df_proxy_deg": 45.0,
            "rep_duration_s": 1.0,
            "hip_mid_jitter_norm": 0.0,
        }
    )
    values.update(overrides)
    return FeatureVector(
        schema_version=MODULE_B_CORE_CONFIG["feature_schema_version"],
        names=LUNGE_FEATURE_NAMES,
        values=tuple(values[name] for name in LUNGE_FEATURE_NAMES),
        lead_leg=lead_leg,
    )


class LungeRomRuleTests(unittest.TestCase):
    def test_rom_band_boundaries(self) -> None:
        expected_scores = {
            0.0: 0.0,
            60.0: 2.0,
            90.0: 5.0,
            110.0: 8.0,
            130.0: 10.0,
        }

        for peak_flexion, expected_score in expected_scores.items():
            with self.subTest(peak_flexion=peak_flexion):
                score = rom_subscore(_features(front_knee_flex_peak_deg=peak_flexion))
                self.assertEqual(score.score, expected_score)

    def test_possible_df_limit_applies_rom_floor_and_note(self) -> None:
        score = rom_subscore(
            _features(front_knee_flex_peak_deg=30.0, front_ankle_df_proxy_deg=10.0)
        )

        self.assertEqual(score.code, ROM_CODE)
        self.assertEqual(score.score, 2.0)
        self.assertEqual(score.notes, ("rom_possibly_df_limited",))


class LungeTempoRuleTests(unittest.TestCase):
    def test_tempo_is_unavailable_for_one_rep(self) -> None:
        self.assertIsNone(tempo_subscore([_features(rep_duration_s=1.0)]).score)

    def test_tempo_cv_band_boundaries(self) -> None:
        high_consistency = tempo_subscore(
            [_features(rep_duration_s=0.9), _features(rep_duration_s=1.1)]
        )
        moderate_consistency = tempo_subscore(
            [_features(rep_duration_s=0.75), _features(rep_duration_s=1.25)]
        )

        self.assertAlmostEqual(high_consistency.score or 0.0, 9.0)
        self.assertAlmostEqual(moderate_consistency.score or 0.0, 5.0)


class LungeStabilityRuleTests(unittest.TestCase):
    def test_stability_jitter_and_duration_boundaries(self) -> None:
        fully_controlled = stability_subscore(
            _features(rep_duration_s=1.0, hip_mid_jitter_norm=0.0)
        )
        fully_unstable = stability_subscore(
            _features(rep_duration_s=1.0, hip_mid_jitter_norm=0.10)
        )
        half_duration_controlled = stability_subscore(
            _features(rep_duration_s=0.5, hip_mid_jitter_norm=0.0)
        )

        self.assertEqual(fully_controlled.score, 10.0)
        self.assertEqual(fully_unstable.score, 0.0)
        self.assertEqual(half_duration_controlled.score, 5.0)

    def test_long_well_controlled_rep_beats_brief_still_moment(self) -> None:
        brief_still = stability_subscore(
            _features(rep_duration_s=0.2, hip_mid_jitter_norm=0.0)
        )
        long_controlled = stability_subscore(
            _features(rep_duration_s=1.2, hip_mid_jitter_norm=0.01)
        )

        self.assertGreaterEqual(long_controlled.score or 0.0, brief_still.score or 0.0)

    def test_set_stability_is_duration_weighted(self) -> None:
        scores = score_lunge_set(
            [
                _features(rep_duration_s=1.0, hip_mid_jitter_norm=0.0),
                _features(rep_duration_s=9.0, hip_mid_jitter_norm=0.10),
            ]
        )

        self.assertAlmostEqual(scores.by_code()[STABILITY_CODE].score or 0.0, 1.0)


class LungeSymmetryRuleTests(unittest.TestCase):
    """Cross-rep only (task.md's delta): compares leading-left vs leading-right
    reps' front-knee peak flexion + ROM. Report-only per HY: score is always
    None, so it can never move S_rule -- only `metrics` carries the numbers."""

    def test_unavailable_with_a_single_leg_set(self) -> None:
        score = symmetry_subscore(
            [
                _features(lead_leg="left", front_knee_flex_peak_deg=90.0),
                _features(lead_leg="left", front_knee_flex_peak_deg=95.0),
            ]
        )

        self.assertIsNone(score.score)
        self.assertEqual(score.notes, ("symmetry_unavailable_single_leg_set",))
        self.assertEqual(score.metrics["left_lead_reps"], 2.0)
        self.assertEqual(score.metrics["right_lead_reps"], 0.0)
        self.assertNotIn("front_knee_peak_symmetry_index_pct", score.metrics)

    def test_available_with_one_rep_per_leg(self) -> None:
        """min_reps_per_leg=1 (HY 2026-07-17): a single rep each side is enough
        to attempt the comparison, mirroring Tempo's philosophy."""
        score = symmetry_subscore(
            [
                _features(
                    lead_leg="left",
                    front_knee_flex_peak_deg=90.0,
                    front_knee_rom_deg=90.0,
                ),
                _features(
                    lead_leg="right",
                    front_knee_flex_peak_deg=90.0,
                    front_knee_rom_deg=90.0,
                ),
            ]
        )

        self.assertIsNone(score.score)
        self.assertEqual(score.metrics["left_lead_reps"], 1.0)
        self.assertEqual(score.metrics["right_lead_reps"], 1.0)
        self.assertAlmostEqual(score.metrics["front_knee_peak_symmetry_index_pct"], 0.0)
        self.assertAlmostEqual(score.metrics["front_knee_rom_symmetry_index_pct"], 0.0)

    def test_symmetry_index_reflects_a_real_left_right_difference(self) -> None:
        score = symmetry_subscore(
            [
                _features(
                    lead_leg="left",
                    front_knee_flex_peak_deg=100.0,
                    front_knee_rom_deg=100.0,
                ),
                _features(
                    lead_leg="right",
                    front_knee_flex_peak_deg=80.0,
                    front_knee_rom_deg=80.0,
                ),
            ]
        )

        # |100-80| / (0.5*(100+80)) * 100 = 22.22%
        self.assertAlmostEqual(
            score.metrics["front_knee_peak_symmetry_index_pct"], 22.222222, places=4
        )
        self.assertAlmostEqual(
            score.metrics["front_knee_rom_symmetry_index_pct"], 22.222222, places=4
        )

    def test_symmetry_never_moves_the_overall_set_score(self) -> None:
        """The whole point of 'report-only': a badly-asymmetric set must score
        identically to a symmetric one on every other axis."""
        common_kwargs = dict(
            front_knee_flex_peak_deg=90.0,
            rep_duration_s=1.0,
            hip_mid_jitter_norm=0.0,
            front_ankle_df_proxy_deg=45.0,
        )
        symmetric = score_lunge_set(
            [
                _features(lead_leg="left", **common_kwargs),
                _features(lead_leg="left", **common_kwargs),
            ]
        )
        asymmetric = score_lunge_set(
            [
                _features(lead_leg="left", **common_kwargs),
                _features(lead_leg="right", **common_kwargs),
            ]
        )

        self.assertEqual(symmetric.score, asymmetric.score)
        self.assertIsNone(symmetric.by_code()[SYMMETRY_CODE].score)
        self.assertIsNone(asymmetric.by_code()[SYMMETRY_CODE].score)


if __name__ == "__main__":
    unittest.main()
