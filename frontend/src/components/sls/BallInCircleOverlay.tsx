// Ball-in-circle stability gauge, overlaid directly on the camera stage.
//
// Design note: the ball position (ballXNorm) is a scale-invariant ratio derived from
// metric WORLD landmarks (hip-midpoint offset / hip width) — it does not correspond
// to a pixel coordinate on the mirrored video feed. Rather than fake a precise
// video-pixel projection (which would misrepresent the geometry), this renders an
// honest self-contained gauge widget.
//
// UAT remediation (Stage R8, T1 "the ball metaphor is opaque" / "the ball is
// spatially divorced from the person"): this used to sit in a bordered card in the
// bottom-left corner, fully detached from the user's body in frame. HY's call: keep
// it a self-contained (not hip-pixel-projected) widget, but drop the corner box
// entirely and float it, transparent, dead-centre over the video -- so the ball
// visually reads as "on me" even though its offset is still a ratio, not a real hip
// pixel position.
import { useTranslation } from "react-i18next";
import { BALL_COLOR_INSIDE, BALL_COLOR_OUTSIDE, CIRCLE_COLOR } from "../../config/slsUi";
import { SLS_CIRCLE_RADIUS_NORM } from "../../config/moduleAThresholds";

interface Props {
  ballXNorm: number;
  ballInside: boolean;
  visible: boolean;
}

const SIZE = 240;
const CENTER = SIZE / 2;
// Keep the ball's pixels-per-hip-width sensitivity constant across radius tweaks
// (matches the prior 0.55 -> 64px mapping, ~116 px/unit) and let the ring itself
// shrink with the tighter tolerance.
const PX_PER_NORM = 64 / 0.55;
const CIRCLE_PX_RADIUS = PX_PER_NORM * SLS_CIRCLE_RADIUS_NORM;
const BALL_RADIUS = 18;

export default function BallInCircleOverlay({ ballXNorm, ballInside, visible }: Props) {
  const { t } = useTranslation();
  if (!visible) return null;

  const maxOffset = CENTER - BALL_RADIUS - 4;
  const ballX = Math.max(-maxOffset, Math.min(maxOffset, ballXNorm * PX_PER_NORM));

  return (
    <div className="sls-ball-overlay" role="status" aria-label={t("sls.stability")}>
      <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`}>
        {/* subtle fill so the target zone is clear against any video background */}
        <circle
          cx={CENTER}
          cy={CENTER}
          r={CIRCLE_PX_RADIUS}
          fill={ballInside ? "rgba(0,174,84,0.10)" : "rgba(255,107,94,0.08)"}
        />
        {/* bold ring */}
        <circle
          cx={CENTER}
          cy={CENTER}
          r={CIRCLE_PX_RADIUS}
          fill="none"
          stroke={ballInside ? "var(--good)" : CIRCLE_COLOR}
          strokeWidth={ballInside ? 4 : 3}
        />
        {/* ball */}
        <circle
          cx={CENTER + ballX}
          cy={CENTER}
          r={BALL_RADIUS}
          fill={ballInside ? BALL_COLOR_INSIDE : BALL_COLOR_OUTSIDE}
        />
        {/* small shadow/depth ring on ball, for contrast against any video colour */}
        <circle
          cx={CENTER + ballX}
          cy={CENTER}
          r={BALL_RADIUS}
          fill="none"
          stroke="rgba(0,0,0,0.25)"
          strokeWidth={2}
        />
      </svg>
      <span className="sls-ball-overlay-label">{t("sls.stability")}</span>
    </div>
  );
}
