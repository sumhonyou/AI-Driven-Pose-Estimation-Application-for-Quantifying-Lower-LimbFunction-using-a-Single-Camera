// Vertical "lift progress" gauge: 0 = foot planted at baseline, 100% = at the
// lift-line. Rendered as a tall vertical fill bar anchored to the right of the
// camera view, filling from bottom to top so users can read it at a glance
// from across the room.
import { useTranslation } from "react-i18next";

interface Props {
  liftProgress: number; // 0..1+, see liveGeometry.ts
  aboveLine: boolean;
  visible: boolean;
}

export default function LiftLineMarker({ liftProgress, aboveLine, visible }: Props) {
  const { t } = useTranslation();
  if (!visible) return null;
  const pct = Math.max(0, Math.min(100, liftProgress * 100));

  return (
    <div className="sls-lift-gauge">
      <span className="sls-lift-gauge-label">{t("sls.liftLine")}</span>
      <div className="sls-lift-track-vertical">
        {/* threshold tick at the top */}
        <div className="sls-lift-tick" />
        <div
          className={"sls-lift-fill " + (aboveLine ? "good" : "fair")}
          style={{ height: pct + "%", transition: "height .15s linear" }}
        />
      </div>
    </div>
  );
}
