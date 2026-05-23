"""🤒 symptom — structured pain & symptom tracker.

Distinct from the existing health tools:

- **`vitals`** stores measurable readings (BP, pulse, glucose, SpO2).
- **`mood`** is whole-person 1-5, not per body-area or kind.
- **`journal`** is freeform text — no aggregation, no intensity trend.

This tool fills the gap for **subjective, scale-able** experiences:
back pain, migraines, allergies, IBS flare-ups, post-viral fatigue.
Each entry stores ``name`` + ``intensity`` (1-10 medical pain scale)
plus optional location, duration, triggers, relief — so users can
correlate flare-ups with the rest of their data over time.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, console, fail, ok, render_record, render_rows

NAME = "symptom"
HELP = "🤒 Pain & symptom tracker (intensity 1-10, location, triggers, relief)"
EMOJI = "🤒"


class Symptom(SQLModel, table=True):
    """One symptom event."""

    __tablename__ = "symptom_entry"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    intensity: int                       # 1-10 medical pain scale
    location: str | None = None          # "lumbar", "frontal", "left shoulder", ...
    duration_min: int = 0                # 0 = unknown / still ongoing
    triggers: str | None = None          # comma-joined: "stress, poor sleep"
    relief: str | None = None            # comma-joined: "ibuprofen, rest"
    entry_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    note: str | None = None


app = typer.Typer(no_args_is_help=True, help=HELP)


def _resolve(db, ident: str) -> Symptom | None:
    """Resolve a CLI arg to a symptom by ID or name (most-recent first)."""
    from clibo.core.base import lookup_by_id_or_name
    if ident.isdigit():
        entry = db.get(Symptom, int(ident))
        if entry:
            return entry
    return db.exec(
        select(Symptom)
        .where(Symptom.name.ilike(f"%{ident}%"))
        .order_by(Symptom.id.desc())
    ).first() or lookup_by_id_or_name(db, Symptom, ident, Symptom.name)


def _intensity_label(intensity: int) -> str:
    """Standard medical interpretation of a 1-10 pain score."""
    if intensity <= 0:
        return "none"
    if intensity <= 3:
        return "mild"
    if intensity <= 6:
        return "moderate"
    if intensity <= 9:
        return "severe"
    return "worst possible"


def _intensity_cell(intensity: int) -> str:
    """Coloured `Rich` cell for the intensity score in tables."""
    label = _intensity_label(intensity)
    colour = {
        "none": "dim", "mild": "green",
        "moderate": "yellow", "severe": "red", "worst possible": "bold red",
    }[label]
    return f"[{colour}]{intensity}/10 · {label}[/{colour}]"


def _row(entry: Symptom) -> dict:
    return {
        "id": entry.id,
        "entry_date": entry.entry_date,
        "name": entry.name,
        "intensity": entry.intensity,
        "intensity_label": _intensity_label(entry.intensity),
        "location": entry.location,
        "duration_min": entry.duration_min,
        "triggers": entry.triggers,
        "relief": entry.relief,
        "note": entry.note,
    }


@app.command()
def log(
    name: str = typer.Argument(..., help="Symptom name, e.g. 'back pain', 'migraine'"),
    intensity: int = typer.Option(..., "--intensity", "-i",
                                   help="Intensity, 1 (mild) – 10 (worst possible)"),
    location: str = typer.Option(None, "--location", "-l",
                                  help="Body area, e.g. 'lumbar', 'frontal'"),
    duration_min: int = typer.Option(0, "--duration", "-t",
                                      help="Duration in minutes (0 = unknown/ongoing)"),
    triggers: str = typer.Option(None, "--triggers",
                                  help="Comma-separated possible triggers"),
    relief: str = typer.Option(None, "--relief", "-r",
                                help="Comma-separated things that helped"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🤒 Log a symptom event."""
    if not 1 <= intensity <= 10:
        fail("Intensity must be 1–10", json_out=json_out)
    if duration_min < 0:
        fail("Duration cannot be negative", json_out=json_out)
    entry = Symptom(
        name=name.strip(),
        intensity=intensity,
        location=location,
        duration_min=duration_min,
        triggers=triggers,
        relief=relief,
        entry_date=parse_date(on),
        note=note,
    )
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        data = _row(entry)
    label = _intensity_label(intensity)
    where = f" ({location})" if location else ""
    ok(f"Logged {EMOJI} {name}{where} — {intensity}/10 ({label})",
       json_out=json_out, data=data)


