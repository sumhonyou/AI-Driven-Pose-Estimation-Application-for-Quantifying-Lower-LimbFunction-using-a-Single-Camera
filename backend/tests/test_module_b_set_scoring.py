"""Stage 5.13: per-rep verdicts aggregated by strict majority vote.

The replay corpus cannot cover this. Its samples are synthetic and every rep inside one
sample is near-identical, so each set is unanimous — exactly the case where per-rep voting
and the old set-wide override agree. The interesting behaviour is a MIXED set, which only
these hand-built vectors exercise.
"""

from __future__ import annotations

import unittest

from app.module_b.core.features import FeatureVector
from app.module_b.core.rules import RuleScores, SubScore, assemble_rule_scores
from app.module_b.core.set_scoring import failed_gates_by_rep, score_set

SCHEMA = "test-1"
# Squat's shipped policy. The threshold is the real calibrated value, so these tests
# break if the deployed cut ever moves without the expectations being revisited.
VOTING_POLICY = {
    "scheme": "binary",
    "decision_threshold": 8.447974,
    "w_rule": 0.0,
    "w_ml": 1.0,
    "aggregation": "majority_vote",
}
LEGACY_POLICY = {k: v for k, v in VOTING_POLICY.items() if k != "aggregation"}


def _vector(marker: float) -> FeatureVector:
    """One vector whose single value the fake model reads straight back as P(Good)."""
    return FeatureVector(schema_version=SCHEMA, names=("p_good",), values=(marker,))


class _EchoModel:
    """Returns P(Good) = the vector's own value, so each rep's score is set by hand."""

    feature_schema_version = SCHEMA
    model_version = "echo-1"
    label_order = ("Poor", "Good")
    feature_names = ("p_good",)
    is_placeholder = False

    def predict_proba(self, features: FeatureVector) -> dict[str, float]:
        p_good = features.values[0]
        return {"Good": p_good, "Poor": 1.0 - p_good}


class _PlaceholderModel(_EchoModel):
    is_placeholder = True
    model_version = "stub-0"


def _rules(score: float = 7.0) -> RuleScores:
    return assemble_rule_scores(
        SubScore(code="rom_completeness", score=score),
        SubScore(code="tempo_consistency", score=score),
        SubScore(code="stability_control", score=score),
    )


# P(Good) values that sit clearly either side of the 0.8448 cut.
PASS = 0.95
FAIL = 0.40


def _score(markers, gates=None, policy=VOTING_POLICY, model=None):
    return score_set(
        rule_scores=_rules(),
        model=model or _EchoModel(),
        feature_vectors=[_vector(m) for m in markers],
        q=0.9,
        band_policy=policy,
        failed_gates_by_rep=gates,
    )


class MajorityVoteTests(unittest.TestCase):
    def test_six_of_ten_good_reps_bands_the_set_good(self) -> None:
        result = _score([PASS] * 6 + [FAIL] * 4)

        self.assertEqual(result.fusion.band, "Good")
        self.assertEqual(result.good_rep_count, 6)

    def test_an_exact_five_five_split_bands_poor(self) -> None:
        """Ties break toward Poor — a strict majority is required to pass.

        Deliberate: Stage 5.11 chose the safety-first operating point, and a set the
        model cannot call either way should not be told it is fine.
        """
        result = _score([PASS] * 5 + [FAIL] * 5)

        self.assertEqual(result.fusion.band, "Poor")
        self.assertEqual(result.good_rep_count, 5)

    def test_one_bad_rep_no_longer_condemns_a_long_set(self) -> None:
        """The Stage 5.12 regression this stage exists to fix."""
        result = _score([PASS] * 29 + [FAIL])

        self.assertEqual(result.fusion.band, "Good")

    def test_set_score_is_the_share_of_clean_reps(self) -> None:
        """Stage 5.18 replaced the old mean-ML score. `ml_score` keeps the mean (it still
        feeds the report's secondary card); `score` is now the clean-rep share."""
        # 0.9 and 0.7 clear the 0.8448 cut... only 0.9 does. 1 of 3 clean -> 3.33/10.
        result = _score([0.9, 0.7, 0.5])

        self.assertAlmostEqual(result.fusion.ml_score, 7.0)  # mean is unchanged
        self.assertEqual(result.good_rep_count, 1)
        self.assertAlmostEqual(result.fusion.score, 10.0 / 3.0)

    def test_score_reaches_both_ends_of_the_scale(self) -> None:
        """The defect that motivated the change: the old score compressed the entire
        0%-100% quality range into 8.02-9.27 on real sessions."""
        self.assertAlmostEqual(_score([PASS] * 4).fusion.score, 10.0)
        self.assertAlmostEqual(_score([FAIL] * 4).fusion.score, 0.0)

    def test_every_rep_gets_a_verdict_not_just_the_first(self) -> None:
        result = _score([PASS, FAIL, PASS])

        self.assertEqual(len(result.rep_verdicts), 3)
        self.assertEqual([v.rep_index for v in result.rep_verdicts], [0, 1, 2])
        self.assertEqual(
            [v.counted_good for v in result.rep_verdicts], [True, False, True]
        )


