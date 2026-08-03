"""Module B squat replay determinism tests.

Runs against the committed corpus so the harness, labels manifest, and tests stay in
sync. The corpus covers reachable squat bands plus a low-capture-quality sample.
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
from app.module_b.squat.config import SQUAT_CONFIG

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

    def test_corpus_spans_both_reachable_bands_plus_a_low_quality_sample(self):
        """Stage 5.11: squat commits to a binary Good/Poor band, and both are reachable.

        The 3-band era (Stage 5.7/5.8) could not reach Poor at all — the confidence
        abstention routed every uncertain rep to Fair, and the shipped model never
        reached confidence>=0.85 toward Poor. The committed binary policy
        (`SQUAT_CONFIG["band_policy"]`) replaces that abstention with a single
        score-threshold cut, so real synthetic samples now land in Poor. This asserts
        the corpus spans exactly the two bands the deployed pipeline can now emit, and
        fails loudly if a future policy change makes that untrue."""
        bands = {sample["measured"]["band"] for sample in SAMPLES}
        self.assertEqual(bands, {"Good", "Poor"})

        low_quality = [
            sample
            for sample in SAMPLES
            if "low_capture_quality" in sample["measured"]["flags"]
        ]
        self.assertTrue(low_quality, "corpus has no low-capture-quality sample")
        for sample in low_quality:
            with self.subTest(sample=sample["sample_id"]):
                # Binary policy: a low-quality capture still commits to a Good/Poor band
                # (no Fair abstention), but must raise the retry flag so the UI can warn.
                self.assertIn(sample["measured"]["band"], {"Good", "Poor"})
                self.assertIn("retry_camera_placement", sample["measured"]["flags"])

    def test_corpus_exercises_the_stage_5_12_fault_gate_override(self):
        """At least one corpus sample bands Poor because a fault gate fired.

        The gates run across every rep and override the fused band to Poor with a
        named reason (Stage 5.12). The corpus records each sample's failed gates in
        `measured.fault_gate_tags`; this asserts the override path is actually
        exercised by the committed corpus, not just by the unit tests, and that every
        recorded tag is one the config defines."""
        allowed = {gate["tag"] for gate in SQUAT_CONFIG["fault_gates"].values()}
        gated = [
            sample for sample in SAMPLES if sample["measured"].get("fault_gate_tags")
        ]
        self.assertTrue(gated, "corpus never exercises a fault-gate override")
        for sample in gated:
            with self.subTest(sample=sample["sample_id"]):
                self.assertEqual(sample["measured"]["band"], "Poor")
                for tag in sample["measured"]["fault_gate_tags"]:
                    self.assertIn(tag, allowed)

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

    def test_determinism_holds_for_the_low_quality_sample(self):
        """A low-capture-quality sample raises the retry/quality flags, so it takes a
        slightly different path through `fuse_scores()` than a clean capture and gets
        its own determinism check. Under the binary policy it commits a Good/Poor band
        (Stage 5.11) rather than abstaining to Fair."""
        sample = next(
            s for s in SAMPLES if "low_capture_quality" in s["measured"]["flags"]
        )
        frames = load_frames_from_json(str(CORPUS_DIR / sample["frames_file"]))
        first = analyse_frames(frames)
        second = analyse_frames(frames)

        self.assertEqual(first, second)
        self.assertIn(first["band"], {"Good", "Poor"})
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
