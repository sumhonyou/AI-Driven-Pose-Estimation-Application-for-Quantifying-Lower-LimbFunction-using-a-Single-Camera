"""Shared `{summary, tips}` feedback JSON contract tests."""

from __future__ import annotations

import unittest

from app.module_b.core.feedback_contract import (
    RewrittenFeedback,
    build,
    joined_text,
    parse,
    serialize,
)


class SerializeRoundTripTests(unittest.TestCase):
    def test_serialize_then_parse_recovers_the_same_value(self) -> None:
        feedback = build("Grade: Good.", ["Nice tempo.", "Keep your chest up."])

        parsed = parse(serialize(feedback))

        self.assertEqual(parsed, feedback)

    def test_serialize_is_deterministic(self) -> None:
        feedback = build("Grade: Good.", ["A tip."])
        self.assertEqual(serialize(feedback), serialize(feedback))


class ParseValidationTests(unittest.TestCase):
    def test_plain_prose_is_rejected(self) -> None:
        self.assertIsNone(parse("Great set! Keep it up."))

    def test_not_a_json_object_is_rejected(self) -> None:
        self.assertIsNone(parse('["summary", "tips"]'))
        self.assertIsNone(parse('"just a string"'))
        self.assertIsNone(parse("42"))

    def test_missing_summary_is_rejected(self) -> None:
        self.assertIsNone(parse('{"tips": ["a tip"]}'))

    def test_missing_tips_is_rejected(self) -> None:
        self.assertIsNone(parse('{"summary": "Grade: Good."}'))

    def test_blank_summary_is_rejected(self) -> None:
        self.assertIsNone(parse('{"summary": "   ", "tips": []}'))

    def test_non_string_tip_is_rejected(self) -> None:
        self.assertIsNone(parse('{"summary": "Grade: Good.", "tips": [1, 2]}'))

    def test_blank_tip_is_rejected(self) -> None:
        self.assertIsNone(parse('{"summary": "Grade: Good.", "tips": [""]}'))

    def test_empty_tips_list_is_valid(self) -> None:
        parsed = parse('{"summary": "Grade: Good.", "tips": []}')
        self.assertEqual(parsed, RewrittenFeedback(summary="Grade: Good.", tips=()))

    def test_garbage_is_rejected_not_raised(self) -> None:
        # Must never throw -- callers treat parse() as a total function.
        self.assertIsNone(parse(""))
        self.assertIsNone(parse("{"))
        self.assertIsNone(parse("not json at all {{{"))


class CodeFenceToleranceTests(unittest.TestCase):
    """LLMs routinely wrap JSON in ```-fences despite being told not to; this is a
    cosmetic habit to tolerate here, not a contract violation -- markdown CONTENT
    inside summary/tips is a separate, content-policy concern for feedback_safety."""

    def test_json_fence_is_stripped(self) -> None:
        text = '```json\n{"summary": "Grade: Good.", "tips": []}\n```'
        self.assertEqual(
            parse(text), RewrittenFeedback(summary="Grade: Good.", tips=())
        )

    def test_bare_fence_is_stripped(self) -> None:
        text = '```\n{"summary": "Grade: Good.", "tips": []}\n```'
        self.assertEqual(
            parse(text), RewrittenFeedback(summary="Grade: Good.", tips=())
        )


class JoinedTextTests(unittest.TestCase):
    def test_joins_summary_and_tips_with_spaces(self) -> None:
        feedback = build("Grade: Good.", ["Tip one.", "Tip two."])
        self.assertEqual(joined_text(feedback), "Grade: Good. Tip one. Tip two.")

    def test_empty_tips_joins_to_just_the_summary(self) -> None:
        feedback = build("Grade: Good.", [])
        self.assertEqual(joined_text(feedback), "Grade: Good.")


if __name__ == "__main__":
    unittest.main()
