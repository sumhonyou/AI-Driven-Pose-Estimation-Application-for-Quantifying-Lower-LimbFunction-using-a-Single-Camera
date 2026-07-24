// UAT remediation (Stage R9): shared, reusable "before you begin" instruction page,
// inserted into the flow as instructions -> camera setup -> countdown -> live. One
// template, driven entirely by config/exerciseInstructions.ts -- adding a future
// exercise only means adding a config entry, never touching this file.
//
// Reference design: Figma "Exercise Instruction / Template" (node 12:37). The Figma
// frame's own "Reusable for all 4 exercises" badge is a note to the designer/dev
// about the frame itself, not user-facing copy -- deliberately not shipped here.
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { DashTopbar } from "../layouts/DashboardLayout";
import { ArrowLeft, Play, Lightbulb } from "../components/Icons";
import { useSessionFlow } from "../session";
import { instructionConfigForExerciseCode } from "../config/exerciseInstructions";

// "Pop out" entrance: a touch bouncier than the site's standard subtle `.reveal`
// fade-up, per HY's request for a more noticeable first appearance. The doc panel
// pops in slightly after the demo panel for a light staggered feel.
const POP_TRANSITION = { type: "spring" as const, stiffness: 300, damping: 26 };

export default function ExerciseInstructions() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const { mode, exerciseCode } = useSessionFlow();
  const [demoPlaying, setDemoPlaying] = useState(false);

  const config = instructionConfigForExerciseCode(exerciseCode);

  function handleBack() {
    nav(`/exercise?mode=${mode}`);
  }

  function handleContinue() {
    nav("/camera");
  }

  if (!config) {
    return <p className="muted">{t("live.noSession")}</p>;
  }

  const expectedView = t(config.cameraAngle.expectedViewKey);

  return (
    <>
      <button type="button" className="back-link" onClick={handleBack}>
        <ArrowLeft />
        {t("common.back")}
      </button>
      <DashTopbar eyebrow={t("instr.eyebrow")} title={t(config.titleKey)} />

      <div className="instr-body">
        <motion.div
          className="panel instr-demo-panel"
          initial={{ opacity: 0, scale: 0.94, y: 16 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={POP_TRANSITION}
        >
          <div className="panel-head" style={{ marginBottom: 14 }}>
            <div>
              <p className="instr-panel-eyebrow">{t("instr.demoEyebrow")}</p>
              <h3>{t("instr.demoTitle")}</h3>
            </div>
            <span className="instr-looping-chip">
              <span className="instr-looping-dot" />
              {t("instr.demoLooping")}
            </span>
          </div>
          <div className="instr-video-stage">
            {demoPlaying ? (
              <video
                src={config.demoSrc}
                controls
                autoPlay
                loop
                playsInline
                className="instr-video"
              />
            ) : (
              <button
                type="button"
                className="instr-play-hint"
                onClick={() => setDemoPlaying(true)}
              >
                <Play />
                <span>{t("instr.demoPlaceholder")}</span>
              </button>
            )}
          </div>
          <p className="instr-demo-caption">{t("instr.demoCaption")}</p>
        </motion.div>

        <motion.div
          className="panel instr-doc-panel"
          initial={{ opacity: 0, scale: 0.94, y: 16 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ ...POP_TRANSITION, delay: 0.08 }}
        >
          <div className="instr-doc-accent" />
          <div>
            <p className="instr-panel-eyebrow">{t("instr.docEyebrow")}</p>
            <h3>{t("instr.docTitle")}</h3>
            <p className="instr-doc-subtitle">{t("instr.docSubtitle")}</p>
          </div>
          <div className="instr-divider" />
          <ol className="instr-steps">
            {config.stepKeys.map((key, i) => (
              <li key={key}>
                <span className="instr-step-number">{i + 1}</span>
                <p>{t(key as never)}</p>
              </li>
            ))}
          </ol>

          <div className="instr-camera-angle">
            <p className="instr-panel-eyebrow instr-camera-eyebrow">{t("instr.cameraEyebrow")}</p>
            <h4>{t("instr.cameraTitle")}</h4>
            <p className="instr-camera-caption">{t(config.cameraAngle.captionKey as never)}</p>
            <div className="instr-camera-diagram">
              <img src={config.cameraAngle.image} alt="" className="instr-camera-image" />
            </div>
            <span className="instr-expected-chip">
              {t("instr.expectedView", { view: expectedView })}
            </span>
          </div>

          {config.equipmentKey && (
            <div className="instr-equipment">
              <span className="instr-equipment-icon">
                <Lightbulb width={16} height={16} />
              </span>
              <p>{t(config.equipmentKey as never)}</p>
            </div>
          )}

          {config.overlayExplainer && (
            <div className="instr-overlay-explainer">
              <h4>{t(config.overlayExplainer.titleKey as never)}</h4>
              <img src={config.overlayExplainer.image} alt="" className="instr-overlay-image" />
              <p>{t(config.overlayExplainer.bodyKey as never)}</p>
            </div>
          )}
        </motion.div>
      </div>

      <motion.div
        className="instr-footer"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ ...POP_TRANSITION, delay: 0.16 }}
      >
        <button type="button" className="btn btn-primary btn-lg" onClick={handleContinue}>
          {t("instr.continueButton")}
        </button>
        <p className="muted">{t("instr.continueCaption")}</p>
      </motion.div>
    </>
  );
}
