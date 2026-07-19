import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { DashTopbar } from "../layouts/DashboardLayout";
import { Lightbulb, ShieldCheck, History, Plus, Alert } from "../components/Icons";
import InfoTooltip from "../components/InfoTooltip";
import { sessionService } from "../services/sessionService";
import { moduleAService, type ModuleAResult } from "../services/moduleAService";
import { moduleBService, type ModuleBResult } from "../services/moduleBService";
import { wbltApi, type WbltLegTrend } from "../services/wblt/wbltApi";
import type { SessionDTO } from "../types/api";
import { useReveal } from "../useReveal";

// Formats a seconds value to one decimal place, or "—" when unavailable.
function fmtSec(value: number | null | undefined) {
  return value == null ? "—" : `${value.toFixed(1)}s`;
}

function fmtDeg(value: number | null | undefined) {
  return value == null ? "—" : `${value.toFixed(0)}°`;
}

// §11 Stage 6: one-line vs-last-session summary for a WBLT leg. `_meaningful`
// is already MDC-suppressed server-side -- a sub-MDC delta reads as "no
// meaningful change" rather than a fabricated up/down signal.
function wbltTrendText(
  t: (key: string, opts?: Record<string, unknown>) => string,
  trend: WbltLegTrend | null | undefined,
) {
  if (!trend) return t("wblt.trendNoPrevious");
  const parts: string[] = [];
  if (trend.distance_delta_cm != null) {
    parts.push(
      trend.distance_meaningful
        ? t("wblt.trendDistanceChanged", {
            sign: trend.distance_delta_cm >= 0 ? "+" : "",
            value: trend.distance_delta_cm.toFixed(1),
          })
        : t("wblt.trendDistanceNoChange"),
    );
  }
  if (trend.angle_delta_deg != null) {
    parts.push(
      trend.angle_meaningful
        ? t("wblt.trendAngleChanged", {
            sign: trend.angle_delta_deg >= 0 ? "+" : "",
            value: trend.angle_delta_deg.toFixed(1),
          })
        : t("wblt.trendAngleNoChange"),
    );
  }
  return parts.length
    ? `${t("wblt.trendVsLast")}: ${parts.join(" · ")}`
    : t("wblt.trendNoPrevious");
}

// Exercise codes graded by Module B's generic registry+plugin pipeline (task.md
// Stage 4.1's architecture) -- exact-match set, not a substring check, to guard
// against any future Module B code colliding with a Module A one.
const MODULE_B_EXERCISE_CODES = new Set(["squat"]);

