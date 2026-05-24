"""📜 cv — career history: jobs, education, projects, certifications.

Distinct from `clibo jobs` which is for *applying* to jobs. ``cv`` is
the career history you'd put on a resume — things you've already done.
"""

from __future__ import annotations

from datetime import date, datetime

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, console, fail, ok, render_record, render_rows

NAME = "cv"
HELP = "📜 Career history — jobs, education, projects, certifications"
EMOJI = "📜"
KINDS = ["job", "education", "project", "cert", "other"]


def _parse_month(value: str | None) -> date | None:
    """Accept YYYY-MM, YYYY-MM-DD, or any date `parse_date` understands."""
    if value is None:
        return None
    value = value.strip()
    if len(value) == 7 and value.count("-") == 1:
        # YYYY-MM → first of that month
        try:
            return datetime.strptime(value, "%Y-%m").date().replace(day=1)
        except ValueError as exc:
            raise typer.BadParameter(f"Bad month: {value!r}") from exc
    return parse_date(value)


class CvEntry(SQLModel, table=True):
    """One résumé entry."""

    __tablename__ = "cv_entry"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    org: str | None = None
    kind: str = "job"
    start_date: date | None = None
    end_date: date | None = None  # None = current / ongoing
    location: str | None = None
    description: str | None = None
    achievements: str | None = None  # newline-separated bullet list
    tags: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _row(entry: CvEntry) -> dict:
    return {
        "id": entry.id,
        "title": entry.title,
        "org": entry.org,
        "kind": entry.kind,
        "start_date": entry.start_date,
        "end_date": entry.end_date,
        "current": entry.end_date is None,
        "location": entry.location,
        "description": entry.description,
        "achievements": entry.achievements,
        "tags": entry.tags,
    }


def _period(entry: CvEntry) -> str:
    """Render a date range in CV style: ``2024 — present`` / ``2020 — 2024``."""
    if entry.start_date is None and entry.end_date is None:
        return ""
    start = entry.start_date.strftime("%Y-%m") if entry.start_date else "?"
    end = entry.end_date.strftime("%Y-%m") if entry.end_date else "present"
    return f"{start} — {end}"


@app.command()
def add(
    title: str = typer.Argument(..., help="Role / degree / project name"),
    org: str = typer.Option(None, "--org", "-o", help="Company / school / where"),
    kind: str = typer.Option("job", "--kind", "-k", help=f"{'/'.join(KINDS)}"),
    start: str = typer.Option(None, "--start", help="Start month (YYYY-MM)"),
    end: str = typer.Option(None, "--end", help="End month (YYYY-MM) — omit if current"),
    location: str = typer.Option(None, "--location", "-l", help="Where"),
    description: str = typer.Option(None, "--desc", "-D", help="One-line description"),
    tag: str = typer.Option(None, "--tag", "-t", help="Comma-separated tags"),
    json_out: JsonOpt = False,
) -> None:
    """📜 Add a CV entry."""
    kind = kind.lower()
    if kind not in KINDS:
        fail(f"Kind must be one of: {', '.join(KINDS)}", json_out=json_out)
    sd = _parse_month(start)
    ed = _parse_month(end)
    if sd and ed and ed < sd:
        fail("End must be on or after start", json_out=json_out)
    entry = CvEntry(
        title=title, org=org, kind=kind, start_date=sd, end_date=ed,
        location=location, description=description, tags=tag,
    )
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        data = _row(entry)
    at = f" @ {org}" if org else ""
    ok(f"Added {EMOJI} {kind}: {title}{at} ({_period(entry) or 'no dates'})",
       json_out=json_out, data=data)


def _resolve_cv(db, ident: str) -> CvEntry | None:
    from clibo.core.base import lookup_by_id_or_name
    return lookup_by_id_or_name(db, CvEntry, ident, CvEntry.title)


