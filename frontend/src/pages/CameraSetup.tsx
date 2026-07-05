import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useState, useEffect, useRef } from "react";
import stsDemoSrc from "../assets/videos/sit to stand.mp4";
import { DashTopbar } from "../layouts/DashboardLayout";
import PoseCanvas from "../components/PoseCanvas";
import CaptureQualityBadge from "../components/CaptureQualityBadge";
import AutoStartCountdown from "../components/AutoStartCountdown";
import StartingSessionOverlay from "../components/StartingSessionOverlay";
import { ArrowLeft, ArrowRight, Camera, Check, Alert, Lightbulb } from "../components/Icons";
import { sessionService } from "../services/sessionService";
import { useSessionFlow } from "../session";
import { useWebcam } from "../hooks/useWebcam";
import { useMediaPipePose } from "../hooks/useMediaPipePose";
import { useAutoStartGate } from "../hooks/useAutoStartGate";
import {
  computeFullBodyQuality,
  areHeadAndFeetVisible,
  FULL_BODY_QUALITY_THRESHOLD,
} from "../utils/captureQuality";
import cameraReadySound from "../assets/sound effect/Camera all good effect.mp3";

/** How long the full body must be detected continuously before the session auto-starts. 1.8s */
const AUTO_START_STABLE_MS = 1800;

/** Derive the required camera view from exercise code. */
function getViewGuidance(exerciseCode: string | null): "side" | "front" {
  if (exerciseCode?.includes("single_leg")) return "front";
  return "side"; // sit_to_stand and weight_bearing_lunge default to side
}

type ChecklistStatus = "done" | "pending" | "info";
interface ChecklistItem {
  id: string;
  label: string;
  status: ChecklistStatus;
}

/** Which guidance banner to show when the full body isn't detected yet. */
type GuidanceKey = "noBody" | "partial" | "lowQuality" | null;

