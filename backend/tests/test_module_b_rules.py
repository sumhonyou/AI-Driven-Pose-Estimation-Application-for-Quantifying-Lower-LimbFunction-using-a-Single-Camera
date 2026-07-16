"""Boundary and incentive tests for the Stage 4.4 squat rule sub-scores."""

from __future__ import annotations

import unittest

from app.module_b.core.config import MODULE_B_CORE_CONFIG
from app.module_b.core.features import FeatureVector
from app.module_b.core.rules import SubScore, assemble_rule_scores
from app.module_b.squat.features import SQUAT_FEATURE_NAMES
from app.module_b.squat.rules import (
    ROM_CODE,
    STABILITY_CODE,
    rom_subscore,
    score_squat_set,
    stability_subscore,
    tempo_subscore,
)


def _features(**overrides: float) -> FeatureVector:
    values = {name: 0.0 for name in SQUAT_FEATURE_NAMES}
    values.update(
        {
            "ankle_df_proxy_deg": 45.0,
            "rep_duration_s": 1.0,
            "hip_mid_jitter_norm": 0.0,
        }
    )
    values.update(overrides)
    return FeatureVector(
        schema_version=MODULE_B_CORE_CONFIG["feature_schema_version"],
        names=SQUAT_FEATURE_NAMES,
        values=tuple(values[name] for name in SQUAT_FEATURE_NAMES),
    )


class SquatRomRuleTests(unittest.TestCase):
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
                score = rom_subscore(_features(knee_flex_peak_deg=peak_flexion))
                self.assertEqual(score.score, expected_score)

    def test_possible_df_limit_applies_rom_floor_and_note(self) -> None:
        score = rom_subscore(
            _features(knee_flex_peak_deg=30.0, ankle_df_proxy_deg=10.0)
        )

        self.assertEqual(score.code, ROM_CODE)
        self.assertEqual(score.score, 2.0)
        self.assertEqual(score.notes, ("rom_possibly_df_limited",))


class SquatTempoRuleTests(unittest.TestCase):
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


class SquatStabilityRuleTests(unittest.TestCase):
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
        scores = score_squat_set(
            [
                _features(rep_duration_s=1.0, hip_mid_jitter_norm=0.0),
                _features(rep_duration_s=9.0, hip_mid_jitter_norm=0.10),
            ]
        )

        self.assertAlmostEqual(scores.by_code()[STABILITY_CODE].score or 0.0, 1.0)


class RuleAssemblyTests(unittest.TestCase):
    def test_overall_rule_score_renormalizes_over_available_subscores(self) -> None:
        scores = assemble_rule_scores(
            SubScore("rom", 2.0), SubScore("tempo", None), SubScore("stability", 8.0)
        )

        self.assertEqual(scores.score, 5.0)


if __name__ == "__main__":
    unittest.main()
