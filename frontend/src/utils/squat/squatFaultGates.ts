// Client-side port of backend app/module_b/squat/fault_gates.py, so a rep with a named
// fault can be rejected the moment it happens instead of only at the end of the set.
//
// The backend stays authoritative: it re-runs these gates over every rep and its result
// is what the report shows. This port exists purely so the user gets an immediate reason
// and the faulty rep does not advance their target.
//
// Thresholds are NEVER hardcoded here -- they arrive from GET /api/module-b/squat/config
// (which serves the whole SQUAT_CONFIG, fault_gates block included).
import { LM, type WorldLandmark } from "../../types/pose";
import { LIVE_MIN_VISIBILITY } from "../../config/moduleAThresholds";

/** Mirrors backend app/module_a/core/config.py's MIN_VISIBILITY (0.6). */
const MIN_VISIBILITY = LIVE_MIN_VISIBILITY;
// Heel-rise measurement uses a short settle baseline and debounce window.
const SETTLE_WINDOW_FRAMES = 3;
const DEBOUNCE_FRAMES = 3;

export type SquatFaultTag = "insufficient_depth" | "excessive_forward_lean" | "heel_lift";

export interface SquatFaultGateConfig {
  depthEnabled: boolean;
  /** Rep fails when peak knee flexion stays BELOW this (clinical floor, not learned). */
  minKneeFlexPeakDeg: number;
  leanEnabled: boolean;
  /** Rep fails when peak trunk lean REACHES this. */
  faultTrunkLeanPeakDeg: number;
  heelRiseEnabled: boolean;
  /** Rep fails when normalised peak heel rise REACHES this. */
  faultHeelRisePeakNorm: number;
}

/** Per-rep measurements the gates read, accumulated live over the rep's frames. */
export interface RepGateMetrics {
  kneeFlexPeakDeg: number;
  trunkLeanPeakDeg: number;
  /** null when the heel/toe landmarks were never reliable enough to judge. */
  heelRisePeakNorm: number | null;
}

/** Backend parity: same comparison directions as fault_gates.py's three predicates.
 * A null heelRisePeakNorm skips only the heel gate; the others still apply. */
export function evaluateSquatFaultGates(
  metrics: RepGateMetrics,
  config: SquatFaultGateConfig,
): SquatFaultTag[] {
  const failed: SquatFaultTag[] = [];
  if (config.depthEnabled && metrics.kneeFlexPeakDeg < config.minKneeFlexPeakDeg) {
    failed.push("insufficient_depth");
  }
  if (config.leanEnabled && metrics.trunkLeanPeakDeg >= config.faultTrunkLeanPeakDeg) {
    failed.push("excessive_forward_lean");
  }
  if (
    config.heelRiseEnabled &&
    metrics.heelRisePeakNorm !== null &&
    metrics.heelRisePeakNorm >= config.faultHeelRisePeakNorm
  ) {
    failed.push("heel_lift");
  }
  return failed;
}

/** One side's (toe_y - heel_y). y is DOWN in MediaPipe world space, so a positive
 * value means the heel sits higher than the grounded toe. Mirrors `_toe_heel_lift`. */
function toeHeelLift(w: WorldLandmark[], side: "left" | "right"): number {
  return side === "left"
    ? w[LM.LEFT_FOOT_INDEX].y - w[LM.LEFT_HEEL].y
    : w[LM.RIGHT_FOOT_INDEX].y - w[LM.RIGHT_HEEL].y;
}

/** Mean heel+toe landmark visibility for one leg. Mirrors `_leg_visibility`. */
function legVisibility(w: WorldLandmark[], side: "left" | "right"): number {
  const heel = w[side === "left" ? LM.LEFT_HEEL : LM.RIGHT_HEEL];
  const toe = w[side === "left" ? LM.LEFT_FOOT_INDEX : LM.RIGHT_FOOT_INDEX];
  return ((heel?.visibility ?? 0) + (toe?.visibility ?? 0)) / 2;
}

/** Shoulder-midpoint to hip-midpoint distance -- the normalisation reference, mirroring
 * `_trunk_length` (and squat's `norm_ref_strategy = "trunk_length"`). */
export function trunkLength(w: WorldLandmark[]): number {
  const sx = (w[LM.LEFT_SHOULDER].x + w[LM.RIGHT_SHOULDER].x) / 2;
  const sy = (w[LM.LEFT_SHOULDER].y + w[LM.RIGHT_SHOULDER].y) / 2;
  const sz = (w[LM.LEFT_SHOULDER].z + w[LM.RIGHT_SHOULDER].z) / 2;
  const hx = (w[LM.LEFT_HIP].x + w[LM.RIGHT_HIP].x) / 2;
  const hy = (w[LM.LEFT_HIP].y + w[LM.RIGHT_HIP].y) / 2;
  const hz = (w[LM.LEFT_HIP].z + w[LM.RIGHT_HIP].z) / 2;
  return Math.sqrt((sx - hx) ** 2 + (sy - hy) ** 2 + (sz - hz) ** 2);
}

function mean(values: number[]): number {
  return values.reduce((sum, v) => sum + v, 0) / values.length;
}

function median(values: number[]): number {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.floor(sorted.length / 2)];
}

/** Accumulates one rep's heel-rise measurement frame by frame.
 *
 * Mirrors the backend construction: choose the better-tracked leg, use a median
 * settle baseline, and require a sustained rise across the debounce window. */
export function createHeelRiseTracker() {
  const leftLifts: number[] = [];
  const rightLifts: number[] = [];
  const leftVisibility: number[] = [];
  const rightVisibility: number[] = [];
  let trunkSum = 0;
  let frames = 0;

  return {
    record(w: WorldLandmark[]) {
      leftLifts.push(toeHeelLift(w, "left"));
      rightLifts.push(toeHeelLift(w, "right"));
      leftVisibility.push(legVisibility(w, "left"));
      rightVisibility.push(legVisibility(w, "right"));
      trunkSum += trunkLength(w);
      frames += 1;
    },
    /** null when the rep was never measurable, or the near leg wasn't reliably
     * visible for the rep (fail-safe: never guess from a foot we can't see). */
    result(): number | null {
      if (frames === 0) return null;
      const meanTrunk = trunkSum / frames;
      if (meanTrunk < 1e-9) return null;

      const meanLeftVisibility = mean(leftVisibility);
      const meanRightVisibility = mean(rightVisibility);
      const nearIsLeft = meanLeftVisibility >= meanRightVisibility;
      const nearVisibility = nearIsLeft ? meanLeftVisibility : meanRightVisibility;
      if (nearVisibility < MIN_VISIBILITY) return null;

      const nearLifts = nearIsLeft ? leftLifts : rightLifts;
      const settle = nearLifts.slice(0, Math.min(SETTLE_WINDOW_FRAMES, nearLifts.length));
      const baseline = median(settle);
      const rises = nearLifts.map((v) => v - baseline);

      const window = Math.min(DEBOUNCE_FRAMES, rises.length);
      let sustainedPeak = -Infinity;
      for (let i = 0; i <= rises.length - window; i += 1) {
        sustainedPeak = Math.max(sustainedPeak, Math.min(...rises.slice(i, i + window)));
      }
      return sustainedPeak / meanTrunk;
    },
    reset() {
      leftLifts.length = 0;
      rightLifts.length = 0;
      leftVisibility.length = 0;
      rightVisibility.length = 0;
      trunkSum = 0;
      frames = 0;
    },
  };
}
