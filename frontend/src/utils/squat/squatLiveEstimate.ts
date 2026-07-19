// Client-side live squat rep count + rough band ESTIMATE for the live UX only.
// Mirrors the shape/depth of the backend's segmentation (HysteresisRepFSM) and
// ROM rule (score_squat_rep) closely enough for instant feedback, but is never
// authoritative — the backend's POST /api/module-b/analyze response (run over
// the whole buffered set) is the only persisted, official score.
//
// Thresholds are fetched once from GET /api/module-b/squat/config so this stays
// in sync with the backend; the constants below are only the pre-fetch fallback
// (X7 — do not hand-sync these long-term, per Phase 3E Stage 5's lesson).
import { LM, type WorldLandmark } from "../../types/pose";
import { moduleBService } from "../../services/moduleBService";

export type SquatLiveConfig = {
  enterDescendingDeg: number;
  exitStandingDeg: number;
  refractoryS: number;
  minRepDurationS: number;
  romShallowStartDeg: number;
  romParallelStartDeg: number;
  romDeepStartDeg: number;
  romDeepFullScoreDeg: number;
};

export const FALLBACK_SQUAT_LIVE_CONFIG: SquatLiveConfig = {
  enterDescendingDeg: 30.0,
  exitStandingDeg: 20.0,
  refractoryS: 0.5,
  minRepDurationS: 0.5,
  romShallowStartDeg: 60.0,
  romParallelStartDeg: 90.0,
  romDeepStartDeg: 110.0,
  romDeepFullScoreDeg: 130.0,
};

/** Binary band cut for the live ROM estimate (Stage 5.11). The authoritative
 * Good/Needs-Improvement verdict comes from the backend's committed binary ML decision
 * after the set; this rough client-side hint only reflects whether the rep reached the
 * "Good" depth-completion boundary (the old Fair/Good cut on the 0-10 ROM score), and
 * never runs the ML model. "Poor" is displayed as "Needs Improvement" via i18n. */
const BAND_GOOD_MIN_SCORE = 7.0;

export type SquatPhase = "standing" | "descending" | "ascending";
export type SquatBandEstimate = "Poor" | "Good" | null;
/** Named ROM zones, using the exact same boundary names as squat/config.py's
 * `rules.rom` thresholds — never an invented cutoff (X2). */
export type SquatDepthZone = "minimal" | "shallow" | "parallel" | "deep";

export interface SquatLiveUpdate {
  repCount: number;
  phase: SquatPhase;
  /** Current bilateral mean knee flexion (0deg straight, increasing as the knee bends). */
  currentFlexionDeg: number;
  /** Current trunk lean off vertical (0deg upright) — mirrors core/geometry.py's trunk_lean_deg. */
  currentTrunkLeanDeg: number;
  /** Peak flexion reached so far in the rep currently in progress; null while standing. */
  currentRepPeakFlexionDeg: number | null;
  lastRepPeakDeg: number | null;
  lastRepPeakTrunkLeanDeg: number | null;
  lastRepBandEstimate: SquatBandEstimate;
  /** True only on the exact frame a rep was just confirmed — used to trigger sounds/toasts. */
  repJustCompleted: boolean;
}

/** Which named ROM zone a live flexion angle currently falls in. */
export function depthZoneFor(flexionDeg: number, config: SquatLiveConfig): SquatDepthZone {
  if (flexionDeg < config.romShallowStartDeg) return "minimal";
  if (flexionDeg < config.romParallelStartDeg) return "shallow";
  if (flexionDeg < config.romDeepStartDeg) return "parallel";
  return "deep";
}

/** Position (0-100) of a flexion angle along the full ROM gauge, clamped to its range. */
export function depthGaugePct(flexionDeg: number, config: SquatLiveConfig): number {
  return Math.max(0, Math.min(100, (flexionDeg / config.romDeepFullScoreDeg) * 100));
}

/** Fetches live thresholds from the backend; falls back to the frozen local
 * defaults (kept identical to squat/config.py's Stage 4.0 values) on failure. */
