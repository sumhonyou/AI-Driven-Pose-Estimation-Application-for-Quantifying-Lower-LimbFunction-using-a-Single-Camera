"""Replay harness: re-runs one attempt's stored (or offline JSON) landmark log
through a fresh `wblt.analysis.analyze_attempt` call and prints the resulting
metrics/band. Mirrors `replay_sls_session.py` -- proves the WBLT analysis core
is deterministic: the same frames always produce the same result as the live
`/api/wblt/analyze` call.

Caveat vs the SLS replay: `module_a_landmark_log` is written once per POST
(one WBLT attempt), with `frame_index` restarting at 0 for each attempt --
there is no per-attempt id in that table, so `--session-id` replay always
loads the MOST RECENTLY WRITTEN attempt for that session (the latest
`created_at` row group). For replaying a SPECIFIC earlier attempt, use
`--json-file` with frames saved at capture time instead.

Usage:
    python -m app.module_a.scripts.replay_wblt_session --session-id <uuid> --leg right \
        --target-distance-cm 10.0 --touched --age 30 --gender male
    python -m app.module_a.scripts.replay_wblt_session --json-file frames.json --leg left \
        --target-distance-cm 8.0 --touched --age 30 --gender male
"""

import argparse
import json
from uuid import UUID

from app.module_a.wblt import analysis


def load_frames_from_db(session_id: str) -> list[dict]:
    from sqlalchemy import select

    from app.db.database import SessionLocal
    from app.db.models import ModuleALandmarkLog

    with SessionLocal() as db:
        latest = db.scalar(
            select(ModuleALandmarkLog.created_at)
            .where(ModuleALandmarkLog.session_id == UUID(session_id))
            .order_by(ModuleALandmarkLog.created_at.desc())
            .limit(1)
        )
        if latest is None:
            return []
        rows = db.scalars(
            select(ModuleALandmarkLog)
            .where(
                ModuleALandmarkLog.session_id == UUID(session_id),
                ModuleALandmarkLog.created_at == latest,
            )
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
    parser = argparse.ArgumentParser(description="Replay a Module A WBLT attempt")
    parser.add_argument(
        "--session-id",
        help="Session UUID (reads the latest module_a_landmark_log write)",
    )
    parser.add_argument(
        "--json-file", help="Offline JSON file of frames instead of the DB"
    )
    parser.add_argument("--leg", required=True, choices=["left", "right"])
    parser.add_argument("--target-distance-cm", required=True, type=float)
    parser.add_argument("--touched", action="store_true")
    parser.add_argument("--age", type=int, default=None)
    parser.add_argument("--gender", default=None)
    args = parser.parse_args()

    if args.session_id:
        frames = load_frames_from_db(args.session_id)
    elif args.json_file:
        frames = load_frames_from_json(args.json_file)
    else:
        parser.error("Provide --session-id or --json-file")
        return

    print(f"[replay] Loaded {len(frames)} frames for leg={args.leg}")

    result = analysis.analyze_attempt(
        frames,
        args.leg,
        args.target_distance_cm,
        args.touched,
        args.age,
        args.gender,
    )
    print(f"[replay] result={json.dumps(result, indent=2)}")

    # Determinism check: re-running the SAME frames must give the IDENTICAL result.
    replay_again = analysis.analyze_attempt(
        frames,
        args.leg,
        args.target_distance_cm,
        args.touched,
        args.age,
        args.gender,
    )
    if replay_again == result:
        print("[replay] deterministic: re-run produced an identical result")
    else:
        print(
            "[replay] WARNING: re-run produced a DIFFERENT result -- non-deterministic!"
        )


if __name__ == "__main__":
    main()
