// Full-viewport countdown (WBLT_GET_READY_DURATION_SEC) after positioning is confirmed
// stable — gives the user time to stand upright (so MediaPipe can re-acquire landmarks),
// read the guidance, and settle into the lunge stance before the calibration window
// opens. Portal covers sidebar + topbar, matching StartHoldCountdown / GeneratingReportOverlay.
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useTranslation } from "react-i18next";

interface Props {
  secondsLeft: number;
  legLabel: string;
  onCancel: () => void;
}

export default function WbltGetReadyCountdown({ secondsLeft, legLabel, onCancel }: Props) {
  const { t } = useTranslation();

  return createPortal(
    <div className="countdown-overlay" role="status" aria-live="assertive">
      <span className="countdown-eyebrow">{legLabel}</span>
      <AnimatePresence mode="wait">
        <motion.span
          key={secondsLeft}
          className="countdown-number"
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 1.15, opacity: 0 }}
          transition={{ duration: 0.35, ease: [0.34, 1.56, 0.64, 1] }}
        >
          {secondsLeft}
        </motion.span>
      </AnimatePresence>
      <p className="countdown-caption">{t("wblt.getReadyGuidance")}</p>
      <p className="countdown-hint">{t("wblt.getReadyStandUp")}</p>
      <p className="countdown-hint">{t("wblt.getReadyNoHandTouch")}</p>
      <button className="btn btn-cancel" onClick={onCancel}>
        {t("common.back")}
      </button>
    </div>,
    document.body,
  );
}