export async function fetchSquatLiveConfig(): Promise<SquatLiveConfig> {
  try {
    const config = await moduleBService.config("squat");
    const exercise = config.exercise as Record<string, unknown>;
    const segmentation = (exercise?.segmentation ?? {}) as Record<string, number>;
    const rom = ((exercise?.rules as Record<string, unknown>)?.rom ?? {}) as Record<string, number>;
    return {
      enterDescendingDeg:
        segmentation.enter_descending_deg ?? FALLBACK_SQUAT_LIVE_CONFIG.enterDescendingDeg,
      exitStandingDeg: segmentation.exit_standing_deg ?? FALLBACK_SQUAT_LIVE_CONFIG.exitStandingDeg,
      refractoryS: segmentation.refractory_s ?? FALLBACK_SQUAT_LIVE_CONFIG.refractoryS,
      minRepDurationS:
        segmentation.min_rep_duration_s ?? FALLBACK_SQUAT_LIVE_CONFIG.minRepDurationS,
      romShallowStartDeg: rom.shallow_start_deg ?? FALLBACK_SQUAT_LIVE_CONFIG.romShallowStartDeg,
      romParallelStartDeg: rom.parallel_start_deg ?? FALLBACK_SQUAT_LIVE_CONFIG.romParallelStartDeg,
      romDeepStartDeg: rom.deep_start_deg ?? FALLBACK_SQUAT_LIVE_CONFIG.romDeepStartDeg,
      romDeepFullScoreDeg:
        rom.deep_full_score_deg ?? FALLBACK_SQUAT_LIVE_CONFIG.romDeepFullScoreDeg,
    };
  } catch (err) {
    console.error("[squatLiveEstimate] Config fetch failed, using fallback thresholds", err);
    return FALLBACK_SQUAT_LIVE_CONFIG;
  }
}

function angleDeg(a: WorldLandmark, b: WorldLandmark, c: WorldLandmark): number {
  const v1 = { x: a.x - b.x, y: a.y - b.y, z: a.z - b.z };
  const v2 = { x: c.x - b.x, y: c.y - b.y, z: c.z - b.z };
  const dot = v1.x * v2.x + v1.y * v2.y + v1.z * v2.z;
  const cross = {
    x: v1.y * v2.z - v1.z * v2.y,
    y: v1.z * v2.x - v1.x * v2.z,
    z: v1.x * v2.y - v1.y * v2.x,
  };
  const crossMag = Math.sqrt(cross.x ** 2 + cross.y ** 2 + cross.z ** 2);
  return (Math.atan2(crossMag, dot) * 180) / Math.PI;
}

/** Bilateral mean knee flexion — mirrors backend squat/segmentation.py's mean_knee_flexion_deg. */
function meanKneeFlexionDeg(w: WorldLandmark[]): number {
  const flexL = 180 - angleDeg(w[LM.LEFT_HIP], w[LM.LEFT_KNEE], w[LM.LEFT_ANKLE]);
  const flexR = 180 - angleDeg(w[LM.RIGHT_HIP], w[LM.RIGHT_KNEE], w[LM.RIGHT_ANKLE]);
  return (flexL + flexR) / 2;
}

function midpoint(a: WorldLandmark, b: WorldLandmark) {
  return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2, z: (a.z + b.z) / 2 };
}

/** Trunk lean off vertical (0deg upright) — mirrors backend core/geometry.py's
 * trunk_lean_deg: angle between the shoulder->hip segment and world "up". */
function trunkLeanDeg(w: WorldLandmark[]): number {
  const shoulderMid = midpoint(w[LM.LEFT_SHOULDER], w[LM.RIGHT_SHOULDER]);
  const hipMid = midpoint(w[LM.LEFT_HIP], w[LM.RIGHT_HIP]);
  const v = {
    x: shoulderMid.x - hipMid.x,
    y: shoulderMid.y - hipMid.y,
    z: shoulderMid.z - hipMid.z,
  };
  const norm = Math.sqrt(v.x ** 2 + v.y ** 2 + v.z ** 2);
  if (norm < 1e-9) return 0;
  // World "up" is (0, -1, 0) — same convention as backend's UP_VECTOR.
  const cos = Math.max(-1, Math.min(1, -v.y / norm));
  return (Math.acos(cos) * 180) / Math.PI;
}

function interpolate(
  value: number,
  start: number,
  end: number,
  startScore: number,
  endScore: number,
): number {
  const proportion = Math.min(Math.max((value - start) / (end - start), 0), 1);
  return startScore + proportion * (endScore - startScore);
}

/** Rough ROM-only score estimate (0-10) from peak flexion — mirrors squat/rules.py's
 * rom_subscore's band shape, without the ankle-dorsiflexion floor override. */
