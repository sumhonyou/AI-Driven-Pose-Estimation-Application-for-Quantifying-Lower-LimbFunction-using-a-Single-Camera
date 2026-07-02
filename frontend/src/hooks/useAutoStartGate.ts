// Tracks how long a quality score has stayed above a threshold, and calls `onReady`
// once it has been stable for long enough (e.g. auto-start a session once the full
// body is reliably detected). Debounced so a single lucky frame cannot trigger it,
// and `onReady` fires at most once per hook lifetime.
import { useEffect, useRef, useState } from "react";

export interface AutoStartGateResult {
  /** 0–1 progress of the current stability countdown. Resets to 0 if quality drops. */
  progress: number;
}

const POLL_MS = 100; // countdown resolution — smooth enough for a visible progress UI

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

  const stableSinceRef = useRef<number | null>(null);
  const hasTriggeredRef = useRef(false);

  useEffect(() => {
    if (!enabled || hasTriggeredRef.current) return;

    const intervalId = window.setInterval(() => {
      if (hasTriggeredRef.current) return;

      const meetsThreshold = qualityRef.current >= threshold;
      const now = performance.now();

      if (!meetsThreshold) {
        if (stableSinceRef.current !== null) {
          stableSinceRef.current = null;
          setProgress(0);
        }
        return;
      }

      if (stableSinceRef.current === null) {
        stableSinceRef.current = now;
      }

      const elapsed = now - stableSinceRef.current;
      const nextProgress = Math.min(1, elapsed / stableDurationMs);
      setProgress(nextProgress);

      if (nextProgress >= 1) {
        hasTriggeredRef.current = true;
        onReadyRef.current();
      }
    }, POLL_MS);

    return () => window.clearInterval(intervalId);
  }, [enabled, threshold, stableDurationMs]);

  return { progress };
}
