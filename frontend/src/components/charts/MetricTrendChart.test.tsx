// Progress trend coverage. jsdom has no layout, so this verifies the rendered
// legend, empty state, and safe mount path rather than chart line geometry.
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import "../../i18n";
import MetricTrendChart, { type MetricSeries } from "./MetricTrendChart";
import type { TrendPoint } from "../../types/api";

function point(overrides: Partial<TrendPoint>): TrendPoint {
  return {
    session_id: crypto.randomUUID(),
    date: "2026-07-20T00:00:00Z",
    score: null,
    band: null,
    capture_quality: null,
    confidence: null,
    rep_count: null,
    completion_time_sec: null,
    avg_rep_time_sec: null,
    hold_left_sec: null,
    hold_right_sec: null,
    distance_left_cm: null,
    distance_right_cm: null,
    ...overrides,
  };
}

const legSeries: MetricSeries[] = [
  { dataKey: "hold_left_sec", label: "Left leg", color: "var(--chart-line)" },
  { dataKey: "hold_right_sec", label: "Right leg", color: "var(--info-blue)" },
];

afterEach(cleanup);

describe("MetricTrendChart", () => {
  it("renders a per-leg legend when two series are plotted", () => {
    render(
      <MetricTrendChart
        points={[point({ hold_left_sec: 12.5, hold_right_sec: 9 })]}
        series={legSeries}
        unit="s"
        yAxisLabel="Seconds"
      />,
    );
    expect(screen.getByText("Left leg")).toBeInTheDocument();
    expect(screen.getByText("Right leg")).toBeInTheDocument();
  });

  it("shows the empty state when no point has a value for any plotted series", () => {
    // A session with only STS fields set must not plot on an SLS chart.
    render(
      <MetricTrendChart
        points={[point({ completion_time_sec: 13 })]}
        series={legSeries}
        unit="s"
        yAxisLabel="Seconds"
      />,
    );
    expect(screen.getByText(/no saved sessions yet/i)).toBeInTheDocument();
  });

  it("omits the legend for a single-series chart", () => {
    render(
      <MetricTrendChart
        points={[point({ completion_time_sec: 13 })]}
        series={[
          { dataKey: "completion_time_sec", label: "Completion time", color: "var(--chart-line)" },
        ]}
        unit="s"
        yAxisLabel="Seconds"
      />,
    );
    expect(screen.queryByText("Completion time")).not.toBeInTheDocument();
  });
});
