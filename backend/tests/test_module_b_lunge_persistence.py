"""Stage 4.6 (Lunge) persistence-shape and deterministic read-back tests.

No shared-table/migration delta from squat's Stage 4.6 (`module_b_results` /
`module_b_error_tags` are already exercise-agnostic, keyed by a plain
`exercise_code` string). The real, lunge-specific finding this stage caught:
`core/crud.py::_metrics_json()` persisted each rep's `FeatureVector` without its
`lead_leg` metadata -- harmless for squat (always `None`), but a real bug for
lunge, since a stored session's cross-rep Symmetry sub-score can only be
reproduced later (a future replay harness, Stage 5.7 (Lunge)) if `lead_leg`
survives the round-trip. Fixed by adding one field to the existing shared
serialization; covered here rather than left for Stage 5.7 to discover.
"""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from uuid import uuid4

from app.module_b.core.config import MODULE_B_CORE_CONFIG
from app.module_b.core.crud import ErrorTagWrite, save_result
from app.module_b.core.features import FeatureVector
from app.module_b.core.fsm import Rep
from app.module_b.core.fusion import FusionResult
from app.module_b.core.rules import SubScore, assemble_rule_scores
from app.module_b.lunge.features import LUNGE_FEATURE_NAMES
from app.module_b.lunge.rules import SYMMETRY_CODE, score_lunge_set


def _lunge_feature_vector(lead_leg: str, peak_flexion: float) -> FeatureVector:
    values = {name: 0.0 for name in LUNGE_FEATURE_NAMES}
    values["front_knee_flex_peak_deg"] = peak_flexion
    return FeatureVector(
        schema_version=MODULE_B_CORE_CONFIG["feature_schema_version"],
        names=LUNGE_FEATURE_NAMES,
        values=tuple(values[name] for name in LUNGE_FEATURE_NAMES),
        lead_leg=lead_leg,
    )


def _rep(index: int) -> Rep:
    return Rep(
        frames=(),
        start_timestamp_s=float(index),
        end_timestamp_s=float(index) + 1.0,
        peak_signal_frame_index=0,
        peak_signal_value=90.0,
    )


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


class LungePersistenceTests(unittest.TestCase):
    def _save_two_leg_set(self) -> dict:
        db = _FakeDb()
        session = SimpleNamespace(id=uuid4(), status="started", score=None, band=None)
        left_rep, right_rep = _lunge_feature_vector(
            "left", 90.0
        ), _lunge_feature_vector("right", 80.0)
        fusion = FusionResult(
            score=6.0,
            band="Fair",
            rule_score=8.0,
            ml_score=5.0,
            confidence=0.5,
            q=0.9,
            w_rule=0.7,
            w_ml=0.3,
            flags=("low_confidence",),
            model_version="stub-0",
            is_placeholder_model=True,
            placeholder_model_notice=True,
        )
        rule_scores = score_lunge_set([left_rep, right_rep])

        result = save_result(
            db,
            session=session,
            exercise_code="lunge",
            fusion=fusion,
            rule_scores=rule_scores,
            feature_vectors=[left_rep, right_rep],
            reps=[_rep(0), _rep(1)],
            quality={
                "q": 0.9,
                "valid_frame_ratio": 1.0,
                "capture_quality_band": "good",
            },
            error_tags=[ErrorTagWrite("low_confidence", "medium", "system")],
        )
        return {"db": db, "session": session, "result": result}

    def test_save_result_records_snapshot_without_raw_frames(self) -> None:
        saved = self._save_two_leg_set()

        self.assertTrue(saved["db"].committed)
        self.assertEqual(saved["session"].status, "completed")
        self.assertEqual(saved["session"].rep_count, 2)
        self.assertEqual(saved["result"].exercise_code, "lunge")
        self.assertNotIn("worldLandmarks", json.dumps(saved["result"].metrics_json))

    def test_lead_leg_survives_the_persist_round_trip(self) -> None:
        """The finding this stage caught: without this, a stored lunge session's
        Symmetry sub-score could never be reproduced from its persisted snapshot."""
        result = self._save_two_leg_set()["result"]

        persisted_vectors = result.metrics_json["feature_vectors"]
        self.assertEqual([v["lead_leg"] for v in persisted_vectors], ["left", "right"])

    def test_reconstructed_feature_vectors_reproduce_the_original_symmetry_metrics(
        self,
    ) -> None:
        """End-to-end proof, not just a key check: rebuild FeatureVectors the way
        a Stage 5.7 (Lunge) replay harness would (from the persisted dicts) and
        confirm score_lunge_set() reproduces the exact original Symmetry numbers."""
        saved = self._save_two_leg_set()
        original_metrics = (
            score_lunge_set(
                [
                    _lunge_feature_vector("left", 90.0),
                    _lunge_feature_vector("right", 80.0),
                ]
            )
            .by_code()[SYMMETRY_CODE]
            .metrics
        )

        reconstructed = [
            FeatureVector(
                schema_version=item["schema_version"],
                names=tuple(item["names"]),
                values=tuple(float(value) for value in item["values"]),
                lead_leg=item["lead_leg"],
            )
            for item in saved["result"].metrics_json["feature_vectors"]
        ]
        replayed_metrics = (
            score_lunge_set(reconstructed).by_code()[SYMMETRY_CODE].metrics
        )

        self.assertEqual(replayed_metrics, original_metrics)
        self.assertGreater(replayed_metrics["front_knee_peak_symmetry_index_pct"], 0.0)

    def test_squat_style_single_leg_vector_still_persists_lead_leg_as_none(
        self,
    ) -> None:
        """Regression guard: the new field must not change squat's own shape --
        a `lead_leg=None` vector (squat's only case) persists `null`, not a
        missing key or a crash."""
        db = _FakeDb()
        session = SimpleNamespace(id=uuid4(), status="started", score=None, band=None)
        squat_vector = FeatureVector(
            schema_version=MODULE_B_CORE_CONFIG["feature_schema_version"],
            names=("knee_flex_peak_deg",),
            values=(90.0,),
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
            model_version="squat-test-1",
            is_placeholder_model=False,
            placeholder_model_notice=False,
        )

        result = save_result(
            db,
            session=session,
            exercise_code="squat",
            fusion=fusion,
            rule_scores=assemble_rule_scores(SubScore("rom_completeness", 8.0)),
            feature_vectors=[squat_vector],
            reps=[_rep(0)],
            quality={
                "q": 0.9,
                "valid_frame_ratio": 1.0,
                "capture_quality_band": "good",
            },
            error_tags=[],
        )

        self.assertIsNone(result.metrics_json["feature_vectors"][0]["lead_leg"])


if __name__ == "__main__":
    unittest.main()
