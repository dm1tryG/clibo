"""``clibo week`` — a 7-day rollup across trackers.

Sister command to ``clibo today``. Where today is about *what's actionable
now*, week is about *how the last seven days actually went* — averages,
totals, streaks. Renders one screen for humans and a single dict for agents.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlmodel import select

from clibo.clis.calorie import CalorieEntry
from clibo.clis.expense import Expense, get_currency, money
from clibo.clis.focus import FocusSession
from clibo.clis.habit import Habit, HabitCheck
from clibo.clis.journal import JournalEntry
from clibo.clis.mood import MoodLog
from clibo.clis.sleep import SleepLog
from clibo.clis.todo import Task
from clibo.clis.water import WaterLog
from clibo.clis.worklog import WorkLogEntry
from clibo.core.db import session
from clibo.core.output import _emit_json, bar, console
from clibo.core.settings import get_setting

WINDOW_DAYS = 7


def _round(value: float, ndigits: int = 1) -> float:
    return round(value, ndigits)


def collect_week() -> dict:
    """Aggregate the past 7 days across the trackers that have time-series data."""
    today = date.today()
    start = today - timedelta(days=WINDOW_DAYS - 1)
    water_goal = int(get_setting("water", "daily_ml", "2000") or 2000)
    calorie_goal = int(get_setting("calorie", "daily_kcal", "0") or 0)
    focus_goal = int(get_setting("focus", "daily_min", "100") or 100)

    with session() as db:
        sleeps = list(
            db.exec(select(SleepLog).where(SleepLog.entry_date >= start)).all()
        )
        calories = list(
            db.exec(select(CalorieEntry).where(CalorieEntry.entry_date >= start)).all()
        )
        waters = list(
            db.exec(select(WaterLog).where(WaterLog.entry_date >= start)).all()
        )
        focus = list(
            db.exec(select(FocusSession).where(FocusSession.entry_date >= start)).all()
        )
        moods = list(
            db.exec(select(MoodLog).where(MoodLog.entry_date >= start)).all()
        )
        expenses = list(
            db.exec(select(Expense).where(Expense.entry_date >= start)).all()
        )
        journal = list(
            db.exec(select(JournalEntry).where(JournalEntry.entry_date >= start)).all()
        )
        worklog = list(
            db.exec(select(WorkLogEntry).where(WorkLogEntry.entry_date >= start)).all()
        )
        tasks_done = list(
            db.exec(
                select(Task).where(
                    Task.done == True, Task.done_at != None,  # noqa: E711, E712
                    Task.done_at >= start,
                )
            ).all()
        )
        habits = list(
            db.exec(select(Habit).where(Habit.active == True)).all()  # noqa: E712
        )
        habit_checks = list(
            db.exec(select(HabitCheck).where(HabitCheck.check_date >= start)).all()
        )

    # Sleep
    sleep_summary = {
        "nights_logged": len({s.entry_date for s in sleeps}),
        "avg_hours": _round(sum(s.hours for s in sleeps) / len(sleeps)) if sleeps else None,
        "avg_quality": _round(sum(s.quality for s in sleeps) / len(sleeps)) if sleeps else None,
    }
    # Calories
    cal_days = {c.entry_date for c in calories}
    calorie_summary = {
        "days_logged": len(cal_days),
        "total_kcal": sum(c.kcal for c in calories),
        "avg_kcal_per_logged_day": (
            _round(sum(c.kcal for c in calories) / len(cal_days), 0) if cal_days else None
        ),
        "goal_kcal": calorie_goal or None,
    }
    # Water
    water_by_day: dict[date, int] = {}
    for w in waters:
        water_by_day[w.entry_date] = water_by_day.get(w.entry_date, 0) + w.amount_ml
    water_summary = {
        "days_logged": len(water_by_day),
        "total_ml": sum(water_by_day.values()),
        "goal_ml": water_goal,
        "days_goal_reached": sum(1 for ml in water_by_day.values() if ml >= water_goal),
    }
    # Focus
    focus_summary = {
        "sessions": len(focus),
        "total_minutes": sum(f.minutes for f in focus),
        "days_focused": len({f.entry_date for f in focus}),
        "goal_minutes_per_day": focus_goal,
    }
    # Mood
    mood_summary = {
        "checkins": len(moods),
        "avg_score": _round(sum(m.score for m in moods) / len(moods)) if moods else None,
    }
    # Expenses
    expense_total = round(sum(e.amount for e in expenses), 2)
    by_category: dict[str, float] = {}
    for entry in expenses:
        by_category[entry.category] = round(
            by_category.get(entry.category, 0) + entry.amount, 2
        )
    top_category = max(by_category.items(), key=lambda kv: kv[1], default=None)
    expense_summary = {
        "entries": len(expenses),
        "total": expense_total,
        "avg_per_day": _round(expense_total / WINDOW_DAYS, 2),
        "top_category": (
            {"category": top_category[0], "amount": top_category[1]}
            if top_category else None
        ),
        "currency": get_currency(),
    }
    # Productivity
    journal_summary = {
        "entries": len(journal),
        "days_journaled": len({j.entry_date for j in journal}),
    }
    worklog_summary = {
        "entries": len(worklog),
        "by_kind": {
            kind: sum(1 for w in worklog if w.kind == kind)
            for kind in ("done", "doing", "blocked", "note")
        },
    }
    tasks_summary = {"completed": len(tasks_done)}
    # Habits — checks per habit this week, vs target
    habit_rows = []
    for habit in habits:
        done = sum(1 for c in habit_checks if c.habit_id == habit.id)
        habit_rows.append({
            "name": habit.name,
            "done": done,
            "target_per_week": habit.target_per_week,
            "hit_target": done >= habit.target_per_week,
        })
    habits_summary = {
        "tracked": len(habits),
        "items": habit_rows,
        "hit_target": sum(1 for h in habit_rows if h["hit_target"]),
    }

    return {
        "start": start,
        "end": today,
        "days": WINDOW_DAYS,
        "sleep": sleep_summary,
        "calories": calorie_summary,
        "water": water_summary,
        "focus": focus_summary,
        "mood": mood_summary,
        "expenses": expense_summary,
        "habits": habits_summary,
        "journal": journal_summary,
        "worklog": worklog_summary,
        "tasks": tasks_summary,
    }


def render_week(json_out: bool) -> None:
    """Render the weekly rollup to stdout."""
    data = collect_week()
    if json_out:
        _emit_json(data)
        return
    start, end = data["start"], data["end"]
    console.print(
        f"\n🗓️  [bold]Last 7 days[/bold]   [dim]{start:%a %d %b}[/dim] → "
        f"[dim]{end:%a %d %b}[/dim]\n"
    )

    # 😴 Sleep, 🍎 Calories, 💧 Water, 🍅 Focus — health metrics block
    metric_lines: list[str] = []
    s = data["sleep"]
    if s["nights_logged"]:
        metric_lines.append(
            f"😴 Sleep      [bold]{s['avg_hours']}h[/bold] avg over "
            f"[cyan]{s['nights_logged']}[/cyan] nights"
            + (f"   ·   quality {s['avg_quality']}/5" if s["avg_quality"] else "")
        )
    c = data["calories"]
    if c["days_logged"]:
        metric_lines.append(
            f"🍎 Calories   [bold]{c['avg_kcal_per_logged_day']:g}[/bold] kcal/day "
            f"over [cyan]{c['days_logged']}[/cyan] days"
        )
    w = data["water"]
    if w["days_logged"]:
        metric_lines.append(
            f"💧 Water      hit goal [bold]{w['days_goal_reached']}/7[/bold] days   "
            f"·   {w['total_ml']} ml total"
        )
    f = data["focus"]
    if f["sessions"]:
        metric_lines.append(
            f"🍅 Focus      [bold]{f['total_minutes']}[/bold] min across "
            f"{f['sessions']} sessions, [cyan]{f['days_focused']}[/cyan] days"
        )
    m = data["mood"]
    if m["checkins"]:
        metric_lines.append(
            f"🙂 Mood       [bold]{m['avg_score']}/5[/bold] avg over "
            f"{m['checkins']} check-ins"
        )
    if metric_lines:
        for line in metric_lines:
            console.print(f"  {line}")
        console.print()

    # 🔥 Habits
    h = data["habits"]
    if h["tracked"]:
        console.print(
            f"[bold]🔥 Habits[/bold]   "
            f"[cyan]{h['hit_target']}[/cyan]/{h['tracked']} hit target"
        )
        for item in h["items"]:
            ratio = bar(item["done"], item["target_per_week"], width=14)
            mark = "[green]✓[/green]" if item["hit_target"] else "[dim]·[/dim]"
            console.print(
                f"  {mark} {item['name']:<22} {ratio}  "
                f"[dim]{item['done']}/{item['target_per_week']}[/dim]"
            )
        console.print()

    # 💸 Expenses
    e = data["expenses"]
    if e["entries"]:
        line = f"[bold]💸 Expenses[/bold]   {money(e['total'])} total   ·   {e['entries']} entries"
        if e["top_category"]:
            line += (
                f"   ·   top: [bold]{e['top_category']['category']}[/bold] "
                f"({money(e['top_category']['amount'])})"
            )
        console.print(line)
        console.print()

    # ✅ Tasks, 📔 Journal, 🗒️ Worklog
    if data["tasks"]["completed"] or data["journal"]["entries"] or data["worklog"]["entries"]:
        console.print("[bold]✅ Productivity[/bold]")
        if data["tasks"]["completed"]:
            console.print(f"  Tasks completed:  {data['tasks']['completed']}")
        if data["journal"]["entries"]:
            j = data["journal"]
            console.print(
                f"  Journal entries:  {j['entries']}  "
                f"[dim]({j['days_journaled']} days journaled)[/dim]"
            )
        if data["worklog"]["entries"]:
            wl = data["worklog"]["by_kind"]
            parts = [f"{kind}: {wl[kind]}" for kind in ("done", "doing", "blocked") if wl[kind]]
            if parts:
                console.print(f"  Worklog:          {', '.join(parts)}")
        console.print()

    if not metric_lines and not h["tracked"] and not e["entries"]:
        console.print("  [dim]Nothing logged in the last 7 days yet.[/dim]\n")
