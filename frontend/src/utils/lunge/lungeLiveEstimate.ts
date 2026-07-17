// Client-side live lunge rep count + rough front-knee band ESTIMATE for the live
// UX only. Mirrors squatLiveEstimate.ts's shape closely, adapted for a lunge's
// asymmetric front/back-leg structure (backend lunge/features.py, lunge/rules.py):
// the rep-boundary FSM still drives off the BILATERAL MEAN knee flexion (matches
// backend lunge/segmentation.py's "no lunge-specific delta" decision — both knees
// cycle together even though their peak magnitude differs), but depth/band
// feedback and the knee-passes-toe warning are read off the FRONT knee only,
// since that is the one the ROM band and the fault actually apply to.
//
// Never authoritative — the backend's POST /api/module-b/analyze response (run
// over the whole buffered set) is the only persisted, official score.
//
// Thresholds are fetched once from GET /api/module-b/lunge/config so this stays
// in sync with the backend; the constants below are only the pre-fetch fallback
// (X7 — do not hand-sync these long-term, per Phase 3E Stage 5's lesson).
import { LM, type WorldLandmark } from "../../types/pose";
import { moduleBService } from "../../services/moduleBService";

export type LungeLiveConfig = {
  enterDescendingDeg: number;
  exitStandingDeg: number;
  refractoryS: number;
  minRepDurationS: number;
  romShallowStartDeg: number;
  romParallelStartDeg: number;
  romDeepStartDeg: number;
  romDeepFullScoreDeg: number;
};

// Identical starting values to backend lunge/config.py's Stage 4.3/4.4 defaults
// (themselves an interim, tagged-heuristic reuse of squat's own numbers — see
// task.md Stage 4.4 (Lunge)).
export const FALLBACK_LUNGE_LIVE_CONFIG: LungeLiveConfig = {
  enterDescendingDeg: 30.0,
  exitStandingDeg: 20.0,
  refractoryS: 0.5,
  minRepDurationS: 0.5,
  romShallowStartDeg: 60.0,
  romParallelStartDeg: 90.0,
  romDeepStartDeg: 110.0,
  romDeepFullScoreDeg: 130.0,
};

const BAND_POOR_MAX = 4.0;
const BAND_FAIR_MAX = 7.0;

export type LungePhase = "standing" | "descending" | "ascending";
export type LungeBandEstimate = "Poor" | "Fair" | "Good" | null;
export type LungeDepthZone = "minimal" | "shallow" | "parallel" | "deep";
export type LungeLeg = "left" | "right";

export interface LungeLiveUpdate {
  repCount: number;
  phase: LungePhase;
  /** Which leg is currently planted forward, inferred from stance geometry. */
  frontLeg: LungeLeg;
  /** Current front-knee flexion (0deg straight, increasing as the knee bends). */
  currentFrontKneeFlexionDeg: number;
  currentTrunkLeanDeg: number;
  /** Peak front-knee flexion reached so far in the rep in progress; null while standing. */
  currentRepPeakFrontKneeFlexionDeg: number | null;
  /** Live fault warning: true the instant the front knee is forward of the front toe. */
  kneePassesToe: boolean;
  lastRepPeakFrontKneeDeg: number | null;
  lastRepBandEstimate: LungeBandEstimate;
  /** Whether the front knee passed the toe at any point during the last completed rep. */
  lastRepKneePassedToe: boolean | null;
  repJustCompleted: boolean;
}

/** Which named ROM zone a live front-knee flexion angle currently falls in. */
export function depthZoneFor(flexionDeg: number, config: LungeLiveConfig): LungeDepthZone {
  if (flexionDeg < config.romShallowStartDeg) return "minimal";
  if (flexionDeg < config.romParallelStartDeg) return "shallow";
  if (flexionDeg < config.romDeepStartDeg) return "parallel";
  return "deep";
}

/** Position (0-100) of a flexion angle along the full ROM gauge, clamped to its range. */
export function depthGaugePct(flexionDeg: number, config: LungeLiveConfig): number {
  return Math.max(0, Math.min(100, (flexionDeg / config.romDeepFullScoreDeg) * 100));
}

/** Fetches live thresholds from the backend; falls back to the frozen local
 * defaults (kept identical to lunge/config.py's current values) on failure. */
