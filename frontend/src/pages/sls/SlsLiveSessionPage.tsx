// Single-Leg Stance live session: walks the fixed leg order (right, then left),
// buffers each leg's landmarks locally, posts to /api/sls/analyze at the end of
// each hold, then collects the support self-report before ending the session.
//
// Live feedback (timer, lift-line, ball-in-circle, combo) is computed entirely
// client-side via liveGeometry.ts for instant response — it is a helper only.
// The backend's POST response is always the authoritative, persisted result.
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import PoseCanvas from "../../components/PoseCanvas";
import CaptureQualityBadge from "../../components/CaptureQualityBadge";
import GeneratingReportOverlay from "../../components/GeneratingReportOverlay";
import BallInCircleOverlay from "../../components/sls/BallInCircleOverlay";
import LiftLineMarker from "../../components/sls/LiftLineMarker";
import ComboScore from "../../components/sls/ComboScore";
import SupportSelfReportModal from "../../components/sls/SupportSelfReportModal";
import StartHoldCountdown from "../../components/sls/StartHoldCountdown";
import { Close } from "../../components/Icons";
import { sessionService, enqueueCancel } from "../../services/sessionService";
import { slsApi, type SlsLegMetrics, type UsedSupport } from "../../services/sls/slsApi";
import {
  createSlsLiveTracker,
  type SlsLeg,
  type SlsLiveUpdate,
} from "../../services/sls/liveGeometry";
import { useSessionFlow } from "../../session";
import { useWebcam } from "../../hooks/useWebcam";
import { useMediaPipePose } from "../../hooks/useMediaPipePose";
import { useSessionRecorder } from "../../hooks/useSessionRecorder";
import { computeFrameQuality } from "../../utils/captureQuality";
import { SLS_LEG_ORDER, SLS_MAX_HOLD_SEC } from "../../config/moduleAThresholds";

type Stage =
  "ready" | "countdown" | "recording" | "posting" | "leg_result" | "support" | "finishing";

const COUNTDOWN_START_SEC = 5;

const IDLE_UPDATE: SlsLiveUpdate = {
  phase: "calibrating",
  holdSeconds: 0,
  ballXNorm: 0,
  ballInside: false,
  aboveLine: false,
  liftProgress: 0,
  points: 0,
  multiplier: 1,
  cappedAtMax: false,
};

