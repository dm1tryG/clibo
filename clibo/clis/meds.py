"""💊 meds — medication log & dosage reminders."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "meds"
HELP = "💊 Medication log & dosage reminders"
EMOJI = "💊"


class Medication(SQLModel, table=True):
    """A medication you take, with its dosage and daily frequency."""

    __tablename__ = "meds_medication"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    dosage: str | None = None
    times_per_day: int = 1
    note: str | None = None
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)


class MedDose(SQLModel, table=True):
    """A single dose taken of a medication."""

    __tablename__ = "meds_dose"

    id: int | None = Field(default=None, primary_key=True)
    med_id: int = Field(index=True)
    taken_at: datetime = Field(default_factory=datetime.now)
    entry_date: date = Field(default_factory=date.today, index=True)
    note: str | None = None


app = typer.Typer(no_args_is_help=True, help=HELP)


def _resolve(db, ident: str) -> Medication | None:
    """Look up a medication by numeric ID or by (case-insensitive) name."""
    if ident.isdigit():
        med = db.get(Medication, int(ident))
        if med:
            return med
    return db.exec(select(Medication).where(Medication.name.ilike(ident))).first()


def _doses_on(db, med_id: int, day: date) -> int:
    """How many doses of a medication were taken on a given day."""
    return len(
        db.exec(
            select(MedDose).where(MedDose.med_id == med_id, MedDose.entry_date == day)
        ).all()
    )


@app.command()
def add(
    name: str = typer.Argument(..., help="Medication name, e.g. 'Vitamin D'"),
    dosage: str = typer.Option(None, "--dosage", "-d", help="Dosage, e.g. '500mg'"),
    times: int = typer.Option(1, "--times", "-t", help="Times to take per day"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """💊 Register a medication you take."""
    if times < 1:
        fail("Times per day must be at least 1", json_out=json_out)
    med = Medication(name=name, dosage=dosage, times_per_day=times, note=note)
    with session() as db:
        db.add(med)
        db.flush()
        db.refresh(med)
        data = {
            "id": med.id,
            "name": med.name,
            "dosage": med.dosage,
            "times_per_day": med.times_per_day,
        }
    ok(f"Added {EMOJI} {name}" + (f" ({dosage})" if dosage else ""),
       json_out=json_out, data=data)


@app.command()
def take(
    medication: str = typer.Argument(..., help="Medication name or ID"),
    on: str = typer.Option("today", "--date", "-d", help="Date taken"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """💊 Log that you took a dose."""
    with session() as db:
        med = _resolve(db, medication)
        if not med:
            fail(f"No medication matching {medication!r}", json_out=json_out)
        dose = MedDose(med_id=med.id, entry_date=parse_date(on), note=note)
        db.add(dose)
        db.flush()
        taken = _doses_on(db, med.id, dose.entry_date)
        data = {
            "id": dose.id,
            "medication": med.name,
            "taken_today": taken,
            "times_per_day": med.times_per_day,
        }
    suffix = "✅ all done" if taken >= med.times_per_day else f"{taken}/{med.times_per_day} today"
    ok(f"Took {EMOJI} {med.name} — {suffix}", json_out=json_out, data=data)


@app.command()
def today(json_out: JsonOpt = False) -> None:
    """💊 Show today's medications and what's still due."""
    day = date.today()
    with session() as db:
        meds = list(
            db.exec(
                select(Medication).where(Medication.active == True).order_by(Medication.name)  # noqa: E712
            ).all()
        )
        doses = list(db.exec(select(MedDose).where(MedDose.entry_date == day)).all())
    taken_by: dict[int, int] = {}
    for dose in doses:
        taken_by[dose.med_id] = taken_by.get(dose.med_id, 0) + 1
    rows = []
    for med in meds:
        taken = taken_by.get(med.id, 0)
        rows.append({
            "id": med.id,
            "medication": med.name,
            "dosage": med.dosage,
            "taken": taken,
            "times_per_day": med.times_per_day,
            "done": taken >= med.times_per_day,
            "remaining": max(0, med.times_per_day - taken),
        })
    if json_out:
        render_record({"date": day, "medications": rows}, json_out=True)
        return
    render_rows(
        rows,
        [("medication", "Medication"), ("dosage", "Dosage"),
         ("taken", "Progress"), ("done", "Status")],
        json_out=False,
        title=f"💊 Medications · {day:%a %d %b}",
        formatters={
            "taken": lambda v, r: f"{v}/{r['times_per_day']}",
            "done": lambda v, r: "[green]✅ done[/green]" if v
            else f"[yellow]⏳ {r['remaining']} left[/yellow]",
        },
        empty="No active medications — add one with: clibo meds add 'Vitamin D'",
    )


@app.command(name="list")
def list_meds(
    show_all: bool = typer.Option(False, "--all", help="Include stopped medications"),
    json_out: JsonOpt = False,
) -> None:
    """💊 List your medications."""
    with session() as db:
        query = select(Medication)
        if not show_all:
            query = query.where(Medication.active == True)  # noqa: E712
        meds = list(db.exec(query.order_by(Medication.name)).all())
    rows = [
        {"id": m.id, "name": m.name, "dosage": m.dosage,
         "times_per_day": m.times_per_day, "active": m.active, "note": m.note}
        for m in meds
    ]
    render_rows(
        rows,
        [("id", "ID"), ("name", "Name"), ("dosage", "Dosage"),
         ("times_per_day", "Per Day"), ("active", "Active"), ("note", "Note")],
        json_out=json_out,
        title="💊 Medications",
        empty="No medications yet — add one with: clibo meds add 'Vitamin D'",
    )


@app.command()
def history(
    days: int = typer.Option(7, "--days", help="Look back this many days"),
    json_out: JsonOpt = False,
) -> None:
    """💊 Recent dose history."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        doses = list(
            db.exec(
                select(MedDose)
                .where(MedDose.entry_date >= since)
                .order_by(MedDose.taken_at.desc())
            ).all()
        )
        names = {m.id: m.name for m in db.exec(select(Medication)).all()}
    rows = [
        {"id": d.id, "entry_date": d.entry_date, "medication": names.get(d.med_id, "?"),
         "taken_at": d.taken_at, "note": d.note}
        for d in doses
    ]
    render_rows(
        rows,
        [("id", "ID"), ("entry_date", "Date"), ("medication", "Medication"),
         ("taken_at", "Taken At"), ("note", "Note")],
        json_out=json_out,
        title="💊 Dose history",
        empty="No doses logged yet.",
    )


