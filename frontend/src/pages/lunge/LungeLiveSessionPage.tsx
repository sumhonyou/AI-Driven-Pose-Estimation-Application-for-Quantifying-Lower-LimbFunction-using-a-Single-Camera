// Lunge live session: mirrors SquatLiveSessionPage.tsx's structure and flow
// exactly (task.md Stage 4.7 (Lunge)) — an unlimited-rep continuous set, ended
// manually by "Finish Set", which posts the whole buffered set once to
// POST /api/module-b/analyze. The backend segments reps and grades the set
// server-side (front/back-leg-aware, cross-rep symmetry); the live rep counter
// and front-knee gauge here are a client-side UX estimate only
// (lungeLiveEstimate.ts), never authoritative.
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import PoseCanvas from "../../components/PoseCanvas";
import CaptureQualityBadge from "../../components/CaptureQualityBadge";
import GeneratingReportOverlay from "../../components/GeneratingReportOverlay";
import StartSetCountdown from "../../components/lunge/StartSetCountdown";
import { Close, Target, Alert } from "../../components/Icons";
import { sessionService } from "../../services/sessionService";
import { moduleBService } from "../../services/moduleBService";
import { useSessionFlow } from "../../session";
import { useWebcam } from "../../hooks/useWebcam";
import { useMediaPipePose } from "../../hooks/useMediaPipePose";
import { useSessionRecorder } from "../../hooks/useSessionRecorder";
import { computeFrameQuality } from "../../utils/captureQuality";
import {
  createLungeLiveEstimator,
  depthGaugePct,
  depthZoneFor,
  fetchLungeLiveConfig,
  FALLBACK_LUNGE_LIVE_CONFIG,
  type LungeBandEstimate,
  type LungeLeg,
  type LungeLiveConfig,
} from "../../utils/lunge/lungeLiveEstimate";
import goodRepSrc from "../../assets/sound effect/Rep correct sound effect.mp3";

type Stage = "setup" | "countdown" | "recording" | "posting";

const COUNTDOWN_START_SEC = 5;

/** Motivational-only target choices; never sent to the backend or grading (mirrors squat). */
const TARGET_OPTIONS = [10, 20, 30, 40, 50, 60, 70, 80];

/** How long without a meaningful flexion change counts as "no movement". */
const INACTIVITY_TIMEOUT_MS = 9000;
/** Minimum frame-to-frame flexion change (deg) that counts as motion. */
const MOTION_EPSILON_DEG = 2;