@app.command()
def achieve(
    entry: str = typer.Argument(..., help="CV entry ID or title (fuzzy)"),
    bullet: str = typer.Argument(..., help="The accomplishment to add"),
    json_out: JsonOpt = False,
) -> None:
    """📜 Append a single accomplishment bullet to a CV entry."""
    with session() as db:
        target = _resolve_cv(db, entry)
        if not target:
            fail(f"No CV entry matching {entry!r}", json_out=json_out)
        existing = (target.achievements or "").rstrip()
        target.achievements = f"{existing}\n{bullet}" if existing else bullet
        db.add(target)
        db.flush()
        data = _row(target)
    ok(f"Added bullet to '{target.title}': {bullet}",
       json_out=json_out, data=data)


@app.command()
def end(
    entry: str = typer.Argument(..., help="CV entry ID or title (fuzzy)"),
    on: str = typer.Option("today", "--on", help="End date (YYYY-MM or YYYY-MM-DD)"),
    json_out: JsonOpt = False,
) -> None:
    """📜 Close out a currently-running entry."""
    with session() as db:
        target = _resolve_cv(db, entry)
        if not target:
            fail(f"No CV entry matching {entry!r}", json_out=json_out)
        ed = _parse_month(on)
        if target.start_date and ed and ed < target.start_date:
            fail("End must be on or after start", json_out=json_out)
        target.end_date = ed
        db.add(target)
        db.flush()
        data = _row(target)
    ok(f"Ended '{target.title}' on {ed}", json_out=json_out, data=data)


@app.command(name="list")
def list_entries(
    kind: str = typer.Option(None, "--kind", "-k", help="Filter by kind"),
    json_out: JsonOpt = False,
) -> None:
    """📜 List CV entries (newest start first)."""
    if kind and kind.lower() not in KINDS:
        fail(f"Kind must be one of: {', '.join(KINDS)}", json_out=json_out)
    with session() as db:
        query = select(CvEntry)
        if kind:
            query = query.where(CvEntry.kind == kind.lower())
        entries = list(db.exec(query).all())
    entries.sort(key=lambda e: (e.start_date or date.min), reverse=True)
    rows = [_row(e) | {"period": _period(e)} for e in entries]
    render_rows(
        rows,
        [("id", "ID"), ("kind", "Kind"), ("title", "Title"),
         ("org", "Where"), ("period", "Period"), ("current", "Now")],
        json_out=json_out,
        title="📜 Career history",
        formatters={"current": lambda v, r: "[green]●[/green]" if v else "[dim]·[/dim]"},
        empty="No entries yet — try: clibo cv add 'Senior Engineer' -o Acme --start 2024-01",
    )


@app.command()
def current(json_out: JsonOpt = False) -> None:
    """📜 Show ongoing entries (no end date)."""
    with session() as db:
        entries = list(db.exec(select(CvEntry).where(CvEntry.end_date == None)).all())  # noqa: E711
    render_rows(
        [_row(e) | {"period": _period(e)} for e in entries],
        [("kind", "Kind"), ("title", "Title"), ("org", "Where"),
         ("period", "Period"), ("location", "Location")],
        json_out=json_out,
        title="📜 Currently",
        empty="Nothing in-progress.",
    )


