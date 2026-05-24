"""🍽️ meals — weekly meal planner."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "meals"
HELP = "🍽️ Weekly meal planner"
EMOJI = "🍽️"
MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack"]
GRID_MEALS = ["breakfast", "lunch", "dinner"]


class MealPlan(SQLModel, table=True):
    """A planned meal on a given day."""

    __tablename__ = "meals_plan"

    id: int | None = Field(default=None, primary_key=True)
    plan_date: date = Field(index=True)
    meal_type: str
    dish: str
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context) -> None:
    """Default: ``clibo meals`` (bare) runs the ``today`` summary."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(today, json_out=False)


def _row(meal: MealPlan) -> dict:
    return {
        "id": meal.id,
        "plan_date": meal.plan_date,
        "meal_type": meal.meal_type,
        "dish": meal.dish,
    }


@app.command()
def plan(
    on: str = typer.Argument(..., help="Date (today, tomorrow, YYYY-MM-DD)"),
    meal: str = typer.Argument(..., help="breakfast / lunch / dinner / snack"),
    dish: str = typer.Argument(..., help="What to eat"),
    json_out: JsonOpt = False,
) -> None:
    """🍽️ Plan a meal for a day."""
    meal = meal.lower()
    if meal not in MEAL_TYPES:
        fail(f"Meal must be one of: {', '.join(MEAL_TYPES)}", json_out=json_out)
    entry = MealPlan(plan_date=parse_date(on), meal_type=meal, dish=dish)
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        data = _row(entry)
    ok(f"Planned {EMOJI} {meal} for {entry.plan_date}: {dish}", json_out=json_out, data=data)


# `add` is the friendlier verb in agent flows — matches every other tool.
app.command(name="add", help="Alias for `plan`")(plan)


@app.command()
def today(json_out: JsonOpt = False) -> None:
    """🍽️ Show today's planned meals."""
    with session() as db:
        meals = list(
            db.exec(select(MealPlan).where(MealPlan.plan_date == date.today())).all()
        )
    meals.sort(key=lambda m: MEAL_TYPES.index(m.meal_type) if m.meal_type in MEAL_TYPES else 9)
    render_rows(
        [_row(m) for m in meals],
        [("id", "ID"), ("meal_type", "Meal"), ("dish", "Dish")],
        json_out=json_out,
        title=f"🍽️ Today's meals · {date.today():%a %d %b}",
        empty="Nothing planned today — try: clibo meals plan today dinner 'pasta'",
    )


@app.command()
def week(
    start: str = typer.Option(None, "--start", help="Week start (default: this Monday)"),
    json_out: JsonOpt = False,
) -> None:
    """📅 Show the week's meal plan as a grid."""
    if start:
        monday = parse_date(start)
    else:
        monday = date.today() - timedelta(days=date.today().weekday())
    days = [monday + timedelta(days=i) for i in range(7)]
    with session() as db:
        meals = list(
            db.exec(
                select(MealPlan)
                .where(MealPlan.plan_date >= days[0], MealPlan.plan_date <= days[-1])
            ).all()
        )
    grid: dict[date, dict[str, str]] = {d: {} for d in days}
    for meal in meals:
        if meal.plan_date in grid:
            grid[meal.plan_date][meal.meal_type] = meal.dish
    rows = [
        {"day": d.strftime("%a %d %b"),
         **{m: grid[d].get(m, "") for m in GRID_MEALS}}
        for d in days
    ]
    if json_out:
        render_record(
            {"week_start": monday,
             "days": [{"date": d, **grid[d]} for d in days]},
            json_out=True,
        )
        return
    render_rows(
        rows,
        [("day", "Day"), ("breakfast", "🥣 Breakfast"),
         ("lunch", "🥗 Lunch"), ("dinner", "🍝 Dinner")],
        json_out=False,
        title=f"📅 Meal plan · week of {monday:%d %b}",
    )


@app.command(name="list")
def list_meals(
    days: int = typer.Option(7, "--days", help="Look ahead/back this many days"),
    json_out: JsonOpt = False,
) -> None:
    """🍽️ List planned meals around today."""
    start = date.today() - timedelta(days=days)
    end = date.today() + timedelta(days=days)
    with session() as db:
        meals = list(
            db.exec(
                select(MealPlan)
                .where(MealPlan.plan_date >= start, MealPlan.plan_date <= end)
                .order_by(MealPlan.plan_date, MealPlan.id)
            ).all()
        )
    render_rows(
        [_row(m) for m in meals],
        [("id", "ID"), ("plan_date", "Date"), ("meal_type", "Meal"), ("dish", "Dish")],
        json_out=json_out,
        title="🍽️ Planned meals",
        empty="Nothing planned — try: clibo meals plan tomorrow lunch 'salad'",
    )


@app.command()
def rm(meal_id: int = typer.Argument(..., help="Meal plan ID"), json_out: JsonOpt = False) -> None:
    """🍽️ Delete a planned meal."""
    with session() as db:
        meal = db.get(MealPlan, meal_id)
        if not meal:
            fail(f"No planned meal #{meal_id}", json_out=json_out)
        db.delete(meal)
    ok(f"Deleted planned meal #{meal_id}", json_out=json_out, data={"deleted": meal_id})


@app.command()
def clear(
    on: str = typer.Argument(..., help="Date to clear"),
    json_out: JsonOpt = False,
) -> None:
    """🧹 Clear all planned meals for a day."""
    day = parse_date(on)
    with session() as db:
        meals = list(db.exec(select(MealPlan).where(MealPlan.plan_date == day)).all())
        for meal in meals:
            db.delete(meal)
    ok(f"Cleared {len(meals)} meal(s) for {day}", json_out=json_out,
       data={"date": day, "cleared": len(meals)})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Meal-planning stats."""
    with session() as db:
        meals = list(db.exec(select(MealPlan)).all())
    by_type = {m: sum(1 for x in meals if x.meal_type == m) for m in MEAL_TYPES}
    data = {
        "total_planned": len(meals),
        "days_planned": len({m.plan_date for m in meals}),
        "by_meal_type": by_type,
    }
    render_record(data, json_out=json_out, title="📊 Meal-plan stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)
