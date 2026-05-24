"""🍎 calorie — food & calorie tracker with macros.

Reference implementation: every other clibo tool follows the same shape —
a SQLModel table, a Typer ``app`` with ``add/list/show/edit/rm`` style verbs,
a ``--json`` flag on every command, and output routed through ``core.output``.
"""

from __future__ import annotations

from datetime import date, datetime

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import (
    JsonOpt,
    bar,
    console,
    fail,
    ok,
    render_record,
    render_rows,
)
from clibo.core.settings import get_setting, set_setting

NAME = "calorie"
HELP = "🍎 Food & calorie tracker with macros"
EMOJI = "🍎"
MEALS = ["breakfast", "lunch", "dinner", "snack"]


class CalorieEntry(SQLModel, table=True):
    """A single logged food item."""

    __tablename__ = "calorie_entry"

    id: int | None = Field(default=None, primary_key=True)
    food: str
    kcal: int
    protein: float = 0.0
    carbs: float = 0.0
    fat: float = 0.0
    meal: str = "snack"
    entry_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    note: str | None = None


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context) -> None:
    """Default: ``clibo calorie`` (bare) shows today's food log + macros."""
    if ctx.invoked_subcommand is None:
        # Explicit `meal=None` so ctx.invoke doesn't forward Typer's
        # OptionInfo sentinel for the new --meal flag (iter 111).
        ctx.invoke(today, meal=None, json_out=False)


def _row(entry: CalorieEntry) -> dict:
    """Flatten an entry into a plain dict for rendering / JSON."""
    return {
        "id": entry.id,
        "meal": entry.meal,
        "food": entry.food,
        "kcal": entry.kcal,
        "protein": entry.protein,
        "carbs": entry.carbs,
        "fat": entry.fat,
        "entry_date": entry.entry_date,
        "note": entry.note,
    }


def _totals(entries: list[CalorieEntry]) -> dict:
    """Sum calories and macros across a list of entries."""
    return {
        "kcal": sum(e.kcal for e in entries),
        "protein": round(sum(e.protein for e in entries), 1),
        "carbs": round(sum(e.carbs for e in entries), 1),
        "fat": round(sum(e.fat for e in entries), 1),
    }


