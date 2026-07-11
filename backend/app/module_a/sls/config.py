"""Single-Leg Stance (SLS) thresholds — both legs, lift-line gate, ball-in-circle stability.

Prototype starting values — conservative, tunable after pilot testing.
"""

# Re-exported so sls/analysis.py and sls/scoring.py can keep addressing every
# threshold they need through a single `config.` import, same as before the
# per-exercise config split.
from app.module_a.core.config import (CALIBRATION_SECONDS, MIN_VISIBILITY,
                                      SCORE_FAIR_MAX, SCORE_POOR_MAX)

SLS_MAX_HOLD_SEC = 45.0  # per-leg hold cap (seconds)
SLS_LEG_ORDER = ("right", "left")  # prompted lift order (right first, then left)
# Lift-line height as a fraction of the stance leg length (hip->ankle). Scale-invariant.
SLS_LIFT_LINE_NORM = 0.15
SLS_LIFT_HYSTERESIS_NORM = 0.03  # margin below the line before a drop is confirmed
SLS_LIFT_PERSIST_FRAMES = 3  # consecutive frames above line to confirm a lift
SLS_DROP_PERSIST_FRAMES = 3  # consecutive frames below line to confirm a drop
# Tolerance-circle radius as a fraction of hip width (|left_hip - right_hip|).
# Provisional: tightened from 0.55 (too generous -- visible wobble never left the
# circle). Pending live-webcam validation; may need to move either direction once
# real resting/wobbling ball offsets are observed (see fsm.CircleDebouncer).
SLS_CIRCLE_RADIUS_NORM = 0.30
# Consecutive frames required to flip the inside/outside circle state -- damps
# single-frame landmark jitter without adding real scoring lag.
SLS_CIRCLE_PERSIST_FRAMES = 2
# Combined score = hold_weight * hold_score + stability_weight * stability_score
SLS_HOLD_WEIGHT = 0.5
SLS_STABILITY_WEIGHT = 0.5
# Hold sub-score piecewise breakpoints (seconds) — band-aligned to Table 6.
SLS_HOLD_POOR_MAX_SEC = 10.0  # 0-10s  -> Poor band (score 0-4)
SLS_HOLD_FAIR_MAX_SEC = 25.0  # 10-25s -> Fair band (score 4-7)
# 25-45s -> Good band (score 7-10)
SLS_MIN_VALID_FRAME_RATIO = 0.8  # below this, capture quality invalidates a hold
