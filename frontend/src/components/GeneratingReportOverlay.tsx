// Full-viewport takeover shown while a finished session is being scored on the
// server. Rendered via a portal so it sits above the dashboard shell (sidebar +
// topbar) regardless of where it's mounted. The waveform bars pulse continuously
// (like an audio recorder/voice-input indicator) and the caption cycles through a
// few short "still working" messages so a multi-second wait never reads as frozen.
import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";

// Relative heights give the "sound wave" taper seen in the reference — tall in the
// middle, shrinking toward the edges — then each bar animates its own height.
const BAR_BASE_HEIGHT = [0.35, 0.6, 0.85, 1, 0.85, 0.55, 0.3];
const STEP_INTERVAL_MS = 2200;

export default function GeneratingReportOverlay() {
  const { t } = useTranslation();
  const steps = [
    t("live.generatingStep1"),
    t("live.generatingStep2"),
    t("live.generatingStep3"),
    t("live.generatingStep4"),
  ];
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    const id = window.setInterval(() => {
      setStepIndex((i) => (i + 1) % steps.length);
    }, STEP_INTERVAL_MS);
    return () => window.clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return createPortal(
    <div className="generating-overlay" role="status" aria-live="polite">
      <div className="generating-waveform" aria-hidden="true">
        {BAR_BASE_HEIGHT.map((base, i) => (
          <motion.span
            key={i}
            className="generating-bar"
            animate={{ scaleY: [base * 0.4, base, base * 0.4] }}
            transition={{
              duration: 0.9 + (i % 3) * 0.15,
              repeat: Infinity,
              ease: "easeInOut",
              delay: i * 0.08,
            }}
          />
        ))}
      </div>
      <h2 className="generating-title">{t("live.generatingTitle")}</h2>
      <p className="generating-subtitle">{t("live.generatingSubtitle")}</p>
      <motion.p
        key={stepIndex}
        className="generating-step"
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -6 }}
        transition={{ duration: 0.35 }}
      >
        {steps[stepIndex]}
      </motion.p>
    </div>,
    document.body,
  );
}
