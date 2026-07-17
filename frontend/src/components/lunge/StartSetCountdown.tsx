// Full-viewport 5-second countdown shown after the user presses "Start Set", giving
// them time to step back and get their whole body in frame before the rep counter
// and live tracking actually start. Mirrors components/squat/StartSetCountdown.tsx
// exactly (task.md Stage 4.7 (Lunge): "follow how squat do and flow") — duplicated
// rather than shared, matching this project's established per-exercise convention
// (backend lunge/segmentation.py duplicates squat/segmentation.py's shape the same
// way). Rendered via a portal so it covers the whole page (sidebar + topbar included).
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useTranslation } from "react-i18next";

interface Props {
  secondsLeft: number;
  onCancel: () => void;
}

export default function StartSetCountdown({ secondsLeft, onCancel }: Props) {
  const { t } = useTranslation();

  return createPortal(
    <div className="countdown-overlay" role="status" aria-live="assertive">
      <span className="countdown-eyebrow">{t("lunge.getReadyEyebrow")}</span>
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
      <p className="countdown-caption">{t("lunge.getReadyCaption")}</p>
      <button className="btn btn-cancel" onClick={onCancel}>
        {t("live.cancel")}
      </button>
    </div>,
    document.body,
  );
}
