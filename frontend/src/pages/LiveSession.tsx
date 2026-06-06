import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import PoseFigure from "../components/PoseFigure";
import { ShieldCheck, Close } from "../components/Icons";
import { sessionService } from "../services/sessionService";
import { useSessionFlow } from "../session";

export default function LiveSession() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const { mode, exerciseCode, sessionId } = useSessionFlow();
  const [sec, setSec] = useState(0);
  const [reps, setReps] = useState(0);
  const [ending, setEnding] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const id = setInterval(() => {
      setSec((s) => s + 1);
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
      await sessionService.end(sessionId, {
        capture_quality: 0.9,
        valid_frame_ratio: 0.9,
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
          <p><span className="band good" style={{ marginRight: 6 }}>{t("live.paused")}</span>{t("common." + (mode === "rehab" ? "rehab" : "functional"))}</p>
        </div>
        <div className="topbar-actions">
          <button className="btn btn-ghost" onClick={endSession} disabled={ending} style={{ borderColor: "var(--coral)", color: "var(--coral)" }}><Close />{ending ? t("common.loading") : t("live.stop")}</button>
        </div>
      </div>
      {error && <p className="muted" style={{ color: "var(--coral)", marginBottom: 18 }}>{error}</p>}

      <div className="cam-grid">
        <div className="cam-stage reveal">
          <div className="q-badge"><ShieldCheck width={16} height={16} />{t("live.quality")} · 90%</div>
          <PoseFigure />
          <div style={{ position: "absolute", bottom: 16, left: 0, right: 0, textAlign: "center", color: "var(--text-3)", fontSize: "0.84rem" }}>{t("live.cue")}</div>
        </div>

        <div className="stack" style={{ gap: 18 }}>
          <div className="live-hud">
            <div className="hud-card reveal"><div className="hl2">{t("live.timer")}</div><div className="hv">{mm}:{ss}</div></div>
            <div className="hud-card reveal"><div className="hl2">{t("live.reps")}</div><div className="hv">{reps} <span style={{ fontSize: "0.9rem", color: "var(--text-3)" }}>{t("live.repTarget")}</span></div></div>
          </div>

          <div className="panel reveal">
            <div className="panel-head" style={{ marginBottom: 18 }}><div><h3>{t("live.liveBand")}</h3></div></div>
            <div className="live-band band-good" style={{ fontSize: "1.6rem", marginBottom: 18 }}>
              <span className="dot" style={{ width: 12, height: 12, borderRadius: "50%", background: "var(--good)", display: "inline-block" }} />
              {t("common.good")}
            </div>
            <div className="track" style={{ height: 12 }}><div className="fill good" style={{ width: pct + "%", transition: "width .5s var(--ease)" }} /></div>
            <p className="muted" style={{ fontSize: "0.84rem", marginTop: 10 }}>{reps}/5 {t("common.functional")}</p>
          </div>

          <button className="btn btn-primary btn-lg btn-block reveal" onClick={endSession} disabled={ending}>{ending ? t("common.loading") : t("live.stop")}</button>
        </div>
      </div>
    </>
  );
}
