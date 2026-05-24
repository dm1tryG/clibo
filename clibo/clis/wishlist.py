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


def _resolve(db, ident: str) -> WishlistItem | None:
    """Resolve a CLI arg to a WishlistItem by ID or name (fuzzy)."""
    from clibo.core.base import lookup_by_id_or_name
    return lookup_by_id_or_name(db, WishlistItem, ident, WishlistItem.name)


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
def show(
    item: str = typer.Argument(..., help="Item ID or name (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """⭐ Show one wishlist item. Accepts a numeric ID or a name."""
    with session() as db:
        target = _resolve(db, item)
        if not target:
            fail(f"No wishlist item matching {item!r}", json_out=json_out)
        data = _row(target) | {"priority_stars": _stars(target.priority)}
    render_record(data, json_out=json_out, title=f"⭐ {data['name']}")


@app.command()
def edit(
    item: str = typer.Argument(..., help="Item ID or name (fuzzy)"),
    name: str = typer.Option(None, "--name", help="New name"),
    price: float = typer.Option(None, "--price", "-p"),
    priority: int = typer.Option(None, "--priority", "-P", help="1–5"),
    url: str = typer.Option(None, "--url", "-u"),
    category: str = typer.Option(None, "--category", "-c"),
    note: str = typer.Option(None, "--note", "-n"),
    json_out: JsonOpt = False,
) -> None:
    """⭐ Edit a wishlist item. Accepts a numeric ID or a name."""
    with session() as db:
        target = _resolve(db, item)
        if not target:
            fail(f"No wishlist item matching {item!r}", json_out=json_out)
        if name is not None:
            target.name = name
        if price is not None:
            if price < 0:
                fail("Price cannot be negative", json_out=json_out)
            target.price = price
        if priority is not None:
            if priority < 1 or priority > 5:
                fail("Priority must be 1–5", json_out=json_out)
            target.priority = priority
        if url is not None:
            target.url = url
        if category is not None:
            target.category = category.lower()
        if note is not None:
            target.note = note
        db.add(target)
        db.flush()
        data = _row(target)
    ok(f"Updated wishlist item #{target.id} — {target.name}",
       json_out=json_out, data=data)


@app.command()
def buy(
    item: str = typer.Argument(..., help="Item ID or name (fuzzy)"),
    on: str = typer.Option("today", "--date", "-d", help="Date purchased"),
    json_out: JsonOpt = False,
) -> None:
    """🛍️ Mark a wishlist item as purchased."""
    with session() as db:
        target = _resolve(db, item)
        if not target:
            fail(f"No wishlist item matching {item!r}", json_out=json_out)
        target.purchased = True
        target.purchased_date = parse_date(on)
        db.add(target)
        db.flush()
        data = _row(target)
    ok(f"Marked {EMOJI} {target.name} as purchased 🛍️",
       json_out=json_out, data=data)


@app.command()
def rm(
    item: str = typer.Argument(..., help="Item ID or name (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """⭐ Delete a wishlist item. Accepts a numeric ID or a name."""
    with session() as db:
        target = _resolve(db, item)
        if not target:
            fail(f"No wishlist item matching {item!r}", json_out=json_out)
        iid = target.id
        db.delete(target)
    ok(f"Deleted wishlist item #{iid}", json_out=json_out, data={"deleted": iid})


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

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `update` is the SQL-natural synonym for `edit`; both work.
app.command(name="update", help="Alias for `edit`")(edit)

# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
