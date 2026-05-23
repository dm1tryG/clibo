"""💡 ideas — idea capture with a lifecycle (raw → shipped or abandoned)."""

from __future__ import annotations

from datetime import datetime

import typer
from sqlalchemy import or_
from sqlmodel import Field, SQLModel, select

from clibo.core.db import session
from clibo.core.output import JsonOpt, console, fail, ok, render_record, render_rows

NAME = "ideas"
HELP = "💡 Idea capture with a lifecycle"
EMOJI = "💡"
STATUSES = ["raw", "exploring", "validated", "shipped", "abandoned"]
OPEN_STATUSES = ["raw", "exploring", "validated"]


class Idea(SQLModel, table=True):
    """One captured idea with status, description and tags."""

    __tablename__ = "ideas_idea"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str | None = None
    status: str = "raw"
    tags: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _row(idea: Idea) -> dict:
    return {
        "id": idea.id,
        "title": idea.title,
        "description": idea.description,
        "status": idea.status,
        "tags": idea.tags,
        "created_at": idea.created_at,
        "updated_at": idea.updated_at,
    }


def _status_cell(status: str) -> str:
    return {
        "raw": "[dim]raw[/dim]",
        "exploring": "[cyan]exploring[/cyan]",
        "validated": "[bold blue]validated[/bold blue]",
        "shipped": "[green]✓ shipped[/green]",
        "abandoned": "[red]✗ abandoned[/red]",
    }.get(status, status)


@app.command()
def add(
    title: str = typer.Argument(..., help="One-line idea title"),
    description: str = typer.Option(None, "--desc", "-D", help="More detail"),
    status: str = typer.Option("raw", "--status", "-s",
                                help=f"{'/'.join(STATUSES)}"),
    tag: str = typer.Option(None, "--tag", "-t", help="Comma-separated tags"),
    json_out: JsonOpt = False,
) -> None:
    """💡 Capture an idea."""
    status = status.lower()
    if status not in STATUSES:
        fail(f"Status must be one of: {', '.join(STATUSES)}", json_out=json_out)
    idea = Idea(title=title, description=description, status=status, tags=tag)
    with session() as db:
        db.add(idea)
        db.flush()
        db.refresh(idea)
        data = _row(idea)
    ok(f"Captured {EMOJI} '{title}' ({status})", json_out=json_out, data=data)


@app.command(name="list")
def list_ideas(
    status: str = typer.Option(None, "--status", "-s", help="Filter by status"),
    tag: str = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    open_only: bool = typer.Option(False, "--open",
                                    help="Only open statuses (raw/exploring/validated)"),
    json_out: JsonOpt = False,
) -> None:
    """💡 List ideas."""
    if status and status.lower() not in STATUSES:
        fail(f"Status must be one of: {', '.join(STATUSES)}", json_out=json_out)
    with session() as db:
        query = select(Idea)
        if status:
            query = query.where(Idea.status == status.lower())
        elif open_only:
            query = query.where(Idea.status.in_(OPEN_STATUSES))
        if tag:
            query = query.where(Idea.tags.ilike(f"%{tag}%"))
        ideas = list(db.exec(query.order_by(Idea.updated_at.desc())).all())
    render_rows(
        [_row(i) for i in ideas],
        [("id", "ID"), ("title", "Idea"), ("status", "Status"),
         ("tags", "Tags"), ("updated_at", "Updated")],
        json_out=json_out,
        title="💡 Ideas",
        formatters={"status": lambda v, r: _status_cell(v)},
        empty="No ideas yet — try: clibo ideas add 'a thing worth building'",
    )


@app.command()
def show(idea_id: int = typer.Argument(..., help="Idea ID"), json_out: JsonOpt = False) -> None:
    """💡 Show one idea in detail."""
    with session() as db:
        idea = db.get(Idea, idea_id)
        if not idea:
            fail(f"No idea #{idea_id}", json_out=json_out)
        data = _row(idea)
    render_record(data, json_out=json_out, title=f"💡 #{idea_id}: {data['title']}")


