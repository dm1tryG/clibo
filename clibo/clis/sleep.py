"""😴 sleep — sleep duration & quality tracker."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, bar, console, fail, ok, render_record, render_rows
from clibo.core.settings import get_setting, set_setting

NAME = "sleep"
HELP = "😴 Sleep duration & quality tracker"
EMOJI = "😴"
DEFAULT_GOAL_HOURS = 8.0
QUALITY_LABELS = {1: "terrible", 2: "poor", 3: "okay", 4: "good", 5: "great"}


class SleepLog(SQLModel, table=True):
    """One night of sleep, dated by the morning you woke up."""

    __tablename__ = "sleep_log"

    id: int | None = Field(default=None, primary_key=True)
    hours: float
    quality: int = 3
    entry_date: date = Field(default_factory=date.today, index=True)
    bedtime: str | None = None
    wake_time: str | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context) -> None:
    """Default: ``clibo sleep`` (bare) shows your most recent night."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(last, json_out=False)


def _goal() -> float:
    return float(get_setting(NAME, "goal_hours", str(DEFAULT_GOAL_HOURS)) or DEFAULT_GOAL_HOURS)


def _row(entry: SleepLog) -> dict:
    return {
        "id": entry.id,
        "entry_date": entry.entry_date,
        "hours": entry.hours,
        "quality": entry.quality,
        "quality_label": QUALITY_LABELS.get(entry.quality, "?"),
        "bedtime": entry.bedtime,
        "wake_time": entry.wake_time,
        "note": entry.note,
    }


