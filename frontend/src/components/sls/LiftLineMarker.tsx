// UAT remediation (Stage R8, T1 "the lift-line reads as an abstract bar rather than a
// height on the user"): this used to be a tall vertical fill bar anchored to the side
// of the frame, disconnected from the person. Now it's a transparent horizontal line
// drawn directly over the video at the calibrated lift height, so the user compares
// their own visible foot against the line instead of reading an abstract percentage.
//
// `lineYImgNorm` (0=top, 1=bottom of the frame) comes from liveGeometry.ts's IMAGE-
// space calibration -- the same normalised coordinate system PoseCanvas already uses
// to draw the skeleton overlay (not a new world->pixel projection), so the line lands
// in the same place the skeleton does. It's null until calibration has captured at
// least one usable frame, in which case nothing is rendered yet.
import { useTranslation } from "react-i18next";

interface Props {
  lineYImgNorm: number | null;
  aboveLine: boolean;
  visible: boolean;
}

// Keeps the line comfortably inside the frame even if a noisy calibration briefly
// places it near an edge -- cosmetic clamp only, never affects the real hold FSM.
const MIN_TOP_PCT = 6;
const MAX_TOP_PCT = 94;

export default function LiftLineMarker({ lineYImgNorm, aboveLine, visible }: Props) {
  const { t } = useTranslation();
  if (!visible || lineYImgNorm === null) return null;
  const topPct = Math.max(MIN_TOP_PCT, Math.min(MAX_TOP_PCT, lineYImgNorm * 100));

  return (
    <div className="sls-lift-line" style={{ top: topPct + "%" }}>
      <div className={"sls-lift-line-bar " + (aboveLine ? "good" : "fair")} />
      <span className={"sls-lift-line-label " + (aboveLine ? "good" : "fair")}>
        {t("sls.liftLine")}
      </span>
    </div>
  );
}
