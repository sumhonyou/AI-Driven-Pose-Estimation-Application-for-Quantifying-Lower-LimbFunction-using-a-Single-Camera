import { useState, type ReactNode } from "react";
import { NavLink, Outlet, useLocation, Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Logo, ThemeToggle, FontSizeControl, LanguageSwitcher } from "../components/Controls";
import { Grid, CirclePlus, History, Chart, Bell, User, Menu, Close } from "../components/Icons";
import { useReveal } from "../useReveal";
import { useAuth } from "../auth";

export default function DashboardLayout() {
  const { t } = useTranslation();
  const { pathname } = useLocation();
  const nav = useNavigate();
  const { logout } = useAuth();
  const [open, setOpen] = useState(false);
  useReveal([pathname]);

  const close = () => setOpen(false);
  const handleLogout = () => {
    logout();
    close();
    nav("/login");
  };

  return (
    <div className="app">
      {open && <div className="scrim" onClick={close} />}
      <aside className={"side" + (open ? " open" : "")}>
        <Logo to="/dashboard" />
        <div className="side-group">{t("dash.sideOverview")}</div>
        <nav className="side-nav" onClick={close}>
          <NavLink to="/dashboard" end className={({ isActive }) => (isActive ? "active" : "")}><Grid />{t("dash.navDashboard")}</NavLink>
          <NavLink to="/mode" className={({ isActive }) => (isActive ? "active" : "")}><CirclePlus />{t("dash.navNew")}</NavLink>
          <NavLink to="/history" className={({ isActive }) => (isActive ? "active" : "")}><History />{t("dash.navHistory")}</NavLink>
          <NavLink to="/dashboard" className={() => ""}><Chart />{t("dash.navProgress")}</NavLink>
        </nav>
        <div className="side-group">{t("dash.sideAccount")}</div>
        <nav className="side-nav" onClick={close}>
          <NavLink to="/reminders" className={({ isActive }) => (isActive ? "active" : "")}><Bell />{t("dash.navReminders")}</NavLink>
          <NavLink to="/profile" className={({ isActive }) => (isActive ? "active" : "")}><User />{t("dash.navProfile")}</NavLink>
        </nav>
        <div className="side-foot">
          <div className="side-card">
            <b>{t("dash.sideCardTitle")}</b>
            <p>{t("dash.sideCardBody")}</p>
            <Link className="btn btn-primary btn-block" to="/mode" onClick={close}>{t("common.startNow")}</Link>
          </div>
          <button className="btn btn-ghost btn-block" style={{ marginTop: 12 }} onClick={handleLogout}>{t("auth.logout")}</button>
        </div>
      </aside>

      <div style={{ minWidth: 0 }}>
        <div className="dash-mobilebar">
          <Logo to="/dashboard" />
          <button className="nav-toggle" onClick={() => setOpen((o) => !o)} aria-label={t("nav.menu")}>
            {open ? <Close /> : <Menu />}
          </button>
        </div>
        <main className="main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

// Reusable dashboard page header with the standard control cluster.
export function DashTopbar({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <div className="topbar">
      <div>
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>
      <div className="topbar-actions">
        <span className="desktop-only"><FontSizeControl /></span>
        <ThemeToggle />
        <LanguageSwitcher />
        {actions}
      </div>
    </div>
  );
}