export default function SlsLiveSessionPage() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const { mode, sessionId, setSessionId } = useSessionFlow();

  const [legIndex, setLegIndex] = useState(0);
  const leg = SLS_LEG_ORDER[legIndex] as SlsLeg;

  const [stage, setStage] = useState<Stage>("ready");
  const [liveUpdate, setLiveUpdate] = useState<SlsLiveUpdate>(IDLE_UPDATE);
  const [legResults, setLegResults] = useState<Partial<Record<SlsLeg, SlsLegMetrics>>>({});
  const [error, setError] = useState("");
  const [supportSubmitting, setSupportSubmitting] = useState(false);
  const [countdownSeconds, setCountdownSeconds] = useState(COUNTDOWN_START_SEC);
  const countdownTimerRef = useRef<number | null>(null);

  const { videoRef, setVideoRef, ready: webcamReady, error: webcamError } = useWebcam();
  const { landmarks, worldLandmarks, stopDetection } = useMediaPipePose(videoRef, webcamReady);
  const recorder = useSessionRecorder();
  const trackerRef = useRef(createSlsLiveTracker(leg));
  const finishingLegRef = useRef(false);
  const finishingSessionRef = useRef(false);
  const qualitySamplesRef = useRef<{ score: number; validFrameRatio: number }[]>([]);

  const captureQuality = computeFrameQuality(landmarks ?? []);

  function startHold() {
    trackerRef.current = createSlsLiveTracker(leg);
    recorder.start();
    setLiveUpdate(IDLE_UPDATE);
    setError("");
    setStage("recording");
  }

  // "Start Hold" begins a 5s full-page countdown (gives the user time to get into
  // position) before the hold itself — and its live tracking/timer — actually starts.
  function beginCountdown() {
    setCountdownSeconds(COUNTDOWN_START_SEC);
    setStage("countdown");
  }

  function cancelCountdown() {
    if (countdownTimerRef.current != null) {
      window.clearInterval(countdownTimerRef.current);
      countdownTimerRef.current = null;
    }
    setStage("ready");
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
          startHold();
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

  async function finalizeLeg() {
    if (finishingLegRef.current || !sessionId) return;
    finishingLegRef.current = true;
    setStage("posting");
    try {
      const { frames, score, validFrameRatio } = recorder.summary();
      qualitySamplesRef.current.push({ score, validFrameRatio });
      const result = await slsApi.analyze(sessionId, leg, frames);
      setLegResults((prev) => ({ ...prev, [leg]: result.metrics }));
      setStage("leg_result");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("camera.startError"));
      setStage("ready");
    } finally {
      finishingLegRef.current = false;
    }
  }

  // Buffer frames + run the live tracker only while a hold is actively recording.
  useEffect(() => {
    if (!landmarks || stage !== "recording") return;
    const now = performance.now();
    recorder.record(
      { timestampMs: now, landmarks, worldLandmarks: worldLandmarks ?? [] },
      captureQuality,
    );
    if (worldLandmarks) {
      const update = trackerRef.current.update(worldLandmarks, now);
      setLiveUpdate(update);
      if (update.phase === "stopped" && !finishingLegRef.current) {
        void finalizeLeg();
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [landmarks, stage]);

  function continueOrFinish() {
    if (legIndex < SLS_LEG_ORDER.length - 1) {
      setLegIndex((i) => i + 1);
      setStage("ready");
    } else {
      setStage("support");
    }
  }

  function retryLeg() {
    setStage("ready");
  }

  async function submitSupport(used: UsedSupport) {
    if (!sessionId || finishingSessionRef.current) return;
    finishingSessionRef.current = true;
    setSupportSubmitting(true);
    try {
      await slsApi.support(sessionId, used);
      setStage("finishing");
      const samples = qualitySamplesRef.current;
      const avg = (vals: number[]) =>
        vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
      await sessionService.end(sessionId, {
        capture_quality: avg(samples.map((s) => s.score)),
        valid_frame_ratio: avg(samples.map((s) => s.validFrameRatio)),
      });
      nav(`/report?session=${sessionId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("live.endError"));
      finishingSessionRef.current = false;
      setSupportSubmitting(false);
    }
  }

  function handleCancel() {
    if (finishingSessionRef.current) return;
    finishingSessionRef.current = true;
    stopDetection();
    if (sessionId) enqueueCancel(sessionId);
    setSessionId(null);
    console.log("[SlsLiveSessionPage] Cancel navigating");
    nav(`/exercise?mode=${mode}`);
  }

  if (!sessionId) {
    return <p className="muted">{t("live.noSession")}</p>;
  }

  const legLabel = t(leg === "right" ? "sls.legRight" : "sls.legLeft");
  const legPrompt = t(leg === "right" ? "sls.legPromptRight" : "sls.legPromptLeft");

  const liveMessage =
    stage === "ready"
      ? t("sls.pressStartHold")
      : liveUpdate.phase === "calibrating"
        ? t("sls.standBothFeet")
        : liveUpdate.phase === "waiting"
          ? t("sls.liftAboveLine")
          : liveUpdate.phase === "holding"
            ? t("sls.holdSteady")
            : liveUpdate.cappedAtMax
              ? t("sls.timeReached")
              : t("sls.footDropped");

  const pct = Math.min(100, (liveUpdate.holdSeconds / SLS_MAX_HOLD_SEC) * 100);
  const currentLegResult = legResults[leg];
  const isLastLeg = legIndex === SLS_LEG_ORDER.length - 1;
  const overlaysVisible = stage === "recording" || stage === "posting";

  return (
    <>
      {(stage === "posting" || stage === "finishing") && <GeneratingReportOverlay />}
      {stage === "countdown" && (
        <StartHoldCountdown
          secondsLeft={countdownSeconds}
          legLabel={legLabel}
          onCancel={cancelCountdown}
        />
      )}
      {stage === "support" && (
        <SupportSelfReportModal onSelect={submitSupport} submitting={supportSubmitting} />
      )}

      <div className="topbar">
        <div>
          <h1>{t("sls.reportTitle")}</h1>
          <p>{legPrompt}</p>
        </div>
        <div className="topbar-actions">
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
        <div className="cam-stage reveal">
          <CaptureQualityBadge quality={captureQuality} label={t("live.quality")} />
          <PoseCanvas
            videoRef={videoRef}
            setVideoRef={setVideoRef}
            landmarks={landmarks}
            webcamReady={webcamReady}
            webcamError={webcamError}
          />
          <LiftLineMarker
            liftProgress={liveUpdate.liftProgress}
            aboveLine={liveUpdate.aboveLine}
            visible={overlaysVisible}
          />
          <BallInCircleOverlay
            ballXNorm={liveUpdate.ballXNorm}
            ballInside={liveUpdate.ballInside}
            visible={overlaysVisible && liveUpdate.phase === "holding"}
          />
          <ComboScore
            points={liveUpdate.points}
            multiplier={liveUpdate.multiplier}
            visible={overlaysVisible && liveUpdate.phase === "holding"}
          />
        </div>

        <div className="stack" style={{ gap: 18 }}>
          <div className="live-hud">
            <div className="hud-card reveal">
              <div className="hl2">{t("live.timer")}</div>
              <div className="hv">{liveUpdate.holdSeconds.toFixed(1)}s</div>
            </div>
            <div className="hud-card reveal">
              <div className="hl2">{t("sls.legLabel")}</div>
              <div className="hv">{legLabel}</div>
            </div>
          </div>

          {stage === "leg_result" && currentLegResult ? (
            <div className="panel reveal">
              <div className="panel-head" style={{ marginBottom: 14 }}>
                <h3>{legLabel}</h3>
              </div>
              <p>
                <strong>{currentLegResult.holdSeconds.toFixed(1)}s</strong> —{" "}
                {t("common." + currentLegResult.band)} ({currentLegResult.combinedScore.toFixed(1)}
                /10)
              </p>
              <p className="muted" style={{ fontSize: "0.85rem", marginTop: 6 }}>
                {t("sls.stability")}: {currentLegResult.stabilityScore.toFixed(1)}/10 ·{" "}
                {t("sls.stopReasonLabel")}: {t("sls.stopReason_" + currentLegResult.stopReason)}
              </p>
              <div className="sls-modal-actions" style={{ marginTop: 18 }}>
                <button className="btn btn-ghost btn-block" onClick={retryLeg}>
                  {t("sls.retry")}
                </button>
                <button className="btn btn-primary btn-block" onClick={continueOrFinish}>
                  {isLastLeg ? t("sls.finishTest") : t("sls.continueNextLeg")}
                </button>
              </div>
            </div>
          ) : (
            <div className="panel reveal">
              <div className="panel-head" style={{ marginBottom: 14 }}>
                <h3>{t("live.liveBand")}</h3>
              </div>
              <div className="sls-live-status-box">
                <span className="sls-live-status-text">{liveMessage}</span>
              </div>
              <div className="track" style={{ height: 12 }}>
                <div
                  className="fill good"
                  style={{ width: pct + "%", transition: "width .5s var(--ease)" }}
                />
              </div>
              <div style={{ marginTop: 20 }}>
                {stage === "ready" && (
                  <button className="btn btn-primary btn-block" onClick={beginCountdown}>
                    {t("sls.startHold")}
                  </button>
                )}
                {stage === "recording" && (
                  <button className="btn btn-cancel btn-block" onClick={() => void finalizeLeg()}>
                    {t("sls.stop")}
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
