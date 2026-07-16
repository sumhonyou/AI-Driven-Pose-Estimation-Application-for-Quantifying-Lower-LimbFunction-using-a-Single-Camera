"""Frozen Module B defaults for the Phase 4 squat slice."""

MODULE_B_CORE_CONFIG = {
    # [proposed heuristic, fixed by D6 / proposal Table 6]
    "band_thresholds": {
        "poor": {
            "min_inclusive": 0.0,
            "max_exclusive": 4.0,
        },
        "fair": {
            "min_inclusive": 4.0,
            "max_exclusive": 7.0,
        },
        "good": {
            "min_inclusive": 7.0,
            "max_inclusive": 10.0,
        },
    },
    # [dataset-derived, Stage 5.6] Iterated joint sweep (confidence_low_threshold <->
    # w_rule, coordinate ascent to a fixed point) over 98 out-of-fold-scored side-view
    # reps: at the old 0.4/0.6 split, the ROM rule sub-score is *inverted* for this
    # population (median 8.83 for Poor vs 7.71 for Good, since Poor reps are deeper —
    # see Stage 5.4/5.5), so no repetition could ever be banded Poor at all. w_rule=0.2
    # minimises the rule score's (harmful, here) influence: 0 severe misclassifications
    # (Poor->Good / Good->Poor) at confidence_low_threshold=0.85, versus the same 0
    # severe count but recall(Poor)=0 (every Poor rep silently routed to Fair, none
    # ever caught) at both this old default and the architecture doc's §10.4
    # recommendation (w_rule=0.6). See ml/reports/SQUAT_FUSION_SWEEP.md.
    "w_rule_default": 0.2,
    # [dataset-derived, Stage 5.6] w_ml = 1 - w_rule_default. See above.
    "w_ml_default": 0.8,
    # [proposed heuristic, R7]
    "w_rule_low_confidence": 0.7,
    # [dataset-derived, Stage 5.6] Swept jointly with the fusion weight above (see
    # ml/reports/SQUAT_FUSION_SWEEP.md); smallest candidate reaching >=0.90 precision
    # on both confidently-classified classes at the converged w_rule=0.2. Deliberately
    # trades a 46.9% Fair-band coverage rate for 0 severe misclassifications.
    "confidence_low_threshold": 0.85,
    # [proposed heuristic, proposal Section 3.3.1 Tables 3 and 4]
    "q_min": 0.6,
    # [proposed heuristic, proposal Section 3.3.1 Tables 3 and 4]
    "confidence_threshold": 0.6,
    # [proposed heuristic, proposal Section 3.3.1 Tables 3 and 4]
    "quality_bands": {
        "good": {
            "min_inclusive": 0.85,
        },
        "moderate": {
            "min_inclusive": 0.70,
            "max_exclusive": 0.85,
        },
        "poor": {
            "min_inclusive": 0.0,
            "max_exclusive": 0.70,
        },
    },
    # [proposed heuristic, proposal Section 3.3.2]
    "feature_schema_version": "1.0.0",
    # [proposed heuristic, proposal Section 3.3.2]
    "interpolation_max_gap_frames": 5,
}
