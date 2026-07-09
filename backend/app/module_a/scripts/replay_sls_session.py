"""Replay harness: re-runs one leg's stored (or offline JSON) landmark log through
a fresh `sls.analysis.analyze_leg` call and prints the resulting metrics/band.
Mirrors `replay_session.py` (STS) -- proves the SLS analysis core is deterministic:
the same frames always produce the same result as the live `/api/sls/analyze` call.

Usage:
    python -m app.module_a.scripts.replay_sls_session --session-id <uuid> --leg right
    python -m app.module_a.scripts.replay_sls_session --json-file frames.json --leg left
"""

import argparse
import json
from uuid import UUID

from app.module_a.sls import analysis


def load_frames_from_db(session_id: str) -> list[dict]:
    from app.db.database import SessionLocal
    from app.db.models import ModuleALandmarkLog
    from sqlalchemy import select

    with SessionLocal() as db:
        rows = db.scalars(
            select(ModuleALandmarkLog)
            .where(ModuleALandmarkLog.session_id == UUID(session_id))
            .order_by(ModuleALandmarkLog.frame_index)
        )
        return [
            {
                "timestampMs": float(row.timestamp_ms),
                "worldLandmarks": row.world_landmarks["landmarks"],
            }
            for row in rows
        ]


def load_frames_from_json(path: str) -> list[dict]:
    with open(path) as f:
        return json.load(f)


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay a Module A SLS leg")
    parser.add_argument(
        "--session-id", help="Session UUID (reads module_a_landmark_log)"
    )
    parser.add_argument(
        "--json-file", help="Offline JSON file of frames instead of the DB"
    )
    parser.add_argument(
        "--leg", required=True, choices=["left", "right"], help="Lifted leg"
    )
    args = parser.parse_args()

    if args.session_id:
        frames = load_frames_from_db(args.session_id)
    elif args.json_file:
        frames = load_frames_from_json(args.json_file)
    else:
        parser.error("Provide --session-id or --json-file")
        return

    print(f"[replay] Loaded {len(frames)} frames for leg={args.leg}")

    result = analysis.analyze_leg(frames, args.leg)
    print(f"[replay] metrics={json.dumps(result['metrics'], indent=2)}")
    print(f"[replay] quality={json.dumps(result['quality'], indent=2)}")


if __name__ == "__main__":
    main()
