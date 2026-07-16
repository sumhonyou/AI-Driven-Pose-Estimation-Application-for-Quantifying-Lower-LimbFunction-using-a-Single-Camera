"""Config-driven squat ROM, tempo and stability rule sub-scores."""

from __future__ import annotations

from statistics import pstdev

from app.module_b.core.features import FeatureVector
from app.module_b.core.rules import RuleScores, SubScore, assemble_rule_scores
from app.module_b.squat.config import SQUAT_CONFIG

ROM_CODE = "rom_completeness"
TEMPO_CODE = "tempo_consistency"
STABILITY_CODE = "stability_control"


def score_squat_rep(features: FeatureVector) -> RuleScores:
    """Score one rep; tempo remains unavailable until the set has two reps."""
    return assemble_rule_scores(
        rom_subscore(features),
        SubScore(code=TEMPO_CODE, score=None),
        stability_subscore(features),
    )


def score_squat_set(feature_vectors: list[FeatureVector]) -> RuleScores:
    """Score the completed squat set from its independently extracted rep vectors."""
    if not feature_vectors:
        return assemble_rule_scores(
            SubScore(code=ROM_CODE, score=None),
            SubScore(code=TEMPO_CODE, score=None),
            SubScore(code=STABILITY_CODE, score=None),
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
    )


def rom_subscore(features: FeatureVector) -> SubScore:
    """Map peak flexion to the configured 0–10 ROM completeness score."""
    config = SQUAT_CONFIG["rules"]["rom"]
    peak_flexion = _feature(features, "knee_flex_peak_deg")
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
    if _feature(features, "ankle_df_proxy_deg") <= config["df_limit_proxy_max_deg"]:
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
    config = SQUAT_CONFIG["rules"]["tempo"]
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
    config = SQUAT_CONFIG["rules"]["stability"]
    jitter = _feature(features, "hip_mid_jitter_norm")
    duration_s = _feature(features, "rep_duration_s")
    jitter_score = 10.0 * (
        1.0 - min(max(jitter, 0.0) / config["jitter_zero_score_norm"], 1.0)
    )
    duration_credit = min(max(duration_s, 0.0) / config["full_duration_credit_s"], 1.0)
    return SubScore(
        code=STABILITY_CODE, score=_clamp_score(jitter_score * duration_credit)
    )


def _feature(features: FeatureVector, name: str) -> float:
    try:
        return features.as_dict()[name]
    except KeyError as error:
        raise ValueError(
            f"Squat FeatureVector is missing required feature: {name}"
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