@app.command()
def show(
    entry: str = typer.Argument(..., help="Entry ID or title (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """📜 Show one CV entry pretty-printed."""
    with session() as db:
        target = _resolve_cv(db, entry)
        if not target:
            fail(f"No CV entry matching {entry!r}", json_out=json_out)
        entry_obj = target
        data = _row(entry_obj) | {"period": _period(entry_obj)}
    if json_out:
        render_record(data, json_out=True)
        return
    title = f"{entry_obj.title}" + (f" — [bold]{entry_obj.org}[/bold]" if entry_obj.org else "")
    console.print(f"\n📜 [bold cyan]{entry_obj.kind.title()}[/bold cyan]   [dim]{_period(entry_obj)}[/dim]\n")
    console.print(f"  {title}")
    if entry_obj.location:
        console.print(f"  [dim]{entry_obj.location}[/dim]")
    if entry_obj.description:
        console.print(f"\n  {entry_obj.description}")
    if entry_obj.achievements:
        console.print("\n  [bold]Highlights[/bold]")
        for bullet in entry_obj.achievements.split("\n"):
            if bullet.strip():
                console.print(f"  · {bullet.strip()}")
    console.print()


@app.command()
def timeline(json_out: JsonOpt = False) -> None:
    """🗓️ Render a chronological CV-style timeline."""
    with session() as db:
        entries = list(db.exec(select(CvEntry)).all())
    entries.sort(key=lambda e: (e.start_date or date.min), reverse=True)
    if json_out:
        render_record(
            {"entries": [_row(e) | {"period": _period(e)} for e in entries]},
            json_out=True,
        )
        return
    if not entries:
        console.print("\n  [dim]No CV entries yet.[/dim]\n")
        return
    console.print(f"\n📜 [bold]Career timeline[/bold]   [dim]({len(entries)} entries)[/dim]\n")
    for entry in entries:
        period = _period(entry) or "[dim]no dates[/dim]"
        org = f"  [bold]{entry.org}[/bold]" if entry.org else ""
        kind_label = f"[cyan]{entry.kind}[/cyan]"
        console.print(f"  {kind_label:<14}  [dim]{period}[/dim]")
        console.print(f"    {entry.title}{org}")
        if entry.description:
            console.print(f"    [dim]{entry.description}[/dim]")
        console.print()


@app.command()
def edit(
    entry: str = typer.Argument(..., help="Entry ID or title (fuzzy)"),
    title: str = typer.Option(None, "--title"),
    org: str = typer.Option(None, "--org", "-o"),
    description: str = typer.Option(None, "--desc", "-D"),
    location: str = typer.Option(None, "--location", "-l"),
    tag: str = typer.Option(None, "--tag", "-t"),
    json_out: JsonOpt = False,
) -> None:
    """📜 Edit a CV entry. Accepts a numeric ID or a title."""
    with session() as db:
        target = _resolve_cv(db, entry)
        if not target:
            fail(f"No CV entry matching {entry!r}", json_out=json_out)
        for field, value in {"title": title, "org": org, "description": description,
                             "location": location, "tags": tag}.items():
            if value is not None:
                setattr(target, field, value)
        db.add(target)
        db.flush()
        data = _row(target)
    ok(f"Updated CV entry #{target.id}", json_out=json_out, data=data)


@app.command()
def rm(
    entry: str = typer.Argument(..., help="Entry ID or title (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """📜 Delete a CV entry."""
    with session() as db:
        target = _resolve_cv(db, entry)
        if not target:
            fail(f"No CV entry matching {entry!r}", json_out=json_out)
        eid = target.id
        db.delete(target)
    ok(f"Deleted CV entry #{eid}", json_out=json_out, data={"deleted": eid})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 CV stats — counts by kind, total years, current roles."""
    with session() as db:
        entries = list(db.exec(select(CvEntry)).all())
    by_kind = {k: sum(1 for e in entries if e.kind == k) for k in KINDS}
    job_months = 0
    for entry in entries:
        if entry.kind != "job" or entry.start_date is None:
            continue
        end_d = entry.end_date or date.today()
        job_months += (end_d.year - entry.start_date.year) * 12 + (end_d.month - entry.start_date.month)
    data = {
        "total": len(entries),
        "by_kind": by_kind,
        "currently": sum(1 for e in entries if e.end_date is None),
        "approx_job_years": round(job_months / 12, 1),
    }
    render_record(data, json_out=json_out, title="📊 CV stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `update` is the SQL-natural synonym for `edit`; both work.
app.command(name="update", help="Alias for `edit`")(edit)

# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
