// Full-viewport attempt feedback shown after each lunge is scored — large type so
// the user can read the outcome from across the room without walking back to the screen.
import { createPortal } from "react-dom";
import { useTranslation } from "react-i18next";
import type { WbltAttemptResult } from "../../services/wblt/wbltApi";

interface Props {
  result: WbltAttemptResult;
  onNext: () => void;
}

export default function WbltAttemptResultOverlay({ result, onNext }: Props) {
  const { t } = useTranslation();
  const touchCounted = result.valid_touch;
  const angleText = result.theta_peak_deg != null ? `${result.theta_peak_deg.toFixed(1)}°` : "—";

  return createPortal(
    <div className="wblt-result-overlay" role="dialog" aria-modal="true">
      <p className="wblt-result-eyebrow">{t("wblt.attemptResultTitle")}</p>

      <p
        className={
          "wblt-result-hero " +
          (touchCounted ? "wblt-result-hero--good" : "wblt-result-hero--muted")
        }
      >
        {touchCounted ? t("wblt.touchCounted") : t("wblt.touchNotCounted")}
      </p>

      <div className="wblt-result-metrics">
        <div className="wblt-result-metric">
          <span className="wblt-result-metric-label">{t("wblt.distanceResultLabel")}</span>
          <span className="wblt-result-metric-value">
            {result.target_distance_cm}
            <span className="wblt-result-metric-unit">cm</span>
          </span>
        </div>
        <div className="wblt-result-metric">
          <span className="wblt-result-metric-label">{t("wblt.angleResultLabel")}</span>
          <span className="wblt-result-metric-value">{angleText}</span>
        </div>
      </div>

      {result.next_target_distance_cm != null && !result.leg_complete && (
        <p className="wblt-result-next">
          {t("wblt.nextTargetLabel")}:{" "}
          <strong>{result.next_target_distance_cm.toFixed(1)} cm</strong>
        </p>
      )}

      {result.warning_tags.length > 0 && (
        <ul className="wblt-result-warnings">
          {result.warning_tags.map((tag) => (
            <li key={tag}>{t(`wblt.warn_${tag}`, { defaultValue: tag })}</li>
          ))}
        </ul>
      )}

      <button className="btn btn-primary wblt-result-cta" onClick={onNext}>
        {t("wblt.nextAttempt")}
      </button>
    </div>,
    document.body,
  );
}
