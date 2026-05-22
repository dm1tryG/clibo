"""❤️ vitals — blood pressure, pulse, glucose & more."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "vitals"
HELP = "❤️ Blood pressure, pulse & glucose log"
EMOJI = "❤️"

#: kind -> (label, default unit, emoji)
KINDS: dict[str, tuple[str, str, str]] = {
    "bp": ("Blood pressure", "mmHg", "🩸"),
    "pulse": ("Pulse", "bpm", "💓"),
    "glucose": ("Glucose", "mg/dL", "🩸"),
    "temp": ("Temperature", "°C", "🌡️"),
    "spo2": ("Blood oxygen", "%", "🫁"),
}


class VitalReading(SQLModel, table=True):
    """One vital-sign reading. ``value2`` holds the diastolic part of a BP."""

    __tablename__ = "vitals_reading"

    id: int | None = Field(default=None, primary_key=True)
    kind: str = Field(index=True)
    value: float
    value2: float | None = None
    unit: str
    entry_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    note: str | None = None


app = typer.Typer(no_args_is_help=True, help=HELP)


def _bp_class(systolic: float, diastolic: float) -> str:
    """WHO/AHA blood-pressure category for a systolic/diastolic pair."""
    if systolic > 180 or diastolic > 120:
        return "hypertensive crisis"
    if systolic >= 140 or diastolic >= 90:
        return "stage 2 hypertension"
    if systolic >= 130 or diastolic >= 80:
        return "stage 1 hypertension"
    if systolic >= 120:
        return "elevated"
    return "normal"


def _display(reading: VitalReading) -> str:
    """Human-readable value, e.g. ``120/80 mmHg`` or ``72 bpm``."""
    if reading.kind == "bp" and reading.value2 is not None:
        return f"{reading.value:g}/{reading.value2:g} {reading.unit}"
    return f"{reading.value:g} {reading.unit}"


def _row(reading: VitalReading) -> dict:
    row = {
        "id": reading.id,
        "kind": reading.kind,
        "entry_date": reading.entry_date,
        "value": reading.value,
        "value2": reading.value2,
        "unit": reading.unit,
        "reading": _display(reading),
        "note": reading.note,
    }
    if reading.kind == "bp" and reading.value2 is not None:
        row["category"] = _bp_class(reading.value, reading.value2)
    return row


def _save(reading: VitalReading) -> dict:
    with session() as db:
        db.add(reading)
        db.flush()
        db.refresh(reading)
        return _row(reading)


@app.command()
def bp(
    systolic: int = typer.Argument(..., help="Systolic pressure"),
    diastolic: int = typer.Argument(..., help="Diastolic pressure"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🩸 Log a blood-pressure reading."""
    data = _save(VitalReading(
        kind="bp", value=systolic, value2=diastolic, unit="mmHg",
        entry_date=parse_date(on), note=note,
    ))
    ok(f"Logged 🩸 BP {systolic}/{diastolic} mmHg — {data['category']}",
       json_out=json_out, data=data)


