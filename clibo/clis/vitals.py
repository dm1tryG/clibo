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


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context, json_out: JsonOpt = False) -> None:
    """Default: ``clibo vitals`` (bare) shows the latest reading of each kind."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(latest, json_out=json_out)


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
    systolic: str = typer.Argument(
        ...,
        help="Systolic pressure as an int (e.g. 120), or 'SYS/DIA' (e.g. '120/80')",
    ),
    diastolic: int = typer.Argument(
        None,
        help="Diastolic pressure (omit if systolic was passed as 'SYS/DIA')",
    ),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🩸 Log a blood-pressure reading.

    Accepts either ``clibo vitals bp 120 80`` or the canonical
    medical notation ``clibo vitals bp 120/80``.
    """
    # Parse: SYS/DIA passed as a single string, or two separate ints.
    if "/" in systolic:
        if diastolic is not None:
            fail(
                "Pass either 'SYS/DIA' OR systolic + diastolic separately, "
                "not both.",
                json_out=json_out,
            )
        parts = systolic.split("/", 1)
        try:
            sys_val = int(parts[0].strip())
            dia_val = int(parts[1].strip())
        except (ValueError, IndexError):
            fail(
                f"Bad blood-pressure format: {systolic!r}. "
                "Expected 'SYS/DIA' like '120/80'.",
                json_out=json_out,
            )
    else:
        try:
            sys_val = int(systolic)
        except ValueError:
            fail(
                f"Systolic must be an integer or 'SYS/DIA' notation; got "
                f"{systolic!r}.",
                json_out=json_out,
            )
        if diastolic is None:
            fail(
                "Missing diastolic pressure. Pass it as a second argument, "
                "or use 'SYS/DIA' notation like '120/80'.",
                json_out=json_out,
            )
        dia_val = diastolic
    data = _save(VitalReading(
        kind="bp", value=sys_val, value2=dia_val, unit="mmHg",
        entry_date=parse_date(on), note=note,
    ))
    ok(f"Logged 🩸 BP {sys_val}/{dia_val} mmHg — {data['category']}",
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


@app.command()
def log(
    kind: str = typer.Argument(
        ..., help=f"Which vital: {', '.join(KINDS)}"
    ),
    value: str = typer.Argument(
        ..., help="The reading. For BP: 'systolic/diastolic' or just systolic"
    ),
    value2: float = typer.Argument(
        None, help="(BP only, optional) diastolic if not given as VALUE/value2"
    ),
    unit: str = typer.Option(None, "--unit", "-u",
                              help="Override default unit (mainly for glucose mmol/L)"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """❤️ Log a vital reading — generic dispatcher.

    Lets you write ``clibo vitals log temp 39.2`` instead of
    ``clibo vitals temp 39.2`` — useful for agents whose mental
    model is *"every tool has a log verb"*. Routes to the right
    kind-specific writer under the hood.

    For blood pressure, supports both shapes:

      clibo vitals log bp 120/80
      clibo vitals log bp 120 80
    """
    kind = kind.lower()
    if kind not in KINDS:
        fail(f"Kind must be one of: {', '.join(KINDS)}", json_out=json_out)

    if kind == "bp":
        # Accept '120/80' as a single argument, or two separate ones.
        sys_val: float
        dia_val: float | None
        if "/" in value:
            try:
                sys_str, dia_str = value.split("/", 1)
                sys_val = float(sys_str)
                dia_val = float(dia_str)
            except ValueError:
                fail("BP must be 'systolic/diastolic' (e.g. 120/80)",
                     json_out=json_out)
        else:
            try:
                sys_val = float(value)
            except ValueError:
                fail(f"Value must be a number (got {value!r})", json_out=json_out)
            dia_val = value2
            if dia_val is None:
                fail("BP needs both systolic and diastolic — "
                     "try: clibo vitals log bp 120/80",
                     json_out=json_out)
        data = _save(VitalReading(
            kind="bp", value=sys_val, value2=dia_val,
            unit=unit or "mmHg", entry_date=parse_date(on), note=note,
        ))
        ok(f"Logged 🩸 BP {sys_val:g}/{dia_val:g} mmHg — {data['category']}",
           json_out=json_out, data=data)
        return

    if value2 is not None:
        fail(f"{kind} takes a single value, not two", json_out=json_out)
    try:
        numeric = float(value)
    except ValueError:
        fail(f"Value must be a number (got {value!r})", json_out=json_out)
    _, default_unit, emoji = KINDS[kind]
    chosen_unit = unit or default_unit
    data = _save(VitalReading(
        kind=kind, value=numeric, unit=chosen_unit,
        entry_date=parse_date(on), note=note,
    ))
    label = KINDS[kind][0].lower()
    ok(f"Logged {emoji} {label} {numeric:g} {chosen_unit}",
       json_out=json_out, data=data)


# `add` is the friendlier verb in agent flows — matches every other tool.
app.command(name="add", help="Alias for `log`")(log)


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

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
