"""🧾 bills — bills & due-date reminders."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.clis.expense import get_currency, money
from clibo.core.base import humanize_delta, parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, console, fail, ok, render_record, render_rows

NAME = "bills"
HELP = "🧾 Bills & due-date reminders"
EMOJI = "🧾"


class Bill(SQLModel, table=True):
    """A bill with a due date that can be marked paid."""

    __tablename__ = "bills_bill"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    amount: float = 0.0
    due_date: date = Field(index=True)
    category: str = "other"
    paid: bool = False
    paid_date: date | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _status(bill: Bill) -> str:
    """One of: paid, overdue, due soon, upcoming."""
    if bill.paid:
        return "paid"
    days = (bill.due_date - date.today()).days
    if days < 0:
        return "overdue"
    if days <= 3:
        return "due soon"
    return "upcoming"


def _row(bill: Bill) -> dict:
    return {
        "id": bill.id,
        "name": bill.name,
        "amount": bill.amount,
        "due_date": bill.due_date,
        "category": bill.category,
        "paid": bill.paid,
        "paid_date": bill.paid_date,
        "status": _status(bill),
        "days_until_due": (bill.due_date - date.today()).days,
        "due_in": humanize_delta(bill.due_date),
        "note": bill.note,
    }


def _status_cell(status: str) -> str:
    return {
        "paid": "[green]✓ paid[/green]",
        "overdue": "[red]⚠ overdue[/red]",
        "due soon": "[yellow]⏰ due soon[/yellow]",
        "upcoming": "[cyan]upcoming[/cyan]",
    }.get(status, status)


@app.command()
def add(
    name: str = typer.Argument(..., help="Bill name, e.g. 'Electricity'"),
    due: str = typer.Option(..., "--due", "-d", help="Due date"),
    amount: float = typer.Option(0, "--amount", "-a", help="Amount due"),
    category: str = typer.Option("other", "--category", "-c", help="Category, e.g. utilities"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🧾 Add a bill with a due date."""
    bill = Bill(
        name=name, amount=amount, due_date=parse_date(due),
        category=category.lower(), note=note,
    )
    with session() as db:
        db.add(bill)
        db.flush()
        db.refresh(bill)
        data = _row(bill)
    ok(f"Added {EMOJI} {name} — due {bill.due_date} ({data['due_in']})",
       json_out=json_out, data=data)


@app.command(name="list")
def list_bills(
    show_all: bool = typer.Option(False, "--all", help="Include paid bills"),
    json_out: JsonOpt = False,
) -> None:
    """🧾 List bills, soonest due first."""
    with session() as db:
        query = select(Bill)
        if not show_all:
            query = query.where(Bill.paid == False)  # noqa: E712
        bills = list(db.exec(query.order_by(Bill.due_date)).all())
    render_rows(
        [_row(b) for b in bills],
        [("id", "ID"), ("name", "Name"), ("amount", "Amount"),
         ("due_date", "Due"), ("due_in", "When"), ("status", "Status")],
        json_out=json_out,
        title="🧾 Bills",
        formatters={
            "amount": lambda v, r: money(v) if v else "[dim]—[/dim]",
            "status": lambda v, r: _status_cell(v),
        },
        empty="No bills due — add one with: clibo bills add 'Rent' -d 2026-06-01 -a 900",
    )


@app.command()
def pay(
    bill_id: int = typer.Argument(..., help="Bill ID"),
    on: str = typer.Option("today", "--date", "-d", help="Date paid"),
    json_out: JsonOpt = False,
) -> None:
    """🧾 Mark a bill as paid."""
    with session() as db:
        bill = db.get(Bill, bill_id)
        if not bill:
            fail(f"No bill #{bill_id}", json_out=json_out)
        bill.paid = True
        bill.paid_date = parse_date(on)
        db.add(bill)
        db.flush()
        data = _row(bill)
    ok(f"Paid {EMOJI} {bill.name}", json_out=json_out, data=data)


@app.command()
def unpay(bill_id: int = typer.Argument(..., help="Bill ID"), json_out: JsonOpt = False) -> None:
    """🧾 Mark a bill as unpaid again."""
    with session() as db:
        bill = db.get(Bill, bill_id)
        if not bill:
            fail(f"No bill #{bill_id}", json_out=json_out)
        bill.paid = False
        bill.paid_date = None
        db.add(bill)
    ok(f"Marked {EMOJI} {bill.name} unpaid", json_out=json_out, data={"id": bill_id, "paid": False})


@app.command()
def rm(bill_id: int = typer.Argument(..., help="Bill ID"), json_out: JsonOpt = False) -> None:
    """🧾 Delete a bill."""
    with session() as db:
        bill = db.get(Bill, bill_id)
        if not bill:
            fail(f"No bill #{bill_id}", json_out=json_out)
        db.delete(bill)
    ok(f"Deleted bill #{bill_id}", json_out=json_out, data={"deleted": bill_id})


@app.command()
def due(
    days: int = typer.Option(7, "--days", help="Look ahead this many days"),
    json_out: JsonOpt = False,
) -> None:
    """🔔 Bills that are overdue or due soon."""
    horizon = date.today() + timedelta(days=days)
    with session() as db:
        bills = list(
            db.exec(
                select(Bill)
                .where(Bill.paid == False)  # noqa: E712
                .where(Bill.due_date <= horizon)
                .order_by(Bill.due_date)
            ).all()
        )
    render_rows(
        [_row(b) for b in bills],
        [("id", "ID"), ("name", "Name"), ("amount", "Amount"),
         ("due_date", "Due"), ("due_in", "When"), ("status", "Status")],
        json_out=json_out,
        title=f"🔔 Bills due within {days} days",
        formatters={
            "amount": lambda v, r: money(v) if v else "[dim]—[/dim]",
            "status": lambda v, r: _status_cell(v),
        },
        empty="Nothing due soon — you're all caught up! ✨",
    )


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Bill stats — unpaid total and overdue count."""
    with session() as db:
        bills = list(db.exec(select(Bill)).all())
    unpaid = [b for b in bills if not b.paid]
    overdue = [b for b in unpaid if b.due_date < date.today()]
    data = {
        "total_bills": len(bills),
        "unpaid": len(unpaid),
        "overdue": len(overdue),
        "unpaid_amount": round(sum(b.amount for b in unpaid), 2),
        "overdue_amount": round(sum(b.amount for b in overdue), 2),
        "currency": get_currency(),
    }
    render_record(data, json_out=json_out, title="📊 Bill stats")
