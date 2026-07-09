"""WBLT score/band computation: dorsiflexion ROM and ankle symmetry."""

from app.module_a.core.banding import score_to_band
from app.module_a.wblt import config


def compute_wblt_band(
    metrics: dict, quality_band: str, warning_tags: list[str]
) -> dict:
    """WBLT-specific banding: based on dorsiflexion ROM and ankle symmetry."""
    trial_count = metrics.get("trial_count", metrics.get("rep_count", 0))
    target_trials = metrics.get(
        "target_trials", metrics.get("target_rep_count", config.TARGET_WBLT_TRIALS)
    )

    # Session status: complete if trials ≥ target, incomplete else, low_confidence if poor quality
    if quality_band == "poor":
        session_status = "low_confidence"
        warning_tags.append("poor_capture_quality")
    elif trial_count >= target_trials:
        session_status = "complete"
    else:
        session_status = "incomplete"
        warning_tags.append("incomplete_trials")

    if trial_count == 0:
        return {
            "score": 0.0,
            "band": "invalid",
            "warning_tags": warning_tags,
            "rom_band": None,
            "symmetry_band": None,
            "session_status": session_status,
            "is_partial_score": False,
        }

    # Determine ROM band from avg dorsiflexion
    avg_dorsiflexion = metrics.get("avg_dorsiflexion_deg", 0.0)
    if avg_dorsiflexion >= config.ANKLE_DORSIFLEXION_GOOD_MIN_DEG:
        rom_band = "good"
        rom_score = 10.0
    elif avg_dorsiflexion >= config.ANKLE_DORSIFLEXION_FAIR_MIN_DEG:
        rom_band = "fair"
        rom_score = 6.0
    else:
        rom_band = "poor"
        rom_score = 3.0

    # Determine symmetry band from avg symmetry diff
    avg_symmetry_diff = metrics.get("avg_symmetry_diff_deg", 0.0)
    if avg_symmetry_diff <= config.ANKLE_SYMMETRY_EXCELLENT_MAX_DEG:
        symmetry_band = "excellent"
        symmetry_deduction = 0.0
    elif avg_symmetry_diff <= config.ANKLE_SYMMETRY_GOOD_MAX_DEG:
        symmetry_band = "good"
        symmetry_deduction = 0.5
    else:
        symmetry_band = "poor"
        symmetry_deduction = 1.5

    score = rom_score - symmetry_deduction

    if quality_band == "moderate":
        warning_tags.append("moderate_capture_quality")
        score -= 1.0

    if avg_dorsiflexion < config.ANKLE_DORSIFLEXION_FAIR_MIN_DEG:
        warning_tags.append("limited_ankle_dorsiflexion")

    if avg_symmetry_diff > config.ANKLE_SYMMETRY_GOOD_MAX_DEG:
        warning_tags.append("poor_ankle_symmetry")

    score = max(0.0, round(score, 2))
    band = score_to_band(score)

    return {
        "score": score,
        "band": band,
        "warning_tags": warning_tags,
        "rom_band": rom_band,
        "symmetry_band": symmetry_band,
        "session_status": session_status,
        "is_partial_score": trial_count < target_trials,
    }
