"""Stage 7.3: reminders due-ness, .ics export, Google Calendar link -- pure functions."""

import unittest
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.api import reminders_service as svc


def _reminder(
    *,
    reminder_time: datetime,
    frequency: str | None = None,
    is_active: bool = True,
    last_completed_at: datetime | None = None,
    title: str = "Do your Sit-to-Stand check",
    id_=None,
):
    return SimpleNamespace(
        id=id_ or uuid4(),
        title=title,
        reminder_time=reminder_time,
        frequency=frequency,
        is_active=is_active,
        last_completed_at=last_completed_at,
    )


# A Wednesday, deliberately (weekday() == 2) so mwf/weekly cases are unambiguous.
_WED = datetime(2026, 7, 22, 8, 0, tzinfo=UTC)
_THU = datetime(2026, 7, 23, 8, 0, tzinfo=UTC)


class IsDueTests(unittest.TestCase):
    def test_inactive_is_never_due(self):
        r = _reminder(reminder_time=_WED, is_active=False)
        self.assertFalse(svc.is_due(r, _WED))

    def test_once_before_scheduled_time_not_due(self):
        r = _reminder(reminder_time=_WED, frequency="once")
        self.assertFalse(svc.is_due(r, _WED.replace(hour=7)))

    def test_once_at_or_after_scheduled_time_is_due(self):
        r = _reminder(reminder_time=_WED, frequency="once")
        self.assertTrue(svc.is_due(r, _WED))
        self.assertTrue(svc.is_due(r, _THU))

    def test_once_completed_is_never_due_again(self):
        r = _reminder(reminder_time=_WED, frequency="once", last_completed_at=_THU)
        self.assertFalse(svc.is_due(r, _THU))

    def test_daily_due_every_day_past_the_time(self):
        r = _reminder(reminder_time=_WED, frequency="daily")
        self.assertTrue(svc.is_due(r, _THU))
        self.assertFalse(svc.is_due(r, _THU.replace(hour=7)))

    def test_daily_not_due_if_completed_today(self):
        r = _reminder(reminder_time=_WED, frequency="daily", last_completed_at=_THU)
        self.assertFalse(svc.is_due(r, _THU))

    def test_daily_due_again_next_day_even_if_completed_yesterday(self):
        r = _reminder(reminder_time=_WED, frequency="daily", last_completed_at=_WED)
        self.assertTrue(svc.is_due(r, _THU))

    def test_mwf_due_on_matching_weekday(self):
        r = _reminder(reminder_time=_WED, frequency="mwf")  # Wed is a match day
        self.assertTrue(svc.is_due(r, _WED))

    def test_mwf_not_due_on_non_matching_weekday(self):
        r = _reminder(reminder_time=_WED, frequency="mwf")
        self.assertFalse(svc.is_due(r, _THU))  # Thursday is not Mon/Wed/Fri

    def test_weekly_due_on_same_weekday_as_scheduled(self):
        r = _reminder(reminder_time=_WED, frequency="weekly")
        next_wed = datetime(2026, 7, 29, 9, 0, tzinfo=UTC)
        self.assertTrue(svc.is_due(r, next_wed))

    def test_weekly_not_due_on_other_weekday(self):
        r = _reminder(reminder_time=_WED, frequency="weekly")
        self.assertFalse(svc.is_due(r, _THU))

    def test_unknown_frequency_is_never_due(self):
        r = _reminder(reminder_time=_WED, frequency="fortnightly")
        self.assertFalse(svc.is_due(r, _WED))


class BuildIcsTests(unittest.TestCase):
    def test_contains_vevent_and_summary(self):
        r = _reminder(reminder_time=_WED, frequency="daily")
        ics = svc.build_ics(r, now=_WED)
        self.assertIn("BEGIN:VEVENT", ics)
        self.assertIn("END:VEVENT", ics)
        self.assertIn("SUMMARY:Do your Sit-to-Stand check", ics)
        self.assertIn("DTSTART:20260722T080000Z", ics)

    def test_daily_frequency_produces_daily_rrule(self):
        r = _reminder(reminder_time=_WED, frequency="daily")
        ics = svc.build_ics(r, now=_WED)
        self.assertIn("RRULE:FREQ=DAILY", ics)

    def test_mwf_frequency_produces_byday_rrule(self):
        r = _reminder(reminder_time=_WED, frequency="mwf")
        ics = svc.build_ics(r, now=_WED)
        self.assertIn("RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR", ics)

    def test_once_has_no_rrule(self):
        r = _reminder(reminder_time=_WED, frequency="once")
        ics = svc.build_ics(r, now=_WED)
        self.assertNotIn("RRULE", ics)

    def test_has_a_popup_valarm(self):
        r = _reminder(reminder_time=_WED, frequency="once")
        ics = svc.build_ics(r, now=_WED)
        self.assertIn("BEGIN:VALARM", ics)
        self.assertIn("ACTION:DISPLAY", ics)

    def test_title_is_escaped(self):
        r = _reminder(reminder_time=_WED, frequency="once", title="Knee, ankle; rehab")
        ics = svc.build_ics(r, now=_WED)
        self.assertIn("SUMMARY:Knee\\, ankle\\; rehab", ics)

    # Stage R13 (UAT): the calendar event title used to be the reminder's own
    # title only, which gave no hint which exercise it was for once it landed in
    # the user's own calendar app, away from PhysioFit's UI.
    def test_exercise_name_appended_to_summary_when_provided(self):
        r = _reminder(reminder_time=_WED, frequency="once", title="Evening set")
        ics = svc.build_ics(r, now=_WED, exercise_name="Sit-to-Stand")
        self.assertIn("SUMMARY:Evening set — Sit-to-Stand", ics)

    def test_summary_unchanged_when_no_exercise_name(self):
        r = _reminder(reminder_time=_WED, frequency="once", title="Evening set")
        ics = svc.build_ics(r, now=_WED, exercise_name=None)
        self.assertIn("SUMMARY:Evening set", ics)
        self.assertNotIn("—", ics)


class BuildGoogleCalendarUrlTests(unittest.TestCase):
    def test_base_url_and_action(self):
        r = _reminder(reminder_time=_WED, frequency="once")
        url = svc.build_google_calendar_url(r)
        self.assertTrue(url.startswith("https://calendar.google.com/calendar/render?"))
        self.assertIn("action=TEMPLATE", url)

    def test_includes_title_and_dates(self):
        r = _reminder(reminder_time=_WED, frequency="once", title="Sit-to-Stand")
        url = svc.build_google_calendar_url(r)
        self.assertIn("text=Sit-to-Stand", url)
        self.assertIn("dates=20260722T080000Z%2F20260722T083000Z", url)

    def test_recurring_includes_recur_param(self):
        r = _reminder(reminder_time=_WED, frequency="weekly")
        url = svc.build_google_calendar_url(r)
        self.assertIn("recur=RRULE%3AFREQ%3DWEEKLY", url)

    def test_once_has_no_recur_param(self):
        r = _reminder(reminder_time=_WED, frequency="once")
        url = svc.build_google_calendar_url(r)
        self.assertNotIn("recur=", url)

    def test_exercise_name_appended_to_event_title_when_provided(self):
        r = _reminder(reminder_time=_WED, frequency="once", title="Evening set")
        url = svc.build_google_calendar_url(r, exercise_name="Sit-to-Stand")
        self.assertIn("text=Evening+set+%E2%80%94+Sit-to-Stand", url)


if __name__ == "__main__":
    unittest.main()
