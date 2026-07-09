// Client-side SLS geometry + live hold/combo tracker.
// Mirrors backend app/module_a/sls/geometry.py + fsm.py so the live numbers the user
// sees (timer, ball-in-circle) match the backend's official recompute. The backend's
// POST response is always authoritative; this is a zero-latency helper only.
//
// World-landmark convention: Y increases DOWNWARD (a lifted foot has a SMALLER y).

import { LM, type WorldLandmark } from "../../types/pose";
import {
  SLS_CALIBRATION_SEC,
  SLS_CIRCLE_RADIUS_NORM,
  SLS_DROP_PERSIST_FRAMES,
  SLS_LIFT_HYSTERESIS_NORM,
  SLS_LIFT_LINE_NORM,
  SLS_LIFT_PERSIST_FRAMES,
  SLS_MAX_HOLD_SEC,
} from "../../config/moduleAThresholds";
import { COMBO_POINTS_PER_SEC, COMBO_TIERS } from "../../config/slsUi";

export type SlsLeg = "left" | "right";
export type LivePhase = "calibrating" | "waiting" | "holding" | "stopped";

const HIP: Record<SlsLeg, number> = { left: LM.LEFT_HIP, right: LM.RIGHT_HIP };
const ANKLE: Record<SlsLeg, number> = { left: LM.LEFT_ANKLE, right: LM.RIGHT_ANKLE };

export function otherLeg(leg: SlsLeg): SlsLeg {
  return leg === "right" ? "left" : "right";
}

function dist(a: WorldLandmark, b: WorldLandmark): number {
  return Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2);
}

export function hipWidth(w: WorldLandmark[]): number {
  return dist(w[LM.LEFT_HIP], w[LM.RIGHT_HIP]);
}

export function hipMidX(w: WorldLandmark[]): number {
  return (w[LM.LEFT_HIP].x + w[LM.RIGHT_HIP].x) / 2;
}

export function stanceLegLength(w: WorldLandmark[], stance: SlsLeg): number {
  return dist(w[HIP[stance]], w[ANKLE[stance]]);
}

/** Frontal-plane offset of the hip-midpoint from the stance foot, normalised by hip width. */
export function ballXNorm(w: WorldLandmark[], stance: SlsLeg): number {
  const width = hipWidth(w);
  if (width < 1e-9) return 0;
  return (hipMidX(w) - w[ANKLE[stance]].x) / width;
}

export function isInsideCircle(ballX: number): boolean {
  return Math.abs(ballX) <= SLS_CIRCLE_RADIUS_NORM;
}

export interface SlsLiveUpdate {
  phase: LivePhase;
  holdSeconds: number;
  ballXNorm: number; // signed lateral offset (for drawing the ball)
  ballInside: boolean;
  aboveLine: boolean;
  /** 0 = foot at the planted baseline, 1 = foot exactly at the lift-line, can exceed 1. */
  liftProgress: number;
  points: number; // gamified combo points (display-only, never persisted)
  multiplier: number; // current combo multiplier
  cappedAtMax: boolean;
}

/** Multiplier for a given continuous seconds-inside, from the configured tiers. */
function multiplierForDwell(secInside: number): number {
  let m = 1;
  for (const tier of COMBO_TIERS) if (secInside >= tier.atSecInside) m = tier.multiplier;
  return m;
}

/**
 * Stateful per-leg live tracker. Feed it every frame's world landmarks; it mirrors
 * the backend lift-line FSM for the timer and runs the combo mechanic for the score.
 */
