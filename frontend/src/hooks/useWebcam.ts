// Manages webcam stream: requests permission, attaches to a video element, and cleans up on unmount.
import { useCallback, useEffect, useRef, useState } from "react";

export type WebcamError = "permission-denied" | "no-camera" | "unknown";

export interface UseWebcamResult {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  setVideoRef: React.RefCallback<HTMLVideoElement>;
  ready: boolean; // true once the video is playing
  error: WebcamError | null;
}

export function useWebcam(): UseWebcamResult {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<WebcamError | null>(null);

  const attachStreamToVideo = useCallback((video: HTMLVideoElement, stream: MediaStream) => {
    if (video.srcObject === stream) return;

    video.srcObject = stream;
    video.onloadedmetadata = () => {
      video
        .play()
        .then(() => {
          console.log("[useWebcam] Video playing");
          setReady(true);
        })
        .catch((err) => {
          console.error("[useWebcam] Video play error:", err);
          setError("unknown");
        });
    };
    console.log("[useWebcam] Camera stream attached to video element");
  }, []);

  const setVideoRef = useCallback(
    (video: HTMLVideoElement | null) => {
      videoRef.current = video;
      if (video && streamRef.current) {
        attachStreamToVideo(video, streamRef.current);
      }
    },
    [attachStreamToVideo],
  );

  useEffect(() => {
    let cancelled = false;

    async function start() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 1280 },
            height: { ideal: 720 },
            facingMode: "user",
          },
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }

        streamRef.current = stream;
        console.log("[useWebcam] Camera stream acquired");

        const video = videoRef.current;
        if (video) {
          attachStreamToVideo(video, stream);
        } else {
          console.log("[useWebcam] Waiting for video element before attaching stream");
        }
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
      cancelled = true;
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
        console.log("[useWebcam] Camera stream stopped");
      }
      setReady(false);
    };
  }, [attachStreamToVideo]);

  return { videoRef, setVideoRef, ready, error };
}
