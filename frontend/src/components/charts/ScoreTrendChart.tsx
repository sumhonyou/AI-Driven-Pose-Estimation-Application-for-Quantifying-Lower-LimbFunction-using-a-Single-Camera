import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useTranslation } from "react-i18next";
import type { TrendPoint } from "../../types/api";
import { SCORE_BAND_THRESHOLDS, formatShortDate } from "./dashboardChartUtils";

// Colors are passed as CSS custom-property references (not resolved values) so
// the chart re-themes on light/dark toggle without a React re-render.
const LINE_COLOR = "var(--chart-line)";
// 22% mix (not the app-wide --good-bg token, which sits at ~12-13% and reads as
// nearly invisible under the line's own area-fill gradient, especially in dark
// mode) -- dedicated to these three zones so bumping it doesn't affect the
// unrelated UI (tags, metric icons, etc.) that also reads --good-bg.
const GOOD_ZONE = "color-mix(in srgb, var(--good) 22%, transparent)";
const FAIR_ZONE = "color-mix(in srgb, var(--amber) 22%, transparent)";
const POOR_ZONE = "color-mix(in srgb, var(--coral) 22%, transparent)";

function ScoreTooltip({ active, payload }: any) {
  const { t } = useTranslation();
  if (!active || !payload?.length) return null;
  const point: TrendPoint = payload[0].payload;
  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "var(--r-sm)",
        padding: "10px 12px",
        boxShadow: "var(--shadow)",
        fontSize: "0.81rem",
      }}
    >
      <div style={{ color: "var(--text-3)", marginBottom: 4 }}>{formatShortDate(point.date)}</div>
      <div style={{ fontWeight: 700, color: "var(--text)" }}>
        {point.score != null ? point.score.toFixed(1) : "—"}
        <span style={{ color: "var(--text-3)", fontWeight: 500 }}> /10</span>
        {point.band && (
          <span className={"band " + point.band.toLowerCase()} style={{ marginLeft: 8 }}>
            {t("common." + point.band.toLowerCase())}
          </span>
        )}
      </div>
      {point.confidence != null && (
        <div style={{ color: "var(--text-3)", marginTop: 2 }}>
          {t("dash.confidence")}: {Math.round(point.confidence * 100)}%
        </div>
      )}
    </div>
  );
}

function ZoneLegend() {
  const { t } = useTranslation();
  const items: Array<{ key: "good" | "fair" | "poor"; color: string }> = [
    { key: "good", color: GOOD_ZONE },
    { key: "fair", color: FAIR_ZONE },
    { key: "poor", color: POOR_ZONE },
  ];
  return (
    <div style={{ display: "flex", gap: 16, marginTop: 10, flexWrap: "wrap" }}>
      {items.map(({ key, color }) => (
        <span
          key={key}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            fontSize: "0.78rem",
            color: "var(--text-3)",
          }}
        >
          <span
            style={{
              width: 10,
              height: 10,
              borderRadius: 3,
              background: color,
              border: "1px solid var(--border)",
            }}
          />
          {t("common." + key)}
        </span>
      ))}
    </div>
  );
}

export default function ScoreTrendChart({
  points,
  variant = "full",
}: {
  points: TrendPoint[];
  variant?: "mini" | "full";
}) {
  const isMini = variant === "mini";
  return (
    <>
      <ResponsiveContainer width="100%" height={isMini ? 56 : 240}>
        <AreaChart
          data={points}
          margin={isMini ? undefined : { top: 6, right: 8, left: -18, bottom: 0 }}
        >
          <defs>
            <linearGradient id="scoreAreaFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={LINE_COLOR} stopOpacity={0.26} />
              <stop offset="100%" stopColor={LINE_COLOR} stopOpacity={0} />
            </linearGradient>
          </defs>
          {!isMini && (
            <>
              <CartesianGrid vertical={false} stroke="var(--border-soft)" />
              <ReferenceArea
                y1={0}
                y2={SCORE_BAND_THRESHOLDS.poorMax}
                fill={POOR_ZONE}
                stroke="var(--coral)"
                strokeOpacity={0.25}
                ifOverflow="extendDomain"
              />
              <ReferenceArea
                y1={SCORE_BAND_THRESHOLDS.poorMax}
                y2={SCORE_BAND_THRESHOLDS.fairMax}
                fill={FAIR_ZONE}
                stroke="var(--amber)"
                strokeOpacity={0.25}
                ifOverflow="extendDomain"
              />
              <ReferenceArea
                y1={SCORE_BAND_THRESHOLDS.fairMax}
                y2={10}
                fill={GOOD_ZONE}
                stroke="var(--good)"
                strokeOpacity={0.25}
                ifOverflow="extendDomain"
              />
              <XAxis
                dataKey="date"
                tickFormatter={formatShortDate}
                tick={{ fill: "var(--text-3)", fontSize: 11 }}
                axisLine={{ stroke: "var(--border-soft)" }}
                tickLine={false}
                minTickGap={24}
              />
              <YAxis
                domain={[0, 10]}
                tick={{ fill: "var(--text-3)", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                width={26}
              />
              <Tooltip content={<ScoreTooltip />} />
            </>
          )}
          <Area
            type="monotone"
            dataKey="score"
            stroke={LINE_COLOR}
            strokeWidth={isMini ? 2 : 2.6}
            fill="url(#scoreAreaFill)"
            dot={
              isMini ? false : { r: 3, fill: "var(--surface)", stroke: LINE_COLOR, strokeWidth: 2 }
            }
            activeDot={{ r: 4 }}
            isAnimationActive={false}
            connectNulls
          />
        </AreaChart>
      </ResponsiveContainer>
      {!isMini && <ZoneLegend />}
    </>
  );
}
