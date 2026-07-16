"""Stage 4.5 tests for placeholder inference, schema guards and fusion gates."""

from __future__ import annotations

import unittest

from app.module_b.core.config import MODULE_B_CORE_CONFIG
from app.module_b.core.features import FeatureVector
from app.module_b.core.fusion import fuse_model, fuse_scores, score_to_band
from app.module_b.core.model_registry import JoblibModelBundle, StubModel
from app.module_b.core.rules import SubScore, assemble_rule_scores


def _features(names: tuple[str, ...] = ("feature_a", "feature_b")) -> FeatureVector:
    return FeatureVector(
        schema_version=MODULE_B_CORE_CONFIG["feature_schema_version"],
        names=names,
        values=tuple(float(index) for index in range(len(names))),
    )


class _FakeClassifier:
    def predict_proba(self, rows: list[list[float]]) -> list[list[float]]:
        return [[0.25, 0.75] for _ in rows]


class ModelRegistryTests(unittest.TestCase):
    def test_stub_model_is_deterministic_and_announces_itself(self) -> None:
        features = _features()
        model = StubModel(rule_score=7.0)

        self.assertEqual(model.model_version, "stub-0")
        self.assertTrue(model.is_placeholder)
        self.assertEqual(
            model.predict_proba(features), {"Poor": 0.30000000000000004, "Good": 0.7}
        )

    def test_schema_mismatch_raises_loudly(self) -> None:
        with self.assertRaisesRegex(ValueError, "schema mismatch"):
            StubModel(rule_score=5.0, feature_schema_version="0.9.0")

    def test_trained_model_refuses_feature_name_order_mismatch(self) -> None:
        features = _features()
        model = JoblibModelBundle(
            classifier=_FakeClassifier(),
            feature_schema_version=features.schema_version,
            model_version="squat-test-1",
            label_order=("Poor", "Good"),
            feature_names=("feature_b", "feature_a"),
        )

        with self.assertRaisesRegex(ValueError, "names/order"):
            model.predict_proba(features)


class FusionTests(unittest.TestCase):
    def test_d6_band_boundaries(self) -> None:
        expected = {
            3.999: "Poor",
            4.0: "Fair",
            6.999: "Fair",
            7.0: "Good",
        }

        for score, band in expected.items():
            with self.subTest(score=score):
                self.assertEqual(score_to_band(score), band)

    def test_low_confidence_forces_fair_and_rule_heavy_weights(self) -> None:
        result = fuse_scores(
            rule_score=8.0,
            probabilities={"Poor": 0.4, "Good": 0.6},
            q=1.0,
            model_version="stub-0",
            is_placeholder_model=True,
        )

        self.assertEqual(result.band, "Fair")
        self.assertIn("low_confidence", result.flags)
        self.assertEqual((result.w_rule, result.w_ml), (0.7, 0.3))
        self.assertTrue(result.placeholder_model_notice)

    def test_low_capture_quality_forces_fair_retry_and_rule_heavy_weights(self) -> None:
        result = fuse_scores(
            rule_score=8.0,
            probabilities={"Poor": 0.1, "Good": 0.9},
            q=0.59,
            model_version="squat-test-1",
            is_placeholder_model=False,
        )

        self.assertEqual(result.band, "Fair")
        self.assertIn("retry_camera_placement", result.flags)
        self.assertEqual((result.w_rule, result.w_ml), (0.7, 0.3))

    def test_model_fusion_carries_model_version_and_default_weights(self) -> None:
        result = fuse_model(
            rule_scores=assemble_rule_scores(SubScore("rom", 8.0)),
            model=StubModel(rule_score=8.0),
            features=_features(),
            q=1.0,
        )

        self.assertEqual(result.model_version, "stub-0")
        self.assertEqual((result.w_rule, result.w_ml), (0.4, 0.6))
        self.assertEqual(result.band, "Good")


if __name__ == "__main__":
    unittest.main()
