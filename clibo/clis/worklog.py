"""🗒️ worklog — work log & standup notes."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, console, fail, ok, render_record, render_rows

NAME = "worklog"
HELP = "🗒️ Work log & standup notes"
EMOJI = "🗒️"
KINDS = ["done", "doing", "blocked", "note"]
KIND_ICON = {"done": "✓", "doing": "→", "blocked": "⚠", "note": "•"}


class WorkLogEntry(SQLModel, table=True):
    """One line of a work log — something done, in progress, or blocked."""

    __tablename__ = "worklog_entry"

    id: int | None = Field(default=None, primary_key=True)
    summary: str
    kind: str = "done"
    project: str | None = None
    entry_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context, json_out: JsonOpt = False) -> None:
    """Default: ``clibo worklog`` (bare) runs the ``today`` summary."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(today, json_out=json_out)


def _row(entry: WorkLogEntry) -> dict:
    return {
        "id": entry.id,
        "entry_date": entry.entry_date,
        "kind": entry.kind,
        "summary": entry.summary,
        "project": entry.project,
    }


def _kind_cell(kind: str) -> str:
    icon = KIND_ICON.get(kind, "•")
    colour = {"done": "green", "doing": "cyan", "blocked": "red", "note": "dim"}.get(kind, "white")
    return f"[{colour}]{icon} {kind}[/{colour}]"


@app.command()
def add(
    summary: str = typer.Argument(..., help="What you worked on"),
    kind: str = typer.Option("done", "--kind", "-k", help="done / doing / blocked / note"),
    project: str = typer.Option(None, "--project", "-P", help="Project"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    json_out: JsonOpt = False,
) -> None:
    """🗒️ Add a work-log entry."""
    kind = kind.lower()
    if kind not in KINDS:
        fail(f"Kind must be one of: {', '.join(KINDS)}", json_out=json_out)
    entry = WorkLogEntry(summary=summary, kind=kind, project=project, entry_date=parse_date(on))
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        data = _row(entry)
    ok(f"Logged {EMOJI} [{kind}] {summary}", json_out=json_out, data=data)


@app.command()
def today(json_out: JsonOpt = False) -> None:
    """🗒️ Show today's work-log entries."""
    with session() as db:
        entries = list(
            db.exec(
                select(WorkLogEntry)
                .where(WorkLogEntry.entry_date == date.today())
                .order_by(WorkLogEntry.id)
            ).all()
        )
    render_rows(
        [_row(e) for e in entries],
        [("id", "ID"), ("kind", "Kind"), ("summary", "Summary"), ("project", "Project")],
        json_out=json_out,
        title=f"🗒️ Work log · {date.today():%a %d %b}",
        formatters={"kind": lambda v, r: _kind_cell(v)},
        empty="Nothing logged today — try: clibo worklog add 'Fixed the build'",
    )


@app.command(name="list")
def list_entries(
    days: int = typer.Option(7, "--days", help="Look back this many days"),
    project: str = typer.Option(None, "--project", "-P", help="Filter by project"),
    json_out: JsonOpt = False,
) -> None:
    """🗒️ List recent work-log entries."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        query = select(WorkLogEntry).where(WorkLogEntry.entry_date >= since)
        if project:
            query = query.where(WorkLogEntry.project == project)
        entries = list(
            db.exec(query.order_by(WorkLogEntry.entry_date.desc(), WorkLogEntry.id.desc())).all()
        )
    render_rows(
        [_row(e) for e in entries],
        [("id", "ID"), ("entry_date", "Date"), ("kind", "Kind"),
         ("summary", "Summary"), ("project", "Project")],
        json_out=json_out,
        title="🗒️ Work log",
        formatters={"kind": lambda v, r: _kind_cell(v)},
        empty="No work logged yet.",
    )


@app.command()
def standup(json_out: JsonOpt = False) -> None:
    """🗣️ Generate a standup: yesterday's done, today's plan, blockers."""
    today_d = date.today()
    yesterday = today_d - timedelta(days=1)
    with session() as db:
        entries = list(db.exec(select(WorkLogEntry)).all())
    yesterday_done = [_row(e) for e in entries
                      if e.entry_date == yesterday and e.kind == "done"]
    today_doing = [_row(e) for e in entries
                   if e.entry_date == today_d and e.kind == "doing"]
    blockers = [_row(e) for e in entries
                if e.entry_date in (today_d, yesterday) and e.kind == "blocked"]
    if json_out:
        render_record(
            {"date": today_d, "yesterday_done": yesterday_done,
             "today_doing": today_doing, "blockers": blockers},
            json_out=True,
        )
        return
    console.print(f"\n🗣️  [bold]Standup[/bold] · {today_d:%A %d %B}\n")

    def _section(title: str, rows: list[dict], icon: str, colour: str) -> None:
        console.print(f"[bold]{title}[/bold]")
        if not rows:
            console.print("  [dim]— nothing —[/dim]")
        for row in rows:
            project = f" [dim]({row['project']})[/dim]" if row["project"] else ""
            console.print(f"  [{colour}]{icon}[/{colour}] {row['summary']}{project}")
        console.print()

    _section("Yesterday", yesterday_done, "✓", "green")
    _section("Today", today_doing, "→", "cyan")
    _section("Blockers", blockers, "⚠", "red")


@app.command()
def rm(entry_id: int = typer.Argument(..., help="Entry ID"), json_out: JsonOpt = False) -> None:
    """🗒️ Delete a work-log entry."""
    with session() as db:
        entry = db.get(WorkLogEntry, entry_id)
        if not entry:
            fail(f"No work-log entry #{entry_id}", json_out=json_out)
        db.delete(entry)
    ok(f"Deleted work-log entry #{entry_id}", json_out=json_out, data={"deleted": entry_id})


@app.command()
def stats(
    days: int = typer.Option(7, "--days", help="Window size in days"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Work-log stats over the last N days."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        entries = list(db.exec(select(WorkLogEntry).where(WorkLogEntry.entry_date >= since)).all())
    by_kind = {k: sum(1 for e in entries if e.kind == k) for k in KINDS}
    data = {
        "window_days": days,
        "entries": len(entries),
        "days_logged": len({e.entry_date for e in entries}),
        "by_kind": by_kind,
    }
    render_record(data, json_out=json_out, title=f"📊 Work-log stats · last {days}d")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
