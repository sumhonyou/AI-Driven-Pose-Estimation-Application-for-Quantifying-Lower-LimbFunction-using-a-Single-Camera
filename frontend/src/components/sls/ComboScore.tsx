// Gamified live combo overlay: points + multiplier, display-only (never persisted —
// the report shows the backend's official stabilityScore, computed separately in
// sls/scoring.py). Plays a sound on each multiplier step-up (x1 -> x2 -> x3), never
// on a reset, mirroring the one-shot-on-transition pattern used elsewhere (e.g.
// CameraSetup's "camera ready" sound).
import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { motion, AnimatePresence } from "framer-motion";
import scoreSoundSrc from "../../assets/sound effect/SLS score.mp3";
import { COMBO_MAX_MULTIPLIER } from "../../config/slsUi";

interface Props {
  points: number;
  multiplier: number;
  visible: boolean;
}

export default function ComboScore({ points, multiplier, visible }: Props) {
  const { t } = useTranslation();
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const prevMultiplierRef = useRef(1);

  useEffect(() => {
    if (multiplier > prevMultiplierRef.current) {
      if (!audioRef.current) audioRef.current = new Audio(scoreSoundSrc);
      audioRef.current.currentTime = 0;
      audioRef.current.play().catch(() => {
        // Autoplay can be blocked before a user gesture — non-critical, ignore.
      });
    }
    prevMultiplierRef.current = multiplier;
  }, [multiplier]);

  if (!visible) return null;

  return (
    <div className="sls-combo">
      <div className="sls-combo-points">
        <AnimatePresence mode="popLayout">
          <motion.span
            key={points}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            {points}
          </motion.span>
        </AnimatePresence>
        <span className="sls-combo-label">{t("sls.comboPoints")}</span>
      </div>
      {multiplier > 1 && (
        <motion.div
          key={multiplier}
          className="sls-combo-multiplier"
          initial={{ scale: 1.3, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", stiffness: 400, damping: 15 }}
        >
          ×{multiplier}
        </motion.div>
      )}
      <div className="sls-combo-meter">
        {Array.from({ length: COMBO_MAX_MULTIPLIER }, (_, i) => (
          <span
            key={i}
            className={"sls-combo-pip" + (i < multiplier ? " sls-combo-pip--lit" : "")}
          />
        ))}
      </div>
    </div>
  );
}
