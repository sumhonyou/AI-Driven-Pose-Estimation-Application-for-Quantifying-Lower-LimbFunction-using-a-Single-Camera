// Regression test for the Phase 3E Stage 2 lesson referenced in task.md Stage
// 4.7: Report.tsx picks its Module A vs Module B render branch off
// `session.exercise_type`, and that choice has silently rendered the wrong
// panel before. This locks in that a "squat" session renders the Module B
// panel (sub-scores + error tags) and never the Module A one, and vice versa
// for a Module A exercise type.
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import "../i18n";
import Report from "./Report";
import { PreferencesProvider } from "../preferences";
import { AuthProvider } from "../auth";
import type { SessionDTO } from "../types/api";
import type { ModuleAResult } from "../services/moduleAService";
import type { ModuleBResult } from "../services/moduleBService";

vi.mock("../services/sessionService", () => ({
  sessionService: { get: vi.fn() },
}));
vi.mock("../services/moduleAService", () => ({
  moduleAService: { get: vi.fn() },
}));
vi.mock("../services/moduleBService", () => ({
  moduleBService: { get: vi.fn() },
}));

import { sessionService } from "../services/sessionService";
import { moduleAService } from "../services/moduleAService";
import { moduleBService } from "../services/moduleBService";

function renderReport(sessionId: string) {
  return render(
    <MemoryRouter initialEntries={[`/report?session=${sessionId}`]}>
      <AuthProvider>
        <PreferencesProvider>
          <Report />
        </PreferencesProvider>
      </AuthProvider>
    </MemoryRouter>,
  );
}

const baseSession: SessionDTO = {
  id: "s1",
  mode: "rehab",
  exercise_code: "squat",
  exercise_name: "Squat",
  exercise_type: "squat",
  started_at: "2026-07-16T00:00:00Z",
  ended_at: "2026-07-16T00:05:00Z",
  status: "complete",
  capture_quality: 0.9,
  valid_frame_ratio: 0.95,
  score: 8,
  band: "good",
  rep_count: 5,
};

const moduleBResult: ModuleBResult = {
  session_id: "s1",
  exercise_code: "squat",
  score: 8,
  band: "Good",
  confidence: 0.9,
  model_version: "stub-0",
  feature_schema_version: "1",
  q: 0.9,
  metrics: {
    rule_score: 8,
    rule_subscores: [{ code: "rom", score: 8, notes: [] }],
    ml_score: 7.5,
    fusion_weights: { w_rule: 0.4, w_ml: 0.6 },
    fusion_flags: [],
    placeholder_model_notice: true,
    capture_quality: { q: 0.9, valid_frame_ratio: 0.95, capture_quality_band: "moderate" },
    per_rep_summaries: [],
  },
  error_tags: [],
  created_at: "2026-07-16T00:05:00Z",
};

const moduleAResult: ModuleAResult = {
  session_id: "s2",
  band: "good",
  score: 8,
  metrics: {
    rep_count: 5,
    target_rep_count: 5,
    completion_time_sec: 12,
    rep_durations_sec: [2, 2, 2, 2, 2],
    avg_rep_time_sec: 2,
    fastest_rep_time_sec: 1.8,
    slowest_rep_time_sec: 2.2,
    knee_rom_deg: 90,
    avg_trunk_lean_deg: 10,
    max_trunk_lean_deg: 15,
    wobble_count: 0,
    session_duration_sec: 12,
    stopped_early: false,
    tracked_leg: null,
    client_attempted_reps: 5,
  },
  warning_tags: [],
  capture_quality_band: "good",
  valid_frame_ratio: 0.95,
  session_status: "complete",
  is_partial_score: false,
  persisted: true,
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("Report", () => {
  it("renders the Module B panel (not Module A) for a squat session", async () => {
    vi.mocked(sessionService.get).mockResolvedValue(baseSession);
    vi.mocked(moduleBService.get).mockResolvedValue(moduleBResult);

    renderReport("s1");

    expect(await screen.findByText(/squat metrics/i)).toBeInTheDocument();
    expect(screen.getAllByText("Moderate").length).toBeGreaterThan(0);
    expect(screen.queryByText("common.moderate")).not.toBeInTheDocument();
    expect(moduleAService.get).not.toHaveBeenCalled();
    // Module A's coaching/"Things to check" panel must not render on the Module B branch.
    expect(screen.queryByText(/things to check/i)).not.toBeInTheDocument();
  });

  it("renders the Module A panel (not Module B) for a sit-to-stand session", async () => {
    vi.mocked(sessionService.get).mockResolvedValue({
      ...baseSession,
      id: "s2",
      exercise_code: "sit_to_stand",
      exercise_type: "sit_to_stand",
    });
    vi.mocked(moduleAService.get).mockResolvedValue(moduleAResult);

    renderReport("s2");

    // Module A's warnings panel is titled "Things to check" (report.warnings).
    expect(await screen.findByText(/things to check/i)).toBeInTheDocument();
    expect(moduleBService.get).not.toHaveBeenCalled();
    expect(screen.queryByText(/squat metrics/i)).not.toBeInTheDocument();
  });

  // Stage 4.7 (Lunge): Module B's "lunge" code contains the substring "lunge"
  // that Module A's "weight_bearing_lunge_test" code also contains -- a real
  // collision bug this test locks in the fix for, not just a hypothetical one.
  it("renders the Module B panel (not Module A) for a lunge session, including the cross-rep symmetry note", async () => {
    vi.mocked(sessionService.get).mockResolvedValue({
      ...baseSession,
      id: "s3",
      exercise_code: "lunge",
      exercise_name: "Leg Lunge",
      exercise_type: "lunge",
    });
    vi.mocked(moduleBService.get).mockResolvedValue({
      ...moduleBResult,
      exercise_code: "lunge",
      metrics: {
        ...moduleBResult.metrics,
        rule_subscores: [
          { code: "rom_completeness", score: 8, notes: [] },
          {
            code: "symmetry_cross_rep",
            score: null,
            notes: [],
            metrics: {
              left_lead_reps: 2,
              right_lead_reps: 1,
              front_knee_peak_symmetry_index_pct: 12.5,
              front_knee_rom_symmetry_index_pct: 8.3,
            },
          },
        ],
      },
    });

    renderReport("s3");

    expect(await screen.findByText(/leg lunge metrics/i)).toBeInTheDocument();
    expect(moduleAService.get).not.toHaveBeenCalled();
    expect(screen.queryByText(/things to check/i)).not.toBeInTheDocument();
    // Symmetry's score is always null (report-only, Stage 4.4 (Lunge)) -- the
    // row must still show its cross-rep numbers, not a bare unexplained "—".
    expect(await screen.findByText(/2.*left-lead.*1.*right-lead/i)).toBeInTheDocument();
  });

  it("renders the Module A panel (not Module B) for a weight-bearing lunge test session", async () => {
    vi.mocked(sessionService.get).mockResolvedValue({
      ...baseSession,
      id: "s4",
      exercise_code: "weight_bearing_lunge_test",
      exercise_name: "Weight-Bearing Lunge Test",
      exercise_type: "weight_bearing_lunge_test",
    });
    vi.mocked(moduleAService.get).mockResolvedValue(moduleAResult);

    renderReport("s4");

    expect(await screen.findByText(/things to check/i)).toBeInTheDocument();
    expect(moduleBService.get).not.toHaveBeenCalled();
    expect(screen.queryByText(/leg lunge metrics/i)).not.toBeInTheDocument();
  });
});
