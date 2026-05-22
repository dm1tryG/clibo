"""``clibo today`` — a one-screen dashboard pulling from every tool.

This is the integrating view that makes 50 separate trackers feel like one
app: tasks due, habits to keep, today's meals and events, bills coming up,
people to follow up with, plants needing water, calories logged, and so on.

It only imports models from other CLI modules (never their Typer apps), so
it stays a pure read-only consumer of each tool's data.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlmodel import select

from clibo.clis.bills import Bill
from clibo.clis.birthdays import Occasion
from clibo.clis.calorie import CalorieEntry
from clibo.clis.chores import Chore
from clibo.clis.events import Event
from clibo.clis.focus import FocusSession
from clibo.clis.followup import FollowUp
from clibo.clis.habit import Habit, HabitCheck
from clibo.clis.meals import MealPlan
from clibo.clis.plants import Plant
from clibo.clis.todo import Task
from clibo.clis.water import WaterLog
from clibo.core.db import session
from clibo.core.output import _emit_json, bar, console
from clibo.core.settings import get_setting


def collect_today() -> dict:
    """Gather a snapshot of everything actionable today."""
    today = date.today()
    soon = today + timedelta(days=2)
    week = today + timedelta(days=7)
    with session() as db:
        # 📋 Tasks
        tasks = list(db.exec(select(Task).where(Task.done == False)).all())  # noqa: E712
        overdue = [t for t in tasks if t.due and t.due < today]
        due_today = [t for t in tasks if t.due == today]
        # 🔥 Habits
        habits = list(
            db.exec(select(Habit).where(Habit.active == True)).all()  # noqa: E712
        )
        checked = {
            c.habit_id
            for c in db.exec(select(HabitCheck).where(HabitCheck.check_date == today)).all()
        }
        # 💧 Water
        water_total = sum(
            w.amount_ml
            for w in db.exec(select(WaterLog).where(WaterLog.entry_date == today)).all()
        )
        water_goal = int(get_setting("water", "daily_ml", "2000") or 2000)
        # 🍎 Calories
        kcal_total = sum(
            c.kcal
            for c in db.exec(select(CalorieEntry).where(CalorieEntry.entry_date == today)).all()
        )
        kcal_goal = int(get_setting("calorie", "daily_kcal", "0") or 0)
        # 🍅 Focus
        focus_total = sum(
            f.minutes
            for f in db.exec(
                select(FocusSession).where(FocusSession.entry_date == today)
            ).all()
        )
        focus_goal = int(get_setting("focus", "daily_min", "100") or 100)
        # 📅 Events today
        events = list(db.exec(select(Event).where(Event.event_date == today)).all())
        # 🍽️ Meals today
        meals = list(db.exec(select(MealPlan).where(MealPlan.plan_date == today)).all())
        # 🧾 Bills due
        bills = list(
            db.exec(
                select(Bill).where(Bill.paid == False, Bill.due_date <= week)  # noqa: E712
            ).all()
        )
        # 🔔 Follow-ups
        followups = list(
            db.exec(
                select(FollowUp).where(
                    FollowUp.done == False, FollowUp.due_date <= soon  # noqa: E712
                )
            ).all()
        )
        # 🪴 Plants
        plants = list(db.exec(select(Plant)).all())
        thirsty = [
            p for p in plants
            if (p.last_watered + timedelta(days=p.water_every_days) if p.last_watered else today)
            <= today
        ]
        # 🧹 Chores
        chores = list(db.exec(select(Chore)).all())
        chores_due = [
            c for c in chores
            if (c.last_done + timedelta(days=c.frequency_days) if c.last_done else today)
            <= today
        ]
        # 🎂 Birthdays today
        occasions = list(db.exec(select(Occasion)).all())
        bdays = [o for o in occasions if o.month == today.month and o.day == today.day]

    return {
        "date": today,
        "tasks": {
            "pending": len(tasks),
            "overdue": [{"title": t.title, "priority": t.priority} for t in overdue],
            "due_today": [{"title": t.title, "priority": t.priority} for t in due_today],
        },
        "habits": {
            "total": len(habits),
            "done_today": sum(1 for h in habits if h.id in checked),
            "items": [{"name": h.name, "done": h.id in checked} for h in habits],
        },
        "water": {"total_ml": water_total, "goal_ml": water_goal},
        "calories": {"total_kcal": kcal_total, "goal_kcal": kcal_goal},
        "focus": {"total_minutes": focus_total, "goal_minutes": focus_goal},
        "events": [{"time": e.event_time, "title": e.title} for e in events],
        "meals": [{"meal": m.meal_type, "dish": m.dish} for m in meals],
        "bills": [
            {"name": b.name, "due": b.due_date, "overdue": b.due_date < today}
            for b in bills
        ],
        "followups": [
            {"person": f.person, "due": f.due_date, "overdue": f.due_date < today}
            for f in followups
        ],
        "plants_thirsty": [{"name": p.name, "location": p.location} for p in thirsty],
        "chores_due": [{"name": c.name, "assignee": c.assignee} for c in chores_due],
        "birthdays": [{"person": o.person, "kind": o.kind} for o in bdays],
    }


def _section(title: str, items: list, render_item) -> None:
    if not items:
        return
    console.print(f"\n[bold]{title}[/bold]")
    for item in items:
        console.print(f"  {render_item(item)}")


def render_today(json_out: bool) -> None:
    """Render the dashboard to stdout."""
    data = collect_today()
    if json_out:
        _emit_json(data)
        return

    today = data["date"]
    console.print(f"\n📅 [bold]Today[/bold] · {today:%A %d %B %Y}\n")

    # 🎂 Birthdays first — easy to miss
    if data["birthdays"]:
        console.print("[bold]🎂 Today[/bold]")
        for b in data["birthdays"]:
            console.print(f"  🎉 {b['kind'].title()}: [bold]{b['person']}[/bold]")
        console.print()

    # ✅ Tasks
    if data["tasks"]["overdue"] or data["tasks"]["due_today"]:
        console.print("[bold]✅ Tasks[/bold]")
        for t in data["tasks"]["overdue"]:
            console.print(f"  [red]⚠ overdue[/red]  {t['title']}  [dim]({t['priority']})[/dim]")
        for t in data["tasks"]["due_today"]:
            console.print(f"  [yellow]● today[/yellow]    {t['title']}  [dim]({t['priority']})[/dim]")
        console.print()

    # 🔥 Habits
    if data["habits"]["total"]:
        h = data["habits"]
        console.print(f"[bold]🔥 Habits[/bold]  [cyan]{h['done_today']}[/cyan]/{h['total']} done")
        for item in h["items"]:
            mark = "[green]✓[/green]" if item["done"] else "[dim]○[/dim]"
            console.print(f"  {mark} {item['name']}")
        console.print()

    # 💧🍎🍅 Daily metrics
    metric_lines = []
    if data["water"]["goal_ml"]:
        w = data["water"]
        metric_lines.append(
            f"💧 Water    {bar(w['total_ml'], w['goal_ml'], width=18)}  "
            f"[bold]{w['total_ml']}[/bold]/{w['goal_ml']} ml"
        )
    if data["calories"]["goal_kcal"]:
        c = data["calories"]
        metric_lines.append(
            f"🍎 Calories {bar(c['total_kcal'], c['goal_kcal'], width=18)}  "
            f"[bold]{c['total_kcal']}[/bold]/{c['goal_kcal']} kcal"
        )
    if data["focus"]["total_minutes"] or data["focus"]["goal_minutes"]:
        f = data["focus"]
        metric_lines.append(
            f"🍅 Focus    {bar(f['total_minutes'], f['goal_minutes'], width=18)}  "
            f"[bold]{f['total_minutes']}[/bold]/{f['goal_minutes']} min"
        )
    if metric_lines:
        for line in metric_lines:
            console.print(f"  {line}")
        console.print()

    # 📅 Events
    _section(
        "📅 Events",
        data["events"],
        lambda e: f"[cyan]{e['time'] or 'all day'}[/cyan]  {e['title']}",
    )
    # 🍽️ Meals
    _section(
        "🍽️ Meals",
        data["meals"],
        lambda m: f"[cyan]{m['meal']:<10}[/cyan] {m['dish']}",
    )
    # 🧾 Bills
    _section(
        "🧾 Bills due",
        data["bills"],
        lambda b: (f"[red]⚠ overdue[/red]  {b['name']}  [dim]({b['due']})[/dim]"
                   if b["overdue"]
                   else f"[yellow]⏰[/yellow]  {b['name']}  [dim]({b['due']})[/dim]"),
    )
    # 🔔 Follow-ups
    _section(
        "🔔 Follow-ups",
        data["followups"],
        lambda f: (f"[red]⚠[/red] {f['person']}  [dim]({f['due']})[/dim]"
                   if f["overdue"]
                   else f"[yellow]⏰[/yellow] {f['person']}  [dim]({f['due']})[/dim]"),
    )
    # 🪴 Plants & 🧹 chores
    _section(
        "🪴 Plants needing water",
        data["plants_thirsty"],
        lambda p: f"{p['name']}" + (f"  [dim]({p['location']})[/dim]" if p["location"] else ""),
    )
    _section(
        "🧹 Chores due",
        data["chores_due"],
        lambda c: f"{c['name']}" + (f"  [dim]({c['assignee']})[/dim]" if c["assignee"] else ""),
    )

    # Empty-state cheer
    has_anything = any([
        data["birthdays"], data["tasks"]["overdue"], data["tasks"]["due_today"],
        data["habits"]["total"], metric_lines, data["events"], data["meals"],
        data["bills"], data["followups"], data["plants_thirsty"], data["chores_due"],
    ])
    if not has_anything:
        console.print("  [dim]Nothing on the radar today — enjoy! ✨[/dim]\n")
    else:
        console.print()
