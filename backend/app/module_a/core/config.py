"""Shared Module A thresholds — constants used across STS, SLS, and WBLT.

Exercise-specific thresholds live in each exercise's own config.py
(app/module_a/sts/config.py, app/module_a/wblt/config.py, app/module_a/sls/config.py).
Keep thresholds here only if genuinely shared; do not hardcode them elsewhere.
"""

# --- Landmark quality ---
MIN_VISIBILITY = 0.6  # landmark ignored (hold-last) below this visibility

# --- Calibration ---
CALIBRATION_SECONDS = 2.0  # initial window used to establish a "standing" baseline

# --- Session limits ---
MAX_SESSION_SECONDS = 60

# --- Capture-quality bands ---
QUALITY_GOOD_MIN = 0.85
QUALITY_MODERATE_MIN = 0.70

# --- Score bands (0-10 scale, proposal Table 6) ---
SCORE_POOR_MAX = 4.0
SCORE_FAIR_MAX = 7.0

# --- Trunk lean ---
TRUNK_LEAN_EXCESSIVE_DEG = 25.0

# --- Landmark logging (evaluation / replay harness) ---
ENABLE_LANDMARK_LOGGING = True
