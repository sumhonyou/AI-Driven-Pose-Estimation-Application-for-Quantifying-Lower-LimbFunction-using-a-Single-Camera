"""Unit tests for the pure-Python agreement statistics (ICC, Bland-Altman, kappa).

Uses hand-verifiable boundary cases (perfect agreement, chance-level agreement,
manually-computed small examples) rather than a reference implementation, since
this project has no numpy/scipy/pingouin dependency to compare against.
"""

import unittest

from app.module_a.sls.evaluation.agreement import bland_altman, cohens_kappa, icc_2_1


class IccTests(unittest.TestCase):
    def test_perfect_agreement_is_one(self):
        system = [10.0, 20.0, 30.0, 15.0, 25.0]
        manual = [10.0, 20.0, 30.0, 15.0, 25.0]
        self.assertAlmostEqual(icc_2_1(system, manual), 1.0, places=6)

    def test_constant_offset_reduces_absolute_agreement(self):
        # ICC(2,1) is an ABSOLUTE agreement measure: a constant +5s system bias
        # must pull the score below 1.0, unlike a "consistency" ICC(3,1) which
        # would ignore the offset. This is exactly why ICC(2,1) was chosen.
        system = [15.0, 25.0, 35.0, 20.0, 30.0]
        manual = [10.0, 20.0, 30.0, 15.0, 25.0]
        score = icc_2_1(system, manual)
        self.assertLess(score, 1.0)
        self.assertGreater(score, -1.0)

    def test_no_between_subject_signal_gives_no_positive_agreement(self):
        # Both raters are just noise around the SAME constant baseline (20) --
        # there is no true per-subject signal, so ICC(2,1) should show no
        # meaningful positive agreement (it can legitimately go slightly
        # negative here; that is a standard, valid ICC(2,1) outcome).
        system = [25.0, 17.0, 28.0, 14.0, 22.0, 11.0, 24.0]
        manual = [16.0, 29.0, 13.0, 23.0, 12.0, 26.0, 18.0]
        score = icc_2_1(system, manual)
        self.assertLess(score, 0.3)

    def test_requires_matching_lengths(self):
        with self.assertRaises(ValueError):
            icc_2_1([1.0, 2.0], [1.0])


class BlandAltmanTests(unittest.TestCase):
    def test_manual_hand_computed_example(self):
        # diffs = [0, 0, -1] -> mean = -1/3, sample sd (n-1=2) = sqrt(((0-(-1/3))^2*2 + (-1-(-1/3))^2)/2)
        system = [1.0, 2.0, 3.0]
        manual = [1.0, 2.0, 4.0]
        result = bland_altman(system, manual)
        self.assertAlmostEqual(result["bias_sec"], -0.333, places=2)
        self.assertAlmostEqual(result["sd_sec"], 0.577, places=2)
        self.assertAlmostEqual(
            result["loa_upper_sec"] - result["loa_lower_sec"],
            2 * 1.96 * result["sd_sec"],
            places=2,
        )

    def test_zero_bias_when_identical(self):
        result = bland_altman([5.0, 10.0, 15.0], [5.0, 10.0, 15.0])
        self.assertEqual(result["bias_sec"], 0.0)
        self.assertEqual(result["sd_sec"], 0.0)

    def test_requires_matching_lengths(self):
        with self.assertRaises(ValueError):
            bland_altman([1.0], [1.0, 2.0])


class CohensKappaTests(unittest.TestCase):
    def test_perfect_agreement_is_one(self):
        labels = ["good", "fair", "poor", "good", "invalid"]
        self.assertAlmostEqual(cohens_kappa(labels, labels), 1.0, places=6)

    def test_chance_level_agreement_is_near_zero(self):
        # Constructed so observed agreement exactly equals chance-expected
        # agreement: 2 categories, 50/50 marginals both sides, half overlap.
        system_labels = ["good", "good", "poor", "poor"]
        manual_labels = ["good", "poor", "good", "poor"]
        self.assertAlmostEqual(
            cohens_kappa(system_labels, manual_labels), 0.0, places=6
        )

    def test_disagreement_below_chance_is_negative(self):
        system_labels = ["good", "good", "poor", "poor"]
        manual_labels = ["poor", "poor", "good", "good"]
        self.assertLess(cohens_kappa(system_labels, manual_labels), 0.0)

    def test_requires_matching_lengths(self):
        with self.assertRaises(ValueError):
            cohens_kappa(["good"], ["good", "poor"])


if __name__ == "__main__":
    unittest.main()
