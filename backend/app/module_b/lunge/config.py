"""Lunge identity config; movement thresholds arrive in later Phase 5B stages."""

LUNGE_CONFIG = {
    # [dataset-derived] Stable REHAB24-6 exercise identifier (Ex11/Ex12 lunge).
    "exercise_code": "lunge",
    # [dataset-derived] Locked Assumption #3: side (sagittal) view only, no valgus.
    "required_view": "side_view",
    # [proposed heuristic] Phase 5B stub key; replaced by a versioned artifact in Stage 5.8.
    "model_key": "lunge",
}
