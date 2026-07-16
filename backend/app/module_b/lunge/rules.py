"""Config-driven lunge ROM, tempo, stability, and symmetry rule sub-scores.

ROM/Tempo/Stability mirror squat's Stage 4.4 formulas exactly, swapped onto the
front leg's features (ROM, DF-limit floor) or the central hip signal (Stability,
already lead-leg-agnostic). Symmetry is new: task.md's delta requires it to be
CROSS-REP (leading-left reps vs leading-right reps), never within-rep, because a
lunge's front and back knee do different jobs in one rep -- a within-rep L-vs-R
comparison would just be comparing two different joints, not a symmetry check.

Per HY (2026-07-17): Symmetry is report-only. Its SubScore.score is always
None, so `RuleScores.score`'s equal-weight mean (core/rules.py) never includes
it -- the comparison numbers live in `SubScore.metrics` instead, purely for the
report, and require >=1 rep per leg to attempt (mirrors Tempo's philosophy of
scoring as soon as it's computable, over waiting for a larger, more stable N).
"""

from __future__ import annotations

from statistics import pstdev

from app.module_b.core.features import FeatureVector
from app.module_b.core.rules import RuleScores, SubScore, assemble_rule_scores
from app.module_b.lunge.config import LUNGE_CONFIG

ROM_CODE = "rom_completeness"
TEMPO_CODE = "tempo_consistency"
STABILITY_CODE = "stability_control"
SYMMETRY_CODE = "symmetry_cross_rep"


def score_lunge_rep(features: FeatureVector) -> RuleScores:
    """Score one rep; tempo and symmetry require the full set to be meaningful."""
    return assemble_rule_scores(
        rom_subscore(features),
        SubScore(code=TEMPO_CODE, score=None),
        stability_subscore(features),
        SubScore(code=SYMMETRY_CODE, score=None, notes=("symmetry_requires_full_set",)),
    )


def score_lunge_set(feature_vectors: list[FeatureVector]) -> RuleScores:
    """Score the completed lunge set from its independently extracted rep vectors."""
    if not feature_vectors:
        return assemble_rule_scores(
            SubScore(code=ROM_CODE, score=None),
            SubScore(code=TEMPO_CODE, score=None),
            SubScore(code=STABILITY_CODE, score=None),
            SubScore(code=SYMMETRY_CODE, score=None),
        )
    rom_scores = [rom_subscore(features) for features in feature_vectors]
    stability_scores = [stability_subscore(features) for features in feature_vectors]
    return assemble_rule_scores(
        SubScore(
            code=ROM_CODE,
            score=_mean_available(rom_scores),
            notes=_combined_notes(rom_scores),
        ),
        tempo_subscore(feature_vectors),
        SubScore(
            code=STABILITY_CODE,
            score=_duration_weighted_mean(stability_scores, feature_vectors),
        ),
        symmetry_subscore(feature_vectors),
    )


def rom_subscore(features: FeatureVector) -> SubScore:
    """Map front-knee peak flexion to the configured 0-10 ROM completeness score."""
    config = LUNGE_CONFIG["rules"]["rom"]
    peak_flexion = _feature(features, "front_knee_flex_peak_deg")
    if peak_flexion < config["shallow_start_deg"]:
        score = _interpolate(peak_flexion, 0.0, config["shallow_start_deg"], 0.0, 2.0)
    elif peak_flexion < config["parallel_start_deg"]:
        score = _interpolate(
            peak_flexion,
            config["shallow_start_deg"],
            config["parallel_start_deg"],
            2.0,
            5.0,
        )
    elif peak_flexion < config["deep_start_deg"]:
        score = _interpolate(
            peak_flexion,
            config["parallel_start_deg"],
            config["deep_start_deg"],
            5.0,
            8.0,
        )
    else:
        score = _interpolate(
            peak_flexion,
            config["deep_start_deg"],
            config["deep_full_score_deg"],
            8.0,
            10.0,
        )

    notes: tuple[str, ...] = ()
    if (
        _feature(features, "front_ankle_df_proxy_deg")
        <= config["df_limit_proxy_max_deg"]
    ):
        score = max(score, config["df_limit_score_floor"])
        notes = ("rom_possibly_df_limited",)
    return SubScore(code=ROM_CODE, score=_clamp_score(score), notes=notes)


