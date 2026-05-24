"""📉 debt — debt & loan payoff tracker."""

from __future__ import annotations

from datetime import date, datetime

import typer
from sqlmodel import Field, SQLModel, select

from clibo.clis.expense import get_currency, money
from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, bar, fail, ok, render_record, render_rows

NAME = "debt"
HELP = "📉 Debt & loan payoff tracker"
EMOJI = "📉"


class Debt(SQLModel, table=True):
    """A debt or loan you are paying down."""

    __tablename__ = "debt_debt"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    principal: float
    creditor: str | None = None
    apr: float | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


class DebtPayment(SQLModel, table=True):
    """A payment made toward a debt."""

    __tablename__ = "debt_payment"

    id: int | None = Field(default=None, primary_key=True)
    debt_id: int = Field(index=True)
    amount: float
    entry_date: date = Field(default_factory=date.today)
    created_at: datetime = Field(default_factory=datetime.now)
    note: str | None = None


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context, json_out: JsonOpt = False) -> None:
    """Default: ``clibo debt`` (bare) lists every debt with payoff progress."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(list_debts, json_out=json_out)


def _resolve(db, ident: str) -> Debt | None:
    """Look up a debt by numeric ID or by (case-insensitive) name."""
    if ident.isdigit():
        debt = db.get(Debt, int(ident))
        if debt:
            return debt
    return db.exec(select(Debt).where(Debt.name.ilike(ident))).first()


def _paid(db, debt_id: int) -> float:
    """Total paid toward a debt."""
    payments = db.exec(select(DebtPayment).where(DebtPayment.debt_id == debt_id)).all()
    return round(sum(p.amount for p in payments), 2)


def _row(db, debt: Debt) -> dict:
    paid = _paid(db, debt.id)
    return {
        "id": debt.id,
        "name": debt.name,
        "creditor": debt.creditor,
        "principal": debt.principal,
        "paid": paid,
        "remaining": round(max(0.0, debt.principal - paid), 2),
        "progress_pct": round(paid / debt.principal * 100, 1) if debt.principal else 0.0,
        "cleared": paid >= debt.principal,
        "apr": debt.apr,
        "note": debt.note,
    }


@app.command()
def add(
    name: str = typer.Argument(..., help="Debt name, e.g. 'Car loan'"),
    amount: float = typer.Option(..., "--amount", "-a", help="Total amount owed"),
    creditor: str = typer.Option(None, "--creditor", "-c", help="Who it's owed to"),
    apr: float = typer.Option(None, "--apr", help="Annual interest rate %"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """📉 Register a debt or loan."""
    if amount <= 0:
        fail("Amount must be positive", json_out=json_out)
    debt = Debt(name=name, principal=amount, creditor=creditor, apr=apr, note=note)
    with session() as db:
        db.add(debt)
        db.flush()
        db.refresh(debt)
        data = _row(db, debt)
    ok(f"Added {EMOJI} '{name}' — owe {money(amount)}", json_out=json_out, data=data)


@app.command()
def pay(
    debt: str = typer.Argument(..., help="Debt name or ID"),
    amount: float = typer.Argument(..., help="Payment amount"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """📉 Log a payment toward a debt."""
    if amount <= 0:
        fail("Amount must be positive", json_out=json_out)
    with session() as db:
        target = _resolve(db, debt)
        if not target:
            fail(f"No debt matching {debt!r}", json_out=json_out)
        db.add(DebtPayment(debt_id=target.id, amount=amount,
                           entry_date=parse_date(on), note=note))
        db.flush()
        data = _row(db, target)
    flair = "  🎉 debt cleared!" if data["cleared"] else ""
    ok(f"Paid {money(amount)} on '{target.name}' — {money(data['remaining'])} left{flair}",
       json_out=json_out, data=data)


@app.command(name="list")
def list_debts(json_out: JsonOpt = False) -> None:
    """📉 List all debts with payoff progress."""
    with session() as db:
        debts = list(db.exec(select(Debt).order_by(Debt.name)).all())
        rows = [_row(db, d) for d in debts]
    render_rows(
        rows,
        [("id", "ID"), ("name", "Debt"), ("creditor", "Creditor"),
         ("paid", "Paid"), ("remaining", "Remaining"), ("progress_pct", "Paid Off")],
        json_out=json_out,
        title="📉 Debts",
        formatters={
            "paid": lambda v, r: money(v),
            "remaining": lambda v, r: money(v),
            "progress_pct": lambda v, r: bar(v, 100),
        },
        empty="No debts tracked — try: clibo debt add 'Car loan' -a 8000",
    )


@app.command()
def show(
    debt: str = typer.Argument(..., help="Debt name or ID"),
    json_out: JsonOpt = False,
) -> None:
    """📉 Show a debt with its payment history."""
    with session() as db:
        target = _resolve(db, debt)
        if not target:
            fail(f"No debt matching {debt!r}", json_out=json_out)
        data = _row(db, target)
        payments = [
            {"id": p.id, "entry_date": p.entry_date, "amount": p.amount, "note": p.note}
            for p in db.exec(
                select(DebtPayment)
                .where(DebtPayment.debt_id == target.id)
                .order_by(DebtPayment.entry_date.desc(), DebtPayment.id.desc())
            ).all()
        ]
    if json_out:
        render_record(data | {"payments": payments}, json_out=True)
        return
    render_record(data, json_out=False, title=f"📉 {target.name}")
    render_rows(
        payments,
        [("id", "ID"), ("entry_date", "Date"), ("amount", "Amount"), ("note", "Note")],
        json_out=False,
        title="Payment history",
        formatters={"amount": lambda v, r: money(v)},
        empty="No payments yet.",
    )


@app.command()
def rm(debt_id: int = typer.Argument(..., help="Debt ID"), json_out: JsonOpt = False) -> None:
    """📉 Delete a debt and its payment history."""
    with session() as db:
        debt = db.get(Debt, debt_id)
        if not debt:
            fail(f"No debt #{debt_id}", json_out=json_out)
        for payment in db.exec(select(DebtPayment).where(DebtPayment.debt_id == debt_id)).all():
            db.delete(payment)
        db.delete(debt)
    ok(f"Deleted debt #{debt_id}", json_out=json_out, data={"deleted": debt_id})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Overall debt summary."""
    with session() as db:
        debts = list(db.exec(select(Debt)).all())
        rows = [_row(db, d) for d in debts]
    if not debts:
        fail("No debts tracked", json_out=json_out)
    total_principal = round(sum(r["principal"] for r in rows), 2)
    total_paid = round(sum(r["paid"] for r in rows), 2)
    data = {
        "debts": len(rows),
        "cleared": sum(1 for r in rows if r["cleared"]),
        "total_borrowed": total_principal,
        "total_paid": total_paid,
        "total_remaining": round(max(0.0, total_principal - total_paid), 2),
        "progress_pct": round(total_paid / total_principal * 100, 1) if total_principal else 0.0,
        "currency": get_currency(),
    }
    render_record(data, json_out=json_out, title="📊 Debt stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
