"""⭐ wishlist — things-to-buy wishlist with prices."""

from __future__ import annotations

from datetime import date, datetime

import typer
from sqlmodel import Field, SQLModel, select

from clibo.clis.expense import get_currency, money
from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "wishlist"
HELP = "⭐ Things-to-buy wishlist with prices"
EMOJI = "⭐"


class WishlistItem(SQLModel, table=True):
    """Something the user wants to buy one day."""

    __tablename__ = "wishlist_item"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    price: float = 0.0
    priority: int = 3
    url: str | None = None
    category: str = "other"
    purchased: bool = False
    purchased_date: date | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _stars(priority: int) -> str:
    """Render a 1–5 priority as filled/empty stars."""
    return "★" * priority + "☆" * (5 - priority)


def _row(item: WishlistItem) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "price": item.price,
        "priority": item.priority,
        "url": item.url,
        "category": item.category,
        "purchased": item.purchased,
        "purchased_date": item.purchased_date,
        "note": item.note,
    }


@app.command()
def add(
    name: str = typer.Argument(..., help="What you want, e.g. 'Standing desk'"),
    price: float = typer.Option(0, "--price", "-p", help="Estimated price"),
    priority: int = typer.Option(3, "--priority", "-P", help="Priority, 1 (low) – 5 (high)"),
    url: str = typer.Option(None, "--url", "-u", help="Link to the item"),
    category: str = typer.Option("other", "--category", "-c", help="Category"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """⭐ Add an item to your wishlist."""
    if priority < 1 or priority > 5:
        fail("Priority must be 1–5", json_out=json_out)
    if price < 0:
        fail("Price cannot be negative", json_out=json_out)
    item = WishlistItem(
        name=name, price=price, priority=priority, url=url, category=category.lower(), note=note,
    )
    with session() as db:
        db.add(item)
        db.flush()
        db.refresh(item)
        data = _row(item)
    suffix = f" — {money(price)}" if price else ""
    ok(f"Added {EMOJI} {name}{suffix}", json_out=json_out, data=data)


@app.command(name="list")
def list_items(
    show_all: bool = typer.Option(False, "--all", help="Include purchased items"),
    category: str = typer.Option(None, "--category", "-c", help="Filter by category"),
    json_out: JsonOpt = False,
) -> None:
    """⭐ List wishlist items, highest priority first."""
    with session() as db:
        query = select(WishlistItem)
        if not show_all:
            query = query.where(WishlistItem.purchased == False)  # noqa: E712
        if category:
            query = query.where(WishlistItem.category == category.lower())
        items = list(
            db.exec(query.order_by(WishlistItem.priority.desc(), WishlistItem.price.desc())).all()
        )
    render_rows(
        [_row(i) for i in items],
        [("id", "ID"), ("name", "Item"), ("price", "Price"),
         ("priority", "Priority"), ("category", "Category"), ("purchased", "Bought")],
        json_out=json_out,
        title="⭐ Wishlist",
        formatters={
            "price": lambda v, r: money(v) if v else "[dim]—[/dim]",
            "priority": lambda v, r: f"[yellow]{_stars(v)}[/yellow]",
        },
        empty="Wishlist is empty — try: clibo wishlist add 'Standing desk' -p 350 -P 4",
    )


@app.command()
def show(item_id: int = typer.Argument(..., help="Item ID"), json_out: JsonOpt = False) -> None:
    """⭐ Show one wishlist item."""
    with session() as db:
        item = db.get(WishlistItem, item_id)
        if not item:
            fail(f"No wishlist item #{item_id}", json_out=json_out)
        data = _row(item) | {"priority_stars": _stars(item.priority)}
    render_record(data, json_out=json_out, title=f"⭐ {data['name']}")


@app.command()
def buy(
    item_id: int = typer.Argument(..., help="Item ID"),
    on: str = typer.Option("today", "--date", "-d", help="Date purchased"),
    json_out: JsonOpt = False,
) -> None:
    """🛍️ Mark a wishlist item as purchased."""
    with session() as db:
        item = db.get(WishlistItem, item_id)
        if not item:
            fail(f"No wishlist item #{item_id}", json_out=json_out)
        item.purchased = True
        item.purchased_date = parse_date(on)
        db.add(item)
        db.flush()
        data = _row(item)
    ok(f"Marked {EMOJI} {item.name} as purchased 🛍️", json_out=json_out, data=data)


@app.command()
def rm(item_id: int = typer.Argument(..., help="Item ID"), json_out: JsonOpt = False) -> None:
    """⭐ Delete a wishlist item."""
    with session() as db:
        item = db.get(WishlistItem, item_id)
        if not item:
            fail(f"No wishlist item #{item_id}", json_out=json_out)
        db.delete(item)
    ok(f"Deleted wishlist item #{item_id}", json_out=json_out, data={"deleted": item_id})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Wishlist stats — total cost and breakdown."""
    with session() as db:
        items = list(db.exec(select(WishlistItem)).all())
    if not items:
        fail("Wishlist is empty", json_out=json_out)
    pending = [i for i in items if not i.purchased]
    by_priority: dict[int, int] = {}
    for item in pending:
        by_priority[item.priority] = by_priority.get(item.priority, 0) + 1
    data = {
        "total_items": len(items),
        "pending": len(pending),
        "purchased": sum(1 for i in items if i.purchased),
        "pending_cost": round(sum(i.price for i in pending), 2),
        "by_priority": {f"{p}★": by_priority[p] for p in sorted(by_priority, reverse=True)},
        "currency": get_currency(),
    }
    render_record(data, json_out=json_out, title="📊 Wishlist stats")