export function createSlsLiveTracker(leg: SlsLeg) {
  const stance = otherLeg(leg);

  let phase: LivePhase = "calibrating";
  let t0: number | null = null;
  let baselineAnkleYSum = 0;
  let baselineCount = 0;
  let baselineLegLenSum = 0;
  let baselineAnkleY: number | null = null;
  let lineY: number | null = null;
  let dropMargin = 0;

  let aboveStreak = 0;
  let belowStreak = 0;
  let holdStartSec: number | null = null;
  let holdSeconds = 0;
  let cappedAtMax = false;

  // Combo (display-only)
  let insideSinceSec: number | null = null;
  let points = 0;
  let lastFrameSec: number | null = null;

  function reset() {
    phase = "calibrating";
    t0 = null;
    baselineAnkleYSum = baselineCount = baselineLegLenSum = 0;
    baselineAnkleY = null;
    lineY = null;
    dropMargin = 0;
    aboveStreak = belowStreak = 0;
    holdStartSec = null;
    holdSeconds = 0;
    cappedAtMax = false;
    insideSinceSec = null;
    points = 0;
    lastFrameSec = null;
  }

  function update(w: WorldLandmark[], nowMs: number): SlsLiveUpdate {
    const idle: SlsLiveUpdate = {
      phase,
      holdSeconds,
      ballXNorm: 0,
      ballInside: false,
      aboveLine: false,
      liftProgress: 0,
      points,
      multiplier: 1,
      cappedAtMax,
    };
    if (!w || w.length < 33) return idle;

    if (t0 === null) t0 = nowMs;
    const t = (nowMs - t0) / 1000;
    const dt = lastFrameSec === null ? 0 : Math.max(0, t - lastFrameSec);
    lastFrameSec = t;

    const ankleY = w[ANKLE[leg]].y;

    // Calibration: average the planted baseline + stance-leg length, then place the line.
    if (t <= SLS_CALIBRATION_SEC) {
      baselineAnkleYSum += ankleY;
      baselineLegLenSum += stanceLegLength(w, stance);
      baselineCount += 1;
      return { ...idle, phase: "calibrating" };
    }
    if (lineY === null) {
      if (baselineCount === 0) return { ...idle, phase: "waiting" };
      baselineAnkleY = baselineAnkleYSum / baselineCount;
      const legLen = baselineLegLenSum / baselineCount;
      lineY = baselineAnkleY - SLS_LIFT_LINE_NORM * legLen;
      dropMargin = SLS_LIFT_HYSTERESIS_NORM * legLen;
      phase = "waiting";
    }

    const aboveLift = ankleY < lineY;
    const aboveHold = ankleY < lineY + dropMargin;
    const bx = ballXNorm(w, stance);
    const inside = isInsideCircle(bx);
    const liftSpan = (baselineAnkleY as number) - lineY;
    const liftProgress = liftSpan > 1e-9 ? ((baselineAnkleY as number) - ankleY) / liftSpan : 0;

    if (phase === "waiting") {
      aboveStreak = aboveLift ? aboveStreak + 1 : 0;
      if (aboveStreak >= SLS_LIFT_PERSIST_FRAMES) {
        phase = "holding";
        holdStartSec = t;
        belowStreak = 0;
      }
    } else if (phase === "holding") {
      if (aboveHold) {
        belowStreak = 0;
        holdSeconds = t - (holdStartSec ?? t);
        if (holdSeconds >= SLS_MAX_HOLD_SEC) {
          holdSeconds = SLS_MAX_HOLD_SEC;
          cappedAtMax = true;
          phase = "stopped";
        }
      } else {
        belowStreak += 1;
        if (belowStreak >= SLS_DROP_PERSIST_FRAMES) phase = "stopped";
      }

      // Combo: accrue points scaled by the dwell multiplier while inside; reset on exit.
      if (phase === "holding") {
        if (inside) {
          if (insideSinceSec === null) insideSinceSec = t;
          const mult = multiplierForDwell(t - insideSinceSec);
          points += COMBO_POINTS_PER_SEC * mult * dt;
        } else {
          insideSinceSec = null;
        }
      }
    }

    const multiplier =
      phase === "holding" && inside && insideSinceSec !== null
        ? multiplierForDwell(t - insideSinceSec)
        : 1;

    return {
      phase,
      holdSeconds,
      ballXNorm: bx,
      ballInside: inside,
      aboveLine: aboveLift,
      liftProgress,
      points: Math.floor(points),
      multiplier,
      cappedAtMax,
    };
  }

  return { update, reset };
}
