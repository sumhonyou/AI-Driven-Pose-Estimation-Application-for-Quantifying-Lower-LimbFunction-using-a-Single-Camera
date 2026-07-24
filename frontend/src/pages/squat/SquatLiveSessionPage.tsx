// Squat live session. The user picks a rep target and the set auto-finishes once that
// many reps have COUNTED; the whole buffered set is then posted to
// POST /api/module-b/analyze, and the backend re-segments and grades it server-side.
//
// A rep only counts if it clears the three fault gates (squatFaultGates.ts, a port of
// backend squat/fault_gates.py). A rejected rep is called out immediately with its
// reason and does not advance the target, so the user corrects and repeats -- but it is
// still recorded, still sent, and still graded, so the report stays honest about
// everything attempted. The live counter remains a UX estimate; the backend's response
// is the only persisted, official result.
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import PoseCanvas from "../../components/PoseCanvas";
import CaptureQualityBadge from "../../components/CaptureQualityBadge";
import ExerciseDemoOverlay from "../../components/ExerciseDemoOverlay";
import GeneratingReportOverlay from "../../components/GeneratingReportOverlay";
import LiveCueOverlay from "../../components/LiveCueOverlay";
import AudioCueToggle from "../../components/AudioCueToggle";
import StartSetCountdown from "../../components/squat/StartSetCountdown";
import SquatTargetPromptModal from "../../components/squat/SquatTargetPromptModal";
import { Close, Check, Alert, Play } from "../../components/Icons";
import { sessionService, enqueueCancel } from "../../services/sessionService";
import { moduleBService } from "../../services/moduleBService";
import { useSessionFlow } from "../../session";
import { useWebcam } from "../../hooks/useWebcam";
import { useMediaPipePose } from "../../hooks/useMediaPipePose";
import { useSessionRecorder } from "../../hooks/useSessionRecorder";
import { useSpeechCues } from "../../hooks/useSpeechCues";
import { computeFrameQuality } from "../../utils/captureQuality";
import {
  createSquatLiveEstimator,
  depthZoneFor,
  fetchSquatLiveConfig,
  FALLBACK_SQUAT_LIVE_CONFIG,
  type SquatBandEstimate,
  type SquatLiveConfig,
} from "../../utils/squat/squatLiveEstimate";
import type { SquatFaultTag } from "../../utils/squat/squatFaultGates";
import goodRepSrc from "../../assets/sound effect/Rep correct sound effect.mp3";
import wrongRepSrc from "../../assets/sound effect/Wrong sound effect.mp3";

type Stage = "setup" | "countdown" | "recording" | "posting";

const COUNTDOWN_START_SEC = 5;

// UAT remediation (Stage R4): the big pop-out cue shows only the PRIMARY reason (one
// cue at a time, per the plan) — this is the fixed priority order when a rep trips
// more than one gate, matching the order the sidebar's fuller list is already built
// in (squat/fault_gates.py evaluates depth -> lean -> heel_rise per rep).
const CUE_TITLE_KEY: Record<SquatFaultTag, string> = {
  insufficient_depth: "squat.cueInsufficientDepth",
  excessive_forward_lean: "squat.cueExcessiveForwardLean",
  heel_lift: "squat.cueHeelLift",
};

// Smaller, specific subheading under the big title — insufficient_depth's is
// interpolated with the live config's actual threshold ({{deg}}) rather than a
// hardcoded number, so it can never drift from what the gate is really checking.
const CUE_SUBHEADING_KEY: Record<SquatFaultTag, string> = {
  insufficient_depth: "squat.cueInsufficientDepthDetail",
  excessive_forward_lean: "squat.cueExcessiveForwardLeanDetail",
  heel_lift: "squat.cueHeelLiftDetail",
};

interface LiveCue {
  title: string;
  subheading?: string;
  tone: "warn" | "good";
}

/** Rep-target choices. The target drives the session: reaching it auto-finishes the set.
 * Stage 5.20 also sends it with the analyze call so the report can show what was aimed
 * for; it is stored on the session row but still never influences segmentation or
 * grading — the backend derives those from the frames alone. */
const TARGET_OPTIONS = [10, 20, 30, 40, 50, 60, 70, 80];

