import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TrendPoint } from "../../types/api";
import { formatShortDate } from "./dashboardChartUtils";

// Shared shape behind the capture-quality trend (Module A + B) and the
// confidence trend (Module B only) -- same 0-1-fraction-over-time mechanism,
// only the field/color/label differ, so one generic component covers both
// rather than two near-duplicate charts (rules.md #16).
type PercentField = "capture_quality" | "confidence";

function PercentTooltip({ active, payload, dataKey, label }: any) {
  if (!active || !payload?.length) return null;
  const point: TrendPoint = payload[0].payload;
  const value = point[dataKey as PercentField];
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
      <div style={{ color: "var(--text-3)" }}>{formatShortDate(point.date)}</div>
      <div style={{ fontWeight: 700, color: "var(--text)" }}>
        {label}: {value != null ? `${Math.round(value * 100)}%` : "—"}
      </div>
    </div>
  );
}

export default function PercentTrendChart({
  points,
  dataKey,
  color,
  label,
  variant = "mini",
}: {
  points: TrendPoint[];
  dataKey: PercentField;
  color: string;
  label: string;
  variant?: "mini" | "full";
}) {
  const isMini = variant === "mini";
  const fillId = `percentFill-${dataKey}`;
  return (
    <ResponsiveContainer width="100%" height={isMini ? 64 : 160}>
      <AreaChart
        data={points}
        margin={isMini ? undefined : { top: 6, right: 8, left: -18, bottom: 0 }}
      >
        <defs>
          <linearGradient id={fillId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.24} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        {!isMini && (
          <>
            <CartesianGrid vertical={false} stroke="var(--border-soft)" />
            <XAxis
              dataKey="date"
              tickFormatter={formatShortDate}
              tick={{ fill: "var(--text-3)", fontSize: 11 }}
              axisLine={{ stroke: "var(--border-soft)" }}
              tickLine={false}
              minTickGap={24}
            />
            <YAxis
              domain={[0, 1]}
              tickFormatter={(v: number) => `${Math.round(v * 100)}%`}
              tick={{ fill: "var(--text-3)", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={38}
            />
          </>
        )}
        <Tooltip content={<PercentTooltip dataKey={dataKey} label={label} />} />
        <Area
          type="monotone"
          dataKey={dataKey}
          stroke={color}
          strokeWidth={isMini ? 2 : 2.4}
          fill={`url(#${fillId})`}
          dot={isMini ? false : { r: 3, fill: "var(--surface)", stroke: color, strokeWidth: 2 }}
          activeDot={{ r: 4 }}
          isAnimationActive={false}
          connectNulls
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
