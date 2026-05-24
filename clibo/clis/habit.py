"""🔥 habit — habit tracker with streaks."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, console, fail, ok, render_record, render_rows

NAME = "habit"
HELP = "🔥 Habit tracker with streaks"
EMOJI = "🔥"


class Habit(SQLModel, table=True):
    """A habit the user wants to keep up."""

    __tablename__ = "habit_habit"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    target_per_week: int = 7
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)


class HabitCheck(SQLModel, table=True):
    """A single day a habit was completed."""

    __tablename__ = "habit_check"

    id: int | None = Field(default=None, primary_key=True)
    habit_id: int = Field(index=True)
    check_date: date = Field(default_factory=date.today, index=True)


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context, json_out: JsonOpt = False) -> None:
    """Default: ``clibo habit`` (bare) shows today's done / pending habits."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(today, json_out=json_out)


def _resolve(db, ident: str) -> Habit | None:
    """Look up a habit by numeric ID or by (case-insensitive) name."""
    if ident.isdigit():
        habit = db.get(Habit, int(ident))
        if habit:
            return habit
    return db.exec(select(Habit).where(Habit.name.ilike(ident))).first()


def _checks(db, habit_id: int) -> set[date]:
    """All dates a habit was checked off."""
    return {
        c.check_date
        for c in db.exec(select(HabitCheck).where(HabitCheck.habit_id == habit_id)).all()
    }


def _streak(days: set[date]) -> int:
    """Current run of consecutive days, ending today or yesterday."""
    if not days:
        return 0
    cursor = date.today()
    if cursor not in days:
        cursor -= timedelta(days=1)
    if cursor not in days:
        return 0
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _longest_streak(days: set[date]) -> int:
    """The longest run of consecutive days ever."""
    if not days:
        return 0
    ordered = sorted(days)
    longest = run = 1
    for i in range(1, len(ordered)):
        run = run + 1 if (ordered[i] - ordered[i - 1]).days == 1 else 1
        longest = max(longest, run)
    return longest


def _week_count(days: set[date]) -> int:
    """How many times the habit was checked this calendar week (from Monday)."""
    monday = date.today() - timedelta(days=date.today().weekday())
    return sum(1 for d in days if d >= monday)


def _row(db, habit: Habit) -> dict:
    checks = _checks(db, habit.id)
    this_week = _week_count(checks)
    target = habit.target_per_week
    today = date.today()
    days_elapsed = today.weekday() + 1   # Mon=1 … Sun=7
    days_left_this_week = 7 - days_elapsed
    # Pace check: by day N you should have at least floor(target * N / 7).
    # Floor (not ceil) is the kinder definition — Wednesday of a 3-per-week
    # target needs 1, not 2.
    expected_by_now = (target * days_elapsed) // 7
    on_pace = this_week >= expected_by_now
    return {
        "id": habit.id,
        "name": habit.name,
        "current_streak": _streak(checks),
        "longest_streak": _longest_streak(checks),
        "this_week": this_week,
        "target_per_week": target,
        "target_remaining": max(0, target - this_week),
        "days_left_this_week": days_left_this_week,
        "on_pace": on_pace,
        "total_checks": len(checks),
        "done_today": today in checks,
        "active": habit.active,
    }


@app.command()
def add(
    name: str = typer.Argument(..., help="Habit name, e.g. 'Read 10 pages'"),
    target: int = typer.Option(7, "--target", "-t", help="Target days per week (1–7)"),
    json_out: JsonOpt = False,
) -> None:
    """🔥 Create a habit to track."""
    if target < 1 or target > 7:
        fail("Target must be between 1 and 7 days per week", json_out=json_out)
    habit = Habit(name=name, target_per_week=target)
    with session() as db:
        db.add(habit)
        db.flush()
        db.refresh(habit)
        data = _row(db, habit)
    ok(f"Created {EMOJI} habit '{name}'", json_out=json_out, data=data)


