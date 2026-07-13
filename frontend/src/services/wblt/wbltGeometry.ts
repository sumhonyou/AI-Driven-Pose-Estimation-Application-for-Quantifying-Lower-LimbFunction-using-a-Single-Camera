// Client-side WBLT geometry + live angle/heel-lift tracker.
// Mirrors backend app/module_a/wblt/geometry.py so the live numbers the user
// sees (angle gauge, heel-down indicator) match the backend's official recompute.
// The backend's POST response is always authoritative; this is a zero-latency helper only.
//
// World-landmark convention: Y increases DOWNWARD (a lifted heel has a SMALLER y).

import { LM, type WorldLandmark } from "../../types/pose";
import {
  WBLT_CALIBRATION_SECONDS,
  WBLT_HEEL_LIFT_DEBOUNCE_FRAMES,
  WBLT_HEEL_LIFT_HYSTERESIS_RATIO,
  WBLT_HEEL_LIFT_TOL_RATIO,
  WBLT_HEEL_MIN_CALIBRATION_FRAMES,
} from "../../config/moduleAThresholds";
import { LandmarkSmoother } from "../../utils/oneEuroFilter";

/** Heel-lift tuning, normally sourced from GET /api/wblt/config so live
 * feedback matches the backend's official recompute; falls back to the
 * hardcoded moduleAThresholds constants if the config fetch hasn't landed yet. */
export type WbltHeelLiftConfig = {
  calibrationSeconds: number;
  heelMinCalibrationFrames: number;
  heelLiftTolRatio: number;
  heelLiftHysteresisRatio: number;
  heelLiftDebounceFrames: number;
};

const DEFAULT_HEEL_LIFT_CONFIG: WbltHeelLiftConfig = {
  calibrationSeconds: WBLT_CALIBRATION_SECONDS,
  heelMinCalibrationFrames: WBLT_HEEL_MIN_CALIBRATION_FRAMES,
  heelLiftTolRatio: WBLT_HEEL_LIFT_TOL_RATIO,
  heelLiftHysteresisRatio: WBLT_HEEL_LIFT_HYSTERESIS_RATIO,
  heelLiftDebounceFrames: WBLT_HEEL_LIFT_DEBOUNCE_FRAMES,
};

export type WbltLeg = "left" | "right";

const KNEE: Record<WbltLeg, number> = { left: LM.LEFT_KNEE, right: LM.RIGHT_KNEE };
const ANKLE: Record<WbltLeg, number> = { left: LM.LEFT_ANKLE, right: LM.RIGHT_ANKLE };
const HEEL: Record<WbltLeg, number> = { left: LM.LEFT_HEEL, right: LM.RIGHT_HEEL };
const FOOT_INDEX: Record<WbltLeg, number> = {
  left: LM.LEFT_FOOT_INDEX,
  right: LM.RIGHT_FOOT_INDEX,
};

type Vec3 = [number, number, number];
const UP: Vec3 = [0, -1, 0];