export async function fetchLungeLiveConfig(): Promise<LungeLiveConfig> {
  try {
    const config = await moduleBService.config("lunge");
    const exercise = config.exercise as Record<string, unknown>;
    const segmentation = (exercise?.segmentation ?? {}) as Record<string, number>;
    const rules = (exercise?.rules ?? {}) as Record<string, unknown>;
    const rom = (rules?.rom ?? {}) as Record<string, number>;
    return {
      enterDescendingDeg:
        segmentation.enter_descending_deg ?? FALLBACK_LUNGE_LIVE_CONFIG.enterDescendingDeg,
      exitStandingDeg: segmentation.exit_standing_deg ?? FALLBACK_LUNGE_LIVE_CONFIG.exitStandingDeg,
      refractoryS: segmentation.refractory_s ?? FALLBACK_LUNGE_LIVE_CONFIG.refractoryS,
      minRepDurationS:
        segmentation.min_rep_duration_s ?? FALLBACK_LUNGE_LIVE_CONFIG.minRepDurationS,
      romShallowStartDeg: rom.shallow_start_deg ?? FALLBACK_LUNGE_LIVE_CONFIG.romShallowStartDeg,
      romParallelStartDeg: rom.parallel_start_deg ?? FALLBACK_LUNGE_LIVE_CONFIG.romParallelStartDeg,
      romDeepStartDeg: rom.deep_start_deg ?? FALLBACK_LUNGE_LIVE_CONFIG.romDeepStartDeg,
      romDeepFullScoreDeg:
        rom.deep_full_score_deg ?? FALLBACK_LUNGE_LIVE_CONFIG.romDeepFullScoreDeg,
    };
  } catch (err) {
    console.error("[lungeLiveEstimate] Config fetch failed, using fallback thresholds", err);
    return FALLBACK_LUNGE_LIVE_CONFIG;
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

function kneeFlexionDeg(hip: WorldLandmark, knee: WorldLandmark, ankle: WorldLandmark): number {
  return 180 - angleDeg(hip, knee, ankle);
}

function midpoint(a: WorldLandmark, b: WorldLandmark) {
  return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2, z: (a.z + b.z) / 2 };
}

/** Trunk lean off vertical (0deg upright) — mirrors backend core/geometry.py's trunk_lean_deg. */
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
  const cos = Math.max(-1, Math.min(1, -v.y / norm));
  return (Math.acos(cos) * 180) / Math.PI;
}

/** +1/-1 for the world-x direction the toes point (forward) — mirrors backend
 * lunge/features.py's `_anterior_sign`. */
function anteriorSign(w: WorldLandmark[]): number {
  const toeAhead =
    w[LM.LEFT_FOOT_INDEX].x - w[LM.LEFT_ANKLE].x + (w[LM.RIGHT_FOOT_INDEX].x - w[LM.RIGHT_ANKLE].x);
  return toeAhead >= 0 ? 1 : -1;
}

/** Which leg is planted more forward along the anterior direction — mirrors
 * backend lunge/features.py's `_resolve_front_leg`. */
