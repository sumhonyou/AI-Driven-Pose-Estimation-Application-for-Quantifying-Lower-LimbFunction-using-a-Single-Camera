"""Stage 6.5: wiring the feedback builder into the analyze flow, and the 3-state
feedback_source/llm_attempted distinction the stored row must be able to represent."""

from __future__ import annotations

import unittest
from unittest.mock import patch
from uuid import uuid4

from app.module_b.core.crud import FeedbackWrite, feedback_summary, save_feedback
from app.module_b.core.router import _build_and_save_feedback


class _FakeDb:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.committed = False

    def scalar(self, _statement):
        return None

    def add(self, item) -> None:
        self.added.append(item)

    def commit(self) -> None:
        self.committed = True

    def refresh(self, _item) -> None:
        return None


def _summary(band="Poor", score=5.0, tags=None):
    return {
        "band": band,
        "score": score,
        "confidence": 0.62,
        "metrics": {
            "rule_subscores": [],
            "per_rep_summaries": [{"duration_s": 1.0}, {"duration_s": 1.2}],
        },
        "error_tags": tags or [],
    }


class BuildAndSaveFeedbackTests(unittest.TestCase):
    """Forces `feedback_llm_enabled=False` regardless of the developer's local `.env`
    (Stage 6.4 made this a real, developer-toggleable flag) -- these tests exercise the
    template-only path specifically and must not flip behaviour, or make a live network
    call, just because someone's `backend/.env` has the LLM turned on for manual testing.
    """

    def setUp(self) -> None:
        patcher = patch("app.module_b.core.router.settings.feedback_llm_enabled", False)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_composes_template_and_persists_it(self) -> None:
        db = _FakeDb()
        summary = _summary(
            tags=[
                {
                    "tag": "insufficient_depth",
                    "severity": "high",
                    "source": "rule",
                    "message": "Didn't reach enough depth — aim for closer to parallel.",
                }
            ]
        )

        feedback = _build_and_save_feedback(db, session_id=uuid4(), summary=summary)

        self.assertTrue(db.committed)
        self.assertEqual(feedback["feedback_source"], "template")
        self.assertFalse(feedback["llm_attempted"])
        self.assertIn("Needs Improvement", feedback["rewritten_feedback"])
        self.assertIn("depth", feedback["rewritten_feedback"])
        # structured/rewritten are identical with the LLM disabled for this test.
        self.assertEqual(
            feedback["structured_feedback"], feedback["rewritten_feedback"]
        )

    def test_never_mutates_the_result_summarys_grade(self) -> None:
        db = _FakeDb()
        summary = _summary(band="Good", score=9.4)
        before = (summary["band"], summary["score"])

        _build_and_save_feedback(db, session_id=uuid4(), summary=summary)

        # Grade byte-identical before/after feedback composition (X5): the feedback
        # layer only reads the summary, it never writes back into it.
        self.assertEqual((summary["band"], summary["score"]), before)


class ThreeStateFeedbackSourceTests(unittest.TestCase):
    """The stored row must distinguish "never tried" from "tried and rejected" from
    "tried and used" -- exactly what the old llm_used boolean collapsed (see the
    migration docstring). Stage 6.4 will drive the latter two; verified here at the
    persistence layer since no LLM client exists yet to drive it end-to-end."""

    def test_never_attempted(self) -> None:
        db = _FakeDb()
        row = save_feedback(
            db,
            session_id=uuid4(),
            feedback=FeedbackWrite(
                structured_feedback="Grade: Good. No specific issues were flagged.",
                rewritten_feedback="Grade: Good. No specific issues were flagged.",
                feedback_source="template",
                llm_attempted=False,
            ),
        )
        summary = feedback_summary(row)
        self.assertEqual(summary["feedback_source"], "template")
        self.assertFalse(summary["llm_attempted"])

    def test_attempted_and_rejected_falls_back_to_template(self) -> None:
        db = _FakeDb()
        row = save_feedback(
            db,
            session_id=uuid4(),
            feedback=FeedbackWrite(
                structured_feedback="Grade: Poor. Didn't reach enough depth.",
                rewritten_feedback="Grade: Poor. Didn't reach enough depth.",
                feedback_source="template",
                llm_attempted=True,
                provider="groq",
            ),
        )
        summary = feedback_summary(row)
        self.assertEqual(summary["feedback_source"], "template")
        self.assertTrue(summary["llm_attempted"])

    def test_attempted_and_used(self) -> None:
        db = _FakeDb()
        row = save_feedback(
            db,
            session_id=uuid4(),
            feedback=FeedbackWrite(
                structured_feedback="Grade: Poor. Didn't reach enough depth.",
                rewritten_feedback="This set needs a bit more depth next time.",
                feedback_source="llm",
                llm_attempted=True,
                provider="groq",
                model_version="llama-3.3-70b",
            ),
        )
        summary = feedback_summary(row)
        self.assertEqual(summary["feedback_source"], "llm")
        self.assertTrue(summary["llm_attempted"])
        self.assertEqual(summary["provider"], "groq")


if __name__ == "__main__":
    unittest.main()
