import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useTranslation } from "react-i18next";
import type { TrendPoint } from "../../types/api";
import { formatShortDate } from "./dashboardChartUtils";

// Stage 5.22: replaces the Progress page's old Confidence trend (a model-internal
// diagnostic a patient cannot act on -- see task.md Stage 5.22). Deliberately NOT a
// clean-rep-rate line: since Stage 5.18 the squat score already IS
// `10 * counted / attempts`, so a percentage chart here would just replot the score
// series a second time. This shows what the score alone can't: how many reps were
// actually attempted, and whether a low score came from a hard session or a short one.

export type AttemptsPoint = {
  date: string;
  session_id: string;
  attempts: number;
  counted: number;
  rejected: number;
};

// `score`/`rep_count` are the only fields the backend persists for this -- per-rep
// verdicts aren't stored on the trend endpoint, so `counted` is derived from the two
// rather than summed from raw verdicts. `score` is exactly `10 * counted / attempts`
// (Stage 5.18), so this recovers the same integer Report.tsx would show, not an
// approximation of some other quantity.
export function toAttemptsPoint(point: TrendPoint): AttemptsPoint | null {
  if (point.rep_count == null || point.rep_count <= 0 || point.score == null) return null;
  const counted = Math.round((point.score / 10) * point.rep_count);
  return {
    date: point.date,
    session_id: point.session_id,
    attempts: point.rep_count,
    counted,
    rejected: point.rep_count - counted,
  };
}

function AttemptsTooltip({ active, payload }: any) {
  const { t } = useTranslation();
  if (!active || !payload?.length) return null;
  const point: AttemptsPoint = payload[0].payload;
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
        {t("progress.repsCounted")}: {point.counted}
      </div>
      {point.rejected > 0 && (
        <div style={{ color: "var(--text-3)" }}>
          {t("progress.repsRejected")}: {point.rejected}
        </div>
      )}
    </div>
  );
}

function Legend() {
  const { t } = useTranslation();
  const items: Array<{ key: string; color: string }> = [
    { key: "progress.repsCounted", color: "var(--good)" },
    { key: "progress.repsRejected", color: "var(--amber)" },
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
          <span style={{ width: 10, height: 10, borderRadius: 3, background: color }} />
          {t(key)}
        </span>
      ))}
    </div>
  );
}

export default function RepAttemptsBarChart({ points }: { points: TrendPoint[] }) {
  const { t } = useTranslation();
  const data = points.map(toAttemptsPoint).filter((p): p is AttemptsPoint => p !== null);

  if (data.length === 0) {
    return (
      <p className="muted center" style={{ padding: "16px 0" }}>
        {t("dash.emptySessions")}
      </p>
    );
  }

  return (
    <>
      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={data} margin={{ top: 6, right: 8, left: -18, bottom: 0 }}>
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
            allowDecimals={false}
            tick={{ fill: "var(--text-3)", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={26}
          />
          <Tooltip content={<AttemptsTooltip />} cursor={{ fill: "var(--surface-2)" }} />
          <Bar dataKey="counted" stackId="attempts" fill="var(--good)" />
          <Bar dataKey="rejected" stackId="attempts" fill="var(--amber)" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
      <Legend />
    </>
  );
}
