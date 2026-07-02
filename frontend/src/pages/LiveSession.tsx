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
import { moduleAService } from "../services/moduleAService";
import { createStsLiveEstimator } from "../utils/stsLiveEstimate";
import { humanizeLabel } from "../utils/format";
import {
  SAMPLE_FPS,
  STS_TARGET_REPS,
  LIVE_KNEE_STAND_ENTER,
  LIVE_KNEE_SIT_ENTER,
  LIVE_MIN_VISIBILITY,
} from "../config/moduleAThresholds";
import type { PoseFrame } from "../types/pose";
import type { StsPhase } from "../utils/stsLiveEstimate";
import goodRepSrc from "../assets/sound effect/Rep correct sound effect.mp3";
import wrongRepSrc from "../assets/sound effect/Wrong sound effect.mp3";

const FAIL_REASON_DISPLAY_MS = 3500;

export default function LiveSession() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const { mode, exerciseCode, sessionId } = useSessionFlow();
  const isSts = exerciseCode === "sit_to_stand";

  const [sec, setSec] = useState(0);
  const [reps, setReps] = useState(0);
  const [running, setRunning] = useState(true);
  const [ending, setEnding] = useState(false);
  const [error, setError] = useState("");

  // Live Sit-to-Stand guidance (knee angle + why a rep wasn't counted) — display only.
  const [kneeAngle, setKneeAngle] = useState(0);
  const [minKneeAngle, setMinKneeAngle] = useState<number | null>(null);
  const [phase, setPhase] = useState<StsPhase>("sitting");
  const [failReason, setFailReason] = useState<string | null>(null);
  const failReasonTimeoutRef = useRef<number | null>(null);

  // Guards against triggering the save/analyze flow (or a cancel) more than once.
  const finishingRef = useRef(false);

  // Real webcam + pose
  const { videoRef, setVideoRef, ready: webcamReady, error: webcamError } = useWebcam();
  const { landmarks, worldLandmarks } = useMediaPipePose(videoRef, webcamReady);

  // Live rep estimate (UX only) — the authoritative count comes back from POST /analyze on Stop.
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

  // Record each frame when we have landmarks, update the live rep estimate, and play sounds
  useEffect(() => {
    if (landmarks) {
      const now = performance.now();
      recorder.record(
        { timestampMs: now, landmarks, worldLandmarks: worldLandmarks ?? [] },
        captureQuality,
      );
      if (worldLandmarks && isSts) {
        const update = liveEstimator.current.update(worldLandmarks, now);
        setReps(update.count);
        setKneeAngle(update.kneeAngleDeg);
        setMinKneeAngle(update.minKneeAngleDeg);
        setPhase(update.phase);
        if (update.event === "good_rep") {
          goodRepAudio.current.currentTime = 0;
          goodRepAudio.current.play().catch(() => {});
        } else if (update.event === "failed_rep") {
          wrongRepAudio.current.currentTime = 0;
          wrongRepAudio.current.play().catch(() => {});
          setFailReason(t("live.reasonNotFullStand"));
          if (failReasonTimeoutRef.current) window.clearTimeout(failReasonTimeoutRef.current);
          failReasonTimeoutRef.current = window.setTimeout(
            () => setFailReason(null),
            FAIL_REASON_DISPLAY_MS,
          );
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

  const mm = String(Math.floor(sec / 60)).padStart(2, "0");
  const ss = String(sec % 60).padStart(2, "0");
  const pct = (reps / STS_TARGET_REPS) * 100;

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

  // Called once the 5th valid rep is detected — saves the session and shows the report.
  // Completion is only ever final once the server responds; reaching 5 client-side just
  // triggers this save so the user doesn't have to press anything.
  const finishSession = async () => {
    if (finishingRef.current || !sessionId) return;
    finishingRef.current = true;
    setRunning(false);
    setEnding(true);
    setError("");
    try {
      const { score, validFrameRatio, frames } = recorder.summary();
      console.log(
        `[LiveSession] Finishing session — quality: ${score.toFixed(2)}, validRatio: ${validFrameRatio.toFixed(2)}, frames: ${frames.length}`,
      );

      await sessionService.end(sessionId, {
        capture_quality: score,
        valid_frame_ratio: validFrameRatio,
      });

      const sampled = sampleFrames(frames);
      console.log(`[LiveSession] Sending ${sampled.length} sampled frames to Module A analyze`);
      await moduleAService.analyze(sessionId, "sit_to_stand", sampled);

      nav(`/report?session=${sessionId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("live.endError"));
      // Allow the user to cancel out if saving the finished session failed.
      finishingRef.current = false;
      setEnding(false);
    }
  };

  // Auto-complete: once 5 valid reps are detected, stop and save immediately — no button needed.
  useEffect(() => {
    if (isSts && reps >= STS_TARGET_REPS && !finishingRef.current) {
      void finishSession();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reps, isSts]);

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
    } else if (failReason) {
      liveMessage = failReason;
      liveToneClass = "band-warn";
    } else if (reps === 0) {
      liveMessage = t("live.waitingMovement");
      liveToneClass = "band-neutral";
    } else if (reps >= STS_TARGET_REPS) {
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

  return (
    <>
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
              {reps}/{STS_TARGET_REPS} {t("common.functional")}
            </p>

            {isSts && (
              <>
                <div className="sub-scores" style={{ marginTop: 18 }}>
                  <div className="sub-score">
                    <div className="ss-top">
                      <b>{t("live.currentKneeAngle")}</b>
                      <span>{Math.round(kneeAngle)}°</span>
                    </div>
                  </div>
                  <div className="sub-score">
                    <div className="ss-top">
                      <b>{t("live.lowestKneeAngle")}</b>
                      <span>{minKneeAngle != null ? `${Math.round(minKneeAngle)}°` : "—"}</span>
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

          <button
            className="btn btn-cancel btn-lg btn-block reveal"
            onClick={handleCancel}
            disabled={ending}
          >
            {ending ? t("common.loading") : t("live.cancel")}
          </button>
        </div>
      </div>
    </>
  );
}
