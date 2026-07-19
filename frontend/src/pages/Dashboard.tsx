import { useEffect, useState } from "react";
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
import { useAuth } from "../auth";
import type { DashboardSummary, SessionDTO } from "../types/api";

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function qualityLabel(value: number | null) {
  return value === null ? "—" : `${Math.round(value * 100)}%`;
}

export default function Dashboard() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [done, setDone] = useState<Record<number, boolean>>({ 0: true });
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [sessions, setSessions] = useState<SessionDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const toggle = (i: number) => setDone((d) => ({ ...d, [i]: !d[i] }));

  useEffect(() => {
    let cancelled = false;
    Promise.all([dashboardService.summary(), sessionService.list()])
      .then(([nextSummary, nextSessions]) => {
        if (!cancelled) {
          setSummary(nextSummary);
          setSessions(nextSessions.slice(0, 5));
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

  const tags = [
    { sev: "low", label: t("dash.tagRom"), ct: 0 },
    { sev: "med", label: t("dash.tagTempo"), ct: 0 },
    { sev: "low", label: t("dash.tagTrunk"), ct: 0 },
    { sev: "high", label: t("dash.tagQuality"), ct: 0 },
  ];
  const reminders = [
    { b: t("dash.remMorning"), s: t("dash.remMorningSub"), time: "08:00" },
    { b: t("dash.remKnee"), s: t("dash.remKneeSub"), time: "18:30" },
    { b: t("dash.remWeekly"), s: t("dash.remWeeklySub"), time: "10:00" },
  ];
  const avgQuality = summary?.avg_capture_quality;

  return (
    <>
      <DashTopbar
        title={
          user?.full_name ? t("dash.greetingName", { name: user.full_name }) : t("dash.greeting")
        }
        subtitle={t("dash.dateline")}
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
            <span className="trend up">—</span>
          </div>
          <div className="mv">
            —<small>/10</small>
          </div>
          <div className="ml">{t("dash.avgScore")}</div>
        </div>
        <div className="metric reveal">
          <div className="mh">
            <span className="mi">
              <ShieldCheck />
            </span>
            <span className="band good">—</span>
          </div>
          <div className="mv">—</div>
          <div className="ml">{t("dash.latestBand")}</div>
        </div>
        <div className="metric reveal">
          <div className="mh">
            <span className="mi em">
              <Activity />
            </span>
            <span className="trend up">DB</span>
          </div>
          <div className="mv">{summary?.total_sessions ?? 0}</div>
          <div className="ml">{t("dash.sessionsDone")}</div>
        </div>
        <div className="metric reveal">
          <div className="mh">
            <span className="mi em">
              <Camera />
            </span>
            <span className="trend down">DB</span>
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
              <span className="sub">{t("dash.placeholderScoring")}</span>
            </div>
            <div className="seg">
              <button className="on">14d</button>
              <button>30d</button>
              <button>All</button>
            </div>
          </div>
          <svg
            className="chart"
            viewBox="0 0 720 220"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            <defs>
              <linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--chart-line)" stopOpacity="0.26" />
                <stop offset="100%" stopColor="var(--chart-line)" stopOpacity="0" />
              </linearGradient>
            </defs>
            {[40, 90, 140, 190].map((y) => (
              <line key={y} className="grid-l" x1="0" y1={y} x2="720" y2={y} />
            ))}
            <path className="area" d="M0,180 L720,180 L720,220 L0,220 Z" />
            <path className="line" d="M0,180 L720,180" />
          </svg>
          <div className="chart-x">
            <span>{t("dash.waitingForScores")}</span>
            <span>—</span>
            <span>—</span>
          </div>
        </div>

        <div className="panel reveal">
          <div className="panel-head">
            <div>
              <h3>{t("dash.bandDist")}</h3>
              <span className="sub">{t("dash.placeholderScoring")}</span>
            </div>
          </div>
          <div className="bands">
            <div className="band-row">
              <div className="bt">
                <b>{t("common.good")}</b>
                <span>—</span>
              </div>
              <div className="track">
                <div className="fill good" style={{ width: "0%" }} />
              </div>
            </div>
            <div className="band-row">
              <div className="bt">
                <b>{t("common.fair")}</b>
                <span>—</span>
              </div>
              <div className="track">
                <div className="fill fair" style={{ width: "0%" }} />
              </div>
            </div>
            <div className="band-row">
              <div className="bt">
                <b>{t("common.poor")}</b>
                <span>—</span>
              </div>
              <div className="track">
                <div className="fill poor" style={{ width: "0%" }} />
              </div>
            </div>
          </div>
          <div style={{ marginTop: 24, paddingTop: 20, borderTop: "1px solid var(--border-soft)" }}>
            <div className="panel-head" style={{ marginBottom: 14 }}>
              <div>
                <h3 style={{ fontSize: "0.94rem" }}>{t("dash.confidence")}</h3>
              </div>
            </div>
            <div className="band-row">
              <div className="bt">
                <b>—</b>
                <span>{t("dash.placeholderScoring")}</span>
              </div>
              <div className="track">
                <div className="fill good" style={{ width: "0%" }} />
              </div>
            </div>
          </div>
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
          <div className="panel-head">
            <div>
              <h3>{t("dash.errorTags")}</h3>
              <span className="sub">{t("dash.placeholderScoring")}</span>
            </div>
          </div>
          <div className="tags">
            {tags.map((tg) => (
              <span className="tag" key={tg.label}>
                <span className={"sev " + tg.sev} />
                {tg.label} <span className="ct">{tg.ct}</span>
              </span>
            ))}
          </div>
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
          {reminders.map((r, i) => (
            <div
              className={"rem-item" + (done[i] ? " is-done" : "")}
              key={i}
              onClick={() => toggle(i)}
            >
              <span className={"rem-check" + (done[i] ? " done" : "")}>
                <Check />
              </span>
              <div className="rem-body">
                <b>{r.b}</b>
                <span>{r.s}</span>
              </div>
              <span className="rem-time">{r.time}</span>
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
