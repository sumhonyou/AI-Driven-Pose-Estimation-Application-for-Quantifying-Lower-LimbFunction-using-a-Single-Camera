// Stage 7.3: real reminders, backed by GET/POST/PATCH/DELETE /api/reminders.
// Delivery is calendar-link based (Google Calendar URL + downloadable .ics,
// both computed server-side) -- no email, no push, no scheduler (task.md's
// "keep it simple" note for this stage). Clicking a reminder tied to an
// exercise deep-links straight into that exercise's camera setup page.
import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { DashTopbar } from "../layouts/DashboardLayout";
import { Plus, Check, Clock, Calendar, Download, Trash, Alert } from "../components/Icons";
import Dropdown from "../components/Dropdown";
import { useReminders } from "../reminders";
import { useSessionFlow } from "../session";
import {
  reminderService,
  type Reminder,
  type ReminderFrequency,
} from "../services/reminderService";
import { exerciseService } from "../services/exerciseService";
import { useReveal } from "../useReveal";
import type { Exercise } from "../types/api";

const NO_EXERCISE = "";
const FREQUENCIES: ReminderFrequency[] = ["once", "daily", "mwf", "weekly"];

type StatusFilter = "all" | "due" | "upcoming" | "completed";
type FreqFilter = "all" | ReminderFrequency;