@app.command()
def stop(med_id: int = typer.Argument(..., help="Medication ID"), json_out: JsonOpt = False) -> None:
    """💊 Stop a medication (keeps its history)."""
    with session() as db:
        med = db.get(Medication, med_id)
        if not med:
            fail(f"No medication #{med_id}", json_out=json_out)
        med.active = False
        db.add(med)
    ok(f"Stopped {EMOJI} {med.name}", json_out=json_out, data={"id": med_id, "active": False})


@app.command()
def rm(med_id: int = typer.Argument(..., help="Medication ID"), json_out: JsonOpt = False) -> None:
    """💊 Delete a medication and all its dose history."""
    with session() as db:
        med = db.get(Medication, med_id)
        if not med:
            fail(f"No medication #{med_id}", json_out=json_out)
        for dose in db.exec(select(MedDose).where(MedDose.med_id == med_id)).all():
            db.delete(dose)
        db.delete(med)
    ok(f"Deleted medication #{med_id}", json_out=json_out, data={"deleted": med_id})


@app.command()
def stats(
    days: int = typer.Option(7, "--days", help="Window size in days"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Medication adherence over the last N days."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        meds = list(
            db.exec(select(Medication).where(Medication.active == True)).all()  # noqa: E712
        )
        doses = list(db.exec(select(MedDose).where(MedDose.entry_date >= since)).all())
    expected = sum(m.times_per_day for m in meds) * days
    taken = len(doses)
    data = {
        "window_days": days,
        "active_medications": len(meds),
        "doses_taken": taken,
        "doses_expected": expected,
        "adherence_pct": round(taken / expected * 100) if expected else 0,
    }
    render_record(data, json_out=json_out, title=f"📊 Meds stats · last {days}d")
