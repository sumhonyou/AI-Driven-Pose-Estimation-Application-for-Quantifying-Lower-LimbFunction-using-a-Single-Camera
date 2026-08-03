// Transparent lift-height guide drawn directly over the video.
//
// `lineYImgNorm` (0=top, 1=bottom of the frame) comes from liveGeometry.ts's IMAGE-
// space calibration, the same coordinate system PoseCanvas uses for the skeleton.
// Null means calibration has not captured a usable frame yet.
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
