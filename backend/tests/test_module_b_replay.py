"""Stage 5.7 determinism gate for the Module B squat replay harness.

Mirrors `WbltDeterminismTests` (Module A Stage 7): re-running the official analysis on
the same stored frames must reproduce an identical result, which is the property that
makes `replay_squat_session.py` a meaningful proof rather than a demo.

Runs against the **committed** corpus (`app/module_b/replay_corpus/squat/`), not
fixtures built inside this file, for two reasons. It is the same data the harness and
`labels.json` use, so the three cannot drift apart; and the corpus spans every band the
shipped model has been found to actually reach (Good and Fair — see
`test_corpus_spans_every_reachable_band_plus_a_low_quality_reject` for why Poor is not
currently one of them) plus a low-capture-quality reject, so determinism is checked on
every band the pipeline can currently produce rather than on one happy path.
"""

from __future__ import annotations

import json
import unittest

from app.module_b.core.evaluation.replay_squat_session import (
    CORPUS_DIR,
    analyse_frames,
    load_frames_from_json,
    replay_rules_and_fusion,
)
from app.module_b.core.features import FeatureVector

MANIFEST = json.loads((CORPUS_DIR / "labels.json").read_text())
SAMPLES = MANIFEST["samples"]


class SquatReplayCorpusTests(unittest.TestCase):
    """The corpus itself is committed and must stay consistent with its manifest."""

    def test_corpus_is_committed_and_complete(self):
        self.assertTrue(CORPUS_DIR.is_dir(), f"missing corpus dir {CORPUS_DIR}")
        for sample in SAMPLES:
            with self.subTest(sample=sample["sample_id"]):
                path = CORPUS_DIR / sample["frames_file"]
                self.assertTrue(path.is_file(), f"missing corpus file {path}")

    def test_corpus_spans_every_reachable_band_plus_a_low_quality_reject(self):
        """The Stage 5.7 checklist asked for Good/Fair/Poor + a low-Q reject.

        Stage 5.8 swapped in the real trained model and found Poor is not currently
        reachable at all: `export_squat_model.py`'s `_deployed_confidence_check()`
        shows the shipped model never reaches confidence>=0.85 toward Poor on any of
        its own 98 training rows (max confidence toward Poor: 1-0.244=0.756), and a
        deliberate geometry sweep while rebuilding this corpus could not reach it
        synthetically either (closest: P(Good)~0.50). Asserting `{"Good","Fair","Poor"}`
        here would therefore assert something the shipped model cannot currently do —
        this checks the bands that are actually reachable instead, so it fails loudly
        if a future retrain ever makes Poor reachable and this test is not updated to
        match (see model_card.md's limitations section for the same finding)."""
        bands = {sample["measured"]["band"] for sample in SAMPLES}
        self.assertEqual(bands, {"Good", "Fair"})

        low_quality = [
            sample
            for sample in SAMPLES
            if "low_capture_quality" in sample["measured"]["flags"]
        ]
        self.assertTrue(low_quality, "corpus has no low-capture-quality reject sample")
        for sample in low_quality:
            with self.subTest(sample=sample["sample_id"]):
                # The reject must be rejected for the *quality* reason, not because it
                # happened to score badly -- otherwise it would not test the q_min gate.
                self.assertEqual(sample["measured"]["band"], "Fair")
                self.assertIn("retry_camera_placement", sample["measured"]["flags"])

    def test_measured_bands_still_match_the_manifest(self):
        """Guards against the corpus and the pipeline drifting apart silently.

        `labels.json` records what the real pipeline produced when the corpus was
        generated. If a config or rule change moves a band, this fails and the corpus
        must be regenerated deliberately -- rather than the manifest quietly describing
        a result the code no longer produces.
        """
        for sample in SAMPLES:
            with self.subTest(sample=sample["sample_id"]):
                frames = load_frames_from_json(str(CORPUS_DIR / sample["frames_file"]))
                result = analyse_frames(frames)
                self.assertEqual(result["band"], sample["measured"]["band"])
                self.assertAlmostEqual(
                    result["score"], sample["measured"]["score"], places=4
                )
                self.assertEqual(result["n_reps"], sample["measured"]["n_reps"])


