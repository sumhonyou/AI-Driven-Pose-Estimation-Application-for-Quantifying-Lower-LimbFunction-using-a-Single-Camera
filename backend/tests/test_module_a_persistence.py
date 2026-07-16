"""Session-level persistence for the generic Module A save path (STS today)."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from uuid import uuid4

from app.module_a.core.crud import save_result


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


class ModuleAPersistenceTests(unittest.TestCase):
    def test_save_result_writes_rep_count_onto_the_session(self) -> None:
        """Mirrors the score/band denormalization already on `session` (Stage 4.6's
        Module B precedent) so the generic /api/sessions listing can show a rep
        count without a per-row metrics_json fetch."""
        db = _FakeDb()
        session = SimpleNamespace(
            id=uuid4(),
            status="started",
            score=None,
            band=None,
            capture_quality=None,
            valid_frame_ratio=None,
            rep_count=None,
        )
        engine_result = {
            "metrics": {
                "rep_count": 5,
                "target_rep_count": 5,
                "completion_time_sec": 12.0,
                "avg_trunk_lean_deg": 4.0,
            },
            "quality": {
                "average_visibility": 0.9,
                "valid_frame_ratio": 1.0,
                "quality_band": "good",
            },
        }
        band_result = {
            "score": 10.0,
            "band": "good",
            "warning_tags": [],
            "session_status": "completed",
            "is_partial_score": False,
        }

        save_result(db, session, engine_result, band_result)

        self.assertTrue(db.committed)
        self.assertEqual(session.status, "completed")
        self.assertEqual(session.rep_count, 5)


if __name__ == "__main__":
    unittest.main()
