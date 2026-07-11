// Weight-Bearing Lunge Test live session — Stage 2 (guided bracket, both legs, symmetry).
// Per leg: LOADING (fetch bracket target) -> SETUP -> COUNTDOWN -> RECORDING
// (calibrate + lunge, buffered together) -> SELF_REPORT_TOUCH -> posting ->
// ATTEMPT_RESULT (more attempts left) or LEG_RESULT (leg complete). After the
// last leg: SESSION_RESULT (symmetry + both legs) -> finish.
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
import GeneratingReportOverlay from "../../components/GeneratingReportOverlay";
import { Close } from "../../components/Icons";
import { sessionService } from "../../services/sessionService";
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
import { useWebcam } from "../../hooks/useWebcam";
import { useMediaPipePose } from "../../hooks/useMediaPipePose";
import { useSessionRecorder } from "../../hooks/useSessionRecorder";
import { computeFrameQuality } from "../../utils/captureQuality";

type Stage =
  | "loading"
  | "setup"
  | "countdown"
  | "recording"
  | "self_report"
  | "posting"
  | "attempt_result"
  | "leg_result"
  | "session_result";

const COUNTDOWN_START_SEC = 3;
const DEFAULT_LEG_ORDER: WbltLeg[] = ["right", "left"];
const DEFAULT_ATTEMPTS_PER_LEG = 3;

const IDLE_UPDATE: WbltLiveUpdate = { calibrated: false, heelLifted: false, thetaDeg: null };

