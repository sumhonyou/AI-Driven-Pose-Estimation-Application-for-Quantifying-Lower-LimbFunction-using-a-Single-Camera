"""Replay harness: re-runs a squat set through a fresh analysis and proves determinism.

Mirrors Module A's Stage 7 precedent (`replay_sls_session.py` / `replay_wblt_session.py`):
same two input modes, same in-script determinism check rather than "trust the DB". What
it can prove differs between the two modes, and the difference is structural, not an
oversight:

**`--json-file` — full replay.** Runs the entire pipeline the live endpoint runs
(quality on the raw buffer -> preprocess -> segment -> features -> rules -> fuse) twice
over the same frames and asserts the two results are identical. This is the real
determinism proof, and it is what the committed replay corpus
(`app/module_b/replay_corpus/squat/`) is for.

**`--session-id` — partial replay, because Module B does not store frames.** Module A
persists raw landmarks to `module_a_landmark_log`; **Module B has no equivalent table by
design** — `crud.save_result()` stores "the exact analyzed snapshot without persisting
browser frames/video", and `assess_capture_quality()` computes Q "without retaining
browser video or frames". So a stored session cannot be replayed from its frames: they
were never kept. What *is* stored is each rep's `FeatureVector` inside
`metrics_json`, so this mode replays the **rules + fusion** stage from those vectors and
leaves preprocessing, segmentation and feature extraction unreplayable. That is a
deliberate privacy property of the architecture, and a real limit on this mode — stated
here rather than papered over. To replay a specific real session end-to-end, save its
frames at capture time and use `--json-file`.

This is the same *shape* of caveat as WBLT's (whose `module_a_landmark_log` has no
per-attempt id, so `--session-id` replays only the most recently written attempt), but
strictly stronger: WBLT loses *which* attempt, Module B has no frames at all.

**`--session-id` compares against the stored snapshot but does not assert equality.**
A mismatch is reported, not raised. `router.py`'s GET handler is explicit that a stored
result is a historical snapshot and is never recomputed; Stage 5.6 changed
`w_rule_default`/`w_ml_default`/`confidence_low_threshold`, so any session graded before
that change *legitimately* re-derives to a different score today. Asserting equality
would turn a correct config change into a crash. The comparison is still worth printing:
it is how you see config drift against real stored data.

Usage:
    python -m app.module_b.core.evaluation.replay_squat_session \\
        --json-file app/module_b/replay_corpus/squat/good_moderate_depth_1.json
    python -m app.module_b.core.evaluation.replay_squat_session --session-id <uuid>
    python -m app.module_b.core.evaluation.replay_squat_session --corpus
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from uuid import UUID

from app.module_b.core.features import FeatureVector
from app.module_b.core.model_registry import get_model_bundle
from app.module_b.core.preprocessing import preprocess_world_landmarks
from app.module_b.core.quality import assess_capture_quality
from app.module_b.core.registry import get_exercise
from app.module_b.core.set_scoring import failed_gates_by_rep, score_set
from app.module_b.squat.rules import score_squat_set

CORPUS_DIR = Path(__file__).resolve().parents[2] / "replay_corpus" / "squat"
EXERCISE_CODE = "squat"


def analyse_frames(frames: list[dict[str, Any]]) -> dict[str, Any]:
    """Run the exact pipeline `router.py::analyze_module_b_session` runs.

    Kept in the same order and with the same semantics as the endpoint — quality on the
    RAW buffer, preprocessing over the whole stream, then segment/extract/score/fuse via
    the registered plugin (X1). Any divergence here would make the replay prove
    something about this file rather than about the endpoint.

    Returns a plain, comparable dict: `FusionResult` is a frozen dataclass and would
    compare fine, but the dict also carries the per-rep features, so a determinism
    failure points at *which* stage drifted instead of only reporting a different score.
    """
    exercise = get_exercise(EXERCISE_CODE)
    quality = assess_capture_quality(frames)
    preprocessed = preprocess_world_landmarks(frames)
    reps = exercise.segment(preprocessed)
    if not reps:
        raise ValueError("No complete repetitions were detected in this set")

    feature_vectors = [exercise.extract_features(rep) for rep in reps]
    rule_scores = exercise.set_rule_scores(reps, feature_vectors)
    if rule_scores.score is None:
        raise ValueError("No rule score is available for this set")

    # Faithful to the endpoint (Stage 5.13): gates are evaluated first and folded into
    # each rep's own verdict, then the set's band is a strict majority of those verdicts.
    # Keeping this in step with router.py matters — the pre-5.11 harness diverged on
    # band_policy exactly this way, and the corpus silently encoded the wrong band.
    gate_result = exercise.evaluate_fault_gates(reps, feature_vectors)
    fusion = score_set(
        rule_scores=rule_scores,
        model=get_model_bundle(exercise.model_key),
        feature_vectors=feature_vectors,
        q=float(quality["q"]),
        band_policy=exercise.band_policy,
        failed_gates_by_rep=failed_gates_by_rep(gate_result),
    ).fusion
    return {
        "n_reps": len(reps),
        "score": fusion.score,
        "band": fusion.band,
        "rule_score": fusion.rule_score,
        "ml_score": fusion.ml_score,
        "confidence": fusion.confidence,
        "q": fusion.q,
        "weights": [fusion.w_rule, fusion.w_ml],
        "flags": list(fusion.flags),
        "model_version": fusion.model_version,
        "feature_vectors": [list(vector.values) for vector in feature_vectors],
    }


def replay_rules_and_fusion(
    feature_vectors: list[FeatureVector], q: float
) -> dict[str, Any]:
    """Re-derive rules + fusion from stored feature vectors (the `--session-id` path).

    Everything upstream of the feature vector is unreplayable from the DB — see the
    module docstring.

    Calls `score_squat_set()` directly rather than the plugin's
    `set_rule_scores(reps, feature_vectors)`: the contract wants the `Rep` objects, and
    this path genuinely does not have them (no frames were stored, so no reps can be
    rebuilt). Passing a list of `None`s would happen to work only because the squat
    implementation ignores its `reps` argument today — depending on that would be
    depending on an implementation detail that is free to change.

    ⚠ **Fault gates cannot run here** (heel-rise reads raw frames, which were never
    stored), so a set whose stored band was decided by a gate failure will replay with
    the model-only band. That gap predates Stage 5.13 — this path never ran gates — but
    per-rep voting makes it visible more often, since gates now decide single reps rather
    than the whole set. Compare bands from this path with that caveat in mind.
    """
    rule_scores = score_squat_set(feature_vectors)
    if rule_scores.score is None:
        raise ValueError("No rule score is available for these stored feature vectors")
    fusion = score_set(
        rule_scores=rule_scores,
        model=get_model_bundle(EXERCISE_CODE),
        feature_vectors=feature_vectors,
        q=q,
        band_policy=get_exercise(EXERCISE_CODE).band_policy,
    ).fusion
    return {
        "score": fusion.score,
        "band": fusion.band,
        "rule_score": fusion.rule_score,
        "confidence": fusion.confidence,
        "flags": list(fusion.flags),
    }


def load_frames_from_json(path: str) -> list[dict[str, Any]]:
    with open(path) as f:
        return json.load(f)


def load_stored_session(session_id: str) -> dict[str, Any]:
    """Read one session's persisted Module B snapshot. Frames are not available."""
    from app.db.database import SessionLocal
    from app.module_b.core import crud

    with SessionLocal() as db:
        result = crud.get_result_by_session(db, UUID(session_id))
        if result is None:
            raise ValueError(f"No Module B result stored for session {session_id}")
        metrics = result.metrics_json or {}
        if not metrics.get("feature_vectors"):
            raise ValueError(
                f"Session {session_id} has no stored feature vectors to replay"
            )
        return {
            "feature_vectors": [
                FeatureVector(
                    schema_version=item["schema_version"],
                    names=tuple(item["names"]),
                    values=tuple(float(value) for value in item["values"]),
                )
                for item in metrics["feature_vectors"]
            ],
            "q": float(result.q) if result.q is not None else 1.0,
            "stored": {
                "score": float(result.score) if result.score is not None else None,
                "band": result.band,
                "rule_score": metrics.get("rule_score"),
            },
        }