/** Hard ceiling on total attempts, as a multiple of the target.
 *
 * A rep that trips a fault gate does not count, so a user who cannot clear a gate would
 * otherwise be asked to repeat forever. The depth gate in particular is a CLINICAL floor
 * (78.04°), not a threshold learned from this cohort, so someone with restricted mobility
 * may genuinely never pass it. The set finishes at this cap regardless, and "Finish Set"
 * stays available at all times (rules.md #3, #18). */
const ATTEMPT_CAP_MULTIPLIER = 2;

/** How long without a meaningful flexion change counts as "no movement". */
const INACTIVITY_TIMEOUT_MS = 9000;
/** Minimum frame-to-frame flexion change (deg) that counts as motion. */
const MOTION_EPSILON_DEG = 2;

export default function SquatLiveSessionPage() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const { mode, sessionId, setSessionId } = useSessionFlow();

  const [stage, setStage] = useState<Stage>("setup");
  const [targetReps, setTargetReps] = useState<number | null>(null);
  const [repCount, setRepCount] = useState(0);
  const [attemptCount, setAttemptCount] = useState(0);
  // Stage 5.21: why the MOST RECENT rep didn't count, or [] if the most recent event
  // was a counted rep (or none has happened yet). Deliberately persistent -- this is
  // what the live-feedback panel reads to decide idle/counted/rejected, and it changes
  // only on the next rep, never on a timer (HY's call: never blank, always show the
  // last verdict).
  const [rejectedGates, setRejectedGates] = useState<SquatFaultTag[]>([]);
  // UAT remediation (Stage R4): the transient full-viewport corrective-cue pop-out,
  // shown on top of (not instead of) the persistent sidebar panel below. null hides
  // it. Replacing it (rather than queueing) is the throttle — at most one cue shows
  // at a time, and a new one simply restarts LiveCueOverlay's own countdown.
  const [liveCue, setLiveCue] = useState<LiveCue | null>(null);
  const [sec, setSec] = useState(0);
  const [error, setError] = useState("");
  const [showInactivityPrompt, setShowInactivityPrompt] = useState(false);
  const [countdownSeconds, setCountdownSeconds] = useState(COUNTDOWN_START_SEC);
  const countdownTimerRef = useRef<number | null>(null);

  // Live angle readouts — display only, mirroring squatLiveEstimate.ts's estimator
  // state so the panel can show exactly what the FSM is currently tracking.
  const [kneeFlexionDeg, setKneeFlexionDeg] = useState(0);
  const [trunkLeanDeg, setTrunkLeanDeg] = useState(0);
  const [repPeakFlexionDeg, setRepPeakFlexionDeg] = useState<number | null>(null);
  const [lastRepPeakDeg, setLastRepPeakDeg] = useState<number | null>(null);
  const [lastRepPeakTrunkLeanDeg, setLastRepPeakTrunkLeanDeg] = useState<number | null>(null);
  const [lastRepBand, setLastRepBand] = useState<SquatBandEstimate>(null);
  // Live thresholds for the depth gauge's zone boundaries — state (not a ref) so
  // the gauge re-renders once the real backend config arrives (X7).
  const [liveConfig, setLiveConfig] = useState<SquatLiveConfig>(FALLBACK_SQUAT_LIVE_CONFIG);

  const { videoRef, setVideoRef, ready: webcamReady, error: webcamError } = useWebcam();
  const { landmarks, worldLandmarks, stopDetection } = useMediaPipePose(videoRef, webcamReady);
  const recorder = useSessionRecorder();
  const speech = useSpeechCues();
  const captureQuality = computeFrameQuality(landmarks ?? []);

  const estimatorRef = useRef(createSquatLiveEstimator());
  const finishingRef = useRef(false);
  const lastMotionMsRef = useRef(0);
  const previousFlexionRef = useRef(0);
  const hasAutoFinishedRef = useRef(false);
  const goodRepAudio = useRef(new Audio(goodRepSrc));
  const wrongRepAudio = useRef(new Audio(wrongRepSrc));
  // Last *rendered* (rounded) angle values — guards the per-frame setState calls
  // below so a frame whose rounded display value hasn't changed never re-renders.
  // Without this, ~30-60 setState calls/sec on 3 state variables can cascade into
  // React's "Maximum update depth exceeded" safety trip.
  const lastRenderedKneeDegRef = useRef(0);
  const lastRenderedTrunkLeanDegRef = useRef(0);
  const lastRenderedRepPeakDegRef = useRef<number | null>(null);

  // Fetch live thresholds once so the on-screen rep/band estimate matches the
  // backend's official squat config (X7 -- local constants are fallback only).
  useEffect(() => {
    fetchSquatLiveConfig().then((config) => {
      setLiveConfig(config);
      estimatorRef.current = createSquatLiveEstimator(config);
    });
  }, []);

  function startSet() {
    estimatorRef.current = createSquatLiveEstimator(liveConfig);
    recorder.start();
    speech.speakSession("squat_start", t("live.speakStarting"));
    setRepCount(0);
    setSec(0);
    setShowInactivityPrompt(false);
    setAttemptCount(0);
    setRejectedGates([]);
    setLiveCue(null);
    hasAutoFinishedRef.current = false;
    lastMotionMsRef.current = performance.now();
    setKneeFlexionDeg(0);
    setTrunkLeanDeg(0);
    setRepPeakFlexionDeg(null);
    lastRenderedKneeDegRef.current = 0;
    lastRenderedTrunkLeanDegRef.current = 0;
    lastRenderedRepPeakDegRef.current = null;
    setLastRepPeakDeg(null);
    setLastRepPeakTrunkLeanDeg(null);
    setLastRepBand(null);
    setStage("recording");
  }

  // "Start Set" begins a 5s full-page countdown (gives the user time to step back and
  // get their whole body in frame) before recording/rep tracking actually starts —
  // avoids the estimator misreading the user's approach to position as a squat rep.
  function beginCountdown() {
    setCountdownSeconds(COUNTDOWN_START_SEC);
    setStage("countdown");
  }

  function cancelCountdown() {
    if (countdownTimerRef.current != null) {
      window.clearInterval(countdownTimerRef.current);
      countdownTimerRef.current = null;
    }
    setStage("setup");
  }

  useEffect(() => {
    if (stage !== "countdown") return;
    countdownTimerRef.current = window.setInterval(() => {
      setCountdownSeconds((prev) => {
        if (prev <= 1) {
          if (countdownTimerRef.current != null) {
            window.clearInterval(countdownTimerRef.current);
            countdownTimerRef.current = null;
          }
          startSet();
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
  }, [stage]);

  // Buffer frames + run the live rep estimator only while recording. Paused
  // while a prompt is open: walking up to dismiss it (e.g. approaching the
  // camera after "Hit your goal!") flexes the knees enough to look like a
  // squat to the threshold-based estimator, so nothing is recorded or fed to
  // it until the user is actually back to exercising.
  useEffect(() => {
    if (!landmarks || stage !== "recording" || showInactivityPrompt) {
      return;
    }
    const now = performance.now();
    recorder.record(
      { timestampMs: now, landmarks, worldLandmarks: worldLandmarks ?? [] },
      captureQuality,
    );
    if (worldLandmarks) {
      const update = estimatorRef.current.update(worldLandmarks, now);
      if (Math.abs(update.currentFlexionDeg - previousFlexionRef.current) > MOTION_EPSILON_DEG) {
        lastMotionMsRef.current = now;
      }
      previousFlexionRef.current = update.currentFlexionDeg;

      const roundedKnee = Math.round(update.currentFlexionDeg);
      if (roundedKnee !== lastRenderedKneeDegRef.current) {
        lastRenderedKneeDegRef.current = roundedKnee;
        setKneeFlexionDeg(update.currentFlexionDeg);
      }
      const roundedTrunkLean = Math.round(update.currentTrunkLeanDeg);
      if (roundedTrunkLean !== lastRenderedTrunkLeanDegRef.current) {
        lastRenderedTrunkLeanDegRef.current = roundedTrunkLean;
        setTrunkLeanDeg(update.currentTrunkLeanDeg);
      }
      const roundedRepPeak =
        update.currentRepPeakFlexionDeg != null
          ? Math.round(update.currentRepPeakFlexionDeg)
          : null;
      if (roundedRepPeak !== lastRenderedRepPeakDegRef.current) {
        lastRenderedRepPeakDegRef.current = roundedRepPeak;
        setRepPeakFlexionDeg(update.currentRepPeakFlexionDeg);
      }

      if (update.repJustCompleted || update.repJustRejected) {
        setRepCount(update.repCount);
        setAttemptCount(update.attemptCount);
        setLastRepPeakDeg(update.lastRepPeakDeg);
        setLastRepPeakTrunkLeanDeg(update.lastRepPeakTrunkLeanDeg);
        setLastRepBand(update.lastRepBandEstimate);
      }
      if (update.repJustCompleted) {
        setRejectedGates([]);
        // HY's refinement: a good rep immediately closes any corrective cue still on
        // screen from an earlier rejected rep, rather than leaving a stale "Go deeper"
        // up after the user has already corrected and completed a valid rep.
        setLiveCue(null);
        goodRepAudio.current.currentTime = 0;
        goodRepAudio.current.play().catch(() => {});
      } else if (update.repJustRejected) {
        console.log("[SquatLiveSessionPage] Rep rejected:", update.lastRepFailedGates);
        setRejectedGates(update.lastRepFailedGates);
        wrongRepAudio.current.currentTime = 0;
        wrongRepAudio.current.play().catch(() => {});
        // UAT remediation (Stage R4): the big corrective pop-out shows only the
        // PRIMARY reason, title + a specific subheading (e.g. "Go deeper" / "Aim for
        // at least 78° knee bend") — the full list of every failed gate stays in the
        // persistent sidebar panel below, so it isn't repeated here.
        const primaryTag = update.lastRepFailedGates[0];
        if (primaryTag) {
          setLiveCue({
            title: t(CUE_TITLE_KEY[primaryTag] as never),
            subheading:
              primaryTag === "insufficient_depth"
                ? t(CUE_SUBHEADING_KEY[primaryTag] as never, {
                    deg: Math.round(liveConfig.faultGates.minKneeFlexPeakDeg),
                  })
                : t(CUE_SUBHEADING_KEY[primaryTag] as never),
            tone: "warn",
          });
        }
        // UAT remediation (Stage R6, HY's call): unlike the VISUAL pop-out above
        // (primary reason only), the SPOKEN cue reads out EVERY failed gate for this
        // rep, in the same fixed priority order -- a rep that trips two gates at once
        // gets both said aloud, one after another (SpeechCueQueue sequences them).
        for (const tag of update.lastRepFailedGates) {
          speech.speakFault(tag, t(CUE_TITLE_KEY[tag] as never));
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [landmarks, stage, showInactivityPrompt]);

  // Session timer.
  useEffect(() => {
    if (stage !== "recording") return;
    const id = window.setInterval(() => setSec((s) => s + 1), 1000);
    return () => window.clearInterval(id);
  }, [stage]);

  // Inactivity safety net: never auto-submits, only prompts.
  useEffect(() => {
    if (stage !== "recording" || repCount < 1 || showInactivityPrompt) return;
    const id = window.setInterval(() => {
      if (performance.now() - lastMotionMsRef.current >= INACTIVITY_TIMEOUT_MS) {
        setShowInactivityPrompt(true);
      }
    }, 1000);
    return () => window.clearInterval(id);
  }, [stage, repCount, showInactivityPrompt]);

  // Auto-finish: the target now controls the session, so "10 reps" yields exactly 10
  // counted reps. Also finishes at the attempt cap, so a user who cannot clear a fault
  // gate is never left repeating indefinitely (see ATTEMPT_CAP_MULTIPLIER).
  useEffect(() => {
    if (stage !== "recording" || !targetReps || hasAutoFinishedRef.current) return;
    const hitTarget = repCount >= targetReps;
    const hitCap = attemptCount >= targetReps * ATTEMPT_CAP_MULTIPLIER;
    if (hitTarget || hitCap) {
      hasAutoFinishedRef.current = true;
      console.log(
        `[SquatLiveSessionPage] Auto-finishing — ${hitTarget ? "target reached" : "attempt cap reached"} ` +
          `(counted ${repCount}/${targetReps}, attempts ${attemptCount})`,
      );
      void finishSet();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [repCount, attemptCount, targetReps, stage]);

  function dismissInactivityPrompt() {
    lastMotionMsRef.current = performance.now();
    setShowInactivityPrompt(false);
  }

  async function finishSet() {
    if (finishingRef.current || !sessionId) return;
    finishingRef.current = true;
    setShowInactivityPrompt(false);
    setLiveCue(null);
    setStage("posting");
    try {
      const { frames, score, validFrameRatio } = recorder.summary();
      await moduleBService.analyze(sessionId, "squat", frames, targetReps);
      await sessionService.end(sessionId, {
        capture_quality: score,
        valid_frame_ratio: validFrameRatio,
      });
      speech.speakSession("squat_end", t("live.speakSessionComplete"));
      nav(`/report?session=${sessionId}`);
    } catch (err) {
      console.error("[SquatLiveSessionPage] Finish set failed", err);
      setError(err instanceof Error ? err.message : t("live.endError"));
      finishingRef.current = false;
      setStage("recording");
    }
  }

  function handleCancel() {
    if (finishingRef.current) return;
    finishingRef.current = true;
    speech.stop();
    stopDetection();
    if (sessionId) enqueueCancel(sessionId);
    setSessionId(null);
    console.log("[SquatLiveSessionPage] Cancel navigating");
    nav(`/exercise?mode=${mode}`);
  }

  if (!sessionId) {
    return <p className="muted">{t("live.noSession")}</p>;
  }

  const mm = String(Math.floor(sec / 60)).padStart(2, "0");
  const ss = String(sec % 60).padStart(2, "0");
  const pct = targetReps
    ? Math.min(100, (repCount / targetReps) * 100)
    : Math.min(100, repCount * 10);

  const currentZone = depthZoneFor(kneeFlexionDeg, liveConfig);

  // Stage 5.21: the promoted live-feedback panel's state, derived rather than tracked
  // separately -- `rejectedGates` already holds exactly "the reasons for the most
  // recent rejection, or none" (see its declaration above), so no new state needed.
  const feedbackKind: "idle" | "counted" | "rejected" =
    attemptCount === 0 ? "idle" : rejectedGates.length > 0 ? "rejected" : "counted";

  return (
    <>
      {stage === "posting" && <GeneratingReportOverlay />}
      {/* UAT remediation (Stage R9): popup overlay instead of a sidebar panel --
          the webcam feed and HUD underneath keep their exact layout whether this is
          open or closed. Clicking Start Set in the modal goes straight into the
          countdown, same as WBLT's Start Attempt. */}
      {stage === "setup" && (
        <SquatTargetPromptModal
          targetReps={targetReps}
          targetOptions={TARGET_OPTIONS}
          onChangeTarget={setTargetReps}
          onStart={beginCountdown}
        />
      )}
      {stage === "countdown" && (
        <StartSetCountdown secondsLeft={countdownSeconds} onCancel={cancelCountdown} />
      )}
      {stage === "recording" && liveCue && (
        <LiveCueOverlay
          title={liveCue.title}
          subheading={liveCue.subheading}
          tone={liveCue.tone}
          onDismiss={() => setLiveCue(null)}
        />
      )}
      {showInactivityPrompt &&
        createPortal(
          <div className="sls-modal-overlay" role="dialog" aria-modal="true">
            <div className="sls-modal-card">
              <h3>{t("squat.inactivityTitle")}</h3>
              <p className="muted">{t("squat.inactivityBody")}</p>
              <div className="sls-modal-actions">
                <button className="btn btn-ghost btn-block" onClick={dismissInactivityPrompt}>
                  {t("squat.continueSet")}
                </button>
                <button className="btn btn-primary btn-block" onClick={() => void finishSet()}>
                  {t("squat.finishSet")}
                </button>
              </div>
            </div>
          </div>,
          document.body,
        )}
      <div className="topbar">
        <div>
          <h1>{t("squat.reportTitle")}</h1>
          <p>{t("squat.livePrompt")}</p>
        </div>
        <div className="topbar-actions">
          <AudioCueToggle />
          {/* HY's refinement: Finish Set moved up here, beside Cancel, now that the
              "Live status" panel that used to hold it is gone during recording. */}
          {stage === "recording" && (
            <button className="btn btn-primary" onClick={() => void finishSet()}>
              {t("squat.finishSet")}
            </button>
          )}
          <button className="btn btn-cancel" onClick={handleCancel}>
            <Close />
            {t("live.cancel")}
          </button>
        </div>
      </div>
      {error && (
        <p className="muted" style={{ color: "var(--coral)", marginBottom: 18 }}>
          {error}
        </p>
      )}

      <div className="cam-grid">
        {/* Recording border via inline style (not a conditional className) so React
            never rewrites the class attribute and wipes the `.in` that useReveal
            adds — same bug class as STS/SLS/CameraSetup. */}
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
          <ExerciseDemoOverlay kind="squat" />
          <PoseCanvas
            videoRef={videoRef}
            setVideoRef={setVideoRef}
            landmarks={landmarks}
            webcamReady={webcamReady}
            webcamError={webcamError}
          />
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
              {/* Stage 5.21: the shared `live.reps` LABEL is untouched (used by
                  STS/SLS/WBLT too) -- only this page's rendered VALUE changes, via a
                  squat-scoped key, to show progress toward a target when one is set. */}
              <div className="hl2">{t("live.reps")}</div>
              <div className="hv">
                {targetReps
                  ? t("squat.repsOfTargetValue", { rep: repCount, target: targetReps })
                  : repCount}
              </div>
              {/* HY's refinement: progress now lives inside the Reps card itself
                  (dropped the separate "Live status" panel below) -- only meaningful
                  with a target set, so it stays hidden without one. */}
              {stage === "recording" && targetReps && (
                <div className="track hud-progress">
                  <div
                    className="fill good"
                    style={{ width: pct + "%", transition: "width .5s var(--ease)" }}
                  />
                </div>
              )}
            </div>
          </div>

          {/* Stage 5.21: promoted directly under the HUD, replacing the deleted
              "Rep 5 of 10" status box -- corrective/positive feedback is the single
              most important thing to read while exercising at a distance from the
              screen. Persistent (see `feedbackKind`'s derivation above): it shows the
              LAST rep's verdict until the next one, never blanking on a timer. */}
          {stage === "recording" && (
            <div className={"live-feedback-panel " + feedbackKind} role="status" aria-live="polite">
              {feedbackKind === "idle" && (
                <div className="live-feedback-head">
                  <span className="live-feedback-icon">
                    <Play width={20} height={20} />
                  </span>
                  <span className="live-feedback-title">{t("squat.startFirstRep")}</span>
                </div>
              )}
              {feedbackKind === "counted" && (
                <>
                  <div className="live-feedback-head">
                    <span className="live-feedback-icon">
                      <Check width={22} height={22} />
                    </span>
                    <span className="live-feedback-title">{t("squat.repCountedTitle")}</span>
                  </div>
                  {lastRepPeakDeg != null && (
                    <p className="live-feedback-detail">
                      {t("squat.repCountedDetail", { deg: Math.round(lastRepPeakDeg) })}
                    </p>
                  )}
                </>
              )}
              {feedbackKind === "rejected" && (
                <>
                  <div className="live-feedback-head">
                    <span className="live-feedback-icon">
                      <Alert width={20} height={20} />
                    </span>
                    <span className="live-feedback-title">{t("squat.repDidNotCount")}</span>
                  </div>
                  <ul className="live-feedback-reasons">
                    {rejectedGates.map((tag) => (
                      <li key={tag}>{t(("moduleB.tag_" + tag) as never, { defaultValue: tag })}</li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          )}

          {stage === "recording" && (
            <div className="panel">
              <div className="panel-head" style={{ marginBottom: 10 }}>
                <h3>{t("squat.liveAnglesTitle")}</h3>
              </div>

              {/* HY's refinement: one compact row of minimalist numbers instead of the
                  gauge bar + ticks + two separate cards, so the whole live page (camera
                  + HUD + feedback + angles) fits on screen without scrolling. */}
              <div className="live-angle-row">
                <div className="live-angle-stat">
                  <span className="live-angle-label">{t("squat.kneeDepthLabel")}</span>
                  <span className="live-angle-value">
                    {Math.round(kneeFlexionDeg)}°
                    <span className="depth-gauge-zone-chip">
                      {t("squat.depthZone_" + currentZone)}
                    </span>
                  </span>
                </div>
                {repPeakFlexionDeg != null && (
                  <div className="live-angle-stat">
                    <span className="live-angle-label">{t("squat.repPeakLabel")}</span>
                    <span className="live-angle-value">{Math.round(repPeakFlexionDeg)}°</span>
                  </div>
                )}
                <div className="live-angle-stat">
                  <span className="live-angle-label">{t("squat.trunkLeanLabel")}</span>
                  <span className="live-angle-value">{Math.round(trunkLeanDeg)}°</span>
                </div>
                <div className="live-angle-stat">
                  <span className="live-angle-label">{t("squat.lastRepDepthLabel")}</span>
                  <span className="live-angle-value">
                    {lastRepPeakDeg != null ? `${Math.round(lastRepPeakDeg)}°` : "—"}
                    {lastRepBand && (
                      <span className={"band " + lastRepBand.toLowerCase()}>
                        {t("common." + lastRepBand.toLowerCase())}
                      </span>
                    )}
                  </span>
                </div>
              </div>

              <p className="muted" style={{ fontSize: "0.7rem", marginTop: 8 }}>
                {t("squat.liveAngleGuidanceNote")}
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
