import { useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Logo, ThemeToggle, FontSizeControl, LanguageSwitcher } from "../components/Controls";
import { Menu, Close, ArrowRight } from "../components/Icons";
import { useReveal } from "../useReveal";

export default function PublicLayout() {
  const { t } = useTranslation();
  const { pathname } = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  useReveal([pathname]);

  return (
    <div className="page">
      <nav className="nav">
        <div className="wrap nav-inner">
          <Logo />
          <div className="nav-links">
            <a href="/#modules">{t("nav.modules")}</a>
            <a href="/#how">{t("nav.how")}</a>
            <a href="/#" onClick={(e) => e.preventDefault()}>{t("nav.clinicians")}</a>
            <a href="/#" onClick={(e) => e.preventDefault()}>{t("nav.about")}</a>
          </div>
          <div className="nav-actions">
            <span className="desktop-only"><FontSizeControl /></span>
            <ThemeToggle />
            <LanguageSwitcher />
            <Link className="btn btn-ghost desktop-only" to="/login">{t("nav.login")}</Link>
            <Link className="btn btn-primary desktop-only" to="/mode">{t("nav.startCheck")}<ArrowRight /></Link>
            <button className="nav-toggle" onClick={() => setMenuOpen((o) => !o)} aria-label={t("nav.menu")}>
              {menuOpen ? <Close /> : <Menu />}
            </button>
          </div>
        </div>
        <div className={"wrap mobile-menu" + (menuOpen ? " open" : "")}>
          <a href="/#modules" onClick={() => setMenuOpen(false)}>{t("nav.modules")}</a>
          <a href="/#how" onClick={() => setMenuOpen(false)}>{t("nav.how")}</a>
          <a href="/#" onClick={(e) => { e.preventDefault(); setMenuOpen(false); }}>{t("nav.clinicians")}</a>
          <a href="/#" onClick={(e) => { e.preventDefault(); setMenuOpen(false); }}>{t("nav.about")}</a>
          <div style={{ padding: "14px 6px 0" }}><FontSizeControl /></div>
          <div className="mm-actions">
            <Link className="btn btn-ghost" to="/login" onClick={() => setMenuOpen(false)}>{t("nav.login")}</Link>
            <Link className="btn btn-primary" to="/mode" onClick={() => setMenuOpen(false)}>{t("nav.startCheck")}<ArrowRight /></Link>
          </div>
        </div>
      </nav>

      <Outlet />

      <Footer />
    </div>
  );
}

function Footer() {
  const { t } = useTranslation();
  return (
    <footer className="footer">
      <div className="wrap">
        <div className="foot-grid">
          <div style={{ maxWidth: 340 }}>
            <Logo size="footer" />
            <p>{t("landing.footTagline")}</p>
          </div>
          <div className="foot-links">
            <div className="foot-col">
              <b>{t("landing.footProduct")}</b>
              <a href="/#modules">{t("landing.fLink1")}</a>
              <a href="/#modules">{t("landing.fLink2")}</a>
              <a href="/#how">{t("landing.fLink3")}</a>
              <Link to="/dashboard">{t("landing.fLink4")}</Link>
            </div>
            <div className="foot-col">
              <b>{t("landing.footCompany")}</b>
              <a href="/#" onClick={(e) => e.preventDefault()}>{t("landing.fLink5")}</a>
              <a href="/#" onClick={(e) => e.preventDefault()}>{t("landing.fLink6")}</a>
              <a href="/#" onClick={(e) => e.preventDefault()}>{t("landing.fLink7")}</a>
              <a href="/#" onClick={(e) => e.preventDefault()}>{t("landing.fLink8")}</a>
            </div>
          </div>
        </div>
        <div className="foot-base">
          <span>{t("landing.copyright")}</span>
          <span>{t("landing.madeFor")}</span>
        </div>
      </div>
    </footer>
  );
}
