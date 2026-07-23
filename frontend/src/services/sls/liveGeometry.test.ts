// UAT remediation (T1, S5 "the lifting too sensitive"): regression coverage for the
// live SLS hold tracker's time-based dwell, mirroring backend
// tests/test_module_a_sls.py::FsmTests. Uses nowMs=0 on the first update so t0=0 and
// every later nowMs equals the elapsed seconds * 1000 directly.

import { describe, expect, it } from "vitest";
import type { WorldLandmark } from "../../types/pose";
import { LM } from "../../types/pose";
import { createSlsLiveTracker } from "./liveGeometry";

function landmark(x = 0, y = 0): WorldLandmark {
  return { x, y, z: 0, visibility: 1 };
}

/** Left leg lifted (leg="left", stance="right"). ankleLiftOffset > 0 raises the left
 * ankle above the y=1 planted baseline (world-y increases downward). */
function frame(ankleLiftOffset = 0): WorldLandmark[] {
  const w = Array.from({ length: 33 }, () => landmark(0, 0));
  w[LM.LEFT_HIP] = landmark(-0.1, 0);
  w[LM.RIGHT_HIP] = landmark(0.1, 0);
  w[LM.LEFT_ANKLE] = landmark(-0.1, 1 - ankleLiftOffset);
  w[LM.RIGHT_ANKLE] = landmark(0.1, 1);
  return w;
}

function calibrate(tracker: ReturnType<typeof createSlsLiveTracker>) {
  tracker.update(frame(0), 0);
  tracker.update(frame(0), 2000);
  // Crosses the 2.0s calibration window; places the lift-line and enters "waiting".
  return tracker.update(frame(0), 2100);
}

describe("createSlsLiveTracker dwell timing", () => {
  it("does not confirm a lift shorter than the dwell window", () => {
    const tracker = createSlsLiveTracker("left");
    calibrate(tracker);

    // Lift held for only 0.1s (< SLS_LIFT_MIN_DWELL_SEC=0.15) then dropped.
    let update = tracker.update(frame(0.5), 2200);
    expect(update.phase).toBe("waiting");
    update = tracker.update(frame(0), 2300);
    expect(update.phase).toBe("waiting");
  });

  it("confirms a lift sustained across the full dwell window", () => {
    const tracker = createSlsLiveTracker("left");
    calibrate(tracker);

    tracker.update(frame(0.5), 2400);
    const update = tracker.update(frame(0.5), 2560); // 0.16s later, past the dwell
    expect(update.phase).toBe("holding");
  });

  it("does not stop on a drop shorter than the drop-dwell window", () => {
    const tracker = createSlsLiveTracker("left");
    calibrate(tracker);
    tracker.update(frame(0.5), 2400);
    tracker.update(frame(0.5), 2560); // confirmed holding

    let update = tracker.update(frame(0), 2600); // brief drop, < 0.1s dwell
    expect(update.phase).toBe("holding");
    update = tracker.update(frame(0.5), 2650); // back up before drop-dwell completes
    expect(update.phase).toBe("holding");
  });

  it("stops once a drop is sustained across the drop-dwell window", () => {
    const tracker = createSlsLiveTracker("left");
    calibrate(tracker);
    tracker.update(frame(0.5), 2400);
    tracker.update(frame(0.5), 2560); // confirmed holding

    tracker.update(frame(0), 2600);
    const update = tracker.update(frame(0), 2710); // 0.11s of sustained drop
    expect(update.phase).toBe("stopped");
  });
});
