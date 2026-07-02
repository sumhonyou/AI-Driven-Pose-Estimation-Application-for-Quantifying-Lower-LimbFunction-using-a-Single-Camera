// Renders the webcam video + skeleton overlay canvas side-by-side in the cam-stage area.
// Replaces the decorative PoseFigure on Camera Setup and Live Session pages.
import { useEffect, useRef } from "react";
import type { Landmark } from "../types/pose";
import { POSE_CONNECTIONS, LOWER_LIMB_INDICES } from "../utils/poseLandmarks";
import type { WebcamError } from "../hooks/useWebcam";

interface PoseCanvasProps {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  setVideoRef: React.RefCallback<HTMLVideoElement>;
  landmarks: Landmark[] | null;
  webcamReady: boolean;
  webcamError: WebcamError | null;
}

// Colours for skeleton drawing
const BONE_COLOR = "rgba(99, 179, 237, 0.85)"; // blue-ish for upper body
const LOWER_LIMB_COLOR = "rgba(154, 230, 113, 0.9)"; // lime for lower limb (matches app theme)
const JOINT_COLOR = "rgba(255, 255, 255, 0.95)";
const LOWER_JOINT_COLOR = "rgba(154, 230, 113, 1)";

export default function PoseCanvas({
  videoRef,
  setVideoRef,
  landmarks,
  webcamReady,
  webcamError,
}: PoseCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Draw skeleton on canvas whenever landmarks update
  useEffect(() => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video || !webcamReady) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Match canvas size to video dimensions
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!landmarks || landmarks.length === 0) return;

    const w = canvas.width;
    const h = canvas.height;

    // Draw bones
    ctx.lineWidth = 2.5;
    for (const [start, end] of POSE_CONNECTIONS) {
      const a = landmarks[start];
      const b = landmarks[end];
      if (!a || !b) continue;
      if (a.visibility < 0.3 || b.visibility < 0.3) continue;

      const isLower = LOWER_LIMB_INDICES.has(start) || LOWER_LIMB_INDICES.has(end);
      ctx.strokeStyle = isLower ? LOWER_LIMB_COLOR : BONE_COLOR;
      ctx.beginPath();
      ctx.moveTo(a.x * w, a.y * h);
      ctx.lineTo(b.x * w, b.y * h);
      ctx.stroke();
    }

    // Draw joints
    for (let i = 0; i < landmarks.length; i++) {
      const lm = landmarks[i];
      if (!lm || lm.visibility < 0.3) continue;
      const isLower = LOWER_LIMB_INDICES.has(i);
      ctx.fillStyle = isLower ? LOWER_JOINT_COLOR : JOINT_COLOR;
      ctx.beginPath();
      ctx.arc(lm.x * w, lm.y * h, isLower ? 5 : 3, 0, Math.PI * 2);
      ctx.fill();
    }
  }, [landmarks, webcamReady, videoRef]);

  // Error UI when camera is not available
  if (webcamError) {
    const msg =
      webcamError === "permission-denied"
        ? "Camera permission denied. Please allow camera access and reload."
        : webcamError === "no-camera"
          ? "No camera detected. Please connect a webcam."
          : "Could not start camera. Please check your device settings.";

    return (
      <div className="pose-error">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          width={40}
          height={40}
          style={{ marginBottom: 10, opacity: 0.5 }}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z"
          />
        </svg>
        <p
          style={{
            fontSize: "0.88rem",
            color: "var(--text-2)",
            textAlign: "center",
            maxWidth: 240,
          }}
        >
          {msg}
        </p>
      </div>
    );
  }

  return (
    <div className="pose-canvas-wrap">
      {/* Mirrored video feed */}
      <video
        ref={setVideoRef}
        className="pose-video"
        autoPlay
        muted
        playsInline
        style={{ transform: "scaleX(-1)" }}
      />
      {/* Skeleton overlay — also mirrored so it aligns with the flipped video */}
      <canvas ref={canvasRef} className="pose-overlay" style={{ transform: "scaleX(-1)" }} />
      {/* Loading shimmer while model/camera initialises */}
      {!webcamReady && (
        <div className="pose-loading">
          <span className="spinner" />
        </div>
      )}
    </div>
  );
}
