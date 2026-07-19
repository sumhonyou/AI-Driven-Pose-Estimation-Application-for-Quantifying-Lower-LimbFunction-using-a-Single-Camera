import { useTranslation } from "react-i18next";
import type { TrendPoint } from "../../types/api";
import { bandKey, type BandKey } from "./dashboardChartUtils";

const BAND_ORDER: BandKey[] = ["good", "fair", "poor"];
const BAND_COLOR: Record<BandKey, string> = {
  good: "var(--good)",
  fair: "var(--amber)",
  poor: "var(--coral)",
};

export default function BandDistributionBar({ points }: { points: TrendPoint[] }) {
  const { t } = useTranslation();
  const counts: Record<BandKey, number> = { good: 0, fair: 0, poor: 0 };
  for (const p of points) {
    const key = bandKey(p.band);
    if (key) counts[key] += 1;
  }
  const total = counts.good + counts.fair + counts.poor;

  if (total === 0) {
    return <p className="muted">{t("dash.emptySessions")}</p>;
  }

  return (
    <div>
      <div className="band-dist-bar">
        {BAND_ORDER.map((key) =>
          counts[key] > 0 ? (
            <div
              key={key}
              className="band-dist-seg"
              style={{
                flexBasis: `${(counts[key] / total) * 100}%`,
                background: BAND_COLOR[key],
              }}
              title={`${t("common." + key)}: ${counts[key]}`}
            />
          ) : null,
        )}
      </div>
      <div className="band-dist-legend">
        {BAND_ORDER.map((key) => (
          <span className="band-dist-legend-item" key={key}>
            <span className="sev" style={{ background: BAND_COLOR[key] }} />
            {t("common." + key)} <b>{counts[key]}</b>
          </span>
        ))}
      </div>
    </div>
  );
}
