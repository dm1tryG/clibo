"""🐾 pets — pet care, feeding & vet log."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.clis.expense import get_currency, money
from clibo.core.base import humanize_delta, parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "pets"
HELP = "🐾 Pet care, feeding & vet log"
EMOJI = "🐾"
EVENT_KINDS = ["feeding", "vet", "grooming", "walk", "medication", "note"]


class Pet(SQLModel, table=True):
    """One of your pets."""

    __tablename__ = "pets_pet"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    species: str | None = None
    breed: str | None = None
    birth: date | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


class PetEvent(SQLModel, table=True):
    """A logged event for a pet — a feeding, vet visit, walk, etc."""

    __tablename__ = "pets_event"

    id: int | None = Field(default=None, primary_key=True)
    pet_id: int = Field(index=True)
    kind: str
    summary: str
    cost: float = 0.0
    entry_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context, json_out: JsonOpt = False) -> None:
    """Default: ``clibo pets`` (bare) lists every pet."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(list_pets, json_out=json_out)


def _resolve(db, ident: str) -> Pet | None:
    """Look up a pet by numeric ID or (case-insensitive) name match.

    Tries exact name first, then substring so `Whisk` finds `Whiskers`.
    """
    if ident.isdigit():
        pet = db.get(Pet, int(ident))
        if pet:
            return pet
    exact = db.exec(select(Pet).where(Pet.name.ilike(ident))).first()
    if exact:
        return exact
    return db.exec(select(Pet).where(Pet.name.ilike(f"%{ident}%"))).first()


def _age_years(birth: date | None) -> float | None:
    """Age in years (one decimal) from a birth date."""
    if birth is None:
        return None
    days = (date.today() - birth).days
    return round(days / 365.25, 1)


def _row(db, pet: Pet) -> dict:
    events = db.exec(select(PetEvent).where(PetEvent.pet_id == pet.id)).all()
    last_vet = max((e.entry_date for e in events if e.kind == "vet"), default=None)
    return {
        "id": pet.id,
        "name": pet.name,
        "species": pet.species,
        "breed": pet.breed,
        "birth": pet.birth,
        "age_years": _age_years(pet.birth),
        "events_logged": len(events),
        "last_vet": last_vet,
        "last_vet_ago": humanize_delta(last_vet) if last_vet else None,
        "notes": pet.notes,
    }


