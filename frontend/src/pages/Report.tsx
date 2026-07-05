import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { DashTopbar } from "../layouts/DashboardLayout";
import { Lightbulb, ShieldCheck, History, Plus, Alert } from "../components/Icons";
import InfoTooltip from "../components/InfoTooltip";
import { sessionService } from "../services/sessionService";
import { moduleAService, type ModuleAResult } from "../services/moduleAService";
import type { SessionDTO } from "../types/api";
import { useReveal } from "../useReveal";

// Formats a seconds value to one decimal place, or "—" when unavailable.
function fmtSec(value: number | null | undefined) {
  return value == null ? "—" : `${value.toFixed(1)}s`;
}

function fmtDeg(value: number | null | undefined) {
  return value == null ? "—" : `${value.toFixed(0)}°`;
}

// Maps a band value to its plain-language meaning key in i18n `common`.
function bandMeaningKey(band: string | null): string {
  switch (band) {
    case "good":
      return "common.bandMeaningGood";
    case "fair":
      return "common.bandMeaningFair";
    case "poor":
      return "common.bandMeaningPoor";
    default:
      return "common.bandMeaningInvalid";
  }
}

export default function Report() {
  const { t } = useTranslation();
  const [params] = useSearchParams();
  const sessionId = params.get("session");

  const [session, setSession] = useState<SessionDTO | null>(null);
  const [result, setResult] = useState<ModuleAResult | null>(null);
  const [loading, setLoading] = useState(!!sessionId);
  const [error, setError] = useState("");

  // Re-run reveal animation after async data loads (elements don't exist on initial nav)
  useReveal([result]);

  useEffect(() => {
    if (!sessionId) return;
    let cancelled = false;
    (async () => {
      try {
        const [sessionData, resultData] = await Promise.all([
          sessionService.get(sessionId),
          moduleAService.get(sessionId),
        ]);
        if (cancelled) return;
        setSession(sessionData);
        setResult(resultData);
        console.log(`[Report] Loaded session ${sessionId} — band=${resultData.band}`);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : t("report.loadError"));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [sessionId, t]);

  const band = result?.band ?? null;
  const score = result?.score ?? 0;
  const r = 66,
    c = 2 * Math.PI * r,
    pct = Math.max(0, Math.min(1, score / 10));

  const metricRows = result
    ? [
        {
          label: t("report.validReps"),
          value: `${result.metrics.rep_count}/${result.metrics.target_rep_count}`,
        },
        ...(result.metrics.client_attempted_reps != null
          ? [
              {
                label: t("report.attemptedReps"),
                value: `${result.metrics.client_attempted_reps}`,
              },
            ]
          : []),
        {
          label: t("report.completionTime"),
          value: fmtSec(result.metrics.completion_time_sec),
        },
        {
          label: t("report.avgRepTime"),
          value: fmtSec(result.metrics.avg_rep_time_sec),
        },
        {
          label: t("report.fastestRep"),
          value: fmtSec(result.metrics.fastest_rep_time_sec),
        },
        {
          label: t("report.slowestRep"),
          value: fmtSec(result.metrics.slowest_rep_time_sec),
        },
        {
          label: t("report.kneeRom"),
          value: fmtDeg(result.metrics.knee_rom_deg),
        },
        {
          label: t("report.trunkLean"),
          value: fmtDeg(result.metrics.avg_trunk_lean_deg),
        },
        {
          label: t("report.captureQualityBand"),
          value: t("common." + result.capture_quality_band),
        },
      ]
    : [];

  return (
    <>
      <DashTopbar
        title={t("report.title")}
        subtitle={t("report.savedTo")}
        actions={
          <>
            <Link className="btn btn-ghost" to="/history">
              <History />
              {t("report.viewHistory")}
            </Link>
            <Link className="btn btn-primary" to="/mode">
              <Plus />
              {t("report.newSession")}
            </Link>
          </>
        }
      />

      {!sessionId && <p className="muted">{t("report.noSession")}</p>}
      {sessionId && loading && <p className="muted">{t("report.loading")}</p>}
      {sessionId && !loading && error && (
        <p className="muted" style={{ color: "var(--coral)" }}>
          {error}
        </p>
      )}

      {result && (
        <>
          {result.session_status !== "complete" && (
            <div className="dash-note reveal" style={{ marginBottom: 18 }}>
              <Alert />
              <span>
                {t(
                  result.session_status === "low_confidence"
                    ? "report.lowConfidenceStatus"
                    : "report.incompleteStatus",
                  {
                    valid: result.metrics.rep_count,
                    target: result.metrics.target_rep_count,
                  },
                )}
              </span>
            </div>
          )}

          <div className="report-hero reveal" style={{ marginBottom: 18 }}>
            <div className="score-dial">
              <svg width="150" height="150" viewBox="0 0 150 150">
                <circle
                  cx="75"
                  cy="75"
                  r={r}
                  fill="none"
                  stroke="var(--surface-2)"
                  strokeWidth="12"
                />
                <circle
                  cx="75"
                  cy="75"
                  r={r}
                  fill="none"
                  stroke="var(--chart-line)"
                  strokeWidth="12"
                  strokeLinecap="round"
                  strokeDasharray={c}
                  strokeDashoffset={c * (1 - pct)}
                  transform="rotate(-90 75 75)"
                />
              </svg>
              <div className="num">
                <b>{score.toFixed(1)}</b>
                <span>/ 10</span>
              </div>
            </div>
            <div>
              <span className="eyebrow">{t("report.finalBand")}</span>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                  margin: "10px 0 6px",
                  flexWrap: "wrap",
                }}
              >
                <span
                  className={"band " + band}
                  style={{ fontSize: "1.05rem", padding: "8px 18px" }}
                >
                  {t("common." + band)}
                </span>
                {result.is_partial_score && (
                  <span className="pill">{t("report.partialScoreLabel")}</span>
                )}
                <InfoTooltip text={t(bandMeaningKey(band))} label={t("report.bandInfoLabel")} />
                <span className="pill">
                  <ShieldCheck width={16} height={16} style={{ color: "var(--emerald)" }} />
                  {t("report.captureQualityBand")}: {t("common." + result.capture_quality_band)}
                </span>
                <InfoTooltip
                  text={t("report.captureQualityMeaning")}
                  label={t("report.captureQualityInfoLabel")}
                />
              </div>
              <p className="muted" style={{ maxWidth: "40em", marginBottom: 10 }}>
                {t(bandMeaningKey(band))}
              </p>
              <p className="muted" style={{ maxWidth: "40em" }}>
                {session?.exercise_name}
              </p>
            </div>
          </div>

          <div className="dash-note reveal" style={{ marginBottom: 18 }}>
            <Alert />
            <span>{t("report.nonDiagnosticReminder")}</span>
          </div>

          <div style={{ marginBottom: 8 }}>
            <span className="eyebrow">{t("report.metrics")}</span>
          </div>
          <div className="sub-scores" style={{ marginBottom: 18 }}>
            {metricRows.map((row) => (
              <div className="sub-score reveal" key={row.label}>
                <div className="ss-top">
                  <b>{row.label}</b>
                  <span>{row.value}</span>
                </div>
              </div>
            ))}
          </div>

          <div className="dash-grid-2" style={{ marginBottom: 18 }}>
            <div className="panel reveal">
              <div className="panel-head" style={{ marginBottom: 16 }}>
                <div>
                  <h3>{t("report.coaching")}</h3>
                </div>
                <span
                  className="mi"
                  style={{
                    width: 38,
                    height: 38,
                    borderRadius: 10,
                    display: "grid",
                    placeItems: "center",
                    background: "var(--good-bg)",
                    color: "var(--accent-text)",
                  }}
                >
                  <Lightbulb width={19} height={19} />
                </span>
              </div>
              <div className="feedback-box">
                <div className="fb-label">{t("common.ai")}</div>
                {t("report.coachingBody")}
              </div>
            </div>
            <div className="panel reveal">
              <div className="panel-head" style={{ marginBottom: 16 }}>
                <div>
                  <h3>{t("report.warnings")}</h3>
                </div>
              </div>
              <div className="tags">
                {result.warning_tags.length === 0 && (
                  <span className="tag">
                    <span className="sev low" />
                    {t("report.noWarnings")}
                  </span>
                )}
                {result.warning_tags.map((tag) => (
                  <span className="tag" key={tag}>
                    <span className="sev med" />
                    {t(("report.warn_" + tag) as never, { defaultValue: tag })}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </>
      )}

      {!result && (
        <div className="dash-note reveal">
          <Alert />
          <span>{t("report.disclaimer")}</span>
        </div>
      )}
    </>
  );
}
