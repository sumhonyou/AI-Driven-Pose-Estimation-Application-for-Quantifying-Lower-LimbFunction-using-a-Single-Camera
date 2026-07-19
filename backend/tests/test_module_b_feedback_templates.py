"""Stage 6.2: the deterministic template fallback, built and proven before any LLM code."""

from __future__ import annotations

import unittest

from app.module_b.core.feedback import build_structured_feedback
from app.module_b.core.feedback_templates import compose_template


def _summary(band="Poor", tags=None, **overrides):
    summary = {
        "band": band,
        "score": 5.0,
        "confidence": 0.62,
        "metrics": {
            "rule_subscores": [
                {"code": "rom_completeness", "score": 8.0},
                {"code": "tempo_consistency", "score": 4.0},
                {"code": "stability_control", "score": 7.0},
            ],
            "per_rep_summaries": [{"duration_s": 1.0}, {"duration_s": 1.2}],
        },
        "error_tags": tags if tags is not None else [],
    }
    summary.update(overrides)
    return summary


class BandLabelTests(unittest.TestCase):
    def test_poor_relabels_to_needs_improvement(self) -> None:
        text = compose_template(build_structured_feedback(_summary(band="Poor")))
        self.assertTrue(text.startswith("Grade: Needs Improvement."))

    def test_good_stays_good(self) -> None:
        text = compose_template(build_structured_feedback(_summary(band="Good")))
        self.assertTrue(text.startswith("Grade: Good."))

    def test_missing_band_is_unavailable(self) -> None:
        text = compose_template(build_structured_feedback(_summary(band=None)))
        self.assertTrue(text.startswith("Grade: Unavailable."))


class TagMessageTests(unittest.TestCase):
    def test_no_tags_uses_fallback_sentence(self) -> None:
        text = compose_template(build_structured_feedback(_summary(tags=[])))
        self.assertIn("No specific issues were flagged for this set.", text)

    def test_top_two_tags_quoted_in_severity_order(self) -> None:
        tags = [
            {
                "tag": "inconsistent_tempo",
                "severity": "low",
                "source": "rule",
                "message": "pace",
            },
            {
                "tag": "insufficient_depth",
                "severity": "high",
                "source": "rule",
                "message": "depth",
            },
            {
                "tag": "low_confidence",
                "severity": "medium",
                "source": "system",
                "message": "conf",
            },
        ]
        text = compose_template(build_structured_feedback(_summary(tags=tags)))
        self.assertIn("depth", text)
        self.assertIn("conf", text)
        self.assertNotIn(
            "pace", text
        )  # third-ranked tag is dropped by the 2-message cap

    def test_tag_without_message_is_skipped_not_blank(self) -> None:
        tags = [
            {"tag": "mystery", "severity": "high", "source": "rule", "message": None}
        ]
        text = compose_template(build_structured_feedback(_summary(tags=tags)))
        self.assertIn("No specific issues were flagged for this set.", text)
        self.assertNotIn("None", text)


class DeterminismTests(unittest.TestCase):
    def test_same_input_produces_byte_identical_output(self) -> None:
        summary = _summary(
            tags=[
                {
                    "tag": "excessive_forward_lean",
                    "severity": "high",
                    "source": "rule",
                    "message": "Leaning too far forward — keep your chest more upright.",
                }
            ]
        )
        first = compose_template(build_structured_feedback(summary))
        second = compose_template(build_structured_feedback(summary))
        self.assertEqual(first, second)


class TemplateGateTests(unittest.TestCase):
    """Stage 6.2's GATE: the full report is composable with the LLM disabled — before
    any API-client code exists (Stage 6.4 is deliberately built last, see task.md)."""

    def test_full_squat_report_composes_with_no_llm_or_network_involved(self) -> None:
        # A realistic post-analyze summary: system tag + a fired fault gate + the new
        # soft tempo tag together, exactly as `crud.result_summary` would shape it.
        summary = _summary(
            band="Poor",
            tags=[
                {
                    "tag": "insufficient_depth",
                    "severity": "high",
                    "source": "rule",
                    "message": "Didn't reach enough depth — aim for closer to parallel.",
                },
                {
                    "tag": "inconsistent_tempo",
                    "severity": "low",
                    "source": "rule",
                    "message": "Aim for a steadier pace across your reps.",
                },
                {
                    "tag": "low_confidence",
                    "severity": "medium",
                    "source": "system",
                    "message": "Model confidence was low for this set.",
                },
            ],
        )
        structured = build_structured_feedback(summary)
        rendered = compose_template(structured)

        self.assertTrue(rendered.startswith("Grade: Needs Improvement."))
        self.assertIn(
            "Didn't reach enough depth", rendered
        )  # highest-severity tag leads
        self.assertNotIn("None", rendered)
        self.assertGreater(len(rendered), 0)
        # No import of any LLM/config module was needed to produce this — pure function
        # of already-persisted data. Stage 6.4 has not been built yet at this point in
        # the plan and this test still passes, proving the report never depends on it.


if __name__ == "__main__":
    unittest.main()
