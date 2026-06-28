// Computes capture quality (0–1) from landmark visibility.
// Focuses on lower-limb + torso landmarks critical for this FYP.

import { LM, type Landmark } from "../types/pose";

/** Landmarks that must be visible for a valid lower-limb capture. */
const KEY_INDICES = [
  LM.LEFT_SHOULDER,
  LM.RIGHT_SHOULDER,
  LM.LEFT_HIP,
  LM.RIGHT_HIP,
  LM.LEFT_KNEE,
  LM.RIGHT_KNEE,
  LM.LEFT_ANKLE,
  LM.RIGHT_ANKLE,
];

const VISIBILITY_THRESHOLD = 0.5; // landmark considered "in frame" above this

/**
 * Returns a 0–1 quality score for a single frame.
 * Score = fraction of key landmarks with visibility >= threshold.
 */
export function computeFrameQuality(landmarks: Landmark[]): number {
  if (!landmarks || landmarks.length === 0) return 0;
  let visible = 0;
  for (const idx of KEY_INDICES) {
    if (landmarks[idx]?.visibility >= VISIBILITY_THRESHOLD) visible++;
  }
  return visible / KEY_INDICES.length;
}

/**
 * Tracks valid-frame ratio across a session.
 * A frame is "valid" when capture quality >= minQuality.
 */
export function createSessionQualityTracker(minQuality = 0.6) {
  let totalFrames = 0;
  let validFrames = 0;

  return {
    record(quality: number) {
      totalFrames++;
      if (quality >= minQuality) validFrames++;
    },
    summary() {
      const validFrameRatio = totalFrames > 0 ? validFrames / totalFrames : 0;
      const score = validFrameRatio; // use ratio as overall quality
      return { score, validFrameRatio };
    },
    reset() {
      totalFrames = 0;
      validFrames = 0;
    },
  };
}
