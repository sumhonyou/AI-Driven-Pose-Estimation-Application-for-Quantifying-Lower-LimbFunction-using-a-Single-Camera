"""Stage 6.3: the safety filter — grade integrity, tag integrity, forbidden phrases, length."""

from __future__ import annotations

import unittest

from app.module_b.core.feedback import build_structured_feedback
from app.module_b.core.feedback_safety import (
    MAX_REWRITE_LENGTH,
    check_llm_feedback,
)
from app.module_b.core.feedback_templates import compose_template


def _structured(band="Poor", score=5.0, tags=None):
    summary = {
        "band": band,
        "score": score,
        "confidence": 0.62,
        "metrics": {"rule_subscores": [], "per_rep_summaries": [{}, {}]},
        "error_tags": tags or [],
    }
    return build_structured_feedback(summary)


class AcceptedCandidateTests(unittest.TestCase):
    def test_plain_matching_rewrite_is_accepted(self) -> None:
        structured = _structured(band="Good", score=9.0)
        result = check_llm_feedback(
            "Great set! Your grade was good overall — keep it up.",
            structured=structured,
        )
        self.assertTrue(result.accepted)
        self.assertIsNone(result.reason)

    def test_poor_relabelled_as_needs_improvement_is_not_a_false_mismatch(self) -> None:
        structured = _structured(band="Poor", score=5.0)
        result = check_llm_feedback(
            "This set needs improvement — work on the flagged points below.",
            structured=structured,
        )
        self.assertTrue(result.accepted)

    def test_flagged_tag_mentioned_by_name_is_fine(self) -> None:
        structured = _structured(
            band="Poor",
            score=5.0,
            tags=[
                {
                    "tag": "heel_lift",
                    "severity": "high",
                    "source": "rule",
                    "message": "Heels lifting off the floor.",
                }
            ],
        )
        result = check_llm_feedback(
            "This set needs improvement — your heels were lifting off the floor.",
            structured=structured,
        )
        self.assertTrue(result.accepted)


class ForbiddenPhraseTests(unittest.TestCase):
    def test_clinical_diagnosis_language_is_rejected(self) -> None:
        structured = _structured(band="Poor", score=5.0)
        result = check_llm_feedback(
            "Based on this set, you have been clinically diagnosed with a knee issue.",
            structured=structured,
        )
        self.assertFalse(result.accepted)
        self.assertIn("forbidden_phrase", result.reason)


class GradeIntegrityTests(unittest.TestCase):
    def test_adversarial_response_that_changes_the_grade_is_rejected(self) -> None:
        # The set was actually graded Poor; the candidate rewrite falsely claims Good.
        structured = _structured(band="Poor", score=5.0)
        candidate = "Great job — your squat form was good throughout the set!"

        result = check_llm_feedback(candidate, structured=structured)

        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "grade_mismatch_band")
        # And the caller's fallback path must show the true grade, not the LLM's claim.
        fallback = compose_template(structured)
        self.assertIn("Needs Improvement", fallback)
        self.assertNotIn("good throughout", fallback)

    def test_score_contradiction_is_rejected(self) -> None:
        structured = _structured(band="Poor", score=5.0)
        result = check_llm_feedback(
            "This set scored 8/10, a strong effort overall.", structured=structured
        )
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "grade_mismatch_score")

    def test_score_within_tolerance_is_accepted(self) -> None:
        structured = _structured(band="Poor", score=5.0)
        result = check_llm_feedback(
            "This set scored 5.0/10 — needs improvement.", structured=structured
        )
        self.assertTrue(result.accepted)


class TagIntegrityTests(unittest.TestCase):
    def test_unflagged_known_tag_is_rejected(self) -> None:
        # heel_lift was never flagged for this set; the model invents it anyway.
        structured = _structured(band="Poor", score=5.0, tags=[])
        result = check_llm_feedback(
            "Watch your heel lift next time — otherwise a solid effort.",
            structured=structured,
        )
        self.assertFalse(result.accepted)
        self.assertIn("invented_tag", result.reason)


class LengthCapTests(unittest.TestCase):
    def test_overlong_candidate_is_rejected(self) -> None:
        structured = _structured(band="Good", score=9.0)
        candidate = "Good work. " * (MAX_REWRITE_LENGTH // len("Good work. ") + 5)
        result = check_llm_feedback(candidate, structured=structured)
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "too_long")

    def test_empty_candidate_is_rejected(self) -> None:
        structured = _structured(band="Good", score=9.0)
        result = check_llm_feedback("   ", structured=structured)
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "empty")


if __name__ == "__main__":
    unittest.main()
