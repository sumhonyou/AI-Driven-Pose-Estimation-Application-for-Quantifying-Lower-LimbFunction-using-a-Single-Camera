// Landmark index constants and skeleton connection pairs for MediaPipe Pose (33 points).
// Also provides a simple moving-average smoother to reduce jitter.

import { LM, type Landmark } from "../types/pose";

/** Skeleton bone connections as [startIndex, endIndex] pairs for drawing. */
export const POSE_CONNECTIONS: [number, number][] = [
  // Torso
  [LM.LEFT_SHOULDER, LM.RIGHT_SHOULDER],
  [LM.LEFT_SHOULDER, LM.LEFT_HIP],
  [LM.RIGHT_SHOULDER, LM.RIGHT_HIP],
  [LM.LEFT_HIP, LM.RIGHT_HIP],
  // Left arm
  [LM.LEFT_SHOULDER, LM.LEFT_ELBOW],
  [LM.LEFT_ELBOW, LM.LEFT_WRIST],
  // Right arm
  [LM.RIGHT_SHOULDER, LM.RIGHT_ELBOW],
  [LM.RIGHT_ELBOW, LM.RIGHT_WRIST],
  // Left leg (highlighted — lower limb focus)
  [LM.LEFT_HIP, LM.LEFT_KNEE],
  [LM.LEFT_KNEE, LM.LEFT_ANKLE],
  [LM.LEFT_ANKLE, LM.LEFT_HEEL],
  [LM.LEFT_ANKLE, LM.LEFT_FOOT_INDEX],
  // Right leg
  [LM.RIGHT_HIP, LM.RIGHT_KNEE],
  [LM.RIGHT_KNEE, LM.RIGHT_ANKLE],
  [LM.RIGHT_ANKLE, LM.RIGHT_HEEL],
  [LM.RIGHT_ANKLE, LM.RIGHT_FOOT_INDEX],
];

/** Lower-limb landmark indices — used to color the key joints differently. */
export const LOWER_LIMB_INDICES: Set<number> = new Set([
  LM.LEFT_HIP,
  LM.RIGHT_HIP,
  LM.LEFT_KNEE,
  LM.RIGHT_KNEE,
  LM.LEFT_ANKLE,
  LM.RIGHT_ANKLE,
  LM.LEFT_HEEL,
  LM.RIGHT_HEEL,
  LM.LEFT_FOOT_INDEX,
  LM.RIGHT_FOOT_INDEX,
]);

/**
 * Moving-average smoother for landmark arrays.
 * Call `smooth(landmarks)` each frame; it blends with the previous N frames.
 */
export function createLandmarkSmoother(windowSize = 4) {
  const history: Landmark[][] = [];

  return function smooth(current: Landmark[]): Landmark[] {
    history.push(current);
    if (history.length > windowSize) history.shift();

    return current.map((_, i) => {
      let x = 0,
        y = 0,
        z = 0,
        vis = 0;
      for (const frame of history) {
        x += frame[i].x;
        y += frame[i].y;
        z += frame[i].z;
        vis += frame[i].visibility;
      }
      const n = history.length;
      return { x: x / n, y: y / n, z: z / n, visibility: vis / n };
    });
  };
}