def _assert_deterministic(label: str, first: dict, second: dict) -> None:
    if first != second:
        raise AssertionError(
            f"{label}: re-running the SAME frames produced a DIFFERENT result.\n"
            f"  first:  {json.dumps(first, sort_keys=True)}\n"
            f"  second: {json.dumps(second, sort_keys=True)}"
        )


def replay_json_file(path: str, *, quiet: bool = False) -> dict[str, Any]:
    """Full replay + in-script determinism check on one frames file."""
    frames = load_frames_from_json(path)
    first = analyse_frames(frames)
    second = analyse_frames(frames)
    _assert_deterministic(Path(path).name, first, second)
    if not quiet:
        print(f"[replay] {Path(path).name}: {len(frames)} frames")
        print(f"[replay]   reps={first['n_reps']} band={first['band']} ")
        print(
            f"[replay]   score={first['score']:.4f} rule={first['rule_score']:.4f} "
            f"confidence={first['confidence']:.4f} q={first['q']:.4f}"
        )
        print(f"[replay]   flags={first['flags']}")
        print("[replay]   determinism: identical across two fresh runs OK")
    return first


def replay_corpus() -> int:
    """Replay every committed corpus sample and check each against labels.json.

    The manifest's `measured` block was written by the generator from the same real
    pipeline, so a mismatch here means the corpus and the code have drifted apart —
    which is precisely what this is for.
    """
    manifest = json.loads((CORPUS_DIR / "labels.json").read_text())
    failures = 0
    for sample in manifest["samples"]:
        result = replay_json_file(str(CORPUS_DIR / sample["frames_file"]), quiet=True)
        expected = sample["measured"]
        drifted = (
            result["band"] != expected["band"]
            or round(result["score"], 4) != expected["score"]
        )
        status = "DRIFT" if drifted else "OK   "
        failures += bool(drifted)
        print(
            f"[replay] {status} {sample['sample_id']:28s} "
            f"band={result['band']:5s} score={result['score']:.4f} "
            f"(labels.json: band={expected['band']} score={expected['score']})"
        )
    if failures:
        print(
            f"\n[replay] {failures} sample(s) drifted from labels.json. Either the "
            "pipeline changed (regenerate the corpus) or something broke."
        )
    else:
        print(f"\n[replay] all {len(manifest['samples'])} samples match labels.json.")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay a Module B squat set")
    parser.add_argument("--json-file", help="Offline JSON frames file (full replay)")
    parser.add_argument(
        "--session-id",
        help="Session UUID (partial replay: rules+fusion from stored feature vectors)",
    )
    parser.add_argument(
        "--corpus",
        action="store_true",
        help="Replay every committed corpus sample and check against labels.json",
    )
    args = parser.parse_args()

    if args.corpus:
        raise SystemExit(1 if replay_corpus() else 0)

    if args.json_file:
        replay_json_file(args.json_file)
        return

    if args.session_id:
        stored = load_stored_session(args.session_id)
        first = replay_rules_and_fusion(stored["feature_vectors"], stored["q"])
        second = replay_rules_and_fusion(stored["feature_vectors"], stored["q"])
        _assert_deterministic(f"session {args.session_id}", first, second)
        print(f"[replay] session {args.session_id}")
        print(
            "[replay]   PARTIAL replay: rules + fusion only. Module B does not persist "
            "frames, so preprocessing/segmentation/feature extraction cannot be "
            "replayed from the DB (see module docstring)."
        )
        print(f"[replay]   re-derived: {json.dumps(first, sort_keys=True)}")
        print(f"[replay]   stored:     {json.dumps(stored['stored'], sort_keys=True)}")
        print("[replay]   determinism: identical across two fresh runs OK")
        if stored["stored"]["band"] != first["band"]:
            print(
                "[replay]   NOTE: re-derived band differs from the stored snapshot. "
                "This is expected for sessions graded before a config change (Stage 5.6 "
                "moved the fusion weights and confidence threshold); stored results are "
                "historical snapshots and are never recomputed by the API."
            )
        return

    parser.error("Provide --json-file, --session-id or --corpus")


if __name__ == "__main__":
    main()
