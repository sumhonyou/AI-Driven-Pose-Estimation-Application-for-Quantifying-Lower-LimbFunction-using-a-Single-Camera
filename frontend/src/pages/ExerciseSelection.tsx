import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { DashTopbar } from "../layouts/DashboardLayout";
import { Activity, Balance, Check, Stretch, ArrowLeft, ArrowRight } from "../components/Icons";
import { exerciseService } from "../services/exerciseService";
import { useSessionFlow } from "../session";
import type { Exercise } from "../types/api";

export default function ExerciseSelection() {
  const { t } = useTranslation();
  const [params] = useSearchParams();
  const mode = params.get("mode") === "rehab" ? "rehab" : "functional";
  const { setMode, setExerciseCode } = useSessionFlow();
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setMode(mode);
    let cancelled = false;
    exerciseService
      .list()
      .then((data) => {
        if (!cancelled) setExercises(data.filter((exercise) => exercise.mode === mode));
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
  }, [mode, setMode, t]);

  const iconFor = (code: string) => {
    if (mode === "rehab") return <Stretch width={24} height={24} />;
    if (code.includes("single_leg")) return <Balance width={24} height={24} />;
    if (code.includes("lunge")) return <Check width={24} height={24} />;
    return <Activity width={24} height={24} />;
  };

  return (
    <>
      <Link className="back-link" to="/mode"><ArrowLeft />{t("common.back")}</Link>
      <DashTopbar title={t("exercise.title")} subtitle={mode === "rehab" ? t("exercise.descRehab") : t("exercise.descFunc")} />
      {error && <p className="muted" style={{ color: "var(--coral)", marginBottom: 18 }}>{error}</p>}
      {loading && <p className="muted" style={{ marginBottom: 18 }}>{t("common.loading")}</p>}
      <div className="ex-grid">
        {exercises.map((exercise) => (
          <Link className="ex-card reveal" to="/camera" key={exercise.code} onClick={() => setExerciseCode(exercise.code)}>
            <div className="ex-top">
              <span className="big-ic">{iconFor(exercise.code)}</span>
              <span className="go" style={{ color: "var(--accent-text)" }}><ArrowRight /></span>
            </div>
            <h3>{exercise.name}</h3>
            <p>{exercise.description}</p>
            <div className="ex-meta">
              <span className="chip">{exercise.view_guidance === "front_view" ? t("exercise.frontView") : t("exercise.sideView")}</span>
              <span className="chip">{mode === "rehab" ? t("exercise.configurable") : t("common.functional")}</span>
            </div>
          </Link>
        ))}
      </div>
      {!loading && exercises.length === 0 && <p className="muted center" style={{ padding: "28px 0" }}>{t("exercise.empty")}</p>}
    </>
  );
}
