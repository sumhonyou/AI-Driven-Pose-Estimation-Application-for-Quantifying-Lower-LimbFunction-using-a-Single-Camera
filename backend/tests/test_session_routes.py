"""Session lifecycle route tests (no DB / HTTP, matching the project's test style).

The live pages call `POST /api/sessions/{id}/end` *after* the analysis endpoint has
already graded and persisted the set, and every analysis path completes the session as
part of that persist. So `end` has to accept an already-completed session, or the user
is stranded on the live page with a graded set they can never navigate to.
"""

from __future__ import annotations

import unittest
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from fastapi import HTTPException

from app.api.session_routes import cancel_session, end_session
from app.db.schemas import SessionEnd


class _FakeDb:
    """Returns one preset session for any query and records commits."""

    def __init__(self, session) -> None:
        self._session = session
        self.commits = 0

    def scalar(self, _statement):
        return self._session

    def add(self, _item) -> None:
        pass

    def commit(self) -> None:
        self.commits += 1

    def refresh(self, _item) -> None:
        pass


def _session(status: str, *, ended_at: datetime | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        mode="patient",
        exercise=SimpleNamespace(code="squat", name="Squat"),
        exercise_type="squat",
        started_at=datetime(2026, 8, 13, tzinfo=UTC),
        ended_at=ended_at,
        status=status,
        capture_quality=Decimal("0.90"),
        valid_frame_ratio=Decimal("0.88"),
        score=Decimal("72.5"),
        band="Good",
        rep_count=10,
        target_rep_count=10,
    )


def _end(session) -> tuple[_FakeDb, object]:
    db = _FakeDb(session)
    payload = SessionEnd(capture_quality=0.25, valid_frame_ratio=0.25)
    user = SimpleNamespace(id=uuid4())
    return db, end_session(session.id, payload, db=db, current_user=user)


class EndSessionTests(unittest.TestCase):
    def test_in_progress_session_is_completed_with_client_quality(self):
        session = _session("in_progress")
        db, response = _end(session)

        self.assertEqual(response.status, "completed")
        self.assertEqual(response.capture_quality, 0.25)
        self.assertEqual(response.valid_frame_ratio, 0.25)
        self.assertIsNotNone(response.ended_at)
        self.assertEqual(db.commits, 1)

    def test_already_completed_session_is_accepted_not_a_conflict(self):
        # What analyze leaves behind: completed, server-computed quality, no end time.
        session = _session("completed")
        db, response = _end(session)

        self.assertEqual(response.status, "completed")
        # The server-computed quality from the analysis survives the client's estimate.
        self.assertEqual(response.capture_quality, 0.90)
        self.assertEqual(response.valid_frame_ratio, 0.88)
        # The missing end time is the one thing this call backfills.
        self.assertIsNotNone(response.ended_at)
        self.assertEqual(db.commits, 1)

    def test_completed_session_with_end_time_is_left_untouched(self):
        stamped = datetime(2026, 8, 13, 10, 30, tzinfo=UTC)
        session = _session("completed", ended_at=stamped)
        db, response = _end(session)

        self.assertEqual(response.ended_at, stamped)
        self.assertEqual(db.commits, 0)

    def test_cancelled_session_cannot_be_ended(self):
        session = _session("cancelled")

        with self.assertRaises(HTTPException) as ctx:
            _end(session)
        self.assertEqual(ctx.exception.status_code, 409)


class CancelSessionTests(unittest.TestCase):
    def test_completed_session_cannot_be_cancelled(self):
        session = _session("completed")
        db = _FakeDb(session)

        with self.assertRaises(HTTPException) as ctx:
            cancel_session(session.id, db=db, current_user=SimpleNamespace(id=uuid4()))
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(db.commits, 0)

    def test_cancelling_twice_is_harmless(self):
        session = _session("cancelled")
        db = _FakeDb(session)

        response = cancel_session(
            session.id, db=db, current_user=SimpleNamespace(id=uuid4())
        )
        self.assertEqual(response.status, "cancelled")
        self.assertEqual(db.commits, 0)


if __name__ == "__main__":
    unittest.main()
