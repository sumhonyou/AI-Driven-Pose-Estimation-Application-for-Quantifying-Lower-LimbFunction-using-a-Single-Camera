// Generic full-viewport "get ready" countdown shared by live exercise flows.
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useTranslation } from "react-i18next";

interface GetReadyCountdownProps {
  secondsLeft: number;
  eyebrow: string;
  caption: string;
  hints?: string[];
  onCancel: () => void;
  cancelLabel?: string;
}

export default function GetReadyCountdown({
  secondsLeft,
  eyebrow,
  caption,
  hints,
  onCancel,
  cancelLabel,
}: GetReadyCountdownProps) {
  const { t } = useTranslation();

  return createPortal(
    <div className="countdown-overlay" role="status" aria-live="assertive">
      <span className="countdown-eyebrow">{eyebrow}</span>
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
      <p className="countdown-caption">{caption}</p>
      {hints?.map((hint) => (
        <p className="countdown-hint" key={hint}>
          {hint}
        </p>
      ))}
      <button className="btn btn-cancel" onClick={onCancel}>
        {cancelLabel ?? t("live.cancel")}
      </button>
    </div>,
    document.body,
  );
}
