"""Squat exercise identity, scoring policy, and movement thresholds."""

SQUAT_CONFIG = {
    # Stable REHAB24-6 exercise identifier.
    "exercise_code": "squat",
    # [dataset-derived] REHAB24-6/runtime-compatible sagittal capture orientation.
    "required_view": "side_view",
    # Model artifact key under ml/artifacts/.
    "model_key": "squat",
    # Binary Good/Poor policy. The UI displays stored "Poor" as "Needs Improvement".
    # The threshold is applied per rep, then the set band is a strict majority vote.
    "band_policy": {
        "scheme": "binary",
        "decision_threshold": 8.447974,
        "w_rule": 0.0,
        "w_ml": 1.0,
        "aggregation": "majority_vote",
    },
    # Dataset-derived normalization reference with the lowest cross-subject spread.
    "norm_ref_strategy": "trunk_length",
    "segmentation": {
        # [proposed heuristic, R9] Flexion from standing that starts a descent.
        "enter_descending_deg": 30.0,
        # [proposed heuristic, R9] Lower exit creates hysteresis against jitter.
        "exit_standing_deg": 20.0,
        # [proposed heuristic, R9] Blocks a rebound from becoming a second rep.
        "refractory_s": 0.5,
        # [proposed heuristic, R9] Rejects very brief threshold-noise candidates.
        "min_rep_duration_s": 0.5,
        # Counts a final rep whose capture stopped inside the 20-30 deg hysteresis
        # deadband: without this the set loses a rep the user actually completed.
        "flush_trailing_rep": True,
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
    # Interpretable per-rep fault gates. Each threshold has its own provenance.
    "fault_gates": {
        "depth": {
            "enabled": True,
            # Clinical parallel-squat floor adjusted for measured camera under-read.
            "min_knee_flex_peak_deg": 78.04,
            "tag": "insufficient_depth",
            # Keep this message angle aligned with min_knee_flex_peak_deg.
            "message": "Didn't reach enough depth — aim for a knee bend of at least 78° (thighs close to parallel).",
        },
        "lean": {
            "enabled": True,
            # Dataset-derived trunk-lean fault threshold.
            "fault_trunk_lean_peak_deg": 41.42411876009375,
            "tag": "excessive_forward_lean",
            "message": "Leaning too far forward — keep your chest more upright.",
        },
        "heel_rise": {
            "enabled": True,
            # Dataset-derived near-leg heel-rise threshold, outside the ML feature schema.
            "fault_heel_rise_peak_norm": 0.07098522548163665,
            "tag": "heel_lift",
            "message": "Heels lifting off the floor — keep your weight through your heels.",
        },
    },
}
