"""⚖️ weight — body-weight log with BMI and trend."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows
from clibo.core.settings import get_setting, set_setting

NAME = "weight"
HELP = "⚖️ Body-weight log with BMI & trend"
EMOJI = "⚖️"


class WeightLog(SQLModel, table=True):
    """One body-weight measurement, in kilograms."""

    __tablename__ = "weight_log"

    id: int | None = Field(default=None, primary_key=True)
    weight_kg: float
    entry_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    note: str | None = None


app = typer.Typer(no_args_is_help=True, help=HELP)


def _bmi(weight_kg: float, height_cm: float) -> float:
    """Body Mass Index from weight (kg) and height (cm)."""
    metres = height_cm / 100
    return round(weight_kg / (metres * metres), 1)


def _bmi_class(bmi: float) -> str:
    """The standard WHO BMI category label."""
    if bmi < 18.5:
        return "underweight"
    if bmi < 25:
        return "normal"
    if bmi < 30:
        return "overweight"
    return "obese"


@app.command()
def log(
    weight_kg: float = typer.Argument(..., help="Your weight in kilograms"),
    on: str = typer.Option("today", "--date", "-d", help="Date measured"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """⚖️ Log a body-weight measurement."""
    if weight_kg <= 0:
        fail("Weight must be positive", json_out=json_out)
    entry = WeightLog(weight_kg=weight_kg, entry_date=parse_date(on), note=note)
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        data = {"id": entry.id, "weight_kg": entry.weight_kg, "entry_date": entry.entry_date}
    height = get_setting(NAME, "height_cm")
    if height:
        bmi = _bmi(weight_kg, float(height))
        data["bmi"] = bmi
        ok(f"Logged {EMOJI} {weight_kg:g}kg — BMI {bmi} ({_bmi_class(bmi)})",
           json_out=json_out, data=data)
    else:
        ok(f"Logged {EMOJI} {weight_kg:g}kg", json_out=json_out, data=data)


@app.command(name="list")
def list_entries(
    days: int = typer.Option(30, "--days", help="Look back this many days"),
    json_out: JsonOpt = False,
) -> None:
    """⚖️ List recent weight measurements."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        entries = list(
            db.exec(
                select(WeightLog)
                .where(WeightLog.entry_date >= since)
                .order_by(WeightLog.entry_date.desc(), WeightLog.id.desc())
            ).all()
        )
    rows = [
        {"id": e.id, "entry_date": e.entry_date, "weight_kg": e.weight_kg, "note": e.note}
        for e in entries
    ]
    render_rows(
        rows,
        [("id", "ID"), ("entry_date", "Date"), ("weight_kg", "Weight·kg"), ("note", "Note")],
        json_out=json_out,
        title="⚖️ Weight log",
        empty="No measurements yet — try: clibo weight log 70.5",
    )


@app.command()
def rm(entry_id: int = typer.Argument(..., help="Log ID"), json_out: JsonOpt = False) -> None:
    """⚖️ Delete a weight measurement."""
    with session() as db:
        entry = db.get(WeightLog, entry_id)
        if not entry:
            fail(f"No weight log #{entry_id}", json_out=json_out)
        db.delete(entry)
    ok(f"Deleted weight log #{entry_id}", json_out=json_out, data={"deleted": entry_id})


@app.command()
def height(
    set_cm: float = typer.Option(None, "--set", help="Set your height in centimetres"),
    json_out: JsonOpt = False,
) -> None:
    """📏 Show or set your height (used for BMI)."""
    if set_cm is not None:
        if set_cm <= 0:
            fail("Height must be positive", json_out=json_out)
        set_setting(NAME, "height_cm", str(set_cm))
        ok(f"Height set to {set_cm:g}cm", json_out=json_out, data={"height_cm": set_cm})
        return
    current = get_setting(NAME, "height_cm")
    if not current:
        fail("No height set. Set it with: clibo weight height --set 175", json_out=json_out)
    render_record({"height_cm": float(current)}, json_out=json_out, title="📏 Height")


@app.command()
def stats(
    days: int = typer.Option(30, "--days", help="Window size in days"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Weight trend, min/max and change over the last N days."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        entries = list(
            db.exec(
                select(WeightLog)
                .where(WeightLog.entry_date >= since)
                .order_by(WeightLog.entry_date, WeightLog.id)
            ).all()
        )
    if not entries:
        fail("No measurements in this window", json_out=json_out)
    weights = [e.weight_kg for e in entries]
    first, last = weights[0], weights[-1]
    change = round(last - first, 1)
    trend = "→ steady" if change == 0 else (f"↑ +{change}kg" if change > 0 else f"↓ {change}kg")
    data = {
        "window_days": days,
        "measurements": len(entries),
        "latest_kg": last,
        "min_kg": min(weights),
        "max_kg": max(weights),
        "avg_kg": round(sum(weights) / len(weights), 1),
        "change_kg": change,
        "trend": trend,
    }
    height_cm = get_setting(NAME, "height_cm")
    if height_cm:
        bmi = _bmi(last, float(height_cm))
        data["bmi"] = bmi
        data["bmi_class"] = _bmi_class(bmi)
    render_record(data, json_out=json_out, title=f"📊 Weight stats · last {days}d")
