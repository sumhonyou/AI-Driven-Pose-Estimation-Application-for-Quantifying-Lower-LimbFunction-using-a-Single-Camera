// Gate direction, threshold boundaries and the heel-rise tracker's near-leg
// selection / settle-window / debounce construction (Stage R1/R4).
// Backend parity of the heel-rise MATH is checked separately, cross-language.
import { describe, it, expect } from "vitest";
import {
  createHeelRiseTracker,
  evaluateSquatFaultGates,
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

// UAT remediation (Stage R1/R4): the tracker now selects the camera-side (near) leg
// per rep by visibility, baselines against a settle-window median, and requires a
// rise to be sustained across a debounce window -- regression coverage for each part
// mirrors backend tests/test_module_b_squat_fault_gates.py::HeelRiseGateTests.
describe("heel-rise tracker", () => {
  it("measures a rise sustained across the debounce window, baselined from the settle window", () => {
    const tracker = createHeelRiseTracker();
    // Trunk length is 0.5 in `pose()`. 3 flat settle frames, then 3 frames with the
    // heel lifted 0.05 (y is DOWN, so a raised heel has the smaller y) -- long enough
    // to survive the debounce window.
    tracker.record(pose());
    tracker.record(pose());
    tracker.record(pose());
    tracker.record(pose({ [LM.LEFT_HEEL]: { y: -0.05 } }));
    tracker.record(pose({ [LM.LEFT_HEEL]: { y: -0.05 } }));
    tracker.record(pose({ [LM.LEFT_HEEL]: { y: -0.05 } }));
    expect(tracker.result()).toBeCloseTo(0.05 / 0.5, 10);
  });

  it("does not report a single-frame spike that never survives the debounce window", () => {
    const tracker = createHeelRiseTracker();
    tracker.record(pose());
    tracker.record(pose());
    tracker.record(pose());
    tracker.record(pose({ [LM.LEFT_HEEL]: { y: -0.5 } })); // one noisy frame
    tracker.record(pose());
    tracker.record(pose());
    expect(tracker.result()).toBeCloseTo(0, 10);
  });

  it("reads the near (more visible) leg, ignoring a noisy low-visibility far leg", () => {
    const tracker = createHeelRiseTracker();
    for (let i = 0; i < 6; i += 1) {
      tracker.record(
        pose({
          [LM.LEFT_HEEL]: { visibility: 1 },
          [LM.LEFT_FOOT_INDEX]: { visibility: 1 },
          // Right leg spikes wildly but is poorly tracked -- must not leak in.
          [LM.RIGHT_HEEL]: { y: -0.5, visibility: 0.3 },
          [LM.RIGHT_FOOT_INDEX]: { visibility: 0.3 },
        }),
      );
    }
    expect(tracker.result()).toBeCloseTo(0, 10);
  });

  it("refuses to report a result when even the near leg is not reliably visible", () => {
    const tracker = createHeelRiseTracker();
    for (let i = 0; i < 6; i += 1) {
      tracker.record(
        pose({
          [LM.LEFT_HEEL]: { y: -0.5, visibility: 0.3 },
          [LM.LEFT_FOOT_INDEX]: { visibility: 0.3 },
          [LM.RIGHT_HEEL]: { y: -0.5, visibility: 0.3 },
          [LM.RIGHT_FOOT_INDEX]: { visibility: 0.3 },
        }),
      );
    }
    expect(tracker.result()).toBeNull();
  });

  it("ignores a heel DROP, reporting zero rise", () => {
    const tracker = createHeelRiseTracker();
    tracker.record(pose());
    tracker.record(pose());
    tracker.record(pose());
    tracker.record(pose({ [LM.LEFT_HEEL]: { y: 0.05 } }));
    tracker.record(pose({ [LM.LEFT_HEEL]: { y: 0.05 } }));
    tracker.record(pose({ [LM.LEFT_HEEL]: { y: 0.05 } }));
    expect(tracker.result()).toBeCloseTo(0, 10);
  });

  it("resets cleanly between reps", () => {
    const tracker = createHeelRiseTracker();
    tracker.record(pose({ [LM.LEFT_HEEL]: { y: -0.5 } }));
    tracker.reset();
    tracker.record(pose());
    tracker.record(pose());
    tracker.record(pose());
    expect(tracker.result()).toBeCloseTo(0, 10);
  });
});
