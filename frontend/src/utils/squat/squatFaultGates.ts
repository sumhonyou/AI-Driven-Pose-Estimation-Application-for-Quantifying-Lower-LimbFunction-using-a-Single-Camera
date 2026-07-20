// Client-side port of backend app/module_b/squat/fault_gates.py, so a rep with a named
// fault can be rejected the moment it happens instead of only at the end of the set.
//
// The backend stays authoritative: it re-runs these gates over every rep and its result
// is what the report shows. This port exists purely so the user gets an immediate reason
// and the faulty rep does not advance their target.
//
// Thresholds are NEVER hardcoded here -- they arrive from GET /api/module-b/squat/config
// (which serves the whole SQUAT_CONFIG, fault_gates block included). See X7: the Phase 3E
// lesson was that hand-synced constants drift silently.
import { LM, type WorldLandmark } from "../../types/pose";

/** Mirrors backend app/module_a/core/config.py's MIN_VISIBILITY. */
const MIN_VISIBILITY = 0.5;

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

/** Bilateral (toe_y - heel_y). y is DOWN in MediaPipe world space, so a positive value
 * means the heel sits higher than the grounded toe. Mirrors `_toe_heel_lift`. */
export function bilateralToeHeelLift(w: WorldLandmark[]): number {
  const left = w[LM.LEFT_FOOT_INDEX].y - w[LM.LEFT_HEEL].y;
  const right = w[LM.RIGHT_FOOT_INDEX].y - w[LM.RIGHT_HEEL].y;
  return (left + right) / 2;
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

/** Whether all four heel/toe landmarks are confident enough to judge a heel lift.
 *
 * Heels and toes are the lowest-visibility landmarks in a side view, and a false
 * heel-lift rejection is the most frustrating possible failure -- it discards a rep the
 * user performed correctly. When they are not visible the live gate abstains and leaves
 * the call to the backend, which sees the whole smoothed stream. */
export function heelLandmarksVisible(w: WorldLandmark[]): boolean {
  return [LM.LEFT_HEEL, LM.RIGHT_HEEL, LM.LEFT_FOOT_INDEX, LM.RIGHT_FOOT_INDEX].every(
    (index) => (w[index]?.visibility ?? 0) >= MIN_VISIBILITY,
  );
}

/** Accumulates one rep's heel-rise measurement frame by frame.
 *
 * Mirrors `_heel_rise_peak_norm`: peak bilateral toe-heel lift relative to the rep's
 * FIRST frame, divided by the mean trunk length over the rep. Built incrementally
 * because the live path sees one frame at a time and never holds the rep's frames. */
export function createHeelRiseTracker() {
  let baseline: number | null = null;
  let peakRise = 0;
  let trunkSum = 0;
  let frames = 0;
  let everOccluded = false;

  return {
    record(w: WorldLandmark[]) {
      if (!heelLandmarksVisible(w)) {
        everOccluded = true;
        return;
      }
      const lift = bilateralToeHeelLift(w);
      if (baseline === null) baseline = lift;
      peakRise = Math.max(peakRise, lift - baseline);
      trunkSum += trunkLength(w);
      frames += 1;
    },
    /** null when the rep was never measurable -- see `heelLandmarksVisible`. */
    result(): number | null {
      if (everOccluded || baseline === null || frames === 0) return null;
      const meanTrunk = trunkSum / frames;
      if (meanTrunk < 1e-9) return null;
      return peakRise / meanTrunk;
    },
    reset() {
      baseline = null;
      peakRise = 0;
      trunkSum = 0;
      frames = 0;
      everOccluded = false;
    },
  };
}
