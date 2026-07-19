import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { DashTopbar } from "../layouts/DashboardLayout";
import { Activity, Balance, Check, Stretch } from "../components/Icons";
import { sessionService } from "../services/sessionService";
import { exerciseService } from "../services/exerciseService";
import Dropdown from "../components/Dropdown";
import type { Exercise, SessionDTO } from "../types/api";

const ALL_EXERCISES = "all";

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

export default function SessionHistory() {
  const { t } = useTranslation();
  const [filter, setFilter] = useState<"all" | "functional" | "rehab">("all");
  // Gates only the picker's options, not the table -- a session run on a
  // since-retired exercise (e.g. the old Leg Lunge) stays visible in the
  // "All exercises" view; it's just not offered as a new filter target.
  const [exerciseFilter, setExerciseFilter] = useState<string>(ALL_EXERCISES);
  const [activeExercises, setActiveExercises] = useState<Exercise[]>([]);
  const [sessions, setSessions] = useState<SessionDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    sessionService
      .list()
      .then((data) => {
        if (!cancelled) setSessions(data);
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

  useEffect(() => {
    exerciseService
      .list()
      .then(setActiveExercises)
      .catch(() => undefined);
  }, []);

  const iconFor = (session: SessionDTO) => {
    if (session.mode === "rehab") return <Stretch />;
    if (session.exercise_code.includes("single_leg")) return <Balance />;
    if (session.exercise_code === "weight_bearing_lunge_test") return <Check />;
    return <Activity />;
  };

  const rows = sessions.filter(
    (r) =>
      (filter === "all" || r.mode === filter) &&
      (exerciseFilter === ALL_EXERCISES || r.exercise_code === exerciseFilter),
  );
  const filters: ("all" | "functional" | "rehab")[] = ["all", "functional", "rehab"];
  // Exercise picker only makes sense once a mode is chosen -- "All" already
  // spans both categories, so a sub-filter by exercise has nothing to scope to.
  const categoryExercises = activeExercises.filter((e) => e.mode === filter);
  const exerciseOptions = [
    { value: ALL_EXERCISES, label: t("history.allExercises") },
    ...categoryExercises.map((e) => ({ value: e.code, label: e.name })),
  ];

  const selectFilter = (f: "all" | "functional" | "rehab") => {
    setFilter(f);
    // Reset the exercise sub-filter -- a selection from the old category (or
    // "all") wouldn't necessarily belong to the newly chosen one.
    setExerciseFilter(ALL_EXERCISES);
  };

  return (
    <>
      <DashTopbar title={t("history.title")} subtitle={t("history.desc")} />
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
      <div className="filters">
        {filters.map((f) => (
          <button
            key={f}
            className={"filter-pill" + (filter === f ? " on" : "")}
            onClick={() => selectFilter(f)}
          >
            {t("history." + f)}
          </button>
        ))}
        {filter !== "all" && (
          <Dropdown
            options={exerciseOptions}
            value={exerciseFilter}
            onChange={setExerciseFilter}
            placeholder={t("history.allExercises")}
            ariaLabel={t("progress.exercisePicker")}
          />
        )}
      </div>
      <div className="panel reveal">
        <div className="tbl-scroll">
          <table className="tbl">
            <thead>
              <tr>
                <th>{t("history.thExercise")}</th>
                <th>{t("history.thMode")}</th>
                <th>{t("history.thDate")}</th>
                <th>{t("history.thQuality")}</th>
                <th>{t("history.thBand")}</th>
                <th>{t("history.thReps")}</th>
                <th>{t("history.thScore")}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
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
                  <td>{r.rep_count ?? "—"}</td>
                  <td className="score-cell">{r.score ?? "—"}</td>
                  <td style={{ textAlign: "right" }}>
                    <Link
                      className="btn btn-ghost"
                      to={`/report?session=${r.id}`}
                      style={{ padding: "7px 14px" }}
                    >
                      {t("history.view")}
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!loading && rows.length === 0 && (
          <p className="muted center" style={{ padding: "28px 0" }}>
            {t("history.empty")}
          </p>
        )}
      </div>
    </>
  );
}
