// REST client for reminders. Delivery is calendar-link based: Google Calendar URL
// plus downloadable .ics, both computed server-side.
import { apiRequest, API_BASE_URL, TOKEN_KEY } from "./apiClient";

export type ReminderFrequency = "once" | "daily" | "mwf" | "weekly";

export type Reminder = {
  id: string;
  title: string;
  reminder_time: string;
  frequency: ReminderFrequency | null;
  is_active: boolean;
  exercise_code: string | null;
  last_completed_at: string | null;
  created_at: string;
  is_due: boolean;
  exercise_name: string | null;
  exercise_mode: "functional" | "rehab" | string | null;
  google_calendar_url: string;
  ics_url: string;
};

export type ReminderCreatePayload = {
  title: string;
  reminder_time: string;
  frequency?: ReminderFrequency | null;
  exercise_code?: string | null;
};

export type ReminderUpdatePayload = Partial<ReminderCreatePayload> & {
  is_active?: boolean;
};

export const reminderService = {
  list() {
    return apiRequest<Reminder[]>("/api/reminders");
  },
  create(payload: ReminderCreatePayload) {
    return apiRequest<Reminder>("/api/reminders", { method: "POST", body: payload });
  },
  update(id: string, payload: ReminderUpdatePayload) {
    return apiRequest<Reminder>(`/api/reminders/${id}`, { method: "PATCH", body: payload });
  },
  complete(id: string) {
    return apiRequest<Reminder>(`/api/reminders/${id}/complete`, { method: "POST" });
  },
  remove(id: string) {
    return apiRequest<void>(`/api/reminders/${id}`, { method: "DELETE" });
  },
  /** Fire-and-forget completion for the reminder that launched the session. */
  completeIfLaunched(reminderId: string | null) {
    if (!reminderId) return;
    reminderService
      .complete(reminderId)
      .then(() => console.log("[reminders] auto-completed launching reminder", reminderId))
      .catch((err) => console.warn("[reminders] auto-complete failed (non-blocking)", err));
  },
  /** Fetches the .ics as a Blob and triggers a browser download -- the endpoint
   * returns `text/calendar`, not JSON, so this bypasses apiRequest directly. */
  async downloadIcs(id: string, filename = "reminder.ics") {
    const token = localStorage.getItem(TOKEN_KEY);
    const response = await fetch(`${API_BASE_URL}/api/reminders/${id}/export.ics`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!response.ok) throw new Error("Could not download the calendar file.");
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  },
};