// Maps a Module B error tag's severity to the existing `.sev` dot CSS class.
function severityClass(severity: string | null): string {
  if (severity === "high") return "high";
  if (severity === "low") return "low";
  return "med";
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
  const [moduleBResult, setModuleBResult] = useState<ModuleBResult | null>(null);
  const [loading, setLoading] = useState(!!sessionId);
  const [error, setError] = useState("");
  // §11 Stage 6: not part of the persisted metrics_json -- computed live from
  // the account's previous WBLT session, so it's fetched separately.
  const [wbltTrend, setWbltTrend] = useState<
    Partial<Record<"left" | "right", WbltLegTrend | null>>
  >({});

  // Re-run reveal animation after async data loads (elements don't exist on initial nav)
  useReveal([result, moduleBResult]);

  useEffect(() => {
    if (!sessionId) return;
    let cancelled = false;
    (async () => {
      try {
        // Session first, since it decides whether this is a Module A or Module B
        // result — the two live on different endpoints with different shapes.
        const sessionData = await sessionService.get(sessionId);
        if (cancelled) return;
        setSession(sessionData);

        if (MODULE_B_EXERCISE_CODES.has(sessionData.exercise_type)) {
          const moduleBData = await moduleBService.get(sessionId);
          if (cancelled) return;
          setModuleBResult(moduleBData);
          console.log(`[Report] Loaded Module B session ${sessionId} — band=${moduleBData.band}`);
        } else {
          const resultData = await moduleAService.get(sessionId);
          if (cancelled) return;
          setResult(resultData);
          console.log(`[Report] Loaded session ${sessionId} — band=${resultData.band}`);
          if (sessionData.exercise_type === "weight_bearing_lunge_test") {
            try {
              const summary = await wbltApi.session(sessionId);
              if (!cancelled) setWbltTrend(summary.trend);
            } catch {
              // Non-fatal: report still renders without the trend row.
            }
          }
        }
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

  // Session's exercise_type decides which of Module A's `result` or Module B's
  // `moduleBResult` is the live one — the two responses have different shapes
  // (Phase 3E Stage 2's lesson: a wrong-panel bug was silent before; see the test).
  const isModuleB = !!session && MODULE_B_EXERCISE_CODES.has(session.exercise_type);
  const band = isModuleB ? (moduleBResult?.band?.toLowerCase() ?? null) : (result?.band ?? null);
  const score = isModuleB ? (moduleBResult?.score ?? 0) : (result?.score ?? 0);
  const captureQualityBandTop = isModuleB
    ? (moduleBResult?.metrics.capture_quality.capture_quality_band ?? null)
    : (result?.capture_quality_band ?? null);
  const r = 66,
    c = 2 * Math.PI * r,
    pct = Math.max(0, Math.min(1, score / 10));

  const isSls = session?.exercise_type?.includes("single_leg");
  const isWblt = session?.exercise_type === "weight_bearing_lunge_test";
  // Migration signal: only SLS rows from the both-legs rebuild carry `perLeg`.
  // Older single-leg rows (pre-rebuild) fall through to the legacy metricRows below.
  const perLeg = result?.metrics.perLeg;
  const hasPerLeg = !!(perLeg && (perLeg.left || perLeg.right));
  const wbltLegs = result?.metrics.legs;
  const hasWbltLegs = !!(wbltLegs && (wbltLegs.right || wbltLegs.left));
  const symmetry = result?.metrics.symmetry;

  // Module B: the three rule sub-scores broken out, plus the ML/confidence/capture
  // figures the checklist asks for — reuses the same "sub-score" row shape as
  // Module A's metricRows below, just from moduleBResult instead of result.
  const moduleBRows = moduleBResult
    ? [
        {
          label: t("report.reps"),
          value: session?.rep_count != null ? `${session.rep_count}` : "—",
        },
        ...moduleBResult.metrics.rule_subscores.map((s) => ({
          label: t(("moduleB.subscore_" + s.code) as never, { defaultValue: s.code }),
          value: s.score != null ? `${s.score.toFixed(1)}/10` : "—",
        })),
        {
          label: t("report.mlPred"),
          value:
            moduleBResult.metrics.ml_score != null
              ? `${moduleBResult.metrics.ml_score.toFixed(1)}/10`
              : "—",
        },
        {
          label: t("report.confidence"),
          value:
            moduleBResult.confidence != null
              ? `${Math.round(moduleBResult.confidence * 100)}%`
              : "—",
        },
        {
          label: t("report.captureQualityBand"),
          value: t("common." + moduleBResult.metrics.capture_quality.capture_quality_band),
        },
      ]
    : [];

  const metricRows =
    result && session && !isWblt
      ? isSls
        ? // Single-Leg Stance metrics
          [
            {
              label: t("report.holdDuration"),
              value: fmtSec(result.metrics.hold_duration_sec),
            },
            {
              label: t("report.maxSway"),
              value:
                result.metrics.max_sway_m != null
                  ? `${(result.metrics.max_sway_m * 100).toFixed(0)}cm`
                  : "—",
            },
            {
              label: t("report.captureQualityBand"),
              value: t("common." + result.capture_quality_band),
            },
          ]
        : // Sit-to-Stand metrics
          [
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

      {(result || moduleBResult) && (
        <>
          {!isModuleB && result && result.session_status !== "complete" && (
            <div className="dash-note reveal" style={{ marginBottom: 18 }}>
              <Alert />
              <span>
                {result.session_status === "low_confidence"
                  ? t("report.lowConfidenceStatus")
                  : isWblt
                    ? t("report.incompleteWbltStatus")
                    : isSls
                      ? t("report.incompleteSlsStatus", {
                          duration: (
                            result.metrics.best_hold_sec ??
                            result.metrics.hold_duration_sec ??
                            0
                          ).toFixed(1),
                          target:
                            result.metrics.maxHoldSeconds ?? result.metrics.target_hold_sec ?? 45,
                        })
                      : t("report.incompleteStatus", {
                          valid: result.metrics.rep_count,
                          target: result.metrics.target_rep_count,
                        })}
              </span>
            </div>
          )}

          {isModuleB && moduleBResult?.metrics.placeholder_model_notice && (
            <div className="dash-note reveal" style={{ marginBottom: 18 }}>
              <Alert />
              <span>
                {t("report.moduleBPlaceholderNotice", {
                  version: moduleBResult.model_version,
                  exercise: session?.exercise_name ?? "",
                })}
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
                {!isModuleB && result?.is_partial_score && (
                  <span className="pill">{t("report.partialScoreLabel")}</span>
                )}
                <InfoTooltip text={t(bandMeaningKey(band))} label={t("report.bandInfoLabel")} />
                <span className="pill">
                  <ShieldCheck width={16} height={16} style={{ color: "var(--emerald)" }} />
                  {t("report.captureQualityBand")}: {t("common." + captureQualityBandTop)}
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
            <span className="eyebrow">
              {t(
                isModuleB
                  ? "report.squatMetrics"
                  : isWblt
                    ? "report.wbltMetrics"
                    : isSls
                      ? "report.slsMetrics"
                      : "report.metrics",
              )}
            </span>
          </div>

          {isModuleB ? (
            <div className="sub-scores" style={{ marginBottom: 18 }}>
              {moduleBRows.map((row) => (
                <div className="sub-score reveal" key={row.label}>
                  <div className="ss-top">
                    <b>{row.label}</b>
                    <span>{row.value}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : hasWbltLegs ? (
            <>
              <div className="dash-grid-2" style={{ marginBottom: 18 }}>
                {(["right", "left"] as const).map((leg) => {
                  const m = wbltLegs?.[leg];
                  if (!m) return null;
                  return (
                    <div className="panel reveal" key={leg}>
                      <div className="panel-head" style={{ marginBottom: 18 }}>
                        <h3>{t(leg === "right" ? "wblt.legRight" : "wblt.legLeft")}</h3>
                        {m.band && (
                          <span className={"band " + m.band.toLowerCase()}>
                            {t("common." + m.band.toLowerCase())}
                          </span>
                        )}
                      </div>
                      {m.best_distance_cm != null ? (
                        <div className="sls-metric-row">
                          <span className="sls-metric-label">{t("wblt.legBestDistanceLabel")}</span>
                          <span className="sls-metric-value">{m.best_distance_cm} cm</span>
                        </div>
                      ) : (
                        <p className="muted" style={{ fontSize: "0.82rem" }}>
                          {t("wblt.floorFlagMessage")}
                        </p>
                      )}
                      <div className="sls-metric-row">
                        <span className="sls-metric-label">{t("wblt.angleResultLabel")}</span>
                        <span className="sls-metric-value">
                          {m.leg_angle_deg != null ? `${m.leg_angle_deg.toFixed(1)}°` : "—"}
                        </span>
                      </div>
                      <p className="muted" style={{ fontSize: "0.82rem", marginTop: 10 }}>
                        {wbltTrendText(t, wbltTrend[leg])}
                      </p>
                    </div>
                  );
                })}
                <div className="panel reveal">
                  <div className="panel-head" style={{ marginBottom: 18 }}>
                    <h3>{t("wblt.symmetryTitle")}</h3>
                  </div>
                  <p className="muted" style={{ fontSize: "0.85rem" }}>
                    {symmetry?.status === "asymmetry_flag"
                      ? t("wblt.symmetryFlag")
                      : symmetry?.status === "symmetric"
                        ? t("wblt.symmetrySymmetric")
                        : "—"}
                  </p>
                  <div className="sls-metric-row" style={{ marginTop: 12 }}>
                    <span className="sls-metric-label">{t("report.captureQualityBand")}</span>
                    <span className="sls-metric-value">
                      {t("common." + result?.capture_quality_band)}
                    </span>
                  </div>
                </div>
              </div>

              <div className="panel reveal" style={{ marginBottom: 18 }}>
                <div className="panel-head" style={{ marginBottom: 14 }}>
                  <h3>{t("wblt.attemptsTableTitle")}</h3>
                </div>
                <div className="tbl-scroll">
                  <table className="tbl">
                    <thead>
                      <tr>
                        <th>{t("wblt.legLabel")}</th>
                        <th>{t("wblt.attemptLabel")}</th>
                        <th>{t("wblt.thDistance")}</th>
                        <th>{t("wblt.thTouched")}</th>
                        <th>{t("wblt.thAngle")}</th>
                        <th>{t("wblt.thValidForm")}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(["right", "left"] as const).flatMap((leg) => {
                        const m = wbltLegs?.[leg];
                        if (!m) return [];
                        return m.attempts.map((a, i) => {
                          const validForm = a.attempt_valid && !a.heel_lift_detected;
                          return (
                            <tr key={`${leg}-${i}`}>
                              <td>{t(leg === "right" ? "wblt.legRight" : "wblt.legLeft")}</td>
                              <td>{i + 1}</td>
                              <td>{a.target_distance_cm} cm</td>
                              <td>{t(a.valid_touch ? "wblt.touchYes" : "wblt.touchNo")}</td>
                              <td>
                                {a.theta_peak_deg != null ? `${a.theta_peak_deg.toFixed(1)}°` : "—"}
                              </td>
                              <td>
                                {a.heel_lift_detected ? (
                                  <span className="band poor">{t("wblt.heelLifted")}</span>
                                ) : validForm ? (
                                  <span className="band good">{t("common.good")}</span>
                                ) : (
                                  <span className="band poor">{t("common.invalid")}</span>
                                )}
                              </td>
                            </tr>
                          );
                        });
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : hasPerLeg ? (
            <div className="dash-grid-2" style={{ marginBottom: 18 }}>
              {(["right", "left"] as const).map((leg) => {
                const m = perLeg?.[leg];
                if (!m) return null;
                return (
                  <div className="panel reveal" key={leg}>
                    <div className="panel-head" style={{ marginBottom: 18 }}>
                      <h3>{t(leg === "right" ? "sls.legRight" : "sls.legLeft")}</h3>
                      <span className={"band " + m.band}>{t("common." + m.band)}</span>
                    </div>
                    <div className="sls-metric-row">
                      <span className="sls-metric-label">{t("sls.bestHold")}</span>
                      <span className="sls-metric-value">{fmtSec(m.holdSeconds)}</span>
                    </div>
                    <div className="sls-metric-row">
                      <span className="sls-metric-label">{t("sls.stabilityScore")}</span>
                      <span className="sls-metric-value">{m.stabilityScore.toFixed(1)}/10</span>
                    </div>
                    <div className="sls-metric-row">
                      <span className="sls-metric-label">{t("sls.combinedScore")}</span>
                      <span className="sls-metric-value">{m.combinedScore.toFixed(1)}/10</span>
                    </div>
                    <p className="muted" style={{ fontSize: "0.82rem", marginTop: 12 }}>
                      {t("sls.stopReasonLabel")}: {t("sls.stopReason_" + m.stopReason)}
                    </p>
                  </div>
                );
              })}
              <div className="panel reveal">
                <div className="panel-head" style={{ marginBottom: 18 }}>
                  <h3>{t("sls.perLegHeading")}</h3>
                </div>
                <div className="sls-metric-row">
                  <span className="sls-metric-label">{t("sls.lrDifference")}</span>
                  <span className="sls-metric-value">
                    {fmtSec(result?.metrics.leftRightHoldDifferenceSeconds)}
                  </span>
                </div>
                <div className="sls-metric-row">
                  <span className="sls-metric-label">{t("sls.supportUsed")}</span>
                  <span className="sls-metric-value">
                    {result?.metrics.usedSupport
                      ? t(
                          "sls.support" +
                            (result.metrics.usedSupport === "none"
                              ? "None"
                              : result.metrics.usedSupport === "slight"
                                ? "Slight"
                                : "Full"),
                        )
                      : "—"}
                  </span>
                </div>
                <div className="sls-metric-row">
                  <span className="sls-metric-label">{t("report.captureQualityBand")}</span>
                  <span className="sls-metric-value">
                    {t("common." + result?.capture_quality_band)}
                  </span>
                </div>
              </div>
            </div>
          ) : (
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
          )}

          {isModuleB ? (
            <div className="panel reveal" style={{ marginBottom: 18 }}>
              <div className="panel-head" style={{ marginBottom: 16 }}>
                <h3>{t("report.errorTags")}</h3>
              </div>
              <div className="tags">
                {moduleBResult?.error_tags.length === 0 && (
                  <span className="tag">
                    <span className="sev low" />
                    {t("report.noWarnings")}
                  </span>
                )}
                {moduleBResult?.error_tags.map((tag) => (
                  <span className="tag" key={tag.tag}>
                    <span className={"sev " + severityClass(tag.severity)} />
                    {t(("moduleB.tag_" + tag.tag) as never, { defaultValue: tag.tag })}
                  </span>
                ))}
              </div>
            </div>
          ) : (
            result && (
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
            )
          )}
        </>
      )}

      {!result && !moduleBResult && (
        <div className="dash-note reveal">
          <Alert />
          <span>{t("report.disclaimer")}</span>
        </div>
      )}
    </>
  );
}
