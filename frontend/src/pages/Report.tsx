import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { DashTopbar } from "../layouts/DashboardLayout";
import {
  Lightbulb,
  ShieldCheck,
  History,
  Plus,
  Alert,
  Info,
  Check,
  CirclePlus,
  ArrowLeft,
  Redo,
  ChevronDown,
} from "../components/Icons";
import InfoTooltip from "../components/InfoTooltip";
import GlossaryTerm from "../components/GlossaryTerm";
import SubScoreBarChart, { type SubScoreDatum } from "../components/charts/SubScoreBarChart";
import { severityClass } from "../components/charts/dashboardChartUtils";
import { sessionService } from "../services/sessionService";
import {
  moduleAService,
  type ModuleAResult,
  type SlsLegTrend,
  type StsTrend,
} from "../services/moduleAService";
import { moduleBService, type ModuleBResult, type SquatTrend } from "../services/moduleBService";
import { wbltApi, type WbltLegTrend } from "../services/wblt/wbltApi";
import type { SlsLeg } from "../services/sls/slsApi";
import type { SessionDTO } from "../types/api";
import { useSessionFlow } from "../session";

// Formats a seconds value to one decimal place, or "—" when unavailable.
function fmtSec(value: number | null | undefined) {
  return value == null ? "—" : `${value.toFixed(1)}s`;
}

function fmtDeg(value: number | null | undefined) {
  return value == null ? "—" : `${value.toFixed(0)}°`;
}

// WBLT trend text. `_meaningful` is already MDC-suppressed server-side.
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

// STS/SLS trend text. No MDC threshold exists, so plain deltas are shown directly.
/** One "vs last session" delta, worded by DIRECTION rather than by a signed number.
 *
 * The previous form interpolated a sign into "score {{sign}}{{value}}/10", so a delta of
 * -1.0 rendered as "score -1.0/10" — which reads as an absolute score of minus one, not
 * as a drop of one point. Direction words also cannot be composed from a sign across
 * languages, so each direction gets its own key. */
function deltaPart(
  t: (key: string, opts?: Record<string, unknown>) => string,
  baseKey: string,
  delta: number,
  digits: number,
) {
  const magnitude = Math.abs(delta).toFixed(digits);
  if (Number(magnitude) === 0) return t(`${baseKey}Same`);
  return t(delta > 0 ? `${baseKey}Up` : `${baseKey}Down`, { value: magnitude });
}

function stsTrendText(
  t: (key: string, opts?: Record<string, unknown>) => string,
  trend: StsTrend | null | undefined,
) {
  if (!trend) return t("report.trendNoPrevious");
  const parts: string[] = [];
  if (trend.score_delta != null) {
    parts.push(deltaPart(t, "report.trendScore", trend.score_delta, 1));
  }
  if (trend.completion_time_delta_sec != null) {
    parts.push(deltaPart(t, "report.trendTime", trend.completion_time_delta_sec, 1));
  }
  return parts.length
    ? `${t("report.trendVsLast")}: ${parts.join(" · ")}`
    : t("report.trendNoPrevious");
}

function slsLegTrendText(
  t: (key: string, opts?: Record<string, unknown>) => string,
  trend: SlsLegTrend | null | undefined,
) {
  if (!trend) return t("report.trendNoPrevious");
  const parts: string[] = [];
  if (trend.hold_delta_sec != null) {
    parts.push(deltaPart(t, "report.trendHold", trend.hold_delta_sec, 1));
  }
  if (trend.score_delta != null) {
    parts.push(deltaPart(t, "report.trendScore", trend.score_delta, 1));
  }
  return parts.length
    ? `${t("report.trendVsLast")}: ${parts.join(" · ")}`
    : t("report.trendNoPrevious");
}

// Squat trend text: score and completed reps, with no MDC-style claim.
function squatTrendText(
  t: (key: string, opts?: Record<string, unknown>) => string,
  trend: SquatTrend | null | undefined,
) {
  if (!trend) return t("report.trendNoPrevious");
  const parts: string[] = [];
  if (trend.score_delta != null) {
    parts.push(deltaPart(t, "report.trendScore", trend.score_delta, 1));
  }
  if (trend.rep_count_delta != null) {
    parts.push(deltaPart(t, "report.trendReps", trend.rep_count_delta, 0));
  }
  return parts.length
    ? `${t("report.trendVsLast")}: ${parts.join(" · ")}`
    : t("report.trendNoPrevious");
}

