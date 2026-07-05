// Full-viewport overlay shown immediately after the auto-start countdown completes,
// while CameraSetup is waiting for the server to create the session. Rendered via
// a portal so it covers the sidebar and topbar too. The quality percentage gives
// the user visible confirmation from across the room that the body was detected well.
import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";

const BAR_BASE_HEIGHT = [0.3, 0.55, 0.8, 1, 0.8, 0.55, 0.3];
const STEP_INTERVAL_MS = 1800;

interface Props {
  /** 0–1 body quality score at the moment the session started. */
  bodyQuality: number;
}

function qualityColor(q: number): string {
  if (q >= 0.7) return "var(--accent-text)";
  if (q >= 0.45) return "var(--warn, #f5a623)";
  return "var(--coral)";
}

export default function StartingSessionOverlay({ bodyQuality }: Props) {
  const { t } = useTranslation();
  const steps = [t("camera.startingStep1"), t("camera.startingStep2"), t("camera.startingStep3")];
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    const id = window.setInterval(() => {
      setStepIndex((i) => (i + 1) % steps.length);
    }, STEP_INTERVAL_MS);
    return () => window.clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const qualityPct = Math.round(bodyQuality * 100);
  const color = qualityColor(bodyQuality);

  return createPortal(
    <div className="generating-overlay" role="status" aria-live="polite">
      {/* Quality score — large enough to read from across the room */}
      <motion.div
        className="starting-quality-badge"
        initial={{ scale: 0.7, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.4, ease: [0.34, 1.56, 0.64, 1] }}
        style={{ color }}
      >
        <span className="starting-quality-pct">{qualityPct}%</span>
        <span className="starting-quality-label" style={{ color }}>
          {t("camera.quality")}
        </span>
      </motion.div>

      {/* Waveform — same motion pattern as GeneratingReportOverlay */}
      <div className="generating-waveform" aria-hidden="true" style={{ marginBottom: 24 }}>
        {BAR_BASE_HEIGHT.map((base, i) => (
          <motion.span
            key={i}
            className="generating-bar"
            style={{ background: color }}
            animate={{ scaleY: [base * 0.35, base, base * 0.35] }}
            transition={{
              duration: 0.85 + (i % 3) * 0.14,
              repeat: Infinity,
              ease: "easeInOut",
              delay: i * 0.07,
            }}
          />
        ))}
      </div>

      <h2 className="generating-title">{t("camera.startingTitle")}</h2>
      <p className="generating-subtitle">{t("camera.startingSubtitle")}</p>
      <motion.p
        key={stepIndex}
        className="generating-step"
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -6 }}
        transition={{ duration: 0.3 }}
        style={{ color }}
      >
        {steps[stepIndex]}
      </motion.p>
    </div>,
    document.body,
  );
}
