"""Detect which trackers the user actively uses, and surface today's status.

The user-facing primitives this powers:

* ``clibo today`` — gains a **Daily check-ins** section that lists every
  tracker with recent activity, showing today's value (✓) or a gentle
  "○ not logged" hint with the last known value.
* ``clibo checkin`` — surfaces only the *pending* check-ins as questions,
  one per active tracker, with a copy-pasteable command. The ``--json``
  form is structured for an AI agent to ask the user one question per
  pending tracker and then run the suggested log command.

A tracker is "active" if it has **two or more entries in the last 14 days**.
That's the minimal evidence the user is actually using it — single
exploratory entries don't pollute the check-in list.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from sqlmodel import select

from clibo.clis.caffeine import CaffeineEntry
from clibo.clis.fasting import FastSession
from clibo.clis.gratitude import GratitudeEntry
from clibo.clis.journal import JournalEntry
from clibo.clis.meditate import MeditationSession
from clibo.clis.mileage import MileageEntry
from clibo.clis.mood import MoodLog
from clibo.clis.sleep import SleepLog
from clibo.clis.steps import StepEntry
from clibo.clis.stretches import StretchSession
from clibo.clis.weight import WeightLog
from clibo.clis.workout import Workout

ACTIVE_WINDOW_DAYS = 14
MIN_ENTRIES_TO_BE_ACTIVE = 2


@dataclass(frozen=True)
class _Tracker:
    """Static config for one tracker the daily check-in flow understands."""

    name: str
    emoji: str
    model: type
    date_field: str
    format_value: Callable[[Any], str]
    question: str
    command: str


TRACKERS: list[_Tracker] = [
    _Tracker(
        name="Weight", emoji="⚖️",
        model=WeightLog, date_field="entry_date",
        format_value=lambda e: f"{e.weight_kg:g} kg",
        question="What's your weight today?",
        command="clibo weight log <kg>",
    ),
    _Tracker(
        name="Sleep", emoji="😴",
        model=SleepLog, date_field="entry_date",
        format_value=lambda e: (
            f"{e.hours:g}h"
            + (f" (quality {e.quality}/5)" if e.quality else "")
        ),
        question="How many hours did you sleep last night?",
        command="clibo sleep log <hours> -q <1-5>",
    ),
    _Tracker(
        name="Mood", emoji="🙂",
        model=MoodLog, date_field="entry_date",
        format_value=lambda e: (
            f"{e.score}/5" + (f" — {e.emotion}" if e.emotion else "")
        ),
        question="How are you feeling, 1-5?",
        command="clibo mood log <1-5> -e <emotion>",
    ),
    _Tracker(
        name="Steps", emoji="👟",
        model=StepEntry, date_field="entry_date",
        format_value=lambda e: f"{e.count:,}",
        question="Steps today?",
        command="clibo steps log <count>",
    ),
    _Tracker(
        name="Workout", emoji="🏋️",
        model=Workout, date_field="entry_date",
        format_value=lambda e: e.exercise,
        question="Did you work out today?",
        command="clibo workout log <exercise> -t <min> -c <kcal>",
    ),
    _Tracker(
        name="Caffeine", emoji="☕",
        model=CaffeineEntry, date_field="entry_date",
        format_value=lambda e: f"{e.drink} ({e.mg} mg)",
        question="Any caffeine today?",
        command="clibo caffeine log <drink>",
    ),
    _Tracker(
        name="Meditate", emoji="🧘",
        model=MeditationSession, date_field="entry_date",
        format_value=lambda e: f"{e.minutes} min",
        question="Meditated today?",
        command="clibo meditate log <minutes>",
    ),
    _Tracker(
        name="Stretches", emoji="🧎",
        model=StretchSession, date_field="entry_date",
        format_value=lambda e: f"{e.duration_min} min {e.area}",
        question="Did you stretch today?",
        command="clibo stretches log <area> -m <min>",
    ),
    _Tracker(
        name="Mileage", emoji="🏃",
        model=MileageEntry, date_field="entry_date",
        format_value=lambda e: f"{e.distance_km:g} km {e.activity}",
        question="Run / walk / cycle today?",
        command="clibo mileage log <km> -a <run|walk|cycle>",
    ),
    _Tracker(
        name="Journal", emoji="📔",
        model=JournalEntry, date_field="entry_date",
        format_value=lambda e: (
            (e.body[:50] + "…") if len(e.body) > 50 else e.body
        ),
        question="Anything you want to journal about today?",
        command="clibo journal write \"...\"",
    ),
    _Tracker(
        name="Gratitude", emoji="🙏",
        model=GratitudeEntry, date_field="entry_date",
        format_value=lambda e: (
            (e.text[:50] + "…") if len(e.text) > 50 else e.text
        ),
        question="What are you grateful for today?",
        command="clibo gratitude add \"...\"",
    ),
    _Tracker(
        name="Caffeine cutoff", emoji="🕒",  # placeholder, replaced below
        model=FastSession, date_field="start_time",
        format_value=lambda e: (
            "in progress" if e.end_time is None
            else f"{e.target_hours:g}h target"
        ),
        question="Start or stop a fast?",
        command="clibo fasting start --target <hours>  /  clibo fasting stop",
    ),
]
# Patch the fasting tracker with the right label (the placeholder above
# was just to keep the dataclass definitions uniform).
TRACKERS[-1] = _Tracker(
    name="Fasting", emoji="🕒",
    model=FastSession, date_field="start_time",
    format_value=lambda e: (
        "in progress" if e.end_time is None
        else f"{e.target_hours:g}h target"
    ),
    question="Start or stop a fast?",
    command="clibo fasting start --target <hours>  /  clibo fasting stop",
)


def _entry_date_of(tracker: _Tracker, entry: Any) -> date:
    """Return the date for an entry, whether its time-column is a date or datetime."""
    value = getattr(entry, tracker.date_field)
    if hasattr(value, "date") and callable(value.date):
        return value.date()
    return value


def collect_checkins(
    db, today: date | None = None, days: int = ACTIVE_WINDOW_DAYS
) -> list[dict]:
    """Return one dict per actively-used tracker with today's status.

    ``db`` is an open SQLModel session. ``days`` controls the activity window.
    Each result has:

    * ``name``, ``emoji`` — display labels
    * ``logged_today`` — bool
    * ``today_value`` — formatted string, or ``None`` if not logged today
    * ``last_value`` — most-recent prior entry, formatted
    * ``last_days_ago`` — int, or ``None`` if no prior entry exists
    * ``question`` — the prompt for ``clibo checkin``
    * ``command`` — suggested CLI to log the new value
    """
    today = today or date.today()
    since = today - timedelta(days=days - 1)
    results: list[dict] = []
    for tc in TRACKERS:
        date_col = getattr(tc.model, tc.date_field)
        entries = list(
            db.exec(
                select(tc.model)
                .where(date_col >= since)
                .order_by(date_col.desc())
            ).all()
        )
        if len(entries) < MIN_ENTRIES_TO_BE_ACTIVE:
            continue
        today_entry = next(
            (e for e in entries if _entry_date_of(tc, e) == today), None
        )
        last_entry = next(
            (e for e in entries if _entry_date_of(tc, e) != today), None
        )
        last_days_ago = (
            (today - _entry_date_of(tc, last_entry)).days
            if last_entry else None
        )
        results.append({
            "name": tc.name,
            "emoji": tc.emoji,
            "logged_today": today_entry is not None,
            "today_value": tc.format_value(today_entry) if today_entry else None,
            "last_value": tc.format_value(last_entry) if last_entry else None,
            "last_days_ago": last_days_ago,
            "question": tc.question,
            "command": tc.command,
        })
    return results