function sub(a: WorldLandmark, b: WorldLandmark): Vec3 {
  return [a.x - b.x, a.y - b.y, a.z - b.z];
}
function dot(a: Vec3, b: Vec3): number {
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}
function cross(a: Vec3, b: Vec3): Vec3 {
  return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
}
function norm(a: Vec3): number {
  return Math.sqrt(dot(a, a));
}
function normalize(a: Vec3): Vec3 {
  const n = norm(a);
  if (n < 1e-9) return [0, 0, 0];
  return [a[0] / n, a[1] / n, a[2] / n];
}
function scale(a: Vec3, s: number): Vec3 {
  return [a[0] * s, a[1] * s, a[2] * s];
}
function vsub(a: Vec3, b: Vec3): Vec3 {
  return [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
}

export function sagittalSideAxis(heel: WorldLandmark, footIndex: WorldLandmark): Vec3 {
  const forwardRaw = sub(footIndex, heel);
  const forwardOrth = vsub(forwardRaw, scale(UP, dot(forwardRaw, UP)));
  const forward = normalize(forwardOrth);
  if (forward[0] === 0 && forward[1] === 0 && forward[2] === 0) return [0, 0, 0];
  return normalize(cross(UP, forward));
}

/** Ankle dorsiflexion angle (degrees): angle between the in-plane shank and vertical. */
export function dorsiflexionAngleDeg(
  knee: WorldLandmark,
  ankle: WorldLandmark,
  heel: WorldLandmark,
  footIndex: WorldLandmark,
): number | null {
  const side = sagittalSideAxis(heel, footIndex);
  if (side[0] === 0 && side[1] === 0 && side[2] === 0) return null;
  const shank = sub(knee, ankle);
  const shankInplane = vsub(shank, scale(side, dot(shank, side)));
  const shankUnit = normalize(shankInplane);
  if (shankUnit[0] === 0 && shankUnit[1] === 0 && shankUnit[2] === 0) return null;
  const cosTheta = Math.max(-1, Math.min(1, dot(shankUnit, UP)));
  return (Math.acos(cosTheta) * 180) / Math.PI;
}

export function shankLength(knee: WorldLandmark, ankle: WorldLandmark): number {
  return norm(sub(knee, ankle));
}

export interface WbltLiveUpdate {
  calibrated: boolean;
  heelLifted: boolean;
  thetaDeg: number | null;
}

/** Stateful per-attempt live tracker: heel-lift baseline + dorsiflexion angle.
 *
 * Calibration finalizes on a FRAME-TIMESTAMP boundary, not a UI timer: the
 * tracker records the timestamp of its own first frame, and once a later
 * frame's time-since-first exceeds `calibrationSeconds`, it locks the baseline
 * from whatever was collected and evaluates THAT SAME frame for a lift — this
 * mirrors backend analysis.py's loop EXACTLY (`if t <= CALIBRATION_SECONDS:
 * feed_calibration(); continue` / `else: finalize()`), frame for frame, using
 * the same clock the posted frames' timestampMs comes from. A page-level UI
 * countdown can still show "2...1...0" for the user, but it no longer decides
 * which frames count as baseline vs hold — that was the actual bug behind
 * live/backend detection disagreements (a UI setInterval can drift a frame or
 * two relative to the backend's timestamp-exact boundary). finalizeCalibration()
 * is kept as an idempotent manual safety net a caller may still invoke.
 *
 * Landmarks are smoothed with the SAME One Euro Filter the backend applies
 * (LandmarkSmoother, see analysis.py) before any geometry runs, for the same
 * reason: reacting to raw/noisy landmarks while the backend smooths first is
 * another way the two can disagree on borderline signals. Caller must pass a
 * monotonically increasing timestamp (seconds) — use the SAME clock/values that
 * get posted as each frame's timestampMs so both the filter's dt sequence and
 * the calibration boundary match what the backend recomputes from. */
export function createWbltLiveTracker(
  leg: WbltLeg,
  heelLiftConfig: WbltHeelLiftConfig = DEFAULT_HEEL_LIFT_CONFIG,
) {
  const { calibrationSeconds, heelLiftTolRatio, heelLiftHysteresisRatio } = heelLiftConfig;
  const minCalibrationFrames = Math.max(1, heelLiftConfig.heelMinCalibrationFrames);
  const debounceFrames = Math.max(1, heelLiftConfig.heelLiftDebounceFrames);
  let calHeelY: number[] = [];
  let calShankLen: number[] = [];
  let baselineHeelY: number | null = null;
  let shankLen: number | null = null;
  let lifted = false;
  let liftStreak = 0;
  let smoother = new LandmarkSmoother<WorldLandmark>();
  let firstTimestampSec: number | null = null;

  function reset() {
    calHeelY = [];
    calShankLen = [];
    baselineHeelY = null;
    shankLen = null;
    lifted = false;
    liftStreak = 0;
    smoother = new LandmarkSmoother<WorldLandmark>();
    firstTimestampSec = null;
  }

  function median(values: number[]): number {
    const sorted = [...values].sort((a, b) => a - b);
    return sorted[Math.floor(sorted.length / 2)];
  }

  /** Lock the baseline from whatever calibration frames were collected. Returns
   * whether calibration actually succeeded (enough foot-flat frames were seen).
   * Idempotent — safe to call more than once. Normally fires automatically from
   * within update() at the frame-timestamp boundary; exposed for a caller that
   * wants to force it (e.g. a UI-driven safety net). */
  function finalizeCalibration(): boolean {
    if (baselineHeelY !== null) return true;
    if (calHeelY.length < minCalibrationFrames) return false;
    baselineHeelY = median(calHeelY);
    shankLen = median(calShankLen) || 1e-6;
    return true;
  }

  function update(rawW: WorldLandmark[], timestampSec: number): WbltLiveUpdate {
    if (!rawW || rawW.length < 33)
      return { calibrated: baselineHeelY !== null, heelLifted: lifted, thetaDeg: null };

    if (firstTimestampSec === null) firstTimestampSec = timestampSec;
    const relativeSec = timestampSec - firstTimestampSec;

    const w = smoother.smoothFrame(timestampSec, rawW);
    const knee = w[KNEE[leg]];
    const ankle = w[ANKLE[leg]];
    const heel = w[HEEL[leg]];
    const footIndex = w[FOOT_INDEX[leg]];

    if (baselineHeelY === null) {
      if (relativeSec <= calibrationSeconds) {
        // Still inside the calibration window (by frame timestamp, not a UI
        // timer) -- accumulate and don't evaluate this frame for a lift yet.
        calHeelY.push(heel.y);
        calShankLen.push(shankLength(knee, ankle));
        return { calibrated: false, heelLifted: false, thetaDeg: null };
      }
      // Boundary crossed -- finalize now, using whatever was collected, then
      // fall through to evaluate THIS frame for a lift (no early return here),
      // exactly like the backend's loop does.
      if (!finalizeCalibration()) {
        return { calibrated: false, heelLifted: false, thetaDeg: null };
      }
    }

    // Y increases downward -> a raised heel has a SMALLER y than baseline.
    const riseRatio = ((baselineHeelY as number) - heel.y) / (shankLen as number);
    if (riseRatio > heelLiftTolRatio) liftStreak += 1;
    else if (riseRatio < heelLiftHysteresisRatio) liftStreak = 0;
    // else: dead zone between hysteresis and tolerance -- hold the streak as-is.
    if (!lifted) {
      if (liftStreak >= debounceFrames) lifted = true;
    } else if (riseRatio < heelLiftHysteresisRatio) {
      lifted = false;
    }
    // Exclude a frame from the live angle whenever its own heel is up, but only
    // surface heelLifted (the HUD / auto-abort signal) once the debounced state
    // has latched -- mirrors backend geometry.HeelLiftDetector exactly.
    const frameHeelUp = riseRatio > heelLiftTolRatio;
    const thetaDeg = frameHeelUp ? null : dorsiflexionAngleDeg(knee, ankle, heel, footIndex);
    return { calibrated: true, heelLifted: lifted, thetaDeg };
  }

  return { update, reset, finalizeCalibration };
}
