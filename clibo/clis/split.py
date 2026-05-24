"""🤝 split — split shared expenses with people."""

from __future__ import annotations

from datetime import date, datetime

import typer
from sqlmodel import Field, SQLModel, select

from clibo.clis.expense import money
from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, console, fail, ok, render_record, render_rows

NAME = "split"
HELP = "🤝 Split shared expenses with people"
EMOJI = "🤝"


class SplitExpense(SQLModel, table=True):
    """A shared expense split equally among its participants."""

    __tablename__ = "split_expense"

    id: int | None = Field(default=None, primary_key=True)
    description: str
    amount: float
    paid_by: str
    participants: str  # comma-joined names
    entry_date: date = Field(default_factory=date.today)
    created_at: datetime = Field(default_factory=datetime.now)
    note: str | None = None


class SplitSettlement(SQLModel, table=True):
    """A cash payment from one person to another to settle up."""

    __tablename__ = "split_settlement"

    id: int | None = Field(default=None, primary_key=True)
    from_person: str
    to_person: str
    amount: float
    entry_date: date = Field(default_factory=date.today)
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context) -> None:
    """Default: ``clibo split`` (bare) runs the ``balances`` summary."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(balances, json_out=False)


def _people(csv: str) -> list[str]:
    """Parse a comma-separated list of names."""
    return [p.strip() for p in csv.split(",") if p.strip()]


def _balances(db) -> dict[str, float]:
    """Net balance per person: positive = owed money, negative = owes."""
    balance: dict[str, float] = {}
    for exp in db.exec(select(SplitExpense)).all():
        parts = _people(exp.participants)
        if not parts:
            continue
        share = exp.amount / len(parts)
        balance[exp.paid_by] = balance.get(exp.paid_by, 0.0) + exp.amount
        for person in parts:
            balance[person] = balance.get(person, 0.0) - share
    for stl in db.exec(select(SplitSettlement)).all():
        balance[stl.from_person] = balance.get(stl.from_person, 0.0) + stl.amount
        balance[stl.to_person] = balance.get(stl.to_person, 0.0) - stl.amount
    return {p: round(v, 2) for p, v in balance.items()}


def _expense_row(exp: SplitExpense) -> dict:
    parts = _people(exp.participants)
    return {
        "id": exp.id,
        "entry_date": exp.entry_date,
        "description": exp.description,
        "amount": exp.amount,
        "paid_by": exp.paid_by,
        "participants": parts,
        "per_person": round(exp.amount / len(parts), 2) if parts else 0.0,
        "note": exp.note,
    }


@app.command()
def add(
    description: str = typer.Argument(..., help="What the expense was for"),
    amount: float = typer.Option(..., "--amount", "-a", help="Total amount"),
    paid_by: str = typer.Option(..., "--by", "-b", help="Who paid"),
    among: str = typer.Option(..., "--with", "-w", help="Comma-separated people sharing it"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🤝 Record a shared expense, split equally among participants."""
    if amount <= 0:
        fail("Amount must be positive", json_out=json_out)
    parts = _people(among)
    if not parts:
        fail("Provide at least one person in --with", json_out=json_out)
    exp = SplitExpense(
        description=description, amount=amount, paid_by=paid_by,
        participants=", ".join(parts), entry_date=parse_date(on), note=note,
    )
    with session() as db:
        db.add(exp)
        db.flush()
        db.refresh(exp)
        data = _expense_row(exp)
    ok(f"Logged {EMOJI} {description} — {money(amount)} paid by {paid_by}, "
       f"{money(data['per_person'])} each", json_out=json_out, data=data)


