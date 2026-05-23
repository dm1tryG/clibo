"""💸 expense — personal expense tracker."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, bar, console, fail, ok, render_record, render_rows
from clibo.core.settings import get_setting, set_setting

NAME = "expense"
HELP = "💸 Personal expense tracker"
EMOJI = "💸"


class Expense(SQLModel, table=True):
    """A single recorded expense."""

    __tablename__ = "expense_entry"

    id: int | None = Field(default=None, primary_key=True)
    amount: float
    description: str
    category: str = "other"
    entry_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    note: str | None = None


app = typer.Typer(no_args_is_help=True, help=HELP)


def get_currency() -> str:
    """The shared money currency code (used by all 💰 tools)."""
    return get_setting("money", "currency", "USD") or "USD"


def money(amount: float) -> str:
    """Format an amount with the active currency code."""
    return f"{amount:.2f} {get_currency()}"


def _row(entry: Expense) -> dict:
    return {
        "id": entry.id,
        "entry_date": entry.entry_date,
        "amount": entry.amount,
        "description": entry.description,
        "category": entry.category,
        "note": entry.note,
    }


def _month_range(spec: str | None) -> tuple[date, date, str]:
    """Resolve a ``YYYY-MM`` spec (or None = current month) to a date range."""
    if spec:
        try:
            anchor = datetime.strptime(spec, "%Y-%m").date()
        except ValueError as exc:
            raise typer.BadParameter("Month must be YYYY-MM") from exc
    else:
        anchor = date.today()
    first = anchor.replace(day=1)
    nxt = (first.replace(year=first.year + 1, month=1) if first.month == 12
           else first.replace(month=first.month + 1))
    return first, nxt, first.strftime("%Y-%m")


@app.command()
def add(
    description: str = typer.Argument(..., help="What you spent on, e.g. 'lunch'"),
    amount: float = typer.Option(..., "--amount", "-a", help="Amount spent"),
    category: str = typer.Option("other", "--category", "-c", help="Category, e.g. food"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """💸 Record an expense."""
    if amount <= 0:
        fail("Amount must be positive", json_out=json_out)
    entry = Expense(
        amount=amount, description=description, category=category.lower(),
        entry_date=parse_date(on), note=note,
    )
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        data = _row(entry)
    ok(f"Logged {EMOJI} {money(amount)} — {description} ({category})",
       json_out=json_out, data=data)


@app.command(name="list")
def list_entries(
    days: int = typer.Option(30, "--days", help="Look back this many days"),
    category: str = typer.Option(None, "--category", "-c", help="Filter by category"),
    json_out: JsonOpt = False,
) -> None:
    """💸 List recent expenses."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        query = select(Expense).where(Expense.entry_date >= since)
        if category:
            query = query.where(Expense.category == category.lower())
        entries = list(
            db.exec(query.order_by(Expense.entry_date.desc(), Expense.id.desc())).all()
        )
    render_rows(
        [_row(e) for e in entries],
        [("id", "ID"), ("entry_date", "Date"), ("amount", "Amount"),
         ("description", "Description"), ("category", "Category")],
        json_out=json_out,
        title="💸 Expenses",
        formatters={"amount": lambda v, r: money(v)},
        empty="No expenses yet — try: clibo expense add 'coffee' -a 4.50 -c food",
    )


@app.command()
def month(
    month_spec: str = typer.Option(None, "--month", "-m", help="YYYY-MM (default: this month)"),
    json_out: JsonOpt = False,
) -> None:
    """📅 This month's spending, broken down by category."""
    first, nxt, label = _month_range(month_spec)
    with session() as db:
        entries = list(
            db.exec(
                select(Expense).where(Expense.entry_date >= first, Expense.entry_date < nxt)
            ).all()
        )
    total = round(sum(e.amount for e in entries), 2)
    by_cat: dict[str, float] = {}
    for entry in entries:
        by_cat[entry.category] = round(by_cat.get(entry.category, 0) + entry.amount, 2)
    rows = [
        {"category": cat, "amount": amt,
         "share": round(amt / total * 100, 1) if total else 0.0}
        for cat, amt in sorted(by_cat.items(), key=lambda kv: kv[1], reverse=True)
    ]
    if json_out:
        render_record(
            {"month": label, "total": total, "expenses": len(entries),
             "by_category": rows, "currency": get_currency()},
            json_out=True,
        )
        return
    render_rows(
        rows,
        [("category", "Category"), ("amount", "Amount"), ("share", "Share")],
        json_out=False,
        title=f"💸 Spending · {label}",
        formatters={
            "amount": lambda v, r: money(v),
            "share": lambda v, r: bar(v, 100),
        },
        empty=f"No expenses in {label}.",
    )
    if rows:
        console.print(f"  💰 [bold]Total:[/bold] {money(total)}   ·   {len(entries)} expenses")


