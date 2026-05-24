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
HELP = "🚗 Car maintenance, fuel & driving log"
EMOJI = "🚗"
KINDS = ["fuel", "service"]
DRIVE_CATEGORIES = ["business", "personal", "commute"]


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


class CarDrive(SQLModel, table=True):
    """One trip in the car — purpose, distance, business/personal category.

    Distinct from ``CarEntry`` because the column shape is different and
    business-vs-personal categorisation is the whole point. Useful for
    deducting business mileage at tax time (most tax authorities allow
    a per-km / per-mile rate — keep this rate out of the tool and let
    users do the math with whatever rate applies in their jurisdiction).
    """

    __tablename__ = "car_drive"

    id: int | None = Field(default=None, primary_key=True)
    purpose: str
    distance_km: float
    category: str = "personal"          # business / personal / commute
    odometer_start: int | None = None
    odometer_end: int | None = None
    entry_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    note: str | None = None


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


def _drive_row(drive: CarDrive) -> dict:
    return {
        "id": drive.id,
        "entry_date": drive.entry_date,
        "kind": "drive",  # mirrors CarEntry.kind for unified rendering
        "purpose": drive.purpose,
        "distance_km": drive.distance_km,
        "category": drive.category,
        "odometer_start": drive.odometer_start,
        "odometer_end": drive.odometer_end,
        "note": drive.note,
    }


