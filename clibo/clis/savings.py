"""🐷 savings — savings goals with progress."""

from __future__ import annotations

from datetime import date, datetime

import typer
from sqlmodel import Field, SQLModel, select

from clibo.clis.expense import get_currency, money
from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, bar, fail, ok, render_record, render_rows

NAME = "savings"
HELP = "🐷 Savings goals with progress"
EMOJI = "🐷"


class SavingsGoal(SQLModel, table=True):
    """A thing you're saving up for."""

    __tablename__ = "savings_goal"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    target: float
    deadline: date | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


class SavingsDeposit(SQLModel, table=True):
    """Money put toward (or taken from) a goal. Withdrawals are negative."""

    __tablename__ = "savings_deposit"

    id: int | None = Field(default=None, primary_key=True)
    goal_id: int = Field(index=True)
    amount: float
    entry_date: date = Field(default_factory=date.today)
    created_at: datetime = Field(default_factory=datetime.now)
    note: str | None = None


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context, json_out: JsonOpt = False) -> None:
    """Default: ``clibo savings`` (bare) lists every goal with progress."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(list_goals, json_out=json_out)


def _resolve(db, ident: str) -> SavingsGoal | None:
    """Look up a goal by numeric ID or by (case-insensitive) name."""
    if ident.isdigit():
        goal = db.get(SavingsGoal, int(ident))
        if goal:
            return goal
    return db.exec(select(SavingsGoal).where(SavingsGoal.name.ilike(ident))).first()


def _saved(db, goal_id: int) -> float:
    """Net amount saved toward a goal."""
    deposits = db.exec(
        select(SavingsDeposit).where(SavingsDeposit.goal_id == goal_id)
    ).all()
    return round(sum(d.amount for d in deposits), 2)


def _row(db, goal: SavingsGoal) -> dict:
    saved = _saved(db, goal.id)
    return {
        "id": goal.id,
        "name": goal.name,
        "target": goal.target,
        "saved": saved,
        "remaining": round(max(0.0, goal.target - saved), 2),
        "progress_pct": round(saved / goal.target * 100, 1) if goal.target else 0.0,
        "achieved": saved >= goal.target,
        "deadline": goal.deadline,
        "note": goal.note,
    }


@app.command()
def add(
    name: str = typer.Argument(..., help="Goal name, e.g. 'New laptop'"),
    target: float = typer.Option(..., "--target", "-t", help="Amount to save"),
    deadline: str = typer.Option(None, "--deadline", help="Target date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🐷 Create a savings goal."""
    if target <= 0:
        fail("Target must be positive", json_out=json_out)
    goal = SavingsGoal(
        name=name, target=target,
        deadline=parse_date(deadline) if deadline else None, note=note,
    )
    with session() as db:
        db.add(goal)
        db.flush()
        db.refresh(goal)
        data = _row(db, goal)
    ok(f"Created {EMOJI} '{name}' — target {money(target)}", json_out=json_out, data=data)


