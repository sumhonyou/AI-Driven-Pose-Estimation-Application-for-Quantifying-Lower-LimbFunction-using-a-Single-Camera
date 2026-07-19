import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useTranslation } from "react-i18next";
import type { DashboardErrorTag } from "../../types/api";
import { humanizeSnakeCase, severityClass } from "./dashboardChartUtils";

const SEVERITY_COLOR: Record<string, string> = {
  low: "var(--emerald)",
  med: "var(--amber)",
  high: "var(--coral)",
};

function TagTooltip({ active, payload, message }: any) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "var(--r-sm)",
        padding: "10px 12px",
        boxShadow: "var(--shadow)",
        fontSize: "0.81rem",
        maxWidth: 240,
      }}
    >
      <div style={{ fontWeight: 700, color: "var(--text)", marginBottom: 2 }}>{row.count}×</div>
      <div style={{ color: "var(--text-2)" }}>{message(row.tag_code)}</div>
    </div>
  );
}

// Ranked most-frequent-first (caller sorts); short humanized labels on the axis,
// the full clinical message (existing moduleB.tag_<code> i18n copy) on hover.
export default function ErrorTagBarChart({ tags }: { tags: DashboardErrorTag[] }) {
  const { t } = useTranslation();
  const message = (tagCode: string) =>
    t("moduleB.tag_" + tagCode, { defaultValue: humanizeSnakeCase(tagCode) });

  return (
    <ResponsiveContainer width="100%" height={Math.max(120, tags.length * 42)}>
      <BarChart data={tags} layout="vertical" margin={{ top: 4, right: 16, left: 4, bottom: 4 }}>
        <XAxis type="number" hide allowDecimals={false} />
        <YAxis
          type="category"
          dataKey="tag_code"
          tickFormatter={humanizeSnakeCase}
          tick={{ fill: "var(--text-2)", fontSize: 12 }}
          axisLine={false}
          tickLine={false}
          width={150}
        />
        <Tooltip content={<TagTooltip message={message} />} cursor={{ fill: "var(--surface-2)" }} />
        <Bar dataKey="count" radius={[0, 6, 6, 0]} isAnimationActive={false} barSize={18}>
          {tags.map((tag) => (
            <Cell key={tag.tag_code} fill={SEVERITY_COLOR[severityClass(tag.severity)]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