function romScoreEstimate(peakFlexionDeg: number, config: SquatLiveConfig): number {
  const {
    romShallowStartDeg: shallow,
    romParallelStartDeg: parallel,
    romDeepStartDeg: deep,
  } = config;
  if (peakFlexionDeg < shallow) return interpolate(peakFlexionDeg, 0, shallow, 0, 2);
  if (peakFlexionDeg < parallel) return interpolate(peakFlexionDeg, shallow, parallel, 2, 5);
  if (peakFlexionDeg < deep) return interpolate(peakFlexionDeg, parallel, deep, 5, 8);
  return interpolate(peakFlexionDeg, deep, config.romDeepFullScoreDeg, 8, 10);
}

function scoreToBandEstimate(score: number): SquatBandEstimate {
  return score >= BAND_GOOD_MIN_SCORE ? "Good" : "Poor";
}

/** Stateful per-set live tracker: hysteresis rep counter + per-rep ROM band estimate. */
export function createSquatLiveEstimator(config: SquatLiveConfig = FALLBACK_SQUAT_LIVE_CONFIG) {
  let repCount = 0;
  let phase: SquatPhase = "standing";
  let active = false;
  let candidateStartS: number | null = null;
  let peakFlexionDeg = 0;
  let peakTrunkLeanDeg = 0;
  let previousFlexionDeg = 0;
  let refractoryUntilS = 0;
  let lastRepPeakDeg: number | null = null;
  let lastRepPeakTrunkLeanDeg: number | null = null;
  let lastRepBandEstimate: SquatBandEstimate = null;

  return {
    update(worldLandmarks: WorldLandmark[], nowMs: number): SquatLiveUpdate {
      const timestampS = nowMs / 1000;
      let repJustCompleted = false;

      if (!worldLandmarks || worldLandmarks.length <= 28) {
        return {
          repCount,
          phase,
          currentFlexionDeg: 0,
          currentTrunkLeanDeg: 0,
          currentRepPeakFlexionDeg: active ? peakFlexionDeg : null,
          lastRepPeakDeg,
          lastRepPeakTrunkLeanDeg,
          lastRepBandEstimate,
          repJustCompleted,
        };
      }
      const flexion = meanKneeFlexionDeg(worldLandmarks);
      const trunkLean = trunkLeanDeg(worldLandmarks);

      if (!active) {
        if (timestampS >= refractoryUntilS && flexion >= config.enterDescendingDeg) {
          active = true;
          candidateStartS = timestampS;
          peakFlexionDeg = flexion;
          peakTrunkLeanDeg = trunkLean;
          phase = "descending";
        }
      } else {
        if (flexion > peakFlexionDeg) peakFlexionDeg = flexion;
        if (trunkLean > peakTrunkLeanDeg) peakTrunkLeanDeg = trunkLean;
        phase = flexion >= previousFlexionDeg ? "descending" : "ascending";

        if (flexion <= config.exitStandingDeg) {
          const durationS = timestampS - (candidateStartS ?? timestampS);
          if (durationS + 1e-9 >= config.minRepDurationS) {
            repCount += 1;
            lastRepPeakDeg = peakFlexionDeg;
            lastRepPeakTrunkLeanDeg = peakTrunkLeanDeg;
            lastRepBandEstimate = scoreToBandEstimate(romScoreEstimate(peakFlexionDeg, config));
            repJustCompleted = true;
          }
          active = false;
          candidateStartS = null;
          refractoryUntilS = timestampS + config.refractoryS;
          phase = "standing";
        }
      }
      previousFlexionDeg = flexion;

      return {
        repCount,
        phase,
        currentFlexionDeg: flexion,
        currentTrunkLeanDeg: trunkLean,
        currentRepPeakFlexionDeg: active ? peakFlexionDeg : null,
        lastRepPeakDeg,
        lastRepPeakTrunkLeanDeg,
        lastRepBandEstimate,
        repJustCompleted,
      };
    },
    reset() {
      repCount = 0;
      phase = "standing";
      active = false;
      candidateStartS = null;
      peakFlexionDeg = 0;
      peakTrunkLeanDeg = 0;
      previousFlexionDeg = 0;
      refractoryUntilS = 0;
      lastRepPeakDeg = null;
      lastRepPeakTrunkLeanDeg = null;
      lastRepBandEstimate = null;
    },
  };
}
