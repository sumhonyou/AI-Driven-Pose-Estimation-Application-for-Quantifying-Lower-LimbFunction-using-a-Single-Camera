"""Stage 4.5/5.8 tests for model bundles, schema guards and fusion gates."""

from __future__ import annotations

import math
import unittest

from app.module_b.core.config import MODULE_B_CORE_CONFIG
from app.module_b.core.features import FeatureVector
from app.module_b.core.fusion import fuse_model, fuse_scores, score_to_band
from app.module_b.core.model_registry import JoblibModelBundle, get_model_bundle
from app.module_b.core.registry import get_exercise
from app.module_b.core.rules import SubScore, assemble_rule_scores
from app.module_b.squat.config import SQUAT_CONFIG
from app.module_b.squat.features import SQUAT_FEATURE_NAMES


def _features(names: tuple[str, ...] = ("feature_a", "feature_b")) -> FeatureVector:
    return FeatureVector(
        schema_version=MODULE_B_CORE_CONFIG["feature_schema_version"],
        names=names,
        values=tuple(float(index) for index in range(len(names))),
    )


class _FakeClassifier:
    def __init__(self, probabilities: tuple[float, float] = (0.25, 0.75)) -> None:
        self._probabilities = list(probabilities)

    def predict_proba(self, rows: list[list[float]]) -> list[list[float]]:
        return [self._probabilities for _ in rows]


class ModelRegistryTests(unittest.TestCase):
    def test_schema_mismatch_raises_loudly(self) -> None:
        # validate_model_bundle() runs in __post_init__, so a bundle whose own
        # feature_schema_version disagrees with the runtime's is rejected at
        # construction -- it never gets far enough to score a feature vector.
        with self.assertRaisesRegex(ValueError, "schema mismatch"):
            JoblibModelBundle(
                classifier=_FakeClassifier(),
                feature_schema_version="0.9.0",
                model_version="squat-test-1",
                label_order=("Poor", "Good"),
                feature_names=(),
            )

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
        # P(Good)=0.9, confidence=0.9 -- clears Stage 5.6's
        # confidence_low_threshold=0.85, so this exercises the DEFAULT (not
        # low-confidence) weight path. A rule_score of 8.0 here would instead fall
        # below 0.85 and force the low-confidence branch already covered by
        # test_low_confidence_forces_fair_and_rule_heavy_weights above.
        model = JoblibModelBundle(
            classifier=_FakeClassifier(probabilities=(0.1, 0.9)),
            feature_schema_version=MODULE_B_CORE_CONFIG["feature_schema_version"],
            model_version="squat-test-1",
            label_order=("Poor", "Good"),
            feature_names=(),
        )
        result = fuse_model(
            rule_scores=assemble_rule_scores(SubScore("rom", 8.0)),
            model=model,
            features=_features(),
            q=1.0,
        )

        self.assertEqual(result.model_version, "squat-test-1")
        self.assertEqual((result.w_rule, result.w_ml), (0.2, 0.8))
        self.assertEqual(result.band, "Good")


