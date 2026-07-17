"""Replay harness: re-runs a stored (or offline JSON) landmark log through the STS
engine and prints the resulting metrics/band. Proves the engine is deterministic —
the same frames always produce the same result as the live analyze endpoint.

Usage:
    python -m app.module_a.scripts.replay_session --session-id <uuid>
    python -m app.module_a.scripts.replay_session --json-file frames.json
"""

import argparse
import json
from uuid import UUID

from app.module_a.core import banding
from app.module_a.sts.engine import run_sts


def load_frames_from_db(session_id: str) -> list[dict]:
    from sqlalchemy import select

    from app.db.database import SessionLocal
    from app.db.models import ModuleALandmarkLog

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
    parser = argparse.ArgumentParser(description="Replay a Module A STS session")
    parser.add_argument(
        "--session-id", help="Session UUID (reads module_a_landmark_log)"
    )
    parser.add_argument(
        "--json-file", help="Offline JSON file of frames instead of the DB"
    )
    args = parser.parse_args()

    if args.session_id:
        frames = load_frames_from_db(args.session_id)
    elif args.json_file:
        frames = load_frames_from_json(args.json_file)
    else:
        parser.error("Provide --session-id or --json-file")
        return

    print(f"[replay] Loaded {len(frames)} frames")

    engine_result = run_sts(frames)
    band_result = banding.compute_band(
        engine_result["metrics"], engine_result["quality"]
    )

    print(f"[replay] band={band_result['band']} score={band_result['score']}")
    print(f"[replay] warning_tags={band_result['warning_tags']}")
    print(f"[replay] metrics={json.dumps(engine_result['metrics'], indent=2)}")
    print(f"[replay] quality={json.dumps(engine_result['quality'], indent=2)}")


if __name__ == "__main__":
    main()
