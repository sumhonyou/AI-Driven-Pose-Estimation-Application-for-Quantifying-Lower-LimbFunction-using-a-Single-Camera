import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import PoseCanvas from "../components/PoseCanvas";
import CaptureQualityBadge from "../components/CaptureQualityBadge";
import { Close } from "../components/Icons";
import { sessionService } from "../services/sessionService";
import { useSessionFlow } from "../session";
import { useWebcam } from "../hooks/useWebcam";
import { useMediaPipePose } from "../hooks/useMediaPipePose";
import { computeFrameQuality } from "../utils/captureQuality";
import { useSessionRecorder } from "../hooks/useSessionRecorder";

export default function LiveSession() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const { mode, exerciseCode, sessionId } = useSessionFlow();
  const [sec, setSec] = useState(0);
  const [reps, setReps] = useState(0);
  const [ending, setEnding] = useState(false);
  const [error, setError] = useState("");

  // Real webcam + pose
  const { videoRef, ready: webcamReady, error: webcamError } = useWebcam();
  const { landmarks } = useMediaPipePose(videoRef, webcamReady);

  // Live quality from landmarks
  const captureQuality = computeFrameQuality(landmarks ?? []);

  // Session quality recorder — buffers frames for Phase 3/4 and provides summary metrics
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

  // Record each frame when we have landmarks
  useEffect(() => {
    if (landmarks) {
      recorder.record(
        { timestampMs: performance.now(), landmarks },
        captureQuality,
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [landmarks]);

  // Session timer
  useEffect(() => {
    const id = setInterval(() => {
      setSec((s) => s + 1);
      // Rep counting is still mocked (real logic arrives in Phase 3)
      setReps((r) => (r < 5 ? (Math.random() > 0.55 ? r + 1 : r) : r));
    }, 1000);
    return () => clearInterval(id);
  }, []);

  const mm = String(Math.floor(sec / 60)).padStart(2, "0");
  const ss = String(sec % 60).padStart(2, "0");
  const pct = (reps / 5) * 100;

  const endSession = async () => {
    if (!sessionId) {
      setError(t("live.noSession"));
      return;
    }
    setEnding(true);
    setError("");
    try {
      // Use real quality metrics from the recorder instead of hardcoded 0.9
      const { score, validFrameRatio } = recorder.summary();
      console.log(
        `[LiveSession] Ending session — quality: ${score.toFixed(2)}, validRatio: ${validFrameRatio.toFixed(2)}`,
      );

      await sessionService.end(sessionId, {
        capture_quality: score,
        valid_frame_ratio: validFrameRatio,
      });
      nav(`/report?session=${sessionId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("live.endError"));
    } finally {
      setEnding(false);
    }
  };

  return (
    <>
      <div className="topbar">
        <div>
          <h1>{exerciseCode || t("landing.s2sName")}</h1>
          <p>
            <span className="band good" style={{ marginRight: 6 }}>
              {t("live.paused")}
            </span>
            {t("common." + (mode === "rehab" ? "rehab" : "functional"))}
          </p>
        </div>
        <div className="topbar-actions">
          <button
            className="btn btn-ghost"
            onClick={endSession}
            disabled={ending}
            style={{ borderColor: "var(--coral)", color: "var(--coral)" }}
          >
            <Close />
            {ending ? t("common.loading") : t("live.stop")}
          </button>
        </div>
      </div>
      {error && (
        <p
          className="muted"
          style={{ color: "var(--coral)", marginBottom: 18 }}
        >
          {error}
        </p>
      )}

      <div className="cam-grid">
        <div className="cam-stage reveal">
          <CaptureQualityBadge
            quality={captureQuality}
            label={t("live.quality")}
          />
          <PoseCanvas
            videoRef={videoRef}
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
                {reps}{" "}
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
              className="live-band band-good"
              style={{ fontSize: "1.6rem", marginBottom: 18 }}
            >
              <span
                className="dot"
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: "50%",
                  background: "var(--good)",
                  display: "inline-block",
                }}
              />
              {t("common.good")}
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
              {reps}/5 {t("common.functional")}
            </p>
          </div>

          <button
            className="btn btn-primary btn-lg btn-block reveal"
            onClick={endSession}
            disabled={ending}
          >
            {ending ? t("common.loading") : t("live.stop")}
          </button>
        </div>
      </div>
    </>
  );
}
