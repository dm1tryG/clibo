"""🏠 home — home maintenance & repairs."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.clis.expense import get_currency, money
from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "home"
HELP = "🏠 Home maintenance & repairs"
EMOJI = "🏠"
KINDS = ["maintenance", "repair", "improvement"]


class HomeEntry(SQLModel, table=True):
    """A home maintenance, repair or improvement entry."""

    __tablename__ = "home_entry"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    kind: str = "maintenance"
    cost: float = 0.0
    location: str | None = None
    contractor: str | None = None
    entry_date: date = Field(default_factory=date.today, index=True)
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _row(entry: HomeEntry) -> dict:
    return {
        "id": entry.id,
        "entry_date": entry.entry_date,
        "title": entry.title,
        "kind": entry.kind,
        "cost": entry.cost,
        "location": entry.location,
        "contractor": entry.contractor,
        "note": entry.note,
    }


def _kind_cell(kind: str) -> str:
    return {
        "maintenance": "[cyan]maintenance[/cyan]",
        "repair": "[yellow]repair[/yellow]",
        "improvement": "[green]improvement[/green]",
    }.get(kind, kind)


@app.command()
def add(
    title: str = typer.Argument(..., help="What was done, e.g. 'Painted bedroom'"),
    kind: str = typer.Option("maintenance", "--kind", "-k", help=f"{' / '.join(KINDS)}"),
    cost: float = typer.Option(0, "--cost", "-c", help="Cost"),
    location: str = typer.Option(None, "--location", "-l", help="Room or area"),
    contractor: str = typer.Option(None, "--contractor", help="Who did the work"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🏠 Log a home maintenance, repair or improvement."""
    kind = kind.lower()
    if kind not in KINDS:
        fail(f"Kind must be one of: {', '.join(KINDS)}", json_out=json_out)
    if cost < 0:
        fail("Cost cannot be negative", json_out=json_out)
    entry = HomeEntry(
        title=title, kind=kind, cost=cost, location=location,
        contractor=contractor, entry_date=parse_date(on), note=note,
    )
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        data = _row(entry)
    detail = f" — {money(cost)}" if cost else ""
    ok(f"Logged {EMOJI} {title} ({kind}){detail}", json_out=json_out, data=data)


@app.command(name="list")
def list_entries(
    days: int = typer.Option(365, "--days", help="Look back this many days"),
    kind: str = typer.Option(None, "--kind", "-k", help="Filter by kind"),
    location: str = typer.Option(None, "--location", "-l", help="Filter by location"),
    json_out: JsonOpt = False,
) -> None:
    """🏠 List home entries."""
    if kind and kind.lower() not in KINDS:
        fail(f"Kind must be one of: {', '.join(KINDS)}", json_out=json_out)
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        query = select(HomeEntry).where(HomeEntry.entry_date >= since)
        if kind:
            query = query.where(HomeEntry.kind == kind.lower())
        if location:
            query = query.where(HomeEntry.location.ilike(f"%{location}%"))
        entries = list(
            db.exec(query.order_by(HomeEntry.entry_date.desc(), HomeEntry.id.desc())).all()
        )
    render_rows(
        [_row(e) for e in entries],
        [("id", "ID"), ("entry_date", "Date"), ("title", "Title"),
         ("kind", "Kind"), ("location", "Location"), ("cost", "Cost")],
        json_out=json_out,
        title="🏠 Home log",
        formatters={
            "kind": lambda v, r: _kind_cell(v),
            "cost": lambda v, r: money(v) if v else "[dim]—[/dim]",
        },
        empty="No home entries yet — try: clibo home add 'Painted bedroom' -k improvement",
    )


@app.command()
def show(entry_id: int = typer.Argument(..., help="Entry ID"), json_out: JsonOpt = False) -> None:
    """🏠 Show one home entry."""
    with session() as db:
        entry = db.get(HomeEntry, entry_id)
        if not entry:
            fail(f"No home entry #{entry_id}", json_out=json_out)
        data = _row(entry) | {"created_at": entry.created_at}
    render_record(data, json_out=json_out, title=f"🏠 {data['title']}")


@app.command()
def rm(entry_id: int = typer.Argument(..., help="Entry ID"), json_out: JsonOpt = False) -> None:
    """🏠 Delete a home entry."""
    with session() as db:
        entry = db.get(HomeEntry, entry_id)
        if not entry:
            fail(f"No home entry #{entry_id}", json_out=json_out)
        db.delete(entry)
    ok(f"Deleted home entry #{entry_id}", json_out=json_out, data={"deleted": entry_id})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Home-spending stats by kind and location."""
    with session() as db:
        entries = list(db.exec(select(HomeEntry)).all())
    by_kind = {k: round(sum(e.cost for e in entries if e.kind == k), 2) for k in KINDS}
    by_location: dict[str, float] = {}
    for entry in entries:
        if entry.location:
            by_location[entry.location] = round(
                by_location.get(entry.location, 0) + entry.cost, 2
            )
    data = {
        "total_entries": len(entries),
        "total_spent": round(sum(e.cost for e in entries), 2),
        "by_kind": by_kind,
        "by_location": by_location,
        "currency": get_currency(),
    }
    render_record(data, json_out=json_out, title="📊 Home stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)
