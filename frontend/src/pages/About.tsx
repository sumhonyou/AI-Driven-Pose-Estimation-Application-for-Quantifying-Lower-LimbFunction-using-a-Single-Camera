import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ArrowRight } from "../components/Icons";
import { useReveal } from "../useReveal";

function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mq.matches);
    const onChange = () => setReduced(mq.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);
  return reduced;
}

/** Scroll progress 0→1 while the pinned hero stage is in view. */
function useHeroPinProgress(stageRef: React.RefObject<HTMLElement | null>, enabled: boolean) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!enabled) {
      setProgress(0);
      return;
    }
    const stage = stageRef.current;
    if (!stage) return;

    const update = () => {
      const rect = stage.getBoundingClientRect();
      const total = Math.max(stage.offsetHeight - window.innerHeight, 1);
      const scrolled = Math.min(Math.max(-rect.top, 0), total);
      setProgress(scrolled / total);
    };

    update();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update, { passive: true });
    return () => {
      window.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
    };
  }, [stageRef, enabled]);

  return progress;
}

export default function About() {
  const { t } = useTranslation();
  const reducedMotion = usePrefersReducedMotion();
  const stageRef = useRef<HTMLElement>(null);
  const progress = useHeroPinProgress(stageRef, !reducedMotion);
  useReveal([t("about.heroTitle")]);

  // Hero soft: title holds, then fades + lifts as the next section arrives.
  const heroOpacity = reducedMotion ? 1 : Math.max(0, 1 - progress * 1.35);
  const heroTranslate = reducedMotion ? 0 : progress * -48;
  const heroScale = reducedMotion ? 1 : 1 - progress * 0.06;

  const features = [
    t("about.feature1"),
    t("about.feature2"),
    t("about.feature3"),
    t("about.feature4"),
    t("about.feature5"),
    t("about.feature6"),
    t("about.feature7"),
    t("about.feature8"),
  ];

  return (
    <main className="about-page">
      <section ref={stageRef} className="about-hero-stage" aria-label={t("about.heroTitle")}>
        <div className="about-hero-pin">
          <div
            className="about-hero-inner"
            style={{
              opacity: heroOpacity,
              transform: `translate3d(0, ${heroTranslate}px, 0) scale(${heroScale})`,
            }}
          >
            <p className="about-hero-kicker">{t("about.heroKicker")}</p>
            <h1 className="about-hero-title">{t("about.heroTitle")}</h1>
            <p className="about-hero-sub">{t("about.heroSub")}</p>
          </div>
          {!reducedMotion && (
            <p
              className="about-hero-scroll-hint"
              aria-hidden="true"
              style={{ opacity: Math.max(0, 1 - progress * 2.2) }}
            >
              {t("about.scrollHint")}
            </p>
          )}
        </div>
      </section>

      <section className="about-body wrap">
        <p className="about-section-label reveal">{t("about.whatLabel")}</p>
        <div className="about-stagger">
          <div className="about-block about-block--left reveal">
            <h2 className="about-heading">{t("about.whatTitle")}</h2>
            <p>{t("about.whatP1")}</p>
            <p>{t("about.whatP2")}</p>
          </div>
          <div className="about-block about-block--right reveal">
            <p>{t("about.whatP3")}</p>
            <p>{t("about.whatP4")}</p>
          </div>
        </div>

        <p className="about-section-label reveal">{t("about.whoLabel")}</p>
        <div className="about-stagger">
          <div className="about-block about-block--left reveal">
            <h2 className="about-heading">{t("about.whoTitle")}</h2>
            <p>{t("about.whoP1")}</p>
          </div>
          <div className="about-block about-block--right reveal">
            <ul className="about-audience">
              <li>{t("about.whoItem1")}</li>
              <li>{t("about.whoItem2")}</li>
              <li>{t("about.whoItem3")}</li>
              <li>{t("about.whoItem4")}</li>
            </ul>
            <p>{t("about.whoP2")}</p>
          </div>
        </div>

        <p className="about-section-label reveal">{t("about.featuresLabel")}</p>
        <div className="about-stagger">
          <div className="about-block about-block--left reveal">
            <h2 className="about-heading">{t("about.featuresTitle")}</h2>
            <p>{t("about.featuresLead")}</p>
          </div>
          <div className="about-block about-block--right reveal">
            <ul className="about-features">
              {features.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </div>

        <aside className="about-disclaimer reveal">
          <p>{t("about.disclaimer")}</p>
        </aside>

        <div className="about-cta reveal">
          <h2 className="about-heading">{t("about.ctaTitle")}</h2>
          <p>{t("about.ctaLead")}</p>
          <div className="about-cta-actions">
            <Link className="btn btn-primary" to="/mode">
              {t("about.ctaPrimary")}
              <ArrowRight />
            </Link>
            <a className="btn btn-ghost" href="/#how">
              {t("about.ctaSecondary")}
            </a>
          </div>
        </div>
      </section>
    </main>
  );
}