@app.command()
def show(entry_id: int = typer.Argument(..., help="Expense ID"), json_out: JsonOpt = False) -> None:
    """💸 Show one expense in detail."""
    with session() as db:
        entry = db.get(Expense, entry_id)
        if not entry:
            fail(f"No expense #{entry_id}", json_out=json_out)
        data = _row(entry) | {"created_at": entry.created_at}
    render_record(data, json_out=json_out, title=f"💸 Expense #{entry_id}")


@app.command()
def edit(
    entry_id: int = typer.Argument(..., help="Expense ID"),
    amount: float = typer.Option(None, "--amount", "-a"),
    description: str = typer.Option(None, "--description"),
    category: str = typer.Option(None, "--category", "-c"),
    note: str = typer.Option(None, "--note", "-n"),
    json_out: JsonOpt = False,
) -> None:
    """💸 Edit an expense."""
    with session() as db:
        entry = db.get(Expense, entry_id)
        if not entry:
            fail(f"No expense #{entry_id}", json_out=json_out)
        for field, value in {"amount": amount, "description": description,
                             "category": category, "note": note}.items():
            if value is not None:
                setattr(entry, field, value.lower() if field == "category" else value)
        db.add(entry)
        db.flush()
        data = _row(entry)
    ok(f"Updated expense #{entry_id}", json_out=json_out, data=data)


@app.command()
def rm(entry_id: int = typer.Argument(..., help="Expense ID"), json_out: JsonOpt = False) -> None:
    """💸 Delete an expense."""
    with session() as db:
        entry = db.get(Expense, entry_id)
        if not entry:
            fail(f"No expense #{entry_id}", json_out=json_out)
        db.delete(entry)
    ok(f"Deleted expense #{entry_id}", json_out=json_out, data={"deleted": entry_id})


@app.command()
def currency(
    set_code: str = typer.Option(None, "--set", help="Set the currency code, e.g. EUR"),
    json_out: JsonOpt = False,
) -> None:
    """💱 Show or set the currency used across all money tools."""
    if set_code:
        set_setting("money", "currency", set_code.upper())
        ok(f"Currency set to {set_code.upper()}", json_out=json_out,
           data={"currency": set_code.upper()})
        return
    render_record({"currency": get_currency()}, json_out=json_out, title="💱 Currency")


@app.command()
def stats(
    days: int = typer.Option(30, "--days", help="Window size in days"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Expense stats over the last N days."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        entries = list(db.exec(select(Expense).where(Expense.entry_date >= since)).all())
    if not entries:
        fail("No expenses in this window", json_out=json_out)
    total = round(sum(e.amount for e in entries), 2)
    by_cat: dict[str, float] = {}
    for entry in entries:
        by_cat[entry.category] = round(by_cat.get(entry.category, 0) + entry.amount, 2)
    top = sorted(by_cat.items(), key=lambda kv: kv[1], reverse=True)[:5]
    from clibo.core.sparkline import sparkline_days
    by_day: dict[date, float] = {}
    for entry in entries:
        by_day[entry.entry_date] = round(
            by_day.get(entry.entry_date, 0) + entry.amount, 2
        )
    data = {
        "window_days": days,
        "expenses": len(entries),
        "total": total,
        "avg_per_day": round(total / days, 2),
        "biggest": max(e.amount for e in entries),
        "top_categories": [{"category": c, "amount": a} for c, a in top],
        "currency": get_currency(),
        "chart": sparkline_days(by_day, since, date.today()),
    }
    render_record(data, json_out=json_out, title=f"📊 Expense stats · last {days}d")
