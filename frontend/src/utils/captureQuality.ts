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
 * Full-body landmark set used by the Camera Setup auto-start gate — stricter than
 * KEY_INDICES because it also requires the head and feet to be inside the frame.
 */
const FULL_BODY_INDICES = [
  LM.NOSE,
  LM.LEFT_SHOULDER,
  LM.RIGHT_SHOULDER,
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
];

/** Head + feet landmarks — used to give the "head and feet inside frame" checklist item. */
const EDGE_INDICES = [
  LM.NOSE,
  LM.LEFT_ANKLE,
  LM.RIGHT_ANKLE,
  LM.LEFT_HEEL,
  LM.RIGHT_HEEL,
  LM.LEFT_FOOT_INDEX,
  LM.RIGHT_FOOT_INDEX,
];

/** Minimum full-body quality before Camera Setup considers the user "ready". */
export const FULL_BODY_QUALITY_THRESHOLD = 0.6;

/**
 * Returns a 0–1 quality score across the full-body landmark set (head, torso, legs, feet).
 * Used by Camera Setup to gate the auto-start countdown.
 */
export function computeFullBodyQuality(landmarks: Landmark[]): number {
  if (!landmarks || landmarks.length === 0) return 0;
  let visible = 0;
  for (const idx of FULL_BODY_INDICES) {
    if (landmarks[idx]?.visibility >= VISIBILITY_THRESHOLD) visible++;
  }
  return visible / FULL_BODY_INDICES.length;
}

/** True once the head and both feet are visible above the visibility threshold. */
export function areHeadAndFeetVisible(landmarks: Landmark[]): boolean {
  if (!landmarks || landmarks.length === 0) return false;
  return EDGE_INDICES.every((idx) => landmarks[idx]?.visibility >= VISIBILITY_THRESHOLD);
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
