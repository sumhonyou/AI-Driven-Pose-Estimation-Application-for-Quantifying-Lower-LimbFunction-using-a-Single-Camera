// Gate direction, threshold boundaries and the heel-visibility abstention.
// Backend parity of the heel-rise MATH is checked separately, cross-language.
import { describe, it, expect } from "vitest";
import {
  createHeelRiseTracker,
  evaluateSquatFaultGates,
  heelLandmarksVisible,
  type SquatFaultGateConfig,
} from "../utils/squat/squatFaultGates";
import { LM, type WorldLandmark } from "../types/pose";
import { FALLBACK_SQUAT_LIVE_CONFIG } from "../utils/squat/squatLiveEstimate";

const CONFIG: SquatFaultGateConfig = FALLBACK_SQUAT_LIVE_CONFIG.faultGates;

const CLEAN = {
  kneeFlexPeakDeg: 100,
  trunkLeanPeakDeg: 10,
  heelRisePeakNorm: 0.0,
};

function pose(overrides: Partial<Record<number, Partial<WorldLandmark>>> = {}): WorldLandmark[] {
  const lms: WorldLandmark[] = Array.from({ length: 33 }, () => ({
    x: 0,
    y: 0,
    z: 0,
    visibility: 1,
  }));
  lms[LM.LEFT_SHOULDER] = { x: 0, y: -0.5, z: 0, visibility: 1 };
  lms[LM.RIGHT_SHOULDER] = { x: 0, y: -0.5, z: 0, visibility: 1 };
  lms[LM.LEFT_HIP] = { x: 0, y: 0, z: 0, visibility: 1 };
  lms[LM.RIGHT_HIP] = { x: 0, y: 0, z: 0, visibility: 1 };
  for (const [i, o] of Object.entries(overrides)) {
    lms[Number(i)] = { ...lms[Number(i)], ...o };
  }
  return lms;
}

describe("evaluateSquatFaultGates", () => {
  it("passes a clean rep", () => {
    expect(evaluateSquatFaultGates(CLEAN, CONFIG)).toEqual([]);
  });

  it("fails depth only BELOW the threshold, matching depth_gate's `<`", () => {
    const at = { ...CLEAN, kneeFlexPeakDeg: CONFIG.minKneeFlexPeakDeg };
    const below = { ...CLEAN, kneeFlexPeakDeg: CONFIG.minKneeFlexPeakDeg - 0.01 };
    expect(evaluateSquatFaultGates(at, CONFIG)).toEqual([]);
    expect(evaluateSquatFaultGates(below, CONFIG)).toEqual(["insufficient_depth"]);
  });

  it("fails lean AT the threshold, matching lean_gate's `>=`", () => {
    const at = { ...CLEAN, trunkLeanPeakDeg: CONFIG.faultTrunkLeanPeakDeg };
    const under = { ...CLEAN, trunkLeanPeakDeg: CONFIG.faultTrunkLeanPeakDeg - 0.01 };
    expect(evaluateSquatFaultGates(at, CONFIG)).toEqual(["excessive_forward_lean"]);
    expect(evaluateSquatFaultGates(under, CONFIG)).toEqual([]);
  });

  it("fails heel rise AT the threshold, matching heel_rise_gate's `>=`", () => {
    const at = { ...CLEAN, heelRisePeakNorm: CONFIG.faultHeelRisePeakNorm };
    expect(evaluateSquatFaultGates(at, CONFIG)).toEqual(["heel_lift"]);
  });

  it("abstains on heel rise when the landmarks were never reliable", () => {
    const unmeasurable = { ...CLEAN, heelRisePeakNorm: null };
    expect(evaluateSquatFaultGates(unmeasurable, CONFIG)).toEqual([]);
  });

  it("still applies depth and lean when heel rise is unmeasurable", () => {
    const shallow = { ...CLEAN, kneeFlexPeakDeg: 50, heelRisePeakNorm: null };
    expect(evaluateSquatFaultGates(shallow, CONFIG)).toEqual(["insufficient_depth"]);
  });

  it("reports every fault a rep trips, not just the first", () => {
    const bad = { kneeFlexPeakDeg: 50, trunkLeanPeakDeg: 60, heelRisePeakNorm: 0.2 };
    expect(evaluateSquatFaultGates(bad, CONFIG)).toEqual([
      "insufficient_depth",
      "excessive_forward_lean",
      "heel_lift",
    ]);
  });

  it("honours a server-side disabled gate", () => {
    const off = { ...CONFIG, depthEnabled: false };
    expect(evaluateSquatFaultGates({ ...CLEAN, kneeFlexPeakDeg: 10 }, off)).toEqual([]);
  });
});

describe("heel visibility", () => {
  it("treats a low-visibility heel as not judgeable", () => {
    expect(heelLandmarksVisible(pose())).toBe(true);
    expect(heelLandmarksVisible(pose({ [LM.LEFT_HEEL]: { visibility: 0.49 } }))).toBe(false);
  });

  it("returns null from the tracker if any frame was occluded", () => {
    const tracker = createHeelRiseTracker();
    tracker.record(pose());
    tracker.record(pose({ [LM.RIGHT_FOOT_INDEX]: { visibility: 0.1 } }));
    expect(tracker.result()).toBeNull();
  });
});

describe("heel-rise tracker", () => {
  it("measures rise relative to the rep's first frame, normalised by trunk length", () => {
    const tracker = createHeelRiseTracker();
    // Trunk length is 0.5 in `pose()`. Heel starts level with the toe, then lifts 0.05
    // (y is DOWN, so a raised heel has the smaller y).
    tracker.record(pose());
    tracker.record(pose({ [LM.LEFT_HEEL]: { y: -0.05 }, [LM.RIGHT_HEEL]: { y: -0.05 } }));
    expect(tracker.result()).toBeCloseTo(0.05 / 0.5, 10);
  });

  it("ignores a heel DROP, reporting zero rise", () => {
    const tracker = createHeelRiseTracker();
    tracker.record(pose());
    tracker.record(pose({ [LM.LEFT_HEEL]: { y: 0.05 }, [LM.RIGHT_HEEL]: { y: 0.05 } }));
    expect(tracker.result()).toBeCloseTo(0, 10);
  });

  it("resets cleanly between reps", () => {
    const tracker = createHeelRiseTracker();
    tracker.record(pose({ [LM.LEFT_HEEL]: { y: -0.5 } }));
    tracker.reset();
    tracker.record(pose());
    expect(tracker.result()).toBeCloseTo(0, 10);
  });
});
