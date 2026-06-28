// Manages webcam stream: requests permission, attaches to a video element, and cleans up on unmount.
import { useEffect, useRef, useState } from "react";

export type WebcamError = "permission-denied" | "no-camera" | "unknown";

export interface UseWebcamResult {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  ready: boolean; // true once the video is playing
  error: WebcamError | null;
}

export function useWebcam(): UseWebcamResult {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<WebcamError | null>(null);

  useEffect(() => {
    let stream: MediaStream | null = null;

    async function start() {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 1280 },
            height: { ideal: 720 },
            facingMode: "user",
          },
          audio: false,
        });
        console.log("[useWebcam] Camera stream acquired");

        const video = videoRef.current;
        if (!video) return;

        video.srcObject = stream;
        video.onloadedmetadata = () => {
          video.play().then(() => {
            console.log("[useWebcam] Video playing");
            setReady(true);
          });
        };
      } catch (err) {
        console.error("[useWebcam] Error:", err);
        if (err instanceof DOMException) {
          if (err.name === "NotAllowedError") setError("permission-denied");
          else if (err.name === "NotFoundError") setError("no-camera");
          else setError("unknown");
        } else {
          setError("unknown");
        }
      }
    }

    start();

    // Stop all tracks on unmount
    return () => {
      if (stream) {
        stream.getTracks().forEach((t) => t.stop());
        console.log("[useWebcam] Camera stream stopped");
      }
    };
  }, []);

  return { videoRef, ready, error };
}
