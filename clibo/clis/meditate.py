"""🧘 meditate — meditation & mindfulness sessions."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, bar, console, fail, ok, render_record, render_rows
from clibo.core.settings import get_setting, set_setting

NAME = "meditate"
HELP = "🧘 Meditation & mindfulness sessions"
EMOJI = "🧘"
DEFAULT_GOAL_MIN = 10


class MeditationSession(SQLModel, table=True):
    """One meditation or mindfulness session."""

    __tablename__ = "meditate_session"

    id: int | None = Field(default=None, primary_key=True)
    minutes: int
    kind: str = "mindfulness"
    entry_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    note: str | None = None


app = typer.Typer(no_args_is_help=True, help=HELP)


def _goal() -> int:
    return int(get_setting(NAME, "daily_min", str(DEFAULT_GOAL_MIN)) or DEFAULT_GOAL_MIN)


def _streak(days: set[date]) -> int:
    """Count consecutive days with a session, ending today or yesterday."""
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


def _row(entry: MeditationSession) -> dict:
    return {
        "id": entry.id,
        "entry_date": entry.entry_date,
        "minutes": entry.minutes,
        "kind": entry.kind,
        "note": entry.note,
    }


@app.command()
def log(
    minutes: int = typer.Argument(..., help="Session length in minutes"),
    kind: str = typer.Option("mindfulness", "--kind", "-k", help="e.g. breathing, guided, body-scan"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🧘 Log a meditation session."""
    if minutes <= 0:
        fail("Minutes must be positive", json_out=json_out)
    entry = MeditationSession(
        minutes=minutes, kind=kind.lower(), entry_date=parse_date(on), note=note
    )
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        data = _row(entry)
    ok(f"Logged {EMOJI} {minutes} min of {kind}", json_out=json_out, data=data)


# `add` is a friendlier alias for `log` (predictable verbs across tools).
app.command(name="add", help="Alias for `log`")(log)


@app.command()
def today(json_out: JsonOpt = False) -> None:
    """🧘 Show today's meditation and goal progress."""
    day = date.today()
    with session() as db:
        entries = list(
            db.exec(
                select(MeditationSession)
                .where(MeditationSession.entry_date == day)
                .order_by(MeditationSession.created_at)
            ).all()
        )
    total = sum(e.minutes for e in entries)
    goal = _goal()
    if json_out:
        render_record(
            {"date": day, "sessions": [_row(e) for e in entries],
             "total_minutes": total, "goal_minutes": goal, "reached": total >= goal},
            json_out=True,
        )
        return
    console.print(f"\n🧘 [bold]Meditation today[/bold] · {day:%a %d %b}\n")
    console.print(f"  {bar(total, goal)}")
    console.print(
        f"  [bold cyan]{total}[/bold cyan] / {goal} min   ·   {len(entries)} sessions"
    )
    console.print(
        "  [green]✓ Goal reached — well done![/green]\n" if total >= goal
        else f"  [yellow]{goal - total} min to go[/yellow]\n"
    )


@app.command(name="list")
def list_entries(
    days: int = typer.Option(14, "--days", help="Look back this many days"),
    json_out: JsonOpt = False,
) -> None:
    """🧘 List recent meditation sessions."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        entries = list(
            db.exec(
                select(MeditationSession)
                .where(MeditationSession.entry_date >= since)
                .order_by(MeditationSession.entry_date.desc(), MeditationSession.id.desc())
            ).all()
        )
    render_rows(
        [_row(e) for e in entries],
        [("id", "ID"), ("entry_date", "Date"), ("minutes", "Minutes"),
         ("kind", "Kind"), ("note", "Note")],
        json_out=json_out,
        title="🧘 Meditation log",
        empty="No sessions yet — try: clibo meditate log 10 -k breathing",
    )


@app.command()
def rm(entry_id: int = typer.Argument(..., help="Session ID"), json_out: JsonOpt = False) -> None:
    """🧘 Delete a meditation session."""
    with session() as db:
        entry = db.get(MeditationSession, entry_id)
        if not entry:
            fail(f"No session #{entry_id}", json_out=json_out)
        db.delete(entry)
    ok(f"Deleted session #{entry_id}", json_out=json_out, data={"deleted": entry_id})


@app.command()
def goal(
    set_min: int = typer.Option(None, "--set", help="Set your daily meditation goal in minutes"),
    json_out: JsonOpt = False,
) -> None:
    """🎯 Show or set your daily meditation goal."""
    if set_min is not None:
        if set_min <= 0:
            fail("Goal must be positive", json_out=json_out)
        set_setting(NAME, "daily_min", str(set_min))
        ok(f"Daily meditation goal set to {set_min} min", json_out=json_out,
           data={"daily_min": set_min})
        return
    render_record({"daily_min": _goal()}, json_out=json_out, title="🎯 Meditation goal")


@app.command()
def streak(json_out: JsonOpt = False) -> None:
    """🔥 Show your current meditation streak."""
    with session() as db:
        days = {e.entry_date for e in db.exec(select(MeditationSession)).all()}
    current = _streak(days)
    if json_out:
        render_record({"current_streak": current, "days_practiced": len(days)}, json_out=True)
        return
    flame = "🔥" * min(current, 10) if current else "[dim]—[/dim]"
    console.print(f"\n  🧘 Meditation streak: [bold cyan]{current}[/bold cyan] days  {flame}\n")


@app.command()
def stats(
    days: int = typer.Option(30, "--days", help="Window size in days"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Meditation stats over the last N days."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        entries = list(
            db.exec(select(MeditationSession).where(MeditationSession.entry_date >= since)).all()
        )
        all_days = {e.entry_date for e in db.exec(select(MeditationSession)).all()}
    if not entries:
        fail("No sessions in this window", json_out=json_out)
    total = sum(e.minutes for e in entries)
    practised = {e.entry_date for e in entries}
    data = {
        "window_days": days,
        "sessions": len(entries),
        "days_practised": len(practised),
        "total_minutes": total,
        "avg_minutes_per_session": round(total / len(entries), 1),
        "longest_session": max(e.minutes for e in entries),
        "current_streak": _streak(all_days),
    }
    render_record(data, json_out=json_out, title=f"📊 Meditation stats · last {days}d")
