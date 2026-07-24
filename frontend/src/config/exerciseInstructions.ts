// UAT remediation (Stage R9): per-exercise content for the shared, reusable
// <ExerciseInstructions> template (pages/ExerciseInstructions.tsx). One config per
// exercise code -- add a new entry here to cover a future exercise; the page itself
// never needs to change. Reference design: Figma "Exercise Instruction / Template"
// (node 12:37), adapted to this app's actual design tokens/components.
import stsDemoSrc from "../assets/videos/sit to stand.mp4";
import slsDemoSrc from "../assets/videos/Balance & Flexibility_ Single Leg Stance Test and Side Leg Raises.mp4";
import wbltDemoSrc from "../assets/videos/(WBLT) Knee to Wall Dorsiflexion Lunge Test for the Ankle.mp4";
import squatDemoSrc from "../assets/videos/Squat.mp4";
import stsAngleSrc from "../assets/exercise type/sit to stand.png";
import slsAngleSrc from "../assets/exercise type/Single Leg Stance pic.png";
import wbltAngleSrc from "../assets/exercise type/WBLT.png";
import squatAngleSrc from "../assets/exercise type/squat in side view.png";
import slsOverlayRefSrc from "../assets/exercise type/SLS overlay reference.png";

export type InstructionExerciseKind = "sts" | "sls" | "wblt" | "squat";

export interface ExerciseInstructionConfig {
  kind: InstructionExerciseKind;
  /** Matches the real backend exercise_code, so the page can look this config up
   * from useSessionFlow()'s exerciseCode without a second mapping table. */
  exerciseCode: string;
  titleKey: string;
  /** UAT remediation (Stage R10): i18n key for the two-sentence, non-diagnostic
   * "why this exercise" blurb (purpose + benefit) — T4's most-repeated content
   * request. Every exercise has one. */
  whyKey: string;
  demoSrc: string;
  /** i18n keys for the numbered steps, in display order. Deliberately variable
   * length per exercise -- the last one or two are always the "what happens if..."
   * consequence step(s) (UAT remediation requirement: explain thresholds/caps in
   * plain language, not just the how-to). */
  stepKeys: string[];
  cameraAngle: {
    image: string;
    captionKey: string;
    expectedViewKey: "instr.viewSide" | "instr.viewFront";
  };
  /** i18n key for the "what you'll need" equipment note (e.g. a chair, or a wall
   * for support/touchdown). Omitted for exercises that need no equipment. */
  equipmentKey?: string;
  /** SLS-only: the ball/line live-overlay explainer, folded into the instruction
   * page per HY's request (previously a separate on-screen legend). */
  overlayExplainer?: {
    titleKey: string;
    bodyKey: string;
    image: string;
  };
}

export const EXERCISE_INSTRUCTIONS: ExerciseInstructionConfig[] = [
  {
    kind: "sts",
    exerciseCode: "sit_to_stand",
    titleKey: "sts.instrTitle",
    whyKey: "sts.whyThisExercise",
    demoSrc: stsDemoSrc,
    stepKeys: ["sts.instrStep1", "sts.instrStep2", "sts.instrStep3", "sts.instrStep4"],
    cameraAngle: {
      image: stsAngleSrc,
      captionKey: "sts.instrCameraCaption",
      expectedViewKey: "instr.viewSide",
    },
    equipmentKey: "sts.instrEquipment",
  },
  {
    kind: "sls",
    exerciseCode: "supported_single_leg_stance",
    titleKey: "sls.instrTitle",
    whyKey: "sls.whyThisExercise",
    demoSrc: slsDemoSrc,
    stepKeys: [
      "sls.instrStep1",
      "sls.instrStep2",
      "sls.instrStep3",
      "sls.instrStep4",
      "sls.instrStep5",
    ],
    cameraAngle: {
      image: slsAngleSrc,
      captionKey: "sls.instrCameraCaption",
      expectedViewKey: "instr.viewFront",
    },
    equipmentKey: "sls.supportGuidance",
    overlayExplainer: {
      titleKey: "sls.instrOverlayTitle",
      bodyKey: "sls.instrOverlayBody",
      image: slsOverlayRefSrc,
    },
  },
  {
    kind: "wblt",
    exerciseCode: "weight_bearing_lunge_test",
    titleKey: "wblt.instrTitle",
    whyKey: "wblt.whyThisExercise",
    demoSrc: wbltDemoSrc,
    stepKeys: ["wblt.instrStep1", "wblt.instrStep2", "wblt.instrStep3", "wblt.instrStep4"],
    cameraAngle: {
      image: wbltAngleSrc,
      captionKey: "wblt.instrCameraCaption",
      expectedViewKey: "instr.viewSide",
    },
    equipmentKey: "wblt.instrEquipment",
  },
  {
    kind: "squat",
    exerciseCode: "squat",
    titleKey: "squat.instrTitle",
    whyKey: "squat.whyThisExercise",
    demoSrc: squatDemoSrc,
    stepKeys: ["squat.instrStep1", "squat.instrStep2", "squat.instrStep3", "squat.instrStep4"],
    cameraAngle: {
      image: squatAngleSrc,
      captionKey: "squat.instrCameraCaption",
      expectedViewKey: "instr.viewSide",
    },
  },
];

export function instructionConfigForExerciseCode(
  exerciseCode: string | null,
): ExerciseInstructionConfig | null {
  if (!exerciseCode) return null;
  return EXERCISE_INSTRUCTIONS.find((c) => c.exerciseCode === exerciseCode) ?? null;
}
