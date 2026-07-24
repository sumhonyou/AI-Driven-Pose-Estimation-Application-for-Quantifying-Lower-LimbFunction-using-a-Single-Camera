// UAT remediation (Stage R8, T1 "the stability ball metaphor is opaque" / S15 "asked
// for a preview image before the session"): a small labelled preview shown once on
// the "ready" screen, before the hold starts, explaining what the two live overlays
// (ball+ring, lift-line) mean -- so they're understood before they matter, not
// discovered mid-hold.
import { useTranslation } from "react-i18next";

export default function OverlayLegend() {
  const { t } = useTranslation();

  return (
    <div className="sls-overlay-legend-wrap">
      <p className="sls-overlay-legend-title">{t("sls.legendTitle")}</p>
      <div className="sls-overlay-legend">
        <div className="sls-overlay-legend-item">
          <svg width={56} height={56} viewBox="0 0 56 56" aria-hidden="true">
            <circle cx={28} cy={28} r={22} fill="none" stroke="var(--border)" strokeWidth={3} />
            <circle cx={34} cy={28} r={9} fill="var(--good)" />
          </svg>
          <p>{t("sls.legendBall")}</p>
        </div>
        <div className="sls-overlay-legend-item">
          <svg width={56} height={56} viewBox="0 0 56 56" aria-hidden="true">
            <line x1={4} y1={18} x2={52} y2={18} stroke="var(--good)" strokeWidth={3} />
            <line
              x1={16}
              y1={18}
              x2={16}
              y2={50}
              stroke="var(--text-3)"
              strokeWidth={2}
              strokeDasharray="3 3"
            />
            <circle cx={16} cy={50} r={4} fill="var(--text-3)" />
          </svg>
          <p>{t("sls.legendLine")}</p>
        </div>
      </div>
    </div>
  );
}