export default function WbltLiveSessionPage() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const { sessionId } = useSessionFlow();

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
  const [ending, setEnding] = useState(false);
  const [countdownSeconds, setCountdownSeconds] = useState(COUNTDOWN_START_SEC);
  const countdownTimerRef = useRef<number | null>(null);

  const { videoRef, setVideoRef, ready: webcamReady, error: webcamError } = useWebcam();
  const { landmarks, worldLandmarks } = useMediaPipePose(videoRef, webcamReady);
  const recorder = useSessionRecorder();
  const trackerRef = useRef(createWbltLiveTracker(leg));
  const busyRef = useRef(false);
  const qualitySamplesRef = useRef<{ score: number; validFrameRatio: number }[]>([]);

  const captureQuality = computeFrameQuality(landmarks ?? []);

  // Fetch bracket/attempts_per_leg config once, then load the first leg's target.
  useEffect(() => {
    if (!sessionId) return;
    let cancelled = false;
    wbltApi
      .config()
      .then((cfg) => {
        if (cancelled) return;
        setLegOrder(cfg.leg_order);
        setAttemptsPerLeg(cfg.attempts_per_leg);
        heelLiftConfigRef.current = {
          heelBaselineFrames: cfg.heel_baseline_frames,
          heelLiftTolRatio: cfg.heel_lift_tol_ratio,
          heelLiftHysteresisRatio: cfg.heel_lift_hysteresis_ratio,
        };
      })
      .catch(() => {
        // Non-fatal: falls back to DEFAULT_LEG_ORDER/DEFAULT_ATTEMPTS_PER_LEG.
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
    void loadBracket(leg);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, leg]);

  function startRecording() {
    trackerRef.current = createWbltLiveTracker(leg, heelLiftConfigRef.current);
    recorder.start();
    setLiveUpdate(IDLE_UPDATE);
    setError("");
    setStage("recording");
  }

  function beginCountdown() {
    setCountdownSeconds(COUNTDOWN_START_SEC);
    setStage("countdown");
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
  }, [stage]);

  // Buffer frames + run the live tracker only while an attempt is actively recording.
  useEffect(() => {
    if (!landmarks || stage !== "recording") return;
    const now = performance.now();
    recorder.record(
      { timestampMs: now, landmarks, worldLandmarks: worldLandmarks ?? [] },
      captureQuality,
    );
    if (worldLandmarks) {
      setLiveUpdate(trackerRef.current.update(worldLandmarks));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [landmarks, stage]);

  function stopAndAskTouch() {
    setStage("self_report");
  }

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

  function nextAttempt() {
    if (!lastResult) return;
    setAttemptNumber(lastResult.attempt_number);
    setTargetDistanceCm(lastResult.next_target_distance_cm);
    setStage("setup");
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
      setStage("session_result");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("camera.startError"));
      setStage("leg_result");
    } finally {
      busyRef.current = false;
    }
  }

  async function finishTest() {
    if (!sessionId || busyRef.current) return;
    busyRef.current = true;
    try {
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
      busyRef.current = false;
    }
  }

  async function handleCancel() {
    if (busyRef.current) return;
    busyRef.current = true;
    setEnding(true);
    try {
      if (sessionId) await sessionService.cancel(sessionId);
    } catch (err) {
      console.error("[WbltLiveSessionPage] Cancel failed", err);
    } finally {
      nav("/exercise");
    }
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

      <div className="topbar">
        <div>
          <h1>{t("wblt.reportTitle")}</h1>
          <p>{legPrompt}</p>
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
              <div className="hud-card reveal">
                <div className="hl2">
                  {isBonusAttempt
                    ? t("wblt.bonusAttempt")
                    : t("wblt.attemptOf", { n: attemptNumber, total: attemptsPerLeg })}
                </div>
              </div>
            )}
          </div>

          {stage === "setup" && targetDistanceCm != null && (
            <div className="panel reveal">
              <div className="panel-head" style={{ marginBottom: 14 }}>
                <h3>{t("wblt.targetInstruction")}</h3>
              </div>
              <div className="hv" style={{ fontSize: "2rem", marginBottom: 16 }}>
                {targetDistanceCm.toFixed(1)} cm
              </div>
              <ol className="setup-guidance-list">
                <li>{t("wblt.setupGuidanceSide")}</li>
                <li>{t("wblt.setupGuidanceDistance")}</li>
                <li>{t("wblt.setupGuidanceLunge")}</li>
              </ol>
              <button
                className="btn btn-primary btn-block"
                onClick={beginCountdown}
                style={{ marginTop: 16 }}
              >
                {t("wblt.startAttempt")}
              </button>
            </div>
          )}

          {stage === "countdown" && (
            <div className="panel reveal">
              <div className="hv" style={{ fontSize: "3rem", textAlign: "center" }}>
                {countdownSeconds}
              </div>
              <p className="muted" style={{ textAlign: "center" }}>
                {t("wblt.setupGuidanceSide")}
              </p>
            </div>
          )}

          {stage === "recording" && (
            <div className="panel reveal">
              <div className="panel-head" style={{ marginBottom: 14 }}>
                <h3>{t("live.liveBand")}</h3>
              </div>
              <div className="sls-live-status-box">
                <span className="sls-live-status-text">{liveMessage}</span>
              </div>
              <button
                className="btn btn-primary btn-block"
                onClick={stopAndAskTouch}
                style={{ marginTop: 20 }}
                disabled={!liveUpdate.calibrated}
              >
                {t("wblt.iAttemptedTouch")}
              </button>
            </div>
          )}

          {stage === "self_report" && (
            <div className="panel reveal">
              <div className="panel-head" style={{ marginBottom: 14 }}>
                <h3>{t("wblt.touchQuestion")}</h3>
              </div>
              <div className="sls-modal-actions">
                <button className="btn btn-ghost btn-block" onClick={() => void submitTouch(false)}>
                  {t("wblt.touchNo")}
                </button>
                <button
                  className="btn btn-primary btn-block"
                  onClick={() => void submitTouch(true)}
                >
                  {t("wblt.touchYes")}
                </button>
              </div>
            </div>
          )}

          {stage === "attempt_result" && lastResult && (
            <div className="panel reveal">
              <div className="panel-head" style={{ marginBottom: 14 }}>
                <h3>{t("wblt.attemptResultTitle")}</h3>
              </div>
              <p>
                <strong>
                  {lastResult.valid_touch ? t("wblt.touchYes") : t("wblt.touchNo")} —{" "}
                  {lastResult.target_distance_cm} cm
                </strong>
              </p>
              <p className="muted" style={{ fontSize: "0.85rem", marginTop: 6 }}>
                {t("wblt.angleResultLabel")}:{" "}
                {lastResult.theta_peak_deg != null
                  ? `${lastResult.theta_peak_deg.toFixed(1)}°`
                  : "—"}
              </p>
              {lastResult.warning_tags.map((tag) => (
                <p key={tag} className="muted" style={{ fontSize: "0.8rem", marginTop: 4 }}>
                  {t(`wblt.warn_${tag}`, { defaultValue: tag })}
                </p>
              ))}
              <button
                className="btn btn-primary btn-block"
                onClick={nextAttempt}
                style={{ marginTop: 18 }}
              >
                {t("wblt.nextAttempt")}
              </button>
            </div>
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
