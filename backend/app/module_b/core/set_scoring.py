"""Score Module B sets and aggregate per-rep verdicts.

Voting is applied per rep because the ML threshold was calibrated on individual reps,
not on averaged set scores. Fault gates also apply per rep, so one failed gate affects
that rep before the set-level vote is calculated.

For voting policies, the headline score is the share of clean reps:
`10 * clean_reps / total_reps`. Mean ML score and mean confidence are still stored as
secondary report values.

Exercises without a voting policy keep the legacy first-vector scoring path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from app.module_b.core.config import MODULE_B_CORE_CONFIG
from app.module_b.core.features import FeatureVector
from app.module_b.core.fusion import FusionResult, fuse_scores, project_ml_score
from app.module_b.core.model_registry import ModelBundle
from app.module_b.core.rules import RuleScores

MAJORITY_VOTE = "majority_vote"


@dataclass(frozen=True)
class RepVerdict:
    """One rep's own Good/Poor call, and what decided it."""

    rep_index: int
    ml_score: float
    confidence: float
    ml_passed: bool
    failed_gates: tuple[str, ...]

    @property
    def counted_good(self) -> bool:
        """A rep is Good only if the model passes it AND no named fault fired on it."""
        return self.ml_passed and not self.failed_gates


@dataclass(frozen=True)
class SetScoreResult:
    """The set's fused result plus the per-rep detail the report renders."""

    fusion: FusionResult
    rep_verdicts: tuple[RepVerdict, ...]

    @property
    def good_rep_count(self) -> int:
        return sum(1 for verdict in self.rep_verdicts if verdict.counted_good)


def score_set(
    *,
    rule_scores: RuleScores,
    model: ModelBundle,
    feature_vectors: Sequence[FeatureVector],
    q: float,
    band_policy: dict | None = None,
    failed_gates_by_rep: Mapping[int, tuple[str, ...]] | None = None,
) -> SetScoreResult:
    """Grade a whole set. Falls back to first-rep scoring unless a policy asks otherwise.

    `failed_gates_by_rep` maps a rep index to the tags that failed on it. It is a plain
    mapping rather than an exercise's gate type so this core module stays decoupled from
    any one exercise's gate module (the router does the duck-typed conversion).
    """
    if not feature_vectors:
        raise ValueError("Cannot score a set with no feature vectors")
    if rule_scores.score is None:
        raise ValueError("Cannot fuse Module B scores without an available rule score")

    if not _uses_majority_vote(band_policy, model):
        # Untouched legacy path: one vector, one fused score, no per-rep verdicts.
        fusion = fuse_scores(
            rule_score=rule_scores.score,
            probabilities=model.predict_proba(feature_vectors[0]),
            q=q,
            model_version=model.model_version,
            is_placeholder_model=model.is_placeholder,
            band_policy=band_policy,
        )
        return SetScoreResult(fusion=fusion, rep_verdicts=())

    gates = failed_gates_by_rep or {}
    w_rule = band_policy["w_rule"]
    w_ml = band_policy["w_ml"]
    threshold = band_policy["decision_threshold"]

    verdicts: list[RepVerdict] = []
    for rep_index, features in enumerate(feature_vectors):
        ml_score, confidence = project_ml_score(model.predict_proba(features))
        # The rule score is a set-level statistic, so every rep shares it. Squat runs
        # w_rule=0.0, which makes this term vanish; it is kept so the weighting stays
        # meaningful for any future exercise that opts into voting with w_rule > 0.
        fused = w_rule * rule_scores.score + w_ml * ml_score
        verdicts.append(
            RepVerdict(
                rep_index=rep_index,
                ml_score=ml_score,
                confidence=confidence,
                ml_passed=fused >= threshold,
                failed_gates=tuple(gates.get(rep_index, ())),
            )
        )

    good = sum(1 for verdict in verdicts if verdict.counted_good)
    # Strict majority: an exact split is not a pass.
    band = "Good" if good * 2 > len(verdicts) else "Poor"

    # Kept for the report's secondary "ML prediction" / "Confidence" cards -- they are no
    # longer what the headline score reports (see below).
    mean_ml_score = sum(v.ml_score for v in verdicts) / len(verdicts)
    mean_confidence = sum(v.confidence for v in verdicts) / len(verdicts)

    # The headline score uses the same clean-rep count as the band vote, so score and
    # band cannot disagree.
    final_score = 10.0 * good / len(verdicts)

    config = MODULE_B_CORE_CONFIG
    flags: list[str] = []
    if mean_confidence < config["confidence_low_threshold"]:
        flags.append("low_confidence")
    if q < config["q_min"]:
        flags.extend(("low_capture_quality", "retry_camera_placement"))

    fusion = FusionResult(
        score=final_score,
        band=band,
        rule_score=rule_scores.score,
        ml_score=mean_ml_score,
        confidence=mean_confidence,
        q=q,
        w_rule=w_rule,
        w_ml=w_ml,
        flags=tuple(flags),
        model_version=model.model_version,
        is_placeholder_model=model.is_placeholder,
        placeholder_model_notice=model.is_placeholder,
    )
    return SetScoreResult(fusion=fusion, rep_verdicts=tuple(verdicts))


def failed_gates_by_rep(gate_result) -> dict[int, tuple[str, ...]]:
    """Group a gate result's failures by the rep they fired on.

    Kept in core so the router and replay harness share one implementation. Duck-typed
    on ``all_passed``/``failed``/``rep_index``/``tag`` so this module stays decoupled
    from exercise-specific gate classes; gate-less exercises pass None.
    """
    if gate_result is None or gate_result.all_passed:
        return {}
    by_rep: dict[int, list[str]] = {}
    for check in gate_result.failed:
        by_rep.setdefault(check.rep_index, []).append(check.tag)
    # Sorted + de-duplicated so a repeated payload stays byte-identical (X8).
    return {index: tuple(sorted(set(tags))) for index, tags in by_rep.items()}


def _uses_majority_vote(band_policy: dict | None, model: ModelBundle) -> bool:
    """A placeholder model never votes -- it has no signal, so it keeps abstaining."""
    return (
        band_policy is not None
        and band_policy.get("scheme") == "binary"
        and band_policy.get("aggregation") == MAJORITY_VOTE
        and not model.is_placeholder
    )
