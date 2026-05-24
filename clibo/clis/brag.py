"""🏆 brag — achievement log for performance reviews."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlalchemy import or_
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, console, fail, ok, render_record, render_rows

NAME = "brag"
HELP = "🏆 Achievement log for performance reviews"
EMOJI = "🏆"


class Achievement(SQLModel, table=True):
    """Something you accomplished — a 'brag document' entry."""

    __tablename__ = "brag_achievement"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str | None = None
    category: str = "work"
    impact: str | None = None
    tags: str | None = None
    entry_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _row(ach: Achievement) -> dict:
    return {
        "id": ach.id,
        "entry_date": ach.entry_date,
        "title": ach.title,
        "description": ach.description,
        "category": ach.category,
        "impact": ach.impact,
        "tags": ach.tags,
    }


@app.command()
def add(
    title: str = typer.Argument(..., help="What you accomplished"),
    description: str = typer.Option(None, "--desc", "-D", help="More detail"),
    category: str = typer.Option("work", "--category", "-c", help="Category"),
    impact: str = typer.Option(None, "--impact", "-i", help="The impact it had"),
    tag: str = typer.Option(None, "--tag", "-t", help="Comma-separated tags"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    json_out: JsonOpt = False,
) -> None:
    """🏆 Log an achievement."""
    ach = Achievement(
        title=title, description=description, category=category.lower(),
        impact=impact, tags=tag, entry_date=parse_date(on),
    )
    with session() as db:
        db.add(ach)
        db.flush()
        db.refresh(ach)
        data = _row(ach)
    ok(f"Logged {EMOJI} {title}", json_out=json_out, data=data)


@app.command(name="list")
def list_achievements(
    days: int = typer.Option(90, "--days", help="Look back this many days"),
    category: str = typer.Option(None, "--category", "-c", help="Filter by category"),
    tag: str = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    json_out: JsonOpt = False,
) -> None:
    """🏆 List recent achievements."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        query = select(Achievement).where(Achievement.entry_date >= since)
        if category:
            query = query.where(Achievement.category == category.lower())
        if tag:
            query = query.where(Achievement.tags.ilike(f"%{tag}%"))
        achievements = list(
            db.exec(query.order_by(Achievement.entry_date.desc(), Achievement.id.desc())).all()
        )
    render_rows(
        [_row(a) for a in achievements],
        [("id", "ID"), ("entry_date", "Date"), ("title", "Achievement"),
         ("category", "Category"), ("impact", "Impact")],
        json_out=json_out,
        title="🏆 Achievements",
        empty="Nothing logged yet — try: clibo brag add 'Shipped the new API'",
    )


@app.command()
def show(
    achievement: str = typer.Argument(..., help="Achievement ID or title (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """🏆 Show one achievement in detail. Accepts a numeric ID or a title."""
    from clibo.core.base import lookup_by_id_or_name
    with session() as db:
        ach = lookup_by_id_or_name(db, Achievement, achievement, Achievement.title)
        if not ach:
            fail(f"No achievement matching {achievement!r}", json_out=json_out)
        data = _row(ach) | {"created_at": ach.created_at}
    render_record(data, json_out=json_out, title=f"🏆 {data['title']}")


@app.command()
def search(
    query: str = typer.Argument(..., help="Text to search for"),
    json_out: JsonOpt = False,
) -> None:
    """🔍 Search achievements by title, description or impact."""
    pattern = f"%{query}%"
    with session() as db:
        achievements = list(
            db.exec(
                select(Achievement).where(
                    or_(
                        Achievement.title.ilike(pattern),
                        Achievement.description.ilike(pattern),
                        Achievement.impact.ilike(pattern),
                    )
                ).order_by(Achievement.entry_date.desc())
            ).all()
        )
    render_rows(
        [_row(a) for a in achievements],
        [("id", "ID"), ("entry_date", "Date"), ("title", "Achievement"),
         ("category", "Category")],
        json_out=json_out,
        title=f"🔍 Achievements matching '{query}'",
        empty=f"No achievements match '{query}'.",
    )


@app.command()
def since(
    from_date: str = typer.Argument(..., help="List achievements since this date"),
    json_out: JsonOpt = False,
) -> None:
    """📋 List achievements since a date — handy for review prep."""
    start = parse_date(from_date)
    with session() as db:
        achievements = list(
            db.exec(
                select(Achievement)
                .where(Achievement.entry_date >= start)
                .order_by(Achievement.entry_date)
            ).all()
        )
    if json_out:
        render_record(
            {"since": start, "count": len(achievements),
             "achievements": [_row(a) for a in achievements]},
            json_out=True,
        )
        return
    console.print(f"\n🏆 [bold]Achievements since {start}[/bold] "
                  f"([cyan]{len(achievements)}[/cyan])\n")
    for ach in achievements:
        console.print(f"  [cyan]{ach.entry_date}[/cyan]  [bold]{ach.title}[/bold]")
        if ach.impact:
            console.print(f"            [dim]Impact: {ach.impact}[/dim]")
    console.print()


@app.command()
def rm(
    achievement: str = typer.Argument(..., help="Achievement ID or title (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """🏆 Delete an achievement. Accepts a numeric ID or a title."""
    from clibo.core.base import lookup_by_id_or_name
    with session() as db:
        ach = lookup_by_id_or_name(db, Achievement, achievement, Achievement.title)
        if not ach:
            fail(f"No achievement matching {achievement!r}", json_out=json_out)
        aid = ach.id
        db.delete(ach)
    ok(f"Deleted achievement #{aid}", json_out=json_out, data={"deleted": aid})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Achievement stats."""
    with session() as db:
        achievements = list(db.exec(select(Achievement)).all())
    by_category: dict[str, int] = {}
    for ach in achievements:
        by_category[ach.category] = by_category.get(ach.category, 0) + 1
    since_90 = date.today() - timedelta(days=90)
    data = {
        "total": len(achievements),
        "last_90_days": sum(1 for a in achievements if a.entry_date >= since_90),
        "by_category": by_category,
        "with_impact": sum(1 for a in achievements if a.impact),
    }
    render_record(data, json_out=json_out, title="📊 Achievement stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
