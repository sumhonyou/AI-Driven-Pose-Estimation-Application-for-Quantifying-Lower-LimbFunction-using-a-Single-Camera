// Client-side port of backend app/module_a/core/smoothing.py's One Euro Filter.
// Same params, same math -- so a live tracker's geometry (e.g. WBLT heel-lift
// detection) tracks what the backend's authoritative recompute will see. Without
// this, the live check runs on raw/noisy landmarks while the backend smooths first,
// so the two can disagree on borderline signals: the live HUD flags a lift the
// backend's smoothed recompute then doesn't confirm (or vice versa).
//
// Reference: Casiez et al., "1€ Filter: A Simple Speed-based Low-pass Filter
// for Noisy Input in Interactive Systems" (blueprint §4.2).

const MIN_VISIBILITY = 0.5; // mirrors backend app/module_a/core/config.py

class OneEuroFilter {
  private readonly minCutoff: number;
  private readonly beta: number;
  private readonly dCutoff: number;
  private xPrev: number | null = null;
  private dxPrev = 0;
  private tPrev: number | null = null;

  constructor(minCutoff = 1.0, beta = 0.5, dCutoff = 1.0) {
    this.minCutoff = minCutoff;
    this.beta = beta;
    this.dCutoff = dCutoff;
  }

  private static alpha(cutoff: number, dt: number): number {
    const tau = 1.0 / (2 * Math.PI * cutoff);
    return 1.0 / (1.0 + tau / dt);
  }

  filter(x: number, t: number): number {
    if (this.tPrev === null) {
      this.xPrev = x;
      this.tPrev = t;
      return x;
    }
    const dt = Math.max(t - this.tPrev, 1e-6);
    this.tPrev = t;

    const dx = (x - (this.xPrev as number)) / dt;
    const aD = OneEuroFilter.alpha(this.dCutoff, dt);
    const dxHat = aD * dx + (1 - aD) * this.dxPrev;
    this.dxPrev = dxHat;

    const cutoff = this.minCutoff + this.beta * Math.abs(dxHat);
    const a = OneEuroFilter.alpha(cutoff, dt);
    const xHat = a * x + (1 - a) * (this.xPrev as number);
    this.xPrev = xHat;
    return xHat;
  }
}

export interface SmoothableLandmark {
  x: number;
  y: number;
  z: number;
  visibility: number;
}

/** Causal port of backend `preprocessing._release_persistent_occlusions`.
 *
 * `LandmarkSmoother` hold-lasts any landmark below MIN_VISIBILITY. That is right for a
 * brief occlusion, but a single side-view camera violates the assumption structurally:
 * a limb can sit below the threshold for an entire set, and hold-last then freezes it at
 * its standing pose — turning "uncertain but usable" into "confidently stale". The
 * backend releases runs longer than `interpolation_max_gap_frames` by raising visibility
 * to exactly MIN_VISIBILITY, so the raw estimate is smoothed instead of frozen. This is
 * the same visibility-bump lever, applied live.
 *
 * ⚠ Causal approximation, not an exact port: the backend sees the whole stream and
 * releases the run retroactively from its first frame. Live, a run is only known to be
 * long once it exceeds the threshold, so the first `maxGapFrames` frames of each run
 * still hold-last. The lag is bounded (5 frames ≈ 0.2 s at 25 fps) and self-corrects.
 *
 * Opt-in — callers that never use it keep the previous hold-last behaviour exactly.
 * Mutates the visibility field of the landmarks it is given.
 */
export function createOcclusionReleaser(maxGapFrames: number) {
  const lowRunLength = new Map<number, number>();
  return {
    apply<T extends SmoothableLandmark>(landmarks: T[]): T[] {
      return landmarks.map((lm, i) => {
        const isLow = (lm.visibility ?? 0) < MIN_VISIBILITY;
        if (!isLow) {
          lowRunLength.set(i, 0);
          return lm;
        }
        const run = (lowRunLength.get(i) ?? 0) + 1;
        lowRunLength.set(i, run);
        if (run <= maxGapFrames) return lm;
        return { ...lm, visibility: MIN_VISIBILITY };
      });
    },
    reset() {
      lowRunLength.clear();
    },
  };
}

/** Runs one OneEuroFilter per landmark index per axis (x, y, z). Landmarks below
 * MIN_VISIBILITY hold their last smoothed value instead of being filtered, so a
 * brief occlusion doesn't inject noise -- mirrors backend LandmarkSmoother exactly. */
export class LandmarkSmoother<T extends SmoothableLandmark> {
  private readonly filters = new Map<string, OneEuroFilter>();
  private readonly last = new Map<number, T>();

  private filterFor(index: number, axis: "x" | "y" | "z"): OneEuroFilter {
    const key = `${index}:${axis}`;
    let f = this.filters.get(key);
    if (!f) {
      f = new OneEuroFilter();
      this.filters.set(key, f);
    }
    return f;
  }

  smoothFrame(timestampSec: number, landmarks: T[]): T[] {
    return landmarks.map((lm, i) => {
      const visibility = lm.visibility ?? 0;
      if (visibility < MIN_VISIBILITY && this.last.has(i)) {
        return this.last.get(i) as T;
      }
      const point = {
        ...lm,
        x: this.filterFor(i, "x").filter(lm.x, timestampSec),
        y: this.filterFor(i, "y").filter(lm.y, timestampSec),
        z: this.filterFor(i, "z").filter(lm.z, timestampSec),
      } as T;
      this.last.set(i, point);
      return point;
    });
  }
}
