"""Stage 4.6 persistence-shape and deterministic read-back tests."""

from __future__ import annotations

import json
import unittest
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.db.models import FeedbackText, ModuleBErrorTag, ModuleBResult
from app.module_b.core.config import MODULE_B_CORE_CONFIG
from app.module_b.core.crud import (
    ErrorTagWrite,
    FeedbackWrite,
    feedback_summary,
    result_summary,
    save_feedback,
    save_result,
)
from app.module_b.core.features import FeatureVector
from app.module_b.core.fsm import Rep
from app.module_b.core.fusion import FusionResult
from app.module_b.core.quality import assess_capture_quality
from app.module_b.core.rules import SubScore, assemble_rule_scores


def _frame(visibility: float) -> dict:
    landmarks = [
        {"x": 0.0, "y": 0.0, "z": 0.0, "visibility": visibility} for _ in range(33)
    ]
    return {"timestampMs": 0.0, "worldLandmarks": landmarks}


class _FakeDb:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.executed: list[object] = []
        self.committed = False

    def scalar(self, _statement):
        return None

    def add(self, item) -> None:
        self.added.append(item)

    def execute(self, statement) -> None:
        self.executed.append(statement)

    def commit(self) -> None:
        self.committed = True

    def refresh(self, _item) -> None:
        return None


class ModuleBQualityTests(unittest.TestCase):
    def test_bilateral_visibility_produces_q_and_valid_frame_ratio(self) -> None:
        quality = assess_capture_quality([_frame(1.0), _frame(0.5)])

        self.assertEqual(quality["q"], 0.75)
        self.assertEqual(quality["valid_frame_ratio"], 0.5)
        self.assertEqual(quality["capture_quality_band"], "moderate")


class ModuleBPersistenceTests(unittest.TestCase):
    def test_save_result_records_snapshot_without_raw_frames(self) -> None:
        db = _FakeDb()
        session = SimpleNamespace(id=uuid4(), status="started", score=None, band=None)
        feature_vector = FeatureVector(
            schema_version=MODULE_B_CORE_CONFIG["feature_schema_version"],
            names=("example",),
            values=(1.0,),
        )
        rep = Rep(
            frames=(),
            start_timestamp_s=0.0,
            end_timestamp_s=1.0,
            peak_signal_frame_index=0,
            peak_signal_value=90.0,
        )
        fusion = FusionResult(
            score=8.0,
            band="Good",
            rule_score=8.0,
            ml_score=8.0,
            confidence=0.8,
            q=0.9,
            w_rule=0.4,
            w_ml=0.6,
            flags=(),
            model_version="stub-0",
            is_placeholder_model=True,
            placeholder_model_notice=True,
        )

        result = save_result(
            db,
            session=session,
            exercise_code="squat",
            fusion=fusion,
            rule_scores=assemble_rule_scores(SubScore("rom_completeness", 8.0)),
            feature_vectors=[feature_vector],
            reps=[rep],
            quality={
                "q": 0.9,
                "valid_frame_ratio": 1.0,
                "capture_quality_band": "good",
            },
            error_tags=[ErrorTagWrite("low_confidence", "medium", "system")],
        )

        self.assertTrue(db.committed)
        self.assertEqual(session.status, "completed")
        self.assertEqual(session.rep_count, 1)
        self.assertEqual(result.model_version, "stub-0")
        self.assertEqual(
            result.metrics_json["fusion_weights"], {"w_rule": 0.4, "w_ml": 0.6}
        )
        self.assertNotIn("worldLandmarks", json.dumps(result.metrics_json))

    def test_read_back_payload_is_byte_stable_and_tags_are_sorted(self) -> None:
        session_id = uuid4()
        result = ModuleBResult(
            session_id=session_id,
            exercise_code="squat",
            score=8.0,
            band="Good",
            confidence=0.8,
            model_version="stub-0",
            feature_schema_version="1.0.0",
            q=0.9,
            metrics_json={"fusion_weights": {"w_rule": 0.4, "w_ml": 0.6}},
            created_at=datetime(2026, 7, 16, tzinfo=UTC),
        )
        tags = [
            ModuleBErrorTag(
                session_id=session_id, tag="z_tag", severity="low", source="system"
            ),
            ModuleBErrorTag(
                session_id=session_id, tag="a_tag", severity="high", source="rule"
            ),
        ]

        first = json.dumps(result_summary(result, tags), separators=(",", ":"))
        second = json.dumps(
            result_summary(result, list(reversed(tags))), separators=(",", ":")
        )

        self.assertEqual(first, second)
        self.assertIn('"tag":"a_tag"', first)


class FeedbackPersistenceTests(unittest.TestCase):
    def test_save_feedback_records_template_row(self) -> None:
        db = _FakeDb()
        session_id = uuid4()

        row = save_feedback(
            db,
            session_id=session_id,
            feedback=FeedbackWrite(
                structured_feedback="Grade: Needs Improvement. Didn't reach enough depth.",
                rewritten_feedback="Grade: Needs Improvement. Didn't reach enough depth.",
                feedback_source="template",
                llm_attempted=False,
                disclaimer_version="v1",
            ),
        )

        self.assertTrue(db.committed)
        self.assertEqual(row.session_id, session_id)
        self.assertEqual(row.feedback_source, "template")
        self.assertFalse(row.llm_attempted)
        self.assertIsNone(row.provider)
        self.assertEqual(row.disclaimer_version, "v1")

    def test_feedback_summary_shape(self) -> None:
        row = FeedbackText(
            session_id=uuid4(),
            structured_feedback="Grade: Good. No specific issues were flagged.",
            rewritten_feedback="Grade: Good. No specific issues were flagged.",
            feedback_source="template",
            llm_attempted=False,
            provider=None,
            model_version=None,
            disclaimer_version="v1",
        )

        summary = feedback_summary(row)

        self.assertEqual(summary["feedback_source"], "template")
        self.assertFalse(summary["llm_attempted"])
        self.assertEqual(summary["disclaimer_version"], "v1")

    def test_feedback_summary_none_when_never_saved(self) -> None:
        self.assertIsNone(feedback_summary(None))


if __name__ == "__main__":
    unittest.main()