@app.command()
def check(
    habit: str = typer.Argument(..., help="Habit name or ID"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    json_out: JsonOpt = False,
) -> None:
    """🔥 Mark a habit done for a day."""
    day = parse_date(on)
    with session() as db:
        target = _resolve(db, habit)
        if not target:
            fail(f"No habit matching {habit!r}", json_out=json_out)
        existing = db.exec(
            select(HabitCheck).where(
                HabitCheck.habit_id == target.id, HabitCheck.check_date == day
            )
        ).first()
        if not existing:
            db.add(HabitCheck(habit_id=target.id, check_date=day))
            db.flush()
        data = _row(db, target)
    streak = data["current_streak"]
    ok(f"Checked {EMOJI} {target.name} — {streak}-day streak", json_out=json_out, data=data)


@app.command()
def uncheck(
    habit: str = typer.Argument(..., help="Habit name or ID"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    json_out: JsonOpt = False,
) -> None:
    """🔥 Remove a habit's check for a day."""
    day = parse_date(on)
    with session() as db:
        target = _resolve(db, habit)
        if not target:
            fail(f"No habit matching {habit!r}", json_out=json_out)
        existing = db.exec(
            select(HabitCheck).where(
                HabitCheck.habit_id == target.id, HabitCheck.check_date == day
            )
        ).first()
        if existing:
            db.delete(existing)
            db.flush()
        data = _row(db, target)
    ok(f"Unchecked {target.name} for {day}", json_out=json_out, data=data)


@app.command(name="list")
def list_habits(
    show_all: bool = typer.Option(False, "--all", help="Include inactive habits"),
    json_out: JsonOpt = False,
) -> None:
    """🔥 List habits with streaks and weekly progress."""
    with session() as db:
        query = select(Habit)
        if not show_all:
            query = query.where(Habit.active == True)  # noqa: E712
        habits = list(db.exec(query.order_by(Habit.name)).all())
        rows = [_row(db, h) for h in habits]
    render_rows(
        rows,
        [("id", "ID"), ("name", "Habit"), ("done_today", "Today"),
         ("current_streak", "Streak"), ("this_week", "This Week"),
         ("longest_streak", "Best")],
        json_out=json_out,
        title="🔥 Habits",
        formatters={
            "done_today": lambda v, r: "[green]✓[/green]" if v else "[dim]·[/dim]",
            "current_streak": lambda v, r: f"🔥 {v}" if v else "[dim]0[/dim]",
            "this_week": lambda v, r: f"{v}/{r['target_per_week']}",
        },
        empty="No habits yet — try: clibo habit add 'Read 10 pages'",
    )


@app.command()
def today(json_out: JsonOpt = False) -> None:
    """🔥 Show which habits are done and pending today."""
    with session() as db:
        habits = list(
            db.exec(select(Habit).where(Habit.active == True).order_by(Habit.name)).all()  # noqa: E712
        )
        rows = [_row(db, h) for h in habits]
    done = [r for r in rows if r["done_today"]]
    pending = [r for r in rows if not r["done_today"]]
    if json_out:
        render_record(
            {"date": date.today(), "done": done, "pending": pending,
             "completion_pct": round(len(done) / len(rows) * 100, 1) if rows else 0.0},
            json_out=True,
        )
        return
    console.print(f"\n🔥 [bold]Habits today[/bold] · {date.today():%a %d %b}\n")
    for row in rows:
        mark = "[green]✓[/green]" if row["done_today"] else "[dim]○[/dim]"
        streak = f"  [dim](🔥 {row['current_streak']})[/dim]" if row["current_streak"] else ""
        console.print(f"  {mark} {row['name']}{streak}")
    if rows:
        console.print(f"\n  [bold]{len(done)}/{len(rows)}[/bold] done today\n")
    else:
        console.print("  [dim]No habits yet.[/dim]\n")


@app.command()
def rm(habit_id: int = typer.Argument(..., help="Habit ID"), json_out: JsonOpt = False) -> None:
    """🔥 Delete a habit and its history."""
    with session() as db:
        habit = db.get(Habit, habit_id)
        if not habit:
            fail(f"No habit #{habit_id}", json_out=json_out)
        for chk in db.exec(select(HabitCheck).where(HabitCheck.habit_id == habit_id)).all():
            db.delete(chk)
        db.delete(habit)
    ok(f"Deleted habit #{habit_id}", json_out=json_out, data={"deleted": habit_id})


@app.command()
def stats(
    habit: str = typer.Argument(..., help="Habit name or ID"),
    days: int = typer.Option(30, "--days", help="Completion-rate window"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Detailed stats for one habit."""
    with session() as db:
        target = _resolve(db, habit)
        if not target:
            fail(f"No habit matching {habit!r}", json_out=json_out)
        checks = _checks(db, target.id)
    since = date.today() - timedelta(days=days - 1)
    in_window = sum(1 for d in checks if d >= since)
    data = {
        "name": target.name,
        "total_checks": len(checks),
        "current_streak": _streak(checks),
        "longest_streak": _longest_streak(checks),
        "this_week": _week_count(checks),
        "target_per_week": target.target_per_week,
        "window_days": days,
        "completion_pct": round(in_window / days * 100, 1),
    }
    render_record(data, json_out=json_out, title=f"📊 Habit stats · {target.name}")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