export default function LungeLiveSessionPage() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const { sessionId } = useSessionFlow();

  const [stage, setStage] = useState<Stage>("setup");
  const [targetReps, setTargetReps] = useState<number | null>(null);
  const [repCount, setRepCount] = useState(0);
  const [sec, setSec] = useState(0);
  const [error, setError] = useState("");
  const [ending, setEnding] = useState(false);
  const [showInactivityPrompt, setShowInactivityPrompt] = useState(false);
  const [showTargetHitPrompt, setShowTargetHitPrompt] = useState(false);
  const [countdownSeconds, setCountdownSeconds] = useState(COUNTDOWN_START_SEC);
  const countdownTimerRef = useRef<number | null>(null);

  // Live angle readouts — display only, mirroring lungeLiveEstimate.ts's estimator
  // state so the panel can show exactly what the FSM is currently tracking.
  const [frontLeg, setFrontLeg] = useState<LungeLeg>("left");
  const [frontKneeFlexionDeg, setFrontKneeFlexionDeg] = useState(0);
  const [trunkLeanDeg, setTrunkLeanDeg] = useState(0);
  const [repPeakFlexionDeg, setRepPeakFlexionDeg] = useState<number | null>(null);
  const [kneePassesToe, setKneePassesToe] = useState(false);
  const [lastRepPeakDeg, setLastRepPeakDeg] = useState<number | null>(null);
  const [lastRepBand, setLastRepBand] = useState<LungeBandEstimate>(null);
  const [lastRepKneePassedToe, setLastRepKneePassedToe] = useState<boolean | null>(null);
  // Live thresholds for the depth gauge's zone boundaries — state (not a ref) so
  // the gauge re-renders once the real backend config arrives (X7).
  const [liveConfig, setLiveConfig] = useState<LungeLiveConfig>(FALLBACK_LUNGE_LIVE_CONFIG);

  const { videoRef, setVideoRef, ready: webcamReady, error: webcamError } = useWebcam();
  const { landmarks, worldLandmarks } = useMediaPipePose(videoRef, webcamReady);
  const recorder = useSessionRecorder();
  const captureQuality = computeFrameQuality(landmarks ?? []);

  const estimatorRef = useRef(createLungeLiveEstimator());
  const finishingRef = useRef(false);
  const lastMotionMsRef = useRef(0);
  const previousFlexionRef = useRef(0);
  const hasPromptedTargetHitRef = useRef(false);
  const goodRepAudio = useRef(new Audio(goodRepSrc));
  // Last *rendered* (rounded) angle values — guards the per-frame setState calls
  // below so a frame whose rounded display value hasn't changed never re-renders.
  const lastRenderedKneeDegRef = useRef(0);
  const lastRenderedTrunkLeanDegRef = useRef(0);
  const lastRenderedRepPeakDegRef = useRef<number | null>(null);

  // Fetch live thresholds once so the on-screen rep/band estimate matches the
  // backend's official lunge config (X7 -- local constants are fallback only).
  useEffect(() => {
    fetchLungeLiveConfig().then((config) => {
      setLiveConfig(config);
      estimatorRef.current = createLungeLiveEstimator(config);
    });
  }, []);

  function startSet() {
    estimatorRef.current = createLungeLiveEstimator(liveConfig);
    recorder.start();
    setRepCount(0);
    setSec(0);
    setShowInactivityPrompt(false);
    setShowTargetHitPrompt(false);
    hasPromptedTargetHitRef.current = false;
    lastMotionMsRef.current = performance.now();
    setFrontLeg("left");
    setFrontKneeFlexionDeg(0);
    setTrunkLeanDeg(0);
    setRepPeakFlexionDeg(null);
    setKneePassesToe(false);
    lastRenderedKneeDegRef.current = 0;
    lastRenderedTrunkLeanDegRef.current = 0;
    lastRenderedRepPeakDegRef.current = null;
    setLastRepPeakDeg(null);
    setLastRepBand(null);
    setLastRepKneePassedToe(null);
    setStage("recording");
  }

  // "Start Set" begins a 5s full-page countdown (gives the user time to step back and
  // get their whole body in frame) before recording/rep tracking actually starts --
  // avoids the estimator misreading the user's approach to position as a lunge rep.
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
  // while a prompt is open, same reasoning as squat: dismissing a prompt by
  // walking up to the camera flexes the knees enough to look like a rep to the
  // threshold-based estimator, so nothing is recorded or fed to it until the
  // user is actually back to exercising.
  useEffect(() => {
    if (!landmarks || stage !== "recording" || showTargetHitPrompt || showInactivityPrompt) {
      return;
    }
    const now = performance.now();
    recorder.record(
      { timestampMs: now, landmarks, worldLandmarks: worldLandmarks ?? [] },
      captureQuality,
    );
    if (worldLandmarks) {
      const update = estimatorRef.current.update(worldLandmarks, now);
      if (
        Math.abs(update.currentFrontKneeFlexionDeg - previousFlexionRef.current) >
        MOTION_EPSILON_DEG
      ) {
        lastMotionMsRef.current = now;
      }
      previousFlexionRef.current = update.currentFrontKneeFlexionDeg;

      setFrontLeg(update.frontLeg);
      setKneePassesToe(update.kneePassesToe);

      const roundedKnee = Math.round(update.currentFrontKneeFlexionDeg);
      if (roundedKnee !== lastRenderedKneeDegRef.current) {
        lastRenderedKneeDegRef.current = roundedKnee;
        setFrontKneeFlexionDeg(update.currentFrontKneeFlexionDeg);
      }
      const roundedTrunkLean = Math.round(update.currentTrunkLeanDeg);
      if (roundedTrunkLean !== lastRenderedTrunkLeanDegRef.current) {
        lastRenderedTrunkLeanDegRef.current = roundedTrunkLean;
        setTrunkLeanDeg(update.currentTrunkLeanDeg);
      }
      const roundedRepPeak =
        update.currentRepPeakFrontKneeFlexionDeg != null
          ? Math.round(update.currentRepPeakFrontKneeFlexionDeg)
          : null;
      if (roundedRepPeak !== lastRenderedRepPeakDegRef.current) {
        lastRenderedRepPeakDegRef.current = roundedRepPeak;
        setRepPeakFlexionDeg(update.currentRepPeakFrontKneeFlexionDeg);
      }

      if (update.repJustCompleted) {
        setRepCount(update.repCount);
        setLastRepPeakDeg(update.lastRepPeakFrontKneeDeg);
        setLastRepBand(update.lastRepBandEstimate);
        setLastRepKneePassedToe(update.lastRepKneePassedToe);
        goodRepAudio.current.currentTime = 0;
        goodRepAudio.current.play().catch(() => {});
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [landmarks, stage, showTargetHitPrompt, showInactivityPrompt]);

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

  // Optional target-hit prompt: fires once, never auto-finishes.
  useEffect(() => {
    if (targetReps && repCount >= targetReps && !hasPromptedTargetHitRef.current) {
      hasPromptedTargetHitRef.current = true;
      setShowTargetHitPrompt(true);
    }
  }, [repCount, targetReps]);

  function dismissInactivityPrompt() {
    lastMotionMsRef.current = performance.now();
    setShowInactivityPrompt(false);
  }

  async function finishSet() {
    if (finishingRef.current || !sessionId) return;
    finishingRef.current = true;
    setShowInactivityPrompt(false);
    setShowTargetHitPrompt(false);
    setStage("posting");
    try {
      const { frames, score, validFrameRatio } = recorder.summary();
      await moduleBService.analyze(sessionId, "lunge", frames);
      await sessionService.end(sessionId, {
        capture_quality: score,
        valid_frame_ratio: validFrameRatio,
      });
      nav(`/report?session=${sessionId}`);
    } catch (err) {
      console.error("[LungeLiveSessionPage] Finish set failed", err);
      setError(err instanceof Error ? err.message : t("live.endError"));
      finishingRef.current = false;
      setStage("recording");
    }
  }

  function handleCancel() {
    if (finishingRef.current) return;
    finishingRef.current = true;
    setEnding(true);
    // Navigate away immediately -- never make "Cancel" wait on the network (mirrors squat).
    if (sessionId) {
      sessionService
        .cancel(sessionId)
        .catch((err) => console.error("[LungeLiveSessionPage] Cancel failed", err));
    }
    nav("/exercise");
  }

  if (!sessionId) {
    return <p className="muted">{t("live.noSession")}</p>;
  }

  const mm = String(Math.floor(sec / 60)).padStart(2, "0");
  const ss = String(sec % 60).padStart(2, "0");
  const pct = targetReps
    ? Math.min(100, (repCount / targetReps) * 100)
    : Math.min(100, repCount * 10);

  // Depth-gauge zone boundaries, as % of the gauge's full range -- identical
  // thresholds to lunge/config.py's rules.rom (X7: config-driven, never inline).
  const shallowPct = (liveConfig.romShallowStartDeg / liveConfig.romDeepFullScoreDeg) * 100;
  const parallelPct = (liveConfig.romParallelStartDeg / liveConfig.romDeepFullScoreDeg) * 100;
  const deepPct = (liveConfig.romDeepStartDeg / liveConfig.romDeepFullScoreDeg) * 100;
  const currentZone = depthZoneFor(frontKneeFlexionDeg, liveConfig);

  return (
    <>
      {stage === "posting" && <GeneratingReportOverlay />}
      {stage === "countdown" && (
        <StartSetCountdown secondsLeft={countdownSeconds} onCancel={cancelCountdown} />
      )}
      {showInactivityPrompt &&
        createPortal(
          <div className="sls-modal-overlay" role="dialog" aria-modal="true">
            <div className="sls-modal-card">
              <h3>{t("lunge.inactivityTitle")}</h3>
              <p className="muted">{t("lunge.inactivityBody")}</p>
              <div className="sls-modal-actions">
                <button className="btn btn-ghost btn-block" onClick={dismissInactivityPrompt}>
                  {t("lunge.continueSet")}
                </button>
                <button className="btn btn-primary btn-block" onClick={() => void finishSet()}>
                  {t("lunge.finishSet")}
                </button>
              </div>
            </div>
          </div>,
          document.body,
        )}
      {showTargetHitPrompt &&
        createPortal(
          <div className="sls-modal-overlay" role="dialog" aria-modal="true">
            <div className="sls-modal-card">
              <h3>{t("lunge.targetHitTitle", { target: targetReps })}</h3>
              <p className="muted">{t("lunge.targetHitBody")}</p>
              <div className="sls-modal-actions">
                <button
                  className="btn btn-ghost btn-block"
                  onClick={() => {
                    lastMotionMsRef.current = performance.now();
                    setShowTargetHitPrompt(false);
                  }}
                >
                  {t("lunge.continueSet")}
                </button>
                <button className="btn btn-primary btn-block" onClick={() => void finishSet()}>
                  {t("lunge.finishSet")}
                </button>
              </div>
            </div>
          </div>,
          document.body,
        )}

      <div className="topbar">
        <div>
          <h1>{t("lunge.reportTitle")}</h1>
          <p>{t("lunge.livePrompt")}</p>
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
              <div className="hv">{repCount}</div>
            </div>
          </div>

          {stage === "recording" && (
            <div className="panel">
              <div className="panel-head" style={{ marginBottom: 14 }}>
                <h3>{t("lunge.liveAnglesTitle")}</h3>
                <span className="pill">{t("lunge.frontLeg_" + frontLeg)}</span>
              </div>

              {kneePassesToe && (
                <div className="setup-banner" role="status" style={{ marginBottom: 14 }}>
                  <Alert width={20} height={20} />
                  <span>{t("lunge.kneePassesToeWarning")}</span>
                </div>
              )}

              <div className="depth-gauge-head">
                <span className="knee-metric-label" style={{ maxWidth: "none" }}>
                  {t("lunge.frontKneeDepthLabel")}
                </span>
                <span className="depth-gauge-value">
                  {Math.round(frontKneeFlexionDeg)}°
                  <span className="depth-gauge-zone-chip">
                    {t("lunge.depthZone_" + currentZone)}
                  </span>
                </span>
              </div>
              {repPeakFlexionDeg != null && (
                <span className="depth-gauge-peak-note">
                  {t("lunge.repPeakSoFar", { deg: Math.round(repPeakFlexionDeg) })}
                </span>
              )}
              <div className="depth-gauge-track">
                <span className="depth-gauge-zone z-minimal" style={{ width: `${shallowPct}%` }} />
                <span
                  className="depth-gauge-zone z-shallow"
                  style={{ width: `${parallelPct - shallowPct}%` }}
                />
                <span
                  className="depth-gauge-zone z-parallel"
                  style={{ width: `${deepPct - parallelPct}%` }}
                />
                <span className="depth-gauge-zone z-deep" style={{ width: `${100 - deepPct}%` }} />
                <span
                  className="depth-gauge-marker"
                  style={{ left: `${depthGaugePct(frontKneeFlexionDeg, liveConfig)}%` }}
                />
              </div>
              <div className="depth-gauge-ticks">
                <span style={{ left: `${shallowPct}%` }}>{t("lunge.depthZone_shallow")}</span>
                <span style={{ left: `${parallelPct}%` }}>{t("lunge.depthZone_parallel")}</span>
                <span style={{ left: `${deepPct}%` }}>{t("lunge.depthZone_deep")}</span>
              </div>

              <div className="knee-metrics">
                <div className="knee-metric-card">
                  <div>
                    <span className="knee-metric-label">{t("lunge.trunkLeanLabel")}</span>
                    <strong>{Math.round(trunkLeanDeg)}°</strong>
                  </div>
                </div>
                <div className="knee-metric-card">
                  <div>
                    <span className="knee-metric-label">{t("lunge.lastRepDepthLabel")}</span>
                    <strong>
                      {lastRepPeakDeg != null ? `${Math.round(lastRepPeakDeg)}°` : "—"}
                    </strong>
                    {lastRepBand && (
                      <span
                        className={"band " + lastRepBand.toLowerCase()}
                        style={{ marginTop: 8, display: "inline-block" }}
                      >
                        {t("common." + lastRepBand.toLowerCase())}
                      </span>
                    )}
                    {lastRepKneePassedToe && (
                      <span
                        className="knee-metric-label"
                        style={{ display: "block", marginTop: 8, color: "var(--coral)" }}
                      >
                        {t("lunge.lastRepKneePassedToe")}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <p className="muted" style={{ fontSize: "0.74rem", marginTop: 12 }}>
                {t("lunge.liveAngleGuidanceNote")}
              </p>
            </div>
          )}

          <div className="panel reveal">
            <div className="panel-head" style={{ marginBottom: 14 }}>
              <h3>{t("live.liveBand")}</h3>
            </div>

            {stage === "setup" ? (
              <>
                <p className="muted" style={{ marginBottom: 14 }}>
                  {t("lunge.setupTargetPrompt")}
                </p>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 18 }}>
                  <Target width={18} height={18} />
                  <select
                    className="select"
                    value={targetReps ?? ""}
                    onChange={(e) => setTargetReps(e.target.value ? Number(e.target.value) : null)}
                  >
                    <option value="">{t("lunge.noTarget")}</option>
                    {TARGET_OPTIONS.map((n) => (
                      <option key={n} value={n}>
                        {t("lunge.targetOption", { n })}
                      </option>
                    ))}
                  </select>
                </div>
                <button className="btn btn-primary btn-block" onClick={beginCountdown}>
                  {t("lunge.startSet")}
                </button>
              </>
            ) : (
              <>
                <div className="sls-live-status-box">
                  <span className="sls-live-status-text">
                    {targetReps
                      ? t("lunge.repOfTarget", { rep: repCount, target: targetReps })
                      : t("lunge.repCounted", { rep: repCount })}
                  </span>
                </div>
                <div className="track" style={{ height: 12 }}>
                  <div
                    className="fill good"
                    style={{ width: pct + "%", transition: "width .5s var(--ease)" }}
                  />
                </div>
                <p className="muted" style={{ fontSize: "0.82rem", marginTop: 10 }}>
                  {t("lunge.finishWhenReady")}
                </p>
                <div style={{ marginTop: 20 }}>
                  <button
                    className="btn btn-primary btn-block"
                    onClick={() => void finishSet()}
                    disabled={stage !== "recording"}
                  >
                    {t("lunge.finishSet")}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
