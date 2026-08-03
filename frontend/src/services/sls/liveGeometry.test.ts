// Regression coverage for the live SLS hold tracker's time-based dwell.
// nowMs=0 on the first update makes later timestamps equal elapsed seconds * 1000.

import { describe, expect, it } from "vitest";
import type { Landmark, WorldLandmark } from "../../types/pose";
import { LM } from "../../types/pose";
import { createSlsLiveTracker } from "./liveGeometry";

function landmark(x = 0, y = 0): WorldLandmark {
  return { x, y, z: 0, visibility: 1 };
}

function imgLandmark(x = 0, y = 0): Landmark {
  return { x, y, z: 0, visibility: 1 };
}

/** Fixed 2D (image-space) frame: both feet planted at y=0.9, hips at y=0.5, so
 * stance-leg image length is a known 0.4 for the lineYImgNorm assertions below. */
function imgFrame(): Landmark[] {
  const img = Array.from({ length: 33 }, () => imgLandmark(0, 0));
  img[LM.LEFT_HIP] = imgLandmark(-0.1, 0.5);
  img[LM.RIGHT_HIP] = imgLandmark(0.1, 0.5);
  img[LM.LEFT_ANKLE] = imgLandmark(-0.1, 0.9);
  img[LM.RIGHT_ANKLE] = imgLandmark(0.1, 0.9);
  return img;
}

/** Left leg lifted (leg="left", stance="right"). ankleLiftOffset > 0 raises the left
 * ankle above the y=1 planted baseline (world-y increases downward). stanceLiftOffset
 * does the same for the RIGHT (stance) ankle -- used for wrong-leg-lift coverage. */
function frame(ankleLiftOffset = 0, stanceLiftOffset = 0): WorldLandmark[] {
  const w = Array.from({ length: 33 }, () => landmark(0, 0));
  w[LM.LEFT_HIP] = landmark(-0.1, 0);
  w[LM.RIGHT_HIP] = landmark(0.1, 0);
  w[LM.LEFT_ANKLE] = landmark(-0.1, 1 - ankleLiftOffset);
  w[LM.RIGHT_ANKLE] = landmark(0.1, 1 - stanceLiftOffset);
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

// Coverage for the stance ankle crossing its own lift-line while the target leg stays planted.
describe("createSlsLiveTracker wrong-leg-lift detection", () => {
  it("does not flag a stance-leg rise shorter than the dwell window", () => {
    const tracker = createSlsLiveTracker("left");
    calibrate(tracker);

    let update = tracker.update(frame(0, 0.5), 2200);
    expect(update.wrongLegLifted).toBe(false);
    update = tracker.update(frame(0, 0), 2300);
    expect(update.wrongLegLifted).toBe(false);
  });

  it("flags wrongLegLifted once the stance leg rises for the full dwell window", () => {
    const tracker = createSlsLiveTracker("left");
    calibrate(tracker);

    tracker.update(frame(0, 0.5), 2400);
    const update = tracker.update(frame(0, 0.5), 2560); // 0.16s later, past the dwell
    expect(update.wrongLegLifted).toBe(true);
    expect(update.phase).toBe("waiting"); // the TARGET leg never lifted
  });

  it("clears wrongLegLifted once the stance leg returns and the drop-dwell completes", () => {
    const tracker = createSlsLiveTracker("left");
    calibrate(tracker);
    tracker.update(frame(0, 0.5), 2400);
    tracker.update(frame(0, 0.5), 2560); // confirmed wrongLegLifted

    tracker.update(frame(0, 0), 2600);
    const update = tracker.update(frame(0, 0), 2710); // 0.11s of sustained return
    expect(update.wrongLegLifted).toBe(false);
  });

  it("does not flag the stance leg while the correct target leg is genuinely lifted", () => {
    const tracker = createSlsLiveTracker("left");
    calibrate(tracker);

    tracker.update(frame(0.5, 0), 2400);
    const update = tracker.update(frame(0.5, 0), 2560);
    expect(update.phase).toBe("holding");
    expect(update.wrongLegLifted).toBe(false);
  });
});

// The video lift-line uses image-space height from the optional `img` update argument.
describe("createSlsLiveTracker lineYImgNorm", () => {
  it("stays null when no image landmarks are ever supplied", () => {
    const tracker = createSlsLiveTracker("left");
    const update = calibrate(tracker);
    expect(update.lineYImgNorm).toBeNull();
  });

  it("computes the image-space line height once calibration completes", () => {
    const tracker = createSlsLiveTracker("left");
    tracker.update(frame(0), 0, imgFrame());
    tracker.update(frame(0), 2000, imgFrame());
    // Crosses the 2.0s calibration window with a fixed image frame: baseline ankle
    // image-y=0.9, stance image leg length=0.4, SLS_LIFT_LINE_NORM=0.15 ->
    // 0.9 - 0.15*0.4 = 0.84.
    const update = tracker.update(frame(0), 2100, imgFrame());
    expect(update.lineYImgNorm).toBeCloseTo(0.84, 5);
  });

  it("does not populate lineYImgNorm from a single late/partial image frame", () => {
    const tracker = createSlsLiveTracker("left");
    tracker.update(frame(0), 0); // no image landmarks this frame
    tracker.update(frame(0), 2000); // or this one
    const update = tracker.update(frame(0), 2100);
    expect(update.lineYImgNorm).toBeNull();
  });
});
