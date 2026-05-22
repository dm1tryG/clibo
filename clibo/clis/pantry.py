"""🥫 pantry — food inventory with expiry dates."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import humanize_delta, parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "pantry"
HELP = "🥫 Food inventory with expiry dates"
EMOJI = "🥫"


class PantryItem(SQLModel, table=True):
    """A food item in the pantry, fridge or freezer."""

    __tablename__ = "pantry_item"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    quantity: str | None = None
    category: str = "other"
    location: str = "pantry"
    expiry: date | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _status(item: PantryItem) -> str:
    """One of: fresh, expiring, expired, or none (no expiry set)."""
    if item.expiry is None:
        return "none"
    days = (item.expiry - date.today()).days
    if days < 0:
        return "expired"
    if days <= 3:
        return "expiring"
    return "fresh"


def _row(item: PantryItem) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "quantity": item.quantity,
        "category": item.category,
        "location": item.location,
        "expiry": item.expiry,
        "expiry_in": humanize_delta(item.expiry) if item.expiry else None,
        "status": _status(item),
    }


def _status_cell(status: str) -> str:
    return {
        "fresh": "[green]fresh[/green]",
        "expiring": "[yellow]⏰ expiring[/yellow]",
        "expired": "[red]⚠ expired[/red]",
        "none": "[dim]—[/dim]",
    }.get(status, status)


@app.command()
def add(
    name: str = typer.Argument(..., help="Food item name"),
    quantity: str = typer.Option(None, "--quantity", "-q", help="How much"),
    expiry: str = typer.Option(None, "--expiry", "-e", help="Expiry date"),
    location: str = typer.Option("pantry", "--location", "-l", help="pantry/fridge/freezer"),
    category: str = typer.Option("other", "--category", "-c", help="Category"),
    json_out: JsonOpt = False,
) -> None:
    """🥫 Add an item to the pantry."""
    item = PantryItem(
        name=name, quantity=quantity, category=category.lower(),
        location=location.lower(), expiry=parse_date(expiry) if expiry else None,
    )
    with session() as db:
        db.add(item)
        db.flush()
        db.refresh(item)
        data = _row(item)
    ok(f"Added {EMOJI} {name} to {item.location}", json_out=json_out, data=data)


@app.command(name="list")
def list_items(
    location: str = typer.Option(None, "--location", "-l", help="Filter by location"),
    json_out: JsonOpt = False,
) -> None:
    """🥫 List pantry items."""
    with session() as db:
        query = select(PantryItem)
        if location:
            query = query.where(PantryItem.location == location.lower())
        items = list(db.exec(query.order_by(PantryItem.location, PantryItem.name)).all())
    render_rows(
        [_row(i) for i in items],
        [("id", "ID"), ("name", "Item"), ("quantity", "Qty"),
         ("location", "Location"), ("expiry", "Expires"), ("status", "Status")],
        json_out=json_out,
        title="🥫 Pantry",
        formatters={"status": lambda v, r: _status_cell(v)},
        empty="Pantry is empty — try: clibo pantry add 'olive oil' -l pantry",
    )


@app.command()
def expiring(
    days: int = typer.Option(7, "--days", help="Flag items expiring within N days"),
    json_out: JsonOpt = False,
) -> None:
    """⏰ Items that are expired or expiring soon."""
    horizon = date.today() + timedelta(days=days)
    with session() as db:
        items = list(
            db.exec(
                select(PantryItem)
                .where(PantryItem.expiry != None)  # noqa: E711
                .where(PantryItem.expiry <= horizon)
                .order_by(PantryItem.expiry)
            ).all()
        )
    render_rows(
        [_row(i) for i in items],
        [("id", "ID"), ("name", "Item"), ("location", "Location"),
         ("expiry", "Expires"), ("expiry_in", "When"), ("status", "Status")],
        json_out=json_out,
        title=f"⏰ Expiring within {days} days",
        formatters={"status": lambda v, r: _status_cell(v)},
        empty="Nothing expiring soon — your pantry is in good shape! ✨",
    )


@app.command()
def show(item_id: int = typer.Argument(..., help="Item ID"), json_out: JsonOpt = False) -> None:
    """🥫 Show one pantry item."""
    with session() as db:
        item = db.get(PantryItem, item_id)
        if not item:
            fail(f"No pantry item #{item_id}", json_out=json_out)
        data = _row(item)
    render_record(data, json_out=json_out, title=f"🥫 {data['name']}")


@app.command()
def rm(item_id: int = typer.Argument(..., help="Item ID"), json_out: JsonOpt = False) -> None:
    """🥫 Remove an item from the pantry (used up or discarded)."""
    with session() as db:
        item = db.get(PantryItem, item_id)
        if not item:
            fail(f"No pantry item #{item_id}", json_out=json_out)
        db.delete(item)
    ok(f"Removed pantry item #{item_id}", json_out=json_out, data={"deleted": item_id})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Pantry stats."""
    with session() as db:
        items = list(db.exec(select(PantryItem)).all())
    statuses = [_status(i) for i in items]
    by_location: dict[str, int] = {}
    for item in items:
        by_location[item.location] = by_location.get(item.location, 0) + 1
    data = {
        "total": len(items),
        "expired": statuses.count("expired"),
        "expiring_soon": statuses.count("expiring"),
        "by_location": by_location,
    }
    render_record(data, json_out=json_out, title="📊 Pantry stats")
