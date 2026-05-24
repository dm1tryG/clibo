"""✈️ travel — trip planner & itinerary."""

from __future__ import annotations

from datetime import date, datetime

import typer
from sqlmodel import Field, SQLModel, select

from clibo.clis.expense import get_currency, money
from clibo.core.base import humanize_delta, parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, console, fail, ok, render_record, render_rows

NAME = "travel"
HELP = "✈️ Trip planner & itinerary"
EMOJI = "✈️"

CATEGORY_ICON = {
    "flight": "✈️",
    "hotel": "🏨",
    "activity": "🎟️",
    "food": "🍽️",
    "transport": "🚆",
    "note": "📝",
}


class Trip(SQLModel, table=True):
    """A planned or past trip."""

    __tablename__ = "travel_trip"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    destination: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget: float = 0.0
    notes: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


class TripEvent(SQLModel, table=True):
    """An itinerary item for a trip."""

    __tablename__ = "travel_event"

    id: int | None = Field(default=None, primary_key=True)
    trip_id: int = Field(index=True)
    event_date: date
    event_time: str | None = None
    title: str
    location: str | None = None
    category: str = "activity"
    cost: float = 0.0
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _resolve(db, ident: str) -> Trip | None:
    """Look up a trip by numeric ID or by (case-insensitive) name."""
    if ident.isdigit():
        trip = db.get(Trip, int(ident))
        if trip:
            return trip
    return db.exec(select(Trip).where(Trip.name.ilike(ident))).first()


def _trip_spent(db, trip_id: int) -> float:
    rows = db.exec(select(TripEvent).where(TripEvent.trip_id == trip_id)).all()
    return round(sum(r.cost for r in rows), 2)


def _trip_status(start: date | None, end: date | None) -> str:
    """Classify a trip's temporal status: ``upcoming`` / ``ongoing`` / ``ended`` / ``undated``."""
    if start is None:
        return "undated"
    today = date.today()
    if today < start:
        return "upcoming"
    if end is None:
        # No end set — call it ongoing on the start day, ended after.
        return "ongoing" if today == start else "ended"
    if today <= end:
        return "ongoing"
    return "ended"


def _trip_when(start: date | None, end: date | None) -> str | None:
    """Human-readable temporal label that matches the trip's status.

    Picks the right preposition / tense based on whether the trip is
    upcoming, ongoing, or already ended. ``starts_in`` (kept for back-
    compat) was always just ``humanize_delta(start_date)``, which read
    wrong for past trips — "starts_in: 3d ago" is contradictory.
    """
    if start is None:
        return None
    today = date.today()
    if today < start:
        # humanize_delta already returns "in 3d" / "tomorrow" / "next week".
        return humanize_delta(start)
    if end is None:
        if today == start:
            return "today"
        return f"ended {humanize_delta(start)}"
    if today <= end:
        day = (today - start).days + 1
        total = (end - start).days + 1
        return f"ongoing · day {day} of {total}"
    return f"ended {humanize_delta(end)}"


def _row(db, trip: Trip) -> dict:
    spent = _trip_spent(db, trip.id)
    return {
        "id": trip.id,
        "name": trip.name,
        "destination": trip.destination,
        "start_date": trip.start_date,
        "end_date": trip.end_date,
        "status": _trip_status(trip.start_date, trip.end_date),
        "when": _trip_when(trip.start_date, trip.end_date),
        # Kept for backward-compat with consumers reading v1.10.0 JSON shape.
        "starts_in": humanize_delta(trip.start_date) if trip.start_date else None,
        "budget": trip.budget,
        "spent": spent,
        "remaining": round(trip.budget - spent, 2) if trip.budget else None,
        "notes": trip.notes,
    }


