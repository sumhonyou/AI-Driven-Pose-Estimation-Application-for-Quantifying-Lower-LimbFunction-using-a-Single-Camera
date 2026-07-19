import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { DashTopbar } from "../layouts/DashboardLayout";
import { Activity, Balance, Check, Stretch, ArrowLeft, ArrowRight } from "../components/Icons";
import { exerciseService } from "../services/exerciseService";
import { useSessionFlow } from "../session";
import { useReveal } from "../useReveal";
import type { Exercise } from "../types/api";
import slsImage from "../assets/exercise type/Single Leg Stance pic.png";
import stsImage from "../assets/exercise type/sit to stand.png";
import wbltImage from "../assets/exercise type/WBLT.png";
import squatImage from "../assets/exercise type/Squat.png";

export default function ExerciseSelection() {
  const { t } = useTranslation();
  const [params] = useSearchParams();
  const mode = params.get("mode") === "rehab" ? "rehab" : "functional";
  const { setMode, setExerciseCode } = useSessionFlow();
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useReveal([exercises]);

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

  const imageFor = (code: string): string | null => {
    if (code.includes("single_leg")) return slsImage;
    if (code.includes("sit_to_stand") || code.includes("sit-to-stand")) return stsImage;
    if (code === "squat") return squatImage;
    if (code.includes("wblt") || code === "weight_bearing_lunge_test") return wbltImage;
    return null;
  };

  const iconFor = (code: string) => {
    if (mode === "rehab") return <Stretch width={24} height={24} />;
    if (code.includes("single_leg")) return <Balance width={24} height={24} />;
    if (code === "weight_bearing_lunge_test") return <Check width={24} height={24} />;
    return <Activity width={24} height={24} />;
  };

  const repInfoFor = (code: string) => {
    if (code.includes("single_leg")) return t("exercise.hold");
    if (code === "squat") return t("exercise.repsUnlimited");
    if (code === "weight_bearing_lunge_test") return t("exercise.trials");
    return t("exercise.reps");
  };

  return (
    <>
      <Link className="back-link" to="/mode">
        <ArrowLeft />
        {t("common.back")}
      </Link>
      <DashTopbar
        title={t("exercise.title")}
        subtitle={mode === "rehab" ? t("exercise.descRehab") : t("exercise.descFunc")}
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

      <div
        className={
          "ex-grid" +
          (mode === "functional" || exercises.some((e) => imageFor(e.code)) ? " bento" : "")
        }
      >
        {exercises.map((exercise) =>
          imageFor(exercise.code) ? (
            /* Image-dominant bento card — reused as-is for any exercise with a real thumbnail. */
            <Link
              className="ex-card reveal"
              to="/camera"
              key={exercise.code}
              onClick={() => setExerciseCode(exercise.code)}
            >
              <div className="ex-img">
                <img
                  src={imageFor(exercise.code)!}
                  alt={exercise.name}
                  style={{ width: "100%", height: "100%", objectFit: "cover" }}
                />
                <span className="ex-go">
                  <ArrowRight width={14} height={14} />
                </span>
              </div>
              <div className="ex-body">
                <span className="ex-eyebrow">
                  {exercise.view_guidance === "front_view"
                    ? t("exercise.frontView")
                    : t("exercise.sideView")}{" "}
                  · {repInfoFor(exercise.code)}
                </span>
                <h3>{exercise.name}</h3>
                <div className="ex-meta">
                  <span className="chip">
                    {t("common." + (mode === "functional" ? "functional" : "rehab"))}
                  </span>
                  {mode === "rehab" && <span className="chip">{t("exercise.configurable")}</span>}
                </div>
              </div>
            </Link>
          ) : (
            /* Rehab mode: original compact card */
            <Link
              className="ex-card reveal"
              to="/camera"
              key={exercise.code}
              onClick={() => setExerciseCode(exercise.code)}
            >
              <div className="ex-top">
                <span className="big-ic">{iconFor(exercise.code)}</span>
                <span className="go" style={{ color: "var(--accent-text)" }}>
                  <ArrowRight />
                </span>
              </div>
              <h3>{exercise.name}</h3>
              <p>{exercise.description}</p>
              <div className="ex-meta">
                <span className="chip">
                  {exercise.view_guidance === "front_view"
                    ? t("exercise.frontView")
                    : t("exercise.sideView")}
                </span>
                <span className="chip">{t("exercise.configurable")}</span>
              </div>
            </Link>
          ),
        )}
      </div>

      {!loading && exercises.length === 0 && (
        <p className="muted center" style={{ padding: "28px 0" }}>
          {t("exercise.empty")}
        </p>
      )}
    </>
  );
}
