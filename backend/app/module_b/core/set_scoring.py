"""Stage 5.13: score every rep in a set, then aggregate one band from the verdicts.

Replaces the long-standing "the ML only ever scores `feature_vectors[0]`" behaviour
(flagged at Stage 5.12 and deferred there). A user's whole set is now graded, not its
first rep.

**Why a vote and not a mean of the reps.** `decision_threshold` was tuned on *individual*
reps (`ml/scripts/tune_squat_binary_band.py`, max macro-F1 over the out-of-fold
predictions). Averaging the reps first and then applying that same cut silently changes
what the cut means, because a mean over N reps has a far narrower spread than one rep.
Voting applies the threshold exactly where it was calibrated and only then combines, so
**no re-calibration is required** -- which matters, because the labels are per-rep and no
set-level ground truth exists to re-tune against.

It is also the noise-robust choice at this model's operating point. Stage 5.11 knowingly
accepted flagging ~31% of Good reps as Poor. Over a 10-rep set that means a spurious flag
is near-certain, so the aggregation rule decides everything: "any rep Poor -> Poor" would
wrongly fail ~98% of clean sets, a majority vote ~5.5%, and the old rep-0-only logic 31%.
(The ~5.5% assumes per-rep errors are independent; they are not -- same subject, camera
and lighting -- so the true rate is higher, though still far below 98%.)

**Gates fold in per rep, not per set.** Stage 5.12 forced the whole set to Poor if any
gate failed on any rep, which condemned a 30-rep set for one heel lift and left
`fusion.score` untouched -- the visible "8.0/10 + Needs Improvement" contradiction. Here a
gate failure invalidates *its own rep*, and the vote decides the set. Note the two signals
genuinely measure different things: `heel_rise_peak_norm` is rule-only and is NOT in the
frozen ML feature vector, so the model cannot see a heel lift at all.

**Stage 5.18 -- the headline score is the share of clean reps, not the mean model
probability.** Stage 5.13 reported `mean(10 * P(Good))` as the score while the band came
from the vote, so the two measured different quantities and could still disagree. Live
capture then showed the mean is not merely uninformative but *anti-correlated* with the
faults the system detects (gate-failing reps 8.845 vs 8.807 for clean reps; the
highest-scoring rep in a set was a depth failure), and that it compresses the whole
0%-100% quality range into 8.02-9.27. `final_score` is now `10 * good / total`, reusing
the vote's own count, which makes `band == "Good"` exactly equivalent to `score > 5.0`.
`mean_ml_score` / `mean_confidence` are unchanged and still populate `FusionResult` for the
report's secondary cards -- the model's opinion is demoted, not discarded, and it still
decides `counted_good` for every rep.

Exercise-agnostic on purpose: everything is driven by `band_policy`. An exercise with no
`aggregation` key keeps the exact single-vector behaviour it shipped with, so Module A is
untouched by construction (same additive pattern as `band_policy` and the gate hook).
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
    # Strict majority: an exact 5/5 split is NOT a pass. Ties break toward Poor, which
    # keeps the safety-first posture Stage 5.11 chose when it accepted the false-alarm
    # rate in exchange for never calling a poor-form rep fine.
    band = "Good" if good * 2 > len(verdicts) else "Poor"

    # Kept for the report's secondary "ML prediction" / "Confidence" cards -- they are no
    # longer what the headline score reports (see below).
    mean_ml_score = sum(v.ml_score for v in verdicts) / len(verdicts)
    mean_confidence = sum(v.confidence for v in verdicts) / len(verdicts)

    # Stage 5.18: the headline score is the SHARE OF CLEAN REPS, not the mean model
    # probability. The mean was measured to be anti-correlated with the faults this system
    # detects -- on live capture, gate-failing reps averaged 8.845 against 8.807 for clean
    # reps, and a set's highest-scoring rep (9.458) was a depth failure. That is the EC3D
    # construct inversion reproduced in deployment, so a mean of it cannot carry a quality
    # scale: recorded sessions spanned only 8.02-9.27 while real performance spanned
    # 0%-100% clean.
    #
    # `good` is the same count the band vote above already uses, so this introduces no new
    # arithmetic -- and it makes band a deterministic function of score:
    #     band == "Good"  <=>  good * 2 > total  <=>  score > 5.0
    # which is why the two can no longer contradict each other (the defect that started
    # this work: 8.0 displayed beside "Needs Improvement").
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

    Lives here rather than in `core/router.py` so the router and the replay harness
    share one implementation (X1) — a forked copy is exactly how the pre-Stage-5.11
    harness drifted out of step with the endpoint. Duck-typed on
    ``all_passed``/``failed``/``rep_index``/``tag`` so this core module stays decoupled
    from any one exercise's gate types; gate-less exercises pass None.
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
