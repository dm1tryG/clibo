"""🏋️ workout — exercise & gym session log."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, console, fail, ok, render_record, render_rows

NAME = "workout"
HELP = "🏋️ Exercise & gym session log"
EMOJI = "🏋️"


class Workout(SQLModel, table=True):
    """One exercise performed: strength (sets/reps/weight) or cardio (minutes)."""

    __tablename__ = "workout_entry"

    id: int | None = Field(default=None, primary_key=True)
    exercise: str
    sets: int = 0
    reps: int = 0
    weight_kg: float = 0.0
    duration_min: int = 0
    kcal_burned: int | None = None     # calories burned in this session
    entry_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    note: str | None = None


app = typer.Typer(no_args_is_help=True, help=HELP)


def _volume(entry: Workout) -> float:
    """Total lifted volume = sets × reps × weight (kg)."""
    return round(entry.sets * entry.reps * entry.weight_kg, 1)


def _row(entry: Workout) -> dict:
    return {
        "id": entry.id,
        "entry_date": entry.entry_date,
        "exercise": entry.exercise,
        "sets": entry.sets,
        "reps": entry.reps,
        "weight_kg": entry.weight_kg,
        "duration_min": entry.duration_min,
        "kcal_burned": entry.kcal_burned,
        "volume_kg": _volume(entry),
        "note": entry.note,
    }


@app.command()
def log(
    exercise: str = typer.Argument(..., help="Exercise name, e.g. 'bench press'"),
    sets: int = typer.Option(0, "--sets", "-s", help="Number of sets"),
    reps: int = typer.Option(0, "--reps", "-r", help="Reps per set"),
    weight_kg: float = typer.Option(0, "--weight", "-w", help="Weight per rep, kg"),
    duration_min: int = typer.Option(0, "--duration", "-t", help="Duration in minutes (cardio)"),
    calories: int = typer.Option(None, "--calories", "-c",
                                  help="Calories burned (kcal) — typical for cardio"),
    on: str = typer.Option("today", "--date", "-d", help="Date performed"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🏋️ Log an exercise — strength sets, cardio session, or both."""
    if calories is not None and calories < 0:
        fail("Calories must be non-negative", json_out=json_out)
    entry = Workout(
        exercise=exercise,
        sets=sets,
        reps=reps,
        weight_kg=weight_kg,
        duration_min=duration_min,
        kcal_burned=calories,
        entry_date=parse_date(on),
        note=note,
    )
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        data = _row(entry)
    if duration_min:
        detail = f"{duration_min} min"
    elif sets or reps or weight_kg:
        detail = f"{sets}×{reps} @ {weight_kg:g}kg"
    else:
        detail = "logged"
    if calories:
        detail += f" · {calories} kcal"
    ok(f"Logged {EMOJI} {exercise} — {detail}", json_out=json_out, data=data)


# `add` is a friendlier alias for `log` (predictable verbs across tools).
app.command(name="add", help="Alias for `log`")(log)


@app.command()
def today(json_out: JsonOpt = False) -> None:
    """🏋️ Show today's workout."""
    day = date.today()
    with session() as db:
        entries = list(
            db.exec(
                select(Workout)
                .where(Workout.entry_date == day)
                .order_by(Workout.created_at)
            ).all()
        )
    rows = [_row(e) for e in entries]
    if json_out:
        render_record(
            {
                "date": day,
                "exercises": rows,
                "total_volume_kg": round(sum(r["volume_kg"] for r in rows), 1),
                "total_minutes": sum(r["duration_min"] for r in rows),
                "total_kcal": sum(r["kcal_burned"] or 0 for r in rows),
            },
            json_out=True,
        )
        return
    render_rows(
        rows,
        [("exercise", "Exercise"), ("sets", "Sets"), ("reps", "Reps"),
         ("weight_kg", "Weight·kg"), ("duration_min", "Min"), ("volume_kg", "Volume·kg")],
        json_out=False,
        title=f"🏋️ Workout · {day:%a %d %b}",
        empty="Nothing logged today — try: clibo workout log 'squat' -s 5 -r 5 -w 80",
    )
    if rows:
        volume = round(sum(r["volume_kg"] for r in rows), 1)
        minutes = sum(r["duration_min"] for r in rows)
        kcal = sum(r["kcal_burned"] or 0 for r in rows)
        line = (f"  💪 [bold]{len(rows)}[/bold] exercises    "
                f"🏋️ {volume:g}kg volume    ⏱️ {minutes} min")
        if kcal:
            line += f"    🔥 {kcal} kcal"
        console.print(line)


@app.command(name="list")
def list_entries(
    days: int = typer.Option(14, "--days", help="Look back this many days"),
    exercise: str = typer.Option(None, "--exercise", "-e", help="Filter by exercise name"),
    json_out: JsonOpt = False,
) -> None:
    """🏋️ List recent workout entries."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        query = select(Workout).where(Workout.entry_date >= since)
        if exercise:
            query = query.where(Workout.exercise.ilike(f"%{exercise}%"))
        entries = list(
            db.exec(query.order_by(Workout.entry_date.desc(), Workout.id.desc())).all()
        )
    render_rows(
        [_row(e) for e in entries],
        [("id", "ID"), ("entry_date", "Date"), ("exercise", "Exercise"),
         ("sets", "Sets"), ("reps", "Reps"), ("weight_kg", "Wt·kg"), ("volume_kg", "Vol·kg")],
        json_out=json_out,
        title="🏋️ Workout log",
        empty="No workouts yet.",
    )


@app.command()
def show(entry_id: int = typer.Argument(..., help="Entry ID"), json_out: JsonOpt = False) -> None:
    """🏋️ Show one workout entry."""
    with session() as db:
        entry = db.get(Workout, entry_id)
        if not entry:
            fail(f"No workout #{entry_id}", json_out=json_out)
        data = _row(entry) | {"created_at": entry.created_at}
    render_record(data, json_out=json_out, title=f"🏋️ Workout #{entry_id}")


@app.command()
def rm(entry_id: int = typer.Argument(..., help="Entry ID"), json_out: JsonOpt = False) -> None:
    """🏋️ Delete a workout entry."""
    with session() as db:
        entry = db.get(Workout, entry_id)
        if not entry:
            fail(f"No workout #{entry_id}", json_out=json_out)
        db.delete(entry)
    ok(f"Deleted workout #{entry_id}", json_out=json_out, data={"deleted": entry_id})


@app.command()
def stats(
    days: int = typer.Option(30, "--days", help="Window size in days"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Workout stats over the last N days."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        entries = list(db.exec(select(Workout).where(Workout.entry_date >= since)).all())
    by_exercise: dict[str, int] = {}
    for entry in entries:
        by_exercise[entry.exercise] = by_exercise.get(entry.exercise, 0) + 1
    top = sorted(by_exercise.items(), key=lambda kv: kv[1], reverse=True)[:3]
    data = {
        "window_days": days,
        "sessions": len({e.entry_date for e in entries}),
        "exercises_logged": len(entries),
        "total_volume_kg": round(sum(_volume(e) for e in entries), 1),
        "total_minutes": sum(e.duration_min for e in entries),
        "total_kcal_burned": sum(e.kcal_burned or 0 for e in entries),
        "top_exercises": [{"exercise": name, "count": count} for name, count in top],
    }
    render_record(data, json_out=json_out, title=f"📊 Workout stats · last {days}d")
