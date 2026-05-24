"""⏱️ time — time tracking by project."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, bar, console, fail, ok, render_record, render_rows

NAME = "time"
HELP = "⏱️ Time tracking by project"
EMOJI = "⏱️"


class TimeEntry(SQLModel, table=True):
    """A completed block of tracked time."""

    __tablename__ = "time_entry"

    id: int | None = Field(default=None, primary_key=True)
    project: str
    task: str | None = None
    minutes: int
    entry_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    note: str | None = None


class TimeTimer(SQLModel, table=True):
    """The single currently-running timer, if any."""

    __tablename__ = "time_timer"

    id: int | None = Field(default=None, primary_key=True)
    project: str
    task: str | None = None
    started_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context) -> None:
    """Default: ``clibo time`` (bare) runs the ``status`` summary."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(status, json_out=False)


def _hm(minutes: int) -> str:
    """Format minutes as ``2h 15m`` (or ``45m``)."""
    hours, mins = divmod(int(minutes), 60)
    return f"{hours}h {mins}m" if hours else f"{mins}m"


@app.command()
def start(
    project: str = typer.Argument(..., help="Project to track time on"),
    task: str = typer.Option(None, "--task", "-t", help="What you're working on"),
    json_out: JsonOpt = False,
) -> None:
    """⏱️ Start a running timer."""
    with session() as db:
        running = db.exec(select(TimeTimer)).first()
        if running:
            fail(f"A timer is already running for '{running.project}' — stop it first",
                 json_out=json_out)
        timer = TimeTimer(project=project, task=task)
        db.add(timer)
        db.flush()
        db.refresh(timer)
        data = {"project": project, "task": task, "started_at": timer.started_at}
    ok(f"Started {EMOJI} timer for '{project}'", json_out=json_out, data=data)


