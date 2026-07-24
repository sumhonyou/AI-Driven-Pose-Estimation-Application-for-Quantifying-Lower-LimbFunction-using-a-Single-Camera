import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import PoseCanvas from "../../components/PoseCanvas";
import CaptureQualityBadge from "../../components/CaptureQualityBadge";
import ExerciseDemoOverlay from "../../components/ExerciseDemoOverlay";
import GeneratingReportOverlay from "../../components/GeneratingReportOverlay";
import LiveCueOverlay from "../../components/LiveCueOverlay";
import GetReadyCountdown from "../../components/GetReadyCountdown";
import AudioCueToggle from "../../components/AudioCueToggle";
import { Close } from "../../components/Icons";
import { sessionService, enqueueCancel } from "../../services/sessionService";
import { reminderService } from "../../services/reminderService";
import { useSessionFlow } from "../../session";
import { useWebcam } from "../../hooks/useWebcam";
import { useMediaPipePose } from "../../hooks/useMediaPipePose";
import { computeFrameQuality } from "../../utils/captureQuality";
import { useSessionRecorder } from "../../hooks/useSessionRecorder";
import { useSpeechCues } from "../../hooks/useSpeechCues";
import { moduleAService } from "../../services/moduleAService";
import { createStsLiveEstimator } from "../../utils/sts/stsLiveEstimate";
import { humanizeLabel } from "../../utils/format";
import {
  SAMPLE_FPS,
  STS_TARGET_REPS,
  MAX_SESSION_SECONDS,
  LIVE_KNEE_STAND_ENTER,
  LIVE_KNEE_SIT_ENTER,
  LIVE_MIN_VISIBILITY,
} from "../../config/moduleAThresholds";
import type { PoseFrame } from "../../types/pose";
import type { StsPhase, InvalidReasonCode } from "../../utils/sts/stsLiveEstimate";
import goodRepSrc from "../../assets/sound effect/Rep correct sound effect.mp3";
import wrongRepSrc from "../../assets/sound effect/Wrong sound effect.mp3";

const FAIL_REASON_DISPLAY_MS = 3500;
// UAT remediation (Stage R5): STS previously auto-recorded on mount with no
// countdown at all -- the most under-reported instruction/legibility issue in UAT.
// Standardised on the same 5s "get ready" countdown every other exercise uses.
const COUNTDOWN_START_SEC = 5;

function reasonCodeToI18nKey(code: InvalidReasonCode): string {
  switch (code) {
    case "low_visibility":
      return "live.reasonLowVisibilityRep";
    case "too_unstable":
      return "live.reasonTooUnstable";
    case "incomplete":
      return "live.reasonNotFullStand";
  }
}

