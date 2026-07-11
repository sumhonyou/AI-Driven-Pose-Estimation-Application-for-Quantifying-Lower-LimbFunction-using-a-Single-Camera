// Client-side WBLT geometry + live angle/heel-lift tracker.
// Mirrors backend app/module_a/wblt/geometry.py so the live numbers the user
// sees (angle gauge, heel-down indicator) match the backend's official recompute.
// The backend's POST response is always authoritative; this is a zero-latency helper only.
//
// World-landmark convention: Y increases DOWNWARD (a lifted heel has a SMALLER y).

import { LM, type WorldLandmark } from "../../types/pose";
import {
  WBLT_HEEL_BASELINE_FRAMES,
  WBLT_HEEL_LIFT_HYSTERESIS_RATIO,
  WBLT_HEEL_LIFT_TOL_RATIO,
} from "../../config/moduleAThresholds";

/** Heel-lift tuning, normally sourced from GET /api/wblt/config so live
 * feedback matches the backend's official recompute; falls back to the
 * hardcoded moduleAThresholds constants if the config fetch hasn't landed yet. */
export type WbltHeelLiftConfig = {
  heelBaselineFrames: number;
  heelLiftTolRatio: number;
  heelLiftHysteresisRatio: number;
};

const DEFAULT_HEEL_LIFT_CONFIG: WbltHeelLiftConfig = {
  heelBaselineFrames: WBLT_HEEL_BASELINE_FRAMES,
  heelLiftTolRatio: WBLT_HEEL_LIFT_TOL_RATIO,
  heelLiftHysteresisRatio: WBLT_HEEL_LIFT_HYSTERESIS_RATIO,
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

/** Stateful per-attempt live tracker: heel-lift baseline + dorsiflexion angle. */
export function createWbltLiveTracker(
  leg: WbltLeg,
  heelLiftConfig: WbltHeelLiftConfig = DEFAULT_HEEL_LIFT_CONFIG,
) {
  const { heelBaselineFrames, heelLiftTolRatio, heelLiftHysteresisRatio } = heelLiftConfig;
  let calHeelY: number[] = [];
  let calShankLen: number[] = [];
  let baselineHeelY: number | null = null;
  let shankLen: number | null = null;
  let lifted = false;

  function reset() {
    calHeelY = [];
    calShankLen = [];
    baselineHeelY = null;
    shankLen = null;
    lifted = false;
  }

  function median(values: number[]): number {
    const sorted = [...values].sort((a, b) => a - b);
    return sorted[Math.floor(sorted.length / 2)];
  }

  function update(w: WorldLandmark[]): WbltLiveUpdate {
    if (!w || w.length < 33)
      return { calibrated: baselineHeelY !== null, heelLifted: lifted, thetaDeg: null };

    const knee = w[KNEE[leg]];
    const ankle = w[ANKLE[leg]];
    const heel = w[HEEL[leg]];
    const footIndex = w[FOOT_INDEX[leg]];

    if (baselineHeelY === null) {
      calHeelY.push(heel.y);
      calShankLen.push(shankLength(knee, ankle));
      if (calHeelY.length >= heelBaselineFrames) {
        baselineHeelY = median(calHeelY);
        shankLen = median(calShankLen) || 1e-6;
      }
      return { calibrated: baselineHeelY !== null, heelLifted: false, thetaDeg: null };
    }

    const riseRatio = (baselineHeelY - heel.y) / (shankLen as number);
    if (!lifted && riseRatio > heelLiftTolRatio) lifted = true;
    else if (lifted && riseRatio < heelLiftHysteresisRatio) lifted = false;

    const thetaDeg = lifted ? null : dorsiflexionAngleDeg(knee, ankle, heel, footIndex);
    return { calibrated: true, heelLifted: lifted, thetaDeg };
  }

  return { update, reset };
}