@app.command()
def owe(
    person: str = typer.Argument(..., help="Who you owe"),
    amount: float = typer.Argument(..., help="How much you owe them"),
    me: str = typer.Option("me", "--me", help="Your name in the ledger"),
    description: str = typer.Option(None, "--for", "-f",
                                     help="What for (default: 'IOU')"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🤝 Quick IOU — 'I owe PERSON AMOUNT'.

    Stored as a 1-participant split (they paid, you're the lone
    participant), so it flows through `balances`, `who`, and `settle`
    like any shared expense — no fake bill needed.
    """
    if amount <= 0:
        fail("Amount must be positive", json_out=json_out)
    exp = SplitExpense(
        description=description or f"IOU: {me} owes {person}",
        amount=amount, paid_by=person, participants=me,
        entry_date=parse_date(on), note=note,
    )
    with session() as db:
        db.add(exp)
        db.flush()
        db.refresh(exp)
        data = _expense_row(exp)
    ok(f"Logged {EMOJI} {me} owes {person} {money(amount)}",
       json_out=json_out, data=data)


@app.command()
def lent(
    person: str = typer.Argument(..., help="Who you lent to"),
    amount: float = typer.Argument(..., help="How much you lent them"),
    me: str = typer.Option("me", "--me", help="Your name in the ledger"),
    description: str = typer.Option(None, "--for", "-f",
                                     help="What for (default: 'IOU')"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🤝 Quick IOU — 'I lent PERSON AMOUNT' (they owe you).

    Mirror of `owe`: you're recorded as the payer, the other person
    is the lone participant, so the running balance shows them owing
    you the full amount.
    """
    if amount <= 0:
        fail("Amount must be positive", json_out=json_out)
    exp = SplitExpense(
        description=description or f"IOU: {person} owes {me}",
        amount=amount, paid_by=me, participants=person,
        entry_date=parse_date(on), note=note,
    )
    with session() as db:
        db.add(exp)
        db.flush()
        db.refresh(exp)
        data = _expense_row(exp)
    ok(f"Logged {EMOJI} {person} owes {me} {money(amount)}",
       json_out=json_out, data=data)


@app.command(name="list")
def list_expenses(json_out: JsonOpt = False) -> None:
    """🤝 List all shared expenses."""
    with session() as db:
        expenses = list(
            db.exec(
                select(SplitExpense).order_by(SplitExpense.entry_date.desc(), SplitExpense.id.desc())
            ).all()
        )
    render_rows(
        [_expense_row(e) for e in expenses],
        [("id", "ID"), ("entry_date", "Date"), ("description", "Description"),
         ("amount", "Amount"), ("paid_by", "Paid By"),
         ("participants", "Split Among"), ("per_person", "Each")],
        json_out=json_out,
        title="🤝 Shared expenses",
        formatters={
            "amount": lambda v, r: money(v),
            "per_person": lambda v, r: money(v),
            "participants": lambda v, r: ", ".join(v),
        },
        empty="No shared expenses — try: clibo split add 'Dinner' -a 60 -b Alice -w 'Alice,Bob'",
    )


@app.command()
def rm(expense_id: int = typer.Argument(..., help="Expense ID"), json_out: JsonOpt = False) -> None:
    """🤝 Delete a shared expense."""
    with session() as db:
        exp = db.get(SplitExpense, expense_id)
        if not exp:
            fail(f"No shared expense #{expense_id}", json_out=json_out)
        db.delete(exp)
    ok(f"Deleted shared expense #{expense_id}", json_out=json_out, data={"deleted": expense_id})


@app.command()
def balances(json_out: JsonOpt = False) -> None:
    """⚖️ Show each person's net balance."""
    with session() as db:
        balance = _balances(db)
    rows = [
        {"person": p, "balance": v,
         "status": "is owed" if v > 0.01 else ("owes" if v < -0.01 else "settled")}
        for p, v in sorted(balance.items(), key=lambda kv: kv[1], reverse=True)
    ]
    render_rows(
        rows,
        [("person", "Person"), ("balance", "Balance"), ("status", "Status")],
        json_out=json_out,
        title="⚖️ Balances",
        formatters={
            "balance": lambda v, r: (f"[green]+{money(v)}[/green]" if v > 0.01
                                     else f"[red]{money(v)}[/red]" if v < -0.01
                                     else "[dim]0[/dim]"),
        },
        empty="No expenses yet — nothing to balance.",
    )


@app.command()
def settle(
    from_person: str = typer.Argument(..., help="Who is paying"),
    to_person: str = typer.Argument(..., help="Who is being paid"),
    amount: float = typer.Argument(..., help="Amount settled"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    json_out: JsonOpt = False,
) -> None:
    """💸 Record a settle-up payment between two people."""
    if amount <= 0:
        fail("Amount must be positive", json_out=json_out)
    stl = SplitSettlement(
        from_person=from_person, to_person=to_person, amount=amount, entry_date=parse_date(on),
    )
    with session() as db:
        db.add(stl)
        db.flush()
        db.refresh(stl)
        data = {"id": stl.id, "from": from_person, "to": to_person, "amount": amount}
    ok(f"Recorded {EMOJI} {from_person} → {to_person}: {money(amount)}",
       json_out=json_out, data=data)


@app.command()
def who(json_out: JsonOpt = False) -> None:
    """🧮 Suggest the fewest payments to settle everyone up."""
    with session() as db:
        balance = _balances(db)
    debtors = [[p, -v] for p, v in balance.items() if v < -0.01]
    creditors = [[p, v] for p, v in balance.items() if v > 0.01]
    debtors.sort(key=lambda x: x[1], reverse=True)
    creditors.sort(key=lambda x: x[1], reverse=True)
    transactions: list[dict] = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        pay = round(min(debtors[i][1], creditors[j][1]), 2)
        transactions.append({"from": debtors[i][0], "to": creditors[j][0], "amount": pay})
        debtors[i][1] -= pay
        creditors[j][1] -= pay
        if debtors[i][1] < 0.01:
            i += 1
        if creditors[j][1] < 0.01:
            j += 1
    if json_out:
        render_record({"transactions": transactions}, json_out=True)
        return
    if not transactions:
        console.print("\n  [green]✓ Everyone is settled up![/green]\n")
        return
    console.print("\n🧮 [bold]To settle up:[/bold]\n")
    for txn in transactions:
        console.print(f"  {txn['from']} [cyan]→[/cyan] {txn['to']}   "
                      f"[bold]{money(txn['amount'])}[/bold]")
    console.print()

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)
