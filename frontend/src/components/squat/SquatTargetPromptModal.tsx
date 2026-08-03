// Rep-target picker shown as an overlay so the camera and HUD layout stay stable.
import { useTranslation } from "react-i18next";
import { Target } from "../Icons";

interface Props {
  targetReps: number | null;
  targetOptions: number[];
  onChangeTarget: (value: number | null) => void;
  onStart: () => void;
}

export default function SquatTargetPromptModal({
  targetReps,
  targetOptions,
  onChangeTarget,
  onStart,
}: Props) {
  const { t } = useTranslation();

  return (
    <div className="sls-modal-overlay" role="dialog" aria-modal="true">
      <div className="sls-modal-card">
        <div className="panel-head" style={{ marginBottom: 14 }}>
          <h3>{t("squat.targetPromptTitle")}</h3>
        </div>
        <p className="muted" style={{ marginBottom: 14 }}>
          {t("squat.setupTargetPrompt")}
        </p>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 18 }}>
          <Target width={18} height={18} />
          <select
            className="select"
            value={targetReps ?? ""}
            onChange={(e) => onChangeTarget(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">{t("squat.noTarget")}</option>
            {targetOptions.map((n) => (
              <option key={n} value={n}>
                {t("squat.targetOption", { n })}
              </option>
            ))}
          </select>
        </div>
        <button type="button" className="btn btn-primary btn-block" onClick={onStart}>
          {t("squat.startSet")}
        </button>
      </div>
    </div>
  );
}
