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
import { SessionProvider } from "../session";
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
          <SessionProvider>
            <Report />
          </SessionProvider>
        </PreferencesProvider>
      </AuthProvider>
    </MemoryRouter>,
  );
}

const baseSession: SessionDTO = {
  target_rep_count: 10,
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
  feedback: {
    structured_feedback: '{"summary": "Grade: Good.", "tips": ["Nice steady pace."]}',
    rewritten_feedback: '{"summary": "Grade: Good.", "tips": ["Nice steady pace."]}',
    rewritten_feedback_structured: {
      summary: "Grade: Good.",
      tips: ["Nice steady pace."],
    },
    feedback_source: "template",
    llm_attempted: false,
    provider: null,
    model_version: null,
    disclaimer_version: "v1",
  },
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
    // Module A's merged coaching panel (labelled "General tip" when no flags fired)
    // must not render on the Module B branch.
    expect(screen.queryByText(/general tip/i)).not.toBeInTheDocument();
    // Stage 5.17: the coaching card renders the structured summary as its own text
    // node and each tip as a real <li>, not a raw JSON/markdown string.
    expect(screen.getByText("Grade: Good.")).toBeInTheDocument();
    const tip = screen.getByText("Nice steady pace.");
    expect(tip.tagName).toBe("LI");
    expect(screen.queryByText(/"summary"/)).not.toBeInTheDocument();
  });

  // Stage 5.20: the breakdown used to list only gate failures, so a set with reps the
  // model rejected on its own showed "8 didn't count" above just 6 reasons. The counts
  // must reconcile: named faults + model-only rejections == total rejected.
  it("accounts for reps the model rejected with no named fault", async () => {
    vi.mocked(sessionService.get).mockResolvedValue(baseSession);
    vi.mocked(moduleBService.get).mockResolvedValue({
      ...moduleBResult,
      metrics: {
        ...moduleBResult.metrics,
        per_rep_summaries: [
          // 2 clean, 1 depth-gated, 2 rejected by the model with no gate.
          { counted_good: true, failed_gates: [] },
          { counted_good: true, failed_gates: [] },
          { counted_good: false, failed_gates: ["insufficient_depth"] },
          { counted_good: false, failed_gates: [] },
          { counted_good: false, failed_gates: [] },
        ],
      },
    } as unknown as ModuleBResult);

    renderReport("s1");

    expect(await screen.findByText(/2 reps counted · 3 didn't count/i)).toBeInTheDocument();
    expect(screen.getByText(/no specific fault identified/i)).toBeInTheDocument();
    expect(screen.getByText(/no specific fault identified/i).textContent).toContain("×2");
    // And the live-vs-final discrepancy is explained rather than left mysterious.
    expect(screen.getByText(/live counter is provisional/i)).toBeInTheDocument();
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

    // Module A's merged coaching panel shows the "General tip" label when
    // warning_tags is empty (moduleAResult mock has no flags).
    expect(await screen.findByText(/general tip/i)).toBeInTheDocument();
    expect(moduleBService.get).not.toHaveBeenCalled();
    expect(screen.queryByText(/squat metrics/i)).not.toBeInTheDocument();
  });

  // Regression test for the "Coaching feedback" merge: previously it showed only
  // warning_tags[0] while "Things to check" listed every fired tag, so a session
  // flagged for two issues silently dropped one of them from any guidance. Now
  // every flagged tag must render with its own label AND its own tip text.
  it("shows every flagged warning tag with its own tip, not just the first one", async () => {
    vi.mocked(sessionService.get).mockResolvedValue({
      ...baseSession,
      id: "s5",
      exercise_code: "sit_to_stand",
      exercise_type: "sit_to_stand",
    });
    vi.mocked(moduleAService.get).mockResolvedValue({
      ...moduleAResult,
      session_id: "s5",
      warning_tags: ["very_slow_completion", "unstable_reps"],
    });

    renderReport("s5");

    expect(
      await screen.findByText(/reps took longer than expected to complete/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/some reps looked unsteady \(partial rise\/sit detected\)/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/try to keep a steadier, quicker rhythm/i)).toBeInTheDocument();
    expect(screen.getByText(/focus on a smooth, controlled rise and sit/i)).toBeInTheDocument();
    // The old single "General tip" label must not appear once there are flags.
    expect(screen.queryByText(/general tip/i)).not.toBeInTheDocument();
  });

  // Leg Lunge was removed from the product (2026-07-19); this test now covers the
  // WBLT side of the collision guard only. The "lunge" Module B code no longer
  // exists to collide with "weight_bearing_lunge_test", but the exact-match check
  // in Report.tsx stays defensive against any future code that would.
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

    expect(await screen.findByText(/general tip/i)).toBeInTheDocument();
    expect(moduleBService.get).not.toHaveBeenCalled();
    expect(screen.queryByText(/leg lunge metrics/i)).not.toBeInTheDocument();
  });
});
