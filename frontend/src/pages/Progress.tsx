import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { DashTopbar } from "../layouts/DashboardLayout";
import { dashboardService } from "../services/dashboardService";
import { exerciseService } from "../services/exerciseService";
import type { DashboardErrorTags, DashboardTrends, Exercise } from "../types/api";
import ScoreTrendChart from "../components/charts/ScoreTrendChart";
import BandDistributionBar from "../components/charts/BandDistributionBar";
import MetricTrendChart, { type MetricSeries } from "../components/charts/MetricTrendChart";
import ErrorTagBarChart from "../components/charts/ErrorTagBarChart";
import RepAttemptsBarChart from "../components/charts/RepAttemptsBarChart";
import { scoreBandThresholdsFor } from "../components/charts/dashboardChartUtils";
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
  // Stage R12 follow-up (HY): the SLS best-hold-per-leg chart defaults to both
  // legs combined, but two overlapping lines read as cluttered -- this lets the
  // user isolate one leg on that card specifically.
  const [legFilter, setLegFilter] = useState<"both" | "left" | "right">("both");

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

  // Stage R12 (UAT): the second progress chart per exercise, replacing the
  // unanimously-rejected capture-quality trend. Each exercise plots the raw
  // metric that actually means something to that movement -- STS finish/avg-rep
  // time, SLS best hold per leg, WBLT best reach per leg, squat valid reps --
  // with axis labels ("Date" on X, the unit on Y) and hover detail. `selected`
  // is the exercise code, which equals its exercise_type here (same key used for
  // `trends[selected]`), so it's safe to match against the known type strings.
  const secondChart = ((): {
    titleKey: string;
    subKey: string;
    node: React.ReactNode;
    // Rendered in the panel head next to the title -- currently only the SLS
    // leg-select dropdown uses this.
    headerExtra?: React.ReactNode;
  } | null => {
    if (!selected) return null;
    if (isModuleB) {
      // Squat: valid-rep volume (counted vs rejected). The score alone can't tell
      // a hard session from a short one; this is the raw-metric view S4 asked for.
      return {
        titleKey: "progress.repVolumeTrend",
        subKey: "progress.repVolumeTrendSub",
        node: <RepAttemptsBarChart points={points} />,
      };
    }
    if (selected === "sit_to_stand") {
      const series: MetricSeries[] = [
        {
          dataKey: "completion_time_sec",
          label: t("progress.metricCompletionTime"),
          color: "var(--chart-line)",
        },
        {
          dataKey: "avg_rep_time_sec",
          label: t("progress.metricAvgRepTime"),
          color: "var(--info-blue)",
        },
      ];
      return {
        titleKey: "progress.stsTimeTrend",
        subKey: "progress.stsTimeTrendSub",
        node: (
          <MetricTrendChart
            points={points}
            series={series}
            unit="s"
            yAxisLabel={t("progress.axisSeconds")}
          />
        ),
      };
    }
    if (selected.includes("single_leg")) {
      const bothSeries: MetricSeries[] = [
        { dataKey: "hold_left_sec", label: t("sls.legLeft"), color: "var(--chart-line)" },
        { dataKey: "hold_right_sec", label: t("sls.legRight"), color: "var(--info-blue)" },
      ];
      // Isolating a leg keeps its own line's colour so switching the dropdown
      // doesn't also change which colour means "this leg" elsewhere on the page.
      const series: MetricSeries[] =
        legFilter === "left"
          ? [bothSeries[0]]
          : legFilter === "right"
            ? [bothSeries[1]]
            : bothSeries;
      return {
        titleKey: "progress.slsHoldTrend",
        subKey: "progress.slsHoldTrendSub",
        headerExtra: (
          <Dropdown
            options={[
              { value: "both", label: t("progress.bothLegs") },
              { value: "left", label: t("sls.legLeft") },
              { value: "right", label: t("sls.legRight") },
            ]}
            value={legFilter}
            onChange={(v) => setLegFilter(v as "both" | "left" | "right")}
            placeholder={t("progress.bothLegs")}
            ariaLabel={t("sls.perLegHeading")}
          />
        ),
        node: (
          <MetricTrendChart
            points={points}
            series={series}
            unit="s"
            yAxisLabel={t("progress.axisSeconds")}
          />
        ),
      };
    }
    if (selected === "weight_bearing_lunge_test") {
      const series: MetricSeries[] = [
        { dataKey: "distance_left_cm", label: t("wblt.legLeft"), color: "var(--chart-line)" },
        { dataKey: "distance_right_cm", label: t("wblt.legRight"), color: "var(--info-blue)" },
      ];
      return {
        titleKey: "progress.wbltDistanceTrend",
        subKey: "progress.wbltDistanceTrendSub",
        node: (
          <MetricTrendChart
            points={points}
            series={series}
            unit=" cm"
            yAxisLabel={t("progress.axisCentimetres")}
          />
        ),
      };
    }
    return null;
  })();

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
            <ScoreTrendChart
              points={points}
              variant="full"
              thresholds={scoreBandThresholdsFor(selected)}
            />

            <div className="dash-grid" style={{ marginTop: 18, marginBottom: 0 }}>
              <div className="panel" style={{ background: "var(--surface-2)" }}>
                <div className="panel-head">
                  <div>
                    <h3 style={{ fontSize: "0.94rem" }}>{t("dash.bandDist")}</h3>
                  </div>
                </div>
                <BandDistributionBar points={points} />
              </div>
              {/* Stage R12 (UAT): the capture-quality trend that used to sit here was
                  the one unanimously-rejected chart (6/18). It's replaced by the
                  raw metric each exercise's users actually track -- squat valid
                  reps, STS finish/avg-rep time, SLS best hold per leg, WBLT best
                  reach per leg. */}
              {secondChart && (
                <div className="panel" style={{ background: "var(--surface-2)" }}>
                  <div className="panel-head" style={{ flexWrap: "wrap", gap: 8 }}>
                    <div>
                      <h3 style={{ fontSize: "0.94rem" }}>{t(secondChart.titleKey)}</h3>
                      <span className="sub">{t(secondChart.subKey)}</span>
                    </div>
                    {secondChart.headerExtra}
                  </div>
                  {secondChart.node}
                </div>
              )}
            </div>

            {isModuleB && tags && (
              <div className="panel" style={{ background: "var(--surface-2)", marginTop: 18 }}>
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
            )}
          </>
        )}
      </div>
    </>
  );
}
