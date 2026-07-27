import { useEffect, useRef, useState, type MouseEvent, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { NavLink, Outlet, useLocation, Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Logo, ThemeToggle, FontSizeControl, LanguageSwitcher } from "../components/Controls";
import AudioCueToggle from "../components/AudioCueToggle";
import {
  Grid,
  CirclePlus,
  History,
  Chart,
  Bell,
  User,
  Menu,
  Close,
  ArrowLeft,
  ArrowRight,
  LogOut,
} from "../components/Icons";
import { useReveal } from "../useReveal";
import { useAuth } from "../auth";
import { RemindersProvider, useReminders } from "../reminders";

const DISMISS_KEY = "physiofit-due-banner-dismissed";

/** Hide the due banner on reminders itself and during live capture. */
function shouldHideDueBanner(pathname: string) {
  if (pathname.startsWith("/reminders")) return true;
  return ["/sts/live", "/sls/live", "/wblt/live", "/squat/live"].some((p) =>
    pathname.startsWith(p),
  );
}

/** Floating coral due-alert; overlays pages without shifting layout. */
function DueReminderBanner() {
  const { t } = useTranslation();
  const { pathname } = useLocation();
  const { soonestDue, loading } = useReminders();
  const [dismissedId, setDismissedId] = useState<string | null>(() =>
    sessionStorage.getItem(DISMISS_KEY),
  );
  const prevDueIdRef = useRef<string | null>(null);
  const readyRef = useRef(false);

  useEffect(() => {
    if (loading) return;
    const id = soonestDue?.id ?? null;
    // First snapshot after load: keep any existing dismiss for this tab.
    if (!readyRef.current) {
      readyRef.current = true;
      prevDueIdRef.current = id;
      return;
    }
    // Live flip: nothing due → due, or a different reminder became the soonest.
    if (id && (prevDueIdRef.current === null || id !== prevDueIdRef.current)) {
      setDismissedId(null);
      sessionStorage.removeItem(DISMISS_KEY);
      console.log("[reminders] due banner shown for", id);
    }
    prevDueIdRef.current = id;
  }, [soonestDue, loading]);

  if (!soonestDue || shouldHideDueBanner(pathname) || dismissedId === soonestDue.id) {
    return null;
  }

  const name = soonestDue.exercise_name ?? soonestDue.title;

  const dismiss = (e: MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDismissedId(soonestDue.id);
    sessionStorage.setItem(DISMISS_KEY, soonestDue.id);
  };

  return createPortal(
    <div className="due-alert-banner" role="status">
      <Link to="/reminders" className="due-alert-banner-link">
        <Bell />
        <span>{t("dash.dueExerciseBanner", { name })}</span>
      </Link>
      <button
        type="button"
        className="due-alert-banner-dismiss"
        onClick={dismiss}
        aria-label={t("dash.dismissDueBanner")}
      >
        <Close />
      </button>
    </div>,
    document.body,
  );
}

function TopbarAvatar() {
  const { user } = useAuth();
  const initials = user?.full_name?.trim().slice(0, 2).toUpperCase() || "PF";
  return (
    <Link to="/profile" className="avatar" aria-label="View profile" title="View profile">
      {user?.avatar_image ? (
        <img src={user.avatar_image} alt="" className="avatar-img" />
      ) : (
        initials
      )}
    </Link>
  );
}

export default function DashboardLayout() {
  // Stage 7.3: RemindersProvider wraps the whole authed shell so both the nav
  // badge here and the Reminders/Dashboard pages (via Outlet) share one fetch.
  return (
    <RemindersProvider>
      <DashboardLayoutInner />
    </RemindersProvider>
  );
}

function DashboardLayoutInner() {
  const { t } = useTranslation();
  const { pathname } = useLocation();
  const nav = useNavigate();
  const { logout } = useAuth();
  const { dueCount } = useReminders();
  const reduceMotion = useReducedMotion();
  const [open, setOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  useReveal([pathname]);

  const close = () => setOpen(false);
  const handleLogout = () => {
    logout();
    close();
    nav("/login");
  };

  // Keep "New session" highlighted for the entire session flow including the report at the end
  const isSessionFlow = ["/mode", "/exercise", "/camera", "/live-session", "/report"].some((path) =>
    pathname.startsWith(path),
  );

  const toggleIconMotion = reduceMotion
    ? { initial: { opacity: 0 }, animate: { opacity: 1 }, exit: { opacity: 0 } }
    : {
        initial: { opacity: 0 },
        animate: { opacity: 1 },
        exit: { opacity: 0 },
      };

  return (
    <div className={"app" + (collapsed ? " sidebar-collapsed" : "")}>
      {open && <div className="scrim" onClick={close} />}
      <aside className={"side" + (open ? " open" : "")}>
        <div className="side-top">
          <Logo to="/dashboard" />
          <button
            className="sidebar-toggle"
            onClick={() => setCollapsed((value) => !value)}
            aria-label="Toggle sidebar"
            aria-pressed={collapsed}
            title="Toggle sidebar"
          >
            {/* Expanded ← collapse; collapsed → expand. Crossfade keeps the swap smooth. */}
            <AnimatePresence mode="wait" initial={false}>
              <motion.span
                key={collapsed ? "expand" : "collapse"}
                className="sidebar-toggle-icon"
                {...toggleIconMotion}
                transition={{ duration: reduceMotion ? 0 : 0.18 }}
              >
                {collapsed ? <ArrowRight /> : <ArrowLeft />}
              </motion.span>
            </AnimatePresence>
          </button>
        </div>
        <div className="side-group">{t("dash.sideOverview")}</div>
        <nav className="side-nav" onClick={close}>
          <NavLink to="/dashboard" end className={({ isActive }) => (isActive ? "active" : "")}>
            <Grid />
            <span className="nav-label">{t("dash.navDashboard")}</span>
          </NavLink>
          {/* UAT remediation (Stage R14 micro-fix): this was a plain <div
              onClick>, not a real link -- unreachable by Tab and with no
              focus-visible outline, unlike every other sidebar item. A real
              <Link> keeps the multi-route "active" logic (isSessionFlow spans
              /mode, /exercise, /camera, /live-session, /report, which
              NavLink's own isActive can't express) while restoring normal
              keyboard focusability. */}
          <Link to="/mode" className={`nav-link ${isSessionFlow ? "active" : ""}`}>
            <CirclePlus />
            <span className="nav-label">{t("dash.navNew")}</span>
          </Link>
          <NavLink to="/history" className={({ isActive }) => (isActive ? "active" : "")}>
            <History />
            <span className="nav-label">{t("dash.navHistory")}</span>
          </NavLink>
          <NavLink to="/progress" className={({ isActive }) => (isActive ? "active" : "")}>
            <Chart />
            <span className="nav-label">{t("dash.navProgress")}</span>
          </NavLink>
          {/* UAT remediation (Stage R13): reminders used to live under "Account"
              alongside Profile, which testers didn't associate with a core,
              frequently-used feature (concept scored 4.71/5 & 67% "strongest" --
              S5/R19). Relocated under "Overview" with the rest of the main flow. */}
          <NavLink to="/reminders" className={({ isActive }) => (isActive ? "active" : "")}>
            <span className="nav-icon-badge">
              <Bell />
              {dueCount > 0 && (
                <span
                  className="nav-badge-dot"
                  aria-label={t("reminders.dueBadge", { count: dueCount })}
                />
              )}
            </span>
            <span className="nav-label">{t("dash.navReminders")}</span>
          </NavLink>
        </nav>
        <div className="side-group">{t("dash.sideAccount")}</div>
        <nav className="side-nav" onClick={close}>
          <NavLink to="/profile" className={({ isActive }) => (isActive ? "active" : "")}>
            <User />
            <span className="nav-label">{t("dash.navProfile")}</span>
          </NavLink>
        </nav>
        <div className="side-foot">
          {/* Expanded: full text button. Collapsed: icon-only so logout stays reachable. */}
          <button
            className={"btn btn-ghost" + (collapsed ? " btn-icon side-logout-icon" : " btn-block")}
            onClick={handleLogout}
            aria-label={t("auth.logout")}
            title={t("auth.logout")}
          >
            {collapsed ? <LogOut /> : t("auth.logout")}
          </button>
        </div>
      </aside>

      <div style={{ minWidth: 0 }}>
        <div className="dash-mobilebar">
          <Logo to="/dashboard" />
          <button
            className="nav-toggle"
            onClick={() => setOpen((o) => !o)}
            aria-label={t("nav.menu")}
          >
            {open ? <Close /> : <Menu />}
          </button>
        </div>
        <main className="main">
          <Outlet />
        </main>
      </div>
      <DueReminderBanner />
    </div>
  );
}

// Reusable dashboard page header with the standard control cluster.
export function DashTopbar({
  title,
  subtitle,
  eyebrow,
  actions,
}: {
  title: string;
  subtitle?: string;
  /** UAT remediation (Stage R9): small uppercase label above the title (e.g.
   * "BEFORE YOU BEGIN" on the instruction page) -- optional, most pages omit it. */
  eyebrow?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="topbar">
      <div>
        {eyebrow && <p className="topbar-eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>
      <div className="topbar-actions">
        <span className="desktop-only">
          <FontSizeControl />
        </span>
        <ThemeToggle />
        <AudioCueToggle />
        <LanguageSwitcher />
        {actions}
        <TopbarAvatar />
      </div>
    </div>
  );
}
