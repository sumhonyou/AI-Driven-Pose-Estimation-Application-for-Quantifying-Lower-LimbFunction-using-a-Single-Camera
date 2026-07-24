// Weight-Bearing Lunge Test live session — Stage 2 (guided bracket, both legs, symmetry).
// Per leg: LOADING (fetch bracket target) -> SETUP -> POSITIONING (quality-gated hold,
// waits until the tested leg + hips are stably visible) -> GET_READY (fixed 5s countdown
// to get into the lunge stance) -> CALIBRATING (fixed 2s "stand still, foot flat" — the
// heel-lift baseline is captured here) -> RECORDING (fixed 10s lunge hold; a confirmed
// heel lift ends it immediately) -> SELF_REPORT_TOUCH (full-page modal) -> posting ->
// ATTEMPT_RESULT (more attempts left) or LEG_RESULT (leg complete). After the last leg:
// SESSION_RESULT (symmetry + both legs) -> finish.
//
// Live feedback (heel-down indicator, angle gauge) is computed entirely
// client-side via wbltGeometry.ts for instant response — it is a helper only.
// The backend's POST response is always the authoritative, persisted result,
// including the next bracket target (never computed client-side).
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import PoseCanvas from "../../components/PoseCanvas";
import CaptureQualityBadge from "../../components/CaptureQualityBadge";
import ExerciseDemoOverlay from "../../components/ExerciseDemoOverlay";
import GeneratingReportOverlay from "../../components/GeneratingReportOverlay";
import AudioCueToggle from "../../components/AudioCueToggle";
import { Close } from "../../components/Icons";
import { sessionService, enqueueCancel } from "../../services/sessionService";
import { reminderService } from "../../services/reminderService";
import {
  wbltApi,
  type WbltAttemptResult,
  type WbltLeg,
  type WbltSessionSummary,
} from "../../services/wblt/wbltApi";
import {
  createWbltLiveTracker,
  type WbltHeelLiftConfig,
  type WbltLiveUpdate,
} from "../../services/wblt/wbltGeometry";
import { useSessionFlow } from "../../session";
import { useReveal } from "../../useReveal";
import { useWebcam } from "../../hooks/useWebcam";
import { useMediaPipePose } from "../../hooks/useMediaPipePose";
import { useSessionRecorder } from "../../hooks/useSessionRecorder";
import { useAutoStartGate } from "../../hooks/useAutoStartGate";
import { useSpeechCues } from "../../hooks/useSpeechCues";
import {
  computeFrameQuality,
  computeWbltLegQuality,
  isWbltLegVisible,
  areWbltHipsVisible,
  WBLT_READY_QUALITY_THRESHOLD,
} from "../../utils/captureQuality";
import WbltTouchSelfReportModal from "../../components/wblt/WbltTouchSelfReportModal";
import WbltGetReadyCountdown from "../../components/wblt/WbltGetReadyCountdown";
import WbltAttemptResultOverlay from "../../components/wblt/WbltAttemptResultOverlay";
import WbltTargetPromptModal from "../../components/wblt/WbltTargetPromptModal";

type Stage =
  | "loading"
  | "setup"
  | "positioning"
  | "get_ready"
  | "calibrating"
  | "recording"
  | "self_report"
  | "posting"
  | "attempt_result"
  | "leg_result"
  | "session_result";

// Positioning phase requires knee/ankle/heel/foot_index of the tested leg + both hips
// to stay visible for this long before moving on to the get-ready countdown — mirrors
// the backend's own per-frame validity gate instead of a blind fixed timer, so an
// attempt can never start on a frame the backend would have rejected anyway.
const WBLT_POSITION_STABLE_MS = 1500;
// Fixed countdown once framing is confirmed stable, giving the user a predictable
// moment to settle into the lunge stance before recording actually starts. UAT
// remediation (Stage R5): standardised to the same 5s every other exercise's
// get-ready countdown uses (was 10s).
const WBLT_GET_READY_DURATION_SEC = 5;
// "Stand still, foot flat" window at the very start of recording. The heel-lift
// baseline is captured here, so it MUST match backend CALIBRATION_SECONDS — a
// mismatch would let lunge frames poison the neutral baseline (see config.py).
const WBLT_CALIBRATION_DURATION_SEC = 2;
// After calibration, the user holds the lunge for this long — the attempt then
// auto-completes and moves to the touch self-report, no manual "done" click needed.
const WBLT_RECORDING_DURATION_SEC = 10;
const DEFAULT_LEG_ORDER: WbltLeg[] = ["right", "left"];
const DEFAULT_ATTEMPTS_PER_LEG = 3;

