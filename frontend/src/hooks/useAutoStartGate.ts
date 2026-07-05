// Tracks how long a quality score has stayed above a threshold, and calls `onReady`
// once it has been stable for long enough (e.g. auto-start a session once the full
// body is reliably detected). Debounced so a single lucky frame cannot trigger it,
// and `onReady` fires at most once per hook lifetime.
import { useEffect, useRef, useState } from "react";

export interface AutoStartGateResult {
  /** 0–1 progress of the current stability countdown. Resets to 0 if quality drops. */
  progress: number;
  /**
   * True as soon as progress has started accumulating, and stays true through brief
   * dips (see GRACE_MS) so the countdown UI doesn't flicker on/off with single noisy
   * frames. Use this instead of the raw quality/threshold check to decide whether to
   * render the countdown.
   */
  active: boolean;
}

const POLL_MS = 100; // countdown resolution — smooth enough for a visible progress UI
// Pose landmark visibility can dip for a single frame (motion blur, brief occlusion)
// even while the user is standing still and fully in frame. Without tolerance, that
// one bad frame would reset the whole countdown, making it feel like it never
// progresses or flicker in and out of view. A short grace window lets progress keep
// counting through brief dips, only resetting if quality stays bad for longer than this.
const GRACE_MS = 500;

export function useAutoStartGate(
  quality: number,
  threshold: number,
  stableDurationMs: number,
  enabled: boolean,
  onReady: () => void,
): AutoStartGateResult {
  // Keep the latest quality/callback available to the interval without restarting it every frame.
  const qualityRef = useRef(quality);
  const onReadyRef = useRef(onReady);
  useEffect(() => {
    qualityRef.current = quality;
  });
  useEffect(() => {
    onReadyRef.current = onReady;
  });

  const [progress, setProgress] = useState(0);
  const [active, setActive] = useState(false);

  // Accumulated "good" time counts up only while quality meets the threshold, but
  // tolerates a bad streak shorter than GRACE_MS without losing progress — it only
  // resets to 0 once quality has been bad for longer than that grace window.
  const accumulatedMsRef = useRef(0);
  const badStreakMsRef = useRef(0);
  const hasTriggeredRef = useRef(false);

  useEffect(() => {
    if (!enabled || hasTriggeredRef.current) return;

    const intervalId = window.setInterval(() => {
      if (hasTriggeredRef.current) return;

      const meetsThreshold = qualityRef.current >= threshold;

      if (meetsThreshold) {
        badStreakMsRef.current = 0;
        accumulatedMsRef.current = Math.min(stableDurationMs, accumulatedMsRef.current + POLL_MS);
      } else {
        badStreakMsRef.current += POLL_MS;
        if (badStreakMsRef.current > GRACE_MS) {
          accumulatedMsRef.current = 0;
          badStreakMsRef.current = 0;
        }
      }

      const nextProgress = Math.min(1, accumulatedMsRef.current / stableDurationMs);
      setProgress(nextProgress);
      setActive(accumulatedMsRef.current > 0);

      if (nextProgress >= 1) {
        hasTriggeredRef.current = true;
        onReadyRef.current();
      }
    }, POLL_MS);

    return () => window.clearInterval(intervalId);
  }, [enabled, threshold, stableDurationMs]);

  return { progress, active };
}