export default function CameraSetup() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const { mode, exerciseCode, setSessionId } = useSessionFlow();
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState("");
  const [hasAutoStarted, setHasAutoStarted] = useState(false);
  const [frozenQuality, setFrozenQuality] = useState(0);
  const [demoOpen, setDemoOpen] = useState(false);

  // Real webcam + pose
  const { videoRef, setVideoRef, ready: webcamReady, error: webcamError } = useWebcam();
  const { landmarks, ready: poseReady, fps } = useMediaPipePose(videoRef, webcamReady);

  // Full-body capture quality (head, torso, legs, feet) — stricter than the live-session badge.
  const hasLandmarks = !!landmarks && landmarks.length > 0;
  const bodyQuality = computeFullBodyQuality(landmarks ?? []);
  const isFullBodyReady = bodyQuality >= FULL_BODY_QUALITY_THRESHOLD;
  const headFeetVisible = areHeadAndFeetVisible(landmarks ?? []);

  const viewGuidance = getViewGuidance(exerciseCode);

  const guidanceText =
    viewGuidance === "front"
      ? "This exercise needs a front view. Face the camera directly so both knees and hips are clearly visible."
      : "This exercise needs a side view. Place your camera to your side so your knee and hip are clearly visible.";

  // Log FPS once pose model is ready
  useEffect(() => {
    if (poseReady) console.log(`[CameraSetup] Pose model ready — FPS: ${fps}`);
  }, [poseReady, fps]);

  // Guards duplicate session starts from the manual button and the auto-start gate racing each other.
  const startedRef = useRef(false);

  const beginSession = async () => {
    if (startedRef.current) return;
    startedRef.current = true;
    setFrozenQuality(bodyQuality);
    setHasAutoStarted(true);

    if (!exerciseCode) {
      setError(t("camera.selectExerciseFirst"));
      startedRef.current = false;
      setHasAutoStarted(false);
      return;
    }

    setError("");
    setStarting(true);
    try {
      const response = await sessionService.start({
        mode,
        exercise_code: exerciseCode,
        device_info: navigator.userAgent,
      });
      setSessionId(response.session_id);
      nav("/live");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("camera.startError"));
      startedRef.current = false;
      setHasAutoStarted(false);
    } finally {
      setStarting(false);
    }
  };

  // Auto-start once the full body has been detected continuously for AUTO_START_STABLE_MS.
  // Note: intentionally does NOT gate on `exerciseCode` — the countdown UI below only depends
  // on `isFullBodyReady`, so gating the timer on exerciseCode too would let the countdown look
  // "ready" while silently never firing if exerciseCode was lost (e.g. a page reload). Instead
  // we always let the timer run, and beginSession() itself reports a clear error if the
  // exercise is missing.
  const autoStartEnabled = webcamReady && poseReady && !hasAutoStarted;
  const { progress: autoStartProgress, active: autoStartActive } = useAutoStartGate(
    bodyQuality,
    FULL_BODY_QUALITY_THRESHOLD,
    AUTO_START_STABLE_MS,
    autoStartEnabled,
    beginSession,
  );

  // Play the "camera all good" sound exactly on the not-ready → ready transition.
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const wasReadyRef = useRef(false);
  useEffect(() => {
    if (isFullBodyReady && !wasReadyRef.current) {
      if (!audioRef.current) audioRef.current = new Audio(cameraReadySound);
      audioRef.current.currentTime = 0;
      audioRef.current.play().catch(() => {
        // Autoplay can be blocked before any user gesture — non-critical, ignore.
      });
    }
    wasReadyRef.current = isFullBodyReady;
  }, [isFullBodyReady]);

  // Large, actionable banner explaining what's missing (only once camera + pose model are up).
  const guidanceKey: GuidanceKey =
    !webcamReady || !poseReady || isFullBodyReady
      ? null
      : !hasLandmarks
        ? "noBody"
        : !headFeetVisible
          ? "partial"
          : "lowQuality";

  const bannerText =
    guidanceKey === "noBody"
      ? t("camera.bannerNoBody")
      : guidanceKey === "partial"
        ? t("camera.bannerPartial")
        : guidanceKey === "lowQuality"
          ? t("camera.bannerLowQuality")
          : null;

  // Applied as inline style (not a conditional className) so it never touches the
  // `.reveal` element's class attribute — doing so would wipe out the `.in` class
  // that useReveal's IntersectionObserver adds imperatively, hiding the video forever.
  const stageBorderStyle: React.CSSProperties | undefined =
    !webcamReady || !poseReady
      ? undefined
      : isFullBodyReady
        ? { borderColor: "var(--good)", boxShadow: "0 0 0 4px var(--good-bg)" }
        : {
            borderColor: "var(--coral)",
            boxShadow: "0 0 0 4px color-mix(in srgb, var(--coral) 16%, transparent)",
          };

  const checklistItems: ChecklistItem[] = [
    {
      id: "permission",
      label: t("camera.checklistPermission"),
      status: webcamReady && !webcamError ? "done" : "pending",
    },
    {
      id: "fullBody",
      label: t("camera.checklistFullBody"),
      status: isFullBodyReady ? "done" : "pending",
    },
    {
      id: "headFeet",
      label: t("camera.checklistHeadFeet"),
      status: headFeetVisible ? "done" : "pending",
    },
    { id: "lighting", label: t("camera.checklistLighting"), status: "info" },
    { id: "space", label: t("camera.checklistSpace"), status: "info" },
  ];

  const autoStartSecondsLeft = Math.max(
    1,
    Math.ceil(((1 - autoStartProgress) * AUTO_START_STABLE_MS) / 1000),
  );

  return (
    <>
      {hasAutoStarted && <StartingSessionOverlay bodyQuality={frozenQuality} />}
      <Link className="back-link" to={`/exercise?mode=${mode}`}>
        <ArrowLeft />
        {t("common.back")}
      </Link>
      <DashTopbar title={t("camera.title")} subtitle={t("camera.desc")} />
      <div className="cam-grid">
        <div className="stack" style={{ gap: 14 }}>
          <div className="cam-stage reveal" style={stageBorderStyle}>
            <CaptureQualityBadge quality={bodyQuality} label={t("camera.quality")} />
            <PoseCanvas
              videoRef={videoRef}
              setVideoRef={setVideoRef}
              landmarks={landmarks}
              webcamReady={webcamReady}
              webcamError={webcamError}
            />
            {/* Corner frame decoration */}
            <div className="cam-frame">
              <span
                className="cam-corner"
                style={{ top: -2, left: -2, borderRight: "none", borderBottom: "none" }}
              />
              <span
                className="cam-corner"
                style={{ top: -2, right: -2, borderLeft: "none", borderBottom: "none" }}
              />
              <span
                className="cam-corner"
                style={{ bottom: -2, left: -2, borderRight: "none", borderTop: "none" }}
              />
              <span
                className="cam-corner"
                style={{ bottom: -2, right: -2, borderLeft: "none", borderTop: "none" }}
              />
            </div>
          </div>

          {bannerText && (
            <div className="setup-banner" role="status">
              <Alert width={24} height={24} />
              <span>{bannerText}</span>
            </div>
          )}

          {!hasAutoStarted && autoStartActive && (
            <AutoStartCountdown
              progress={autoStartProgress}
              secondsLeft={autoStartSecondsLeft}
              label={t("camera.autoStarting")}
            />
          )}
        </div>

        <div className="stack" style={{ gap: 18 }}>
          <div className="panel reveal">
            <div className="panel-head" style={{ marginBottom: 16 }}>
              <div>
                <h3>{t("camera.checklist")}</h3>
              </div>
            </div>
            <div className="check-list">
              {checklistItems.map((item) => (
                <div className={`cl-row cl-row--${item.status}`} key={item.id}>
                  <span className={`cl-ic cl-ic--${item.status}`}>
                    {item.status === "done" && <Check width={16} height={16} />}
                    {item.status === "pending" && <Alert width={16} height={16} />}
                    {item.status === "info" && <Lightbulb width={16} height={16} />}
                  </span>
                  {item.label}
                </div>
              ))}
            </div>
          </div>

          <div className="panel reveal">
            <div className="panel-head" style={{ marginBottom: 12 }}>
              <div>
                <h3>{t("camera.guidanceTitle")}</h3>
              </div>
              <span
                className="mi"
                style={{
                  width: 38,
                  height: 38,
                  borderRadius: 10,
                  display: "grid",
                  placeItems: "center",
                  background: "var(--good-bg)",
                  color: "var(--accent-text)",
                }}
              >
                <Camera width={19} height={19} />
              </span>
            </div>
            <p style={{ color: "var(--text-2)", fontSize: "0.94rem" }}>{guidanceText}</p>
          </div>

          {exerciseCode === "sit_to_stand" && (
            <div className="panel reveal">
              <div className="panel-head" style={{ marginBottom: demoOpen ? 14 : 0 }}>
                <div>
                  <h3>{t("camera.demoTitle")}</h3>
                </div>
                <button
                  className="btn btn-ghost"
                  style={{ padding: "6px 12px", fontSize: "0.85rem" }}
                  onClick={() => setDemoOpen((o) => !o)}
                >
                  {demoOpen ? "▲" : "▶"}
                </button>
              </div>
              {demoOpen && (
                <video
                  src={stsDemoSrc}
                  controls
                  playsInline
                  style={{ width: "100%", borderRadius: "var(--r-md)", display: "block" }}
                />
              )}
            </div>
          )}

          {error && (
            <p className="muted" style={{ color: "var(--coral)" }}>
              {error}
            </p>
          )}

          <button
            className="btn btn-primary btn-lg btn-block reveal"
            onClick={beginSession}
            disabled={starting || hasAutoStarted}
          >
            {starting ? t("common.loading") : t("camera.startSession")}
            <ArrowRight />
          </button>
        </div>
      </div>
    </>
  );
}
