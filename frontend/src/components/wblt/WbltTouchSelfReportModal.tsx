// Post-attempt self-report: did the knee touch the wall? Camera-measured heel-lift
// validity can still override an over-optimistic "yes" server-side (see analysis.py),
// so this is a self-report input, not the final word. Full-page overlay, matching
// SLS's SupportSelfReportModal pattern.
import { createPortal } from "react-dom";
import { useTranslation } from "react-i18next";

interface Props {
  onSelect: (touched: boolean) => void;
}

export default function WbltTouchSelfReportModal({ onSelect }: Props) {
  const { t } = useTranslation();

  return createPortal(
    <div className="sls-modal-overlay" role="dialog" aria-modal="true">
      <div className="sls-modal-card">
        <h3>{t("wblt.touchQuestion")}</h3>
        <div className="sls-modal-actions">
          <button className="btn btn-ghost btn-block" onClick={() => onSelect(false)}>
            {t("wblt.touchNo")}
          </button>
          <button className="btn btn-primary btn-block" onClick={() => onSelect(true)}>
            {t("wblt.touchYes")}
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
