import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { DashTopbar } from "../layouts/DashboardLayout";
import { Lightbulb, ShieldCheck, History, Plus, Alert } from "../components/Icons";

export default function Report() {
  const { t } = useTranslation();
  const subs = [
    { name: t("landing.romName"), val: "—" },
    { name: t("landing.tempoName"), val: "—" },
    { name: t("landing.stabName"), val: "—" },
  ];

  // dial geometry
  const r = 66, c = 2 * Math.PI * r, pct = 0;

  return (
    <>
      <DashTopbar
        title={t("report.title")}
        subtitle={t("report.savedTo")}
        actions={<><Link className="btn btn-ghost" to="/history"><History />{t("report.viewHistory")}</Link><Link className="btn btn-primary" to="/mode"><Plus />{t("report.newSession")}</Link></>}
      />

      <div className="report-hero reveal" style={{ marginBottom: 18 }}>
        <div className="score-dial">
          <svg width="150" height="150" viewBox="0 0 150 150">
            <circle cx="75" cy="75" r={r} fill="none" stroke="var(--surface-2)" strokeWidth="12" />
            <circle cx="75" cy="75" r={r} fill="none" stroke="var(--chart-line)" strokeWidth="12" strokeLinecap="round"
              strokeDasharray={c} strokeDashoffset={c * (1 - pct)} transform="rotate(-90 75 75)" />
          </svg>
          <div className="num"><b>—</b><span>/ 10</span></div>
        </div>
        <div>
          <span className="eyebrow">{t("report.finalBand")}</span>
          <div style={{ display: "flex", alignItems: "center", gap: 14, margin: "10px 0 14px", flexWrap: "wrap" }}>
            <span className="band good" style={{ fontSize: "1.05rem", padding: "8px 18px" }}>—</span>
            <span className="pill"><ShieldCheck width={16} height={16} style={{ color: "var(--emerald)" }} />{t("report.confidence")}: —</span>
          </div>
          <p className="muted" style={{ maxWidth: "40em" }}>
            {t("dash.placeholderScoring")}
          </p>
        </div>
      </div>

      <div style={{ marginBottom: 8 }}><span className="eyebrow">{t("report.subScores")}</span></div>
      <div className="sub-scores" style={{ marginBottom: 18 }}>
        {subs.map((s) => (
          <div className="sub-score reveal" key={s.name}>
            <div className="ss-top"><b>{s.name}</b><span>{s.val}</span></div>
            <div className="track"><div className="fill good" style={{ width: "0%" }} /></div>
          </div>
        ))}
      </div>

      <div className="dash-grid-2" style={{ marginBottom: 18 }}>
        <div className="panel reveal">
          <div className="panel-head" style={{ marginBottom: 16 }}><div><h3>{t("report.coaching")}</h3></div><span className="mi" style={{ width: 38, height: 38, borderRadius: 10, display: "grid", placeItems: "center", background: "var(--good-bg)", color: "var(--accent-text)" }}><Lightbulb width={19} height={19} /></span></div>
          <div className="feedback-box">
            <div className="fb-label">{t("common.ai")}</div>
            {t("dash.placeholderScoring")}
          </div>
        </div>
        <div className="panel reveal">
          <div className="panel-head" style={{ marginBottom: 16 }}><div><h3>{t("report.errorTags")}</h3></div></div>
          <div className="tags">
            <span className="tag"><span className="sev low" />{t("dash.placeholderScoring")}</span>
          </div>
        </div>
      </div>

      <div className="dash-note reveal"><Alert /><span>{t("report.disclaimer")}</span></div>
    </>
  );
}