@app.command()
def move(
    idea_id: int = typer.Argument(..., help="Idea ID"),
    status: str = typer.Argument(..., help=f"New status: {', '.join(STATUSES)}"),
    json_out: JsonOpt = False,
) -> None:
    """💡 Move an idea to a new lifecycle status."""
    status = status.lower()
    if status not in STATUSES:
        fail(f"Status must be one of: {', '.join(STATUSES)}", json_out=json_out)
    with session() as db:
        idea = db.get(Idea, idea_id)
        if not idea:
            fail(f"No idea #{idea_id}", json_out=json_out)
        idea.status = status
        idea.updated_at = datetime.now()
        db.add(idea)
        db.flush()
        data = _row(idea)
    flair = " 🚀" if status == "shipped" else ""
    ok(f"Moved '{idea.title}' to {status}{flair}", json_out=json_out, data=data)


@app.command()
def edit(
    idea_id: int = typer.Argument(..., help="Idea ID"),
    title: str = typer.Option(None, "--title", help="New title"),
    description: str = typer.Option(None, "--desc", "-D"),
    tag: str = typer.Option(None, "--tag", "-t"),
    json_out: JsonOpt = False,
) -> None:
    """💡 Edit an idea."""
    with session() as db:
        idea = db.get(Idea, idea_id)
        if not idea:
            fail(f"No idea #{idea_id}", json_out=json_out)
        if title is not None:
            idea.title = title
        if description is not None:
            idea.description = description
        if tag is not None:
            idea.tags = tag
        idea.updated_at = datetime.now()
        db.add(idea)
        db.flush()
        data = _row(idea)
    ok(f"Updated idea #{idea_id}", json_out=json_out, data=data)


@app.command()
def search(
    query: str = typer.Argument(..., help="Text to search in title/description/tags"),
    json_out: JsonOpt = False,
) -> None:
    """🔍 Search ideas."""
    pattern = f"%{query}%"
    with session() as db:
        ideas = list(
            db.exec(
                select(Idea).where(
                    or_(
                        Idea.title.ilike(pattern),
                        Idea.description.ilike(pattern),
                        Idea.tags.ilike(pattern),
                    )
                ).order_by(Idea.updated_at.desc())
            ).all()
        )
    render_rows(
        [_row(i) for i in ideas],
        [("id", "ID"), ("title", "Idea"), ("status", "Status")],
        json_out=json_out,
        title=f"🔍 Ideas matching '{query}'",
        formatters={"status": lambda v, r: _status_cell(v)},
        empty=f"No ideas match '{query}'.",
    )


@app.command()
def rm(idea_id: int = typer.Argument(..., help="Idea ID"), json_out: JsonOpt = False) -> None:
    """💡 Delete an idea."""
    with session() as db:
        idea = db.get(Idea, idea_id)
        if not idea:
            fail(f"No idea #{idea_id}", json_out=json_out)
        db.delete(idea)
    ok(f"Deleted idea #{idea_id}", json_out=json_out, data={"deleted": idea_id})


@app.command()
def pipeline(json_out: JsonOpt = False) -> None:
    """📊 Idea pipeline — counts by lifecycle status."""
    with session() as db:
        ideas = list(db.exec(select(Idea)).all())
    by_status = {s: sum(1 for i in ideas if i.status == s) for s in STATUSES}
    if json_out:
        render_record({"by_status": by_status, "total": len(ideas)}, json_out=True)
        return
    if not ideas:
        console.print("\n  [dim]No ideas captured yet.[/dim]\n")
        return
    render_rows(
        [{"status": s, "count": by_status[s]} for s in STATUSES],
        [("status", "Status"), ("count", "Count")],
        json_out=False,
        title="📊 Idea pipeline",
        formatters={"status": lambda v, r: _status_cell(v)},
    )


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Idea stats."""
    with session() as db:
        ideas = list(db.exec(select(Idea)).all())
    data = {
        "total": len(ideas),
        "open": sum(1 for i in ideas if i.status in OPEN_STATUSES),
        "shipped": sum(1 for i in ideas if i.status == "shipped"),
        "abandoned": sum(1 for i in ideas if i.status == "abandoned"),
        "by_status": {s: sum(1 for i in ideas if i.status == s) for s in STATUSES},
    }
    render_record(data, json_out=json_out, title="📊 Idea stats")
