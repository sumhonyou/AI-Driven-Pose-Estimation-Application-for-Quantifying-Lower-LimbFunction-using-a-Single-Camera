import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { DashTopbar } from "../layouts/DashboardLayout";
import {
  Chart,
  ShieldCheck,
  Activity,
  Camera,
  Plus,
  Check,
  Alert,
  Stretch,
  Balance,
} from "../components/Icons";
import { dashboardService } from "../services/dashboardService";
import { sessionService } from "../services/sessionService";
import { exerciseService } from "../services/exerciseService";
import { reminderService } from "../services/reminderService";
import { useReveal } from "../useReveal";
import { useAuth } from "../auth";
import { useReminders } from "../reminders";
import type {
  DashboardErrorTags,
  DashboardSummary,
  DashboardTrends,
  Exercise,
  SessionDTO,
} from "../types/api";
import BandDistributionBar from "../components/charts/BandDistributionBar";
import MiniTrendCard from "../components/charts/MiniTrendCard";
import {
  averageScore,
  humanizeExerciseType,
  severityClass,
} from "../components/charts/dashboardChartUtils";
import Dropdown from "../components/Dropdown";
import GlossaryTerm from "../components/GlossaryTerm";

const FOURTEEN_DAYS_MS = 14 * 24 * 60 * 60 * 1000;
const ALL_EXERCISES = "all";

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

/** Today's date for the dashboard subheading, e.g. "Sunday, 19 July 2026".
 *  Chinese uses weekday-first: "星期一，2026年7月20日". */
