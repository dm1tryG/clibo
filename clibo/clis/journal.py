"""📔 journal — daily journal & diary."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, console, fail, ok, render_record, render_rows

NAME = "journal"
HELP = "📔 Daily journal & diary"
EMOJI = "📔"


class JournalEntry(SQLModel, table=True):
    """One dated journal / diary entry."""

    __tablename__ = "journal_entry"

    id: int | None = Field(default=None, primary_key=True)
    entry_date: date = Field(default_factory=date.today, index=True)
    body: str
    mood: int | None = None
    tags: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context) -> None:
    """Default: ``clibo journal`` (bare) runs the ``today`` summary."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(today, json_out=False)


def _preview(body: str, width: int = 56) -> str:
    flat = " ".join(body.split())
    return flat if len(flat) <= width else flat[: width - 1] + "…"


def _row(entry: JournalEntry) -> dict:
    return {
        "id": entry.id,
        "entry_date": entry.entry_date,
        "body": entry.body,
        "preview": _preview(entry.body),
        "mood": entry.mood,
        "tags": entry.tags,
    }


def _streak(days: set[date]) -> int:
    """Consecutive journaling days, ending today or yesterday."""
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


@app.command()
def write(
    body: str = typer.Argument(..., help="Your journal entry"),
    on: str = typer.Option("today", "--date", "-d", help="Entry date"),
    mood: int = typer.Option(None, "--mood", "-m", help="Mood 1 (low) – 5 (great)"),
    tag: str = typer.Option(None, "--tag", "-t", help="Comma-separated tags"),
    json_out: JsonOpt = False,
) -> None:
    """📔 Write a journal entry."""
    if mood is not None and (mood < 1 or mood > 5):
        fail("Mood must be 1–5", json_out=json_out)
    entry = JournalEntry(entry_date=parse_date(on), body=body, mood=mood, tags=tag)
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        data = _row(entry)
    ok(f"Saved {EMOJI} journal entry for {entry.entry_date}", json_out=json_out, data=data)


# `add` is the friendlier verb in agent flows — matches every other tool.
app.command(name="add", help="Alias for `write`")(write)


@app.command()
def today(json_out: JsonOpt = False) -> None:
    """📔 Show today's journal entries."""
    with session() as db:
        entries = list(
            db.exec(
                select(JournalEntry)
                .where(JournalEntry.entry_date == date.today())
                .order_by(JournalEntry.id)
            ).all()
        )
    if json_out:
        render_record(
            {"date": date.today(), "entries": [_row(e) for e in entries]}, json_out=True
        )
        return
    if not entries:
        console.print("\n  📔 [dim]Nothing journaled today yet.[/dim]\n")
        return
    console.print(f"\n📔 [bold]Journal[/bold] · {date.today():%A %d %B}\n")
    for entry in entries:
        mood = f"  [dim](mood {entry.mood}/5)[/dim]" if entry.mood else ""
        console.print(f"  [cyan]#{entry.id}[/cyan]{mood}")
        console.print(f"  {entry.body}\n")


@app.command(name="list")
def list_entries(
    days: int = typer.Option(14, "--days", help="Look back this many days"),
    on: str = typer.Option(None, "--date", "-d", help="Only this date"),
    json_out: JsonOpt = False,
) -> None:
    """📔 List recent journal entries."""
    with session() as db:
        query = select(JournalEntry)
        if on:
            query = query.where(JournalEntry.entry_date == parse_date(on))
        else:
            since = date.today() - timedelta(days=days - 1)
            query = query.where(JournalEntry.entry_date >= since)
        entries = list(
            db.exec(query.order_by(JournalEntry.entry_date.desc(), JournalEntry.id.desc())).all()
        )
    render_rows(
        [_row(e) for e in entries],
        [("id", "ID"), ("entry_date", "Date"), ("mood", "Mood"),
         ("preview", "Preview"), ("tags", "Tags")],
        json_out=json_out,
        title="📔 Journal",
        empty="No entries yet — try: clibo journal write 'Today I...'",
    )


@app.command()
def show(entry_id: int = typer.Argument(..., help="Entry ID"), json_out: JsonOpt = False) -> None:
    """📔 Show a journal entry's full text."""
    with session() as db:
        entry = db.get(JournalEntry, entry_id)
        if not entry:
            fail(f"No journal entry #{entry_id}", json_out=json_out)
        data = _row(entry) | {"created_at": entry.created_at}
    if json_out:
        render_record(data, json_out=True)
        return
    render_record(
        {"id": entry.id, "entry_date": entry.entry_date, "mood": entry.mood, "tags": entry.tags},
        json_out=False,
        title=f"📔 Entry #{entry_id}",
    )
    console.print(entry.body)


@app.command()
def edit(
    entry_id: int = typer.Argument(..., help="Entry ID"),
    body: str = typer.Option(None, "--body", "-b", help="New body text"),
    mood: int = typer.Option(None, "--mood", "-m", help="New mood 1–5"),
    tag: str = typer.Option(None, "--tag", "-t", help="New tags"),
    json_out: JsonOpt = False,
) -> None:
    """📔 Edit a journal entry."""
    if mood is not None and (mood < 1 or mood > 5):
        fail("Mood must be 1–5", json_out=json_out)
    with session() as db:
        entry = db.get(JournalEntry, entry_id)
        if not entry:
            fail(f"No journal entry #{entry_id}", json_out=json_out)
        if body is not None:
            entry.body = body
        if mood is not None:
            entry.mood = mood
        if tag is not None:
            entry.tags = tag
        entry.updated_at = datetime.now()
        db.add(entry)
        db.flush()
        data = _row(entry)
    ok(f"Updated journal entry #{entry_id}", json_out=json_out, data=data)


@app.command()
def rm(entry_id: int = typer.Argument(..., help="Entry ID"), json_out: JsonOpt = False) -> None:
    """📔 Delete a journal entry."""
    with session() as db:
        entry = db.get(JournalEntry, entry_id)
        if not entry:
            fail(f"No journal entry #{entry_id}", json_out=json_out)
        db.delete(entry)
    ok(f"Deleted journal entry #{entry_id}", json_out=json_out, data={"deleted": entry_id})


@app.command()
def search(
    query: str = typer.Argument(..., help="Text to search for"),
    json_out: JsonOpt = False,
) -> None:
    """🔍 Search journal entries by text."""
    with session() as db:
        entries = list(
            db.exec(
                select(JournalEntry)
                .where(JournalEntry.body.ilike(f"%{query}%"))
                .order_by(JournalEntry.entry_date.desc())
            ).all()
        )
    render_rows(
        [_row(e) for e in entries],
        [("id", "ID"), ("entry_date", "Date"), ("preview", "Preview"), ("tags", "Tags")],
        json_out=json_out,
        title=f"🔍 Journal matching '{query}'",
        empty=f"No entries match '{query}'.",
    )


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Journal stats — entries, days and streak."""
    with session() as db:
        entries = list(db.exec(select(JournalEntry)).all())
    if not entries:
        fail("No journal entries yet", json_out=json_out)
    days = {e.entry_date for e in entries}
    moods = [e.mood for e in entries if e.mood is not None]
    data = {
        "total_entries": len(entries),
        "days_journaled": len(days),
        "current_streak": _streak(days),
        "avg_mood": round(sum(moods) / len(moods), 1) if moods else None,
    }
    render_record(data, json_out=json_out, title="📊 Journal stats")
