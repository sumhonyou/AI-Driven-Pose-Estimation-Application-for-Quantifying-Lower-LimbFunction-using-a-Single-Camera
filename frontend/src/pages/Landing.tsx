import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Disclaimer } from "../components/Controls";
import PoseFigure from "../components/PoseFigure";
import {
  ArrowRight,
  Play,
  Camera,
  User,
  Chart,
  Clock,
  Activity,
  ShieldCheck,
} from "../components/Icons";
import stsImage from "../assets/exercise type/sit to stand.png";
import slsImage from "../assets/exercise type/Single Leg Stance pic.png";
import wbltImage from "../assets/exercise type/WBLT.png";
import squatImage from "../assets/exercise type/Squat.png";

export default function Landing() {
  const { t } = useTranslation();

  const checksA = [
    { img: stsImage, b: t("landing.s2sName"), s: t("landing.s2sMeta") },
    { img: slsImage, b: t("landing.slsName"), s: t("landing.slsMeta") },
    { img: wbltImage, b: t("landing.wbltName"), s: t("landing.wbltMeta") },
  ];
  const checksB = [
    { b: t("landing.romName"), s: t("landing.romDesc") },
    { b: t("landing.tempoName"), s: t("landing.tempoDesc") },
    { b: t("landing.stabName"), s: t("landing.stabDesc") },
  ];
  const steps = [
    { icon: <Camera />, h: t("landing.step1Title"), p: t("landing.step1Desc") },
    { icon: <User />, h: t("landing.step2Title"), p: t("landing.step2Desc") },
    { icon: <Chart />, h: t("landing.step3Title"), p: t("landing.step3Desc") },
    { icon: <Clock />, h: t("landing.step4Title"), p: t("landing.step4Desc") },
  ];

  return (
    <div className="page page-landing">
      {/* Hero: copy left, pose skeleton + scan animation right */}
      <header className="lp-hero">
        <div className="wrap lp-hero-grid">
          <div className="lp-hero-copy">
            <h1 className="reveal lp-title">
              <span className="lp-title-line">{t("landing.titleLine1")}</span>
              <span className="lp-title-line">{t("landing.titleLine2")}</span>
              <span className="lp-title-hl hl">{t("landing.titleHl")}</span>
            </h1>
            <p className="lp-lead reveal">{t("landing.lead")}</p>
            <div className="lp-cta-row reveal">
              <Link className="btn btn-primary btn-lg" to="/mode">
                {t("landing.ctaPrimary")}
                <ArrowRight />
              </Link>
              <a className="btn btn-ghost btn-lg" href="#how">
                <Play />
                {t("landing.ctaSecondary")}
              </a>
            </div>
            <ul className="lp-trust reveal">
              <li>
                <strong>3</strong>
                <span>{t("landing.stat1")}</span>
              </li>
              <li>
                <strong>33</strong>
                <span>{t("landing.stat2")}</span>
              </li>
              <li>
                <strong className="lp-trust-accent">{t("landing.stat3num")}</strong>
                <span>{t("landing.stat3")}</span>
              </li>
            </ul>
          </div>

          <div className="lp-hero-media reveal">
            <div className="device">
              <div className="device-screen">
                <div className="scan-line" aria-hidden="true" />
                <PoseFigure />
              </div>
              <div className="float-card tl">
                <span className="ic lime">
                  <Activity />
                </span>
                <div>
                  <small>{t("landing.kneeRom")}</small>
                  <strong>
                    108° · <span className="band-good">{t("common.good")}</span>
                  </strong>
                </div>
              </div>
              <div className="float-card br">
                <span className="ic em">
                  <ShieldCheck />
                </span>
                <div>
                  <small>{t("landing.captureQuality")}</small>
                  <strong>92%</strong>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="wrap lp-disclaimer-wrap reveal">
          <Disclaimer text={t("landing.disclaimer")} />
        </div>
      </header>

      {/* Modules: asymmetric feature + panel (not two equal cards) */}
      <section className="lp-section lp-modules" id="modules">
        <div className="wrap">
          <div className="lp-section-head reveal">
            <span className="lp-eyebrow">{t("landing.modEyebrow")}</span>
            <h2>{t("landing.modTitle")}</h2>
            <p>{t("landing.modLead")}</p>
          </div>

          <div className="lp-mod-split">
            <article className="lp-mod-feature reveal">
              <div className="lp-mod-kicker">{t("landing.modATag")}</div>
              <h3>{t("landing.modATitle")}</h3>
              <p>{t("landing.modADesc")}</p>
              <ul className="lp-check-tiles">
                {checksA.map((c) => (
                  <li key={c.b}>
                    <img src={c.img} alt="" width={72} height={72} />
                    <div>
                      <b>{c.b}</b>
                      <span>{c.s}</span>
                    </div>
                  </li>
                ))}
              </ul>
            </article>

            <article className="lp-mod-panel reveal">
              <div className="lp-mod-panel-media" aria-hidden="true">
                <img src={squatImage} alt="" />
              </div>
              <div className="lp-mod-panel-body">
                <div className="lp-mod-kicker">{t("landing.modBTag")}</div>
                <h3>{t("landing.modBTitle")}</h3>
                <p>{t("landing.modBDesc")}</p>
                <ul className="lp-aspect-list">
                  {checksB.map((c) => (
                    <li key={c.b}>
                      <b>{c.b}</b>
                      <span>{c.s}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </article>
          </div>
        </div>
      </section>

      {/* How: vertical timeline — different layout family from modules */}
      <section className="lp-section lp-how" id="how">
        <div className="wrap">
          <div className="lp-section-head reveal">
            <h2>{t("landing.howTitle")}</h2>
          </div>
          <ol className="lp-timeline">
            {steps.map((s) => (
              <li className="lp-timeline-item reveal" key={s.h}>
                <span className="lp-timeline-icon">{s.icon}</span>
                <div className="lp-timeline-body">
                  <h3>{s.h}</h3>
                  <p>{s.p}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Closing CTA: full-bleed brand band */}
      <section className="lp-section lp-closing">
        <div className="wrap">
          <div className="lp-closing-band reveal">
            <div className="lp-closing-copy">
              <h2>{t("landing.ctaTitle")}</h2>
              <p>{t("landing.ctaLead")}</p>
            </div>
            <div className="lp-cta-row">
              <Link className="btn btn-primary btn-lg" to="/dashboard">
                {t("landing.ctaOpen")}
                <ArrowRight />
              </Link>
              <a className="btn btn-ghost btn-lg lp-btn-on-dark" href="#modules">
                {t("landing.ctaExplore")}
              </a>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