@app.command()
def stop(
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """⏱️ Stop the running timer and log the time."""
    with session() as db:
        running = db.exec(select(TimeTimer)).first()
        if not running:
            fail("No timer is running", json_out=json_out)
        minutes = max(0, round((datetime.now() - running.started_at).total_seconds() / 60))
        entry = TimeEntry(
            project=running.project, task=running.task, minutes=minutes,
            entry_date=date.today(), note=note,
        )
        db.add(entry)
        db.delete(running)
        db.flush()
        db.refresh(entry)
        data = {"id": entry.id, "project": entry.project, "task": entry.task,
                "minutes": minutes, "entry_date": entry.entry_date}
    ok(f"Stopped {EMOJI} — logged {_hm(minutes)} on '{entry.project}'",
       json_out=json_out, data=data)


@app.command()
def status(json_out: JsonOpt = False) -> None:
    """⏱️ Show whether a timer is running."""
    with session() as db:
        running = db.exec(select(TimeTimer)).first()
    if not running:
        if json_out:
            render_record({"running": False}, json_out=True)
        else:
            console.print("\n  ⏱️  [dim]No timer running.[/dim]\n")
        return
    elapsed = round((datetime.now() - running.started_at).total_seconds() / 60)
    data = {"running": True, "project": running.project, "task": running.task,
            "started_at": running.started_at, "elapsed_minutes": elapsed}
    if json_out:
        render_record(data, json_out=True)
        return
    task = f" · {running.task}" if running.task else ""
    console.print(f"\n  ⏱️  [bold]{running.project}[/bold]{task} — running for "
                  f"[cyan]{_hm(elapsed)}[/cyan]\n")


@app.command()
def log(
    project: str = typer.Argument(..., help="Project"),
    minutes: int = typer.Argument(..., help="Minutes to log"),
    task: str = typer.Option(None, "--task", "-t", help="What you worked on"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """⏱️ Log time manually without a timer."""
    if minutes <= 0:
        fail("Minutes must be positive", json_out=json_out)
    entry = TimeEntry(project=project, task=task, minutes=minutes,
                      entry_date=parse_date(on), note=note)
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        data = {"id": entry.id, "project": entry.project, "task": entry.task,
                "minutes": minutes, "entry_date": entry.entry_date}
    ok(f"Logged {EMOJI} {_hm(minutes)} on '{project}'", json_out=json_out, data=data)


# `add` is a friendlier alias for `log` (predictable verbs across tools).
app.command(name="add", help="Alias for `log`")(log)


@app.command(name="list")
def list_entries(
    days: int = typer.Option(7, "--days", help="Look back this many days"),
    project: str = typer.Option(None, "--project", "-P", help="Filter by project"),
    json_out: JsonOpt = False,
) -> None:
    """⏱️ List recent tracked time."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        query = select(TimeEntry).where(TimeEntry.entry_date >= since)
        if project:
            query = query.where(TimeEntry.project == project)
        entries = list(
            db.exec(query.order_by(TimeEntry.entry_date.desc(), TimeEntry.id.desc())).all()
        )
    render_rows(
        [{"id": e.id, "entry_date": e.entry_date, "project": e.project,
          "task": e.task, "minutes": e.minutes} for e in entries],
        [("id", "ID"), ("entry_date", "Date"), ("project", "Project"),
         ("task", "Task"), ("minutes", "Time")],
        json_out=json_out,
        title="⏱️ Time entries",
        formatters={"minutes": lambda v, r: _hm(v)},
        empty="No time logged yet — try: clibo time log myproject 90",
    )


@app.command()
def rm(entry_id: int = typer.Argument(..., help="Entry ID"), json_out: JsonOpt = False) -> None:
    """⏱️ Delete a time entry."""
    with session() as db:
        entry = db.get(TimeEntry, entry_id)
        if not entry:
            fail(f"No time entry #{entry_id}", json_out=json_out)
        db.delete(entry)
    ok(f"Deleted time entry #{entry_id}", json_out=json_out, data={"deleted": entry_id})


@app.command()
def report(
    days: int = typer.Option(7, "--days", help="Window size in days"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Time spent per project over the last N days."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        entries = list(db.exec(select(TimeEntry).where(TimeEntry.entry_date >= since)).all())
    total = sum(e.minutes for e in entries)
    by_project: dict[str, int] = {}
    for entry in entries:
        by_project[entry.project] = by_project.get(entry.project, 0) + entry.minutes
    rows = [
        {"project": p, "minutes": m, "hours": round(m / 60, 1),
         "share": round(m / total * 100, 1) if total else 0.0}
        for p, m in sorted(by_project.items(), key=lambda kv: kv[1], reverse=True)
    ]
    if json_out:
        render_record(
            {"window_days": days, "total_minutes": total, "by_project": rows},
            json_out=True,
        )
        return
    render_rows(
        rows,
        [("project", "Project"), ("minutes", "Time"), ("share", "Share")],
        json_out=False,
        title=f"📊 Time report · last {days}d",
        formatters={
            "minutes": lambda v, r: _hm(v),
            "share": lambda v, r: bar(v, 100),
        },
        empty="No time logged in this window.",
    )
    if rows:
        console.print(f"  ⏱️  [bold]Total:[/bold] {_hm(total)}")


@app.command()
def stats(
    days: int = typer.Option(7, "--days", help="Window size in days"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Time-tracking stats over the last N days."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        entries = list(db.exec(select(TimeEntry).where(TimeEntry.entry_date >= since)).all())
    if not entries:
        fail("No time logged in this window", json_out=json_out)
    total = sum(e.minutes for e in entries)
    data = {
        "window_days": days,
        "entries": len(entries),
        "total_minutes": total,
        "total_hours": round(total / 60, 1),
        "projects": len({e.project for e in entries}),
        "days_tracked": len({e.entry_date for e in entries}),
        "avg_minutes_per_day": round(total / days),
    }
    render_record(data, json_out=json_out, title=f"📊 Time stats · last {days}d")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
