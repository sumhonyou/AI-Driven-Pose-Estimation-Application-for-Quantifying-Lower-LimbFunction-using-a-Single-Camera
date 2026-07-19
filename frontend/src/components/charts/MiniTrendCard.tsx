import { useTranslation } from "react-i18next";
import type { ExerciseTrend } from "../../types/api";
import ScoreTrendChart from "./ScoreTrendChart";

export default function MiniTrendCard({
  exerciseName,
  trend,
}: {
  exerciseName: string;
  trend: ExerciseTrend;
}) {
  const { t } = useTranslation();
  const scored = trend.points.filter((p) => p.score != null);
  const latest = scored.at(-1);
  const previous = scored.at(-2);
  const delta =
    latest?.score != null && previous?.score != null ? latest.score - previous.score : null;

  return (
    <div className="mini-trend-card">
      <div className="mini-trend-head">
        <div>
          <b>{exerciseName}</b>
          <div className="mini-trend-sub">
            {t("dash.sessionsCount", { count: trend.points.length })}
          </div>
        </div>
        {latest?.band && (
          <span className={"band " + latest.band.toLowerCase()}>
            {t("common." + latest.band.toLowerCase())}
          </span>
        )}
      </div>
      <ScoreTrendChart points={trend.points} variant="mini" />
      <div className="mini-trend-foot">
        <span className="mini-trend-score">
          {latest?.score != null ? latest.score.toFixed(1) : "—"}
          <small>/10</small>
        </span>
        {delta != null && (
          <span className={"trend " + (delta >= 0 ? "up" : "down")}>
            {delta >= 0 ? "+" : ""}
            {delta.toFixed(1)}
          </span>
        )}
      </div>
    </div>
  );
}