function formatWhen(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

/** True when the completed chip should show (not due; once forever / recurring today). */
function isCompletedVisible(r: Reminder) {
  if (!r.last_completed_at || r.is_due) return false;
  if ((r.frequency ?? "once") === "once") return true;
  const done = new Date(r.last_completed_at);
  const now = new Date();
  return done.toDateString() === now.toDateString();
}

/** Due first, then soonest time; completed items sink to the bottom. */
function sortReminders(list: Reminder[]) {
  return [...list].sort((a, b) => {
    const aDone = isCompletedVisible(a) ? 1 : 0;
    const bDone = isCompletedVisible(b) ? 1 : 0;
    if (aDone !== bDone) return aDone - bDone;
    if (a.is_due !== b.is_due) return a.is_due ? -1 : 1;
    return new Date(a.reminder_time).getTime() - new Date(b.reminder_time).getTime();
  });
}

// datetime-local inputs want "YYYY-MM-DDTHH:mm" in *local* time, with no
// timezone suffix -- new Date(...).toISOString() would silently shift it.
function defaultDateTimeLocal() {
  const d = new Date(Date.now() + 60 * 60 * 1000); // an hour from now
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function ReminderFormModal({
  exercises,
  onClose,
  onCreated,
}: {
  exercises: Exercise[];
  onClose: () => void;
  onCreated: () => void;
}) {
  const { t } = useTranslation();
  const [title, setTitle] = useState("");
  const [when, setWhen] = useState(defaultDateTimeLocal);
  const [frequency, setFrequency] = useState<ReminderFrequency>("once");
  const [exerciseCode, setExerciseCode] = useState(NO_EXERCISE);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const exerciseOptions = [
    { value: NO_EXERCISE, label: t("reminders.noExercise") },
    ...exercises.map((e) => ({ value: e.code, label: e.name })),
  ];

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!title.trim() || !when) return;
    setSubmitting(true);
    setError("");
    try {
      await reminderService.create({
        title: title.trim(),
        reminder_time: new Date(when).toISOString(),
        frequency,
        exercise_code: exerciseCode || null,
      });
      onCreated();
      onClose();
    } catch {
      setError(t("reminders.createError"));
    } finally {
      setSubmitting(false);
    }
  };

  return createPortal(
    <div className="reminder-modal-overlay" role="dialog" aria-modal="true">
      <div className="reminder-modal-card">
        <h3>{t("reminders.formTitle")}</h3>
        <form onSubmit={submit} noValidate>
          <div className="field">
            <label htmlFor="rem-title">{t("reminders.fieldTitle")}</label>
            <input
              id="rem-title"
              className="input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder={t("reminders.fieldTitlePh")}
              required
            />
          </div>
          <div className="field-row">
            <div className="field">
              <label htmlFor="rem-when">{t("reminders.fieldWhen")}</label>
              <input
                id="rem-when"
                className="input"
                type="datetime-local"
                value={when}
                onChange={(e) => setWhen(e.target.value)}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="rem-freq">{t("reminders.fieldFrequency")}</label>
              <select
                id="rem-freq"
                className="select"
                value={frequency}
                onChange={(e) => setFrequency(e.target.value as ReminderFrequency)}
              >
                {FREQUENCIES.map((f) => (
                  <option key={f} value={f}>
                    {t("reminders.freq_" + f)}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="field">
            <label>{t("reminders.fieldExercise")}</label>
            <Dropdown
              options={exerciseOptions}
              value={exerciseCode}
              onChange={setExerciseCode}
              placeholder={t("reminders.noExercise")}
              ariaLabel={t("reminders.fieldExercise")}
            />
          </div>
          {error && (
            <p className="field-error">
              <Alert />
              {error}
            </p>
          )}
          <div className="reminder-modal-actions">
            <button
              type="button"
              className="btn btn-ghost btn-block"
              onClick={onClose}
              disabled={submitting}
            >
              {t("common.cancel")}
            </button>
            <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
              {t("reminders.save")}
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body,
  );
}

export default function Reminders() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const { reminders, refresh, removeOptimistic } = useReminders();
  const { resetSession, setMode, setExerciseCode } = useSessionFlow();
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [freqFilter, setFreqFilter] = useState<FreqFilter>("all");
  // Reminders load async via RemindersProvider, after DashboardLayout's own
  // useReveal([pathname]) has already set up its IntersectionObserver -- without
  // this, cards that don't exist yet at that point never get watched and stay
  // invisible (opacity:0 from .reveal), same bug class as Report.tsx guards against.
  useReveal([reminders, statusFilter, freqFilter]);

  useEffect(() => {
    let cancelled = false;
    exerciseService.list().then((data) => {
      if (!cancelled) setExercises(data);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = useMemo(() => {
    const list = reminders.filter((r) => {
      if (statusFilter === "due" && !r.is_due) return false;
      if (statusFilter === "completed" && !isCompletedVisible(r)) return false;
      if (statusFilter === "upcoming" && (r.is_due || isCompletedVisible(r))) return false;
      if (freqFilter !== "all" && (r.frequency ?? "once") !== freqFilter) return false;
      return true;
    });
    return sortReminders(list);
  }, [reminders, statusFilter, freqFilter]);

  const complete = (id: string) => reminderService.complete(id).then(refresh);

  // Remove from UI first, then hit the API; roll back with refresh if delete fails.
  const remove = async (id: string) => {
    removeOptimistic(id);
    console.log("[reminders] deleted locally", id);
    try {
      await reminderService.remove(id);
    } catch (err) {
      console.warn("[reminders] delete failed, refreshing list", err);
      await refresh();
    }
  };

  const downloadIcs = (r: Reminder) =>
    reminderService.downloadIcs(
      r.id,
      `physiofit-${r.title.toLowerCase().replace(/\s+/g, "-")}.ics`,
    );

  // Gate the deep-link, not the reminder: a reminder tied to a since-retired
  // exercise (exercise_name absent from the server's response) stays visible
  // and editable, it just can't be clicked into a session.
  const openExercise = (r: Reminder) => {
    if (!r.exercise_code || !r.exercise_name) return;
    resetSession();
    setMode(r.exercise_mode === "rehab" ? "rehab" : "functional");
    setExerciseCode(r.exercise_code);
    nav("/camera");
  };

  const statusOptions = [
    { value: "all", label: t("reminders.filterStatusAll") },
    { value: "due", label: t("reminders.due") },
    { value: "upcoming", label: t("reminders.upcoming") },
    { value: "completed", label: t("reminders.completed") },
  ];
  const freqOptions = [
    { value: "all", label: t("reminders.filterFreqAll") },
    ...FREQUENCIES.map((f) => ({ value: f, label: t("reminders.freq_" + f) })),
  ];

  return (
    <>
      <DashTopbar
        title={t("reminders.title")}
        subtitle={t("reminders.desc")}
        actions={
          <button className="btn btn-primary" onClick={() => setShowForm(true)}>
            <Plus />
            {t("reminders.add")}
          </button>
        }
      />

      {reminders.length > 0 && (
        <div className="rem-toolbar reveal">
          <div className="rem-filter">
            <span className="rem-filter-label">{t("reminders.filterStatus")}</span>
            <Dropdown
              options={statusOptions}
              value={statusFilter}
              onChange={(v) => setStatusFilter(v as StatusFilter)}
              placeholder={t("reminders.filterStatusAll")}
              ariaLabel={t("reminders.filterStatus")}
            />
          </div>
          <div className="rem-filter">
            <span className="rem-filter-label">{t("reminders.filterFrequency")}</span>
            <Dropdown
              options={freqOptions}
              value={freqFilter}
              onChange={(v) => setFreqFilter(v as FreqFilter)}
              placeholder={t("reminders.filterFreqAll")}
              ariaLabel={t("reminders.filterFrequency")}
            />
          </div>
        </div>
      )}

      {reminders.length === 0 && <p className="muted reveal">{t("reminders.empty")}</p>}
      {reminders.length > 0 && filtered.length === 0 && (
        <p className="muted reveal">{t("reminders.filterEmpty")}</p>
      )}

      <div className="rem-list">
        {filtered.map((r) => (
          <div className={"rem-card reveal" + (isCompletedVisible(r) ? " is-done" : "")} key={r.id}>
            <button
              className={"rem-check" + (isCompletedVisible(r) ? " done" : "")}
              onClick={() => complete(r.id)}
              aria-label={t("reminders.markDone")}
            >
              <Check />
            </button>
            <div
              className="rem-body"
              style={{ flex: 1, cursor: r.exercise_name ? "pointer" : "default" }}
              onClick={() => openExercise(r)}
              title={
                r.exercise_name ? t("reminders.openExercise", { name: r.exercise_name }) : undefined
              }
            >
              <b>{r.title}</b>
              <span>{r.exercise_name ?? t("reminders.noExercise")}</span>
            </div>
            {/* Kept as a sibling of .rem-body, not nested inside it -- any
                <span> inside .rem-body is force-styled as the muted subtitle
                line (.rem-body span), which would swallow this chip's pill
                look (found live-testing: it rendered as a full-width bar). */}
            {r.is_due && <span className="chip chip-due">{t("reminders.due")}</span>}
            {isCompletedVisible(r) && (
              <span className="chip chip-completed">{t("reminders.completed")}</span>
            )}
            <span className="chip">{t("reminders.freq_" + (r.frequency ?? "once"))}</span>
            <span
              className="rem-time"
              style={{ display: "inline-flex", alignItems: "center", gap: 6 }}
            >
              <Clock width={15} height={15} />
              {formatWhen(r.reminder_time)}
            </span>
            <div className="rem-actions">
              <a
                className="btn btn-ghost btn-icon rem-tip"
                href={r.google_calendar_url}
                target="_blank"
                rel="noreferrer"
                data-tip={t("reminders.tipGoogleCalendar")}
                aria-label={t("reminders.tipGoogleCalendar")}
              >
                <Calendar width={16} height={16} />
              </a>
              <button
                type="button"
                className="btn btn-ghost btn-icon rem-tip"
                onClick={() => downloadIcs(r)}
                data-tip={t("reminders.tipDownloadIcs")}
                aria-label={t("reminders.tipDownloadIcs")}
              >
                <Download width={16} height={16} />
              </button>
              <button
                type="button"
                className="btn btn-ghost btn-icon rem-tip"
                onClick={() => remove(r.id)}
                data-tip={t("reminders.tipDelete")}
                aria-label={t("reminders.tipDelete")}
              >
                <Trash width={16} height={16} />
              </button>
            </div>
          </div>
        ))}
      </div>
      {showForm && (
        <ReminderFormModal
          exercises={exercises}
          onClose={() => setShowForm(false)}
          onCreated={refresh}
        />
      )}
    </>
  );
}
