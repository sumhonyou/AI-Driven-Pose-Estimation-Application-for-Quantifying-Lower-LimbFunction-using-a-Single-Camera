import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import PoseCanvas from "../components/PoseCanvas";
import CaptureQualityBadge from "../components/CaptureQualityBadge";
import GeneratingReportOverlay from "../components/GeneratingReportOverlay";
import { Close } from "../components/Icons";
import { sessionService } from "../services/sessionService";
import { useSessionFlow } from "../session";
import { useWebcam } from "../hooks/useWebcam";
import { useMediaPipePose } from "../hooks/useMediaPipePose";
import { computeFrameQuality } from "../utils/captureQuality";
import { useSessionRecorder } from "../hooks/useSessionRecorder";
import { moduleAService } from "../services/moduleAService";
import { createStsLiveEstimator } from "../utils/stsLiveEstimate";
import { humanizeLabel } from "../utils/format";
import {
  SAMPLE_FPS,
  STS_TARGET_REPS,
  MAX_SESSION_SECONDS,
  LIVE_KNEE_STAND_ENTER,
  LIVE_KNEE_SIT_ENTER,
  LIVE_MIN_VISIBILITY,
} from "../config/moduleAThresholds";
import type { PoseFrame } from "../types/pose";
import type { StsPhase, InvalidReasonCode } from "../utils/stsLiveEstimate";
import goodRepSrc from "../assets/sound effect/Rep correct sound effect.mp3";
import wrongRepSrc from "../assets/sound effect/Wrong sound effect.mp3";

const FAIL_REASON_DISPLAY_MS = 3500;

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

export default function LiveSession() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const { mode, exerciseCode, sessionId } = useSessionFlow();
  const isSts = exerciseCode === "sit_to_stand";

  const [sec, setSec] = useState(0);
  // Attempted: every concluded rep-boundary the client's FSM detects. Valid: only
  // ever set from the backend's authoritative recount — never guessed client-side.
  const [attemptedReps, setAttemptedReps] = useState(0);
  const [validReps, setValidReps] = useState(0);
  // Mirrors `validReps` but read/written synchronously within runAnalyzeCheck so a
  // chained (coalesced) call in the same tick never compares against a stale closure.
  const validRepsRef = useRef(0);
  const [running, setRunning] = useState(true);
  const [ending, setEnding] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [error, setError] = useState("");

  // Live Sit-to-Stand guidance (knee angle + why a rep wasn't counted) — display only.
  const [kneeAngle, setKneeAngle] = useState(0);
  const [minKneeAngle, setMinKneeAngle] = useState<number | null>(null);
  const [phase, setPhase] = useState<StsPhase>("sitting");
  // Optimistic client guess, shown instantly and reconciled once the backend responds.
  const [liveReasonGuess, setLiveReasonGuess] = useState<string | null>(null);
  const failReasonTimeoutRef = useRef<number | null>(null);

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
  const { landmarks, worldLandmarks } = useMediaPipePose(videoRef, webcamReady);

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

  // Start recorder on mount
  useEffect(() => {
    if (!recorderStarted.current) {
      recorder.start();
      recorderStarted.current = true;
      console.log("[LiveSession] Session recorder started");
    }
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
  useEffect(() => {
    if (landmarks) {
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
            setLiveReasonGuess(t(reasonCodeToI18nKey(update.reasonCode)));
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
  }, [landmarks]);

  // Session timer — stops immediately once the session is finishing or cancelled.
  useEffect(() => {
    if (!running) return;
    const id = setInterval(() => setSec((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, [running]);

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

  // Cancel: bails out of an incomplete session. Never scored, never saved as completed.
  const handleCancel = async () => {
    if (finishingRef.current) return;
    finishingRef.current = true;
    setRunning(false);
    setEnding(true);
    try {
      if (sessionId) await sessionService.cancel(sessionId);
    } catch (err) {
      console.error("[LiveSession] Cancel failed", err);
      setError(t("live.cancelError"));
    } finally {
      nav("/exercise");
    }
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
      <div className="topbar">
        <div>
          <h1>{liveTitle}</h1>
          <p>
            <span className="band good" style={{ marginRight: 6 }}>
              {t("live.paused")}
            </span>
            {t("common." + (mode === "rehab" ? "rehab" : "functional"))}
          </p>
        </div>
        <div className="topbar-actions">
          <button className="btn btn-cancel" onClick={handleCancel} disabled={ending}>
            <Close />
            {ending ? t("common.loading") : t("live.cancel")}
          </button>
        </div>
      </div>
      {error && (
        <p className="muted" style={{ color: "var(--coral)", marginBottom: 18 }}>
          {error}
        </p>
      )}

      <div className="cam-grid">
        <div className="cam-stage reveal">
          <CaptureQualityBadge quality={captureQuality} label={t("live.quality")} />
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
              <div className="hv">
                {validReps}{" "}
                <span style={{ fontSize: "0.9rem", color: "var(--text-3)" }}>
                  {t("live.repTarget")}
                </span>
              </div>
            </div>
          </div>

          <div className="panel reveal">
            <div className="panel-head" style={{ marginBottom: 18 }}>
              <div>
                <h3>{t("live.liveBand")}</h3>
              </div>
            </div>
            <div
              className={"live-band " + liveToneClass}
              style={{ fontSize: "1.15rem", marginBottom: 18 }}
            >
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
            <div className="track" style={{ height: 12 }}>
              <div
                className="fill good"
                style={{
                  width: pct + "%",
                  transition: "width .5s var(--ease)",
                }}
              />
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