# `add` is the friendlier verb across the codebase.
app.command(name="add", help="Alias for `log`")(log)


@app.command()
def today(json_out: JsonOpt = False) -> None:
    """🤒 Today's symptom log."""
    day = date.today()
    with session() as db:
        entries = list(
            db.exec(
                select(Symptom)
                .where(Symptom.entry_date == day)
                .order_by(Symptom.created_at)
            ).all()
        )
    if json_out:
        render_record(
            {
                "date": day,
                "entries": [_row(e) for e in entries],
                "worst": max((e.intensity for e in entries), default=0),
            },
            json_out=True,
        )
        return
    if not entries:
        console.print(
            "\n  [dim]No symptoms logged today — "
            "clibo symptom log 'back pain' -i 5[/dim]\n"
        )
        return
    console.print(f"\n🤒 [bold]Today[/bold] · {day:%a %d %b}\n")
    for e in entries:
        loc = f"  [dim]({e.location})[/dim]" if e.location else ""
        dur = f"  [dim]· {e.duration_min} min[/dim]" if e.duration_min else ""
        console.print(
            f"  · [bold]{e.name}[/bold]{loc}   {_intensity_cell(e.intensity)}{dur}"
        )
    console.print()


@app.command(name="list")
def list_entries(
    days: int = typer.Option(14, "--days", help="Look back this many days"),
    name: str = typer.Option(None, "--name", "-N", help="Filter by symptom name (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """🤒 Recent symptom entries."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        query = select(Symptom).where(Symptom.entry_date >= since)
        if name:
            query = query.where(Symptom.name.ilike(f"%{name}%"))
        entries = list(
            db.exec(
                query.order_by(Symptom.entry_date.desc(), Symptom.id.desc())
            ).all()
        )
    render_rows(
        [_row(e) for e in entries],
        [("id", "ID"), ("entry_date", "Date"), ("name", "Symptom"),
         ("intensity", "Intensity"), ("location", "Location"),
         ("duration_min", "Min")],
        json_out=json_out,
        title="🤒 Symptom log",
        formatters={
            "intensity": lambda v, r: _intensity_cell(v),
            "duration_min": lambda v, r: f"{v}" if v else "[dim]—[/dim]",
            "location": lambda v, r: v or "[dim]—[/dim]",
        },
        empty="No symptoms logged in this window.",
    )


@app.command()
def show(
    entry: str = typer.Argument(..., help="Entry ID or symptom name (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """🤒 Show one symptom entry."""
    with session() as db:
        target = _resolve(db, entry)
        if not target:
            fail(f"No symptom matching {entry!r}", json_out=json_out)
        data = _row(target) | {"created_at": target.created_at}
    render_record(data, json_out=json_out, title=f"🤒 {data['name']} #{target.id}")


@app.command()
def edit(
    entry: str = typer.Argument(..., help="Entry ID or symptom name (fuzzy)"),
    name: str = typer.Option(None, "--name"),
    intensity: int = typer.Option(None, "--intensity", "-i"),
    location: str = typer.Option(None, "--location", "-l"),
    duration_min: int = typer.Option(None, "--duration", "-t"),
    triggers: str = typer.Option(None, "--triggers"),
    relief: str = typer.Option(None, "--relief", "-r"),
    on: str = typer.Option(None, "--date", "-d"),
    note: str = typer.Option(None, "--note", "-n"),
    json_out: JsonOpt = False,
) -> None:
    """🤒 Edit a symptom entry."""
    if intensity is not None and not 1 <= intensity <= 10:
        fail("Intensity must be 1–10", json_out=json_out)
    if duration_min is not None and duration_min < 0:
        fail("Duration cannot be negative", json_out=json_out)
    with session() as db:
        target = _resolve(db, entry)
        if not target:
            fail(f"No symptom matching {entry!r}", json_out=json_out)
        if name is not None:
            target.name = name.strip()
        if intensity is not None:
            target.intensity = intensity
        if location is not None:
            target.location = location
        if duration_min is not None:
            target.duration_min = duration_min
        if triggers is not None:
            target.triggers = triggers
        if relief is not None:
            target.relief = relief
        if on is not None:
            target.entry_date = parse_date(on)
        if note is not None:
            target.note = note
        db.add(target)
        db.flush()
        data = _row(target)
    ok(f"Updated symptom #{target.id}", json_out=json_out, data=data)


@app.command()
def rm(
    entry: str = typer.Argument(..., help="Entry ID or symptom name (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """🤒 Delete a symptom entry."""
    with session() as db:
        target = _resolve(db, entry)
        if not target:
            fail(f"No symptom matching {entry!r}", json_out=json_out)
        eid = target.id
        db.delete(target)
    ok(f"Deleted symptom #{eid}", json_out=json_out, data={"deleted": eid})


@app.command()
def history(
    name: str = typer.Argument(..., help="Symptom name (fuzzy)"),
    days: int = typer.Option(90, "--days", help="Look back this many days"),
    json_out: JsonOpt = False,
) -> None:
    """📈 One symptom over time — intensity trend & how often it flares.

    Useful for chronic conditions: "is my migraine getting better or
    worse?". Aggregates by day, returns avg intensity per day.
    """
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        entries = list(
            db.exec(
                select(Symptom)
                .where(Symptom.name.ilike(f"%{name}%"))
                .where(Symptom.entry_date >= since)
                .order_by(Symptom.entry_date)
            ).all()
        )
    if not entries:
        fail(f"No entries for {name!r} in the last {days} days",
             json_out=json_out)
    daily: dict[date, list[int]] = {}
    for e in entries:
        daily.setdefault(e.entry_date, []).append(e.intensity)
    rows = [
        {"entry_date": d,
         "episodes": len(scores),
         "avg_intensity": round(sum(scores) / len(scores), 1),
         "max_intensity": max(scores)}
        for d, scores in sorted(daily.items())
    ]
    render_rows(
        rows,
        [("entry_date", "Date"), ("episodes", "Episodes"),
         ("avg_intensity", "Avg"), ("max_intensity", "Max")],
        json_out=json_out,
        title=f"📈 {name} · last {days}d",
        formatters={
            "max_intensity": lambda v, r: _intensity_cell(v),
        },
        empty="—",
    )
    if not json_out:
        worst = max(rows, key=lambda r: r["max_intensity"])
        first = rows[0]["avg_intensity"]
        last = rows[-1]["avg_intensity"]
        trend = (
            "[green]↘ improving[/green]" if last < first - 0.5
            else "[red]↗ worsening[/red]" if last > first + 0.5
            else "[yellow]→ steady[/yellow]"
        )
        console.print(
            f"  📊 [bold]{len(entries)}[/bold] episodes over "
            f"[bold]{len(rows)}[/bold] days   ·   trend: {trend}   ·   "
            f"worst {worst['max_intensity']}/10 on {worst['entry_date']}"
        )


@app.command()
def stats(
    days: int = typer.Option(30, "--days", help="Window size in days"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Symptom stats — top complaints, avg intensity, days affected."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        entries = list(
            db.exec(
                select(Symptom).where(Symptom.entry_date >= since)
            ).all()
        )
    by_name: dict[str, list[int]] = {}
    for e in entries:
        by_name.setdefault(e.name, []).append(e.intensity)
    top = sorted(
        (
            {
                "name": name,
                "episodes": len(scores),
                "avg_intensity": round(sum(scores) / len(scores), 1),
                "worst": max(scores),
            }
            for name, scores in by_name.items()
        ),
        key=lambda r: r["episodes"],
        reverse=True,
    )
    data = {
        "window_days": days,
        "total_episodes": len(entries),
        "days_affected": len({e.entry_date for e in entries}),
        "avg_intensity": (
            round(sum(e.intensity for e in entries) / len(entries), 1)
            if entries else None
        ),
        "top_symptoms": top[:5],
        "worst_episode": (
            max(({"name": e.name, "intensity": e.intensity,
                  "entry_date": e.entry_date} for e in entries),
                key=lambda r: r["intensity"])
            if entries else None
        ),
    }
    render_record(data, json_out=json_out, title=f"📊 Symptom stats · last {days}d")
