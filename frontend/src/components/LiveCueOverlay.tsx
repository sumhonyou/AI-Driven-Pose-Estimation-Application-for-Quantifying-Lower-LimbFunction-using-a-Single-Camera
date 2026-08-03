// Full-viewport corrective cue that keeps the camera and HUD visible underneath.
// Rendered in a portal, auto-dismisses with a countdown ring, and only captures its
// own dismiss button.
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useTranslation } from "react-i18next";
import { Alert, Check, Close } from "./Icons";

const RADIUS = 26;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export type LiveCueTone = "warn" | "good" | "neutral";

interface LiveCueOverlayProps {
  /** The big, glanceable corrective/positive cue, e.g. "Go deeper" or "Nice depth!". */
  title: string;
  /** Smaller supporting line directly under the title, e.g. "Aim for at least 78°
   * knee bend" — the SPECIFIC detail behind the headline, not a separate note. */
  subheading?: string;
  tone?: LiveCueTone;
  /** Auto-dismiss duration in ms — a visible ring counts down to it. */
  autoDismissMs?: number;
  onDismiss: () => void;
}

const ICONS: Record<LiveCueTone, typeof Alert> = { warn: Alert, good: Check, neutral: Alert };

export default function LiveCueOverlay({
  title,
  subheading,
  tone = "warn",
  autoDismissMs = 10000,
  onDismiss,
}: LiveCueOverlayProps) {
  const { t } = useTranslation();
  const [msLeft, setMsLeft] = useState(autoDismissMs);
  const startRef = useRef(0);
  const onDismissRef = useRef(onDismiss);
  onDismissRef.current = onDismiss;

  // Restarts the countdown whenever a NEW cue arrives (title/subheading change), so a
  // second corrective cue while one is already showing gets its own full 10s.
  useEffect(() => {
    startRef.current = performance.now();
    setMsLeft(autoDismissMs);
    const id = window.setInterval(() => {
      const remaining = Math.max(0, autoDismissMs - (performance.now() - startRef.current));
      setMsLeft(remaining);
      if (remaining <= 0) {
        window.clearInterval(id);
        onDismissRef.current();
      }
    }, 100);
    return () => window.clearInterval(id);
  }, [title, subheading, autoDismissMs]);

  const progress = autoDismissMs > 0 ? msLeft / autoDismissMs : 0;
  const offset = CIRCUMFERENCE * (1 - progress);
  const secondsLeft = Math.ceil(msLeft / 1000);
  const Icon = ICONS[tone];

  return createPortal(
    <div
      className={"live-cue-overlay live-cue-overlay--" + tone}
      role="status"
      aria-live="assertive"
    >
      <button className="live-cue-dismiss" onClick={onDismiss} aria-label={t("live.cueDismiss")}>
        <Close width={20} height={20} />
      </button>
      <span className="live-cue-icon">
        <Icon width={34} height={34} />
      </span>
      <div className="live-cue-copy">
        <AnimatePresence mode="wait">
          <motion.p
            key={title + (subheading ?? "")}
            className="live-cue-title"
            initial={{ scale: 0.85, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25, ease: [0.34, 1.56, 0.64, 1] }}
          >
            {title}
          </motion.p>
        </AnimatePresence>
        {subheading && <p className="live-cue-subheading">{subheading}</p>}
      </div>
      <div className="live-cue-ring-wrap">
        <svg className="live-cue-ring" viewBox="0 0 72 72">
          <circle className="live-cue-ring-track" cx="36" cy="36" r={RADIUS} />
          <circle
            className="live-cue-ring-fill"
            cx="36"
            cy="36"
            r={RADIUS}
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={offset}
          />
        </svg>
        <span className="live-cue-ring-number" aria-hidden="true">
          {secondsLeft}
        </span>
      </div>
    </div>,
    document.body,
  );
}
