import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { DashTopbar } from "../layouts/DashboardLayout";
import { dashboardService } from "../services/dashboardService";
import { exerciseService } from "../services/exerciseService";
import type { DashboardErrorTags, DashboardTrends, Exercise } from "../types/api";
import ScoreTrendChart from "../components/charts/ScoreTrendChart";
import BandDistributionBar from "../components/charts/BandDistributionBar";
import PercentTrendChart from "../components/charts/PercentTrendChart";
import ErrorTagBarChart from "../components/charts/ErrorTagBarChart";
import Dropdown from "../components/Dropdown";

type Range = "7d" | "14d" | "30d" | "90d" | "all";
type Category = "functional" | "rehab";

const RANGE_DAYS: Record<Exclude<Range, "all">, number> = {
  "7d": 7,
  "14d": 14,
  "30d": 30,
  "90d": 90,
};

function rangeToFrom(range: Range): string | undefined {
  if (range === "all") return undefined;
  return new Date(Date.now() - RANGE_DAYS[range] * 24 * 60 * 60 * 1000).toISOString();
}

export default function Progress() {
  const { t } = useTranslation();
  const [activeExercises, setActiveExercises] = useState<Exercise[]>([]);
  const [trends, setTrends] = useState<DashboardTrends>({});
  const [errorTags, setErrorTags] = useState<DashboardErrorTags>({});
  const [range, setRange] = useState<Range>("all");
  const [category, setCategory] = useState<Category>("functional");
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Active exercise catalog once -- /api/exercises already server-filters to
  // is_active=true, so this is also the "logic gate" that keeps a retired
  // exercise (e.g. the old Leg Lunge) out of the picker even though its past
  // sessions still exist in `trends`/`errorTags` below.
  useEffect(() => {
    exerciseService
      .list()
      .then(setActiveExercises)
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const from = rangeToFrom(range);
    Promise.all([dashboardService.trends({ from }), dashboardService.errorTags({ from })])
      .then(([nextTrends, nextErrorTags]) => {
        if (cancelled) return;
        setTrends(nextTrends);
        setErrorTags(nextErrorTags);
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
  }, [range, t]);

  // Active exercises (any category) the account actually has session data
  // for, in the current range -- distinguishes "no data at all yet" from
  // "no data in this category" for the empty states below.
  const exercisesWithData = useMemo(
    () => activeExercises.filter((e) => trends[e.code]),
    [activeExercises, trends],
  );
  const categoryExercises = useMemo(
    () => exercisesWithData.filter((e) => e.mode === category),
    [exercisesWithData, category],
  );

  // Re-derive the selected exercise whenever the available options change
  // (range refetch, category switch, or the catalog finishing its own fetch)
  // -- pure client-side selection, no network call of its own.
  useEffect(() => {
    setSelected((current) => {
      const stillValid = current && categoryExercises.some((e) => e.code === current);
      return stillValid ? current : (categoryExercises[0]?.code ?? null);
    });
  }, [categoryExercises]);

  const points = selected ? (trends[selected]?.points ?? []) : [];
  const tags = selected ? (errorTags[selected] ?? null) : null;
  // Presence in errorTags (even an empty list) is the Stage 7.0 signal for
  // "this exercise type has a Module B result" -- Module A types never get a key.
  const isModuleB = selected != null && errorTags[selected] !== undefined;

  return (
    <>
      <DashTopbar title={t("progress.title")} subtitle={t("progress.subtitle")} />

      {error && (
        <p className="muted" style={{ color: "var(--coral)", marginBottom: 18 }}>
          {error}
        </p>
      )}

      <div className="panel reveal" style={{ marginBottom: 18 }}>
        <div className="panel-head" style={{ flexWrap: "wrap", gap: 12 }}>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
            <div className="seg">
              <button
                className={category === "functional" ? "on" : ""}
                onClick={() => setCategory("functional")}
              >
                {t("landing.modATitle")}
              </button>
              <button
                className={category === "rehab" ? "on" : ""}
                onClick={() => setCategory("rehab")}
              >
                {t("landing.modBTitle")}
              </button>
            </div>
            {categoryExercises.length > 0 && (
              <Dropdown
                options={categoryExercises.map((e) => ({ value: e.code, label: e.name }))}
                value={selected}
                onChange={setSelected}
                placeholder={t("progress.chooseExercise")}
                ariaLabel={t("progress.exercisePicker")}
              />
            )}
          </div>
          <div className="seg">
            <button className={range === "7d" ? "on" : ""} onClick={() => setRange("7d")}>
              {t("progress.range7d")}
            </button>
            <button className={range === "14d" ? "on" : ""} onClick={() => setRange("14d")}>
              {t("progress.range14d")}
            </button>
            <button className={range === "30d" ? "on" : ""} onClick={() => setRange("30d")}>
              {t("progress.range30d")}
            </button>
            <button className={range === "90d" ? "on" : ""} onClick={() => setRange("90d")}>
              {t("progress.range90d")}
            </button>
            <button className={range === "all" ? "on" : ""} onClick={() => setRange("all")}>
              {t("progress.rangeAll")}
            </button>
          </div>
        </div>

        {loading ? (
          <p className="muted" style={{ padding: "24px 0" }}>
            {t("common.loading")}
          </p>
        ) : exercisesWithData.length === 0 ? (
          <p className="muted center" style={{ padding: "24px 0" }}>
            {t("dash.emptySessions")}
          </p>
        ) : !selected ? (
          <p className="muted center" style={{ padding: "24px 0" }}>
            {t("progress.noExerciseInCategory")}
          </p>
        ) : points.length === 0 ? (
          <p className="muted center" style={{ padding: "24px 0" }}>
            {t("progress.noExercise")}
          </p>
        ) : (
          <>
            <div className="panel-head">
              <div>
                <h3>{t("dash.scoreTrend")}</h3>
                <span className="sub">
                  {t("progress.sessionsInRange", { count: points.length })}
                </span>
              </div>
            </div>
            <ScoreTrendChart points={points} variant="full" />

            <div className="dash-grid" style={{ marginTop: 18, marginBottom: 0 }}>
              <div className="panel" style={{ background: "var(--surface-2)" }}>
                <div className="panel-head">
                  <div>
                    <h3 style={{ fontSize: "0.94rem" }}>{t("dash.bandDist")}</h3>
                  </div>
                </div>
                <BandDistributionBar points={points} />
              </div>
              <div className="panel" style={{ background: "var(--surface-2)" }}>
                <div className="panel-head">
                  <div>
                    <h3 style={{ fontSize: "0.94rem" }}>{t("progress.captureQualityTrend")}</h3>
                    <span className="sub">{t("progress.captureQualityTrendSub")}</span>
                  </div>
                </div>
                <PercentTrendChart
                  points={points}
                  dataKey="capture_quality"
                  color="var(--emerald)"
                  label={t("dash.avgQuality")}
                  variant="full"
                />
              </div>
            </div>

            {isModuleB && tags && (
              <div className="dash-grid" style={{ marginTop: 18, marginBottom: 0 }}>
                <div className="panel" style={{ background: "var(--surface-2)" }}>
                  <div className="panel-head">
                    <div>
                      <h3 style={{ fontSize: "0.94rem" }}>{t("progress.confidenceTrend")}</h3>
                      <span className="sub">{t("progress.confidenceTrendSub")}</span>
                    </div>
                  </div>
                  <PercentTrendChart
                    points={points}
                    dataKey="confidence"
                    color="var(--accent-text)"
                    label={t("dash.confidence")}
                    variant="full"
                  />
                </div>
                <div className="panel" style={{ background: "var(--surface-2)" }}>
                  <div className="panel-head">
                    <div>
                      <h3 style={{ fontSize: "0.94rem" }}>{t("dash.errorTags")}</h3>
                      <span className="sub">{t("dash.errorTagsSub")}</span>
                    </div>
                  </div>
                  {tags.length === 0 ? (
                    <p className="muted center" style={{ padding: "16px 0" }}>
                      {t("dash.noErrorTags")}
                    </p>
                  ) : (
                    <ErrorTagBarChart tags={tags} />
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}
