"""Squat identity config; movement thresholds arrive in later Phase 4 stages."""

SQUAT_CONFIG = {
    # [dataset-derived] Stable REHAB24-6 exercise identifier selected in Stage 4.0.
    "exercise_code": "squat",
    # [dataset-derived] REHAB24-6/runtime-compatible sagittal capture orientation.
    "required_view": "side_view",
    # [proposed heuristic] Phase 4 stub key; replaced by a versioned artifact in Phase 5.
    "model_key": "squat",
    # [proposed heuristic, R5.3] Phase 5.4 compares this against trunk_length.
    "norm_ref_strategy": "thigh_length",
    "segmentation": {
        # [proposed heuristic, R9] Flexion from standing that starts a descent.
        "enter_descending_deg": 30.0,
        # [proposed heuristic, R9] Lower exit creates hysteresis against jitter.
        "exit_standing_deg": 20.0,
        # [proposed heuristic, R9] Blocks a rebound from becoming a second rep.
        "refractory_s": 0.5,
        # [proposed heuristic, R9] Rejects very brief threshold-noise candidates.
        "min_rep_duration_s": 0.5,
    },
    "rules": {
        "rom": {
            # [clinical norm, S1] Lower edge of the shallow-ROM band.
            "shallow_start_deg": 60.0,
            # [clinical norm, S1] Lower edge of the parallel-ROM band.
            "parallel_start_deg": 90.0,
            # [clinical norm, S1] Lower edge of the deep-ROM band.
            "deep_start_deg": 110.0,
            # [proposed heuristic, pilot-tune] Reaches the top of deep-band interpolation.
            "deep_full_score_deg": 130.0,
            # [proposed heuristic, R3] Low shank-forward proxy may indicate limited DF.
            "df_limit_proxy_max_deg": 20.0,
            # [proposed heuristic, R3] Avoids treating a possible mobility cap as zero control.
            "df_limit_score_floor": 2.0,
        },
        "tempo": {
            # [proposed heuristic, R6] Consistent duration CV earns 9–10.
            "high_consistency_cv_max": 0.10,
            # [proposed heuristic, R6] Moderate duration CV earns 5–8.
            "moderate_consistency_cv_max": 0.25,
            # [proposed heuristic, R6] CV at or above this reaches zero.
            "poor_consistency_cv_zero_score": 0.50,
        },
        "stability": {
            # [proposed heuristic, R6] In-plane jitter at this value receives zero jitter credit.
            "jitter_zero_score_norm": 0.10,
            # [proposed heuristic, R6] Prevents a very brief still sample earning full control credit.
            "full_duration_credit_s": 1.0,
        },
    },
}
