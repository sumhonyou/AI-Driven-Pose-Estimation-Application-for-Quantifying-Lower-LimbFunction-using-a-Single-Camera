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
    "segmentation": {
        # [proposed heuristic, R9] Flexion from standing that starts a descent.
        # Same value as squat's Stage 4.3: REHAB24-6 Segmentation.csv (Ex5, n=174)
        # measures a mean rep duration of 3.37s vs squat Ex6's 3.31s (n=195) and a
        # near-identical median (3.33s vs 3.20s) -- the two movements' overall
        # rep-timing envelope is close enough that squat's tuned starting point
        # transfers, pending Stage 5.4's own empirical check on real lunge reps.
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
            # [proposed heuristic] NOT [clinical norm] -- unlike squat's S1-sourced
            # bands, Q6 confirms no published normative lunge front-knee angle
            # table exists. These reuse squat's exact band edges as an interim
            # starting point (the "front knee to ~90 deg" cue is a coaching
            # convention, not a sourced cutoff) -- Stage 5.6 (Lunge) replaces them
            # with edges calibrated from REHAB24-6's own correct-rep distribution
            # and re-tags them [dataset-derived], per that stage's own delta.
            "shallow_start_deg": 60.0,
            "parallel_start_deg": 90.0,
            "deep_start_deg": 110.0,
            "deep_full_score_deg": 130.0,
            # [proposed heuristic, R3] Low shank-forward proxy may indicate limited DF.
            "df_limit_proxy_max_deg": 20.0,
            # [proposed heuristic, R3] Avoids treating a possible mobility cap as zero control.
            "df_limit_score_floor": 2.0,
        },
        "tempo": {
            # [proposed heuristic, R6] Consistent duration CV earns 9-10. No delta
            # from squat: both movements' rep-timing envelopes measured near-
            # identical in Stage 4.3's research (mean 3.37s vs 3.31s).
            "high_consistency_cv_max": 0.10,
            # [proposed heuristic, R6] Moderate duration CV earns 5-8.
            "moderate_consistency_cv_max": 0.25,
            # [proposed heuristic, R6] CV at or above this reaches zero.
            "poor_consistency_cv_zero_score": 0.50,
        },
        "stability": {
            # [proposed heuristic, R6] In-plane jitter at this value receives zero
            # jitter credit. No delta from squat: hip_mid_jitter_norm is a central
            # (both-hips-midpoint) signal, not lead-leg-specific.
            "jitter_zero_score_norm": 0.10,
            # [proposed heuristic, R6] Prevents a very brief still sample earning full control credit.
            "full_duration_credit_s": 1.0,
        },
        "symmetry": {
            # [proposed heuristic, R5.2, HY 2026-07-17] Cross-rep only (a lunge's
            # front/back knees do different jobs, so within-rep L-vs-R is
            # meaningless -- task.md's Stage 4.4 delta). HY decided this is a
            # report-only metric (SubScore.score stays None; see
            # core/rules.py's SubScore.metrics), never part of S_rule, and that
            # 1 rep per leg is enough to attempt the comparison (mirrors Tempo's
            # score-as-soon-as-computable philosophy over waiting for a larger N).
            "min_reps_per_leg": 1,
        },
    },
}
