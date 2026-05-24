"""📊 budget — monthly budgets by category.

Reads the 💸 expense tool's data to show live spending against each budget.
"""

from __future__ import annotations

from datetime import date, datetime

import typer
from sqlmodel import Field, SQLModel, select

from clibo.clis.expense import Expense, get_currency, money
from clibo.core.db import session
from clibo.core.output import JsonOpt, bar, console, fail, ok, render_record, render_rows

NAME = "budget"
HELP = "📊 Monthly budgets by category"
EMOJI = "📊"


class Budget(SQLModel, table=True):
    """A monthly spending limit for one expense category."""

    __tablename__ = "budget_limit"

    id: int | None = Field(default=None, primary_key=True)
    category: str = Field(index=True)
    monthly_limit: float
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context) -> None:
    """Default: ``clibo budget`` (bare) shows every budget with this month's spending."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(list_budgets, json_out=False)


def _month_start() -> date:
    return date.today().replace(day=1)


def _spent_this_month() -> dict[str, float]:
    """Sum expenses per category for the current calendar month."""
    with session() as db:
        entries = db.exec(
            select(Expense).where(Expense.entry_date >= _month_start())
        ).all()
    spent: dict[str, float] = {}
    for entry in entries:
        spent[entry.category] = round(spent.get(entry.category, 0) + entry.amount, 2)
    return spent


def _status_row(budget: Budget, spent: float) -> dict:
    remaining = round(budget.monthly_limit - spent, 2)
    return {
        "category": budget.category,
        "limit": budget.monthly_limit,
        "spent": round(spent, 2),
        "remaining": remaining,
        "used_pct": round(spent / budget.monthly_limit * 100, 1) if budget.monthly_limit else 0.0,
        "over_budget": spent > budget.monthly_limit,
    }


@app.command(name="set")
def set_budget(
    category: str = typer.Argument(..., help="Expense category, e.g. food"),
    amount: float = typer.Argument(..., help="Monthly limit for this category"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Set or update a category's monthly budget."""
    if amount <= 0:
        fail("Budget amount must be positive", json_out=json_out)
    cat = category.lower()
    with session() as db:
        budget = db.exec(select(Budget).where(Budget.category == cat)).first()
        if budget:
            budget.monthly_limit = amount
        else:
            budget = Budget(category=cat, monthly_limit=amount)
        db.add(budget)
        db.flush()
        db.refresh(budget)
        data = {"id": budget.id, "category": budget.category, "monthly_limit": amount}
    ok(f"Budget for {cat} set to {money(amount)}/month", json_out=json_out, data=data)


# `add` is the friendlier verb in agent flows — matches every other tool.
app.command(name="add", help="Alias for `set` — create or update a budget")(set_budget)


@app.command(name="list")
def list_budgets(json_out: JsonOpt = False) -> None:
    """📊 Show every budget with this month's spending against it."""
    spent = _spent_this_month()
    with session() as db:
        budgets = list(db.exec(select(Budget).order_by(Budget.category)).all())
    rows = [_status_row(b, spent.get(b.category, 0.0)) for b in budgets]
    if json_out:
        render_record(
            {"month": _month_start().strftime("%Y-%m"), "budgets": rows,
             "currency": get_currency()},
            json_out=True,
        )
        return
    render_rows(
        rows,
        [("category", "Category"), ("limit", "Limit"), ("spent", "Spent"),
         ("remaining", "Remaining"), ("used_pct", "Progress")],
        json_out=False,
        title=f"📊 Budgets · {_month_start():%B %Y}",
        formatters={
            "limit": lambda v, r: money(v),
            "spent": lambda v, r: money(v),
            "remaining": lambda v, r: (f"[red]{money(v)}[/red]" if v < 0
                                       else f"[green]{money(v)}[/green]"),
            "used_pct": lambda v, r: bar(v, 100),
        },
        empty="No budgets set — try: clibo budget add food 400",
    )
    if rows:
        total_limit = round(sum(r["limit"] for r in rows), 2)
        total_spent = round(sum(r["spent"] for r in rows), 2)
        over = [r["category"] for r in rows if r["over_budget"]]
        console.print(
            f"  💰 [bold]{money(total_spent)}[/bold] spent of {money(total_limit)} budgeted"
        )
        if over:
            console.print(f"  [red]⚠️  Over budget: {', '.join(over)}[/red]")


@app.command()
def check(
    category: str = typer.Argument(..., help="Category to check"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Check one category's budget status."""
    cat = category.lower()
    with session() as db:
        budget = db.exec(select(Budget).where(Budget.category == cat)).first()
    if not budget:
        fail(f"No budget set for {cat!r} — set one with: clibo budget add {cat} 300",
             json_out=json_out)
    row = _status_row(budget, _spent_this_month().get(cat, 0.0))
    render_record(row, json_out=json_out, title=f"📊 Budget · {cat}")


@app.command()
def status(json_out: JsonOpt = False) -> None:
    """📊 Overall budget summary for this month."""
    spent = _spent_this_month()
    with session() as db:
        budgets = list(db.exec(select(Budget)).all())
    if not budgets:
        fail("No budgets set — try: clibo budget add food 400", json_out=json_out)
    rows = [_status_row(b, spent.get(b.category, 0.0)) for b in budgets]
    total_limit = round(sum(r["limit"] for r in rows), 2)
    total_spent = round(sum(r["spent"] for r in rows), 2)
    data = {
        "month": _month_start().strftime("%Y-%m"),
        "categories": len(rows),
        "total_limit": total_limit,
        "total_spent": total_spent,
        "total_remaining": round(total_limit - total_spent, 2),
        "used_pct": round(total_spent / total_limit * 100, 1) if total_limit else 0.0,
        "over_budget_categories": [r["category"] for r in rows if r["over_budget"]],
        "currency": get_currency(),
    }
    render_record(data, json_out=json_out, title="📊 Budget status")


@app.command()
def rm(
    category: str = typer.Argument(..., help="Category to remove the budget for"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Delete a category budget."""
    cat = category.lower()
    with session() as db:
        budget = db.exec(select(Budget).where(Budget.category == cat)).first()
        if not budget:
            fail(f"No budget set for {cat!r}", json_out=json_out)
        db.delete(budget)
    ok(f"Deleted budget for {cat}", json_out=json_out, data={"deleted": cat})
