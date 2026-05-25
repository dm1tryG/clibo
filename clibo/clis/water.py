"""💧 water — daily water intake tracker."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date, parse_volume_ml
from clibo.core.db import session
from clibo.core.output import JsonOpt, bar, console, fail, ok, render_record, render_rows
from clibo.core.settings import get_setting, set_setting

NAME = "water"
HELP = "💧 Daily water intake tracker"
EMOJI = "💧"
DEFAULT_GOAL_ML = 2000


class WaterLog(SQLModel, table=True):
    """One drink of water, in millilitres."""

    __tablename__ = "water_log"

    id: int | None = Field(default=None, primary_key=True)
    amount_ml: int
    entry_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context, json_out: JsonOpt = False) -> None:
    """Default: ``clibo water`` (bare) shows today's intake vs goal."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(today, json_out=json_out)


def _goal() -> int:
    return int(get_setting(NAME, "daily_ml", str(DEFAULT_GOAL_ML)) or DEFAULT_GOAL_ML)


@app.command()
def drink(
    amount_ml: str = typer.Argument(
        "250",
        help="Amount — ml by default ('500'), or with explicit suffix "
             "('500ml' / '16oz' / '1L'); oz and L auto-convert to ml",
    ),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    json_out: JsonOpt = False,
) -> None:
    """💧 Log a drink of water.

    Accepts plain ml (``500``) or unit-suffixed values (``500ml`` /
    ``16oz`` / ``1L``). US fluid ounces convert via 1 fl oz =
    29.5735 ml; litres × 1000.
    """
    parsed_ml = parse_volume_ml(amount_ml)
    if parsed_ml <= 0:
        fail("Amount must be positive", json_out=json_out)
    entry = WaterLog(amount_ml=parsed_ml, entry_date=parse_date(on))
    with session() as db:
        db.add(entry)
        db.flush()
        total = sum(
            r.amount_ml
            for r in db.exec(
                select(WaterLog).where(WaterLog.entry_date == entry.entry_date)
            ).all()
        )
    goal = _goal()
    ok(
        f"Logged {EMOJI} {parsed_ml}ml — {total}/{goal}ml today",
        json_out=json_out,
        data={"id": entry.id, "amount_ml": parsed_ml, "total_today": total, "goal_ml": goal},
    )


# `add` is a friendlier alias for `drink` (predictable verbs across tools).
app.command(name="add", help="Alias for `drink`")(drink)


@app.command()
def today(json_out: JsonOpt = False) -> None:
    """💧 Show today's water intake and goal progress."""
    day = date.today()
    with session() as db:
        entries = list(
            db.exec(select(WaterLog).where(WaterLog.entry_date == day)).all()
        )
    total = sum(e.amount_ml for e in entries)
    goal = _goal()
    remaining_ml = max(0, goal - total) if goal > 0 else None
    pct_of_goal = round(total / goal * 100, 1) if goal > 0 else None
    if json_out:
        render_record(
            {"date": day, "total_ml": total, "goal_ml": goal, "drinks": len(entries),
             "reached": total >= goal if goal > 0 else False,
             "remaining_ml": remaining_ml, "pct_of_goal": pct_of_goal},
            json_out=True,
        )
        return
    console.print(f"\n💧 [bold]Water today[/bold] · {day:%a %d %b}\n")
    console.print(f"  {bar(total, goal)}")
    console.print(f"  [bold cyan]{total}[/bold cyan] / {goal} ml   ·   {len(entries)} drinks")
    if total >= goal:
        console.print("  [green]✓ Goal reached — nice![/green]\n")
    else:
        console.print(f"  [yellow]{goal - total}ml to go[/yellow]\n")


@app.command(name="list")
def list_entries(
    days: int = typer.Option(7, "--days", help="Look back this many days"),
    json_out: JsonOpt = False,
) -> None:
    """💧 Daily water totals for the last N days."""
    since = date.today() - timedelta(days=days - 1)
    goal = _goal()
    with session() as db:
        entries = list(db.exec(select(WaterLog).where(WaterLog.entry_date >= since)).all())
    by_day: dict[date, int] = {}
    for entry in entries:
        by_day[entry.entry_date] = by_day.get(entry.entry_date, 0) + entry.amount_ml
    rows = [
        {"date": d, "total_ml": ml, "goal_ml": goal, "reached": ml >= goal}
        for d, ml in sorted(by_day.items(), reverse=True)
    ]
    render_rows(
        rows,
        [("date", "Date"), ("total_ml", "Total·ml"), ("reached", "Goal?")],
        json_out=json_out,
        title="💧 Water — daily totals",
        empty="No water logged yet — try: clibo water drink 250",
    )


@app.command()
def rm(entry_id: int = typer.Argument(..., help="Log ID"), json_out: JsonOpt = False) -> None:
    """💧 Delete a water log entry."""
    with session() as db:
        entry = db.get(WaterLog, entry_id)
        if not entry:
            fail(f"No water log #{entry_id}", json_out=json_out)
        db.delete(entry)
    ok(f"Deleted water log #{entry_id}", json_out=json_out, data={"deleted": entry_id})


@app.command()
def goal(
    set_ml: int = typer.Option(None, "--set", help="Set your daily water goal in ml"),
    json_out: JsonOpt = False,
) -> None:
    """🎯 Show or set your daily water goal."""
    if set_ml is not None:
        if set_ml <= 0:
            fail("Goal must be positive", json_out=json_out)
        set_setting(NAME, "daily_ml", str(set_ml))
        ok(f"Daily water goal set to {set_ml}ml", json_out=json_out, data={"daily_ml": set_ml})
        return
    render_record({"daily_ml": _goal()}, json_out=json_out, title="🎯 Water goal")


@app.command()
def stats(
    days: int = typer.Option(7, "--days", help="Window size in days"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Water intake stats over the last N days."""
    since = date.today() - timedelta(days=days - 1)
    goal = _goal()
    with session() as db:
        entries = list(db.exec(select(WaterLog).where(WaterLog.entry_date >= since)).all())
    by_day: dict[date, int] = {}
    for entry in entries:
        by_day[entry.entry_date] = by_day.get(entry.entry_date, 0) + entry.amount_ml
    logged = len(by_day)
    total = sum(by_day.values())
    data = {
        "window_days": days,
        "days_logged": logged,
        "total_ml": total,
        "avg_ml_per_day": round(total / logged) if logged else 0,
        "days_goal_reached": sum(1 for ml in by_day.values() if ml >= goal),
        "goal_ml": goal,
    }
    render_record(data, json_out=json_out, title=f"📊 Water stats · last {days}d")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