@app.command()
def pulse(
    bpm: int = typer.Argument(..., help="Heart rate in beats per minute"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """💓 Log a pulse / heart-rate reading."""
    data = _save(VitalReading(kind="pulse", value=bpm, unit="bpm",
                              entry_date=parse_date(on), note=note))
    ok(f"Logged 💓 pulse {bpm} bpm", json_out=json_out, data=data)


@app.command()
def glucose(
    value: float = typer.Argument(..., help="Blood glucose value"),
    unit: str = typer.Option("mg/dL", "--unit", "-u", help="mg/dL or mmol/L"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🩸 Log a blood-glucose reading."""
    data = _save(VitalReading(kind="glucose", value=value, unit=unit,
                              entry_date=parse_date(on), note=note))
    ok(f"Logged 🩸 glucose {value:g} {unit}", json_out=json_out, data=data)


@app.command()
def temp(
    celsius: float = typer.Argument(..., help="Body temperature in °C"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🌡️ Log a body-temperature reading."""
    data = _save(VitalReading(kind="temp", value=celsius, unit="°C",
                              entry_date=parse_date(on), note=note))
    ok(f"Logged 🌡️ temperature {celsius:g} °C", json_out=json_out, data=data)


@app.command()
def spo2(
    percent: float = typer.Argument(..., help="Blood-oxygen saturation %"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🫁 Log a blood-oxygen (SpO₂) reading."""
    data = _save(VitalReading(kind="spo2", value=percent, unit="%",
                              entry_date=parse_date(on), note=note))
    ok(f"Logged 🫁 SpO₂ {percent:g}%", json_out=json_out, data=data)


@app.command(name="list")
def list_entries(
    kind: str = typer.Option(None, "--kind", "-k", help=f"Filter: {', '.join(KINDS)}"),
    days: int = typer.Option(14, "--days", help="Look back this many days"),
    json_out: JsonOpt = False,
) -> None:
    """❤️ List recent vital readings."""
    if kind and kind not in KINDS:
        fail(f"Kind must be one of: {', '.join(KINDS)}", json_out=json_out)
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        query = select(VitalReading).where(VitalReading.entry_date >= since)
        if kind:
            query = query.where(VitalReading.kind == kind)
        readings = list(
            db.exec(query.order_by(VitalReading.entry_date.desc(), VitalReading.id.desc())).all()
        )
    render_rows(
        [_row(r) for r in readings],
        [("id", "ID"), ("entry_date", "Date"), ("kind", "Kind"),
         ("reading", "Reading"), ("note", "Note")],
        json_out=json_out,
        title="❤️ Vital readings",
        empty="No readings yet — try: clibo vitals bp 120 80",
    )


@app.command()
def latest(json_out: JsonOpt = False) -> None:
    """❤️ Show the most recent reading of each vital sign."""
    result = {}
    with session() as db:
        for kind in KINDS:
            reading = db.exec(
                select(VitalReading)
                .where(VitalReading.kind == kind)
                .order_by(VitalReading.created_at.desc())
            ).first()
            if reading:
                result[kind] = _row(reading)
    if json_out:
        render_record(result, json_out=True)
        return
    rows = [
        {"kind": KINDS[k][0], "reading": v["reading"], "date": v["entry_date"],
         "category": v.get("category")}
        for k, v in result.items()
    ]
    render_rows(
        rows,
        [("kind", "Vital"), ("reading", "Latest"), ("date", "Date"), ("category", "Note")],
        json_out=False,
        title="❤️ Latest vitals",
        empty="No readings yet — try: clibo vitals pulse 72",
    )


@app.command()
def rm(reading_id: int = typer.Argument(..., help="Reading ID"), json_out: JsonOpt = False) -> None:
    """❤️ Delete a vital reading."""
    with session() as db:
        reading = db.get(VitalReading, reading_id)
        if not reading:
            fail(f"No reading #{reading_id}", json_out=json_out)
        db.delete(reading)
    ok(f"Deleted reading #{reading_id}", json_out=json_out, data={"deleted": reading_id})


@app.command()
def stats(
    kind: str = typer.Argument(..., help=f"Which vital: {', '.join(KINDS)}"),
    days: int = typer.Option(30, "--days", help="Window size in days"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Stats for one vital sign over the last N days."""
    if kind not in KINDS:
        fail(f"Kind must be one of: {', '.join(KINDS)}", json_out=json_out)
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        readings = list(
            db.exec(
                select(VitalReading)
                .where(VitalReading.kind == kind, VitalReading.entry_date >= since)
            ).all()
        )
    if not readings:
        fail(f"No {kind} readings in this window", json_out=json_out)
    values = [r.value for r in readings]
    data = {
        "kind": kind,
        "window_days": days,
        "readings": len(readings),
        "avg": round(sum(values) / len(values), 1),
        "min": min(values),
        "max": max(values),
        "unit": readings[0].unit,
    }
    if kind == "bp":
        dia = [r.value2 for r in readings if r.value2 is not None]
        if dia:
            data["avg_diastolic"] = round(sum(dia) / len(dia), 1)
            data["avg_systolic"] = data.pop("avg")
    render_record(data, json_out=json_out, title=f"📊 {KINDS[kind][0]} stats · last {days}d")
