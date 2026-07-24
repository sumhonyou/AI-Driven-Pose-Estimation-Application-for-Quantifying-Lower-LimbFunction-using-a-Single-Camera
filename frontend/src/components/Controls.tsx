import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { usePreferences } from "../preferences";
import { LANGUAGES } from "../i18n";
import { Sun, Moon, Globe, Check } from "./Icons";
import CtrlHint from "./CtrlHint";
import logoLight from "../assets/Physiofit_Logo-removebg-preview.png";
import logoDark from "../assets/logo_in_dark_themed-removebg-preview.png";

export function Logo({ to = "/", size = "nav" }: { to?: string; size?: "nav" | "footer" }) {
  const { theme } = usePreferences();
  const logoImg = theme === "dark" ? logoDark : logoLight;
  return (
    <Link
      className={"brand" + (size === "footer" ? " brand--footer" : "")}
      to={to}
      aria-label="PhysioFit home"
    >
      <span className="logo">
        <img src={logoImg} alt="PhysioFit" />
      </span>
    </Link>
  );
}

export function ThemeToggle() {
  const { theme, toggleTheme } = usePreferences();
  const { t } = useTranslation();
  return (
    <CtrlHint text={t("nav.themeHint")}>
      <button
        className="ctrl theme-toggle icon-btn"
        onClick={toggleTheme}
        aria-label={t("nav.theme")}
      >
        {theme === "light" ? <Moon /> : <Sun />}
      </button>
    </CtrlHint>
  );
}

export function FontSizeControl() {
  const { fontScale, setFontScale } = usePreferences();
  const { t } = useTranslation();
  return (
    <CtrlHint text={t("nav.fontSizeHint")}>
      <div className="fs-seg" role="group" aria-label={t("nav.fontSize")}>
        {[1, 2, 3].map((s) => (
          <button
            key={s}
            className={fontScale === s ? "on" : ""}
            onClick={() => setFontScale(s as 1 | 2 | 3)}
            aria-pressed={fontScale === s}
            aria-label={`${t("nav.fontSize")} ${s}`}
          >
            A
          </button>
        ))}
      </div>
    </CtrlHint>
  );
}

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const current = LANGUAGES.find((l) => l.code === i18n.language) ?? LANGUAGES[0];

  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [open]);

  return (
    <div className="lang" ref={ref}>
      <CtrlHint text={t("nav.languageHint")} align="end">
        <button
          className="ctrl"
          onClick={() => setOpen((o) => !o)}
          aria-haspopup="listbox"
          aria-expanded={open}
          aria-label={t("nav.language")}
        >
          <Globe />
          <span
            className="desktop-only"
            style={{
              maxWidth: 70,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {current.label}
          </span>
        </button>
      </CtrlHint>
      {open && (
        <div className="lang-menu" role="listbox">
          {LANGUAGES.map((l) => (
            <button
              key={l.code}
              className={l.code === current.code ? "on" : ""}
              role="option"
              aria-selected={l.code === current.code}
              onClick={() => {
                i18n.changeLanguage(l.code);
                setOpen(false);
              }}
            >
              <span className="flag">{l.flag}</span>
              {l.label}
              <Check className="check" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export function Disclaimer({ text }: { text: string }) {
  return (
    <div className="disclaimer">
      <Alert />
      <span>{text}</span>
    </div>
  );
}

function Alert() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 9v4M12 17h.01" />
      <path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
    </svg>
  );
}
