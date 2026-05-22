"""🛒 groceries — grocery & shopping list."""

from __future__ import annotations

from datetime import datetime

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "groceries"
HELP = "🛒 Grocery & shopping list"
EMOJI = "🛒"


class GroceryItem(SQLModel, table=True):
    """One item on the shopping list."""

    __tablename__ = "groceries_item"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    quantity: str | None = None
    category: str = "other"
    bought: bool = False
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _row(item: GroceryItem) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "quantity": item.quantity,
        "category": item.category,
        "bought": item.bought,
    }


@app.command()
def add(
    name: str = typer.Argument(..., help="Item to buy"),
    quantity: str = typer.Option(None, "--quantity", "-q", help="How much, e.g. '2 kg'"),
    category: str = typer.Option("other", "--category", "-c", help="Aisle / category"),
    json_out: JsonOpt = False,
) -> None:
    """🛒 Add an item to the shopping list."""
    item = GroceryItem(name=name, quantity=quantity, category=category.lower())
    with session() as db:
        db.add(item)
        db.flush()
        db.refresh(item)
        data = _row(item)
    qty = f" ({quantity})" if quantity else ""
    ok(f"Added {EMOJI} {name}{qty}", json_out=json_out, data=data)


@app.command(name="list")
def list_items(
    show_all: bool = typer.Option(False, "--all", help="Include bought items"),
    json_out: JsonOpt = False,
) -> None:
    """🛒 Show the shopping list."""
    with session() as db:
        query = select(GroceryItem)
        if not show_all:
            query = query.where(GroceryItem.bought == False)  # noqa: E712
        items = list(db.exec(query.order_by(GroceryItem.category, GroceryItem.id)).all())
    render_rows(
        [_row(i) for i in items],
        [("id", "ID"), ("bought", "✓"), ("name", "Item"),
         ("quantity", "Qty"), ("category", "Category")],
        json_out=json_out,
        title="🛒 Shopping list",
        formatters={"bought": lambda v, r: "[green]✓[/green]" if v else "[dim]·[/dim]"},
        empty="Shopping list is empty — try: clibo groceries add milk -q '2 L'",
    )


@app.command()
def buy(item_id: int = typer.Argument(..., help="Item ID"), json_out: JsonOpt = False) -> None:
    """🛒 Mark an item as bought."""
    _set_bought(item_id, True, json_out)


@app.command()
def unbuy(item_id: int = typer.Argument(..., help="Item ID"), json_out: JsonOpt = False) -> None:
    """🛒 Put a bought item back on the list."""
    _set_bought(item_id, False, json_out)


def _set_bought(item_id: int, bought: bool, json_out: bool) -> None:
    with session() as db:
        item = db.get(GroceryItem, item_id)
        if not item:
            fail(f"No grocery item #{item_id}", json_out=json_out)
        item.bought = bought
        db.add(item)
        db.flush()
        data = _row(item)
    verb = "Bought" if bought else "Restored"
    ok(f"{verb} {item.name}", json_out=json_out, data=data)


@app.command()
def rm(item_id: int = typer.Argument(..., help="Item ID"), json_out: JsonOpt = False) -> None:
    """🛒 Delete an item from the list."""
    with session() as db:
        item = db.get(GroceryItem, item_id)
        if not item:
            fail(f"No grocery item #{item_id}", json_out=json_out)
        db.delete(item)
    ok(f"Deleted grocery item #{item_id}", json_out=json_out, data={"deleted": item_id})


@app.command()
def clear(json_out: JsonOpt = False) -> None:
    """🧹 Remove all bought items from the list."""
    with session() as db:
        bought = list(
            db.exec(select(GroceryItem).where(GroceryItem.bought == True)).all()  # noqa: E712
        )
        for item in bought:
            db.delete(item)
    ok(f"Cleared {len(bought)} bought item(s)", json_out=json_out,
       data={"cleared": len(bought)})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Shopping-list stats."""
    with session() as db:
        items = list(db.exec(select(GroceryItem)).all())
    data = {
        "total": len(items),
        "pending": sum(1 for i in items if not i.bought),
        "bought": sum(1 for i in items if i.bought),
        "categories": len({i.category for i in items}),
    }
    render_record(data, json_out=json_out, title="📊 Groceries stats")
