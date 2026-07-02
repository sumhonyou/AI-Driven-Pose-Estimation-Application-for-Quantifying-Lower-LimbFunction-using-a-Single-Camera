"""Module A thresholds — single source of truth for STS rule-based checking.

All numbers below come from the PhysioFit Module A blueprint (§5.1 / §6 / §12).
Keep thresholds here only; do not hardcode them elsewhere.
"""

# --- Landmark quality ---
MIN_VISIBILITY = 0.6  # landmark ignored (hold-last) below this visibility

# --- Calibration ---
CALIBRATION_SECONDS = 2.0  # initial window used to establish a "standing" baseline

# --- Knee-angle hysteresis FSM (degrees) ---
KNEE_STAND_ENTER = 160.0
KNEE_STAND_EXIT = 150.0
KNEE_SIT_ENTER = 110.0
KNEE_SIT_EXIT = 120.0

# --- Rep confirmation ---
HIP_RISE_CONFIRM_M = 0.08  # min hip-height rise (meters) to confirm a stand
MIN_REP_GAP_MS = 500  # refractory period between reps to avoid double counting

# --- Session limits ---
MAX_SESSION_SECONDS = 60
TARGET_REP_COUNT = 5

# --- Capture-quality bands ---
QUALITY_GOOD_MIN = 0.85
QUALITY_MODERATE_MIN = 0.70

# --- Score bands (0-10 scale, proposal Table 6) ---
SCORE_POOR_MAX = 4.0
SCORE_FAIR_MAX = 7.0

# --- STS time bands (5 reps) ---
TIME_GOOD_MAX_SEC = 12.0
TIME_FAIR_MAX_SEC = 16.0

# --- Trunk lean ---
TRUNK_LEAN_EXCESSIVE_DEG = 25.0

# --- Landmark logging (evaluation / replay harness) ---
ENABLE_LANDMARK_LOGGING = False
