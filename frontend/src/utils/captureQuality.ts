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

/** Landmarks the WBLT backend hard-requires per frame for the tested leg
 * (analysis.py `_frame_valid_for_wblt`), keyed by which leg is under test. */
const WBLT_LEG_INDICES: Record<"left" | "right", number[]> = {
  left: [LM.LEFT_KNEE, LM.LEFT_ANKLE, LM.LEFT_HEEL, LM.LEFT_FOOT_INDEX],
  right: [LM.RIGHT_KNEE, LM.RIGHT_ANKLE, LM.RIGHT_HEEL, LM.RIGHT_FOOT_INDEX],
};

/** Both hips — needed for the backend's lateral_alignment quality sub-check
 * (analysis.py, computed from hip x-separation during the calibration window). */
const WBLT_HIP_INDICES = [LM.LEFT_HIP, LM.RIGHT_HIP];

/** Fraction (0-1) of the WBLT-required landmark set (both hips + the tested
 * leg's knee/ankle/heel/foot_index) currently visible. Feed this into
 * useAutoStartGate to gate WBLT's per-attempt positioning phase, so an
 * attempt never starts recording before the backend's own validity gate
 * would actually accept the frames. */
export function computeWbltLegQuality(landmarks: Landmark[], leg: "left" | "right"): number {
  if (!landmarks || landmarks.length === 0) return 0;
  const indices = [...WBLT_HIP_INDICES, ...WBLT_LEG_INDICES[leg]];
  let visible = 0;
  for (const idx of indices) {
    if (landmarks[idx]?.visibility >= VISIBILITY_THRESHOLD) visible++;
  }
  return visible / indices.length;
}

/** computeWbltLegQuality must equal this (i.e. every required landmark
 * visible) before a WBLT attempt is allowed to start — mirrors the backend's
 * all-or-nothing per-frame validity check rather than a lenient fraction. */
export const WBLT_READY_QUALITY_THRESHOLD = 1;

/** True once the tested leg's knee/ankle/heel/foot_index are all visible,
 * regardless of the hips — lets the UI tell "leg out of frame" apart from
 * "camera isn't side-on enough" (see areWbltHipsVisible). */
export function isWbltLegVisible(landmarks: Landmark[], leg: "left" | "right"): boolean {
  if (!landmarks || landmarks.length === 0) return false;
  return WBLT_LEG_INDICES[leg].every((idx) => landmarks[idx]?.visibility >= VISIBILITY_THRESHOLD);
}

/** True once both hips are visible — see isWbltLegVisible. */
export function areWbltHipsVisible(landmarks: Landmark[]): boolean {
  if (!landmarks || landmarks.length === 0) return false;
  return WBLT_HIP_INDICES.every((idx) => landmarks[idx]?.visibility >= VISIBILITY_THRESHOLD);
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
