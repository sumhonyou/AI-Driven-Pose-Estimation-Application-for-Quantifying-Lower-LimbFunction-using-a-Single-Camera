"""Deterministic structured-feedback builder tests."""

from __future__ import annotations

import unittest

from app.module_b.core.feedback import build_structured_feedback


def _summary(**overrides):
    summary = {
        "band": "Poor",
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
        "error_tags": [
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
                "message": None,
            },
        ],
    }
    summary.update(overrides)
    return summary


class StructuredFeedbackTests(unittest.TestCase):
    def test_passthrough_fields(self) -> None:
        fb = build_structured_feedback(_summary())
        self.assertEqual(fb.band, "Poor")
        self.assertEqual(fb.score, 5.0)
        self.assertEqual(fb.confidence, 0.62)
        self.assertEqual(fb.rep_count, 2)
        self.assertEqual(len(fb.sub_scores), 3)

    def test_tags_ranked_high_to_low(self) -> None:
        fb = build_structured_feedback(_summary())
        self.assertEqual(
            [t.tag for t in fb.tags],
            ["insufficient_depth", "low_confidence", "inconsistent_tempo"],
        )

    def test_deterministic_tiebreak_on_tag_name(self) -> None:
        summary = _summary(
            error_tags=[
                {
                    "tag": "heel_lift",
                    "severity": "high",
                    "source": "rule",
                    "message": None,
                },
                {
                    "tag": "excessive_forward_lean",
                    "severity": "high",
                    "source": "rule",
                    "message": None,
                },
            ]
        )
        fb = build_structured_feedback(summary)
        self.assertEqual(
            [t.tag for t in fb.tags], ["excessive_forward_lean", "heel_lift"]
        )

    def test_empty_result_is_safe(self) -> None:
        fb = build_structured_feedback({})
        self.assertIsNone(fb.band)
        self.assertEqual(fb.rep_count, 0)
        self.assertEqual(fb.tags, ())
        self.assertEqual(fb.sub_scores, ())


if __name__ == "__main__":
    unittest.main()