const IDLE_UPDATE: WbltLiveUpdate = { calibrated: false, heelLifted: false, thetaDeg: null };

export default function WbltLiveSessionPage() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const { mode, sessionId, setSessionId, reminderId, setReminderId } = useSessionFlow();

  const [legOrder, setLegOrder] = useState<WbltLeg[]>(DEFAULT_LEG_ORDER);
  const [attemptsPerLeg, setAttemptsPerLeg] = useState(DEFAULT_ATTEMPTS_PER_LEG);
  const heelLiftConfigRef = useRef<WbltHeelLiftConfig | undefined>(undefined);
  const [legIndex, setLegIndex] = useState(0);
  const leg = legOrder[legIndex] ?? "right";

  const [stage, setStage] = useState<Stage>("loading");
  const [attemptNumber, setAttemptNumber] = useState(1);
  const [targetDistanceCm, setTargetDistanceCm] = useState<number | null>(null);
  const [liveUpdate, setLiveUpdate] = useState<WbltLiveUpdate>(IDLE_UPDATE);
  const [lastResult, setLastResult] = useState<WbltAttemptResult | null>(null);
  const [sessionSummary, setSessionSummary] = useState<WbltSessionSummary | null>(null);
  const [error, setError] = useState("");
  const [recordingSecondsLeft, setRecordingSecondsLeft] = useState(WBLT_RECORDING_DURATION_SEC);
  const recordingTimerRef = useRef<number | null>(null);
  const [getReadySecondsLeft, setGetReadySecondsLeft] = useState(WBLT_GET_READY_DURATION_SEC);
  const getReadyTimerRef = useRef<number | null>(null);
  const [calibrationSecondsLeft, setCalibrationSecondsLeft] = useState(
    WBLT_CALIBRATION_DURATION_SEC,
  );
  const calibrationTimerRef = useRef<number | null>(null);
  // Display-only countdown length, synced to the fetched config once it lands (see
  // the config-fetch effect below); the tracker's actual calibration boundary is
  // frame-timestamp-driven and doesn't depend on this value at all.
  const calibrationDisplaySecRef = useRef(WBLT_CALIBRATION_DURATION_SEC);

  const { videoRef, setVideoRef, ready: webcamReady, error: webcamError } = useWebcam();
  const { landmarks, worldLandmarks, stopDetection } = useMediaPipePose(videoRef, webcamReady);
  const recorder = useSessionRecorder();
  const speech = useSpeechCues();
  const trackerRef = useRef(createWbltLiveTracker(leg));
  const busyRef = useRef(false);
  const qualitySamplesRef = useRef<{ score: number; validFrameRatio: number }[]>([]);

  const captureQuality = computeFrameQuality(landmarks ?? []);

  // Re-run reveal when stage panels mount after async bracket fetch (pathname-only
  // useReveal in DashboardLayout misses elements added later).
  useReveal([stage, attemptNumber, targetDistanceCm, lastResult, sessionSummary]);

  // Fetch bracket/attempts_per_leg config once, then load the first leg's target.
  useEffect(() => {
    if (!sessionId) return;
    const cancelled = false;
    wbltApi
      .config()
      .then((cfg) => {
        if (cancelled) return;
        setLegOrder(cfg.leg_order);
        setAttemptsPerLeg(cfg.attempts_per_leg);
        heelLiftConfigRef.current = {
          calibrationSeconds: cfg.calibration_seconds,
          heelMinCalibrationFrames: cfg.heel_min_calibration_frames,
          heelLiftTolRatio: cfg.heel_lift_tol_ratio,
          heelLiftHysteresisRatio: cfg.heel_lift_hysteresis_ratio,
          heelLiftDebounceFrames: cfg.heel_lift_debounce_frames,
        };
        // Keep the visible "Calibrating" countdown in step with the ACTUAL frame-
        // timestamp boundary the tracker now enforces internally (see
        // wbltGeometry.ts) — purely cosmetic, but a mismatched display duration
        // would be confusing even though it can no longer cause a detection bug.
        calibrationDisplaySecRef.current = Math.round(cfg.calibration_seconds);
      })
      .catch(() => {
        // Non-fatal: falls back to DEFAULT_LEG_ORDER/DEFAULT_ATTEMPTS_PER_LEG.
      });
  }, [sessionId]);

  async function loadBracket(targetLeg: WbltLeg) {
    if (!sessionId) return;
    setStage("loading");
    setError("");
    try {
      const bracket = await wbltApi.bracket(sessionId, targetLeg);
      setAttemptNumber(bracket.attempt_number);
      setTargetDistanceCm(bracket.next_target_distance_cm);
      setStage("setup");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("camera.startError"));
    }
  }

  useEffect(() => {
    if (!sessionId) return;
    queueMicrotask(() => void loadBracket(leg));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, leg]);

  // Start buffering + a fresh tracker for the "stand still, foot flat" calibration
  // window. The heel-lift baseline is captured from these neutral-stance frames.
  function startCalibration() {
    trackerRef.current = createWbltLiveTracker(leg, heelLiftConfigRef.current);
    recorder.start();
    setLiveUpdate(IDLE_UPDATE);
    setError("");
    setCalibrationSecondsLeft(calibrationDisplaySecRef.current);
    setStage("calibrating");
  }

  // Calibration window has ended — lock the live tracker's baseline NOW (not on
  // some later frame count), so heel-lift detection is live from the very first
  // frame of the hold instead of lagging in on a slow/low-fps camera. Mirrors the
  // backend's own finalize-at-window-boundary (analysis.py). Recording keeps
  // buffering into the SAME recorder (calibration + hold posted together; the
  // backend splits them by timestamp against CALIBRATION_SECONDS).
  function startHold() {
    trackerRef.current.finalizeCalibration();
    setRecordingSecondsLeft(WBLT_RECORDING_DURATION_SEC);
    // UAT remediation (Stage R6): announces the exact instruction the user needs at
    // this instant -- reuses the same "lunge now" text already shown on screen
    // (wblt.lungeNow) so the spoken and visual cues can never drift apart.
    speech.speakSession("wblt_lunge_start", t("wblt.lungeNow"));
    setStage("recording");
  }

  function beginPositioning() {
    setError("");
    setStage("positioning");
  }

  function beginGetReady() {
    setGetReadySecondsLeft(WBLT_GET_READY_DURATION_SEC);
    setStage("get_ready");
  }

  function cancelGetReady() {
    if (getReadyTimerRef.current != null) {
      window.clearInterval(getReadyTimerRef.current);
      getReadyTimerRef.current = null;
    }
    setStage("setup");
  }

  // Positioning phase: gate the move to the get-ready countdown on live landmark
  // quality instead of a blind timer, so the backend's calibration window never opens
  // on a frame where the tested leg or hips aren't actually visible yet (the root
  // cause of attempts silently getting flagged low-confidence).
  const positionEnabled = stage === "positioning";
  const legQuality = positionEnabled ? computeWbltLegQuality(landmarks ?? [], leg) : 0;
  const { progress: positionProgress, active: positionActive } = useAutoStartGate(
    legQuality,
    WBLT_READY_QUALITY_THRESHOLD,
    WBLT_POSITION_STABLE_MS,
    positionEnabled,
    beginGetReady,
  );
  const positionSecondsLeft = Math.max(
    1,
    Math.ceil(((1 - positionProgress) * WBLT_POSITION_STABLE_MS) / 1000),
  );

  // Fixed get-ready countdown: once framing is confirmed stable, give the user a
  // predictable few seconds to settle into the lunge stance before recording starts.
  useEffect(() => {
    if (stage !== "get_ready") return;
    getReadyTimerRef.current = window.setInterval(() => {
      setGetReadySecondsLeft((prev) => {
        if (prev <= 1) {
          if (getReadyTimerRef.current != null) {
            window.clearInterval(getReadyTimerRef.current);
            getReadyTimerRef.current = null;
          }
          startCalibration();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => {
      if (getReadyTimerRef.current != null) {
        window.clearInterval(getReadyTimerRef.current);
        getReadyTimerRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stage]);
  const legVisible = isWbltLegVisible(landmarks ?? [], leg);
  const hipsVisible = areWbltHipsVisible(landmarks ?? []);
  // UAT remediation (Stage R9): the old fallback reused the long setupGuidanceSide
  // sentence here; replaced with a short, uniform framing instruction (HY's wording)
  // now that reading distance matters again on the live positioning box. The two
  // "retry_*" messages stay as-is -- already short and specific to their failure.
  const positionGuidance = !landmarks?.length
    ? t("wblt.positionGuidanceShort")
    : !legVisible
      ? t("wblt.warn_retry_leg_visibility")
      : !hipsVisible
        ? t("wblt.warn_retry_lateral_alignment")
        : t("wblt.positioningHold");
  // UAT remediation (Stage R9): this box previously stayed green through every one
  // of the warning states above -- now only the genuine "you're framed, hold still"
  // message is green; everything else (including the real backend `retry_*` fault
  // tags this mirrors) reads amber.
  const positionWarning =
    stage === "positioning" && (!landmarks?.length || !legVisible || !hipsVisible);

  // UAT remediation (Stage R9, HY's question -- "did you include this into audio
  // feedback? I think this is also one of the error tags"): confirmed yes, the
  // backend's warning_tags really does include a `retry_{limiting_factor}` entry
  // for exactly this (analysis.py) -- but nothing spoke it. Edge-detected so it
  // fires once per bad-framing episode, not every frame; SpeechCueQueue's own
  // per-key throttle covers the rest.
  const wasPositionWarningRef = useRef(false);
  useEffect(() => {
    if (stage !== "positioning") {
      wasPositionWarningRef.current = false;
      return;
    }
    if (positionWarning && !wasPositionWarningRef.current) {
      speech.speakFault("wblt_framing", t("wblt.positionGuidanceShort"));
    }
    wasPositionWarningRef.current = positionWarning;
  }, [stage, positionWarning, speech, t]);

  // Buffer frames + run the live tracker across BOTH the calibration window and the
  // lunge hold — the tracker calibrates its baseline during "calibrating", then
  // detects lifts during "recording".
  useEffect(() => {
    if (!landmarks || (stage !== "calibrating" && stage !== "recording")) return;
    const now = performance.now();
    recorder.record(
      { timestampMs: now, landmarks, worldLandmarks: worldLandmarks ?? [] },
      captureQuality,
    );
    if (worldLandmarks) {
      // Seconds, matching how the backend derives t from the posted timestampMs —
      // keeps the live tracker's One Euro Filter dt sequence in step with the
      // backend's recompute (see wbltGeometry.ts's createWbltLiveTracker doc).
      setLiveUpdate(trackerRef.current.update(worldLandmarks, now / 1000));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [landmarks, stage]);

  // Fixed calibration countdown: hold the neutral stance while the baseline is
  // captured, then roll into the lunge hold.
  useEffect(() => {
    if (stage !== "calibrating") return;
    calibrationTimerRef.current = window.setInterval(() => {
      setCalibrationSecondsLeft((prev) => {
        if (prev <= 1) {
          if (calibrationTimerRef.current != null) {
            window.clearInterval(calibrationTimerRef.current);
            calibrationTimerRef.current = null;
          }
          startHold();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => {
      if (calibrationTimerRef.current != null) {
        window.clearInterval(calibrationTimerRef.current);
        calibrationTimerRef.current = null;
      }
    };
  }, [stage]);

  function stopAndAskTouch() {
    setStage("self_report");
  }

  // Recording auto-completes after WBLT_RECORDING_DURATION_SEC of holding the lunge —
  // no manual "done" click needed. Frames buffered before the timer fires are unaffected;
  // the backend only uses heel-down, in-frame frames for the analysis regardless.
  useEffect(() => {
    if (stage !== "recording") return;
    recordingTimerRef.current = window.setInterval(() => {
      setRecordingSecondsLeft((prev) => {
        if (prev <= 1) {
          if (recordingTimerRef.current != null) {
            window.clearInterval(recordingTimerRef.current);
            recordingTimerRef.current = null;
          }
          stopAndAskTouch();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => {
      if (recordingTimerRef.current != null) {
        window.clearInterval(recordingTimerRef.current);
        recordingTimerRef.current = null;
      }
    };
  }, [stage]);

  async function submitTouch(touched: boolean) {
    if (busyRef.current || !sessionId || targetDistanceCm == null) return;
    busyRef.current = true;
    setStage("posting");
    try {
      const { frames, score, validFrameRatio } = recorder.summary();
      qualitySamplesRef.current.push({ score, validFrameRatio });
      const result = await wbltApi.analyze(sessionId, leg, targetDistanceCm, touched, frames);
      setLastResult(result);
      setStage(result.leg_complete ? "leg_result" : "attempt_result");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("camera.startError"));
      setStage("setup");
    } finally {
      busyRef.current = false;
    }
  }

  // Item 3: a confirmed (debounced) heel lift during the hold ends the attempt
  // immediately — no point asking "did you touch?", the camera already knows this
  // attempt is invalid. We still post the buffered frames (touched=false) so the
  // attempt persists and the backend's authoritative recompute records the lift.
  useEffect(() => {
    if (stage !== "recording") return;
    if (!liveUpdate.calibrated || !liveUpdate.heelLifted) return;
    if (recordingTimerRef.current != null) {
      window.clearInterval(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }
    // UAT remediation (Stage R6, HY's note): every fault tag gets spoken, including
    // this one -- fires once since the attempt ends immediately after (no need for
    // edge-detection/throttling like the other pages' sustained faults).
    speech.speakFault("heel_lift", t("wblt.heelLifted"));
    queueMicrotask(() => void submitTouch(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stage, liveUpdate.calibrated, liveUpdate.heelLifted]);

  function nextAttempt() {
    if (!lastResult) return;
    setAttemptNumber(lastResult.attempt_number);
    setTargetDistanceCm(lastResult.next_target_distance_cm);
    setStage("setup");
  }

  // Ends the session (aggregated capture-quality) and navigates to the report.
  // Assumes the caller already holds busyRef — does not manage it itself.
  async function endSessionAndNavigate() {
    if (!sessionId) return;
    const samples = qualitySamplesRef.current;
    const avg = (vals: number[]) =>
      vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
    await sessionService.end(sessionId, {
      capture_quality: avg(samples.map((s) => s.score)),
      valid_frame_ratio: avg(samples.map((s) => s.validFrameRatio)),
    });
    // Stage R13 (UAT): scoped to the reminder that launched THIS session.
    reminderService.completeIfLaunched(reminderId);
    setReminderId(null);
    speech.speakSession("wblt_end", t("live.speakSessionComplete"));
    nav(`/report?session=${sessionId}`);
  }

  async function continueOrFinish() {
    if (!lastResult) return;
    if (legIndex < legOrder.length - 1) {
      setLegIndex((i) => i + 1);
      return;
    }
    if (!sessionId || busyRef.current) return;
    busyRef.current = true;
    setStage("loading");
    try {
      const summary = await wbltApi.session(sessionId);
      setSessionSummary(summary);
      // Both legs are done — go straight to the report instead of an extra
      // "session complete" screen the user has to click through; the loading
      // overlay stays up the whole time so this reads as one continuous transition.
      await endSessionAndNavigate();
    } catch (err) {
      // Something failed on the way to the report (summary fetch or session-end) --
      // fall back to the manual session_result screen so the user isn't stuck on a
      // spinner and can retry via its "Finish test" button.
      setError(err instanceof Error ? err.message : t("camera.startError"));
      setStage("session_result");
    } finally {
      busyRef.current = false;
    }
  }

  async function finishTest() {
    if (!sessionId || busyRef.current) return;
    busyRef.current = true;
    try {
      await endSessionAndNavigate();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("live.endError"));
      busyRef.current = false;
    }
  }

  function handleCancel() {
    if (busyRef.current) return;
    busyRef.current = true;
    speech.stop();
    stopDetection();
    if (sessionId) enqueueCancel(sessionId);
    setSessionId(null);
    setReminderId(null);
    console.log("[WbltLiveSessionPage] Cancel navigating");
    nav(`/exercise?mode=${mode}`);
  }

  if (!sessionId) {
    return <p className="muted">{t("live.noSession")}</p>;
  }

  const legLabel = t(leg === "right" ? "wblt.legRight" : "wblt.legLeft");
  const legPrompt = t(leg === "right" ? "wblt.legPromptRight" : "wblt.legPromptLeft");
  const isBonusAttempt = attemptNumber > attemptsPerLeg;

  const liveMessage =
    stage === "setup"
      ? t("wblt.setupGuidanceLunge")
      : !liveUpdate.calibrated
        ? t("wblt.calibrating")
        : t("wblt.lungeNow");

  const overlaysVisible = stage === "recording";
  const angleDisplay = liveUpdate.thetaDeg != null ? `${liveUpdate.thetaDeg.toFixed(1)}°` : "—";
  const isLastLeg = legIndex === legOrder.length - 1;

  function bandDisplay(band: "Poor" | "Fair" | "Good" | null) {
    return band ? t("common." + band.toLowerCase()) : null;
  }

  return (
    <>
      {(stage === "posting" || stage === "loading") && <GeneratingReportOverlay />}
      {stage === "get_ready" && (
        <WbltGetReadyCountdown
          secondsLeft={getReadySecondsLeft}
          legLabel={legLabel}
          onCancel={cancelGetReady}
        />
      )}
      {stage === "attempt_result" && lastResult && (
        <WbltAttemptResultOverlay result={lastResult} onNext={nextAttempt} />
      )}
      {/* UAT remediation (Stage R9): popup overlay instead of a sidebar panel --
          the webcam feed and HUD underneath keep their exact layout whether this is
          open or closed. */}
      {stage === "setup" && targetDistanceCm != null && (
        <WbltTargetPromptModal targetDistanceCm={targetDistanceCm} onStart={beginPositioning} />
      )}

      <div className="topbar">
        <div>
          <h1>{t("wblt.reportTitle")}</h1>
          <p>{legPrompt}</p>
        </div>
        <div className="topbar-actions">
          <AudioCueToggle />
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
        <div
          className={"cam-stage reveal" + (stage === "recording" ? " cam-stage--recording" : "")}
        >
          <CaptureQualityBadge quality={captureQuality} label={t("live.quality")} />
          <ExerciseDemoOverlay kind="wblt" />
          <PoseCanvas
            videoRef={videoRef}
            setVideoRef={setVideoRef}
            landmarks={landmarks}
            webcamReady={webcamReady}
            webcamError={webcamError}
          />
          {overlaysVisible && (
            <div
              className="hud-card reveal"
              style={{
                position: "absolute",
                top: 16,
                left: 16,
                background: liveUpdate.heelLifted
                  ? "var(--coral-bg, rgba(255,107,107,0.15))"
                  : "var(--good-bg)",
              }}
            >
              <div className="hl2">
                {liveUpdate.heelLifted ? t("wblt.heelLifted") : t("wblt.heelDown")}
              </div>
            </div>
          )}
          {overlaysVisible && (
            <div className="hud-card reveal" style={{ position: "absolute", top: 16, right: 16 }}>
              <div className="hl2">{t("wblt.angleLabel")}</div>
              <div className="hv">{angleDisplay}</div>
            </div>
          )}
        </div>

        <div className="stack" style={{ gap: 18 }}>
          <div className="live-hud">
            <div className="hud-card reveal">
              <div className="hl2">{t("wblt.legLabel")}</div>
              <div className="hv">{legLabel}</div>
            </div>
            {stage !== "leg_result" && stage !== "session_result" && (
              // UAT remediation (Stage R9): redesigned like Squat's Reps HUD card --
              // big value + a progress bar toward attemptsPerLeg, instead of plain text.
              <div className="hud-card reveal">
                <div className="hl2">{t("wblt.attemptLabel")}</div>
                <div className="hv">
                  {isBonusAttempt ? (
                    t("wblt.bonusShort")
                  ) : (
                    <>
                      {attemptNumber}
                      <span style={{ fontSize: "0.9rem", color: "var(--text-3)" }}>
                        {" "}
                        / {attemptsPerLeg}
                      </span>
                    </>
                  )}
                </div>
                {!isBonusAttempt && (
                  <div className="track hud-progress">
                    <div
                      className="fill good"
                      style={{
                        width: Math.min(100, ((attemptNumber - 1) / attemptsPerLeg) * 100) + "%",
                        transition: "width .5s var(--ease)",
                      }}
                    />
                  </div>
                )}
              </div>
            )}
          </div>

          {stage === "positioning" && (
            <div className="panel reveal">
              <div className="panel-head" style={{ marginBottom: 14 }}>
                <h3>{t("wblt.positioningTitle")}</h3>
              </div>
              {positionActive && (
                <div
                  className="hv"
                  style={{
                    fontSize: "3rem",
                    textAlign: "center",
                    color: "var(--accent-text)",
                    marginBottom: 8,
                  }}
                >
                  {positionSecondsLeft}
                </div>
              )}
              <div className={"sls-live-status-box wblt" + (positionWarning ? " warn" : "")}>
                <span className="sls-live-status-text">{positionGuidance}</span>
              </div>
              <button
                className="btn btn-ghost btn-block"
                onClick={() => setStage("setup")}
                style={{ marginTop: 16 }}
              >
                {t("common.back")}
              </button>
            </div>
          )}

          {stage === "calibrating" && (
            <div className="panel reveal">
              <div className="panel-head" style={{ marginBottom: 14 }}>
                <h3>{t("wblt.calibrationTitle")}</h3>
              </div>
              <div
                className="hv"
                style={{
                  fontSize: "3rem",
                  textAlign: "center",
                  color: "var(--accent-text)",
                  marginBottom: 8,
                }}
              >
                {calibrationSecondsLeft}
              </div>
              <div className="sls-live-status-box wblt">
                <span className="sls-live-status-text">{t("wblt.calibrating")}</span>
              </div>
            </div>
          )}

          {stage === "recording" && (
            <div className="panel reveal">
              <div className="panel-head" style={{ marginBottom: 14 }}>
                <h3>{t("live.liveBand")}</h3>
              </div>
              <div
                className="hv"
                style={{
                  fontSize: "3rem",
                  textAlign: "center",
                  color: "var(--accent-text)",
                  marginBottom: 8,
                }}
              >
                {recordingSecondsLeft}
              </div>
              <div className="sls-live-status-box wblt">
                <span className="sls-live-status-text">{liveMessage}</span>
              </div>
            </div>
          )}

          {stage === "self_report" && (
            <WbltTouchSelfReportModal onSelect={(touched) => void submitTouch(touched)} />
          )}

          {stage === "leg_result" && lastResult && (
            <div className="panel reveal">
              <div className="panel-head" style={{ marginBottom: 14 }}>
                <h3>{t("wblt.legCompleteTitle")}</h3>
              </div>
              {lastResult.leg_best_distance_cm != null ? (
                <p>
                  <strong>
                    {t("wblt.legBestDistanceLabel")}: {lastResult.leg_best_distance_cm} cm
                  </strong>
                  {lastResult.leg_band && <> — {bandDisplay(lastResult.leg_band)}</>}
                </p>
              ) : (
                <p className="muted" style={{ color: "var(--coral)" }}>
                  {t("wblt.floorFlagMessage")}
                </p>
              )}
              <p className="muted" style={{ fontSize: "0.85rem", marginTop: 6 }}>
                {t("wblt.angleResultLabel")}:{" "}
                {lastResult.leg_angle_deg != null ? `${lastResult.leg_angle_deg.toFixed(1)}°` : "—"}
              </p>
              <button
                className="btn btn-primary btn-block"
                onClick={() => void continueOrFinish()}
                style={{ marginTop: 18 }}
              >
                {isLastLeg ? t("wblt.viewFinalResults") : t("wblt.continueNextLeg")}
              </button>
            </div>
          )}

          {stage === "session_result" && sessionSummary && (
            <div className="panel reveal">
              <div className="panel-head" style={{ marginBottom: 14 }}>
                <h3>{t("wblt.sessionResultTitle")}</h3>
              </div>
              {legOrder.map((legKey) => {
                const summary = sessionSummary.legs[legKey];
                if (!summary) return null;
                return (
                  <div key={legKey} style={{ marginBottom: 12 }}>
                    <strong>{t(legKey === "right" ? "wblt.legRight" : "wblt.legLeft")}</strong>
                    {summary.best_distance_cm != null ? (
                      <p>
                        {summary.best_distance_cm} cm
                        {summary.band && <> — {bandDisplay(summary.band)}</>} ·{" "}
                        {t("wblt.angleResultLabel")}:{" "}
                        {summary.leg_angle_deg != null
                          ? `${summary.leg_angle_deg.toFixed(1)}°`
                          : "—"}
                      </p>
                    ) : (
                      <p className="muted" style={{ color: "var(--coral)" }}>
                        {t("wblt.floorFlagMessage")}
                      </p>
                    )}
                  </div>
                );
              })}
              <div className="panel-head" style={{ marginTop: 10, marginBottom: 8 }}>
                <h3 style={{ fontSize: "1rem" }}>{t("wblt.symmetryTitle")}</h3>
              </div>
              <p className="muted" style={{ fontSize: "0.85rem" }}>
                {sessionSummary.symmetry.status === "asymmetry_flag"
                  ? t("wblt.symmetryFlag")
                  : sessionSummary.symmetry.status === "symmetric"
                    ? t("wblt.symmetrySymmetric")
                    : "—"}
              </p>
              <button
                className="btn btn-primary btn-block"
                onClick={() => void finishTest()}
                style={{ marginTop: 18 }}
              >
                {t("wblt.finishTest")}
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
