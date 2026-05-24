"""🍅 focus — pomodoro & focus sessions."""

from __future__ import annotations

import time
from datetime import date, datetime, timedelta

import typer
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, bar, console, fail, ok, render_record, render_rows
from clibo.core.settings import get_setting, set_setting

NAME = "focus"
HELP = "🍅 Pomodoro & focus sessions"
EMOJI = "🍅"
DEFAULT_POMODORO = 25
DEFAULT_GOAL_MIN = 100


class FocusSession(SQLModel, table=True):
    """One completed focus / pomodoro session."""

    __tablename__ = "focus_session"

    id: int | None = Field(default=None, primary_key=True)
    task: str | None = None
    minutes: int
    entry_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    note: str | None = None


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context, json_out: JsonOpt = False) -> None:
    """Default: ``clibo focus`` (bare) runs the ``today`` summary."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(today, json_out=json_out)


def _goal() -> int:
    return int(get_setting(NAME, "daily_min", str(DEFAULT_GOAL_MIN)) or DEFAULT_GOAL_MIN)


def _record(task: str | None, minutes: int, on: date, note: str | None) -> dict:
    entry = FocusSession(task=task, minutes=minutes, entry_date=on, note=note)
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        return {
            "id": entry.id, "task": entry.task, "minutes": entry.minutes,
            "entry_date": entry.entry_date, "note": entry.note,
        }


def _countdown(minutes: int, label: str) -> None:
    """Run a live countdown for `minutes`, drawing a progress bar."""
    total = minutes * 60
    with Progress(
        TextColumn("[bold]🍅 {task.description}"),
        BarColumn(bar_width=30),
        TextColumn("[cyan]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(label, total=total)
        for _ in range(total):
            time.sleep(1)
            progress.advance(task)


@app.command()
def log(
    minutes: str = typer.Argument(
        str(DEFAULT_POMODORO),
        help="Length of the session — minutes ('45') or H:MM ('1:25')",
    ),
    task: str = typer.Option(None, "--task", "-t", help="What you focused on"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🍅 Log a completed focus session.

    Accepts plain minutes (``focus log 45``) or H:MM notation
    (``focus log 1:25`` → 85 minutes).
    """
    if ":" in minutes:
        try:
            h_part, m_part = minutes.split(":", 1)
            parsed_min = int(h_part) * 60 + int(m_part)
        except ValueError:
            fail(
                f"Bad H:MM format: {minutes!r}. Expected '1:25' or a "
                "plain integer.",
                json_out=json_out,
            )
    else:
        try:
            parsed_min = int(minutes)
        except ValueError:
            fail(
                f"Minutes must be an integer or H:MM (got {minutes!r})",
                json_out=json_out,
            )
    if parsed_min <= 0:
        fail("Minutes must be positive", json_out=json_out)
    data = _record(task, parsed_min, parse_date(on), note)
    label = f" on {task}" if task else ""
    ok(f"Logged {EMOJI} {parsed_min} min focus{label}", json_out=json_out, data=data)


# `add` is a friendlier alias for `log` (predictable verbs across tools).
app.command(name="add", help="Alias for `log`")(log)


@app.command()
def timer(
    minutes: int = typer.Option(DEFAULT_POMODORO, "--minutes", "-m", help="Pomodoro length"),
    task: str = typer.Option(None, "--task", "-t", help="What you're focusing on"),
    json_out: JsonOpt = False,
) -> None:
    """🍅 Run a live pomodoro timer, then log the session."""
    if minutes <= 0:
        fail("Minutes must be positive", json_out=json_out)
    if not json_out:
        _countdown(minutes, task or "focus")
    data = _record(task, minutes, date.today(), None)
    ok(f"Pomodoro done {EMOJI} {minutes} min logged", json_out=json_out, data=data)


