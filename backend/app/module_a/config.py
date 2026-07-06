"""Module A thresholds — single source of truth for rule-based checking.

All numbers below come from the PhysioFit Module A blueprint (§5.1 / §6 / §12).
Keep thresholds here only; do not hardcode them elsewhere.
"""

# --- Landmark quality ---
MIN_VISIBILITY = 0.6  # landmark ignored (hold-last) below this visibility

# --- Calibration ---
CALIBRATION_SECONDS = 2.0  # initial window used to establish a "standing" baseline

# --- STS: Knee-angle hysteresis FSM (degrees) ---
KNEE_STAND_ENTER = 160.0
KNEE_STAND_EXIT = 150.0
KNEE_SIT_ENTER = 110.0
KNEE_SIT_EXIT = 120.0

# --- Rep confirmation ---
MIN_REP_GAP_MS = 500  # refractory period between reps to avoid double counting

# --- Session limits ---
MAX_SESSION_SECONDS = 60
TARGET_REP_COUNT = 5  # STS: 5 reps
TARGET_SLS_HOLD_SEC = 30.0  # Single-Leg Stance: 30 seconds

# --- SLS: Balance/sway detection ---
MAX_HIP_SWAY_M = 0.15  # max lateral hip displacement to stay "balanced" (meters)
MAX_ANKLE_SWAY_M = 0.20  # max lateral ankle displacement (meters)
SWAY_SAMPLE_WINDOW_FRAMES = 10  # smoothing window for sway detection

# --- Capture-quality bands ---
QUALITY_GOOD_MIN = 0.85
QUALITY_MODERATE_MIN = 0.70

# --- Score bands (0-10 scale, proposal Table 6) ---
SCORE_POOR_MAX = 4.0
SCORE_FAIR_MAX = 7.0

# --- STS time bands (5 reps) ---
TIME_GOOD_MAX_SEC = 12.0
TIME_FAIR_MAX_SEC = 16.0

# --- SLS hold-quality bands (30-second max) ---
# Hold duration at sustained single-leg: <10s (poor), 10-20s (fair), 20-30s (good)
HOLD_GOOD_MIN_SEC = 20.0
HOLD_FAIR_MIN_SEC = 10.0

# --- Trunk lean ---
TRUNK_LEAN_EXCESSIVE_DEG = 25.0

# --- Landmark logging (evaluation / replay harness) ---
ENABLE_LANDMARK_LOGGING = True
