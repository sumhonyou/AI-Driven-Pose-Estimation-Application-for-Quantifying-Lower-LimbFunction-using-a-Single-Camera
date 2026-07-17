import { describe, expect, it } from "vitest";

import { LM, type WorldLandmark } from "../../types/pose";
import { FALLBACK_LUNGE_LIVE_CONFIG, createLungeLiveEstimator } from "./lungeLiveEstimate";

/** Build a split-stance pose with per-knee visibility we control.
 *
 * `frontLeg` is planted forward along +x (toes ahead of ankles, so anteriorSign is +1).
 * `frontKneeVis`/`backKneeVis` are what the turn-around hint reads: MediaPipe reports
 * lower visibility for whichever limb is further from the camera.
 */
function pose(
  frontLeg: "left" | "right",
  frontKneeVis: number,
  backKneeVis: number,
  frontFlexionDeg = 0,
): WorldLandmark[] {
  const lm = (x: number, y: number, visibility = 1.0): WorldLandmark => ({
    x,
    y,
    z: 0,
    visibility,
  });
  const w: WorldLandmark[] = Array.from({ length: 33 }, () => lm(0, 0));
  const FRONT_X = 0.6;
  const BACK_X = -0.6;
  const FOOT = 0.15;

  const sides = {
    left: {
      shoulder: LM.LEFT_SHOULDER,
      hip: LM.LEFT_HIP,
      knee: LM.LEFT_KNEE,
      ankle: LM.LEFT_ANKLE,
      toe: LM.LEFT_FOOT_INDEX,
    },
    right: {
      shoulder: LM.RIGHT_SHOULDER,
      hip: LM.RIGHT_HIP,
      knee: LM.RIGHT_KNEE,
      ankle: LM.RIGHT_ANKLE,
      toe: LM.RIGHT_FOOT_INDEX,
    },
  };
  const backLeg = frontLeg === "left" ? "right" : "left";

  for (const [leg, baseX, flexDeg, kneeVis] of [
    [frontLeg, FRONT_X, frontFlexionDeg, frontKneeVis],
    [backLeg, BACK_X, 0, backKneeVis],
  ] as const) {
    const s = sides[leg];
    const rad = (flexDeg * Math.PI) / 180;
    w[s.shoulder] = lm(baseX, -1);
    w[s.hip] = lm(baseX, 0);
    w[s.knee] = lm(baseX, 1, kneeVis);
    const ankleX = baseX + Math.sin(rad);
    w[s.ankle] = lm(ankleX, 1 + Math.cos(rad));
    w[s.toe] = lm(ankleX + FOOT, 1 + Math.cos(rad));
  }
  return w;
}

const DEBOUNCE = FALLBACK_LUNGE_LIVE_CONFIG.leadLegHintDebounceFrames;

describe("turn-around hint (lead leg facing away from the camera)", () => {
  it("stays silent when the leading leg is nearest the camera", () => {
    const estimator = createLungeLiveEstimator();
    let update = estimator.update(pose("left", 0.98, 0.77), 0);

    // Well past the debounce window: a correct stance must never trip the hint.
    for (let i = 1; i <= DEBOUNCE * 3; i += 1) {
      update = estimator.update(pose("left", 0.98, 0.77), i * 33);
    }

    expect(update.leadLegAwayFromCamera).toBe(false);
  });

  it("flags the leading leg on the far side of the camera", () => {
    const estimator = createLungeLiveEstimator();
    let update = estimator.update(pose("right", 0.94, 0.99), 0);

    for (let i = 1; i <= DEBOUNCE; i += 1) {
      update = estimator.update(pose("right", 0.94, 0.99), i * 33);
    }

    expect(update.leadLegAwayFromCamera).toBe(true);
  });

  it("does not flash the hint before the debounce window elapses", () => {
    const estimator = createLungeLiveEstimator();

    // One frame short of the threshold — a transient dropout must not show the hint.
    let update = estimator.update(pose("right", 0.94, 0.99), 0);
    for (let i = 1; i < DEBOUNCE - 1; i += 1) {
      update = estimator.update(pose("right", 0.94, 0.99), i * 33);
    }

    expect(update.leadLegAwayFromCamera).toBe(false);
  });

  it("clears once the user turns around", () => {
    const estimator = createLungeLiveEstimator();
    for (let i = 0; i <= DEBOUNCE; i += 1) {
      estimator.update(pose("right", 0.94, 0.99), i * 33);
    }

    // The user turns: the leading leg is now the clearly-visible limb.
    const update = estimator.update(pose("right", 0.99, 0.94), (DEBOUNCE + 1) * 33);

    expect(update.leadLegAwayFromCamera).toBe(false);
  });

  it("separates the two cases on the real measured margin", () => {
    // Stage 5.4 measured front-minus-back knee visibility over all 88 side-view reps:
    // lead-near spans +0.129..+0.319, lead-far spans -0.106..-0.027, with no overlap.
    // The configured margin must sit strictly inside that empty gap, or the hint would
    // misfire on real data.
    const margin = FALLBACK_LUNGE_LIVE_CONFIG.leadLegNearMarginVis;
    expect(margin).toBeGreaterThan(-0.027);
    expect(margin).toBeLessThan(0.129);
  });

  it("is cleared by reset, so a stale hint cannot leak into the next set", () => {
    const estimator = createLungeLiveEstimator();
    for (let i = 0; i <= DEBOUNCE; i += 1) {
      estimator.update(pose("right", 0.94, 0.99), i * 33);
    }
    expect(estimator.update(pose("right", 0.94, 0.99), 999).leadLegAwayFromCamera).toBe(true);

    estimator.reset();

    // First frame of the next set, correct stance: no inherited hint.
    expect(estimator.update(pose("left", 0.98, 0.77), 0).leadLegAwayFromCamera).toBe(false);
  });

  it("never blocks rep counting — the hint is advisory only", () => {
    const estimator = createLungeLiveEstimator();
    const cycle = [0, 50, 95, 50, 0];
    let update = estimator.update(pose("right", 0.94, 0.99, 0), 0);
    let t = 0;
    // Two full rep cycles at 200ms/frame, entirely in the flagged stance.
    for (let rep = 0; rep < 2; rep += 1) {
      for (const deg of cycle) {
        t += 200;
        update = estimator.update(pose("right", 0.94, 0.99, deg), t);
      }
    }

    expect(update.leadLegAwayFromCamera).toBe(true);
    expect(update.repCount).toBeGreaterThan(0);
  });
});
