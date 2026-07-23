// Frontend-only constants for Module A. Backend thresholds live in each exercise's
// own config.py (backend/app/module_a/{core,sts,wblt,sls}/config.py) — these are
// UX-only values (live counter estimate, buffer sampling), not the authoritative rules.

/** Frames-per-second sampled into the buffer sent to POST /api/module-a/analyze. */
export const SAMPLE_FPS = 15;

/** Live-estimate knee-angle thresholds (hysteresis) — the server recount is authoritative. */
export const LIVE_KNEE_STAND_ENTER = 160;
export const LIVE_KNEE_SIT_ENTER = 110;
/** Exit bands (mirrors backend KNEE_STAND_EXIT/KNEE_SIT_EXIT) — lets the live FSM
 * recognise a mid-stand wobble as continuing the same attempt instead of misreading
 * it as two separate rep-boundary events. */
export const LIVE_KNEE_STAND_EXIT = 150;
export const LIVE_KNEE_SIT_EXIT = 120;
/** Knee angle at which we consider someone to have started rising (used for failed-rep detection). */
export const LIVE_KNEE_RISING_ENTER = 130;
export const LIVE_MIN_REP_GAP_MS = 500;

export const STS_TARGET_REPS = 5;
/** Mirrors backend MAX_SESSION_SECONDS — auto-finalizes a session that never reaches
 * STS_TARGET_REPS valid reps instead of running forever. */
export const MAX_SESSION_SECONDS = 60;

// --- SLS REBUILD geometry — KEEP IN SYNC with backend app/module_a/sls/config.py ---
// These drive live feedback (lift-line, ball-in-circle) so the on-screen numbers
// match the backend's official recompute. Prototype values, tunable after pilot.
export const SLS_MAX_HOLD_SEC = 45; // per-leg hold cap (seconds)
export const SLS_CALIBRATION_SEC = 2.0; // both-feet-planted baseline window
export const SLS_LIFT_LINE_NORM = 0.15; // lift-line height / stance-leg length
export const SLS_LIFT_HYSTERESIS_NORM = 0.03; // drop margin below the line
// UAT remediation (T1, S5 "the lifting too sensitive"): a frame-count dwell made the
// debounce depend on the browser's actual frame rate (MediaPipe runs via
// requestAnimationFrame, so real rates vary well past the ~30fps the old 3-frame
// count assumed). A time-based minimum guarantees a genuine dwell regardless of
// frame rate. Mirrors backend app/module_a/sls/config.py.
export const SLS_LIFT_MIN_DWELL_SEC = 0.15; // min time above line to confirm a lift
export const SLS_DROP_MIN_DWELL_SEC = 0.1; // min time below hold-line to confirm a drop
// Provisional: tightened from 0.55 (too generous -- visible wobble never left
// the circle). Pending live-webcam validation; may move either direction once
// real resting/wobbling ball offsets are observed.
export const SLS_CIRCLE_RADIUS_NORM = 0.3; // tolerance-circle radius / hip width
// Consecutive frames required to flip the inside/outside circle state -- damps
// single-frame landmark jitter without adding real scoring lag.
export const SLS_CIRCLE_PERSIST_FRAMES = 2;
export const SLS_LEG_ORDER = ["right", "left"] as const; // prompted lift order

/** Below this capture-quality score, live feedback should warn the user instead of showing progress. */
export const LIVE_MIN_VISIBILITY = 0.6;
/** Below this average per-rep capture quality, the live estimator's optimistic
 * guess for why a rep didn't count is "low visibility" — stricter than
 * LIVE_MIN_VISIBILITY since it judges a whole completed attempt, not one frame. */
export const LIVE_MIN_QUALITY_FOR_VALID_REP = 0.7;

// --- WBLT (Weight-Bearing Lunge Test) fallback values, used only until
// GET /api/wblt/config resolves (see wbltGeometry.ts's createWbltLiveTracker).
// Once fetched, the live tracker uses the backend's app/module_a/wblt/config.py
// values directly, so these never need hand-syncing after that point.
export const WBLT_CALIBRATION_SECONDS = 2; // "stand still, foot flat" window length
export const WBLT_HEEL_MIN_CALIBRATION_FRAMES = 5; // fewest baseline frames to trust a calibration
export const WBLT_HEEL_LIFT_TOL_RATIO = 0.1; // heel rise / shank length -> lifted
export const WBLT_HEEL_LIFT_HYSTERESIS_RATIO = 0.06;
export const WBLT_HEEL_LIFT_DEBOUNCE_FRAMES = 3; // consecutive raised frames before a lift latches
