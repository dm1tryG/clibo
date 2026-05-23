"""🚗 car — car maintenance & fuel log."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.clis.expense import get_currency, money
from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "car"
HELP = "🚗 Car maintenance & fuel log"
EMOJI = "🚗"
KINDS = ["fuel", "service"]


class CarEntry(SQLModel, table=True):
    """A fuel fill-up or a service / maintenance entry."""

    __tablename__ = "car_entry"

    id: int | None = Field(default=None, primary_key=True)
    kind: str
    entry_date: date = Field(default_factory=date.today, index=True)
    odometer: int | None = None
    volume: float | None = None
    cost: float = 0.0
    service: str | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _row(entry: CarEntry) -> dict:
    return {
        "id": entry.id,
        "entry_date": entry.entry_date,
        "kind": entry.kind,
        "odometer": entry.odometer,
        "volume": entry.volume,
        "cost": entry.cost,
        "service": entry.service,
        "note": entry.note,
    }


@app.command()
def fuel(
    volume: float = typer.Argument(..., help="Volume filled (litres or gallons)"),
    extra: float = typer.Argument(
        None,
        help="(Deprecated) Old positional form was `ODOMETER VOLUME` — if a "
             "second number is passed it is interpreted as the volume and the "
             "first as the odometer.",
        hidden=True,
    ),
    odometer: int = typer.Option(None, "--odometer", "-o",
                                  help="Odometer reading (km or mi) — optional, "
                                       "but needed for economy stats"),
    cost: float = typer.Option(0, "--cost", "-c", help="Total cost"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """⛽ Log a fuel fill-up.

    Volume is required; odometer is optional via `-o/--odometer` (without it,
    economy stats simply skip this fill-up). The old two-positional form
    `car fuel ODOMETER VOLUME` is still accepted for backward compatibility.
    """
    # Back-compat shim: if a second positional was passed, the first one was
    # actually the odometer (old signature: `fuel ODOMETER VOLUME`).
    if extra is not None:
        if odometer is not None:
            fail(
                "Pass odometer either positionally (old form) or with "
                "`-o/--odometer`, not both",
                json_out=json_out,
            )
        odometer = int(volume)
        volume = extra
    if volume <= 0 or cost < 0:
        fail("Volume and cost must be non-negative", json_out=json_out)
    if odometer is not None and odometer < 0:
        fail("Odometer must be non-negative", json_out=json_out)
    entry = CarEntry(
        kind="fuel", entry_date=parse_date(on), odometer=odometer,
        volume=volume, cost=cost, note=note,
    )
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        data = _row(entry)
    odo_str = f" @ {odometer}" if odometer is not None else ""
    cost_str = f" for {money(cost)}" if cost else ""
    ok(f"Logged {EMOJI} fuel — {volume:g}{odo_str}{cost_str}",
       json_out=json_out, data=data)


@app.command()
def service(
    name: str = typer.Argument(..., help="What was serviced"),
    cost: float = typer.Option(0, "--cost", "-c", help="Cost"),
    odometer: int = typer.Option(None, "--odometer", "-o", help="Odometer at the time"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🔧 Log a maintenance / service entry."""
    if cost < 0 or (odometer is not None and odometer < 0):
        fail("Cost and odometer must be non-negative", json_out=json_out)
    entry = CarEntry(
        kind="service", entry_date=parse_date(on), service=name,
        odometer=odometer, cost=cost, note=note,
    )
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        data = _row(entry)
    ok(f"Logged 🔧 {name}{' — ' + money(cost) if cost else ''}",
       json_out=json_out, data=data)


@app.command(name="list")
def list_entries(
    days: int = typer.Option(365, "--days", help="Look back this many days"),
    kind: str = typer.Option(None, "--kind", "-k", help="Filter: fuel / service"),
    json_out: JsonOpt = False,
) -> None:
    """🚗 List car entries."""
    if kind and kind.lower() not in KINDS:
        fail(f"Kind must be one of: {', '.join(KINDS)}", json_out=json_out)
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        query = select(CarEntry).where(CarEntry.entry_date >= since)
        if kind:
            query = query.where(CarEntry.kind == kind.lower())
        entries = list(
            db.exec(query.order_by(CarEntry.entry_date.desc(), CarEntry.id.desc())).all()
        )
    render_rows(
        [_row(e) for e in entries],
        [("id", "ID"), ("entry_date", "Date"), ("kind", "Kind"),
         ("odometer", "Odo"), ("volume", "Vol"), ("service", "Service"),
         ("cost", "Cost")],
        json_out=json_out,
        title="🚗 Car log",
        formatters={"cost": lambda v, r: money(v) if v else "[dim]—[/dim]"},
        empty="No car entries yet — try: clibo car fuel 45.5 -o 50000 -c 65",
    )


@app.command()
def rm(entry_id: int = typer.Argument(..., help="Entry ID"), json_out: JsonOpt = False) -> None:
    """🚗 Delete a car entry."""
    with session() as db:
        entry = db.get(CarEntry, entry_id)
        if not entry:
            fail(f"No car entry #{entry_id}", json_out=json_out)
        db.delete(entry)
    ok(f"Deleted car entry #{entry_id}", json_out=json_out, data={"deleted": entry_id})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Car stats — fuel and maintenance spending, plus economy."""
    with session() as db:
        entries = list(db.exec(select(CarEntry)).all())
    fuels = [e for e in entries if e.kind == "fuel"]
    services = [e for e in entries if e.kind == "service"]
    fuel_cost = round(sum(e.cost for e in fuels), 2)
    service_cost = round(sum(e.cost for e in services), 2)
    fuels_with_odo = sorted(
        [e for e in fuels if e.odometer is not None], key=lambda e: e.odometer
    )
    economy = None
    if len(fuels_with_odo) >= 2:
        distance = fuels_with_odo[-1].odometer - fuels_with_odo[0].odometer
        # Fuel consumed between fills excludes the first fill-up's volume.
        consumed = sum(e.volume for e in fuels_with_odo[1:] if e.volume)
        if distance > 0 and consumed > 0:
            economy = round(consumed / distance * 100, 2)  # L/100 (units assumed)
    data = {
        "fuel_entries": len(fuels),
        "service_entries": len(services),
        "fuel_spent": fuel_cost,
        "service_spent": service_cost,
        "total_spent": round(fuel_cost + service_cost, 2),
        "avg_economy_per_100": economy,
        "currency": get_currency(),
    }
    render_record(data, json_out=json_out, title="📊 Car stats")