export default function StsLiveSessionPage() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const { mode, exerciseCode, sessionId, setSessionId, reminderId, setReminderId } =
    useSessionFlow();
  const isSts = exerciseCode === "sit_to_stand";

  // UAT remediation (Stage R5): "countdown" is the 5s get-ready window, only entering
  // "recording" (and therefore actually buffering frames / running the estimator)
  // once it completes -- mirrors squat/SLS/WBLT's stage machine.
  const [stage, setStage] = useState<"countdown" | "recording">("countdown");
  const [countdownSecondsLeft, setCountdownSecondsLeft] = useState(COUNTDOWN_START_SEC);
  const countdownTimerRef = useRef<number | null>(null);

  const [sec, setSec] = useState(0);
  // Attempted: every concluded rep-boundary the client's FSM detects. Valid: only
  // ever set from the backend's authoritative recount — never guessed client-side.
  const [attemptedReps, setAttemptedReps] = useState(0);
  const [validReps, setValidReps] = useState(0);
  // Mirrors `validReps` but read/written synchronously within runAnalyzeCheck so a
  // chained (coalesced) call in the same tick never compares against a stale closure.
  const validRepsRef = useRef(0);
  const [running, setRunning] = useState(true);
  const [generatingReport, setGeneratingReport] = useState(false);

  // Live Sit-to-Stand guidance (knee angle + why a rep wasn't counted) — display only.
  const [kneeAngle, setKneeAngle] = useState(0);
  const [minKneeAngle, setMinKneeAngle] = useState<number | null>(null);
  const [phase, setPhase] = useState<StsPhase>("sitting");
  // Optimistic client guess, shown instantly and reconciled once the backend responds.
  const [liveReasonGuess, setLiveReasonGuess] = useState<string | null>(null);
  const failReasonTimeoutRef = useRef<number | null>(null);
  // UAT remediation (Stage R4): the transient full-viewport corrective-cue pop-out,
  // shown alongside (not instead of) the persistent "live band" panel below -- same
  // pattern as squat/SLS. null hides it; a new rejection replaces it outright.
  const [liveCue, setLiveCue] = useState<{ title: string; tone: "warn" } | null>(null);

  // Guards against triggering the completion/navigation flow (or a cancel) more than once.
  const finishingRef = useRef(false);
  // Ensures only one analyze() call is in flight at a time; a boundary that fires
  // while one is pending just queues the latest frame buffer instead of overlapping.
  const checkInFlightRef = useRef(false);
  const pendingCheckRef = useRef<{
    frames: PoseFrame[];
    attempted: number;
    forceFinalize: boolean;
  } | null>(null);
  const timeoutTriggeredRef = useRef(false);

  // Real webcam + pose
  const { videoRef, setVideoRef, ready: webcamReady, error: webcamError } = useWebcam();
  const { landmarks, worldLandmarks, stopDetection } = useMediaPipePose(videoRef, webcamReady);

  // Live rep-boundary detector (UX only) — the authoritative count comes back from
  // POST /analyze, called once per boundary below.
  const liveEstimator = useRef(createStsLiveEstimator());

  // Sound effects — preloaded once
  const goodRepAudio = useRef(new Audio(goodRepSrc));
  const wrongRepAudio = useRef(new Audio(wrongRepSrc));

  // Live quality from landmarks
  const captureQuality = computeFrameQuality(landmarks ?? []);
  const lowVisibility = isSts && captureQuality < LIVE_MIN_VISIBILITY;

  // Session quality recorder — buffers frames for Module A and provides summary metrics
  const recorder = useSessionRecorder();
  const recorderStarted = useRef(false);
  const speech = useSpeechCues();

  // UAT remediation (Stage R5): recording (and therefore the recorder) now starts
  // only once the get-ready countdown below completes, not on mount.
  function startRecording() {
    if (!recorderStarted.current) {
      recorder.start();
      recorderStarted.current = true;
      console.log("[LiveSession] Session recorder started");
    }
    speech.speakSession("sts_start", t("live.speakStarting"));
    setStage("recording");
  }

  // 5s get-ready countdown, run once on mount — CameraSetup already confirmed the
  // full body is visible before navigating here, so this is purely the "settle into
  // position" window, same as squat/SLS/WBLT's post-button countdown.
  useEffect(() => {
    countdownTimerRef.current = window.setInterval(() => {
      setCountdownSecondsLeft((prev) => {
        if (prev <= 1) {
          if (countdownTimerRef.current != null) {
            window.clearInterval(countdownTimerRef.current);
            countdownTimerRef.current = null;
          }
          startRecording();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => {
      if (countdownTimerRef.current != null) {
        window.clearInterval(countdownTimerRef.current);
        countdownTimerRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Downsamples the buffered frames to SAMPLE_FPS so the analyze request stays a reasonable size.
  function sampleFrames(frames: PoseFrame[]): PoseFrame[] {
    if (frames.length === 0) return frames;
    const minGapMs = 1000 / SAMPLE_FPS;
    const sampled: PoseFrame[] = [frames[0]];
    let lastTs = frames[0].timestampMs;
    for (const frame of frames.slice(1)) {
      if (frame.timestampMs - lastTs >= minGapMs) {
        sampled.push(frame);
        lastTs = frame.timestampMs;
      }
    }
    return sampled;
  }

  // Runs a progress check against the backend: called once per rep-boundary, and
  // once (forced) on the 60s timeout. The backend decides whether to persist —
  // once its own recount reaches target (or forceFinalize is set), the response
  // carries persisted:true and this navigates straight to the report. No separate
  // "final" call is ever needed for the common path.
  async function runAnalyzeCheck(frames: PoseFrame[], attempted: number, forceFinalize: boolean) {
    if (!sessionId || finishingRef.current) return;
    if (checkInFlightRef.current) {
      pendingCheckRef.current = { frames, attempted, forceFinalize };
      return;
    }
    checkInFlightRef.current = true;
    try {
      const sampled = sampleFrames(frames);
      const response = await moduleAService.analyze(sessionId, "sit_to_stand", sampled, {
        clientAttemptedReps: attempted,
        forceFinalize,
      });
      if (finishingRef.current) return;

      if (response.metrics.rep_count > validRepsRef.current) {
        setLiveReasonGuess(null);
        setLiveCue(null);
        goodRepAudio.current.currentTime = 0;
        goodRepAudio.current.play().catch(() => {});
      }
      validRepsRef.current = response.metrics.rep_count;
      setValidReps(response.metrics.rep_count);

      if (response.persisted) {
        finishingRef.current = true;
        setRunning(false);
        setGeneratingReport(true);
        try {
          const { score, validFrameRatio } = recorder.summary();
          await sessionService.end(sessionId, {
            capture_quality: score,
            valid_frame_ratio: validFrameRatio,
          });
        } catch (err) {
          console.error("[LiveSession] sessionService.end failed (non-blocking)", err);
        }
        // Stage R13 (UAT): scoped to the reminder that launched THIS session.
        reminderService.completeIfLaunched(reminderId);
        setReminderId(null);
        speech.speakSession("sts_end", t("live.speakSessionComplete"));
        nav(`/report?session=${sessionId}`);
      }
    } catch (err) {
      console.error("[LiveSession] Progress check failed (non-blocking)", err);
    } finally {
      checkInFlightRef.current = false;
      const pending = pendingCheckRef.current;
      pendingCheckRef.current = null;
      if (pending) void runAnalyzeCheck(pending.frames, pending.attempted, pending.forceFinalize);
    }
  }

  // Record each frame when we have landmarks, run the rep-boundary FSM, and play sounds.
  // Gated on stage === "recording" (Stage R5) -- nothing is buffered or estimated
  // during the get-ready countdown.
  useEffect(() => {
    if (landmarks && stage === "recording") {
      const now = performance.now();
      recorder.record(
        { timestampMs: now, landmarks, worldLandmarks: worldLandmarks ?? [] },
        captureQuality,
      );
      if (worldLandmarks && isSts && !finishingRef.current) {
        const update = liveEstimator.current.update(worldLandmarks, now, captureQuality);
        setAttemptedReps(update.attemptedRepCount);
        setKneeAngle(update.kneeAngleDeg);
        setMinKneeAngle(update.minKneeAngleDeg);
        setPhase(update.phase);
        if (update.event === "rep_boundary") {
          if (update.reasonCode) {
            wrongRepAudio.current.currentTime = 0;
            wrongRepAudio.current.play().catch(() => {});
            const reasonText = t(reasonCodeToI18nKey(update.reasonCode));
            setLiveReasonGuess(reasonText);
            setLiveCue({ title: reasonText, tone: "warn" });
            speech.speakFault(update.reasonCode, reasonText);
            if (failReasonTimeoutRef.current) window.clearTimeout(failReasonTimeoutRef.current);
            failReasonTimeoutRef.current = window.setTimeout(
              () => setLiveReasonGuess(null),
              FAIL_REASON_DISPLAY_MS,
            );
          }
          const { frames } = recorder.summary();
          void runAnalyzeCheck(frames, update.attemptedRepCount, false);
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [landmarks, stage]);

  // Session timer — stops immediately once the session is finishing or cancelled, and
  // (Stage R5) doesn't start ticking until recording actually begins.
  useEffect(() => {
    if (!running || stage !== "recording") return;
    const id = setInterval(() => setSec((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, [running, stage]);

  // A session that never reaches STS_TARGET_REPS valid reps must still end
  // eventually — force-finalize once, persisting whatever was captured.
  useEffect(() => {
    if (
      isSts &&
      sec >= MAX_SESSION_SECONDS &&
      validReps < STS_TARGET_REPS &&
      !finishingRef.current &&
      !timeoutTriggeredRef.current
    ) {
      timeoutTriggeredRef.current = true;
      const { frames } = recorder.summary();
      void runAnalyzeCheck(frames, attemptedReps, true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sec, isSts, validReps]);

  const mm = String(Math.floor(sec / 60)).padStart(2, "0");
  const ss = String(sec % 60).padStart(2, "0");
  const pct = (validReps / STS_TARGET_REPS) * 100;

  // Cancel: stop pose first (frees main thread), enqueue cancel, then navigate.
  const handleCancel = () => {
    if (finishingRef.current) return;
    finishingRef.current = true;
    setRunning(false);
    speech.stop();
    stopDetection();
    if (sessionId) enqueueCancel(sessionId);
    setSessionId(null);
    setReminderId(null);
    console.log("[LiveSession] Cancel navigating");
    nav(`/exercise?mode=${mode}`);
  };

  const liveTitle = exerciseCode ? humanizeLabel(exerciseCode) : t("landing.s2sName");

  let liveMessage = t("common.good");
  let liveToneClass = "band-good";
  if (isSts) {
    if (lowVisibility) {
      liveMessage = t("live.reasonLowVisibility");
      liveToneClass = "band-warn";
    } else if (liveReasonGuess) {
      liveMessage = liveReasonGuess;
      liveToneClass = "band-warn";
    } else if (validReps === 0 && attemptedReps === 0) {
      liveMessage = t("live.waitingMovement");
      liveToneClass = "band-neutral";
    } else if (validReps >= STS_TARGET_REPS) {
      liveMessage = t("live.allComplete");
      liveToneClass = "band-good";
    } else {
      liveMessage = t("live.repsCountedMsg");
      liveToneClass = "band-good";
    }
  }
  const liveDotColor =
    liveToneClass === "band-warn"
      ? "var(--coral)"
      : liveToneClass === "band-neutral"
        ? "var(--text-3)"
        : "var(--good)";

  const kneeTargetText = () => {
    if (phase === "sitting") return t("live.kneeTargetStand", { deg: LIVE_KNEE_STAND_ENTER });
    if (phase === "rising") return t("live.kneeTargetRising", { deg: LIVE_KNEE_STAND_ENTER });
    return t("live.kneeTargetSit", { deg: LIVE_KNEE_SIT_ENTER });
  };
  const deepEnough = minKneeAngle != null && minKneeAngle <= LIVE_KNEE_SIT_ENTER;
  const notCountedCount = attemptedReps - validReps;

  return (
    <>
      {generatingReport && <GeneratingReportOverlay />}
      {stage === "countdown" && (
        <GetReadyCountdown
          secondsLeft={countdownSecondsLeft}
          eyebrow={liveTitle}
          caption={t("live.getReadyCaption")}
          onCancel={handleCancel}
        />
      )}
      {running && liveCue && (
        <LiveCueOverlay
          title={liveCue.title}
          tone={liveCue.tone}
          onDismiss={() => setLiveCue(null)}
        />
      )}
      <div className="topbar">
        <div>
          <h1>{liveTitle}</h1>
          <p>{t("common." + (mode === "rehab" ? "rehab" : "functional"))}</p>
        </div>
        <div className="topbar-actions">
          <AudioCueToggle />
          <button className="btn btn-cancel" onClick={handleCancel}>
            <Close />
            {t("live.cancel")}
          </button>
        </div>
      </div>
      <div className="cam-grid">
        {/* Recording border via inline style (not a conditional className) so React
            never rewrites the class attribute and wipes the `.in` that useReveal
            adds — same bug class CameraSetup documents. */}
        <div
          className="cam-stage reveal"
          style={
            stage === "recording"
              ? {
                  borderColor: "var(--coral)",
                  boxShadow: "0 0 0 4px color-mix(in srgb, var(--coral) 18%, transparent)",
                }
              : undefined
          }
        >
          <CaptureQualityBadge quality={captureQuality} label={t("live.quality")} />
          <ExerciseDemoOverlay kind="sts" />
          <PoseCanvas
            videoRef={videoRef}
            setVideoRef={setVideoRef}
            landmarks={landmarks}
            webcamReady={webcamReady}
            webcamError={webcamError}
          />
          <div
            style={{
              position: "absolute",
              bottom: 16,
              left: 0,
              right: 0,
              textAlign: "center",
              color: "var(--text-3)",
              fontSize: "0.84rem",
            }}
          >
            {t("live.cue")}
          </div>
        </div>

        <div className="stack" style={{ gap: 18 }}>
          <div className="live-hud">
            <div className="hud-card reveal">
              <div className="hl2">{t("live.timer")}</div>
              <div className="hv">
                {mm}:{ss}
              </div>
            </div>
            <div className="hud-card reveal">
              <div className="hl2">{t("live.reps")}</div>
              {/* Match squat: show counted / target in the value, with progress under it. */}
              <div className="hv">
                {t("live.repsOfTargetValue", { rep: validReps, target: STS_TARGET_REPS })}
              </div>
              {stage === "recording" && (
                <div className="track hud-progress">
                  <div
                    className="fill good"
                    style={{ width: pct + "%", transition: "width .5s var(--ease)" }}
                  />
                </div>
              )}
            </div>
          </div>

          <div className="panel reveal">
            <div className="panel-head" style={{ marginBottom: 18 }}>
              <div>
                <h3>{t("live.liveBand")}</h3>
              </div>
            </div>
            <div className={"live-band " + liveToneClass} style={{ marginBottom: 18 }}>
              <span
                className="dot"
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: "50%",
                  background: liveDotColor,
                  display: "inline-block",
                }}
              />
              {liveMessage}
            </div>
            <p className="muted" style={{ fontSize: "0.84rem", marginTop: 10 }}>
              {t("live.validRepsStatus", { valid: validReps, target: STS_TARGET_REPS })}
            </p>
            {notCountedCount > 0 && (
              <p className="muted" style={{ fontSize: "0.82rem", marginTop: 4 }}>
                {t("live.repsNotCountedStatus", { count: notCountedCount })}
              </p>
            )}
            {validReps < STS_TARGET_REPS && (
              <p className="muted" style={{ fontSize: "0.82rem", marginTop: 4 }}>
                {t("live.oneMoreRepPrompt")}
              </p>
            )}

            {isSts && (
              <>
                <div className="knee-metrics">
                  <div className="knee-metric-card">
                    <div>
                      <span className="knee-metric-label">{t("live.currentKneeAngle")}</span>
                      <strong>{Math.round(kneeAngle)}°</strong>
                    </div>
                  </div>
                  <div className="knee-metric-card">
                    <div>
                      <span className="knee-metric-label">{t("live.lowestKneeAngle")}</span>
                      <strong>{minKneeAngle != null ? `${Math.round(minKneeAngle)}°` : "—"}</strong>
                    </div>
                  </div>
                </div>
                <p className="muted" style={{ fontSize: "0.82rem", marginTop: 12 }}>
                  {kneeTargetText()}
                  {phase === "standing" && (
                    <>
                      {" "}
                      —{" "}
                      <span style={{ color: deepEnough ? "var(--good)" : "var(--text-3)" }}>
                        {deepEnough ? t("live.kneeStatusDeep") : t("live.kneeStatusShallow")}
                      </span>
                    </>
                  )}
                </p>
                <p className="muted" style={{ fontSize: "0.74rem", marginTop: 6 }}>
                  {t("live.kneeGuidanceNote")}
                </p>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
