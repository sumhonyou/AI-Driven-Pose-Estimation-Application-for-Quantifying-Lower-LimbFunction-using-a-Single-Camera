// Types for MediaPipe pose landmark data used across Camera and Live pages.

/** A single body landmark with normalized x/y/z coordinates and visibility score (0–1). */
export interface Landmark {
  x: number;
  y: number;
  z: number;
  visibility: number;
}

/** A world-space landmark: metric (meters), hip-centered, scale-invariant. Used for Module A geometry. */
export interface WorldLandmark {
  x: number;
  y: number;
  z: number;
  visibility: number;
}

/** One frame of pose data: timestamp + all 33 landmarks (image-space for overlay, world-space for geometry). */
export interface PoseFrame {
  timestampMs: number;
  landmarks: Landmark[];
  worldLandmarks: WorldLandmark[];
}

/** Capture quality summary for a session or a moment in time. */
export interface CaptureQuality {
  /** 0–1 score based on key landmark visibility and in-frame check. */
  score: number;
  /** Fraction of frames considered valid (key landmarks visible above threshold). */
  validFrameRatio: number;
}

/** MediaPipe Pose Landmarker indices for the 33 body points. */
export const LM = {
  NOSE: 0,
  LEFT_EYE: 1,
  RIGHT_EYE: 2,
  LEFT_EAR: 7,
  RIGHT_EAR: 8,
  LEFT_SHOULDER: 11,
  RIGHT_SHOULDER: 12,
  LEFT_ELBOW: 13,
  RIGHT_ELBOW: 14,
  LEFT_WRIST: 15,
  RIGHT_WRIST: 16,
  LEFT_HIP: 23,
  RIGHT_HIP: 24,
  LEFT_KNEE: 25,
  RIGHT_KNEE: 26,
  LEFT_ANKLE: 27,
  RIGHT_ANKLE: 28,
  LEFT_HEEL: 29,
  RIGHT_HEEL: 30,
  LEFT_FOOT_INDEX: 31,
  RIGHT_FOOT_INDEX: 32,
} as const;
