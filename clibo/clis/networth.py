"""💰 networth — assets, liabilities & net worth."""

from __future__ import annotations

from datetime import date, datetime

import typer
from sqlmodel import Field, SQLModel, select

from clibo.clis.expense import get_currency, money
from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, console, fail, ok, render_record, render_rows

NAME = "networth"
HELP = "💰 Assets, liabilities & net worth"
EMOJI = "💰"
KINDS = ["asset", "liability"]


class NetWorthItem(SQLModel, table=True):
    """One asset or liability that contributes to net worth."""

    __tablename__ = "networth_item"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    kind: str
    amount: float
    category: str = "other"
    note: str | None = None
    updated_at: datetime = Field(default_factory=datetime.now)
    created_at: datetime = Field(default_factory=datetime.now)


class NetWorthSnapshot(SQLModel, table=True):
    """A point-in-time record of net worth, for tracking change."""

    __tablename__ = "networth_snapshot"

    id: int | None = Field(default=None, primary_key=True)
    total_assets: float
    total_liabilities: float
    net_worth: float
    entry_date: date = Field(default_factory=date.today)
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context) -> None:
    """Default: ``clibo networth`` (bare) shows your net worth.

    The natural agent / human flow for *"what's my net worth?"* is to
    type ``clibo networth`` and get the answer, not a menu. Subcommands
    are still available — ``add``, ``list``, ``snapshot``, etc.
    """
    if ctx.invoked_subcommand is None:
        ctx.invoke(worth, json_out=False)


def _totals(db) -> tuple[float, float, float]:
    """Return (total assets, total liabilities, net worth)."""
    items = db.exec(select(NetWorthItem)).all()
    assets = round(sum(i.amount for i in items if i.kind == "asset"), 2)
    liabilities = round(sum(i.amount for i in items if i.kind == "liability"), 2)
    return assets, liabilities, round(assets - liabilities, 2)


def _row(item: NetWorthItem) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "kind": item.kind,
        "amount": item.amount,
        "category": item.category,
        "note": item.note,
    }


