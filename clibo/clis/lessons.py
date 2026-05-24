"""📓 lessons — lessons learned: context + takeaway, structured for review."""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta

import typer
from sqlalchemy import or_
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, console, fail, ok, render_record, render_rows

NAME = "lessons"
HELP = "📓 Lessons learned — structured takeaways from real situations"
EMOJI = "📓"


class Lesson(SQLModel, table=True):
    """One lesson learned: a takeaway and (optionally) the situation it came from."""

    __tablename__ = "lessons_lesson"

    id: int | None = Field(default=None, primary_key=True)
    takeaway: str
    context: str | None = None
    category: str = "general"
    tags: str | None = None
    entry_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _row(lesson: Lesson) -> dict:
    return {
        "id": lesson.id,
        "entry_date": lesson.entry_date,
        "takeaway": lesson.takeaway,
        "context": lesson.context,
        "category": lesson.category,
        "tags": lesson.tags,
    }


@app.command()
def add(
    takeaway: str = typer.Argument(..., help="The lesson itself"),
    context: str = typer.Option(None, "--context", "-x",
                                help="Where/when you learned it"),
    category: str = typer.Option("general", "--category", "-c",
                                 help="e.g. work / life / coding / health"),
    tag: str = typer.Option(None, "--tag", "-t", help="Comma-separated tags"),
    on: str = typer.Option("today", "--date", "-d", help="Date learned"),
    json_out: JsonOpt = False,
) -> None:
    """📓 Capture a lesson learned."""
    lesson = Lesson(
        takeaway=takeaway, context=context, category=category.lower(),
        tags=tag, entry_date=parse_date(on),
    )
    with session() as db:
        db.add(lesson)
        db.flush()
        db.refresh(lesson)
        data = _row(lesson)
    ok(f"Captured {EMOJI} {takeaway[:80]}{'…' if len(takeaway) > 80 else ''}",
       json_out=json_out, data=data)


@app.command(name="list")
def list_lessons(
    days: int = typer.Option(365, "--days", help="Look back this many days"),
    category: str = typer.Option(None, "--category", "-c", help="Filter by category"),
    tag: str = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    json_out: JsonOpt = False,
) -> None:
    """📓 List lessons."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        query = select(Lesson).where(Lesson.entry_date >= since)
        if category:
            query = query.where(Lesson.category == category.lower())
        if tag:
            query = query.where(Lesson.tags.ilike(f"%{tag}%"))
        lessons = list(
            db.exec(query.order_by(Lesson.entry_date.desc(), Lesson.id.desc())).all()
        )
    render_rows(
        [_row(ls) for ls in lessons],
        [("id", "ID"), ("entry_date", "Date"), ("takeaway", "Takeaway"),
         ("category", "Category"), ("context", "Context")],
        json_out=json_out,
        title="📓 Lessons",
        empty="No lessons yet — try: clibo lessons add 'always set retry max-attempts'",
    )


@app.command()
def show(lesson_id: int = typer.Argument(..., help="Lesson ID"), json_out: JsonOpt = False) -> None:
    """📓 Show one lesson."""
    with session() as db:
        lesson = db.get(Lesson, lesson_id)
        if not lesson:
            fail(f"No lesson #{lesson_id}", json_out=json_out)
        data = _row(lesson) | {"created_at": lesson.created_at}
    if json_out:
        render_record(data, json_out=True)
        return
    console.print(f"\n📓 [bold]Lesson #{lesson.id}[/bold]   [dim]({lesson.entry_date})[/dim]\n")
    console.print("  [bold cyan]Takeaway[/bold cyan]")
    console.print(f"  {lesson.takeaway}\n")
    if lesson.context:
        console.print("  [bold cyan]Context[/bold cyan]")
        console.print(f"  {lesson.context}\n")
    if lesson.tags:
        console.print(f"  [dim]tags: {lesson.tags}   ·   category: {lesson.category}[/dim]\n")
    else:
        console.print(f"  [dim]category: {lesson.category}[/dim]\n")


@app.command()
def search(
    query: str = typer.Argument(..., help="Text to search in takeaway/context/tags"),
    json_out: JsonOpt = False,
) -> None:
    """🔍 Search lessons."""
    pattern = f"%{query}%"
    with session() as db:
        lessons = list(
            db.exec(
                select(Lesson).where(
                    or_(
                        Lesson.takeaway.ilike(pattern),
                        Lesson.context.ilike(pattern),
                        Lesson.tags.ilike(pattern),
                    )
                ).order_by(Lesson.entry_date.desc())
            ).all()
        )
    render_rows(
        [_row(ls) for ls in lessons],
        [("id", "ID"), ("entry_date", "Date"), ("takeaway", "Takeaway"),
         ("category", "Category")],
        json_out=json_out,
        title=f"🔍 Lessons matching '{query}'",
        empty=f"No lessons match '{query}'.",
    )


@app.command(name="random")
def pick(json_out: JsonOpt = False) -> None:
    """🎲 Pick one random lesson — a quick way to re-encounter what you've learned."""
    with session() as db:
        lessons = list(db.exec(select(Lesson)).all())
    if not lessons:
        fail("No lessons saved yet — capture one first", json_out=json_out)
    chosen = random.choice(lessons)
    data = _row(chosen)
    if json_out:
        render_record(data, json_out=True)
        return
    console.print(f"\n  📓 [italic]{chosen.takeaway}[/italic]")
    if chosen.context:
        console.print(f"     [dim]— from: {chosen.context}[/dim]")
    console.print()


@app.command()
def rm(lesson_id: int = typer.Argument(..., help="Lesson ID"), json_out: JsonOpt = False) -> None:
    """📓 Delete a lesson."""
    with session() as db:
        lesson = db.get(Lesson, lesson_id)
        if not lesson:
            fail(f"No lesson #{lesson_id}", json_out=json_out)
        db.delete(lesson)
    ok(f"Deleted lesson #{lesson_id}", json_out=json_out, data={"deleted": lesson_id})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Lesson stats — counts and category breakdown."""
    with session() as db:
        lessons = list(db.exec(select(Lesson)).all())
    by_category: dict[str, int] = {}
    for lesson in lessons:
        by_category[lesson.category] = by_category.get(lesson.category, 0) + 1
    since_90 = date.today() - timedelta(days=90)
    data = {
        "total": len(lessons),
        "last_90_days": sum(1 for ls in lessons if ls.entry_date >= since_90),
        "by_category": by_category,
        "with_context": sum(1 for ls in lessons if ls.context),
    }
    render_record(data, json_out=json_out, title="📊 Lesson stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)
