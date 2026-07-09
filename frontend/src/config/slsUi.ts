// UI-only constants for the Single-Leg Stance live session. No scoring thresholds
// here — those live in moduleAThresholds.ts (mirrored from the backend). These only
// shape the gamified combo overlay, which is display-only and never persisted.

/** Base points earned per second while the ball stays inside the circle (before multiplier). */
export const COMBO_POINTS_PER_SEC = 10;

/** Continuous seconds-inside needed to reach each combo multiplier tier.
 * e.g. inside 0s+ => x1, 3s+ => x2, 7s+ => x3. Resets to x1 the moment the ball exits. */
export const COMBO_TIERS: { atSecInside: number; multiplier: number }[] = [
  { atSecInside: 0, multiplier: 1 },
  { atSecInside: 3, multiplier: 2 },
  { atSecInside: 7, multiplier: 3 },
];

/** Highest multiplier available (used for the combo meter's full mark). */
export const COMBO_MAX_MULTIPLIER = COMBO_TIERS[COMBO_TIERS.length - 1].multiplier;

/** Ball/circle overlay colours (reference the app's CSS variables for theming). */
export const BALL_COLOR_INSIDE = "var(--good)";
export const BALL_COLOR_OUTSIDE = "var(--coral)";
export const CIRCLE_COLOR = "var(--border)";
