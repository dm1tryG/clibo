"""🎂 birthdays — birthday & anniversary reminders."""

from __future__ import annotations

import re
from datetime import date, datetime

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import _parse_month_name_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "birthdays"
HELP = "🎂 Birthday & anniversary reminders"
EMOJI = "🎂"
KINDS = ["birthday", "anniversary"]


class Occasion(SQLModel, table=True):
    """A recurring yearly occasion — a birthday or an anniversary."""

    __tablename__ = "birthdays_occasion"

    id: int | None = Field(default=None, primary_key=True)
    person: str
    kind: str = "birthday"
    month: int
    day: int
    year: int | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context, json_out: JsonOpt = False) -> None:
    """Default: ``clibo birthdays`` (bare) runs the ``upcoming`` summary."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(upcoming, days=30, json_out=json_out)


def _parse_md(text: str) -> tuple[int, int, int | None]:
    """Parse a date string into (month, day, optional year).

    Accepts the numeric forms ``YYYY-MM-DD``, ``MM-DD``, ``DD.MM`` and
    ``MM/DD``, plus the month-name forms ``"March 12"``, ``"12 March"``,
    ``"Mar 12 1985"`` (year stays optional in all cases — a birthday on
    "March 12" doesn't need a birth year).
    """
    text = text.strip()
    for fmt, has_year in (("%Y-%m-%d", True), ("%m-%d", False),
                          ("%d.%m", False), ("%m/%d", False)):
        try:
            parsed = datetime.strptime(text, fmt)
        except ValueError:
            continue
        return parsed.month, parsed.day, (parsed.year if has_year else None)
    # Month-name forms ("March 12" / "12 march 1985" / "Mar 12").
    md = _parse_month_name_date(text.lower())
    if md is not None:
        # If the original text didn't contain a 4-digit year, treat the
        # year as unknown (parse_month_name_date fills in current year).
        has_year_in_text = bool(re.search(r"\b\d{4}\b", text))
        return md.month, md.day, (md.year if has_year_in_text else None)
    raise typer.BadParameter(
        f"Date must be MM-DD, YYYY-MM-DD, or a month-name form like "
        f"'March 12' / 'Mar 12 1985': {text!r}"
    )


def _next_occurrence(month: int, day: int) -> date:
    """The next date this month/day falls on, today or later."""
    today = date.today()
    for year in (today.year, today.year + 1):
        try:
            occ = date(year, month, day)
        except ValueError:  # Feb 29 in a non-leap year
            occ = date(year, month, 28)
        if occ >= today:
            return occ
    return today


def _row(occasion: Occasion) -> dict:
    nxt = _next_occurrence(occasion.month, occasion.day)
    return {
        "id": occasion.id,
        "person": occasion.person,
        "kind": occasion.kind,
        "date": f"{occasion.month:02d}-{occasion.day:02d}",
        "next_date": nxt,
        "days_until": (nxt - date.today()).days,
        "turning": (nxt.year - occasion.year) if occasion.year else None,
        "note": occasion.note,
    }


@app.command()
def add(
    person: str = typer.Argument(..., help="Whose occasion this is"),
    on: str = typer.Option(..., "--date", "-d",
                            help="MM-DD, YYYY-MM-DD, or a month-name form like "
                                 "'March 12' / 'Mar 12 1985'"),
    kind: str = typer.Option("birthday", "--kind", "-k", help="birthday / anniversary"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🎂 Add a birthday or anniversary."""
    kind = kind.lower()
    if kind not in KINDS:
        fail(f"Kind must be one of: {', '.join(KINDS)}", json_out=json_out)
    month, day, year = _parse_md(on)
    if not 1 <= month <= 12 or not 1 <= day <= 31:
        fail("Invalid month or day", json_out=json_out)
    occasion = Occasion(person=person, kind=kind, month=month, day=day, year=year, note=note)
    with session() as db:
        db.add(occasion)
        db.flush()
        db.refresh(occasion)
        data = _row(occasion)
    ok(f"Added {EMOJI} {kind} for {person} ({data['date']})", json_out=json_out, data=data)


@app.command(name="list")
def list_occasions(
    kind: str = typer.Option(None, "--kind", "-k", help="Filter by kind"),
    json_out: JsonOpt = False,
) -> None:
    """🎂 List occasions, soonest first."""
    if kind and kind.lower() not in KINDS:
        fail(f"Kind must be one of: {', '.join(KINDS)}", json_out=json_out)
    with session() as db:
        query = select(Occasion)
        if kind:
            query = query.where(Occasion.kind == kind.lower())
        occasions = list(db.exec(query).all())
    rows = sorted((_row(o) for o in occasions), key=lambda r: r["days_until"])
    render_rows(
        rows,
        [("id", "ID"), ("person", "Person"), ("kind", "Kind"),
         ("next_date", "Next"), ("days_until", "Days"), ("turning", "Turning")],
        json_out=json_out,
        title="🎂 Birthdays & anniversaries",
        empty="Nothing yet — try: clibo birthdays add 'Mom' -d 04-15",
    )


@app.command()
def today(json_out: JsonOpt = False) -> None:
    """🎂 Whose birthday or anniversary is today."""
    with session() as db:
        occasions = list(db.exec(select(Occasion)).all())
    rows = [_row(o) for o in occasions if _row(o)["days_until"] == 0]
    if json_out:
        render_record({"date": date.today(), "occasions": rows}, json_out=True)
        return
    if not rows:
        from clibo.core.output import console

        console.print("\n  🎂 [dim]No birthdays or anniversaries today.[/dim]\n")
        return
    render_rows(
        rows,
        [("person", "Person"), ("kind", "Kind"), ("turning", "Turning")],
        json_out=False,
        title=f"🎉 Today · {date.today():%d %B}",
    )


@app.command()
def upcoming(
    days: int = typer.Option(30, "--days", help="Look ahead this many days"),
    json_out: JsonOpt = False,
) -> None:
    """🔔 Occasions coming up in the next N days."""
    with session() as db:
        occasions = list(db.exec(select(Occasion)).all())
    rows = sorted(
        (r for o in occasions if (r := _row(o))["days_until"] <= days),
        key=lambda r: r["days_until"],
    )
    render_rows(
        rows,
        [("person", "Person"), ("kind", "Kind"), ("next_date", "Date"),
         ("days_until", "Days"), ("turning", "Turning")],
        json_out=json_out,
        title=f"🔔 Next {days} days",
        empty="Nothing coming up.",
    )


def _resolve_occasion(db, ident: str) -> Occasion | None:
    from clibo.core.base import lookup_by_id_or_name
    return lookup_by_id_or_name(db, Occasion, ident, Occasion.person)


@app.command()
def edit(
    occasion: str = typer.Argument(..., help="Occasion ID or person name"),
    on: str = typer.Option(None, "--date", "-d",
                            help="New date (MM-DD, YYYY-MM-DD, or 'March 15')"),
    kind: str = typer.Option(None, "--kind", "-k",
                              help="birthday / anniversary"),
    note: str = typer.Option(None, "--note", "-n", help="New note"),
    person: str = typer.Option(None, "--person",
                                 help="Rename the person"),
    json_out: JsonOpt = False,
) -> None:
    """🎂 Edit an occasion. Accepts a numeric ID or a person name."""
    with session() as db:
        target = _resolve_occasion(db, occasion)
        if not target:
            fail(f"No occasion matching {occasion!r}", json_out=json_out)
        if on is not None:
            month, day, year = _parse_md(on)
            target.month, target.day = month, day
            if year is not None:
                target.year = year
        if kind is not None:
            if kind.lower() not in KINDS:
                fail(f"Kind must be one of: {', '.join(KINDS)}",
                     json_out=json_out)
            target.kind = kind.lower()
        if note is not None:
            target.note = note
        if person is not None:
            target.person = person
        db.add(target)
        db.flush()
        data = _row(target)
    ok(f"Updated occasion #{target.id} — {target.person}",
       json_out=json_out, data=data)


@app.command()
def rm(
    occasion: str = typer.Argument(..., help="Occasion ID or person name"),
    json_out: JsonOpt = False,
) -> None:
    """🎂 Delete an occasion."""
    with session() as db:
        target = _resolve_occasion(db, occasion)
        if not target:
            fail(f"No occasion matching {occasion!r}", json_out=json_out)
        oid = target.id
        db.delete(target)
    ok(f"Deleted occasion #{oid}", json_out=json_out, data={"deleted": oid})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Occasion stats."""
    with session() as db:
        occasions = list(db.exec(select(Occasion)).all())
    rows = [_row(o) for o in occasions]
    nxt = min(rows, key=lambda r: r["days_until"], default=None)
    data = {
        "total": len(occasions),
        "birthdays": sum(1 for o in occasions if o.kind == "birthday"),
        "anniversaries": sum(1 for o in occasions if o.kind == "anniversary"),
        "next_up": nxt["person"] if nxt else None,
        "next_in_days": nxt["days_until"] if nxt else None,
    }
    render_record(data, json_out=json_out, title="📊 Birthday stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `update` is the SQL-natural synonym for `edit`; both work.
app.command(name="update", help="Alias for `edit`")(edit)

# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
