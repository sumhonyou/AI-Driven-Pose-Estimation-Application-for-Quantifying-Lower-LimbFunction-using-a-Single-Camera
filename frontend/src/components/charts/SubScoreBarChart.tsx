// Horizontal sub-score chart with shared Good/Fair/Poor color bands and hover detail.
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { scoreBandThresholdsFor } from "./dashboardChartUtils";

export interface SubScoreDatum {
  code: string;
  label: string;
  score: number | null;
  /** Plain-language definition shown on hover, alongside the score. */
  meaning: string;
}

function barColor(score: number | null, thresholds: { poorMax: number; fairMax: number }) {
  if (score == null) return "var(--text-3)";
  if (score < thresholds.poorMax) return "var(--coral)";
  if (score < thresholds.fairMax) return "var(--amber)";
  return "var(--good)";
}

function SubScoreTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const row: SubScoreDatum = payload[0].payload;
  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "var(--r-sm)",
        padding: "10px 12px",
        boxShadow: "var(--shadow)",
        fontSize: "0.81rem",
        maxWidth: 260,
      }}
    >
      <div style={{ fontWeight: 700, color: "var(--text)", marginBottom: 4 }}>
        {row.label} — {row.score != null ? `${row.score.toFixed(1)}/10` : "—"}
      </div>
      {row.meaning && <div style={{ color: "var(--text-2)" }}>{row.meaning}</div>}
    </div>
  );
}

export default function SubScoreBarChart({
  data,
  exerciseType,
}: {
  data: SubScoreDatum[];
  exerciseType?: string | null;
}) {
  const thresholds = scoreBandThresholdsFor(exerciseType);

  return (
    <ResponsiveContainer width="100%" height={Math.max(110, data.length * 46)}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 28, left: 4, bottom: 4 }}>
        <XAxis
          type="number"
          domain={[0, 10]}
          tick={{ fill: "var(--text-3)", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          type="category"
          dataKey="label"
          tick={{ fill: "var(--text-2)", fontSize: 12 }}
          axisLine={false}
          tickLine={false}
          width={150}
        />
        <Tooltip content={<SubScoreTooltip />} cursor={{ fill: "var(--surface-2)" }} />
        <Bar dataKey="score" radius={[0, 6, 6, 0]} barSize={20} isAnimationActive={false}>
          {data.map((d) => (
            <Cell key={d.code} fill={barColor(d.score, thresholds)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
