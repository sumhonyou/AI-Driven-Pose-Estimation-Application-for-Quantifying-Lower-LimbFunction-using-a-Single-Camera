// Buffers per-frame landmarks and quality scores during a session.
// Call summary() at session end to get metrics to send to the backend.
import { useRef, useCallback } from "react";
import type { PoseFrame, CaptureQuality } from "../types/pose";
import { createSessionQualityTracker } from "../utils/captureQuality";

export interface SessionSummary extends CaptureQuality {
  frameCount: number;
  durationMs: number;
  frames: PoseFrame[]; // includes worldLandmarks, sent to Module A analyze endpoint
}

export function useSessionRecorder() {
  const framesRef = useRef<PoseFrame[]>([]);
  const startMsRef = useRef<number>(0);
  const trackerRef = useRef(createSessionQualityTracker(0.6));

  // Call once when session starts
  const start = useCallback(() => {
    framesRef.current = [];
    startMsRef.current = performance.now();
    trackerRef.current.reset();
    console.log("[useSessionRecorder] Recording started");
  }, []);

  // Call each frame with current landmarks and quality score
  const record = useCallback((frame: PoseFrame, quality: number) => {
    framesRef.current.push(frame);
    trackerRef.current.record(quality);
  }, []);

  // Call at session end — returns metrics for backend
  const summary = useCallback((): SessionSummary => {
    const durationMs = performance.now() - startMsRef.current;
    const { score, validFrameRatio } = trackerRef.current.summary();
    console.log(
      `[useSessionRecorder] Summary — frames: ${framesRef.current.length}, quality: ${score.toFixed(2)}, validRatio: ${validFrameRatio.toFixed(2)}`,
    );
    return {
      score,
      validFrameRatio,
      frameCount: framesRef.current.length,
      durationMs,
      frames: framesRef.current,
    };
  }, []);

  return { start, record, summary };
}
