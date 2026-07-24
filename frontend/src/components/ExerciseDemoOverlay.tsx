// UAT remediation (Stage R7): small looping demo clip/photo pinned to the top-right
// corner of the live camera stage, so the user has a reference of correct form while
// exercising -- without leaving the live page or covering the pose skeleton underneath.
import squatLoopSrc from "../assets/videos/Squat Loop.gif";
import stsLoopSrc from "../assets/videos/Sts loop.gif";
import wbltLoopSrc from "../assets/videos/WBLT loop.mp4";
import slsPicSrc from "../assets/exercise type/Single Leg Stance pic.png";

export type ExerciseDemoKind = "squat" | "sts" | "sls" | "wblt";

interface ExerciseDemoOverlayProps {
  kind: ExerciseDemoKind;
}

export default function ExerciseDemoOverlay({ kind }: ExerciseDemoOverlayProps) {
  return (
    <div className={"demo-overlay demo-overlay--" + kind}>
      {kind === "wblt" ? (
        <video className="demo-overlay-media" src={wbltLoopSrc} autoPlay loop muted playsInline />
      ) : (
        <img
          className="demo-overlay-media"
          src={kind === "squat" ? squatLoopSrc : kind === "sts" ? stsLoopSrc : slsPicSrc}
          alt=""
        />
      )}
    </div>
  );
}
