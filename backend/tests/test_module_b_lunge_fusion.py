"""Stage 4.5 (Lunge) tests: the placeholder model path through the shared registry."""

from __future__ import annotations

import unittest

from app.module_b.core.config import MODULE_B_CORE_CONFIG
from app.module_b.core.features import FeatureVector
from app.module_b.core.fusion import fuse_model
from app.module_b.core.model_registry import (PlaceholderModelBundle,
                                              get_model_bundle)
from app.module_b.core.rules import SubScore, assemble_rule_scores
from app.module_b.lunge.features import LUNGE_FEATURE_NAMES


def _lunge_features() -> FeatureVector:
    return FeatureVector(
        schema_version=MODULE_B_CORE_CONFIG["feature_schema_version"],
        names=LUNGE_FEATURE_NAMES,
        values=tuple(float(index) for index in range(len(LUNGE_FEATURE_NAMES))),
    )


class LungePlaceholderModelTests(unittest.TestCase):
    def test_get_model_bundle_falls_back_to_a_placeholder_for_lunge(self) -> None:
        """No `ml/artifacts/lunge/` exists yet (Stage 5.8 (Lunge) is far off), so
        the shared accessor -- unchanged, no lunge branching inside it -- must
        fall back rather than crash trying to load a missing model.joblib."""
        model = get_model_bundle("lunge")

        self.assertIsInstance(model, PlaceholderModelBundle)
        self.assertTrue(model.is_placeholder)
        self.assertEqual(model.model_version, "stub-0")
        self.assertEqual(model.label_order, ("Poor", "Good"))

    def test_predict_proba_is_a_constant_fifty_fifty_regardless_of_features(
        self,
    ) -> None:
        model = get_model_bundle("lunge")
        low = FeatureVector(
            schema_version=MODULE_B_CORE_CONFIG["feature_schema_version"],
            names=LUNGE_FEATURE_NAMES,
            values=tuple(0.0 for _ in LUNGE_FEATURE_NAMES),
        )
        high = FeatureVector(
            schema_version=MODULE_B_CORE_CONFIG["feature_schema_version"],
            names=LUNGE_FEATURE_NAMES,
            values=tuple(999.0 for _ in LUNGE_FEATURE_NAMES),
        )

        self.assertEqual(model.predict_proba(low), {"Poor": 0.5, "Good": 0.5})
        self.assertEqual(model.predict_proba(high), {"Poor": 0.5, "Good": 0.5})

    def test_get_model_bundle_is_cached(self) -> None:
        self.assertIs(get_model_bundle("lunge"), get_model_bundle("lunge"))

    def test_squat_still_resolves_the_real_trained_model_not_the_placeholder(
        self,
    ) -> None:
        """Regression guard: adding the fallback branch must not change squat's
        own path -- `ml/artifacts/squat/model.joblib` exists, so it should still
        win over the new placeholder branch."""
        model = get_model_bundle("squat")

        self.assertFalse(model.is_placeholder)
        self.assertNotIsInstance(model, PlaceholderModelBundle)

    def test_fusion_with_the_placeholder_always_forces_fair_and_rule_heavy_weights(
        self,
    ) -> None:
        """A constant 0.5/0.5 probability means confidence is always exactly 0.5,
        below confidence_low_threshold -- so even a high rule score cannot buy a
        confident Good/Poor call the placeholder has no real basis for."""
        model = get_model_bundle("lunge")
        result = fuse_model(
            rule_scores=assemble_rule_scores(SubScore("rom_completeness", 9.5)),
            model=model,
            features=_lunge_features(),
            q=1.0,
        )

        self.assertEqual(result.band, "Fair")
        self.assertIn("low_confidence", result.flags)
        self.assertAlmostEqual(result.confidence, 0.5)
        self.assertEqual(result.model_version, "stub-0")
        self.assertTrue(result.placeholder_model_notice)
        self.assertEqual(
            (result.w_rule, result.w_ml),
            (
                MODULE_B_CORE_CONFIG["w_rule_low_confidence"],
                round(1.0 - MODULE_B_CORE_CONFIG["w_rule_low_confidence"], 10),
            ),
        )


if __name__ == "__main__":
    unittest.main()
