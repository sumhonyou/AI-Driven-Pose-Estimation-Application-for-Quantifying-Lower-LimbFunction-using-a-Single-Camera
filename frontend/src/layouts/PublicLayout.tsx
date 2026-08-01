import { useEffect, useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Logo, ThemeToggle, FontSizeControl, LanguageSwitcher } from "../components/Controls";
import { Menu, Close, ArrowRight } from "../components/Icons";
import ContactModal from "../components/ContactModal";
import { FEEDBACK_FORM_URL } from "../config/projectContact";
import { useReveal } from "../useReveal";

type NavSection = "modules" | "how" | "about" | null;

function useActivePublicNav(): NavSection {
  const { pathname, hash } = useLocation();
  const [section, setSection] = useState<NavSection>(null);

  useEffect(() => {
    if (pathname === "/about") {
      setSection("about");
      return;
    }
    if (pathname !== "/") {
      setSection(null);
      return;
    }

    const fromHash = (): NavSection => {
      if (hash === "#modules") return "modules";
      if (hash === "#how") return "how";
      return null;
    };

    // Prefer explicit hash clicks immediately; then refine from scroll position.
    setSection(fromHash());

    const modulesEl = document.getElementById("modules");
    const howEl = document.getElementById("how");
    if (!modulesEl || !howEl) return;

    const updateFromScroll = () => {
      const marker = window.scrollY + Math.min(160, window.innerHeight * 0.28);
      const howTop = howEl.getBoundingClientRect().top + window.scrollY;
      const modulesTop = modulesEl.getBoundingClientRect().top + window.scrollY;

      if (marker >= howTop - 40) {
        setSection("how");
      } else if (marker >= modulesTop - 40) {
        setSection("modules");
      } else {
        setSection(fromHash());
      }
    };

    updateFromScroll();
    window.addEventListener("scroll", updateFromScroll, { passive: true });
    window.addEventListener("hashchange", updateFromScroll);
    return () => {
      window.removeEventListener("scroll", updateFromScroll);
      window.removeEventListener("hashchange", updateFromScroll);
    };
  }, [pathname, hash]);

  return section;
}

export default function PublicLayout() {
  const { t } = useTranslation();
  const { pathname } = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const active = useActivePublicNav();
  useReveal([pathname]);

  return (
    <div className="page">
      <nav className="nav">
        <div className="wrap nav-inner">
          <Logo />
          <div className="nav-links">
            <a href="/#modules" className={active === "modules" ? "active" : undefined}>
              {t("nav.modules")}
            </a>
            <a href="/#how" className={active === "how" ? "active" : undefined}>
              {t("nav.how")}
            </a>
            <Link to="/about" className={active === "about" ? "active" : undefined}>
              {t("nav.about")}
            </Link>
          </div>
          <div className="nav-actions">
            <span className="desktop-only">
              <FontSizeControl />
            </span>
            <ThemeToggle />
            <LanguageSwitcher />
            <Link className="btn btn-ghost desktop-only" to="/login">
              {t("nav.login")}
            </Link>
            <Link className="btn btn-primary desktop-only" to="/mode">
              {t("nav.startCheck")}
              <ArrowRight />
            </Link>
            <button
              className="nav-toggle"
              onClick={() => setMenuOpen((o) => !o)}
              aria-label={t("nav.menu")}
            >
              {menuOpen ? <Close /> : <Menu />}
            </button>
          </div>
        </div>
        <div className={"wrap mobile-menu" + (menuOpen ? " open" : "")}>
          <a
            href="/#modules"
            className={active === "modules" ? "active" : undefined}
            onClick={() => setMenuOpen(false)}
          >
            {t("nav.modules")}
          </a>
          <a
            href="/#how"
            className={active === "how" ? "active" : undefined}
            onClick={() => setMenuOpen(false)}
          >
            {t("nav.how")}
          </a>
          <Link
            to="/about"
            className={active === "about" ? "active" : undefined}
            onClick={() => setMenuOpen(false)}
          >
            {t("nav.about")}
          </Link>
          <div style={{ padding: "14px 6px 0" }}>
            <FontSizeControl />
          </div>
          <div className="mm-actions">
            <Link className="btn btn-ghost" to="/login" onClick={() => setMenuOpen(false)}>
              {t("nav.login")}
            </Link>
            <Link className="btn btn-primary" to="/mode" onClick={() => setMenuOpen(false)}>
              {t("nav.startCheck")}
              <ArrowRight />
            </Link>
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
  const [contactOpen, setContactOpen] = useState(false);

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
              <b>{t("landing.footExplore")}</b>
              <a href="/#modules">{t("landing.fLink1")}</a>
              <a href="/#modules">{t("landing.fLink2")}</a>
              <a href="/#how">{t("landing.fLink3")}</a>
              <Link to="/dashboard">{t("landing.fLink4")}</Link>
            </div>
            <div className="foot-col">
              <b>{t("landing.footProject")}</b>
              <Link to="/about">{t("landing.fLink5")}</Link>
              <a href={FEEDBACK_FORM_URL} target="_blank" rel="noreferrer">
                {t("landing.fLink6")}
              </a>
              {/* Opens the student + supervisor contact pop-out. */}
              <button type="button" className="foot-link-btn" onClick={() => setContactOpen(true)}>
                {t("landing.fLink8")}
              </button>
            </div>
          </div>
        </div>
        <div className="foot-base">
          <span>{t("landing.copyright")}</span>
          <span>{t("landing.madeFor")}</span>
        </div>
      </div>
      {contactOpen && <ContactModal onClose={() => setContactOpen(false)} />}
    </footer>
  );
}