@app.command()
def today(json_out: JsonOpt = False) -> None:
    """🍅 Today's focus time and goal progress."""
    day = date.today()
    with session() as db:
        sessions = list(
            db.exec(select(FocusSession).where(FocusSession.entry_date == day)).all()
        )
    total = sum(s.minutes for s in sessions)
    goal = _goal()
    remaining_minutes = max(0, goal - total) if goal > 0 else None
    pct_of_goal = round(total / goal * 100, 1) if goal > 0 else None
    if json_out:
        render_record(
            {"date": day, "sessions": len(sessions), "total_minutes": total,
             "goal_minutes": goal,
             "reached": total >= goal if goal > 0 else False,
             "remaining_minutes": remaining_minutes,
             "pct_of_goal": pct_of_goal},
            json_out=True,
        )
        return
    console.print(f"\n🍅 [bold]Focus today[/bold] · {day:%a %d %b}\n")
    console.print(f"  {bar(total, goal)}")
    console.print(f"  [bold cyan]{total}[/bold cyan] / {goal} min   ·   {len(sessions)} sessions")
    console.print(
        "  [green]✓ Goal reached![/green]\n" if total >= goal
        else f"  [yellow]{goal - total} min to go[/yellow]\n"
    )


@app.command(name="list")
def list_sessions(
    days: int = typer.Option(7, "--days", help="Look back this many days"),
    json_out: JsonOpt = False,
) -> None:
    """🍅 List recent focus sessions."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        sessions = list(
            db.exec(
                select(FocusSession)
                .where(FocusSession.entry_date >= since)
                .order_by(FocusSession.entry_date.desc(), FocusSession.id.desc())
            ).all()
        )
    render_rows(
        [{"id": s.id, "entry_date": s.entry_date, "task": s.task,
          "minutes": s.minutes, "note": s.note} for s in sessions],
        [("id", "ID"), ("entry_date", "Date"), ("task", "Task"),
         ("minutes", "Minutes"), ("note", "Note")],
        json_out=json_out,
        title="🍅 Focus sessions",
        empty="No focus sessions yet — try: clibo focus log 25 -t 'deep work'",
    )


@app.command()
def rm(session_id: int = typer.Argument(..., help="Session ID"), json_out: JsonOpt = False) -> None:
    """🍅 Delete a focus session."""
    with session() as db:
        entry = db.get(FocusSession, session_id)
        if not entry:
            fail(f"No focus session #{session_id}", json_out=json_out)
        db.delete(entry)
    ok(f"Deleted focus session #{session_id}", json_out=json_out, data={"deleted": session_id})


@app.command()
def goal(
    set_min: int = typer.Option(None, "--set", help="Set your daily focus goal in minutes"),
    json_out: JsonOpt = False,
) -> None:
    """🎯 Show or set your daily focus goal."""
    if set_min is not None:
        if set_min <= 0:
            fail("Goal must be positive", json_out=json_out)
        set_setting(NAME, "daily_min", str(set_min))
        ok(f"Daily focus goal set to {set_min} min", json_out=json_out,
           data={"daily_min": set_min})
        return
    render_record({"daily_min": _goal()}, json_out=json_out, title="🎯 Focus goal")


@app.command()
def stats(
    days: int = typer.Option(7, "--days", help="Window size in days"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Focus stats over the last N days."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        sessions = list(
            db.exec(select(FocusSession).where(FocusSession.entry_date >= since)).all()
        )
    if not sessions:
        fail("No focus sessions in this window", json_out=json_out)
    total = sum(s.minutes for s in sessions)
    # Best single session — *"what's my longest unbroken focus block?"*.
    # Distinct from the per-day total since one day may contain many.
    best = max(sessions, key=lambda s: s.minutes)
    # Best day — total focus across multiple sessions on the same date.
    daily: dict[date, int] = {}
    for s in sessions:
        daily[s.entry_date] = daily.get(s.entry_date, 0) + s.minutes
    best_day = max(daily.items(), key=lambda kv: kv[1])
    data = {
        "window_days": days,
        "sessions": len(sessions),
        "total_minutes": total,
        "total_hours": round(total / 60, 1),
        "avg_session_minutes": round(total / len(sessions), 1),
        "days_focused": len({s.entry_date for s in sessions}),
        "best_session": {
            "id": best.id,
            "entry_date": best.entry_date,
            "task": best.task,
            "minutes": best.minutes,
        },
        "best_day": {"date": best_day[0], "minutes": best_day[1]},
    }
    render_record(data, json_out=json_out, title=f"📊 Focus stats · last {days}d")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
