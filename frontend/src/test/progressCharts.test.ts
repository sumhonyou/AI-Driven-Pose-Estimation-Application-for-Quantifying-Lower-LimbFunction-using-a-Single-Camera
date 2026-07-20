// Stage 5.22: the Progress page's replacement for the Confidence trend, and the
// per-exercise score-band thresholds fix.
import { describe, it, expect } from "vitest";
import { toAttemptsPoint } from "../components/charts/RepAttemptsBarChart";
import {
  SCORE_BAND_THRESHOLDS,
  scoreBandThresholdsFor,
} from "../components/charts/dashboardChartUtils";
import type { TrendPoint } from "../../src/types/api";

function point(overrides: Partial<TrendPoint> = {}): TrendPoint {
  return {
    session_id: "s1",
    date: "2026-07-20T00:00:00Z",
    score: null,
    band: null,
    capture_quality: null,
    confidence: null,
    rep_count: null,
    ...overrides,
  };
}

describe("toAttemptsPoint", () => {
  it("recovers the exact counted/rejected split Report.tsx would show", () => {
    // The real Stage 5.18 session: 8 of 16 clean -> score 5.0.
    const result = toAttemptsPoint(point({ score: 5.0, rep_count: 16 }));
    expect(result).toEqual({
      date: "2026-07-20T00:00:00Z",
      session_id: "s1",
      attempts: 16,
      counted: 8,
      rejected: 8,
    });
  });

  it("handles a perfect set with zero rejections", () => {
    const result = toAttemptsPoint(point({ score: 10, rep_count: 3 }));
    expect(result).toEqual({
      date: "2026-07-20T00:00:00Z",
      session_id: "s1",
      attempts: 3,
      counted: 3,
      rejected: 0,
    });
  });

  it("handles a set with zero clean reps", () => {
    const result = toAttemptsPoint(point({ score: 0, rep_count: 9 }));
    expect(result?.counted).toBe(0);
    expect(result?.rejected).toBe(9);
  });

  it("returns null for exercises with no rep concept (SLS/WBLT)", () => {
    expect(toAttemptsPoint(point({ score: 8, rep_count: null }))).toBeNull();
  });

  it("returns null when the score is missing", () => {
    expect(toAttemptsPoint(point({ score: null, rep_count: 10 }))).toBeNull();
  });

  it("returns null for a zero-rep session rather than dividing by zero", () => {
    expect(toAttemptsPoint(point({ score: 0, rep_count: 0 }))).toBeNull();
  });

  it("counted + rejected always reconciles to attempts, across the full score range", () => {
    for (let tenth = 0; tenth <= 10; tenth++) {
      const result = toAttemptsPoint(point({ score: tenth, rep_count: 13 }));
      expect(result!.counted + result!.rejected).toBe(13);
    }
  });
});

describe("scoreBandThresholdsFor", () => {
  it("gives squat a 5.0 cut with no Fair band", () => {
    const thresholds = scoreBandThresholdsFor("squat");
    expect(thresholds).toEqual({ poorMax: 5, fairMax: 5 });
    // Zero-width Fair zone -- the property ScoreTrendChart's ZoneLegend relies on
    // to decide whether to render a "Fair" swatch at all.
    expect(thresholds.fairMax).toBe(thresholds.poorMax);
  });

  it("falls back to the shared Module A thresholds for every other exercise", () => {
    for (const exerciseType of ["sit_to_stand", "supported_single_leg_stance", null, undefined]) {
      expect(scoreBandThresholdsFor(exerciseType)).toEqual(SCORE_BAND_THRESHOLDS);
    }
  });
});