@app.command()
def deposit(
    goal: str = typer.Argument(..., help="Goal name or ID"),
    amount: float = typer.Argument(..., help="Amount to add"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🐷 Put money toward a goal."""
    if amount <= 0:
        fail("Amount must be positive", json_out=json_out)
    with session() as db:
        target = _resolve(db, goal)
        if not target:
            fail(f"No savings goal matching {goal!r}", json_out=json_out)
        db.add(SavingsDeposit(goal_id=target.id, amount=amount,
                              entry_date=parse_date(on), note=note))
        db.flush()
        data = _row(db, target)
    flair = "  🎉 goal reached!" if data["achieved"] else ""
    ok(f"Deposited {money(amount)} to '{target.name}' — "
       f"{money(data['saved'])}/{money(data['target'])}{flair}",
       json_out=json_out, data=data)


@app.command()
def withdraw(
    goal: str = typer.Argument(..., help="Goal name or ID"),
    amount: float = typer.Argument(..., help="Amount to take out"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🐷 Take money back out of a goal."""
    if amount <= 0:
        fail("Amount must be positive", json_out=json_out)
    with session() as db:
        target = _resolve(db, goal)
        if not target:
            fail(f"No savings goal matching {goal!r}", json_out=json_out)
        db.add(SavingsDeposit(goal_id=target.id, amount=-amount,
                              entry_date=parse_date(on), note=note))
        db.flush()
        data = _row(db, target)
    ok(f"Withdrew {money(amount)} from '{target.name}' — now {money(data['saved'])}",
       json_out=json_out, data=data)


@app.command(name="list")
def list_goals(json_out: JsonOpt = False) -> None:
    """🐷 List all savings goals with progress."""
    with session() as db:
        goals = list(db.exec(select(SavingsGoal).order_by(SavingsGoal.name)).all())
        rows = [_row(db, g) for g in goals]
    render_rows(
        rows,
        [("id", "ID"), ("name", "Goal"), ("saved", "Saved"), ("target", "Target"),
         ("remaining", "To Go"), ("progress_pct", "Progress")],
        json_out=json_out,
        title="🐷 Savings goals",
        formatters={
            "saved": lambda v, r: money(v),
            "target": lambda v, r: money(v),
            "remaining": lambda v, r: money(v),
            "progress_pct": lambda v, r: bar(v, 100),
        },
        empty="No goals yet — try: clibo savings add 'Vacation' -t 1500",
    )


@app.command()
def show(
    goal: str = typer.Argument(..., help="Goal name or ID"),
    json_out: JsonOpt = False,
) -> None:
    """🐷 Show a goal with its deposit history."""
    with session() as db:
        target = _resolve(db, goal)
        if not target:
            fail(f"No savings goal matching {goal!r}", json_out=json_out)
        data = _row(db, target)
        deposits = [
            {"id": d.id, "entry_date": d.entry_date, "amount": d.amount, "note": d.note}
            for d in db.exec(
                select(SavingsDeposit)
                .where(SavingsDeposit.goal_id == target.id)
                .order_by(SavingsDeposit.entry_date.desc(), SavingsDeposit.id.desc())
            ).all()
        ]
    if json_out:
        render_record(data | {"deposits": deposits}, json_out=True)
        return
    render_record(data, json_out=False, title=f"🐷 {target.name}")
    render_rows(
        deposits,
        [("id", "ID"), ("entry_date", "Date"), ("amount", "Amount"), ("note", "Note")],
        json_out=False,
        title="Deposit history",
        formatters={"amount": lambda v, r: money(v)},
        empty="No deposits yet.",
    )


@app.command()
def rm(goal_id: int = typer.Argument(..., help="Goal ID"), json_out: JsonOpt = False) -> None:
    """🐷 Delete a savings goal and its deposits."""
    with session() as db:
        goal = db.get(SavingsGoal, goal_id)
        if not goal:
            fail(f"No savings goal #{goal_id}", json_out=json_out)
        for dep in db.exec(select(SavingsDeposit).where(SavingsDeposit.goal_id == goal_id)).all():
            db.delete(dep)
        db.delete(goal)
    ok(f"Deleted savings goal #{goal_id}", json_out=json_out, data={"deleted": goal_id})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Overall savings progress across all goals."""
    with session() as db:
        goals = list(db.exec(select(SavingsGoal)).all())
        rows = [_row(db, g) for g in goals]
    if not goals:
        fail("No savings goals yet", json_out=json_out)
    total_target = round(sum(r["target"] for r in rows), 2)
    total_saved = round(sum(r["saved"] for r in rows), 2)
    data = {
        "goals": len(rows),
        "achieved": sum(1 for r in rows if r["achieved"]),
        "total_target": total_target,
        "total_saved": total_saved,
        "total_remaining": round(max(0.0, total_target - total_saved), 2),
        "progress_pct": round(total_saved / total_target * 100, 1) if total_target else 0.0,
        "currency": get_currency(),
    }
    render_record(data, json_out=json_out, title="📊 Savings stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