def tempo_subscore(feature_vectors: list[FeatureVector]) -> SubScore:
    """Score within-set duration consistency; absolute movement speed is not rated."""
    if len(feature_vectors) < 2:
        return SubScore(code=TEMPO_CODE, score=None)
    durations = [_feature(features, "rep_duration_s") for features in feature_vectors]
    mean_duration = sum(durations) / len(durations)
    if mean_duration <= 0.0:
        return SubScore(code=TEMPO_CODE, score=None)
    cv = pstdev(durations) / mean_duration
    config = LUNGE_CONFIG["rules"]["tempo"]
    if cv <= config["high_consistency_cv_max"]:
        score = _interpolate(cv, 0.0, config["high_consistency_cv_max"], 10.0, 9.0)
    elif cv <= config["moderate_consistency_cv_max"]:
        score = _interpolate(
            cv,
            config["high_consistency_cv_max"],
            config["moderate_consistency_cv_max"],
            9.0,
            5.0,
        )
    else:
        score = _interpolate(
            cv,
            config["moderate_consistency_cv_max"],
            config["poor_consistency_cv_zero_score"],
            5.0,
            0.0,
        )
    return SubScore(code=TEMPO_CODE, score=_clamp_score(score))


def stability_subscore(features: FeatureVector) -> SubScore:
    """Score stable in-plane motion without rewarding a very brief still sample."""
    config = LUNGE_CONFIG["rules"]["stability"]
    jitter = _feature(features, "hip_mid_jitter_norm")
    duration_s = _feature(features, "rep_duration_s")
    jitter_score = 10.0 * (
        1.0 - min(max(jitter, 0.0) / config["jitter_zero_score_norm"], 1.0)
    )
    duration_credit = min(max(duration_s, 0.0) / config["full_duration_credit_s"], 1.0)
    return SubScore(
        code=STABILITY_CODE, score=_clamp_score(jitter_score * duration_credit)
    )


def symmetry_subscore(feature_vectors: list[FeatureVector]) -> SubScore:
    """Compare front-knee peak flexion + ROM across leading-left vs leading-right
    reps. Report-only (score stays None; see core/rules.py's SubScore docstring)
    -- the comparison lives in `metrics` and never moves S_rule."""
    config = LUNGE_CONFIG["rules"]["symmetry"]
    min_reps = config["min_reps_per_leg"]
    left = [features for features in feature_vectors if features.lead_leg == "left"]
    right = [features for features in feature_vectors if features.lead_leg == "right"]
    metrics: dict[str, float] = {
        "left_lead_reps": float(len(left)),
        "right_lead_reps": float(len(right)),
    }
    if len(left) < min_reps or len(right) < min_reps:
        return SubScore(
            code=SYMMETRY_CODE,
            score=None,
            notes=("symmetry_unavailable_single_leg_set",),
            metrics=metrics,
        )

    peak_left = _mean(_feature(f, "front_knee_flex_peak_deg") for f in left)
    peak_right = _mean(_feature(f, "front_knee_flex_peak_deg") for f in right)
    rom_left = _mean(_feature(f, "front_knee_rom_deg") for f in left)
    rom_right = _mean(_feature(f, "front_knee_rom_deg") for f in right)
    metrics["front_knee_peak_symmetry_index_pct"] = _symmetry_index_pct(
        peak_left, peak_right
    )
    metrics["front_knee_rom_symmetry_index_pct"] = _symmetry_index_pct(
        rom_left, rom_right
    )
    return SubScore(code=SYMMETRY_CODE, score=None, metrics=metrics)


def _feature(features: FeatureVector, name: str) -> float:
    try:
        return features.as_dict()[name]
    except KeyError as error:
        raise ValueError(
            f"Lunge FeatureVector is missing required feature: {name}"
        ) from error


def _interpolate(
    value: float, start: float, end: float, start_score: float, end_score: float
) -> float:
    if end <= start:
        raise ValueError("Interpolation range must increase")
    proportion = min(max((value - start) / (end - start), 0.0), 1.0)
    return start_score + proportion * (end_score - start_score)


def _clamp_score(score: float) -> float:
    return min(max(score, 0.0), 10.0)


def _mean(values) -> float:
    values = list(values)
    return sum(values) / len(values)


def _symmetry_index_pct(a: float, b: float) -> float:
    denominator = 0.5 * (a + b)
    if abs(denominator) < 1e-9:
        return 0.0
    return abs(a - b) / denominator * 100.0


def _mean_available(sub_scores: list[SubScore]) -> float | None:
    available = [
        sub_score.score for sub_score in sub_scores if sub_score.score is not None
    ]
    return sum(available) / len(available) if available else None


def _combined_notes(sub_scores: list[SubScore]) -> tuple[str, ...]:
    return tuple(note for sub_score in sub_scores for note in sub_score.notes)


def _duration_weighted_mean(
    sub_scores: list[SubScore], feature_vectors: list[FeatureVector]
) -> float | None:
    weighted_score = 0.0
    total_duration = 0.0
    for sub_score, features in zip(sub_scores, feature_vectors, strict=True):
        if sub_score.score is None:
            continue
        duration_s = max(_feature(features, "rep_duration_s"), 0.0)
        weighted_score += sub_score.score * duration_s
        total_duration += duration_s
    return weighted_score / total_duration if total_duration > 0.0 else None
