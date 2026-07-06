"""STS score/band computation (blueprint §6): start at 10, apply deductions.

Score is on a 0-10 scale (proposal Table 6: Poor 0-4, Fair 4-7, Good 7-10).
Poor capture quality overrides everything -> band is "invalid" (never a
misleading Good/Fair/Poor claim on unreliable data).
"""

from app.module_a import config


def score_to_band(score: float) -> str:
    if score < config.SCORE_POOR_MAX:
        return "poor"
    if score < config.SCORE_FAIR_MAX:
        return "fair"
    return "good"


def time_band(completion_time_sec: float | None) -> str | None:
    """Band from total time to complete 5 reps (only meaningful if all 5 reps done)."""
    if completion_time_sec is None:
        return None
    if completion_time_sec <= config.TIME_GOOD_MAX_SEC:
        return "good"
    if completion_time_sec <= config.TIME_FAIR_MAX_SEC:
        return "fair"
    return "poor"


def compute_session_status(rep_count: int, target: int, quality_band: str) -> str:
    """Completeness/confidence status, kept independent of movement-quality band.

    A tracking problem (poor capture) or an early/incomplete stop must never be
    presented as if the movement itself was graded Poor -- that's a separate axis
    from `band`, which only ever describes movement quality.
    """
    if quality_band == "poor":
        return "low_confidence"
    if rep_count < target:
        return "incomplete"
    return "complete"


def compute_band(
    metrics: dict, quality: dict, exercise_type: str = "sit_to_stand"
) -> dict:
    """Returns {score, band, warning_tags, session_status, is_partial_score}.

    Exercise-specific scoring: STS uses rep count; SLS uses hold duration.
    Band/score computed from valid data only; session_status (complete/incomplete/
    low_confidence) tracks completeness/confidence separately from quality band.
    """
    warning_tags: list[str] = []
    quality_band = quality["quality_band"]

    if exercise_type == "sit_to_stand":
        return _compute_sts_band(metrics, quality_band, warning_tags)
    elif exercise_type in ("single_leg_stance", "supported_single_leg_stance"):
        return _compute_sls_band(metrics, quality_band, warning_tags)
    elif exercise_type == "weight_bearing_lunge_test":
        return _compute_wblt_band(metrics, quality_band, warning_tags)
    else:
        raise ValueError(f"Unknown exercise_type: {exercise_type}")


def _compute_sts_band(
    metrics: dict, quality_band: str, warning_tags: list[str]
) -> dict:
    """STS-specific banding: based on rep count, timing, and stability."""
    rep_count = metrics["rep_count"]
    target = metrics["target_rep_count"]

    session_status = compute_session_status(rep_count, target, quality_band)
    if quality_band == "poor":
        warning_tags.append("poor_capture_quality")
    if rep_count < target:
        warning_tags.append("incomplete_reps")

    if rep_count == 0:
        return {
            "score": 0.0,
            "band": "invalid",
            "warning_tags": warning_tags,
            "time_band": None,
            "session_status": session_status,
            "is_partial_score": False,
        }

    score = 10.0

    if quality_band == "moderate":
        warning_tags.append("moderate_capture_quality")
        score -= 1.0

    completion_time = metrics["completion_time_sec"]
    t_band = time_band(completion_time) if rep_count >= target else None
    if t_band == "poor":
        warning_tags.append("very_slow_completion")
        score -= 2.0

    if metrics.get("wobble_count", 0) > 0:
        warning_tags.append("unstable_reps")
        score -= 1.0

    avg_trunk_lean = metrics.get("avg_trunk_lean_deg")
    if avg_trunk_lean is not None and avg_trunk_lean > config.TRUNK_LEAN_EXCESSIVE_DEG:
        warning_tags.append("excessive_trunk_lean")
        score -= 1.0

    score = max(0.0, round(score, 2))
    band = score_to_band(score)

    return {
        "score": score,
        "band": band,
        "warning_tags": warning_tags,
        "time_band": t_band,
        "session_status": session_status,
        "is_partial_score": rep_count < target,
    }


def _compute_sls_band(
    metrics: dict, quality_band: str, warning_tags: list[str]
) -> dict:
    """SLS-specific banding: based on hold duration and stability/sway."""
    hold_duration = metrics.get("hold_duration_sec", 0.0)
    target_hold = metrics.get("target_hold_sec", config.TARGET_SLS_HOLD_SEC)

    # For SLS, session_status considers hold_duration as the primary metric
    # Treat as "complete" if hold >= target_hold, "incomplete" if < target, "low_confidence" if poor quality
    if quality_band == "poor":
        session_status = "low_confidence"
        warning_tags.append("poor_capture_quality")
    elif hold_duration >= target_hold:
        session_status = "complete"
    else:
        session_status = "incomplete"
        warning_tags.append("incomplete_hold")

    if hold_duration == 0.0:
        return {
            "score": 0.0,
            "band": "invalid",
            "warning_tags": warning_tags,
            "hold_band": None,
            "session_status": session_status,
            "is_partial_score": False,
        }

    # Determine hold-duration band and start score from it
    if hold_duration >= config.HOLD_GOOD_MIN_SEC:
        hold_band = "good"
        score = 10.0
    elif hold_duration >= config.HOLD_FAIR_MIN_SEC:
        hold_band = "fair"
        score = 6.0  # Fair is 4-7, so middle at 6.0
    else:
        hold_band = "poor"
        score = 3.0  # Poor is 0-4, so middle at 3.0

    if quality_band == "moderate":
        warning_tags.append("moderate_capture_quality")
        score -= 1.0

    # Sway/stability deduction
    max_sway = metrics.get("max_sway_m", 0.0)
    if max_sway > config.MAX_HIP_SWAY_M:
        warning_tags.append("excessive_sway")
        score -= 1.0

    score = max(0.0, round(score, 2))
    band = score_to_band(score)

    return {
        "score": score,
        "band": band,
        "warning_tags": warning_tags,
        "hold_band": hold_band,
        "session_status": session_status,
        "is_partial_score": hold_duration < target_hold,
    }


def _compute_wblt_band(
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
