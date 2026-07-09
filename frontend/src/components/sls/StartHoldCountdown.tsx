// Full-viewport 5-second countdown shown after the user presses "Start Hold", giving
// them time to get into position before the hold timer + live tracking begins.
// Rendered via a portal so it covers the whole page (sidebar + topbar included),
// matching the take-over pattern used by GeneratingReportOverlay.
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useTranslation } from "react-i18next";

interface Props {
  secondsLeft: number;
  legLabel: string;
  onCancel: () => void;
}

export default function StartHoldCountdown({ secondsLeft, legLabel, onCancel }: Props) {
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
      <p className="countdown-caption">{t("sls.getReadyCaption")}</p>
      <button className="btn btn-cancel" onClick={onCancel}>
        {t("live.cancel")}
      </button>
    </div>,
    document.body,
  );
}
