"""Pure helpers for Stage 7.3 reminders: due-ness, .ics export, Google Calendar link.

Kept separate from the router so the recurrence/date logic is unit-testable with
plain objects (no DB), matching this project's existing test style (see
dashboard_service.py). Every function takes a Reminder-shaped object (duck-typed:
needs `.title`, `.reminder_time`, `.frequency`, `.is_active`, `.last_completed_at`,
`.id`) so tests can pass a SimpleNamespace instead of a real ORM row.

Deliberately no email, no OAuth, no scheduler here (task.md Stage 7.3: "keep it
simple, do not build scheduling infrastructure") -- the .ics file and Google
Calendar link hand the actual timed alert off to the user's own calendar app.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

# Recurrence vocabulary this feature supports. Anything else is treated as
# "never due" rather than guessed at (fail closed, not silently wrong).
_MWF_WEEKDAYS = (0, 2, 4)  # Mon, Wed, Fri (datetime.weekday(): Mon=0..Sun=6)


def _rrule_value(frequency: str | None) -> str | None:
    """RFC-5545 RRULE value for a frequency string, or None for a one-time reminder."""
    freq = (frequency or "once").lower()
    if freq == "daily":
        return "FREQ=DAILY"
    if freq == "mwf":
        return "FREQ=WEEKLY;BYDAY=MO,WE,FR"
    if freq == "weekly":
        return "FREQ=WEEKLY"
    return None


def is_due(reminder: Any, now: datetime) -> bool:
    """True if `reminder` has a due-but-not-yet-completed occurrence at `now`.

    This is the single source of truth for both the nav red-dot and the
    dashboard alert banner, so they can never disagree.

    - inactive reminders are never due.
    - "once" (no frequency / frequency == "once"): due once `now` reaches the
      scheduled datetime, until `last_completed_at` is ever set.
    - "daily" / "mwf" / "weekly": due once `now`'s time-of-day reaches the
      scheduled time-of-day on a matching day, and not yet completed for
      *today's* occurrence (a later `last_completed_at` on a different date
      doesn't suppress a new day's occurrence).
    - an unrecognised frequency string is never due (fail closed).
    """
    if not reminder.is_active:
        return False

    freq = (reminder.frequency or "once").lower()

    if freq == "once":
        if now < reminder.reminder_time:
            return False
        return reminder.last_completed_at is None

    if freq == "daily":
        day_matches = True
    elif freq == "mwf":
        day_matches = now.weekday() in _MWF_WEEKDAYS
    elif freq == "weekly":
        day_matches = now.weekday() == reminder.reminder_time.weekday()
    else:
        return False

    if not day_matches:
        return False
    if now.time() < reminder.reminder_time.time():
        return False
    if (
        reminder.last_completed_at is not None
        and reminder.last_completed_at.date() == now.date()
    ):
        return False
    return True


def _ics_escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def _to_utc(value: datetime) -> datetime:
    return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)


def _fmt_ics_datetime(value: datetime) -> str:
    return _to_utc(value).strftime("%Y%m%dT%H%M%SZ")


def build_ics(reminder: Any, now: datetime | None = None) -> str:
    """RFC-5545 VCALENDAR text with one VEVENT + a popup VALARM at the reminder time.

    `now` is only the DTSTAMP (when this file was generated) -- optional, tests can
    pin it; production leaves it None and stamps the real time.
    """
    if now is None:
        now = datetime.now(UTC)

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//PhysioFit//Reminders//EN",
        "BEGIN:VEVENT",
        f"UID:{reminder.id}@physiofit",
        f"DTSTAMP:{_fmt_ics_datetime(now)}",
        f"DTSTART:{_fmt_ics_datetime(reminder.reminder_time)}",
        f"SUMMARY:{_ics_escape(reminder.title)}",
        f"DESCRIPTION:{_ics_escape('PhysioFit reminder: ' + reminder.title)}",
    ]
    rrule = _rrule_value(reminder.frequency)
    if rrule:
        lines.append(f"RRULE:{rrule}")
    lines += [
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        "DESCRIPTION:PhysioFit reminder",
        "TRIGGER:-PT0M",
        "END:VALARM",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    return "\r\n".join(lines) + "\r\n"


def build_google_calendar_url(reminder: Any) -> str:
    """A prefilled 'Add to Google Calendar' link -- no OAuth, just a render URL
    the browser opens; the user's own Google account handles the rest."""
    start = _to_utc(reminder.reminder_time)
    end = start + timedelta(minutes=30)
    params = {
        "action": "TEMPLATE",
        "text": reminder.title,
        "dates": f"{start.strftime('%Y%m%dT%H%M%SZ')}/{end.strftime('%Y%m%dT%H%M%SZ')}",
        "details": f"PhysioFit reminder: {reminder.title}",
    }
    rrule = _rrule_value(reminder.frequency)
    if rrule:
        params["recur"] = f"RRULE:{rrule}"
    return "https://calendar.google.com/calendar/render?" + urlencode(params)