@app.command()
def drive(
    purpose: str = typer.Argument(..., help="What the trip was for (e.g. 'client meeting')"),
    distance_km: float = typer.Option(
        None, "--km", "-k",
        help="Distance driven in km (use --mi for miles)",
    ),
    distance_mi: float = typer.Option(
        None, "--mi", help="Distance driven in miles (converted to km)"
    ),
    category: str = typer.Option(
        "personal", "--category", "-c",
        help=f"One of: {', '.join(DRIVE_CATEGORIES)}",
    ),
    odometer_start: int = typer.Option(
        None, "--start-odo", help="Start odometer reading"
    ),
    odometer_end: int = typer.Option(
        None, "--end-odo", help="End odometer reading (auto-computes distance)"
    ),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🚗 Log a car trip — purpose, distance, business / personal / commute.

    Distance can come from any of:

    \b
      --km 47          explicit kilometres
      --mi 30          explicit miles (converted)
      --start-odo / --end-odo   pair of odometer readings (km)

    Categorising as ``business`` separates trips that are typically tax-
    deductible (most jurisdictions allow a per-km or per-mile rate at
    filing time).
    """
    category = category.lower()
    if category not in DRIVE_CATEGORIES:
        fail(f"Category must be one of: {', '.join(DRIVE_CATEGORIES)}",
             json_out=json_out)
    # Resolve distance from any of the supplied inputs.
    if distance_km is None and distance_mi is not None:
        distance_km = round(distance_mi * 1.609344, 2)
    if distance_km is None and odometer_start is not None and odometer_end is not None:
        distance_km = float(odometer_end - odometer_start)
    if distance_km is None:
        fail("Provide --km, --mi, or both odometer readings",
             json_out=json_out)
    if distance_km < 0:
        fail("Distance cannot be negative", json_out=json_out)
    if odometer_start is not None and odometer_end is not None \
            and odometer_end < odometer_start:
        fail("End odometer must be ≥ start odometer", json_out=json_out)
    trip = CarDrive(
        purpose=purpose.strip(),
        distance_km=round(distance_km, 2),
        category=category,
        odometer_start=odometer_start,
        odometer_end=odometer_end,
        entry_date=parse_date(on),
        note=note,
    )
    with session() as db:
        db.add(trip)
        db.flush()
        db.refresh(trip)
        data = _drive_row(trip)
    ok(f"Logged 🚗 {purpose} — {distance_km:g} km ({category})",
       json_out=json_out, data=data)


_KINDS_ALL = [*KINDS, "drive"]


@app.command(name="list")
def list_entries(
    days: int = typer.Option(365, "--days", help="Look back this many days"),
    kind: str = typer.Option(None, "--kind", "-k",
                              help=f"Filter: {' / '.join(_KINDS_ALL)}"),
    json_out: JsonOpt = False,
) -> None:
    """🚗 List car entries (fuel, service, and drive trips)."""
    if kind and kind.lower() not in _KINDS_ALL:
        fail(f"Kind must be one of: {', '.join(_KINDS_ALL)}",
             json_out=json_out)
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        rows: list[dict] = []
        if kind is None or kind.lower() != "drive":
            query = select(CarEntry).where(CarEntry.entry_date >= since)
            if kind and kind.lower() in KINDS:
                query = query.where(CarEntry.kind == kind.lower())
            entries = list(
                db.exec(query.order_by(CarEntry.entry_date.desc(), CarEntry.id.desc())).all()
            )
            for e in entries:
                rows.append(_row(e) | {"_sort_id": e.id})
        if kind is None or kind.lower() == "drive":
            drives = list(
                db.exec(
                    select(CarDrive)
                    .where(CarDrive.entry_date >= since)
                    .order_by(CarDrive.entry_date.desc(), CarDrive.id.desc())
                ).all()
            )
            for d in drives:
                rows.append(_drive_row(d) | {"_sort_id": d.id})
    # Merge sort across both tables: newest first, with id as tiebreak.
    rows.sort(key=lambda r: (r["entry_date"], r.get("_sort_id", 0)), reverse=True)
    for r in rows:
        r.pop("_sort_id", None)
    render_rows(
        rows,
        [("id", "ID"), ("entry_date", "Date"), ("kind", "Kind"),
         ("purpose", "Purpose / Service"), ("distance_km", "Km"),
         ("volume", "Vol"), ("cost", "Cost"), ("category", "Cat")],
        json_out=json_out,
        title="🚗 Car log",
        formatters={
            "cost": lambda v, r: money(v) if v else "[dim]—[/dim]",
            "distance_km": lambda v, r: (f"{v:g}" if v else "[dim]—[/dim]"),
            "category": lambda v, r: v or "[dim]—[/dim]",
            # Show 'service' (CarEntry) or 'purpose' (CarDrive) under one column.
            "purpose": lambda v, r: v or r.get("service") or "[dim]—[/dim]",
        },
        empty="No car entries yet — try: clibo car fuel 45.5 -o 50000 -c 65",
    )


@app.command()
def rm(
    entry_id: int = typer.Argument(..., help="Entry ID"),
    drive: bool = typer.Option(
        False, "--drive",
        help="Delete a drive entry instead of a fuel/service entry "
             "(IDs are separate per table)",
    ),
    json_out: JsonOpt = False,
) -> None:
    """🚗 Delete a car entry. Use ``--drive`` to delete a trip row."""
    with session() as db:
        if drive:
            target = db.get(CarDrive, entry_id)
            if not target:
                fail(f"No car drive #{entry_id}", json_out=json_out)
            db.delete(target)
        else:
            target = db.get(CarEntry, entry_id)
            if not target:
                fail(f"No car entry #{entry_id}", json_out=json_out)
            db.delete(target)
    ok(f"Deleted car entry #{entry_id}", json_out=json_out, data={"deleted": entry_id})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Car stats — fuel + service spending, plus economy & driving."""
    with session() as db:
        entries = list(db.exec(select(CarEntry)).all())
        drives = list(db.exec(select(CarDrive)).all())
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
    # Driving rollup by category for tax-friendly visibility.
    drive_total_km = round(sum(d.distance_km for d in drives), 2)
    by_cat: dict[str, float] = {}
    for d in drives:
        by_cat[d.category] = round(
            by_cat.get(d.category, 0) + d.distance_km, 2
        )
    data = {
        "fuel_entries": len(fuels),
        "service_entries": len(services),
        "fuel_spent": fuel_cost,
        "service_spent": service_cost,
        "total_spent": round(fuel_cost + service_cost, 2),
        "avg_economy_per_100": economy,
        "drive_entries": len(drives),
        "drive_total_km": drive_total_km,
        "drive_by_category": [
            {"category": c, "km": km}
            for c, km in sorted(by_cat.items(), key=lambda kv: -kv[1])
        ],
        "currency": get_currency(),
    }
    render_record(data, json_out=json_out, title="📊 Car stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)