function resolveFrontLeg(w: WorldLandmark[], sign: number): LungeLeg {
  const leftForward = w[LM.LEFT_ANKLE].x * sign;
  const rightForward = w[LM.RIGHT_ANKLE].x * sign;
  return leftForward >= rightForward ? "left" : "right";
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

/** Rough ROM-only score estimate (0-10) from front-knee peak flexion — mirrors
 * lunge/rules.py's rom_subscore's band shape, without the ankle-DF floor override. */
function romScoreEstimate(peakFlexionDeg: number, config: LungeLiveConfig): number {
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

function scoreToBandEstimate(score: number): LungeBandEstimate {
  if (score < BAND_POOR_MAX) return "Poor";
  if (score < BAND_FAIR_MAX) return "Fair";
  return "Good";
}

/** Stateful per-set live tracker: hysteresis rep counter (bilateral mean) + a
 * front-leg-aware ROM band estimate and knee-passes-toe warning. */
export function createLungeLiveEstimator(config: LungeLiveConfig = FALLBACK_LUNGE_LIVE_CONFIG) {
  let repCount = 0;
  let phase: LungePhase = "standing";
  let active = false;
  let frontLeg: LungeLeg = "left";
  let candidateStartS: number | null = null;
  let peakFrontKneeDeg = 0;
  let peakTrunkLeanDeg = 0;
  let kneePassedToeDuringRep = false;
  let previousMeanFlexionDeg = 0;
  let refractoryUntilS = 0;
  let lastRepPeakFrontKneeDeg: number | null = null;
  let lastRepBandEstimate: LungeBandEstimate = null;
  let lastRepKneePassedToe: boolean | null = null;

  return {
    update(worldLandmarks: WorldLandmark[], nowMs: number): LungeLiveUpdate {
      const timestampS = nowMs / 1000;
      let repJustCompleted = false;

      if (!worldLandmarks || worldLandmarks.length <= 32) {
        return {
          repCount,
          phase,
          frontLeg,
          currentFrontKneeFlexionDeg: 0,
          currentTrunkLeanDeg: 0,
          currentRepPeakFrontKneeFlexionDeg: active ? peakFrontKneeDeg : null,
          kneePassesToe: false,
          lastRepPeakFrontKneeDeg,
          lastRepBandEstimate,
          lastRepKneePassedToe,
          repJustCompleted,
        };
      }

      const leftKneeFlex = kneeFlexionDeg(
        worldLandmarks[LM.LEFT_HIP],
        worldLandmarks[LM.LEFT_KNEE],
        worldLandmarks[LM.LEFT_ANKLE],
      );
      const rightKneeFlex = kneeFlexionDeg(
        worldLandmarks[LM.RIGHT_HIP],
        worldLandmarks[LM.RIGHT_KNEE],
        worldLandmarks[LM.RIGHT_ANKLE],
      );
      const meanFlexion = (leftKneeFlex + rightKneeFlex) / 2;
      const trunkLean = trunkLeanDeg(worldLandmarks);

      // Front leg is a stance property, not a per-frame one (Stage 4.3's research
      // finding) — only re-resolve it while standing, so it can't flicker mid-rep.
      if (!active) {
        frontLeg = resolveFrontLeg(worldLandmarks, anteriorSign(worldLandmarks));
      }
      const frontKneeFlex = frontLeg === "left" ? leftKneeFlex : rightKneeFlex;
      const frontKneeIdx = frontLeg === "left" ? LM.LEFT_KNEE : LM.RIGHT_KNEE;
      const frontToeIdx = frontLeg === "left" ? LM.LEFT_FOOT_INDEX : LM.RIGHT_FOOT_INDEX;
      const sign = anteriorSign(worldLandmarks);
      const kneePassesToe =
        (worldLandmarks[frontKneeIdx].x - worldLandmarks[frontToeIdx].x) * sign > 0;

      if (!active) {
        if (timestampS >= refractoryUntilS && meanFlexion >= config.enterDescendingDeg) {
          active = true;
          candidateStartS = timestampS;
          peakFrontKneeDeg = frontKneeFlex;
          peakTrunkLeanDeg = trunkLean;
          kneePassedToeDuringRep = kneePassesToe;
          phase = "descending";
        }
      } else {
        if (frontKneeFlex > peakFrontKneeDeg) peakFrontKneeDeg = frontKneeFlex;
        if (trunkLean > peakTrunkLeanDeg) peakTrunkLeanDeg = trunkLean;
        if (kneePassesToe) kneePassedToeDuringRep = true;
        phase = meanFlexion >= previousMeanFlexionDeg ? "descending" : "ascending";

        if (meanFlexion <= config.exitStandingDeg) {
          const durationS = timestampS - (candidateStartS ?? timestampS);
          if (durationS + 1e-9 >= config.minRepDurationS) {
            repCount += 1;
            lastRepPeakFrontKneeDeg = peakFrontKneeDeg;
            lastRepBandEstimate = scoreToBandEstimate(romScoreEstimate(peakFrontKneeDeg, config));
            lastRepKneePassedToe = kneePassedToeDuringRep;
            repJustCompleted = true;
          }
          active = false;
          candidateStartS = null;
          refractoryUntilS = timestampS + config.refractoryS;
          phase = "standing";
        }
      }
      previousMeanFlexionDeg = meanFlexion;

      return {
        repCount,
        phase,
        frontLeg,
        currentFrontKneeFlexionDeg: frontKneeFlex,
        currentTrunkLeanDeg: trunkLean,
        currentRepPeakFrontKneeFlexionDeg: active ? peakFrontKneeDeg : null,
        kneePassesToe,
        lastRepPeakFrontKneeDeg,
        lastRepBandEstimate,
        lastRepKneePassedToe,
        repJustCompleted,
      };
    },
    reset() {
      repCount = 0;
      phase = "standing";
      active = false;
      frontLeg = "left";
      candidateStartS = null;
      peakFrontKneeDeg = 0;
      peakTrunkLeanDeg = 0;
      kneePassedToeDuringRep = false;
      previousMeanFlexionDeg = 0;
      refractoryUntilS = 0;
      lastRepPeakFrontKneeDeg = null;
      lastRepBandEstimate = null;
      lastRepKneePassedToe = null;
    },
  };
}