@app.command()
def add(
    name: str = typer.Argument(..., help="Trip name"),
    destination: str = typer.Option(None, "--destination", "-d", help="Where to"),
    start: str = typer.Option(None, "--start", help="Start date"),
    end: str = typer.Option(None, "--end", help="End date"),
    budget: float = typer.Option(0, "--budget", "-b", help="Trip budget"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """✈️ Add a trip."""
    if budget < 0:
        fail("Budget cannot be negative", json_out=json_out)
    trip = Trip(
        name=name, destination=destination,
        start_date=parse_date(start) if start else None,
        end_date=parse_date(end) if end else None,
        budget=budget, notes=note,
    )
    with session() as db:
        db.add(trip)
        db.flush()
        db.refresh(trip)
        data = _row(db, trip)
    ok(f"Added {EMOJI} trip '{name}'" + (f" to {destination}" if destination else ""),
       json_out=json_out, data=data)


@app.command(name="list")
def list_trips(
    show_all: bool = typer.Option(False, "--all", help="Include past trips"),
    json_out: JsonOpt = False,
) -> None:
    """✈️ List trips."""
    with session() as db:
        query = select(Trip)
        if not show_all:
            query = query.where(
                (Trip.start_date == None) | (Trip.start_date >= date.today())  # noqa: E711
            )
        trips = list(db.exec(query.order_by(Trip.start_date)).all())
        rows = [_row(db, t) for t in trips]
    render_rows(
        rows,
        [("id", "ID"), ("name", "Trip"), ("destination", "Destination"),
         ("start_date", "Start"), ("end_date", "End"), ("when", "When"),
         ("budget", "Budget"), ("spent", "Spent")],
        json_out=json_out,
        title="✈️ Trips",
        formatters={
            "budget": lambda v, r: money(v) if v else "[dim]—[/dim]",
            "spent": lambda v, r: money(v) if v else "[dim]—[/dim]",
        },
        empty="No trips yet — try: clibo travel add 'Paris weekend' -d Paris --start 2026-08-10",
    )


@app.command()
def show(
    trip: str = typer.Argument(..., help="Trip name or ID"),
    json_out: JsonOpt = False,
) -> None:
    """✈️ Show a trip's full itinerary."""
    with session() as db:
        target = _resolve(db, trip)
        if not target:
            fail(f"No trip matching {trip!r}", json_out=json_out)
        data = _row(db, target)
        events = [
            {"id": e.id, "event_date": e.event_date, "event_time": e.event_time,
             "title": e.title, "category": e.category, "location": e.location,
             "cost": e.cost}
            for e in db.exec(
                select(TripEvent)
                .where(TripEvent.trip_id == target.id)
                .order_by(TripEvent.event_date, TripEvent.event_time, TripEvent.id)
            ).all()
        ]
    if json_out:
        render_record(data | {"itinerary": events}, json_out=True)
        return
    render_record(data, json_out=False, title=f"✈️ {target.name}")
    by_day: dict[date, list[dict]] = {}
    for event in events:
        by_day.setdefault(event["event_date"], []).append(event)
    if not by_day:
        console.print(
            "  [dim]No itinerary yet — add with: clibo travel plan <trip> DATE TITLE[/dim]\n"
        )
        return
    for day, items in sorted(by_day.items()):
        console.print(f"\n[bold cyan]{day:%A %d %B}[/bold cyan]")
        for item in items:
            icon = CATEGORY_ICON.get(item["category"], "•")
            t = f"[cyan]{item['event_time']}[/cyan]  " if item["event_time"] else ""
            loc = f"  [dim]@ {item['location']}[/dim]" if item["location"] else ""
            cost = f"  [dim]({money(item['cost'])})[/dim]" if item["cost"] else ""
            console.print(f"  {icon} {t}{item['title']}{loc}{cost}")
    console.print()


@app.command()
def plan(
    trip: str = typer.Argument(..., help="Trip name or ID"),
    on: str = typer.Argument(..., help="Date"),
    title: str = typer.Argument(..., help="What's on"),
    time: str = typer.Option(None, "--time", "-t", help="Time, e.g. 14:30"),
    location: str = typer.Option(None, "--location", "-l", help="Where"),
    category: str = typer.Option("activity", "--category", "-c",
                                 help=f"{' / '.join(CATEGORY_ICON)}"),
    cost: float = typer.Option(0, "--cost", help="Cost"),
    json_out: JsonOpt = False,
) -> None:
    """✈️ Add an itinerary item to a trip."""
    if cost < 0:
        fail("Cost cannot be negative", json_out=json_out)
    with session() as db:
        target = _resolve(db, trip)
        if not target:
            fail(f"No trip matching {trip!r}", json_out=json_out)
        event = TripEvent(
            trip_id=target.id, event_date=parse_date(on), event_time=time,
            title=title, location=location, category=category.lower(), cost=cost,
        )
        db.add(event)
        db.flush()
        db.refresh(event)
        data = {"id": event.id, "trip": target.name, "event_date": event.event_date,
                "event_time": event.event_time, "title": title,
                "category": event.category, "cost": cost}
    ok(f"Planned {EMOJI} {target.name}: {title} on {event.event_date}",
       json_out=json_out, data=data)


@app.command()
def upcoming(json_out: JsonOpt = False) -> None:
    """🔔 Upcoming trips."""
    with session() as db:
        trips = list(
            db.exec(
                select(Trip)
                .where(Trip.start_date != None)  # noqa: E711
                .where(Trip.start_date >= date.today())
                .order_by(Trip.start_date)
            ).all()
        )
        rows = [_row(db, t) for t in trips]
    render_rows(
        rows,
        [("name", "Trip"), ("destination", "Destination"),
         ("start_date", "Starts"), ("when", "When")],
        json_out=json_out,
        title="🔔 Upcoming trips",
        empty="No upcoming trips planned.",
    )


@app.command()
def rm(trip_id: int = typer.Argument(..., help="Trip ID"), json_out: JsonOpt = False) -> None:
    """✈️ Delete a trip and its itinerary."""
    with session() as db:
        trip = db.get(Trip, trip_id)
        if not trip:
            fail(f"No trip #{trip_id}", json_out=json_out)
        for event in db.exec(select(TripEvent).where(TripEvent.trip_id == trip_id)).all():
            db.delete(event)
        db.delete(trip)
    ok(f"Deleted trip #{trip_id}", json_out=json_out, data={"deleted": trip_id})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Travel stats — trips, days and spending."""
    with session() as db:
        trips = list(db.exec(select(Trip)).all())
        events = list(db.exec(select(TripEvent)).all())
    spent = round(sum(e.cost for e in events), 2)
    upcoming_trips = [t for t in trips if t.start_date and t.start_date >= date.today()]
    days = 0
    for trip in trips:
        if trip.start_date and trip.end_date:
            days += (trip.end_date - trip.start_date).days + 1
    data = {
        "trips": len(trips),
        "upcoming": len(upcoming_trips),
        "itinerary_items": len(events),
        "days_traveled": days,
        "spent": spent,
        "currency": get_currency(),
    }
    render_record(data, json_out=json_out, title="📊 Travel stats")
