import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useState } from "react";
import { DashTopbar } from "../layouts/DashboardLayout";
import PoseFigure from "../components/PoseFigure";
import { ArrowLeft, ArrowRight, Camera, Check, ShieldCheck } from "../components/Icons";
import { sessionService } from "../services/sessionService";
import { useSessionFlow } from "../session";

export default function CameraSetup() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const { mode, exerciseCode, setSessionId } = useSessionFlow();
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState("");
  const checks = [t("camera.c1"), t("camera.c2"), t("camera.c3"), t("camera.c4")];

  const startSession = async () => {
    if (!exerciseCode) {
      setError(t("camera.selectExerciseFirst"));
      return;
    }
    setError("");
    setStarting(true);
    try {
      const response = await sessionService.start({
        mode,
        exercise_code: exerciseCode,
        device_info: navigator.userAgent,
      });
      setSessionId(response.session_id);
      nav("/live");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("camera.startError"));
    } finally {
      setStarting(false);
    }
  };

  return (
    <>
      <Link className="back-link" to={`/exercise?mode=${mode}`}><ArrowLeft />{t("common.back")}</Link>
      <DashTopbar title={t("camera.title")} subtitle={t("camera.desc")} />
      <div className="cam-grid">
        <div className="cam-stage reveal">
          <div className="q-badge"><ShieldCheck width={16} height={16} />{t("camera.quality")} · 92%</div>
          <PoseFigure />
          <div className="cam-frame">
            <span className="cam-corner" style={{ top: -2, left: -2, borderRight: "none", borderBottom: "none" }} />
            <span className="cam-corner" style={{ top: -2, right: -2, borderLeft: "none", borderBottom: "none" }} />
            <span className="cam-corner" style={{ bottom: -2, left: -2, borderRight: "none", borderTop: "none" }} />
            <span className="cam-corner" style={{ bottom: -2, right: -2, borderLeft: "none", borderTop: "none" }} />
          </div>
        </div>

        <div className="stack" style={{ gap: 18 }}>
          <div className="panel reveal">
            <div className="panel-head" style={{ marginBottom: 16 }}><div><h3>{t("camera.checklist")}</h3></div></div>
            <div className="check-list">
              {checks.map((c) => (
                <div className="cl-row" key={c}><span className="cl-ic"><Check width={15} height={15} /></span>{c}</div>
              ))}
            </div>
          </div>
          <div className="panel reveal">
            <div className="panel-head" style={{ marginBottom: 12 }}><div><h3>{t("camera.guidanceTitle")}</h3></div><span className="mi" style={{ width: 38, height: 38, borderRadius: 10, display: "grid", placeItems: "center", background: "var(--good-bg)", color: "var(--accent-text)" }}><Camera width={19} height={19} /></span></div>
            <p style={{ color: "var(--text-2)", fontSize: "0.94rem" }}>{t("camera.guidanceBody")}</p>
          </div>
          {error && <p className="muted" style={{ color: "var(--coral)" }}>{error}</p>}
          <button className="btn btn-primary btn-lg btn-block reveal" onClick={startSession} disabled={starting}>{starting ? t("common.loading") : t("camera.startSession")}<ArrowRight /></button>
        </div>
      </div>
    </>
  );
}