function formatTodayDateline(language: string) {
  const now = new Date();
  if (language.startsWith("zh")) {
    const weekday = new Intl.DateTimeFormat("zh-CN", { weekday: "long" }).format(now);
    const date = new Intl.DateTimeFormat("zh-CN", {
      year: "numeric",
      month: "long",
      day: "numeric",
    }).format(now);
    return `${weekday}，${date}`;
  }
  const locale = language.startsWith("ms") ? "ms-MY" : "en-GB";
  return new Intl.DateTimeFormat(locale, {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(now);
}

function qualityLabel(value: number | null) {
  return value === null ? "—" : `${Math.round(value * 100)}%`;
}

export default function Dashboard() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const { reminders: allReminders, refresh: refreshReminders } = useReminders();
  const todayLabel = formatTodayDateline(i18n.language);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [sessions, setSessions] = useState<SessionDTO[]>([]);
  const [trends, setTrends] = useState<DashboardTrends>({});
  const [errorTags, setErrorTags] = useState<DashboardErrorTags>({});
  const [activeExercises, setActiveExercises] = useState<Exercise[]>([]);
  const [loading, setLoading] = useState(true);
  // Stage R12 (UAT): drill-down filters for the two account-wide panels below --
  // both default to "all" (today's pooled-across-everything behaviour) so
  // nothing changes until the user opts into a single exercise's view.
  const [bandFilter, setBandFilter] = useState<string>(ALL_EXERCISES);
  const [tagFilter, setTagFilter] = useState<string>(ALL_EXERCISES);
  // This page's real content only exists once `loading` flips false (and once
  // reminders load, for the due-banner/panel) -- DashboardLayout's own
  // useReveal([pathname]) fires on mount, before any of that async data has
  // landed, so it never observes these elements. Found live-testing Stage 7.3
  // (the reminders panel/banner stayed invisible); this was a pre-existing gap
  // affecting the whole page, not something the reminders work introduced, so
  // fixed here rather than worked around locally.
  useReveal([loading, allReminders]);
  const [error, setError] = useState("");
  const completeReminder = (id: string) => reminderService.complete(id).then(refreshReminders);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      dashboardService.summary(),
      sessionService.list(),
      dashboardService.trends(),
      dashboardService.errorTags(),
      exerciseService.list(),
    ])
      .then(([nextSummary, nextSessions, nextTrends, nextErrorTags, nextExercises]) => {
        if (!cancelled) {
          setSummary(nextSummary);
          setSessions(nextSessions.slice(0, 5));
          setTrends(nextTrends);
          setErrorTags(nextErrorTags);
          setActiveExercises(nextExercises);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : t("common.loadError"));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [t]);

  const iconFor = (session: SessionDTO) => {
    if (session.mode === "rehab") return <Stretch />;
    if (session.exercise_code.includes("single_leg")) return <Balance />;
    if (session.exercise_code === "weight_bearing_lunge_test") return <Check />;
    return <Activity />;
  };

  // Stage 7.3: real reminders (shared via RemindersContext), soonest-first,
  // capped to a small preview -- the full list lives on the Reminders page.
  const upcomingReminders = allReminders.slice(0, 4);
  const avgQuality = summary?.avg_capture_quality;

  // All exercise types' trend points pooled together, for the account-wide
  // panels (band distribution, confidence) -- deliberately unfiltered, so a
  // retired exercise's historical sessions still count toward the account's
  // overall numbers (same "gate the picker, not the history" principle as
  // Session History). The small-multiples grid below uses each exercise's own
  // points separately, and IS gated to active exercises -- it's a per-exercise
  // picker/breakdown, not an aggregate history figure.
  const allPoints = useMemo(() => Object.values(trends).flatMap((ex) => ex.points), [trends]);

  const activeExerciseCodes = useMemo(
    () => new Set(activeExercises.map((e) => e.code)),
    [activeExercises],
  );
  const activeTrendEntries = useMemo(
    () => Object.entries(trends).filter(([exerciseType]) => activeExerciseCodes.has(exerciseType)),
    [trends, activeExerciseCodes],
  );

  const avgScoreLast14d = useMemo(() => {
    const cutoff = Date.now() - FOURTEEN_DAYS_MS;
    return averageScore(allPoints.filter((p) => new Date(p.date).getTime() >= cutoff));
  }, [allPoints]);

  // The most recently completed session with a score, across every exercise
  // type -- the same session summary.latest_score/latest_band describe.
  const latestScoredSession = sessions.find((s) => s.score != null);

  // Module B only: confidence is null for every Module A point, so this stays
  // empty (and the tile hides) for accounts with no rehab-graded exercises.
  const confidencePoints = allPoints.filter((p) => p.confidence != null);
  const avgConfidence =
    confidencePoints.length > 0
      ? confidencePoints.reduce((sum, p) => sum + (p.confidence ?? 0), 0) / confidencePoints.length
      : null;

  const rankedErrorTags = useMemo(() => {
    const merged = new Map<string, { severity: string | null; count: number }>();
    for (const tags of Object.values(errorTags)) {
      for (const tag of tags) {
        const existing = merged.get(tag.tag_code);
        if (existing) existing.count += tag.count;
        else merged.set(tag.tag_code, { severity: tag.severity, count: tag.count });
      }
    }
    return [...merged.entries()]
      .map(([tag_code, v]) => ({ tag_code, ...v }))
      .sort((a, b) => b.count - a.count);
  }, [errorTags]);

  // Stage R12 (UAT): "drill-down by exercise" for Band distribution -- the panel
  // pools every exercise type by default (the account-wide view), but a picker
  // lets it narrow to one. Options are exercises the account actually has trend
  // data for (mirrors Progress's own "only exercises with data" gate).
  const bandFilterOptions = useMemo(
    () => [
      { value: ALL_EXERCISES, label: t("dash.allExercises") },
      ...activeTrendEntries.map(([exerciseType]) => ({
        value: exerciseType,
        label: humanizeExerciseType(exerciseType, sessions),
      })),
    ],
    [activeTrendEntries, sessions, t],
  );
  const bandPoints = bandFilter === ALL_EXERCISES ? allPoints : (trends[bandFilter]?.points ?? []);

  // Stage R12 (UAT): "filter by exercise" for Common error tags -- only Module B
  // exercise types ever carry a key in `errorTags` (Stage 7.0's presence signal),
  // so the option list is built off that map, not the full exercise catalog.
  const tagFilterOptions = useMemo(
    () => [
      { value: ALL_EXERCISES, label: t("dash.allExercises") },
      ...Object.keys(errorTags)
        .filter((exerciseType) => activeExerciseCodes.has(exerciseType))
        .map((exerciseType) => ({
          value: exerciseType,
          label: humanizeExerciseType(exerciseType, sessions),
        })),
    ],
    [errorTags, activeExerciseCodes, sessions, t],
  );
  // A single exercise's tags are already ranked most-frequent-first by the
  // backend (build_error_tags) -- only the "all" view needs the client-side merge.
  const displayedErrorTags =
    tagFilter === ALL_EXERCISES ? rankedErrorTags : (errorTags[tagFilter] ?? []);

  return (
    <>
      <DashTopbar
        title={
          user?.full_name ? t("dash.greetingName", { name: user.full_name }) : t("dash.greeting")
        }
        subtitle={t("dash.dateline", { date: todayLabel })}
        actions={
          <Link className="btn btn-primary" to="/mode">
            {t("common.newSession")}
            <Plus />
          </Link>
        }
      />

      {error && (
        <p className="muted" style={{ color: "var(--coral)", marginBottom: 18 }}>
          {error}
        </p>
      )}
      {loading && (
        <p className="muted" style={{ marginBottom: 18 }}>
          {t("common.loading")}
        </p>
      )}

      <div className="metrics">
        <div className="metric reveal">
          <div className="mh">
            <span className="mi">
              <Chart />
            </span>
          </div>
          <div className="mv">
            {avgScoreLast14d == null ? "—" : avgScoreLast14d.toFixed(1)}
            <small>/10</small>
          </div>
          <div className="ml">{t("dash.avgScore")}</div>
        </div>
        <div className="metric reveal">
          <div className="mh">
            <span className="mi">
              <ShieldCheck />
            </span>
            {latestScoredSession?.band && (
              <span className={"band " + latestScoredSession.band.toLowerCase()}>
                {t("common." + latestScoredSession.band.toLowerCase())}
              </span>
            )}
          </div>
          <div className="mv">{latestScoredSession?.score ?? "—"}</div>
          <div className="ml">
            {t("dash.latestBand")}
            {latestScoredSession && ` · ${latestScoredSession.exercise_name}`}
          </div>
        </div>
        <div className="metric reveal">
          <div className="mh">
            <span className="mi em">
              <Activity />
            </span>
          </div>
          <div className="mv">{summary?.total_sessions ?? 0}</div>
          <div className="ml">{t("dash.sessionsDone")}</div>
        </div>
        <div className="metric reveal">
          <div className="mh">
            <span className="mi em">
              <Camera />
            </span>
          </div>
          <div className="mv">
            {avgQuality == null ? "—" : Math.round(avgQuality * 100)}
            <small>{avgQuality == null ? "" : "%"}</small>
          </div>
          <div className="ml">{t("dash.avgQuality")}</div>
        </div>
      </div>

      <div className="dash-grid">
        <div className="panel reveal">
          <div className="panel-head">
            <div>
              <h3>{t("dash.scoreTrend")}</h3>
              <span className="sub">{t("dash.scoreTrendSub")}</span>
            </div>
          </div>
          {activeTrendEntries.length === 0 ? (
            <p className="muted center" style={{ padding: "24px 0" }}>
              {t("dash.emptySessions")}
            </p>
          ) : (
            <div className="mini-trend-grid">
              {activeTrendEntries.map(([exerciseType, trend]) => (
                <MiniTrendCard
                  key={exerciseType}
                  exerciseName={humanizeExerciseType(exerciseType, sessions)}
                  trend={trend}
                />
              ))}
            </div>
          )}
        </div>

        <div className="panel reveal">
          <div className="panel-head" style={{ flexWrap: "wrap", gap: 8 }}>
            <div>
              <h3>
                {t("dash.bandDist")}
                <GlossaryTerm id="goodFairPoor" />
              </h3>
              <span className="sub">{t("dash.bandDistSub")}</span>
            </div>
            {bandFilterOptions.length > 1 && (
              <Dropdown
                options={bandFilterOptions}
                value={bandFilter}
                onChange={setBandFilter}
                placeholder={t("dash.allExercises")}
                ariaLabel={t("progress.exercisePicker")}
              />
            )}
          </div>
          <BandDistributionBar points={bandPoints} />
          {avgConfidence != null && (
            <div
              style={{ marginTop: 24, paddingTop: 20, borderTop: "1px solid var(--border-soft)" }}
            >
              <div className="panel-head" style={{ marginBottom: 14 }}>
                <div>
                  <h3 style={{ fontSize: "0.94rem" }}>{t("dash.confidence")}</h3>
                </div>
              </div>
              <div className="band-row">
                <div className="bt">
                  <b>{Math.round(avgConfidence * 100)}%</b>
                </div>
                <div className="track">
                  <div className="fill good" style={{ width: `${avgConfidence * 100}%` }} />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="panel reveal" style={{ marginBottom: 18 }}>
        <div className="panel-head">
          <div>
            <h3>{t("dash.recent")}</h3>
            <span className="sub">{t("dash.recentSub")}</span>
          </div>
          <Link className="btn btn-ghost" to="/history" style={{ padding: "8px 16px" }}>
            {t("common.viewAll")}
          </Link>
        </div>
        <div className="tbl-scroll">
          <table className="tbl">
            <thead>
              <tr>
                <th>{t("dash.thExercise")}</th>
                <th>{t("dash.thMode")}</th>
                <th>{t("dash.thDate")}</th>
                <th>{t("dash.thQuality")}</th>
                <th>{t("dash.thBand")}</th>
                <th style={{ textAlign: "right" }}>{t("dash.thScore")}</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((r) => (
                <tr key={r.id}>
                  <td>
                    <div className="ex-cell">
                      <span className="ex-ic">{iconFor(r)}</span>
                      <b>{r.exercise_name}</b>
                    </div>
                  </td>
                  <td>
                    <span className="mode-tag">
                      {t("common." + (r.mode === "rehab" ? "rehab" : "functional"))}
                    </span>
                  </td>
                  <td>{formatDate(r.started_at)}</td>
                  <td>{qualityLabel(r.capture_quality)}</td>
                  <td>
                    {r.band ? (
                      <span className={"band " + r.band.toLowerCase()}>
                        {t("common." + r.band.toLowerCase())}
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="score-cell" style={{ textAlign: "right" }}>
                    {r.score ?? "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!loading && sessions.length === 0 && (
          <p className="muted center" style={{ padding: "24px 0" }}>
            {t("dash.emptySessions")}
          </p>
        )}
      </div>

      <div className="dash-grid-2">
        <div className="panel reveal">
          <div className="panel-head" style={{ flexWrap: "wrap", gap: 8 }}>
            <div>
              <h3>{t("dash.errorTags")}</h3>
              <span className="sub">{t("dash.errorTagsSub")}</span>
            </div>
            {tagFilterOptions.length > 1 && (
              <Dropdown
                options={tagFilterOptions}
                value={tagFilter}
                onChange={setTagFilter}
                placeholder={t("dash.allExercises")}
                ariaLabel={t("progress.exercisePicker")}
              />
            )}
          </div>
          {displayedErrorTags.length === 0 ? (
            <p className="muted center" style={{ padding: "24px 0" }}>
              {t("dash.noErrorTags")}
            </p>
          ) : (
            <div className="tags">
              {displayedErrorTags.map((tag) => (
                <span className="tag" key={tag.tag_code}>
                  <span className={"sev " + severityClass(tag.severity)} />
                  {t("moduleB.tag_" + tag.tag_code, { defaultValue: tag.tag_code })}{" "}
                  <span className="ct">{tag.count}</span>
                </span>
              ))}
            </div>
          )}
        </div>
        <div className="panel reveal">
          <div className="panel-head">
            <div>
              <h3>{t("dash.reminders")}</h3>
              <span className="sub">{t("dash.remindersSub")}</span>
            </div>
            <Link className="btn btn-ghost" to="/reminders" style={{ padding: "8px 16px" }}>
              + {t("common.add")}
            </Link>
          </div>
          {upcomingReminders.length === 0 && (
            <p className="muted" style={{ fontSize: "0.85rem" }}>
              {t("dash.remindersEmpty")}
            </p>
          )}
          {upcomingReminders.map((r) => (
            <div
              className={"rem-item" + (r.last_completed_at ? " is-done" : "")}
              key={r.id}
              onClick={() => completeReminder(r.id)}
            >
              <span className={"rem-check" + (r.last_completed_at ? " done" : "")}>
                <Check />
              </span>
              <div className="rem-body">
                <b>{r.title}</b>
                <span>{r.exercise_name ?? t("dash.remindersSub")}</span>
              </div>
              <span className="rem-time">{formatDate(r.reminder_time)}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="dash-note reveal" style={{ marginTop: 22 }}>
        <Alert />
        <span>{t("dash.note")}</span>
      </div>
    </>
  );
}
