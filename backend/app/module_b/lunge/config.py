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
    # Cycle segmentation, NOT absolute threshold-crossing. This replaced squat's
    # borrowed enter/exit thresholds (enter_descending_deg=30 / exit_standing_deg=20)
    # after Stage 5.3 (Lunge) measured them at 50/88 = 56.8% rep recall against
    # REHAB24-6's physio-verified boundaries, versus squat's 93/98 = 94.9%.
    #
    # Why the old model could not be rescued by retuning, measured not argued: a
    # lunge set is performed *continuously* (the dataset annotates reps back-to-back,
    # median 1-frame gap), and subjects differ in how far they straighten at the top
    # of each cycle. A single global (enter, exit) pair would need exit > 60.0 deg
    # (one subject's worst cycle top) AND enter < 14.8 deg (another's weakest rep
    # peak) AND exit < enter -- arithmetically impossible. Driving off the front knee
    # only was measured *worse* (subjects rest with the front knee more flexed than
    # the bilateral mean), and a per-clip baseline-relative threshold failed globally
    # too. Absolute posture thresholds cannot separate these subjects because rest
    # posture and rep depth overlap *across* them; cycle shape can.
    #
    # A squat necessarily returns to a two-legs-extended stance so its mean flexion
    # reliably falls to baseline; a lunge carries no such requirement. This is the
    # empirical check Stage 4.3 (Lunge) recorded the borrowed thresholds as pending.
    "segmentation": {
        # [dataset-derived, Stage 5.3 (Lunge) sweep] How far the bilateral-mean knee
        # flexion must fall from a local maximum (or rise from a local minimum) for
        # that extremum to be confirmed -- i.e. the minimum swing depth of a real rep
        # cycle. Serves the noise-rejection role the old hysteresis deadband and
        # refractory window served, in cycle terms rather than absolute-posture terms.
        #
        # Swept 10-30 deg against REHAB24-6's physio-verified boundaries. Selection
        # rule, fixed before reading the numbers: the **largest** prominence that still
        # recovers every side-view rep (higher prominence = stricter = fewer spurious
        # detections, so take the strictest setting that costs no recall). 17.5 deg is
        # that value -- front-rep recall 88/88 (100%) and precision 99.4%, detecting
        # exactly 174 reps against 174 annotated. It sits mid-plateau, not on a knife
        # edge: 10-17.5 deg all hold 100% recall while precision climbs monotonically
        # (86.5% -> 99.4%), and recall only starts falling at 20 deg (87/88).
        #
        # Honest caveat: this was tuned on the same cohort it is measured against, so
        # 99.4% is an in-sample figure, not a generalisation estimate. The plateau's
        # width is the reason to believe it is not a fluke of one threshold.
        "cycle_prominence_deg": 17.5,
        # [proposed heuristic, R9] Rejects very brief spurious cycles. Unchanged.
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