@app.command()
def add(
    name: str = typer.Argument(..., help="Item name, e.g. 'Savings account'"),
    amount: float = typer.Option(..., "--amount", "-a", help="Current value"),
    kind: str = typer.Option("asset", "--type", "-t", help="asset / liability"),
    category: str = typer.Option("other", "--category", "-c", help="Category, e.g. cash"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """💰 Add an asset or a liability."""
    kind = kind.lower()
    if kind not in KINDS:
        fail(f"Type must be one of: {', '.join(KINDS)}", json_out=json_out)
    if amount <= 0:
        fail("Amount must be positive", json_out=json_out)
    item = NetWorthItem(name=name, kind=kind, amount=amount, category=category.lower(), note=note)
    with session() as db:
        db.add(item)
        db.flush()
        db.refresh(item)
        data = _row(item)
    ok(f"Added {EMOJI} {kind} '{name}' — {money(amount)}", json_out=json_out, data=data)


@app.command(name="list")
def list_items(
    kind: str = typer.Option(None, "--type", "-t", help="Filter: asset / liability"),
    json_out: JsonOpt = False,
) -> None:
    """💰 List assets and liabilities."""
    if kind and kind.lower() not in KINDS:
        fail(f"Type must be one of: {', '.join(KINDS)}", json_out=json_out)
    with session() as db:
        query = select(NetWorthItem)
        if kind:
            query = query.where(NetWorthItem.kind == kind.lower())
        items = list(db.exec(query.order_by(NetWorthItem.kind, NetWorthItem.name)).all())
    render_rows(
        [_row(i) for i in items],
        [("id", "ID"), ("name", "Name"), ("kind", "Type"),
         ("amount", "Value"), ("category", "Category")],
        json_out=json_out,
        title="💰 Assets & liabilities",
        formatters={
            "amount": lambda v, r: money(v),
            "kind": lambda v, r: ("[green]asset[/green]" if v == "asset"
                                  else "[red]liability[/red]"),
        },
        empty="Nothing tracked yet — try: clibo networth add 'Cash' -a 5000",
    )


@app.command()
def update(
    item_id: int = typer.Argument(..., help="Item ID"),
    amount: float = typer.Argument(..., help="New current value"),
    json_out: JsonOpt = False,
) -> None:
    """💰 Update an item's current value."""
    if amount <= 0:
        fail("Amount must be positive", json_out=json_out)
    with session() as db:
        item = db.get(NetWorthItem, item_id)
        if not item:
            fail(f"No item #{item_id}", json_out=json_out)
        item.amount = amount
        item.updated_at = datetime.now()
        db.add(item)
        db.flush()
        data = _row(item)
    ok(f"Updated '{item.name}' to {money(amount)}", json_out=json_out, data=data)


@app.command()
def rm(item_id: int = typer.Argument(..., help="Item ID"), json_out: JsonOpt = False) -> None:
    """💰 Delete an asset or liability."""
    with session() as db:
        item = db.get(NetWorthItem, item_id)
        if not item:
            fail(f"No item #{item_id}", json_out=json_out)
        db.delete(item)
    ok(f"Deleted item #{item_id}", json_out=json_out, data={"deleted": item_id})


@app.command()
def worth(json_out: JsonOpt = False) -> None:
    """💰 Show your current net worth (also the default for bare ``clibo networth``)."""
    with session() as db:
        assets, liabilities, net = _totals(db)
        items = db.exec(select(NetWorthItem)).all()
    if json_out:
        render_record(
            {"total_assets": assets, "total_liabilities": liabilities,
             "net_worth": net, "items": len(items), "currency": get_currency()},
            json_out=True,
        )
        return
    console.print("\n💰 [bold]Net worth[/bold]\n")
    console.print(f"  [green]Assets[/green]        {money(assets):>16}")
    console.print(f"  [red]Liabilities[/red]   {money(liabilities):>16}")
    console.print("  " + "─" * 30)
    colour = "green" if net >= 0 else "red"
    console.print(f"  [bold]Net worth[/bold]     [bold {colour}]{money(net):>16}[/bold {colour}]\n")


# Friendlier alias: agents naturally reach for `show` across the codebase
# (films show, books show, crm show, …), so accept it here too.
app.command(name="show", help="Alias for `worth` — show your current net worth")(worth)


@app.command()
def snapshot(
    on: str = typer.Option("today", "--date", "-d", help="Snapshot date"),
    json_out: JsonOpt = False,
) -> None:
    """📸 Save a net-worth snapshot for history tracking."""
    with session() as db:
        assets, liabilities, net = _totals(db)
        snap = NetWorthSnapshot(
            total_assets=assets, total_liabilities=liabilities,
            net_worth=net, entry_date=parse_date(on),
        )
        db.add(snap)
        db.flush()
        db.refresh(snap)
        data = {"id": snap.id, "entry_date": snap.entry_date, "net_worth": net,
                "total_assets": assets, "total_liabilities": liabilities}
    ok(f"Snapshot saved {EMOJI} net worth {money(net)}", json_out=json_out, data=data)


@app.command()
def history(json_out: JsonOpt = False) -> None:
    """📊 Net-worth snapshots over time."""
    with session() as db:
        snaps = list(
            db.exec(
                select(NetWorthSnapshot).order_by(NetWorthSnapshot.entry_date.desc())
            ).all()
        )
    rows = [
        {"id": s.id, "entry_date": s.entry_date, "total_assets": s.total_assets,
         "total_liabilities": s.total_liabilities, "net_worth": s.net_worth}
        for s in snaps
    ]
    render_rows(
        rows,
        [("entry_date", "Date"), ("total_assets", "Assets"),
         ("total_liabilities", "Liabilities"), ("net_worth", "Net Worth")],
        json_out=json_out,
        title="📊 Net-worth history",
        formatters={
            "total_assets": lambda v, r: money(v),
            "total_liabilities": lambda v, r: money(v),
            "net_worth": lambda v, r: money(v),
        },
        empty="No snapshots yet — save one with: clibo networth snapshot",
    )
