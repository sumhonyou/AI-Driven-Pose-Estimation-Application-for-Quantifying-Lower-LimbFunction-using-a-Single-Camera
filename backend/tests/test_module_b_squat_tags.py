"""Squat tag taxonomy and tag-builder tests."""

from __future__ import annotations

import unittest

from app.module_b.core.rules import SubScore, assemble_rule_scores
from app.module_b.squat.fault_gates import FaultGateResult, GateCheck
from app.module_b.squat.rules import (
    ROM_CODE,
    STABILITY_CODE,
    TEMPO_CODE,
    tempo_subscore,
)
from app.module_b.squat.tags import SQUAT_TAG_TAXONOMY, build_squat_error_tags


def _rule_scores(cv: float | None = None):
    """RuleScores whose tempo sub-score carries a CV (as the real pipeline now does)."""
    tempo_metrics = {"cv": cv} if cv is not None else {}
    return assemble_rule_scores(
        SubScore(code=ROM_CODE, score=8.0),
        SubScore(code=TEMPO_CODE, score=5.0, metrics=tempo_metrics),
        SubScore(code=STABILITY_CODE, score=7.0),
    )


class TaxonomyShapeTests(unittest.TestCase):
    def test_dropped_tags_are_absent(self) -> None:
        # The two side-view-invalid tags must never reappear in the taxonomy.
        self.assertNotIn("asymmetry", SQUAT_TAG_TAXONOMY)
        self.assertNotIn("feet_too_wide", SQUAT_TAG_TAXONOMY)
        self.assertNotIn("knee_valgus", SQUAT_TAG_TAXONOMY)

    def test_kept_tags_present_with_expected_metadata(self) -> None:
        self.assertEqual(SQUAT_TAG_TAXONOMY["insufficient_depth"].severity, "high")
        self.assertEqual(SQUAT_TAG_TAXONOMY["insufficient_depth"].source, "rule")
        self.assertEqual(SQUAT_TAG_TAXONOMY["inconsistent_tempo"].severity, "low")
        self.assertEqual(SQUAT_TAG_TAXONOMY["inconsistent_tempo"].kind, "soft")
        self.assertEqual(SQUAT_TAG_TAXONOMY["low_confidence"].source, "system")
        # Gate messages are single-sourced from config, so the taxonomy carries them.
        self.assertTrue(SQUAT_TAG_TAXONOMY["heel_lift"].message)


class SystemTagTests(unittest.TestCase):
    def test_known_system_flags_get_taxonomy_severity(self) -> None:
        tags = build_squat_error_tags(
            fusion_flags=("low_confidence", "low_capture_quality"),
            gate_result=None,
            rule_scores=_rule_scores(),
        )
        by_tag = {t.tag: t for t in tags}
        self.assertEqual(by_tag["low_confidence"].severity, "medium")
        self.assertEqual(by_tag["low_confidence"].source, "system")
        self.assertEqual(by_tag["low_capture_quality"].source, "system")

    def test_unknown_flag_is_still_surfaced(self) -> None:
        tags = build_squat_error_tags(
            fusion_flags=("some_new_flag",),
            gate_result=None,
            rule_scores=_rule_scores(),
        )
        self.assertEqual(tags[0].tag, "some_new_flag")
        self.assertIsNone(tags[0].severity)
        self.assertEqual(tags[0].source, "system")


class FaultGateTagTests(unittest.TestCase):
    def test_failed_gates_become_high_rule_tags_deduped(self) -> None:
        result = FaultGateResult(
            all_passed=False,
            failed=(
                GateCheck("insufficient_depth", "Depth msg", 60.0, 0),
                GateCheck("insufficient_depth", "Depth msg", 62.0, 2),
                GateCheck("heel_lift", "Heel msg", 0.2, 1),
            ),
        )
        tags = build_squat_error_tags(
            fusion_flags=(), gate_result=result, rule_scores=_rule_scores()
        )
        gate_tags = [t for t in tags if t.source == "rule"]
        self.assertEqual(
            [t.tag for t in gate_tags], ["heel_lift", "insufficient_depth"]
        )
        self.assertTrue(all(t.severity == "high" for t in gate_tags))
        self.assertEqual({t.tag: t.message for t in gate_tags}["heel_lift"], "Heel msg")


class TempoTagTests(unittest.TestCase):
    def test_tempo_tag_fires_at_or_above_moderate_cv(self) -> None:
        tags = build_squat_error_tags(
            fusion_flags=(), gate_result=None, rule_scores=_rule_scores(cv=0.30)
        )
        tempo = [t for t in tags if t.tag == "inconsistent_tempo"]
        self.assertEqual(len(tempo), 1)
        self.assertEqual(tempo[0].severity, "low")
        self.assertEqual(tempo[0].source, "rule")

    def test_tempo_tag_silent_below_threshold(self) -> None:
        tags = build_squat_error_tags(
            fusion_flags=(), gate_result=None, rule_scores=_rule_scores(cv=0.10)
        )
        self.assertEqual([t for t in tags if t.tag == "inconsistent_tempo"], [])

    def test_tempo_tag_silent_when_cv_absent(self) -> None:
        # One-rep set: tempo sub-score has no CV, so the tag never fires.
        tags = build_squat_error_tags(
            fusion_flags=(), gate_result=None, rule_scores=_rule_scores(cv=None)
        )
        self.assertEqual([t for t in tags if t.tag == "inconsistent_tempo"], [])

    def test_tempo_subscore_now_carries_cv(self) -> None:
        # The rule layer surfaces the CV the tag depends on.
        from app.module_b.core.config import MODULE_B_CORE_CONFIG
        from app.module_b.core.features import FeatureVector
        from app.module_b.squat.features import SQUAT_FEATURE_NAMES

        def _f(duration: float) -> FeatureVector:
            values = {name: 0.0 for name in SQUAT_FEATURE_NAMES}
            values["rep_duration_s"] = duration
            return FeatureVector(
                schema_version=MODULE_B_CORE_CONFIG["feature_schema_version"],
                names=SQUAT_FEATURE_NAMES,
                values=tuple(values[name] for name in SQUAT_FEATURE_NAMES),
            )

        sub = tempo_subscore([_f(0.75), _f(1.25)])
        self.assertIn("cv", sub.metrics)
        self.assertGreater(sub.metrics["cv"], 0.0)


if __name__ == "__main__":
    unittest.main()
