// Shared "before you begin" page driven by config/exerciseInstructions.ts.
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { DashTopbar } from "../layouts/DashboardLayout";
import { ArrowLeft, Play, Lightbulb, Info } from "../components/Icons";
import { useSessionFlow } from "../session";
import { instructionConfigForExerciseCode } from "../config/exerciseInstructions";

// Slightly bouncy entrance with a stagger between the demo and instruction panels.
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

          {/* Non-diagnostic purpose and benefit blurb for the selected exercise. */}
          <div className="instr-why">
            <span className="instr-why-icon">
              <Info width={16} height={16} />
            </span>
            <div>
              <p className="instr-why-title">{t("instr.whyTitle")}</p>
              <p className="instr-why-body">{t(config.whyKey as never)}</p>
            </div>
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
