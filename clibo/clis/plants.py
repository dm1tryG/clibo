"""🪴 plants — plant care & watering schedule."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import humanize_delta
from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "plants"
HELP = "🪴 Plant care & watering schedule"
EMOJI = "🪴"


class Plant(SQLModel, table=True):
    """A houseplant with a watering schedule."""

    __tablename__ = "plants_plant"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    species: str | None = None
    water_every_days: int = 7
    last_watered: date | None = None
    location: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context) -> None:
    """Default: ``clibo plants`` (bare) runs the ``thirsty`` summary."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(thirsty, json_out=False)


def _resolve(db, ident: str) -> Plant | None:
    """Look up a plant by numeric ID or (case-insensitive) name match.

    Tries exact name first, then substring so `Bas` finds `Basil`.
    """
    if ident.isdigit():
        plant = db.get(Plant, int(ident))
        if plant:
            return plant
    exact = db.exec(select(Plant).where(Plant.name.ilike(ident))).first()
    if exact:
        return exact
    return db.exec(
        select(Plant).where(Plant.name.ilike(f"%{ident}%"))
    ).first()


def _next_water(plant: Plant) -> date:
    """When the plant next needs water (today if never watered)."""
    if plant.last_watered is None:
        return date.today()
    return plant.last_watered + timedelta(days=plant.water_every_days)


def _status(plant: Plant) -> str:
    days = (_next_water(plant) - date.today()).days
    if days < 0:
        return "thirsty"
    if days == 0:
        return "water today"
    return "ok"


def _row(plant: Plant) -> dict:
    nxt = _next_water(plant)
    return {
        "id": plant.id,
        "name": plant.name,
        "species": plant.species,
        "location": plant.location,
        "water_every_days": plant.water_every_days,
        "last_watered": plant.last_watered,
        "next_water": nxt,
        "water_in": humanize_delta(nxt),
        "status": _status(plant),
    }


def _status_cell(status: str) -> str:
    return {
        "thirsty": "[red]⚠ thirsty[/red]",
        "water today": "[yellow]💧 water today[/yellow]",
        "ok": "[green]ok[/green]",
    }.get(status, status)


@app.command()
def add(
    name: str = typer.Argument(..., help="Plant name, e.g. 'Monstera'"),
    water_every: int = typer.Option(7, "--water-every", "-w", help="Water every N days"),
    species: str = typer.Option(None, "--species", "-s", help="Plant species"),
    location: str = typer.Option(None, "--location", "-l", help="Where it lives"),
    json_out: JsonOpt = False,
) -> None:
    """🪴 Add a plant to care for."""
    if water_every < 1:
        fail("Watering frequency must be at least 1 day", json_out=json_out)
    plant = Plant(name=name, species=species, water_every_days=water_every, location=location)
    with session() as db:
        db.add(plant)
        db.flush()
        db.refresh(plant)
        data = _row(plant)
    ok(f"Added {EMOJI} {name} (water every {water_every}d)", json_out=json_out, data=data)


@app.command(name="list")
def list_plants(json_out: JsonOpt = False) -> None:
    """🪴 List plants, thirstiest first."""
    with session() as db:
        plants = list(db.exec(select(Plant)).all())
    rows = sorted((_row(p) for p in plants), key=lambda r: r["next_water"])
    render_rows(
        rows,
        [("id", "ID"), ("name", "Plant"), ("location", "Location"),
         ("water_every_days", "Every"), ("next_water", "Next Water"),
         ("water_in", "When"), ("status", "Status")],
        json_out=json_out,
        title="🪴 Plants",
        formatters={
            "water_every_days": lambda v, r: f"{v}d",
            "status": lambda v, r: _status_cell(v),
        },
        empty="No plants yet — try: clibo plants add 'Monstera' -w 7",
    )


@app.command()
def water(
    plant: str = typer.Argument(..., help="Plant name or ID"),
    json_out: JsonOpt = False,
) -> None:
    """💧 Mark a plant as watered today."""
    with session() as db:
        target = _resolve(db, plant)
        if not target:
            fail(f"No plant matching {plant!r}", json_out=json_out)
        target.last_watered = date.today()
        db.add(target)
        db.flush()
        data = _row(target)
    ok(f"Watered {EMOJI} {target.name} — next on {data['next_water']}",
       json_out=json_out, data=data)


@app.command()
def thirsty(json_out: JsonOpt = False) -> None:
    """🔔 Plants that need watering now."""
    with session() as db:
        plants = list(db.exec(select(Plant)).all())
    rows = sorted(
        (r for p in plants if (r := _row(p))["status"] in ("thirsty", "water today")),
        key=lambda r: r["next_water"],
    )
    render_rows(
        rows,
        [("id", "ID"), ("name", "Plant"), ("location", "Location"),
         ("water_in", "When"), ("status", "Status")],
        json_out=json_out,
        title="🔔 Plants needing water",
        formatters={"status": lambda v, r: _status_cell(v)},
        empty="Every plant is happy and watered! 🌿",
    )


@app.command()
def edit(
    plant: str = typer.Argument(..., help="Plant name or ID"),
    name: str = typer.Option(None, "--name", help="New name"),
    location: str = typer.Option(None, "--location", "-l", help="New location"),
    water_every: int = typer.Option(None, "--water-every", "-w",
                                     help="Water every N days"),
    note: str = typer.Option(None, "--note", "-n", help="New note"),
    json_out: JsonOpt = False,
) -> None:
    """🪴 Edit a plant. Accepts a numeric ID or a name."""
    with session() as db:
        target = _resolve(db, plant)
        if not target:
            fail(f"No plant matching {plant!r}", json_out=json_out)
        if name is not None:
            target.name = name
        if location is not None:
            target.location = location
        if water_every is not None:
            if water_every <= 0:
                fail("Water-every must be positive", json_out=json_out)
            target.water_every_days = water_every
        if note is not None:
            target.note = note
        db.add(target)
        db.flush()
        data = _row(target)
    ok(f"Updated plant #{target.id}", json_out=json_out, data=data)


@app.command()
def rm(
    plant: str = typer.Argument(..., help="Plant name or ID"),
    json_out: JsonOpt = False,
) -> None:
    """🪴 Delete a plant."""
    with session() as db:
        target = _resolve(db, plant)
        if not target:
            fail(f"No plant matching {plant!r}", json_out=json_out)
        pid = target.id
        db.delete(target)
    ok(f"Deleted plant #{pid}", json_out=json_out, data={"deleted": pid})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Plant-care stats."""
    with session() as db:
        plants = list(db.exec(select(Plant)).all())
    rows = [_row(p) for p in plants]
    data = {
        "total": len(plants),
        "thirsty": sum(1 for r in rows if r["status"] == "thirsty"),
        "water_today": sum(1 for r in rows if r["status"] == "water today"),
        "locations": len({p.location for p in plants if p.location}),
    }
    render_record(data, json_out=json_out, title="📊 Plant stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `update` is the SQL-natural synonym for `edit`; both work.
app.command(name="update", help="Alias for `edit`")(edit)

# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
