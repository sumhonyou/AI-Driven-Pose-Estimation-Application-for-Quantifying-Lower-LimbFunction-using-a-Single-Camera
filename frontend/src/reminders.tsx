/* eslint-disable react-refresh/only-export-components */
// Shared reminder state for nav badge, due banner, dashboard, and Reminders page.
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { reminderService, type Reminder } from "./services/reminderService";

type RemindersValue = {
  reminders: Reminder[];
  dueCount: number;
  /** Soonest due reminder (by reminder_time), or null if nothing is due. */
  soonestDue: Reminder | null;
  loading: boolean;
  refresh: () => Promise<void>;
  /** Drop a reminder from local state immediately (optimistic delete). */
  removeOptimistic: (id: string) => void;
};

const RemindersContext = createContext<RemindersValue | undefined>(undefined);

/**
 * Live due-ness on the client (mirrors backend reminders_service.is_due).
 * Lets the banner/badge flip the second the scheduled time arrives, without
 * waiting for a page refresh or a server round-trip.
 */
function isDueNow(reminder: Reminder, now: Date): boolean {
  if (!reminder.is_active) return false;

  const scheduled = new Date(reminder.reminder_time);
  if (Number.isNaN(scheduled.getTime())) return false;

  const freq = (reminder.frequency ?? "once").toLowerCase();

  if (freq === "once") {
    if (now.getTime() < scheduled.getTime()) return false;
    return reminder.last_completed_at == null;
  }

  // JS getDay(): Sun=0..Sat=6 → Python weekday(): Mon=0..Sun=6
  const pyWeekday = (now.getDay() + 6) % 7;
  let dayMatches = false;
  if (freq === "daily") dayMatches = true;
  else if (freq === "mwf") dayMatches = pyWeekday === 0 || pyWeekday === 2 || pyWeekday === 4;
  else if (freq === "weekly") dayMatches = now.getDay() === scheduled.getDay();
  else return false;

  if (!dayMatches) return false;

  const nowSecs = now.getHours() * 3600 + now.getMinutes() * 60 + now.getSeconds();
  const dueSecs =
    scheduled.getHours() * 3600 + scheduled.getMinutes() * 60 + scheduled.getSeconds();
  if (nowSecs < dueSecs) return false;

  if (reminder.last_completed_at) {
    const done = new Date(reminder.last_completed_at);
    if (done.toDateString() === now.toDateString()) return false;
  }
  return true;
}

function withLiveDue(list: Reminder[], now: Date): Reminder[] {
  return list.map((r) => ({ ...r, is_due: isDueNow(r, now) }));
}

export function RemindersProvider({ children }: { children: ReactNode }) {
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [loading, setLoading] = useState(true);
  // Tick every second so is_due flips live when the clock reaches reminder_time.
  const [nowMs, setNowMs] = useState(() => Date.now());

  const refresh = useCallback(async () => {
    try {
      const list = await reminderService.list();
      setReminders(list);
      console.log("[reminders] list refreshed", list.length);
    } catch (err) {
      console.warn("[reminders] refresh failed", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const removeOptimistic = useCallback((id: string) => {
    setReminders((prev) => prev.filter((r) => r.id !== id));
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    const id = window.setInterval(() => setNowMs(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, []);

  // Re-sync from server when the tab is focused again (sleep / other window).
  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState === "visible") refresh();
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => document.removeEventListener("visibilitychange", onVisible);
  }, [refresh]);

  const value = useMemo(() => {
    const live = withLiveDue(reminders, new Date(nowMs));
    const due = live.filter((r) => r.is_due);
    const soonestDue =
      due.length === 0
        ? null
        : [...due].sort(
            (a, b) => new Date(a.reminder_time).getTime() - new Date(b.reminder_time).getTime(),
          )[0];
    return {
      reminders: live,
      dueCount: due.length,
      soonestDue,
      loading,
      refresh,
      removeOptimistic,
    };
  }, [reminders, nowMs, loading, refresh, removeOptimistic]);

  return <RemindersContext.Provider value={value}>{children}</RemindersContext.Provider>;
}

export function useReminders() {
  const context = useContext(RemindersContext);
  if (!context) throw new Error("useReminders must be used inside RemindersProvider");
  return context;
}