class GatesFoldIntoTheRepVerdictTests(unittest.TestCase):
    def test_a_gated_rep_is_not_good_even_when_the_model_passes_it(self) -> None:
        result = _score([PASS, PASS, PASS], gates={1: ("heel_lift",)})

        self.assertEqual(result.good_rep_count, 2)
        self.assertFalse(result.rep_verdicts[1].counted_good)
        self.assertTrue(result.rep_verdicts[1].ml_passed)
        self.assertEqual(result.rep_verdicts[1].failed_gates, ("heel_lift",))

    def test_gates_on_a_majority_of_reps_flip_the_set_to_poor(self) -> None:
        result = _score(
            [PASS] * 3, gates={0: ("insufficient_depth",), 1: ("heel_lift",)}
        )

        self.assertEqual(result.fusion.band, "Poor")

    def test_gate_failures_now_move_the_score_as_well_as_the_band(self) -> None:
        """Stage 5.18 reversed Stage 5.13's "gates change the band, never the number".

        Under the old mean-ML score these three reps scored 9.5 while banding Poor,
        because the model cannot see a heel lift (`heel_rise_peak_norm` is rule-only and
        absent from the feature vector). The score now counts clean reps, so a gated rep
        lowers it. The model's own reading is preserved on `ml_score`.
        """
        result = _score([PASS] * 3, gates={0: ("heel_lift",), 1: ("heel_lift",)})

        self.assertEqual(result.fusion.band, "Poor")
        self.assertAlmostEqual(result.fusion.score, 10.0 / 3.0)  # 1 of 3 clean
        self.assertAlmostEqual(result.fusion.ml_score, 10.0 * PASS)  # model unchanged


class BandAndScoreCannotContradictTests(unittest.TestCase):
    """Stage 5.18's headline property, and the whole point of the change.

    The original bug report was a report showing 8.0/10 beside "Needs Improvement".
    Because the score is now the same clean-rep fraction the band vote uses, the two are
    two renderings of one quantity: `band == "Good"` iff `score > 5.0`, always.
    """

    def test_invariant_holds_across_every_split_from_zero_to_all_clean(self) -> None:
        total = 10
        for clean in range(total + 1):
            with self.subTest(clean=clean):
                result = _score([PASS] * clean + [FAIL] * (total - clean))
                score, band = result.fusion.score, result.fusion.band

                self.assertAlmostEqual(score, 10.0 * clean / total)
                self.assertEqual(band, "Good" if score > 5.0 else "Poor")

    def test_the_exact_boundary_is_a_tie_and_bands_poor(self) -> None:
        result = _score([PASS] * 5 + [FAIL] * 5)

        self.assertAlmostEqual(result.fusion.score, 5.0)
        self.assertEqual(
            result.fusion.band, "Poor"
        )  # strict majority: 5.0 is not > 5.0

    def test_gated_and_model_rejected_reps_both_lower_the_score_identically(
        self,
    ) -> None:
        """A rep that fails a gate and a rep the model rejects are both "not clean" —
        the score does not rank one worse than the other, it just counts."""
        by_gate = _score([PASS] * 4, gates={0: ("heel_lift",), 1: ("heel_lift",)})
        by_model = _score([PASS, PASS, FAIL, FAIL])

        self.assertAlmostEqual(by_gate.fusion.score, by_model.fusion.score)
        self.assertAlmostEqual(by_gate.fusion.score, 5.0)


class NonVotingExercisesAreUntouchedTests(unittest.TestCase):
    def test_a_policy_without_aggregation_keeps_first_vector_scoring(self) -> None:
        result = _score([FAIL, PASS, PASS], policy=LEGACY_POLICY)

        self.assertEqual(result.rep_verdicts, ())
        self.assertAlmostEqual(result.fusion.ml_score, 10.0 * FAIL)
        self.assertEqual(result.fusion.band, "Poor")

    def test_no_band_policy_at_all_keeps_the_three_band_abstention(self) -> None:
        result = _score([FAIL] * 3, policy=None)

        self.assertEqual(result.rep_verdicts, ())
        self.assertIn(result.fusion.band, {"Good", "Fair", "Poor"})

    def test_a_placeholder_model_never_votes(self) -> None:
        result = _score([PASS] * 3, model=_PlaceholderModel())

        self.assertEqual(result.rep_verdicts, ())
        self.assertTrue(result.fusion.is_placeholder_model)


class FailedGatesByRepTests(unittest.TestCase):
    class _Check:
        def __init__(self, rep_index: int, tag: str) -> None:
            self.rep_index = rep_index
            self.tag = tag

    class _Result:
        def __init__(self, failed) -> None:
            self.failed = tuple(failed)
            self.all_passed = not failed

    def test_none_and_all_passed_both_yield_no_gates(self) -> None:
        self.assertEqual(failed_gates_by_rep(None), {})
        self.assertEqual(failed_gates_by_rep(self._Result([])), {})

    def test_failures_group_by_rep_sorted_and_deduplicated(self) -> None:
        grouped = failed_gates_by_rep(
            self._Result(
                [
                    self._Check(2, "heel_lift"),
                    self._Check(0, "insufficient_depth"),
                    self._Check(2, "excessive_forward_lean"),
                    self._Check(2, "heel_lift"),
                ]
            )
        )

        self.assertEqual(
            grouped,
            {
                0: ("insufficient_depth",),
                2: ("excessive_forward_lean", "heel_lift"),
            },
        )


if __name__ == "__main__":
    unittest.main()
