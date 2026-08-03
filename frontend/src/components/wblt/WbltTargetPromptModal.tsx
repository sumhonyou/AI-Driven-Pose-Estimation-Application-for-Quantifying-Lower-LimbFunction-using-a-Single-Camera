// Per-attempt target and instructions shown as an overlay to keep the live layout stable.
import { useTranslation } from "react-i18next";

interface Props {
  targetDistanceCm: number;
  onStart: () => void;
}

export default function WbltTargetPromptModal({ targetDistanceCm, onStart }: Props) {
  const { t } = useTranslation();

  return (
    <div className="sls-modal-overlay" role="dialog" aria-modal="true">
      <div className="sls-modal-card">
        <div className="panel-head" style={{ marginBottom: 14 }}>
          <h3>{t("wblt.targetInstruction")}</h3>
        </div>
        <div className="wblt-target-distance">
          {targetDistanceCm.toFixed(1)}
          <span className="wblt-target-distance-unit">cm</span>
        </div>
        <ol className="setup-guidance-list">
          <li>{t("wblt.setupGuidanceSide")}</li>
          <li>{t("wblt.setupGuidanceDistance")}</li>
          <li>{t("wblt.setupGuidanceLunge")}</li>
        </ol>
        <button
          type="button"
          className="btn btn-primary btn-block"
          onClick={onStart}
          style={{ marginTop: 16 }}
        >
          {t("wblt.startAttempt")}
        </button>
      </div>
    </div>
  );
}
