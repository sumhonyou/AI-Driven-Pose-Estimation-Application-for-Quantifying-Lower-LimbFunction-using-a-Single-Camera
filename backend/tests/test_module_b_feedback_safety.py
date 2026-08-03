"""LLM feedback safety-filter tests."""

from __future__ import annotations

import json
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


def _candidate(summary: str, tips: list[str] | None = None) -> str:
    """Build a `feedback_contract`-shaped JSON string, the only thing
    `check_llm_feedback` now accepts as input."""
    return json.dumps({"summary": summary, "tips": tips or []})


class AcceptedCandidateTests(unittest.TestCase):
    def test_plain_matching_rewrite_is_accepted(self) -> None:
        structured = _structured(band="Good", score=9.0)
        result = check_llm_feedback(
            _candidate("Great set! Your grade was good overall — keep it up."),
            structured=structured,
        )
        self.assertTrue(result.accepted)
        self.assertIsNone(result.reason)

    def test_poor_relabelled_as_needs_improvement_is_not_a_false_mismatch(self) -> None:
        structured = _structured(band="Poor", score=5.0)
        result = check_llm_feedback(
            _candidate(
                "This set needs improvement — work on the flagged points below."
            ),
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
            _candidate(
                "This set needs improvement.",
                ["Your heels were lifting off the floor."],
            ),
            structured=structured,
        )
        self.assertTrue(result.accepted)


class ForbiddenPhraseTests(unittest.TestCase):
    def test_clinical_diagnosis_language_is_rejected(self) -> None:
        structured = _structured(band="Poor", score=5.0)
        result = check_llm_feedback(
            _candidate(
                "Based on this set, you have been clinically diagnosed with a knee issue."
            ),
            structured=structured,
        )
        self.assertFalse(result.accepted)
        self.assertIn("forbidden_phrase", result.reason)


class GradeIntegrityTests(unittest.TestCase):
    def test_adversarial_response_that_changes_the_grade_is_rejected(self) -> None:
        # The set was actually graded Poor; the candidate rewrite falsely claims Good.
        structured = _structured(band="Poor", score=5.0)
        candidate = _candidate(
            "Great job — your squat form was good throughout the set!"
        )

        result = check_llm_feedback(candidate, structured=structured)

        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "grade_mismatch_band")
        # And the caller's fallback path must show the true grade, not the LLM's claim.
        fallback = compose_template(structured)
        self.assertIn("Needs Improvement", fallback.summary)
        self.assertNotIn("good throughout", fallback.summary)

    def test_score_contradiction_is_rejected(self) -> None:
        structured = _structured(band="Poor", score=5.0)
        result = check_llm_feedback(
            _candidate("This set scored 8/10, a strong effort overall."),
            structured=structured,
        )
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "grade_mismatch_score")

    def test_score_within_tolerance_is_accepted(self) -> None:
        structured = _structured(band="Poor", score=5.0)
        result = check_llm_feedback(
            _candidate("This set scored 5.0/10 — needs improvement."),
            structured=structured,
        )
        self.assertTrue(result.accepted)


class TagIntegrityTests(unittest.TestCase):
    def test_unflagged_known_tag_is_rejected(self) -> None:
        # heel_lift was never flagged for this set; the model invents it anyway.
        structured = _structured(band="Poor", score=5.0, tags=[])
        result = check_llm_feedback(
            _candidate(
                "A solid effort overall.",
                ["Watch your heel lift next time."],
            ),
            structured=structured,
        )
        self.assertFalse(result.accepted)
        self.assertIn("invented_tag", result.reason)


class LengthCapTests(unittest.TestCase):
    def test_overlong_candidate_is_rejected(self) -> None:
        structured = _structured(band="Good", score=9.0)
        candidate = _candidate(
            "Good work. " * (MAX_REWRITE_LENGTH // len("Good work. ") + 5)
        )
        result = check_llm_feedback(candidate, structured=structured)
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "too_long")

    def test_empty_candidate_is_rejected(self) -> None:
        structured = _structured(band="Good", score=9.0)
        result = check_llm_feedback("   ", structured=structured)
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "empty")


class JsonContractTests(unittest.TestCase):
    """Stage 5.17: the candidate must be the `feedback_contract` JSON shape."""

    def test_plain_prose_with_no_json_envelope_is_rejected(self) -> None:
        structured = _structured(band="Good", score=9.0)
        result = check_llm_feedback(
            "Great set! Your grade was good overall.", structured=structured
        )
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "invalid_json")

    def test_missing_tips_key_is_rejected(self) -> None:
        structured = _structured(band="Good", score=9.0)
        result = check_llm_feedback(
            json.dumps({"summary": "Great set!"}), structured=structured
        )
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "invalid_json")


class MarkdownFormattingTests(unittest.TestCase):
    """Stage 5.17: the concrete bug this stage fixes — literal '* ' bullets and other
    markdown rendering inline instead of as a real list."""

    def test_asterisk_bullet_in_a_tip_is_rejected(self) -> None:
        structured = _structured(band="Good", score=9.0)
        result = check_llm_feedback(
            _candidate("Great set overall.", ["* Keep your chest up next time."]),
            structured=structured,
        )
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "markdown_formatting")

    def test_bold_markup_in_the_summary_is_rejected(self) -> None:
        structured = _structured(band="Good", score=9.0)
        result = check_llm_feedback(
            _candidate("**Great set** overall."), structured=structured
        )
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "markdown_formatting")

    def test_numbered_list_marker_in_a_tip_is_rejected(self) -> None:
        structured = _structured(band="Good", score=9.0)
        result = check_llm_feedback(
            _candidate("Great set overall.", ["1. Keep your chest up next time."]),
            structured=structured,
        )
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "markdown_formatting")

    def test_plain_prose_tips_are_accepted(self) -> None:
        structured = _structured(band="Good", score=9.0)
        result = check_llm_feedback(
            _candidate(
                "Great set overall.",
                ["Keep your chest up next time.", "Nice steady pace."],
            ),
            structured=structured,
        )
        self.assertTrue(result.accepted)


if __name__ == "__main__":
    unittest.main()
