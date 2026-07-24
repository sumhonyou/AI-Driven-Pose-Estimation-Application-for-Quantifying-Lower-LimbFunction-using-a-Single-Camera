import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useState, useEffect, useRef } from "react";
import { DashTopbar } from "../layouts/DashboardLayout";
import PoseCanvas from "../components/PoseCanvas";
import CaptureQualityBadge from "../components/CaptureQualityBadge";
import AutoStartCountdown from "../components/AutoStartCountdown";
import StartingSessionOverlay from "../components/StartingSessionOverlay";
import { ArrowLeft, ArrowRight, Check, Alert, Lightbulb, Info } from "../components/Icons";
import { sessionService, enqueueCancel } from "../services/sessionService";
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

/** How long the full body must be detected continuously before the session
 * auto-starts. UAT remediation (Stage R5): raised from 1.8s to a standard 5s across
 * every start protocol in the app — 1.8s didn't give users enough time to read the
 * checklist/guidance before the session took over. */
const AUTO_START_STABLE_MS = 5000;

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
  const { mode, exerciseCode, sessionId, setSessionId, setReminderId } = useSessionFlow();
  const [error, setError] = useState("");
  const [hasAutoStarted, setHasAutoStarted] = useState(false);
  const [frozenQuality, setFrozenQuality] = useState(0);

  // Real webcam + pose
  const { videoRef, setVideoRef, ready: webcamReady, error: webcamError } = useWebcam();
  // Stop the (CPU-heavy, per-frame) pose detection loop the instant the session has
  // started — otherwise it keeps competing with the in-flight session-start request
  // for the main thread, making navigation to the live page feel stuck/delayed.
  const {
    landmarks,
    ready: poseReady,
    fps,
    stopDetection,
  } = useMediaPipePose(videoRef, webcamReady && !hasAutoStarted);

  // Full-body capture quality (head, torso, legs, feet) — stricter than the live-session badge.
  const hasLandmarks = !!landmarks && landmarks.length > 0;
  const bodyQuality = computeFullBodyQuality(landmarks ?? []);
  const isFullBodyReady = bodyQuality >= FULL_BODY_QUALITY_THRESHOLD;
  const headFeetVisible = areHeadAndFeetVisible(landmarks ?? []);

  const isSls = !!exerciseCode?.includes("single_leg");
  // Exact match only: Module A's "weight_bearing_lunge_test" and Module B exercise
  // codes could collide on a loose substring check, so this stays exact.
  const isWblt = exerciseCode === "weight_bearing_lunge_test";
  const isSquat = exerciseCode === "squat";

  // Log FPS once pose model is ready
  useEffect(() => {
    if (poseReady) console.log(`[CameraSetup] Pose model ready — FPS: ${fps}`);
  }, [poseReady, fps]);

  // Guards duplicate session starts from the manual button and the auto-start gate racing each other.
  const startedRef = useRef(false);

  // Stop pose before leaving so Back is not blocked by CPU detectForVideo.
  const handleBack = () => {
    stopDetection();
    if (sessionId) {
      enqueueCancel(sessionId);
      setSessionId(null);
    }
    // Stage R13 (UAT): abandoning here (before the live page even mounts)
    // must not let a leftover reminderId auto-tick that reminder on some
    // later, unrelated session -- see session.tsx's doc comment.
    setReminderId(null);
    // UAT remediation (Stage R9): Instructions now sits between Exercise Selection
    // and Camera Setup in the flow, so Back returns one step, not two.
    console.log("[CameraSetup] Back navigating");
    nav("/instructions");
  };

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
    try {
      const response = await sessionService.start({
        mode,
        exercise_code: exerciseCode,
        device_info: navigator.userAgent,
      });
      setSessionId(response.session_id);
      nav(isSls ? "/sls/live" : isWblt ? "/wblt/live" : isSquat ? "/squat/live" : "/sts/live");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("camera.startError"));
      startedRef.current = false;
      setHasAutoStarted(false);
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
    { id: "noOcclusion", label: t("camera.checklistNoOcclusion"), status: "info" },
  ];

  const autoStartSecondsLeft = Math.max(
    1,
    Math.ceil(((1 - autoStartProgress) * AUTO_START_STABLE_MS) / 1000),
  );

  return (
    <>
      {hasAutoStarted && <StartingSessionOverlay bodyQuality={frozenQuality} />}
      <button type="button" className="back-link" onClick={handleBack}>
        <ArrowLeft />
        {t("common.back")}
      </button>
      <DashTopbar title={t("camera.title")} subtitle={t("camera.desc")} />
      <div className="cam-grid">
        <div className="stack" style={{ gap: 14 }}>
          <div className="cam-stage" style={stageBorderStyle}>
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

          {/* UAT remediation: HY's ask (2026-07-24) -- the instruction was easy to
              miss buried in the muted "Getting ready" panel on the right; moved
              directly under the webcam frame with a high-contrast light-blue "info"
              card (icon sized to roughly match 2 lines of text) so it's impossible
              to miss while adjusting position. */}
          <div className="cam-instruction-card">
            <Info />
            <span>{t("camera.autoStartWaiting")}</span>
          </div>

          {/* TEMP DEV BUTTON — added 2026-07-24 at HY's request purely to speed up
              manual QA while developing (skip waiting for the 5s auto-start gate).
              Kept in the left column, below the instruction card, so a screenshot of
              the right column ("Before you start" / "Getting ready") never includes
              it. The real flow never needs a manual button, since beginSession()
              already fires from useAutoStartGate above. REMOVE THIS BUTTON before
              final submission/handoff. */}
          <button
            type="button"
            className="btn btn-primary btn-lg btn-block"
            onClick={beginSession}
            disabled={hasAutoStarted}
          >
            {t("camera.startSession")}
            <ArrowRight />
          </button>
        </div>

        <div className="stack" style={{ gap: 14 }}>
          <div className="panel">
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

          {/* UAT remediation: replaces the removed view-guidance/demo panels and
              manual Start button — the moved framing banner and the auto-start
              countdown now live here, in the same slot. `cam-status-panel` grows to
              fill the column so its bottom edge lines up with the instruction card
              under the video (HY's request). */}
          <div className="panel cam-status-panel">
            <div className="panel-head" style={{ marginBottom: 14 }}>
              <div>
                <h3>{t("camera.statusTitle")}</h3>
              </div>
            </div>
            {bannerText ? (
              <div className="setup-banner" role="status">
                <Alert width={24} height={24} />
                <span>{bannerText}</span>
              </div>
            ) : (
              !hasAutoStarted &&
              autoStartActive && (
                <AutoStartCountdown
                  progress={autoStartProgress}
                  secondsLeft={autoStartSecondsLeft}
                  label={t("camera.autoStarting")}
                />
              )
            )}
          </div>

          {error && (
            <p className="muted" style={{ color: "var(--coral)" }}>
              {error}
            </p>
          )}
        </div>
      </div>
    </>
  );
}
