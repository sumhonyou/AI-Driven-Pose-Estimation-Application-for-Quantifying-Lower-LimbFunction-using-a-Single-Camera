import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Disclaimer } from "../components/Controls";
import PoseFigure from "../components/PoseFigure";
import {
  ArrowRight,
  Play,
  Activity,
  ShieldCheck,
  Camera,
  User,
  Chart,
  Clock,
} from "../components/Icons";

export default function Landing() {
  const { t } = useTranslation();

  const checksA = [
    { n: "1", b: t("landing.s2sName"), s: t("landing.s2sMeta") },
    { n: "2", b: t("landing.slsName"), s: t("landing.slsMeta") },
    { n: "3", b: t("landing.wbltName"), s: t("landing.wbltMeta") },
  ];
  const checksB = [
    { b: t("landing.romName"), s: t("landing.romDesc") },
    { b: t("landing.tempoName"), s: t("landing.tempoDesc") },
    { b: t("landing.stabName"), s: t("landing.stabDesc") },
  ];
  const steps = [
    { n: "01", icon: <Camera />, h: t("landing.step1Title"), p: t("landing.step1Desc") },
    { n: "02", icon: <User />, h: t("landing.step2Title"), p: t("landing.step2Desc") },
    { n: "03", icon: <Chart />, h: t("landing.step3Title"), p: t("landing.step3Desc") },
    { n: "04", icon: <Clock />, h: t("landing.step4Title"), p: t("landing.step4Desc") },
  ];

  return (
    <div className="page">
      <header className="hero">
        <div className="wrap hero-grid">
          <div>
            <span className="pill reveal">
              <span className="dot" /> {t("landing.badge")}
            </span>
            <h1 className="reveal">
              {t("landing.title")} <span className="hl">{t("landing.titleHl")}</span>
            </h1>
            <p className="lead reveal">{t("landing.lead")}</p>
            <div className="hero-cta reveal">
              <Link className="btn btn-primary btn-lg" to="/mode">
                {t("landing.ctaPrimary")}
                <ArrowRight />
              </Link>
              <a className="btn btn-ghost btn-lg" href="#how">
                <Play />
                {t("landing.ctaSecondary")}
              </a>
            </div>
            <div className="hero-stats reveal">
              <div className="stat">
                <b>3</b>
                <span>{t("landing.stat1")}</span>
              </div>
              <div className="stat">
                <b>33</b>
                <span>{t("landing.stat2")}</span>
              </div>
              <div className="stat">
                <b>
                  <em>{t("landing.stat3num")}</em>
                </b>
                <span>{t("landing.stat3")}</span>
              </div>
            </div>
          </div>

          <div className="hero-visual reveal">
            <div className="device">
              <div className="device-screen">
                <div className="scan-line" />
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

        <div className="wrap" style={{ marginTop: 24 }}>
          <div className="reveal">
            <Disclaimer text={t("landing.disclaimer")} />
          </div>
        </div>
      </header>

      <section className="section" id="modules">
        <div className="wrap">
          <div className="sec-head reveal">
            <span className="eyebrow">{t("landing.modEyebrow")}</span>
            <h2>{t("landing.modTitle")}</h2>
            <p>{t("landing.modLead")}</p>
          </div>
          <div className="modules">
            <article className="module-card reveal">
              <span className="module-tag">{t("landing.modATag")}</span>
              <h3>{t("landing.modATitle")}</h3>
              <p>{t("landing.modADesc")}</p>
              <div className="checks">
                {checksA.map((c) => (
                  <div className="check-row" key={c.n}>
                    <span className="num">{c.n}</span>
                    <div className="txt">
                      <b>{c.b}</b>
                      <span>{c.s}</span>
                    </div>
                  </div>
                ))}
              </div>
            </article>
            <article className="module-card reveal">
              <span className="module-tag">{t("landing.modBTag")}</span>
              <h3>{t("landing.modBTitle")}</h3>
              <p>{t("landing.modBDesc")}</p>
              <div className="checks">
                {checksB.map((c) => (
                  <div className="check-row" key={c.b}>
                    <span className="num">◷</span>
                    <div className="txt">
                      <b>{c.b}</b>
                      <span>{c.s}</span>
                    </div>
                    <span className="badge-soon">{t("common.ai")}</span>
                  </div>
                ))}
              </div>
            </article>
          </div>
        </div>
      </section>

      <section className="section" id="how">
        <div className="wrap">
          <div className="sec-head reveal">
            <span className="eyebrow">{t("landing.howEyebrow")}</span>
            <h2>{t("landing.howTitle")}</h2>
          </div>
          <div className="steps">
            {steps.map((s) => (
              <div className="step reveal" key={s.n}>
                <span className="sn">{s.n}</span>
                <span className="si">{s.icon}</span>
                <h4>{s.h}</h4>
                <p>{s.p}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <div className="wrap">
          <div className="cta-strip reveal">
            <h2>{t("landing.ctaTitle")}</h2>
            <p>{t("landing.ctaLead")}</p>
            <div className="hero-cta">
              <Link className="btn btn-primary btn-lg" to="/dashboard">
                {t("landing.ctaOpen")}
                <ArrowRight />
              </Link>
              <a className="btn btn-ghost btn-lg" href="#modules">
                {t("landing.ctaExplore")}
              </a>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
