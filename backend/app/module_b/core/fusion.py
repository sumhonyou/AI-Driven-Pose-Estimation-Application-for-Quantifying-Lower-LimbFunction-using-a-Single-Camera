"""Option A score fusion, banding and explicit confidence/quality overrides."""

from __future__ import annotations

from dataclasses import dataclass

from app.module_b.core.config import MODULE_B_CORE_CONFIG
from app.module_b.core.features import FeatureVector
from app.module_b.core.model_registry import ModelBundle
from app.module_b.core.rules import RuleScores


@dataclass(frozen=True)
class FusionResult:
    """Fusion output ready for later persistence and report rendering."""

    score: float
    band: str
    rule_score: float
    ml_score: float
    confidence: float
    q: float
    w_rule: float
    w_ml: float
    flags: tuple[str, ...]
    model_version: str
    is_placeholder_model: bool
    placeholder_model_notice: bool


def score_to_band(score: float) -> str:
    """Map a validated 0–10 score to the fixed D6 Poor/Fair/Good bands."""
    _assert_0_to_10(score, "score")
    thresholds = MODULE_B_CORE_CONFIG["band_thresholds"]
    if score < thresholds["poor"]["max_exclusive"]:
        return "Poor"
    if score < thresholds["fair"]["max_exclusive"]:
        return "Fair"
    return "Good"


def project_ml_score(probabilities: dict[str, float]) -> tuple[float, float]:
    """Project Option A's binary probabilities to S_ml and calibrated confidence."""
    _validate_option_a_probabilities(probabilities)
    return 10.0 * probabilities["Good"], max(probabilities.values())


def fuse_model(
    *,
    rule_scores: RuleScores,
    model: ModelBundle,
    features: FeatureVector,
    q: float,
    band_policy: dict | None = None,
) -> FusionResult:
    """Run one versioned model and fuse it with the available rule score.

    `band_policy` is the exercise's optional banding override (None -> the default
    3-band Good/Fair/Poor abstention behaviour). Squat passes a binary policy; every
    other exercise leaves it None and keeps the abstaining 3-band output.
    """
    if rule_scores.score is None:
        raise ValueError("Cannot fuse Module B scores without an available rule score")
    return fuse_scores(
        rule_score=rule_scores.score,
        probabilities=model.predict_proba(features),
        q=q,
        model_version=model.model_version,
        is_placeholder_model=model.is_placeholder,
        band_policy=band_policy,
    )


def fuse_scores(
    *,
    rule_score: float,
    probabilities: dict[str, float],
    q: float,
    model_version: str,
    is_placeholder_model: bool,
    band_policy: dict | None = None,
) -> FusionResult:
    """Fuse known 0–10 inputs into a score and a band.

    Two banding schemes, selected by `band_policy`:

    - **Default (triband, `band_policy=None`):** force Fair when confidence or capture
      is low — the abstaining Good/Fair/Poor output every exercise shipped with.
    - **Binary (`band_policy={"scheme": "binary", ...}`):** commit to Good/Poor on every
      rep. Fair is never emitted, the low-confidence rule-heavy weight switch is skipped
      (that switch lets the ROM rule — inverted for the squat population — dominate every
      rep), and the band comes from a single decision threshold on the fused score. The
      low-confidence / low-capture-quality flags are still recorded, they just no longer
      change the band. Placeholder models always keep abstaining, whatever the policy.
    """
    _assert_0_to_10(rule_score, "rule_score")
    _assert_unit_interval(q, "q")
    ml_score, confidence = project_ml_score(probabilities)
    _assert_0_to_10(ml_score, "ml_score")

    config = MODULE_B_CORE_CONFIG
    low_confidence = confidence < config["confidence_low_threshold"]
    low_capture_quality = q < config["q_min"]

    # Flags are recorded under both schemes; only the triband scheme lets them force
    # a band or change the fusion weights.
    flags: list[str] = []
    if low_confidence:
        flags.append("low_confidence")
    if low_capture_quality:
        flags.extend(("low_capture_quality", "retry_camera_placement"))

    binary = (
        band_policy is not None
        and band_policy.get("scheme") == "binary"
        and not is_placeholder_model
    )
    if binary:
        w_rule = band_policy["w_rule"]
        w_ml = band_policy["w_ml"]
        _assert_weights_sum_to_one(w_rule, w_ml)
        final_score = w_rule * rule_score + w_ml * ml_score
        threshold = band_policy["decision_threshold"]
        _assert_0_to_10(threshold, "decision_threshold")
        band = "Good" if final_score >= threshold else "Poor"
    else:
        if low_confidence or low_capture_quality:
            w_rule = config["w_rule_low_confidence"]
            w_ml = round(1.0 - w_rule, 10)
        else:
            w_rule = config["w_rule_default"]
            w_ml = config["w_ml_default"]
        _assert_weights_sum_to_one(w_rule, w_ml)
        final_score = w_rule * rule_score + w_ml * ml_score
        band = "Fair" if flags else score_to_band(final_score)

    return FusionResult(
        score=final_score,
        band=band,
        rule_score=rule_score,
        ml_score=ml_score,
        confidence=confidence,
        q=q,
        w_rule=w_rule,
        w_ml=w_ml,
        flags=tuple(flags),
        model_version=model_version,
        is_placeholder_model=is_placeholder_model,
        placeholder_model_notice=is_placeholder_model,
    )


def _assert_weights_sum_to_one(w_rule: float, w_ml: float) -> None:
    if abs((w_rule + w_ml) - 1.0) > 1e-9:
        raise ValueError("Fusion weights must sum to 1")


def _validate_option_a_probabilities(probabilities: dict[str, float]) -> None:
    if set(probabilities) != {"Poor", "Good"}:
        raise ValueError("Option A probabilities must contain exactly Poor and Good")
    for label, probability in probabilities.items():
        _assert_unit_interval(probability, f"P({label})")
    if abs(sum(probabilities.values()) - 1.0) > 1e-9:
        raise ValueError("Option A probabilities must sum to 1")


def _assert_0_to_10(value: float, name: str) -> None:
    if not 0.0 <= value <= 10.0:
        raise ValueError(f"{name} must be on the 0–10 scale")


def _assert_unit_interval(value: float, name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1")