// Shared trend line with the same "vs last session" tooltip for every exercise.
function TrendLine({
  t,
  text,
  style,
}: {
  t: (key: string, opts?: Record<string, unknown>) => string;
  text: string;
  style?: React.CSSProperties;
}) {
  return (
    <p
      className="muted"
      style={{ fontSize: "0.82rem", display: "flex", alignItems: "center", gap: 4, ...style }}
    >
      {text}
      <InfoTooltip text={t("report.trendInfoText")} label={t("report.trendInfoLabel")} />
    </p>
  );
}

// Exercise codes graded by Module B's generic registry+plugin pipeline.
const MODULE_B_EXERCISE_CODES = new Set(["squat"]);

// Severity uses both icon shape and colour.
function severityIcon(severity: string | null) {
  const cls = severityClass(severity);
  if (cls === "high") return Alert;
  if (cls === "low") return CirclePlus;
  return Info;
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
  const nav = useNavigate();
  const [params] = useSearchParams();
  const sessionId = params.get("session");
  const { setMode, setExerciseCode } = useSessionFlow();

  const [session, setSession] = useState<SessionDTO | null>(null);
  const [result, setResult] = useState<ModuleAResult | null>(null);
  const [moduleBResult, setModuleBResult] = useState<ModuleBResult | null>(null);
  // The score a set must reach to band Good. Read from the exercise's own band_policy
  // so the report can never disagree with the backend's actual cut (X7).
  const [passMark, setPassMark] = useState<number | null>(null);
  const [loading, setLoading] = useState(!!sessionId);
  const [error, setError] = useState("");
  // Collapsed technical details: full prediction/probability stays secondary.
  const [detailsOpen, setDetailsOpen] = useState(false);
  // WBLT trend is fetched separately from the persisted metrics_json.
  const [wbltTrend, setWbltTrend] = useState<
    Partial<Record<"left" | "right", WbltLegTrend | null>>
  >({});

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
          try {
            const config = await moduleBService.config(sessionData.exercise_type);
            const policy = (config.exercise as Record<string, unknown>)?.band_policy as
              { decision_threshold?: number } | undefined;
            if (!cancelled && typeof policy?.decision_threshold === "number") {
              setPassMark(policy.decision_threshold);
            }
          } catch {
            // Non-fatal: the report simply renders without the pass-mark sentence.
          }
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

  // Retry must use this report's session, not whatever the flow context last held.
  function handleRetry() {
    if (!session) return;
    setMode(session.mode === "rehab" ? "rehab" : "functional");
    setExerciseCode(session.exercise_code);
    nav("/instructions");
  }

  // exercise_type decides which result payload is active; Module A/B shapes differ.
  const isModuleB = !!session && MODULE_B_EXERCISE_CODES.has(session.exercise_type);
  const band = isModuleB ? (moduleBResult?.band?.toLowerCase() ?? null) : (result?.band ?? null);
  const score = isModuleB ? (moduleBResult?.score ?? 0) : (result?.score ?? 0);
  const captureQualityBandTop = isModuleB
    ? (moduleBResult?.metrics.capture_quality.capture_quality_band ?? null)
    : (result?.capture_quality_band ?? null);
  const r = 66,
    c = 2 * Math.PI * r,
    pct = Math.max(0, Math.min(1, score / 10));

  // Per-rep verdicts: how many reps counted, and why the rest did not.
  const repSummaries = moduleBResult?.metrics.per_rep_summaries ?? [];
  const hasRepVerdicts = repSummaries.some((rep) => rep.counted_good !== undefined);
  const countedReps = repSummaries.filter((rep) => rep.counted_good).length;
  const rejectedReps = repSummaries.length - countedReps;
  // One entry per fault kind with a count, e.g. "heels lifted ×3".
  const rejectionCounts = repSummaries.reduce<Record<string, number>>((acc, rep) => {
    for (const tag of rep.failed_gates ?? []) acc[tag] = (acc[tag] ?? 0) + 1;
    return acc;
  }, {});
  // A rep counts only if it clears the gates AND the model's threshold, so a rep can be
  // rejected with no named fault at all. Those were previously invisible: the header said
  // "8 didn't count" above only 6 reasons. Counted by REP (a rep can trip two gates, which
  // would double-count in `rejectionCounts`).
  const modelOnlyRejections = repSummaries.filter(
    (rep) => rep.counted_good === false && (rep.failed_gates ?? []).length === 0,
  ).length;

  const isSls = session?.exercise_type?.includes("single_leg");
  const isWblt = session?.exercise_type === "weight_bearing_lunge_test";
  // Migration signal: only SLS rows from the both-legs rebuild carry `perLeg`.
  // Older single-leg rows (pre-rebuild) fall through to the legacy metricRows below.
  const perLeg = result?.metrics.perLeg;
  const hasPerLeg = !!(perLeg && (perLeg.left || perLeg.right));
  const wbltLegs = result?.metrics.legs;
  const hasWbltLegs = !!(wbltLegs && (wbltLegs.right || wbltLegs.left));
  const symmetry = result?.metrics.symmetry;
  // SLS trend is per-leg; STS trend is a single object.
  const slsTrend = hasPerLeg
    ? (result?.trend as Partial<Record<SlsLeg, SlsLegTrend | null>> | undefined)
    : undefined;

  // Module B summary rows. Rule sub-scores live in the chart below; ML details
  // stay in the collapsed technical section.
  const moduleBRows: { label: string; value: string; info?: string }[] = moduleBResult
    ? [
        {
          // Attempts are all segmented reps, including reps that did not count.
          label: t("report.attempts"),
          value: session?.rep_count != null ? `${session.rep_count}` : "—",
          info: t("report.attemptsMeaning"),
        },
        // Valid reps counted toward the score. Only shown when per-rep verdicts exist.
        ...(hasRepVerdicts
          ? [
              {
                label: t("report.validReps"),
                value: `${countedReps}`,
                info: t("glossary.validRep.def"),
              },
            ]
          : []),
        ...(session?.target_rep_count != null
          ? [
              {
                label: t("report.repTarget"),
                value: t("report.repTargetValue", { target: session.target_rep_count }),
              },
            ]
          : []),
        {
          label: t("report.confidence"),
          value:
            moduleBResult.confidence != null
              ? `${Math.round(moduleBResult.confidence * 100)}%`
              : "—",
          info: t("report.confidenceMeaning"),
        },
        {
          label: t("report.captureQualityBand"),
          value: t("common." + moduleBResult.metrics.capture_quality.capture_quality_band),
        },
      ]
    : [];

  // Rule sub-scores for the interactive chart and hover tooltips.
  const subScoreChartData: SubScoreDatum[] = moduleBResult
    ? moduleBResult.metrics.rule_subscores.map((s) => ({
        code: s.code,
        label: t(("moduleB.subscore_" + s.code) as never, { defaultValue: s.code }),
        score: s.score,
        meaning:
          s.code === "rom_completeness"
            ? t("glossary.rom.def")
            : s.code === "tempo_consistency"
              ? t("report.tempoConsistencyMeaning")
              : s.code === "stability_control"
                ? t("report.stabilityControlMeaning")
                : "",
      }))
    : [];

  // Collapsed technical figures for users who want model details.
  const technicalDetailsRows: { label: string; value: string }[] = moduleBResult
    ? [
        {
          label: t("report.mlPred"),
          value:
            moduleBResult.metrics.ml_score != null
              ? `${moduleBResult.metrics.ml_score.toFixed(1)}/10`
              : "—",
        },
        {
          label: t("report.ruleScore"),
          value:
            moduleBResult.metrics.rule_score != null
              ? `${moduleBResult.metrics.rule_score.toFixed(1)}/10`
              : "—",
        },
        {
          label: t("report.fusionWeights"),
          value: t("report.fusionWeightsValue", {
            rule: Math.round(moduleBResult.metrics.fusion_weights.w_rule * 100),
            ml: Math.round(moduleBResult.metrics.fusion_weights.w_ml * 100),
          }),
        },
        {
          label: t("report.modelVersion"),
          value: moduleBResult.model_version ?? "—",
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
              // Reuse the shared glossary definition for "valid rep".
              info: t("glossary.validRep.def"),
            },
            ...(result.metrics.client_attempted_reps != null
              ? [
                  {
                    label: t("report.attemptedReps"),
                    value: `${result.metrics.client_attempted_reps}`,
                    info: t("report.attemptedRepsMeaning"),
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
              info: t("report.kneeRomMeaning"),
            },
            {
              label: t("report.trunkLean"),
              value: fmtDeg(result.metrics.avg_trunk_lean_deg),
              info: t("report.trunkLeanMeaning"),
            },
            {
              label: t("report.captureQualityBand"),
              value: t("common." + result.capture_quality_band),
            },
          ]
      : [];

  return (
    <>
      {/* True history-back because Report can be reached from several routes. */}
      <button type="button" className="back-link" onClick={() => nav(-1)}>
        <ArrowLeft />
        {t("common.back")}
      </button>
      <DashTopbar
        title={t("report.title")}
        subtitle={t("report.savedTo")}
        actions={
          <>
            <Link className="btn btn-ghost" to="/history">
              <History />
              {t("report.viewHistory")}
            </Link>
            {session && (
              <button type="button" className="btn btn-primary" onClick={handleRetry}>
                <Redo />
                {t("report.retryExercise")}
              </button>
            )}
            <Link className="btn btn-ghost" to="/mode">
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
            <div className="dash-note" style={{ marginBottom: 18 }}>
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
            <div className="dash-note" style={{ marginBottom: 18 }}>
              <Alert />
              <span>
                {t("report.moduleBPlaceholderNotice", {
                  version: moduleBResult.model_version,
                  exercise: session?.exercise_name ?? "",
                })}
              </span>
            </div>
          )}

          <div className="report-hero" style={{ marginBottom: 18 }}>
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
                <GlossaryTerm id="captureQuality" />
                {/* Prominent non-diagnostic reminder beside the score band. */}
                <span className="pill non-diagnostic-badge">
                  <Alert width={14} height={14} />
                  {t("report.nonDiagnosticReminder")}
                </span>
              </div>
              <p className="muted" style={{ maxWidth: "40em", marginBottom: 10 }}>
                {t(bandMeaningKey(band))}
              </p>
              {/* Say WHY, in one line. The score and the band can legitimately disagree:
                  heel rise is a rule-only signal that is not in the ML feature vector, so
                  the model literally cannot see it. Explaining that beats faking
                  agreement by adjusting the number. */}
              {isModuleB && hasRepVerdicts && (
                <p className="muted" style={{ maxWidth: "40em", marginBottom: 10 }}>
                  {passMark != null && (
                    <>{t("report.passMarkNote", { passMark: passMark.toFixed(1) })} </>
                  )}
                  {rejectedReps > 0
                    ? t("report.bandReasonWithFaults", {
                        counted: countedReps,
                        total: repSummaries.length,
                      })
                    : t("report.bandReasonAllClean", { total: repSummaries.length })}
                </p>
              )}
              <p className="muted" style={{ maxWidth: "40em" }}>
                {session?.exercise_name}
              </p>
            </div>
          </div>

          {/* Coaching and issue tags appear directly after the score. */}
          {isModuleB ? (
            <div className="dash-grid-2" style={{ marginBottom: 18 }}>
              <div className="panel panel--coaching">
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
                  <div className="fb-label">
                    {moduleBResult?.feedback?.feedback_source === "llm"
                      ? t("report.feedbackSourceLlm")
                      : t("report.feedbackSourceTemplate")}
                  </div>
                  {/* Render structured feedback as summary + tips, never raw markdown. */}
                  {moduleBResult?.feedback?.rewritten_feedback_structured ? (
                    <>
                      <p>{moduleBResult.feedback.rewritten_feedback_structured.summary}</p>
                      {moduleBResult.feedback.rewritten_feedback_structured.tips.length > 0 && (
                        <ul>
                          {moduleBResult.feedback.rewritten_feedback_structured.tips.map(
                            (tip, index) => (
                              <li key={index}>{tip}</li>
                            ),
                          )}
                        </ul>
                      )}
                    </>
                  ) : (
                    <p>{t("report.feedbackUnavailable")}</p>
                  )}
                </div>
              </div>
              <div className="panel panel--errors">
                <div className="panel-head" style={{ marginBottom: 16 }}>
                  <h3>{t("report.errorTags")}</h3>
                  {/* Issue count badge. */}
                  {!!moduleBResult?.error_tags.length && (
                    <span className="pill">
                      {t("report.tagsCount", { count: moduleBResult.error_tags.length })}
                    </span>
                  )}
                </div>
                <div className="tags">
                  {moduleBResult?.error_tags.length === 0 && (
                    <span className="tag">
                      <span className="sev ok">
                        <Check width={11} height={11} />
                      </span>
                      {t("report.noWarnings")}
                    </span>
                  )}
                  {moduleBResult?.error_tags.map((tag) => {
                    const SevIcon = severityIcon(tag.severity);
                    return (
                      <span className="tag" key={tag.tag}>
                        <span className={"sev " + severityClass(tag.severity)}>
                          <SevIcon width={11} height={11} />
                        </span>
                        {t(("moduleB.tag_" + tag.tag) as never, { defaultValue: tag.tag })}
                      </span>
                    );
                  })}
                </div>
                {/* Severity legend shown only when issue tags exist. */}
                {!!moduleBResult?.error_tags.length && (
                  <div className="sev-legend">
                    <span className="sev-legend-item">
                      <span className="sev high">
                        <Alert width={11} height={11} />
                      </span>
                      {t("report.severityHigh")}
                    </span>
                    <span className="sev-legend-item">
                      <span className="sev med">
                        <Info width={11} height={11} />
                      </span>
                      {t("report.severityMed")}
                    </span>
                    <span className="sev-legend-item">
                      <span className="sev low">
                        <CirclePlus width={11} height={11} />
                      </span>
                      {t("report.severityLow")}
                    </span>
                  </div>
                )}
              </div>
            </div>
          ) : (
            result && (
              <div className="panel panel--coaching" style={{ marginBottom: 18 }}>
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
                {result.warning_tags.length === 0 ? (
                  <div className="feedback-box">
                    <div className="fb-label">{t("report.coachingTipLabel")}</div>
                    {t("report.coachingBody")}
                  </div>
                ) : (
                  <div className="check-list">
                    {result.warning_tags.map((tag) => (
                      <div className="check-item" key={tag}>
                        <div className="check-item-head">
                          <span className="sev med">
                            <Info width={11} height={11} />
                          </span>
                          <b>{t(("report.warn_" + tag) as never, { defaultValue: tag })}</b>
                        </div>
                        <p className="muted check-item-tip">
                          {t(("report.tip_" + tag) as never, { defaultValue: "" })}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          )}

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
            <>
              {/* Interactive rule sub-score chart. */}
              {subScoreChartData.length > 0 && (
                <div className="panel" style={{ marginBottom: 14 }}>
                  <SubScoreBarChart
                    data={subScoreChartData}
                    exerciseType={session?.exercise_type}
                  />
                </div>
              )}
              <div className="sub-scores" style={{ marginBottom: 8 }}>
                {moduleBRows.map((row) => (
                  <div className="sub-score" key={row.label}>
                    <div className="ss-top">
                      <b>
                        {row.label}
                        {row.info && <InfoTooltip text={row.info} label={row.label} />}
                      </b>
                      <span>{row.value}</span>
                    </div>
                  </div>
                ))}
              </div>
              {/* Rep breakdown: which reps counted and, for those that didn't, the named
                  fault. Reuses the report's own tag i18n keys so the wording matches the
                  Error tags panel and the live "didn't count" note verbatim. */}
              {hasRepVerdicts && rejectedReps > 0 && (
                <div className="rep-breakdown" style={{ marginBottom: 18 }}>
                  <b>
                    {t("report.repBreakdown", {
                      counted: countedReps,
                      rejected: rejectedReps,
                    })}
                    <GlossaryTerm id="validRep" />
                  </b>
                  <ul>
                    {Object.entries(rejectionCounts)
                      .sort(([a], [b]) => a.localeCompare(b))
                      .map(([tag, count]) => (
                        <li key={tag}>
                          {t(("moduleB.tag_" + tag) as never, { defaultValue: tag })}
                          {" ×"}
                          {count}
                        </li>
                      ))}
                    {/* Without this the counts don't add up: reps the model rejected with
                        no named fault were simply missing from the list. */}
                    {modelOnlyRejections > 0 && (
                      <li>
                        {t("report.modelOnlyRejection")}
                        {" ×"}
                        {modelOnlyRejections}
                      </li>
                    )}
                  </ul>
                  <p className="muted" style={{ fontSize: "0.82rem", marginTop: 10 }}>
                    {t("report.liveCountProvisional")}
                  </p>
                </div>
              )}
              <TrendLine
                t={t}
                text={squatTrendText(t, moduleBResult?.trend)}
                style={{ marginBottom: 18 }}
              />
              {/* Collapsed technical model details. */}
              {technicalDetailsRows.length > 0 && (
                <div className="tech-details" style={{ marginBottom: 18 }}>
                  <button
                    type="button"
                    className="tech-details-toggle"
                    onClick={() => setDetailsOpen((o) => !o)}
                    aria-expanded={detailsOpen}
                  >
                    <ChevronDown
                      width={16}
                      height={16}
                      style={{
                        transform: detailsOpen ? "rotate(180deg)" : undefined,
                        transition: "transform 0.2s var(--ease)",
                      }}
                    />
                    {detailsOpen
                      ? t("report.technicalDetailsHide")
                      : t("report.technicalDetailsShow")}
                  </button>
                  {detailsOpen && (
                    <div className="sub-scores" style={{ marginTop: 14 }}>
                      {technicalDetailsRows.map((row) => (
                        <div className="sub-score" key={row.label}>
                          <div className="ss-top">
                            <b>{row.label}</b>
                            <span>{row.value}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </>
          ) : hasWbltLegs ? (
            <>
              <div className="dash-grid-2" style={{ marginBottom: 18 }}>
                {(["right", "left"] as const).map((leg) => {
                  const m = wbltLegs?.[leg];
                  if (!m) return null;
                  return (
                    <div className="panel" key={leg}>
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
                        <span className="sls-metric-label">
                          {t("wblt.angleResultLabel")}
                          <GlossaryTerm id="dorsiflexion" />
                        </span>
                        <span className="sls-metric-value">
                          {m.leg_angle_deg != null ? `${m.leg_angle_deg.toFixed(1)}°` : "—"}
                        </span>
                      </div>
                      <TrendLine
                        t={t}
                        text={wbltTrendText(t, wbltTrend[leg])}
                        style={{ marginTop: 10 }}
                      />
                    </div>
                  );
                })}
                <div className="panel">
                  <div className="panel-head" style={{ marginBottom: 18 }}>
                    <h3>
                      {t("wblt.symmetryTitle")}
                      <GlossaryTerm id="symmetryIndex" />
                    </h3>
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

              <div className="panel" style={{ marginBottom: 18 }}>
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
                        <th>
                          {t("wblt.thValidForm")}
                          <GlossaryTerm id="validRep" />
                        </th>
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
                  <div className="panel" key={leg}>
                    <div className="panel-head" style={{ marginBottom: 18 }}>
                      <h3>{t(leg === "right" ? "sls.legRight" : "sls.legLeft")}</h3>
                      <span className={"band " + m.band}>{t("common." + m.band)}</span>
                    </div>
                    <div className="sls-metric-row">
                      <span className="sls-metric-label">
                        {t("sls.bestHold")}
                        <GlossaryTerm id="holdTime" />
                      </span>
                      <span className="sls-metric-value">{fmtSec(m.holdSeconds)}</span>
                    </div>
                    <div className="sls-metric-row">
                      <span className="sls-metric-label">
                        {t("sls.stabilityScore")}
                        <GlossaryTerm id="stability" />
                      </span>
                      <span className="sls-metric-value">{m.stabilityScore.toFixed(1)}/10</span>
                    </div>
                    <div className="sls-metric-row">
                      <span className="sls-metric-label">{t("sls.combinedScore")}</span>
                      <span className="sls-metric-value">{m.combinedScore.toFixed(1)}/10</span>
                    </div>
                    <p className="muted" style={{ fontSize: "0.82rem", marginTop: 12 }}>
                      {t("sls.stopReasonLabel")}: {t("sls.stopReason_" + m.stopReason)}
                    </p>
                    <TrendLine
                      t={t}
                      text={slsLegTrendText(t, slsTrend?.[leg])}
                      style={{ marginTop: 6 }}
                    />
                  </div>
                );
              })}
              <div className="panel">
                <div className="panel-head" style={{ marginBottom: 18 }}>
                  <h3>{t("sls.perLegHeading")}</h3>
                </div>
                <div className="sls-metric-row">
                  <span className="sls-metric-label">
                    {t("sls.lrDifference")}
                    <GlossaryTerm id="symmetryIndex" />
                  </span>
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
            <>
              <div className="sub-scores" style={{ marginBottom: !isSls && !isWblt ? 8 : 18 }}>
                {metricRows.map((row) => (
                  <div className="sub-score" key={row.label}>
                    <div className="ss-top">
                      <b>
                        {row.label}
                        {"info" in row && row.info && (
                          <InfoTooltip text={row.info} label={row.label} />
                        )}
                      </b>
                      <span>{row.value}</span>
                    </div>
                  </div>
                ))}
              </div>
              {/* STS only -- SLS's legacy (pre-rebuild) metricRows fall through
                  here too, but result.trend is SLS-shaped in that case, not
                  StsTrend, so it's deliberately excluded. */}
              {!isSls && !isWblt && result && (
                <TrendLine
                  t={t}
                  text={stsTrendText(t, result.trend as StsTrend | null | undefined)}
                  style={{ marginBottom: 18 }}
                />
              )}
            </>
          )}
        </>
      )}

      {!result && !moduleBResult && (
        <div className="dash-note">
          <Alert />
          <span>{t("report.disclaimer")}</span>
        </div>
      )}
    </>
  );
}
