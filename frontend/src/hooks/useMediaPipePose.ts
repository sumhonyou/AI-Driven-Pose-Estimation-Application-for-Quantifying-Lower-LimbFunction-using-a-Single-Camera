// Lazily initialises the MediaPipe PoseLandmarker and runs a rAF detection loop.
// Self-hosts WASM from /mediapipe/wasm and model from /models/.
import { useEffect, useRef, useState, useCallback } from "react";
import { FilesetResolver, PoseLandmarker } from "@mediapipe/tasks-vision";
import { createLandmarkSmoother } from "../utils/poseLandmarks";
import type { Landmark, WorldLandmark } from "../types/pose";

// Singleton landmarker shared across page navigations
let landmarkerInstance: PoseLandmarker | null = null;
let landmarkerLoading = false;

async function getLandmarker(): Promise<PoseLandmarker> {
  if (landmarkerInstance) return landmarkerInstance;
  if (landmarkerLoading) {
    // Wait for the in-flight load to finish
    return new Promise((resolve) => {
      const check = setInterval(() => {
        if (landmarkerInstance) {
          clearInterval(check);
          resolve(landmarkerInstance!);
        }
      }, 100);
    });
  }

  landmarkerLoading = true;
  console.log("[useMediaPipePose] Loading MediaPipe PoseLandmarker...");

  const vision = await FilesetResolver.forVisionTasks("/mediapipe/wasm");
  landmarkerInstance = await PoseLandmarker.createFromOptions(vision, {
    baseOptions: {
      modelAssetPath: "/models/pose_landmarker_full.task",
      // GPU delegate has a known issue where visibility/presence scores aren't
      // populated (google-ai-edge/mediapipe#4479) — CPU reports them correctly.
      delegate: "CPU",
    },
    runningMode: "VIDEO",
    numPoses: 1,
    minPoseDetectionConfidence: 0.5,
    minPosePresenceConfidence: 0.5,
    minTrackingConfidence: 0.5,
  });

  landmarkerLoading = false;
  console.log("[useMediaPipePose] PoseLandmarker ready");
  return landmarkerInstance;
}

export interface UsePoseResult {
  landmarks: Landmark[] | null;
  /** Metric, hip-centered world landmarks (Module A geometry input). Raw from MediaPipe, no smoothing applied. */
  worldLandmarks: WorldLandmark[] | null;
  fps: number;
  ready: boolean;
  error: string | null;
  /** Stop the rAF loop immediately (before navigate) so Cancel/Back are not blocked by CPU detect. */
  stopDetection: () => void;
}

/**
 * Runs the MediaPipe pose detection loop against a playing <video> element.
 * Pass the video ref once webcam is ready.
 */
export function useMediaPipePose(
  videoRef: React.RefObject<HTMLVideoElement | null>,
  webcamReady: boolean,
): UsePoseResult {
  const [landmarks, setLandmarks] = useState<Landmark[] | null>(null);
  const [worldLandmarks, setWorldLandmarks] = useState<WorldLandmark[] | null>(null);
  const [fps, setFps] = useState(0);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const rafRef = useRef<number | null>(null);
  const lastTsRef = useRef<number>(0);
  const frameCountRef = useRef(0);
  const fpsTimerRef = useRef<number>(0);
  const smoother = useRef(createLandmarkSmoother(4));
  // Set by stopDetection so an in-flight detect() does not schedule another frame.
  const stoppedRef = useRef(false);
  const debugPose = import.meta.env.VITE_ENABLE_DEBUG_POSE === "true";

  const stopLoop = useCallback(() => {
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
  }, []);

  // Free the main thread before nav — do not wait for React unmount cleanup.
  const stopDetection = useCallback(() => {
    stoppedRef.current = true;
    stopLoop();
    setLandmarks(null);
    setWorldLandmarks(null);
    console.log("[useMediaPipePose] Detection stopped early");
  }, [stopLoop]);

  useEffect(() => {
    if (!webcamReady) return;

    let cancelled = false;
    stoppedRef.current = false;

    async function init() {
      try {
        const landmarker = await getLandmarker();
        if (cancelled || stoppedRef.current) return;

        setReady(true);
        console.log("[useMediaPipePose] Detection loop started");

        function detect() {
          if (cancelled || stoppedRef.current) return;

          const video = videoRef.current;
          if (!video || video.readyState < 2) {
            if (!cancelled && !stoppedRef.current) {
              rafRef.current = requestAnimationFrame(detect);
            }
            return;
          }

          const nowMs = performance.now();

          // MediaPipe requires monotonically increasing timestamps
          if (nowMs <= lastTsRef.current) {
            if (!cancelled && !stoppedRef.current) {
              rafRef.current = requestAnimationFrame(detect);
            }
            return;
          }
          lastTsRef.current = nowMs;

          const result = landmarker.detectForVideo(video, nowMs);

          if (cancelled || stoppedRef.current) return;

          if (result.landmarks && result.landmarks.length > 0) {
            const smoothed = smoother.current(
              result.landmarks[0].map((lm) => ({
                x: lm.x,
                y: lm.y,
                z: lm.z ?? 0,
                visibility: lm.visibility ?? 0,
              })),
            );
            setLandmarks(smoothed);

            // World landmarks: metric, hip-centered — used for Module A joint-angle geometry.
            if (result.worldLandmarks && result.worldLandmarks.length > 0) {
              setWorldLandmarks(
                result.worldLandmarks[0].map((lm) => ({
                  x: lm.x,
                  y: lm.y,
                  z: lm.z ?? 0,
                  visibility: lm.visibility ?? 0,
                })),
              );
            } else {
              setWorldLandmarks(null);
            }

            if (debugPose) console.debug("[pose] landmarks", smoothed.length);
          } else {
            setLandmarks(null);
            setWorldLandmarks(null);
          }

          // FPS counter (update every second)
          frameCountRef.current++;
          if (nowMs - fpsTimerRef.current >= 1000) {
            setFps(frameCountRef.current);
            frameCountRef.current = 0;
            fpsTimerRef.current = nowMs;
          }

          if (!cancelled && !stoppedRef.current) {
            rafRef.current = requestAnimationFrame(detect);
          }
        }

        rafRef.current = requestAnimationFrame(detect);
      } catch (err) {
        console.error("[useMediaPipePose] Init error:", err);
        setError(err instanceof Error ? err.message : "Failed to load pose model");
      }
    }

    init();

    return () => {
      cancelled = true;
      stopLoop();
      console.log("[useMediaPipePose] Detection loop stopped");
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [webcamReady]);

  return { landmarks, worldLandmarks, fps, ready, error, stopDetection };
}