class RealSquatModelBundleTests(unittest.TestCase):
    """Stage 5.8: the real exported artifact, loaded via `get_model_bundle()`.

    Reads `ml/artifacts/squat/` — a committed artifact, not gitignored (task.md's own
    note), so these tests are reproducible from a fresh checkout without retraining.
    """

    def test_bundle_is_the_real_trained_model_not_a_placeholder(self) -> None:
        model = get_model_bundle("squat")

        self.assertFalse(model.is_placeholder)
        self.assertEqual(model.label_order, ("Poor", "Good"))
        self.assertEqual(model.feature_names, SQUAT_FEATURE_NAMES)
        self.assertTrue(model.model_version.startswith("squat-1.0.0+rehab246-loso-"))

    def test_predict_proba_matches_the_forestplussigmoid_recomposition_directly(
        self,
    ) -> None:
        """Cross-checks `JoblibModelBundle.predict_proba()`'s dict output against the
        same forest+sigmoid formula computed independently in this test, rather than
        trusting `_CalibratedForestClassifier`'s own arithmetic to grade itself."""
        model = get_model_bundle("squat")
        features = FeatureVector(
            schema_version=model.feature_schema_version,
            names=model.feature_names,
            values=tuple(float(i + 1) for i in range(len(model.feature_names))),
        )

        result = model.predict_proba(features)

        forest = model.classifier.forest
        calibration = model.classifier.calibration
        raw_p_good = forest.predict_proba([list(features.values)])[0][1]
        expected_p_good = 1.0 / (
            1.0 + math.exp(calibration["a"] * raw_p_good + calibration["b"])
        )
        self.assertAlmostEqual(result["Good"], expected_p_good, places=9)
        self.assertAlmostEqual(result["Poor"], 1.0 - expected_p_good, places=9)
        self.assertAlmostEqual(result["Good"] + result["Poor"], 1.0, places=9)

    def test_predict_proba_is_deterministic_across_repeated_calls(self) -> None:
        model = get_model_bundle("squat")
        features = FeatureVector(
            schema_version=model.feature_schema_version,
            names=model.feature_names,
            values=tuple(float(i + 1) for i in range(len(model.feature_names))),
        )

        first = model.predict_proba(features)
        second = model.predict_proba(features)

        self.assertEqual(first, second)

    def test_schema_guard_fires_against_the_real_bundle_on_mismatch(self) -> None:
        model = get_model_bundle("squat")
        stale_features = FeatureVector(
            schema_version="0.9.0",
            names=model.feature_names,
            values=tuple(float(i + 1) for i in range(len(model.feature_names))),
        )

        with self.assertRaisesRegex(ValueError, "schema mismatch"):
            model.predict_proba(stale_features)

    def test_schema_guard_fires_on_feature_name_order_mismatch_for_the_real_bundle(
        self,
    ) -> None:
        model = get_model_bundle("squat")
        reordered_features = FeatureVector(
            schema_version=model.feature_schema_version,
            names=tuple(reversed(model.feature_names)),
            values=tuple(float(i + 1) for i in range(len(model.feature_names))),
        )

        with self.assertRaisesRegex(ValueError, "names/order"):
            model.predict_proba(reordered_features)


class BinaryBandPolicyTests(unittest.TestCase):
    """Stage 5.11: squat commits to a binary Good/Poor band via SQUAT_CONFIG.band_policy.

    The 3-band abstention path stays the default (covered by FusionTests above); these
    check the opt-in binary branch and the placeholder safeguard.
    """

    def setUp(self) -> None:
        self.policy = SQUAT_CONFIG["band_policy"]

    def test_squat_exercise_exposes_the_binary_policy(self) -> None:
        policy = get_exercise("squat").band_policy
        self.assertEqual(policy["scheme"], "binary")
        self.assertEqual((policy["w_rule"], policy["w_ml"]), (0.0, 1.0))

    def test_high_confidence_good_commits_to_good(self) -> None:
        result = fuse_scores(
            rule_score=2.0,
            probabilities={"Poor": 0.05, "Good": 0.95},
            q=1.0,
            model_version="squat-test-1",
            is_placeholder_model=False,
            band_policy=self.policy,
        )
        self.assertEqual(result.band, "Good")
        self.assertEqual((result.w_rule, result.w_ml), (0.0, 1.0))

    def test_low_pgood_commits_to_poor_and_never_fair(self) -> None:
        # score = 10*P(Good) = 6.0, below the 8.448 cut -> Poor. Confidence 0.6 < 0.85
        # records low_confidence, but under the binary policy that no longer forces Fair.
        # A high rule_score would prop the score above the cut under the old triband
        # weights; w_rule=0 makes that irrelevant here.
        result = fuse_scores(
            rule_score=9.0,
            probabilities={"Poor": 0.4, "Good": 0.6},
            q=1.0,
            model_version="squat-test-1",
            is_placeholder_model=False,
            band_policy=self.policy,
        )
        self.assertEqual(result.band, "Poor")
        self.assertIn("low_confidence", result.flags)

    def test_low_capture_quality_still_commits_a_band_but_flags_retry(self) -> None:
        result = fuse_scores(
            rule_score=2.0,
            probabilities={"Poor": 0.05, "Good": 0.95},
            q=0.4,
            model_version="squat-test-1",
            is_placeholder_model=False,
            band_policy=self.policy,
        )
        self.assertIn(result.band, {"Good", "Poor"})
        self.assertNotEqual(result.band, "Fair")
        self.assertIn("retry_camera_placement", result.flags)

    def test_placeholder_model_keeps_abstaining_even_with_a_binary_policy(self) -> None:
        # A constant-0.5 placeholder must not be forced into a hard Good/Poor verdict.
        result = fuse_scores(
            rule_score=8.0,
            probabilities={"Poor": 0.5, "Good": 0.5},
            q=1.0,
            model_version="stub-0",
            is_placeholder_model=True,
            band_policy=self.policy,
        )
        self.assertEqual(result.band, "Fair")


if __name__ == "__main__":
    unittest.main()
