import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useTranslation } from "react-i18next";
import type { TrendPoint } from "../../types/api";
import { formatShortDate } from "./dashboardChartUtils";

// Stage R12 (UAT): the per-exercise raw-metric trend that replaces the rejected
// capture-quality trend on the Progress page. One generic line chart drives all
// three time/distance series -- STS finish + avg-rep time, SLS best hold per leg,
// WBLT best reach per leg -- since they differ only in which TrendPoint fields
// they read, their unit, and their labels (rules.md #16: one component, not three
// near-duplicates). Every series carries an explicit Y-axis unit label and a
// "Date" X-axis label, and hovering a point reveals each series' exact value.

export type MetricSeries = {
  // Which TrendPoint field this line plots. Restricted to the numeric series
  // fields so a typo can't silently point at `band`/`date`.
  dataKey:
    | "completion_time_sec"
    | "avg_rep_time_sec"
    | "hold_left_sec"
    | "hold_right_sec"
    | "distance_left_cm"
    | "distance_right_cm";
  label: string;
  color: string;
};

function MetricTooltip({
  active,
  payload,
  series,
  unit,
  decimals,
}: {
  active?: boolean;
  payload?: Array<{ payload: TrendPoint }>;
  series: MetricSeries[];
  unit: string;
  decimals: number;
}) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;
  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "var(--r-sm)",
        padding: "8px 10px",
        boxShadow: "var(--shadow)",
        fontSize: "0.78rem",
      }}
    >
      <div style={{ color: "var(--text-3)", marginBottom: 4 }}>{formatShortDate(point.date)}</div>
      {series.map((s) => {
        const value = point[s.dataKey];
        return (
          <div
            key={s.dataKey}
            style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--text)" }}
          >
            <span
              style={{ width: 9, height: 9, borderRadius: 3, background: s.color, flex: "none" }}
            />
            <span style={{ color: "var(--text-3)" }}>{s.label}:</span>
            <b>{value != null ? `${value.toFixed(decimals)}${unit}` : "—"}</b>
          </div>
        );
      })}
    </div>
  );
}

function Legend({ series }: { series: MetricSeries[] }) {
  // Only worth a legend when more than one line shares the plot (per-leg charts).
  if (series.length < 2) return null;
  return (
    <div style={{ display: "flex", gap: 16, marginTop: 10, flexWrap: "wrap" }}>
      {series.map((s) => (
        <span
          key={s.dataKey}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            fontSize: "0.78rem",
            color: "var(--text-3)",
          }}
        >
          <span style={{ width: 10, height: 10, borderRadius: 3, background: s.color }} />
          {s.label}
        </span>
      ))}
    </div>
  );
}

export default function MetricTrendChart({
  points,
  series,
  unit,
  yAxisLabel,
  decimals = 1,
}: {
  points: TrendPoint[];
  series: MetricSeries[];
  // Short unit suffix on values, e.g. "s" or " cm".
  unit: string;
  // Spelled-out Y-axis caption, e.g. "Seconds" / "Centimetres".
  yAxisLabel: string;
  decimals?: number;
}) {
  const { t } = useTranslation();
  // A point contributes only if at least one plotted series has a value there --
  // otherwise an all-null session would open a gap the eye reads as a real dip.
  const data = points.filter((p) => series.some((s) => p[s.dataKey] != null));

  if (data.length === 0) {
    return (
      <p className="muted center" style={{ padding: "16px 0" }}>
        {t("dash.emptySessions")}
      </p>
    );
  }

  return (
    <>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data} margin={{ top: 6, right: 10, left: 4, bottom: 20 }}>
          <CartesianGrid vertical={false} stroke="var(--border-soft)" />
          <XAxis
            dataKey="date"
            tickFormatter={formatShortDate}
            tick={{ fill: "var(--text-3)", fontSize: 11 }}
            axisLine={{ stroke: "var(--border-soft)" }}
            tickLine={false}
            minTickGap={24}
            label={{
              value: t("progress.axisDate"),
              position: "insideBottom",
              offset: -8,
              fill: "var(--text-3)",
              fontSize: 11,
            }}
          />
          <YAxis
            tick={{ fill: "var(--text-3)", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={44}
            label={{
              value: yAxisLabel,
              angle: -90,
              position: "insideLeft",
              style: { textAnchor: "middle", fill: "var(--text-3)", fontSize: 11 },
            }}
          />
          <Tooltip
            content={<MetricTooltip series={series} unit={unit} decimals={decimals} />}
            cursor={{ stroke: "var(--border)" }}
          />
          {series.map((s) => (
            <Line
              key={s.dataKey}
              type="monotone"
              dataKey={s.dataKey}
              name={s.label}
              stroke={s.color}
              strokeWidth={2.4}
              dot={{ r: 3, fill: "var(--surface)", stroke: s.color, strokeWidth: 2 }}
              activeDot={{ r: 4 }}
              isAnimationActive={false}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
      <Legend series={series} />
    </>
  );
}
