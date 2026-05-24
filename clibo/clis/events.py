"""📅 events — events & reminders calendar."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import humanize_delta, parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, console, fail, ok, render_record, render_rows

NAME = "events"
HELP = "📅 Events & reminders calendar"
EMOJI = "📅"


class Event(SQLModel, table=True):
    """A calendar event or reminder."""

    __tablename__ = "events_event"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    event_date: date = Field(index=True)
    event_time: str | None = None
    location: str | None = None
    category: str = "other"
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context, json_out: JsonOpt = False) -> None:
    """Default: ``clibo events`` (bare) runs the ``today`` summary."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(today, json_out=json_out)


def _row(event: Event) -> dict:
    return {
        "id": event.id,
        "title": event.title,
        "event_date": event.event_date,
        "event_time": event.event_time,
        "when": humanize_delta(event.event_date),
        "days_until": (event.event_date - date.today()).days,
        "location": event.location,
        "category": event.category,
        "note": event.note,
    }


def _sorted(events: list[Event]) -> list[Event]:
    """By date, then time (untimed events first)."""
    return sorted(events, key=lambda e: (e.event_date, e.event_time or ""))


@app.command()
def add(
    title: str = typer.Argument(..., help="Event title"),
    on: str = typer.Option(..., "--date", "-d", help="Event date"),
    at: str = typer.Option(None, "--time", "-t", help="Time, e.g. 14:30"),
    location: str = typer.Option(None, "--location", "-l", help="Where"),
    category: str = typer.Option("other", "--category", "-c", help="Category"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """📅 Add an event or reminder."""
    event = Event(
        title=title, event_date=parse_date(on), event_time=at,
        location=location, category=category.lower(), note=note,
    )
    with session() as db:
        db.add(event)
        db.flush()
        db.refresh(event)
        data = _row(event)
    ok(f"Added {EMOJI} {title} — {event.event_date} ({data['when']})",
       json_out=json_out, data=data)


@app.command(name="list")
def list_events(
    show_all: bool = typer.Option(False, "--all", help="Include past events"),
    category: str = typer.Option(None, "--category", "-c",
                                  help="Filter by category"),
    json_out: JsonOpt = False,
) -> None:
    """📅 List events (upcoming first; optionally filtered by category)."""
    with session() as db:
        query = select(Event)
        if not show_all:
            query = query.where(Event.event_date >= date.today())
        if category:
            query = query.where(Event.category == category.lower())
        events = _sorted(list(db.exec(query).all()))
    render_rows(
        [_row(e) for e in events],
        [("id", "ID"), ("event_date", "Date"), ("event_time", "Time"),
         ("title", "Event"), ("category", "Category"),
         ("when", "When"), ("location", "Location")],
        json_out=json_out,
        title="📅 Events" + (f" · {category}" if category else ""),
        empty="No events — add one with: clibo events add 'Dentist' -d 2026-06-01 -t 09:00",
    )


@app.command()
def today(json_out: JsonOpt = False) -> None:
    """📅 Show today's events."""
    with session() as db:
        events = _sorted(
            list(db.exec(select(Event).where(Event.event_date == date.today())).all())
        )
    if json_out:
        render_record({"date": date.today(), "events": [_row(e) for e in events]}, json_out=True)
        return
    if not events:
        console.print("\n  📅 [dim]Nothing on today.[/dim]\n")
        return
    console.print(f"\n📅 [bold]Today[/bold] · {date.today():%A %d %B}\n")
    for event in events:
        when = f"[cyan]{event.event_time}[/cyan]  " if event.event_time else "[dim]all day[/dim]  "
        loc = f"  [dim]@ {event.location}[/dim]" if event.location else ""
        console.print(f"  {when}{event.title}{loc}")
    console.print()


@app.command()
def upcoming(
    days: int = typer.Option(7, "--days", help="Look ahead this many days"),
    json_out: JsonOpt = False,
) -> None:
    """🔔 Events in the next N days."""
    horizon = date.today() + timedelta(days=days)
    with session() as db:
        events = _sorted(
            list(
                db.exec(
                    select(Event).where(
                        Event.event_date >= date.today(), Event.event_date <= horizon
                    )
                ).all()
            )
        )
    render_rows(
        [_row(e) for e in events],
        [("event_date", "Date"), ("event_time", "Time"), ("title", "Event"),
         ("when", "When"), ("location", "Location")],
        json_out=json_out,
        title=f"🔔 Next {days} days",
        empty="Nothing coming up.",
    )


@app.command()
def show(event_id: int = typer.Argument(..., help="Event ID"), json_out: JsonOpt = False) -> None:
    """📅 Show one event."""
    with session() as db:
        event = db.get(Event, event_id)
        if not event:
            fail(f"No event #{event_id}", json_out=json_out)
        data = _row(event)
    render_record(data, json_out=json_out, title=f"📅 {data['title']}")


@app.command()
def edit(
    event_id: int = typer.Argument(..., help="Event ID"),
    title: str = typer.Option(None, "--title", help="New title"),
    on: str = typer.Option(None, "--date", "-d", help="New date"),
    at: str = typer.Option(None, "--time", "-t", help="New time"),
    location: str = typer.Option(None, "--location", "-l", help="New location"),
    note: str = typer.Option(None, "--note", "-n", help="New note"),
    json_out: JsonOpt = False,
) -> None:
    """📅 Edit an event."""
    with session() as db:
        event = db.get(Event, event_id)
        if not event:
            fail(f"No event #{event_id}", json_out=json_out)
        if title is not None:
            event.title = title
        if on is not None:
            event.event_date = parse_date(on)
        if at is not None:
            event.event_time = at
        if location is not None:
            event.location = location
        if note is not None:
            event.note = note
        db.add(event)
        db.flush()
        data = _row(event)
    ok(f"Updated event #{event_id}", json_out=json_out, data=data)


@app.command()
def rm(event_id: int = typer.Argument(..., help="Event ID"), json_out: JsonOpt = False) -> None:
    """📅 Delete an event."""
    with session() as db:
        event = db.get(Event, event_id)
        if not event:
            fail(f"No event #{event_id}", json_out=json_out)
        db.delete(event)
    ok(f"Deleted event #{event_id}", json_out=json_out, data={"deleted": event_id})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Event stats."""
    with session() as db:
        events = list(db.exec(select(Event)).all())
    upcoming_events = [e for e in events if e.event_date >= date.today()]
    next_event = min(upcoming_events, key=lambda e: e.event_date, default=None)
    data = {
        "total_events": len(events),
        "upcoming": len(upcoming_events),
        "past": len(events) - len(upcoming_events),
        "next_event": _row(next_event)["title"] if next_event else None,
        "next_event_date": next_event.event_date if next_event else None,
    }
    render_record(data, json_out=json_out, title="📊 Event stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `update` is the SQL-natural synonym for `edit`; both work.
app.command(name="update", help="Alias for `edit`")(edit)

# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
