"""Lunge identity config; movement thresholds arrive in later Phase 5B stages."""

LUNGE_CONFIG = {
    # [dataset-derived] Stable REHAB24-6 exercise identifier (Ex11/Ex12 lunge).
    "exercise_code": "lunge",
    # [dataset-derived] Locked Assumption #3: side (sagittal) view only, no valgus.
    "required_view": "side_view",
    # [proposed heuristic] Phase 5B stub key; replaced by a versioned artifact in Stage 5.8.
    "model_key": "lunge",
    # [proposed heuristic, R5.3] Body-scale reference for normalised features.
    # Mirrors squat's Stage 4.2 starting point (thigh_length); lunge's own Stage 5.4
    # bake-off picks the winner (thigh_length vs trunk_length) empirically.
    "norm_ref_strategy": "thigh_length",
}
