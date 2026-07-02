import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { DashTopbar } from "../layouts/DashboardLayout";
import { Activity, Balance, Check, Stretch } from "../components/Icons";
import { sessionService } from "../services/sessionService";
import type { SessionDTO } from "../types/api";

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

  const iconFor = (session: SessionDTO) => {
    if (session.mode === "rehab") return <Stretch />;
    if (session.exercise_code.includes("single_leg")) return <Balance />;
    if (session.exercise_code.includes("lunge")) return <Check />;
    return <Activity />;
  };

  const rows = sessions.filter((r) => filter === "all" || r.mode === filter);
  const filters: ("all" | "functional" | "rehab")[] = ["all", "functional", "rehab"];

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
            onClick={() => setFilter(f)}
          >
            {t("history." + f)}
          </button>
        ))}
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
                      <span className={"band " + r.band}>{t("common." + r.band)}</span>
                    ) : (
                      "—"
                    )}
                  </td>
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