@app.command()
def log(
    hours: float = typer.Argument(..., help="Hours slept, e.g. 7.5"),
    quality: int = typer.Option(3, "--quality", "-q", help="Sleep quality, 1 (terrible) – 5 (great)"),
    on: str = typer.Option("today", "--date", "-d", help="Date you woke up"),
    bedtime: str = typer.Option(None, "--bedtime", "-b", help="Bedtime, e.g. 23:30"),
    wake: str = typer.Option(None, "--wake", "-w", help="Wake time, e.g. 07:15"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """😴 Log a night of sleep."""
    if hours <= 0 or hours > 24:
        fail("Hours must be between 0 and 24", json_out=json_out)
    if quality not in QUALITY_LABELS:
        fail("Quality must be 1–5", json_out=json_out)
    entry = SleepLog(
        hours=hours,
        quality=quality,
        entry_date=parse_date(on),
        bedtime=bedtime,
        wake_time=wake,
        note=note,
    )
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        data = _row(entry)
    ok(
        f"Logged {EMOJI} {hours:g}h sleep — {QUALITY_LABELS[quality]} quality",
        json_out=json_out,
        data=data,
    )


# `add` is a friendlier alias for `log` (predictable verbs across tools).
app.command(name="add", help="Alias for `log`")(log)


@app.command()
def last(json_out: JsonOpt = False) -> None:
    """😴 Show your most recent night of sleep."""
    with session() as db:
        entry = db.exec(
            select(SleepLog).order_by(SleepLog.entry_date.desc(), SleepLog.id.desc())
        ).first()
    if not entry:
        fail("No sleep logged yet — try: clibo sleep log 7.5 -q 4", json_out=json_out)
    data = _row(entry)
    goal = _goal()
    if json_out:
        render_record(data | {"goal_hours": goal}, json_out=True)
        return
    console.print(f"\n😴 [bold]Last night[/bold] · {entry.entry_date:%a %d %b}\n")
    console.print(f"  {bar(entry.hours, goal)}")
    console.print(
        f"  [bold cyan]{entry.hours:g}h[/bold cyan] / {goal:g}h goal   ·   "
        f"quality: [bold]{entry.quality}/5[/bold] ({QUALITY_LABELS[entry.quality]})"
    )
    if entry.bedtime or entry.wake_time:
        console.print(f"  🛏️  {entry.bedtime or '?'}  →  ☀️  {entry.wake_time or '?'}")
    if entry.note:
        console.print(f"  [dim]{entry.note}[/dim]")
    console.print()


@app.command(name="list")
def list_entries(
    days: int = typer.Option(7, "--days", help="Look back this many days"),
    json_out: JsonOpt = False,
) -> None:
    """😴 List recent nights of sleep."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        entries = list(
            db.exec(
                select(SleepLog)
                .where(SleepLog.entry_date >= since)
                .order_by(SleepLog.entry_date.desc(), SleepLog.id.desc())
            ).all()
        )
    render_rows(
        [_row(e) for e in entries],
        [("id", "ID"), ("entry_date", "Date"), ("hours", "Hours"),
         ("quality", "Quality"), ("quality_label", "Rating"), ("note", "Note")],
        json_out=json_out,
        title="😴 Sleep log",
        empty="No sleep logged yet — try: clibo sleep log 7.5 -q 4",
    )


@app.command()
def rm(entry_id: int = typer.Argument(..., help="Log ID"), json_out: JsonOpt = False) -> None:
    """😴 Delete a sleep log entry."""
    with session() as db:
        entry = db.get(SleepLog, entry_id)
        if not entry:
            fail(f"No sleep log #{entry_id}", json_out=json_out)
        db.delete(entry)
    ok(f"Deleted sleep log #{entry_id}", json_out=json_out, data={"deleted": entry_id})


@app.command()
def edit(
    target: str = typer.Argument(..., help="Entry ID or 'last' for the most recent"),
    hours: float = typer.Option(None, "--hours", "-H", help="New hours of sleep"),
    quality: int = typer.Option(None, "--quality", "-q", help="New quality 1–5"),
    bedtime: str = typer.Option(None, "--bed", "-b", help="New bedtime (free text)"),
    wake_time: str = typer.Option(None, "--wake", "-w", help="New wake time"),
    note: str = typer.Option(None, "--note", "-n", help="New note"),
    on: str = typer.Option(None, "--date", "-d", help="New date"),
    json_out: JsonOpt = False,
) -> None:
    """😴 Edit an existing sleep log."""
    from clibo.core.base import resolve_id
    with session() as db:
        entry = resolve_id(target, SleepLog, db)
        if not entry:
            fail(f"No sleep log matching {target!r}", json_out=json_out)
        if hours is not None:
            if hours <= 0:
                fail("Hours must be positive", json_out=json_out)
            entry.hours = hours
        if quality is not None:
            if not 1 <= quality <= 5:
                fail("Quality must be 1–5", json_out=json_out)
            entry.quality = quality
        if bedtime is not None:
            entry.bedtime = bedtime
        if wake_time is not None:
            entry.wake_time = wake_time
        if note is not None:
            entry.note = note
        if on is not None:
            entry.entry_date = parse_date(on)
        db.add(entry)
        db.flush()
        data = _row(entry)
    ok(f"Updated sleep log #{entry.id} — {entry.hours:g}h",
       json_out=json_out, data=data)


@app.command()
def goal(
    set_hours: float = typer.Option(None, "--set", help="Set your nightly sleep goal in hours"),
    json_out: JsonOpt = False,
) -> None:
    """🎯 Show or set your nightly sleep goal."""
    if set_hours is not None:
        if set_hours <= 0 or set_hours > 24:
            fail("Goal must be between 0 and 24 hours", json_out=json_out)
        set_setting(NAME, "goal_hours", str(set_hours))
        ok(f"Sleep goal set to {set_hours:g}h", json_out=json_out, data={"goal_hours": set_hours})
        return
    render_record({"goal_hours": _goal()}, json_out=json_out, title="🎯 Sleep goal")


@app.command()
def stats(
    days: int = typer.Option(7, "--days", help="Window size in days"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Sleep stats over the last N days."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        entries = list(db.exec(select(SleepLog).where(SleepLog.entry_date >= since)).all())
    if not entries:
        fail("No sleep logged in this window", json_out=json_out)
    from clibo.core.sparkline import sparkline_days
    hours = [e.hours for e in entries]
    quality = [e.quality for e in entries]
    goal = _goal()
    by_date = {e.entry_date: e.hours for e in entries}
    data = {
        "window_days": days,
        "nights_logged": len(entries),
        "avg_hours": round(sum(hours) / len(hours), 1),
        "min_hours": min(hours),
        "max_hours": max(hours),
        "avg_quality": round(sum(quality) / len(quality), 1),
        "nights_goal_reached": sum(1 for h in hours if h >= goal),
        "goal_hours": goal,
        "chart": sparkline_days(by_date, since, date.today()),
    }
    render_record(data, json_out=json_out, title=f"📊 Sleep stats · last {days}d")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)