class SquatDeterminismTests(unittest.TestCase):
    """Stage 5.7 gate: the same frames must always produce the same result."""

    def test_same_frames_produce_identical_result_for_every_corpus_sample(self):
        for sample in SAMPLES:
            with self.subTest(sample=sample["sample_id"]):
                frames = load_frames_from_json(str(CORPUS_DIR / sample["frames_file"]))
                first = analyse_frames(frames)
                second = analyse_frames(frames)
                self.assertEqual(first, second)

    def test_determinism_holds_for_the_low_quality_reject(self):
        """A rejected capture takes a different branch in `fuse_scores()` (flags force
        Fair before banding), so it needs its own determinism check rather than being
        assumed covered by the loop above."""
        sample = next(
            s for s in SAMPLES if "low_capture_quality" in s["measured"]["flags"]
        )
        frames = load_frames_from_json(str(CORPUS_DIR / sample["frames_file"]))
        first = analyse_frames(frames)
        second = analyse_frames(frames)

        self.assertEqual(first, second)
        self.assertEqual(first["band"], "Fair")
        self.assertIn("low_capture_quality", first["flags"])

    def test_feature_extraction_is_stable_across_runs(self):
        """Narrower than the result-level check above: pins the drift to the feature
        stage if it ever happens, instead of only reporting a changed score."""
        sample = SAMPLES[0]
        frames = load_frames_from_json(str(CORPUS_DIR / sample["frames_file"]))

        first = analyse_frames(frames)["feature_vectors"]
        second = analyse_frames(frames)["feature_vectors"]

        self.assertEqual(first, second)

    def test_stored_feature_vector_replay_is_deterministic(self):
        """The `--session-id` path: rules + fusion re-derived from stored vectors.

        Module B never persists frames, so this is all a stored session can replay --
        the harness's docstring explains why. Determinism still has to hold for it.
        """
        sample = SAMPLES[0]
        frames = load_frames_from_json(str(CORPUS_DIR / sample["frames_file"]))
        result = analyse_frames(frames)
        vectors = [
            FeatureVector(
                schema_version=MANIFEST["config_at_build"]["feature_schema_version"],
                names=_feature_names(),
                values=tuple(values),
            )
            for values in result["feature_vectors"]
        ]

        first = replay_rules_and_fusion(vectors, result["q"])
        second = replay_rules_and_fusion(vectors, result["q"])

        self.assertEqual(first, second)
        # The rules stage is frame-independent, so re-deriving it from the stored
        # vectors must reproduce the full pipeline's rule score exactly. If this
        # diverges, the stored snapshot is not a faithful record of the analysis.
        self.assertAlmostEqual(first["rule_score"], result["rule_score"], places=9)


def _feature_names() -> tuple[str, ...]:
    from app.module_b.squat.features import SQUAT_FEATURE_NAMES

    return SQUAT_FEATURE_NAMES


class SquatReplayHarnessTests(unittest.TestCase):
    def test_replay_rejects_a_frame_stream_with_no_reps(self):
        """A standing-still capture has no reps; the harness must say so rather than
        fabricate a grade from an empty set."""
        frames = load_frames_from_json(str(CORPUS_DIR / SAMPLES[0]["frames_file"]))
        standing_only = frames[:5]

        with self.assertRaisesRegex(ValueError, "No complete repetitions"):
            analyse_frames(standing_only)

    def test_corpus_files_are_valid_json_frame_lists(self):
        for sample in SAMPLES:
            with self.subTest(sample=sample["sample_id"]):
                frames = load_frames_from_json(str(CORPUS_DIR / sample["frames_file"]))
                self.assertEqual(len(frames), sample["n_frames"])
                self.assertIn("timestampMs", frames[0])
                self.assertEqual(len(frames[0]["worldLandmarks"]), 33)


if __name__ == "__main__":
    unittest.main()