@app.command()
def log(
    food: str = typer.Argument(..., help="What you ate, e.g. 'oatmeal with berries'"),
    kcal: int = typer.Option(..., "--kcal", "-k", help="Calories for this item"),
    protein: float = typer.Option(0, "--protein", "-p", help="Protein, grams"),
    carbs: float = typer.Option(0, "--carbs", "-c", help="Carbs, grams"),
    fat: float = typer.Option(0, "--fat", "-f", help="Fat, grams"),
    meal: str = typer.Option("snack", "--meal", "-m", help="breakfast/lunch/dinner/snack"),
    on: str = typer.Option("today", "--date", "-d", help="Date eaten"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🍎 Log a food item with its calories and macros."""
    meal = meal.lower()
    if meal not in MEALS:
        fail(f"Meal must be one of: {', '.join(MEALS)}", json_out=json_out)
    entry = CalorieEntry(
        food=food,
        kcal=kcal,
        protein=protein,
        carbs=carbs,
        fat=fat,
        meal=meal,
        entry_date=parse_date(on),
        note=note,
    )
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        data = _row(entry)
    ok(f"Logged {EMOJI} {food} — {kcal} kcal ({meal})", json_out=json_out, data=data)


# `add` is a friendlier alias for `log` (predictable verbs across tools).
app.command(name="add", help="Alias for `log`")(log)


@app.command()
def today(
    meal: str = typer.Option(
        None, "--meal", "-m",
        help=f"Filter to one meal: {' / '.join(MEALS)}",
    ),
    json_out: JsonOpt = False,
) -> None:
    """🍎 Show today's food log with calorie & macro totals.

    Pass ``--meal breakfast`` (or ``-m breakfast``) to scope the view to
    a single meal — answers questions like "how many calories for
    breakfast today?" without post-processing. The ``by_meal`` block in
    JSON output gives per-meal subtotals regardless of the filter.
    """
    if meal and meal.lower() not in MEALS:
        fail(f"Meal must be one of: {', '.join(MEALS)}", json_out=json_out)
    day = date.today()
    with session() as db:
        entries = list(
            db.exec(
                select(CalorieEntry)
                .where(CalorieEntry.entry_date == day)
                .order_by(CalorieEntry.created_at)
            ).all()
        )
    # Compute per-meal subtotals on the unfiltered set, so the JSON
    # `by_meal` is always complete (agents can read across meals even
    # when --meal is set).
    by_meal_subtotals = {
        m: _totals([e for e in entries if e.meal == m])
        | {"count": sum(1 for e in entries if e.meal == m)}
        for m in MEALS
        if any(e.meal == m for e in entries)
    }
    # Apply the filter for the rendered/returned entries + totals.
    if meal:
        meal_lower = meal.lower()
        entries = [e for e in entries if e.meal == meal_lower]
    entries.sort(key=lambda e: MEALS.index(e.meal) if e.meal in MEALS else 99)
    rows = [_row(e) for e in entries]
    totals = _totals(entries)
    goal = int(get_setting(NAME, "daily_kcal", "0") or "0")

    if json_out:
        render_record(
            {"date": day, "entries": rows, "totals": totals,
             "by_meal": by_meal_subtotals,
             "filter_meal": meal.lower() if meal else None,
             "goal_kcal": goal},
            json_out=True,
        )
        return

    title_suffix = f" · {meal.lower()}" if meal else ""
    render_rows(
        rows,
        [("meal", "Meal"), ("food", "Food"), ("kcal", "Kcal"),
         ("protein", "P·g"), ("carbs", "C·g"), ("fat", "F·g")],
        json_out=False,
        title=f"🍎 Food log · {day:%a %d %b}{title_suffix}",
        empty="No food logged today — add one with: clibo calorie log \"...\" -k 300",
    )
    summary = (
        f"🔥 [bold]{totals['kcal']}[/bold] kcal    "
        f"🥩 {totals['protein']:g}g    🍚 {totals['carbs']:g}g    🧈 {totals['fat']:g}g"
    )
    if goal and not meal:
        summary += (
            f"\n🎯 {bar(totals['kcal'], goal)}  "
            f"[dim]{totals['kcal']}/{goal} kcal[/dim]"
        )
    console.print(summary)
    # Per-meal subtotal line (skipped when filtering — the totals line already
    # is the per-meal view).
    if not meal and len(by_meal_subtotals) > 1:
        parts = [
            f"  [dim]{m}[/dim] {by_meal_subtotals[m]['kcal']}"
            for m in MEALS if m in by_meal_subtotals
        ]
        console.print("  " + "   ·   ".join(parts))


@app.command(name="list")
def list_entries(
    on: str = typer.Option(None, "--date", "-d", help="Only this date"),
    days: int = typer.Option(7, "--days", help="Look back this many days"),
    meal: str = typer.Option(None, "--meal", "-m", help="Filter by meal"),
    json_out: JsonOpt = False,
) -> None:
    """🍎 List recent food entries."""
    with session() as db:
        query = select(CalorieEntry)
        if on:
            query = query.where(CalorieEntry.entry_date == parse_date(on))
        else:
            from datetime import timedelta

            since = date.today() - timedelta(days=days - 1)
            query = query.where(CalorieEntry.entry_date >= since)
        if meal:
            query = query.where(CalorieEntry.meal == meal.lower())
        entries = list(
            db.exec(query.order_by(CalorieEntry.entry_date.desc(), CalorieEntry.id)).all()
        )
    render_rows(
        [_row(e) | {"id": e.id} for e in entries],
        [("id", "ID"), ("entry_date", "Date"), ("meal", "Meal"),
         ("food", "Food"), ("kcal", "Kcal")],
        json_out=json_out,
        title="🍎 Food entries",
        empty="No entries yet.",
    )


@app.command()
def show(entry_id: int = typer.Argument(..., help="Entry ID"), json_out: JsonOpt = False) -> None:
    """🍎 Show one food entry in detail."""
    with session() as db:
        entry = db.get(CalorieEntry, entry_id)
        if not entry:
            fail(f"No entry #{entry_id}", json_out=json_out)
        data = _row(entry) | {"id": entry.id, "created_at": entry.created_at}
    render_record(data, json_out=json_out, title=f"🍎 Entry #{entry_id}")


@app.command()
def edit(
    entry_id: int = typer.Argument(..., help="Entry ID"),
    food: str = typer.Option(None, "--food", help="New food name"),
    kcal: int = typer.Option(None, "--kcal", "-k", help="New calories"),
    protein: float = typer.Option(None, "--protein", "-p"),
    carbs: float = typer.Option(None, "--carbs", "-c"),
    fat: float = typer.Option(None, "--fat", "-f"),
    meal: str = typer.Option(None, "--meal", "-m"),
    note: str = typer.Option(None, "--note", "-n"),
    json_out: JsonOpt = False,
) -> None:
    """🍎 Edit an existing food entry."""
    with session() as db:
        entry = db.get(CalorieEntry, entry_id)
        if not entry:
            fail(f"No entry #{entry_id}", json_out=json_out)
        for field, value in {
            "food": food, "kcal": kcal, "protein": protein,
            "carbs": carbs, "fat": fat, "meal": meal, "note": note,
        }.items():
            if value is not None:
                setattr(entry, field, value.lower() if field == "meal" else value)
        db.add(entry)
        db.flush()
        data = _row(entry) | {"id": entry.id}
    ok(f"Updated entry #{entry_id}", json_out=json_out, data=data)


@app.command()
def rm(entry_id: int = typer.Argument(..., help="Entry ID"), json_out: JsonOpt = False) -> None:
    """🍎 Delete a food entry."""
    with session() as db:
        entry = db.get(CalorieEntry, entry_id)
        if not entry:
            fail(f"No entry #{entry_id}", json_out=json_out)
        db.delete(entry)
    ok(f"Deleted entry #{entry_id}", json_out=json_out, data={"deleted": entry_id})


@app.command()
def goal(
    set_kcal: int = typer.Option(None, "--set", help="Set your daily calorie goal"),
    json_out: JsonOpt = False,
) -> None:
    """🎯 Show or set your daily calorie goal."""
    if set_kcal is not None:
        set_setting(NAME, "daily_kcal", str(set_kcal))
        ok(f"Daily calorie goal set to {set_kcal} kcal", json_out=json_out,
           data={"daily_kcal": set_kcal})
        return
    current = int(get_setting(NAME, "daily_kcal", "0") or "0")
    if not current:
        fail("No goal set yet. Set one with: clibo calorie goal --set 2000",
             json_out=json_out)
    render_record({"daily_kcal": current}, json_out=json_out, title="🎯 Calorie goal")


@app.command()
def stats(
    days: int = typer.Option(7, "--days", help="Window size in days"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Average calories & macros over the last N days."""
    from datetime import timedelta

    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        entries = list(
            db.exec(select(CalorieEntry).where(CalorieEntry.entry_date >= since)).all()
        )
    logged_days = len({e.entry_date for e in entries})
    totals = _totals(entries)
    divisor = logged_days or 1
    data = {
        "window_days": days,
        "days_logged": logged_days,
        "entries": len(entries),
        "total_kcal": totals["kcal"],
        "avg_kcal_per_day": round(totals["kcal"] / divisor),
        "avg_protein_per_day": round(totals["protein"] / divisor, 1),
        "avg_carbs_per_day": round(totals["carbs"] / divisor, 1),
        "avg_fat_per_day": round(totals["fat"] / divisor, 1),
    }
    render_record(data, json_out=json_out, title=f"📊 Calorie stats · last {days}d")
