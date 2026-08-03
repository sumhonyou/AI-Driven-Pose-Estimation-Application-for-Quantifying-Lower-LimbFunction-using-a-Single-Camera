import type { SessionDTO, TrendPoint } from "../../types/api";

export type ScoreBandThresholds = { poorMax: number; fairMax: number };

// Shared 0-10 score bands (Table 6: Poor 0-4, Fair 4-7, Good 7-10), the same
// cutoffs used by every Module A exercise's score_to_band on the backend
// (app/module_a/core/config.py, app/module_b/core/config.py).
export const SCORE_BAND_THRESHOLDS: ScoreBandThresholds = { poorMax: 4, fairMax: 7 };

// Squat is binary: score > 5.0 is Good, otherwise Poor. Equal poor/fair cutoffs
// collapse the Fair zone without needing a separate chart variant.
const EXERCISE_SCORE_BAND_THRESHOLDS: Record<string, ScoreBandThresholds> = {
  squat: { poorMax: 5, fairMax: 5 },
};

export function scoreBandThresholdsFor(
  exerciseType: string | null | undefined,
): ScoreBandThresholds {
  if (exerciseType && exerciseType in EXERCISE_SCORE_BAND_THRESHOLDS) {
    return EXERCISE_SCORE_BAND_THRESHOLDS[exerciseType];
  }
  return SCORE_BAND_THRESHOLDS;
}

export type BandKey = "good" | "fair" | "poor";

export function bandKey(band: string | null | undefined): BandKey | null {
  if (!band) return null;
  const lower = band.toLowerCase();
  return lower === "good" || lower === "fair" || lower === "poor" ? lower : null;
}

// module_b tag severities are "high"/"medium"/"low"; CSS uses .sev.med, not .sev.medium.
export function severityClass(severity: string | null | undefined): "low" | "med" | "high" {
  if (severity === "high") return "high";
  if (severity === "low") return "low";
  return "med";
}

export function humanizeSnakeCase(value: string): string {
  return value
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function humanizeExerciseType(exerciseType: string, recentSessions: SessionDTO[]): string {
  const match = recentSessions.find((s) => s.exercise_code === exerciseType);
  return match ? match.exercise_name : humanizeSnakeCase(exerciseType);
}

export function formatShortDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(
    new Date(value),
  );
}

export function averageScore(points: TrendPoint[]): number | null {
  const scored = points.filter((p): p is TrendPoint & { score: number } => p.score != null);
  if (scored.length === 0) return null;
  return scored.reduce((sum, p) => sum + p.score, 0) / scored.length;
}
