"""Widget registry for ``clibo dashboard``.

Each widget is a small, side-effect-free function that pulls data for one
"thing today" and returns ``{title, lines, data}``. The dashboard renders
the lines block in human mode and the data block in ``--json`` mode.

Adding a widget is one entry in :data:`WIDGETS` — see existing ones for
the pattern.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, timedelta

from sqlmodel import select

from clibo.clis.bills import Bill
from clibo.clis.birthdays import Occasion
from clibo.clis.calorie import CalorieEntry
from clibo.clis.chores import Chore
from clibo.clis.events import Event
from clibo.clis.expense import Expense
from clibo.clis.focus import FocusSession
from clibo.clis.followup import FollowUp
from clibo.clis.gratitude import GratitudeEntry
from clibo.clis.habit import Habit, HabitCheck
from clibo.clis.income import IncomeEntry
from clibo.clis.mileage import MileageEntry
from clibo.clis.mood import MoodLog
from clibo.clis.plants import Plant
from clibo.clis.sleep import SleepLog
from clibo.clis.todo import Task
from clibo.clis.water import WaterLog
from clibo.clis.weight import WeightLog
from clibo.core.output import bar
from clibo.core.settings import get_setting


def _today() -> date:
    return date.today()


# ── individual widgets ─────────────────────────────────────────────────────

def _w_tasks(db) -> dict:
    today = _today()
    rows = list(db.exec(select(Task).where(Task.done == False)).all())  # noqa: E712
    overdue = [t for t in rows if t.due and t.due < today]
    due_today = [t for t in rows if t.due == today]
    lines = (
        [f"[red]⚠ overdue[/red]  {t.title}  [dim]({t.priority})[/dim]" for t in overdue]
        + [f"[yellow]● today[/yellow]   {t.title}  [dim]({t.priority})[/dim]" for t in due_today]
    )
    return {
        "title": "✅ Tasks",
        "lines": lines,
        "data": {
            "pending": len(rows),
            "overdue": [{"title": t.title, "priority": t.priority} for t in overdue],
            "due_today": [{"title": t.title, "priority": t.priority} for t in due_today],
        },
    }


def _w_habits(db) -> dict:
    today = _today()
    habits = list(
        db.exec(select(Habit).where(Habit.active == True)).all()  # noqa: E712
    )
    checked = {
        c.habit_id
        for c in db.exec(select(HabitCheck).where(HabitCheck.check_date == today)).all()
    }
    done = sum(1 for h in habits if h.id in checked)
    lines = (
        [f"[cyan]{done}[/cyan]/{len(habits)} done"]
        + [
            f"  {'[green]✓[/green]' if h.id in checked else '[dim]○[/dim]'} {h.name}"
            for h in habits
        ]
        if habits else []
    )
    return {
        "title": "🔥 Habits",
        "lines": lines,
        "data": {
            "total": len(habits),
            "done_today": done,
            "items": [{"name": h.name, "done": h.id in checked} for h in habits],
        },
    }


def _w_water(db) -> dict:
    today = _today()
    total = sum(
        w.amount_ml
        for w in db.exec(select(WaterLog).where(WaterLog.entry_date == today)).all()
    )
    goal = int(get_setting("water", "daily_ml", "2000") or 2000)
    return {
        "title": "💧 Water",
        "lines": [
            f"{bar(total, goal, width=18)}  [bold]{total}[/bold]/{goal} ml",
        ],
        "data": {"total_ml": total, "goal_ml": goal, "reached": total >= goal},
    }


def _w_calories(db) -> dict:
    today = _today()
    total = sum(
        c.kcal
        for c in db.exec(select(CalorieEntry).where(CalorieEntry.entry_date == today)).all()
    )
    goal = int(get_setting("calorie", "daily_kcal", "0") or 0)
    if not goal and not total:
        return {"title": "🍎 Calories", "lines": [], "data": {"total_kcal": 0, "goal_kcal": 0}}
    lines = (
        [f"{bar(total, goal, width=18)}  [bold]{total}[/bold]/{goal} kcal"]
        if goal else [f"[bold]{total}[/bold] kcal today  [dim](no goal set)[/dim]"]
    )
    return {
        "title": "🍎 Calories",
        "lines": lines,
        "data": {"total_kcal": total, "goal_kcal": goal},
    }


def _w_focus(db) -> dict:
    today = _today()
    total = sum(
        f.minutes
        for f in db.exec(select(FocusSession).where(FocusSession.entry_date == today)).all()
    )
    goal = int(get_setting("focus", "daily_min", "100") or 100)
    return {
        "title": "🍅 Focus",
        "lines": [f"{bar(total, goal, width=18)}  [bold]{total}[/bold]/{goal} min"]
                  if total or goal else [],
        "data": {"total_minutes": total, "goal_minutes": goal},
    }


def _w_sleep(db) -> dict:
    last = db.exec(
        select(SleepLog).order_by(SleepLog.entry_date.desc(), SleepLog.id.desc())
    ).first()
    if not last:
        return {"title": "😴 Sleep", "lines": [], "data": None}
    return {
        "title": "😴 Sleep",
        "lines": [f"Last night: [bold]{last.hours:g}h[/bold]  · quality {last.quality}/5"],
        "data": {"hours": last.hours, "quality": last.quality, "date": last.entry_date},
    }


def _w_events(db) -> dict:
    today = _today()
    events = list(
        db.exec(select(Event).where(Event.event_date == today).order_by(Event.event_time)).all()
    )
    lines = [
        f"[cyan]{e.event_time or 'all day'}[/cyan]  {e.title}"
        + (f"  [dim]@ {e.location}[/dim]" if e.location else "")
        for e in events
    ]
    return {
        "title": "📅 Events",
        "lines": lines,
        "data": [{"time": e.event_time, "title": e.title, "location": e.location} for e in events],
    }


def _w_bills(db) -> dict:
    today = _today()
    horizon = today + timedelta(days=7)
    bills = list(
        db.exec(
            select(Bill).where(Bill.paid == False, Bill.due_date <= horizon)  # noqa: E712
        ).order_by(Bill.due_date).all()
    )
    lines = [
        (f"[red]⚠ overdue[/red]  {b.name}  [dim]({b.due_date})[/dim]"
         if b.due_date < today
         else f"[yellow]⏰[/yellow] {b.name}  [dim]({b.due_date})[/dim]")
        for b in bills
    ]
    return {
        "title": "🧾 Bills due",
        "lines": lines,
        "data": [
            {"name": b.name, "due": b.due_date.isoformat(), "overdue": b.due_date < today}
            for b in bills
        ],
    }


def _w_followups(db) -> dict:
    today = _today()
    soon = today + timedelta(days=2)
    rows = list(
        db.exec(
            select(FollowUp).where(
                FollowUp.done == False, FollowUp.due_date <= soon  # noqa: E712
            )
        ).order_by(FollowUp.due_date).all()
    )
    lines = [
        (f"[red]⚠[/red] {f.person}  [dim]({f.due_date})[/dim]" if f.due_date < today
         else f"[yellow]⏰[/yellow] {f.person}  [dim]({f.due_date})[/dim]")
        for f in rows
    ]
    return {
        "title": "🔔 Follow-ups",
        "lines": lines,
        "data": [
            {"person": f.person, "due": f.due_date.isoformat(), "overdue": f.due_date < today}
            for f in rows
        ],
    }


def _w_plants(db) -> dict:
    today = _today()
    plants = list(db.exec(select(Plant)).all())
    thirsty = [
        p for p in plants
        if (p.last_watered + timedelta(days=p.water_every_days) if p.last_watered else today)
        <= today
    ]
    lines = [
        f"{p.name}" + (f"  [dim]({p.location})[/dim]" if p.location else "")
        for p in thirsty
    ]
    return {
        "title": "🪴 Plants needing water",
        "lines": lines,
        "data": [{"name": p.name, "location": p.location} for p in thirsty],
    }


def _w_chores(db) -> dict:
    today = _today()
    chores = list(db.exec(select(Chore)).all())
    due = [
        c for c in chores
        if (c.last_done + timedelta(days=c.frequency_days) if c.last_done else today)
        <= today
    ]
    lines = [
        f"{c.name}" + (f"  [dim]({c.assignee})[/dim]" if c.assignee else "")
        for c in due
    ]
    return {
        "title": "🧹 Chores due",
        "lines": lines,
        "data": [{"name": c.name, "assignee": c.assignee} for c in due],
    }


def _w_birthdays(db) -> dict:
    today = _today()
    occasions = list(db.exec(select(Occasion)).all())
    matches = [o for o in occasions if o.month == today.month and o.day == today.day]
    lines = [f"🎉 {o.kind.title()}: [bold]{o.person}[/bold]" for o in matches]
    return {
        "title": "🎂 Today",
        "lines": lines,
        "data": [{"person": o.person, "kind": o.kind} for o in matches],
    }


def _w_mileage(db) -> dict:
    today = _today()
    rows = list(db.exec(select(MileageEntry).where(MileageEntry.entry_date == today)).all())
    if not rows:
        return {"title": "🏃 Mileage today", "lines": [], "data": None}
    total = round(sum(r.distance_km for r in rows), 2)
    return {
        "title": "🏃 Mileage today",
        "lines": [f"[bold]{total:g}[/bold] km  ·  {len(rows)} sessions"],
        "data": {"total_km": total, "sessions": len(rows)},
    }


def _w_gratitude(db) -> dict:
    today = _today()
    rows = list(db.exec(select(GratitudeEntry).where(GratitudeEntry.entry_date == today)).all())
    return {
        "title": "🙏 Grateful for today",
        "lines": [f"· {r.text}" for r in rows],
        "data": [r.text for r in rows],
    }


def _w_mood(db) -> dict:
    today = _today()
    rows = list(db.exec(select(MoodLog).where(MoodLog.entry_date == today)).all())
    if not rows:
        return {"title": "🙂 Mood", "lines": [], "data": None}
    avg = round(sum(r.score for r in rows) / len(rows), 1)
    return {
        "title": "🙂 Mood",
        "lines": [f"avg [bold]{avg}/5[/bold] over {len(rows)} check-ins"],
        "data": {"avg_score": avg, "checkins": len(rows)},
    }


def _w_weight(db) -> dict:
    last = db.exec(
        select(WeightLog).order_by(WeightLog.entry_date.desc(), WeightLog.id.desc())
    ).first()
    if not last:
        return {"title": "⚖️ Weight", "lines": [], "data": None}
    return {
        "title": "⚖️ Weight",
        "lines": [f"latest: [bold]{last.weight_kg:g} kg[/bold]  [dim]({last.entry_date})[/dim]"],
        "data": {"weight_kg": last.weight_kg, "date": last.entry_date},
    }


def _w_expense(db) -> dict:
    today = _today()
    rows = list(db.exec(select(Expense).where(Expense.entry_date == today)).all())
    if not rows:
        return {"title": "💸 Spent today", "lines": [], "data": None}
    total = round(sum(e.amount for e in rows), 2)
    currency = get_setting("money", "currency", "USD")
    return {
        "title": "💸 Spent today",
        "lines": [f"[bold]{total:g} {currency}[/bold]  ·  {len(rows)} entries"],
        "data": {"total": total, "entries": len(rows), "currency": currency},
    }


def _w_income(db) -> dict:
    today = _today()
    rows = list(db.exec(select(IncomeEntry).where(IncomeEntry.entry_date == today)).all())
    if not rows:
        return {"title": "💵 Income today", "lines": [], "data": None}
    total = round(sum(e.amount for e in rows), 2)
    currency = get_setting("money", "currency", "USD")
    return {
        "title": "💵 Income today",
        "lines": [f"[bold green]+{total:g} {currency}[/bold green]  ·  {len(rows)} entries"],
        "data": {"total": total, "entries": len(rows), "currency": currency},
    }


#: Public registry. Each entry: ``name → (one-line description, render fn)``.
WIDGETS: dict[str, tuple[str, Callable]] = {
    "tasks":     ("Overdue + today's tasks",       _w_tasks),
    "habits":    ("Habit check-offs for today",    _w_habits),
    "water":     ("Water intake progress bar",     _w_water),
    "calories":  ("Calorie intake progress bar",   _w_calories),
    "focus":     ("Focus minutes vs goal",         _w_focus),
    "sleep":     ("Last night's sleep summary",    _w_sleep),
    "mood":      ("Today's mood average",          _w_mood),
    "events":    ("Today's calendar events",       _w_events),
    "bills":     ("Bills due in the next 7 days",  _w_bills),
    "followups": ("Follow-ups due soon",           _w_followups),
    "plants":    ("Plants needing water",          _w_plants),
    "chores":    ("Chores due today",              _w_chores),
    "birthdays": ("Birthdays / anniversaries today", _w_birthdays),
    "mileage":   ("Today's distance",              _w_mileage),
    "gratitude": ("Today's gratitudes",            _w_gratitude),
    "weight":    ("Latest weight measurement",     _w_weight),
    "expense":   ("Today's total spending",        _w_expense),
    "income":    ("Today's total income",          _w_income),
}

#: Default widget set if the user has never configured one.
DEFAULT_WIDGETS = ["tasks", "habits", "water", "calories", "focus", "events"]