@app.command()
def add(
    name: str = typer.Argument(..., help="Pet name"),
    species: str = typer.Option(None, "--species", "-s", help="e.g. cat, dog"),
    breed: str = typer.Option(None, "--breed", "-b", help="Breed"),
    birth: str = typer.Option(None, "--birth", help="Birth date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🐾 Add a pet."""
    pet = Pet(
        name=name, species=species, breed=breed,
        birth=parse_date(birth) if birth else None, notes=note,
    )
    with session() as db:
        db.add(pet)
        db.flush()
        db.refresh(pet)
        data = _row(db, pet)
    extra = f" ({species})" if species else ""
    ok(f"Added {EMOJI} {name}{extra}", json_out=json_out, data=data)


@app.command(name="list")
def list_pets(json_out: JsonOpt = False) -> None:
    """🐾 List all pets."""
    with session() as db:
        pets = list(db.exec(select(Pet).order_by(Pet.name)).all())
        rows = [_row(db, p) for p in pets]
    render_rows(
        rows,
        [("id", "ID"), ("name", "Name"), ("species", "Species"),
         ("age_years", "Age"), ("events_logged", "Events"),
         ("last_vet_ago", "Last Vet")],
        json_out=json_out,
        title="🐾 Pets",
        empty="No pets yet — try: clibo pets add 'Whiskers' -s cat",
    )


@app.command()
def show(
    pet: str = typer.Argument(..., help="Pet name or ID"),
    days: int = typer.Option(30, "--days", help="Show events from the last N days"),
    json_out: JsonOpt = False,
) -> None:
    """🐾 Show a pet with their recent events."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        target = _resolve(db, pet)
        if not target:
            fail(f"No pet matching {pet!r}", json_out=json_out)
        data = _row(db, target)
        events = [
            {"id": e.id, "entry_date": e.entry_date, "kind": e.kind,
             "summary": e.summary, "cost": e.cost}
            for e in db.exec(
                select(PetEvent)
                .where(PetEvent.pet_id == target.id, PetEvent.entry_date >= since)
                .order_by(PetEvent.entry_date.desc(), PetEvent.id.desc())
            ).all()
        ]
    if json_out:
        render_record(data | {"events": events}, json_out=True)
        return
    render_record(data, json_out=False, title=f"🐾 {target.name}")
    render_rows(
        events,
        [("id", "ID"), ("entry_date", "Date"), ("kind", "Kind"),
         ("summary", "Summary"), ("cost", "Cost")],
        json_out=False,
        title=f"Events · last {days}d",
        formatters={"cost": lambda v, r: money(v) if v else "[dim]—[/dim]"},
        empty="No events yet — log one with: clibo pets log <pet> feeding 'morning meal'",
    )


@app.command()
def log(
    pet: str = typer.Argument(..., help="Pet name or ID"),
    kind: str = typer.Argument(..., help=f"{' / '.join(EVENT_KINDS)}"),
    summary: str = typer.Argument(
        "", help="What happened (defaults to the kind name if omitted)"
    ),
    cost: float = typer.Option(0, "--cost", "-c", help="Cost, if any"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    json_out: JsonOpt = False,
) -> None:
    """🐾 Log an event for a pet.

    `summary` is optional — if omitted, the row's summary defaults to the
    `kind` (e.g. just "vet"), so agents/users can log a quick event
    without inventing a description.
    """
    kind = kind.lower()
    if kind not in EVENT_KINDS:
        fail(f"Kind must be one of: {', '.join(EVENT_KINDS)}", json_out=json_out)
    if cost < 0:
        fail("Cost cannot be negative", json_out=json_out)
    summary_text = summary.strip() if summary else kind
    with session() as db:
        target = _resolve(db, pet)
        if not target:
            fail(f"No pet matching {pet!r}", json_out=json_out)
        event = PetEvent(pet_id=target.id, kind=kind, summary=summary_text,
                         cost=cost, entry_date=parse_date(on))
        db.add(event)
        db.flush()
        db.refresh(event)
        data = {"id": event.id, "pet": target.name, "kind": kind,
                "summary": summary_text, "cost": cost,
                "entry_date": event.entry_date}
    ok(f"Logged 🐾 {target.name} · {kind}: {summary_text}",
       json_out=json_out, data=data)


@app.command()
def edit(
    pet: str = typer.Argument(..., help="Pet name or ID"),
    name: str = typer.Option(None, "--name", help="New name"),
    species: str = typer.Option(None, "--species", "-s",
                                  help="New species (cat / dog / …)"),
    breed: str = typer.Option(None, "--breed", "-b", help="New breed"),
    birth: str = typer.Option(None, "--birth", help="New birth date"),
    note: str = typer.Option(None, "--note", "-n", help="New note"),
    json_out: JsonOpt = False,
) -> None:
    """🐾 Edit a pet's profile. Accepts a numeric ID or a name."""
    with session() as db:
        target = _resolve(db, pet)
        if not target:
            fail(f"No pet matching {pet!r}", json_out=json_out)
        if name is not None:
            target.name = name
        if species is not None:
            target.species = species.lower().strip() or None
        if breed is not None:
            target.breed = breed
        if birth is not None:
            target.birth = parse_date(birth)
        if note is not None:
            target.notes = note
        db.add(target)
        db.flush()
        data = _row(db, target)
    ok(f"Updated pet #{target.id} — {target.name}",
       json_out=json_out, data=data)


@app.command()
def events(
    days: int = typer.Option(14, "--days", help="Look back this many days"),
    json_out: JsonOpt = False,
) -> None:
    """📋 Recent events across all pets."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        rows = list(
            db.exec(
                select(PetEvent)
                .where(PetEvent.entry_date >= since)
                .order_by(PetEvent.entry_date.desc(), PetEvent.id.desc())
            ).all()
        )
        names = {p.id: p.name for p in db.exec(select(Pet)).all()}
    output = [
        {"id": e.id, "entry_date": e.entry_date, "pet": names.get(e.pet_id, "?"),
         "kind": e.kind, "summary": e.summary, "cost": e.cost}
        for e in rows
    ]
    render_rows(
        output,
        [("entry_date", "Date"), ("pet", "Pet"), ("kind", "Kind"),
         ("summary", "Summary"), ("cost", "Cost")],
        json_out=json_out,
        title=f"📋 Pet events · last {days}d",
        formatters={"cost": lambda v, r: money(v) if v else "[dim]—[/dim]"},
        empty="No events logged.",
    )


@app.command()
def rm(
    pet: str = typer.Argument(..., help="Pet name or ID"),
    json_out: JsonOpt = False,
) -> None:
    """🐾 Delete a pet and their event history."""
    with session() as db:
        target = _resolve(db, pet)
        if not target:
            fail(f"No pet matching {pet!r}", json_out=json_out)
        pid = target.id
        for event in db.exec(select(PetEvent).where(PetEvent.pet_id == pid)).all():
            db.delete(event)
        db.delete(target)
    ok(f"Deleted pet #{pid}", json_out=json_out, data={"deleted": pid})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Pet stats — counts and total spending on care."""
    with session() as db:
        pets = list(db.exec(select(Pet)).all())
        all_events = list(db.exec(select(PetEvent)).all())
    by_kind = {k: sum(1 for e in all_events if e.kind == k) for k in EVENT_KINDS}
    data = {
        "pets": len(pets),
        "events": len(all_events),
        "spent": round(sum(e.cost for e in all_events), 2),
        "by_kind": by_kind,
        "currency": get_currency(),
    }
    render_record(data, json_out=json_out, title="📊 Pet stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `update` is the SQL-natural synonym for `edit`; both work.
app.command(name="update", help="Alias for `edit`")(edit)

# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
