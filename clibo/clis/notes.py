"""📝 notes — quick searchable notes."""

from __future__ import annotations

from datetime import datetime

import typer
from sqlalchemy import or_
from sqlmodel import Field, SQLModel, select

from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "notes"
HELP = "📝 Quick searchable notes"
EMOJI = "📝"


class Note(SQLModel, table=True):
    """A short text note with optional tags."""

    __tablename__ = "notes_note"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    body: str = ""
    tags: str | None = None
    pinned: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context, json_out: JsonOpt = False) -> None:
    """Default: ``clibo notes`` (bare) lists notes — pinned first."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(list_notes, tag=None, json_out=json_out)


def _preview(body: str, width: int = 48) -> str:
    """A one-line preview of a note body."""
    flat = " ".join(body.split())
    return flat if len(flat) <= width else flat[: width - 1] + "…"


def _row(note: Note) -> dict:
    return {
        "id": note.id,
        "title": note.title,
        "body": note.body,
        "preview": _preview(note.body),
        "tags": note.tags,
        "pinned": note.pinned,
        "updated_at": note.updated_at,
    }


def _sorted(notes: list[Note]) -> list[Note]:
    """Pinned notes first, then most recently updated."""
    return sorted(notes, key=lambda n: (n.pinned, n.updated_at), reverse=True)


@app.command()
def add(
    title: str = typer.Argument(..., help="Note title"),
    body: str = typer.Option("", "--body", "-b", help="Note text"),
    tag: str = typer.Option(None, "--tag", "-t", help="Comma-separated tags"),
    json_out: JsonOpt = False,
) -> None:
    """📝 Create a note."""
    note = Note(title=title, body=body, tags=tag)
    with session() as db:
        db.add(note)
        db.flush()
        db.refresh(note)
        data = _row(note)
    ok(f"Saved {EMOJI} note #{note.id}: {title}", json_out=json_out, data=data)


@app.command(name="list")
def list_notes(
    tag: str = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    json_out: JsonOpt = False,
) -> None:
    """📝 List notes (pinned first, then newest)."""
    with session() as db:
        query = select(Note)
        if tag:
            query = query.where(Note.tags.ilike(f"%{tag}%"))
        notes = _sorted(list(db.exec(query).all()))
    render_rows(
        [_row(n) for n in notes],
        [("id", "ID"), ("pinned", "📌"), ("title", "Title"),
         ("preview", "Preview"), ("tags", "Tags"), ("updated_at", "Updated")],
        json_out=json_out,
        title="📝 Notes",
        formatters={"pinned": lambda v, r: "📌" if v else "[dim]·[/dim]"},
        empty="No notes yet — try: clibo notes add 'Idea' -b 'build a thing'",
    )


@app.command()
def show(note_id: int = typer.Argument(..., help="Note ID"), json_out: JsonOpt = False) -> None:
    """📝 Show a note's full text."""
    with session() as db:
        note = db.get(Note, note_id)
        if not note:
            fail(f"No note #{note_id}", json_out=json_out)
        data = _row(note) | {"created_at": note.created_at}
    if json_out:
        render_record(data, json_out=True)
        return
    render_record(
        {"id": note.id, "title": note.title, "tags": note.tags,
         "pinned": note.pinned, "updated_at": note.updated_at},
        json_out=False,
        title=f"📝 Note #{note_id}",
    )
    from clibo.core.output import console

    console.print(note.body or "[dim](empty)[/dim]")


@app.command()
def search(
    query: str = typer.Argument(..., help="Text to search for in titles and bodies"),
    json_out: JsonOpt = False,
) -> None:
    """🔍 Search notes by title or body text."""
    pattern = f"%{query}%"
    with session() as db:
        notes = _sorted(
            list(
                db.exec(
                    select(Note).where(or_(Note.title.ilike(pattern), Note.body.ilike(pattern)))
                ).all()
            )
        )
    render_rows(
        [_row(n) for n in notes],
        [("id", "ID"), ("title", "Title"), ("preview", "Preview"), ("tags", "Tags")],
        json_out=json_out,
        title=f"🔍 Notes matching '{query}'",
        empty=f"No notes match '{query}'.",
    )


@app.command()
def edit(
    note_id: int = typer.Argument(..., help="Note ID"),
    title: str = typer.Option(None, "--title", help="New title"),
    body: str = typer.Option(None, "--body", "-b", help="New body text"),
    tag: str = typer.Option(None, "--tag", "-t", help="New tags"),
    json_out: JsonOpt = False,
) -> None:
    """📝 Edit a note."""
    with session() as db:
        note = db.get(Note, note_id)
        if not note:
            fail(f"No note #{note_id}", json_out=json_out)
        if title is not None:
            note.title = title
        if body is not None:
            note.body = body
        if tag is not None:
            note.tags = tag
        note.updated_at = datetime.now()
        db.add(note)
        db.flush()
        data = _row(note)
    ok(f"Updated note #{note_id}", json_out=json_out, data=data)


@app.command()
def pin(note_id: int = typer.Argument(..., help="Note ID"), json_out: JsonOpt = False) -> None:
    """📌 Pin a note to the top."""
    _set_pinned(note_id, True, json_out)


@app.command()
def unpin(note_id: int = typer.Argument(..., help="Note ID"), json_out: JsonOpt = False) -> None:
    """📌 Unpin a note."""
    _set_pinned(note_id, False, json_out)


def _set_pinned(note_id: int, pinned: bool, json_out: bool) -> None:
    with session() as db:
        note = db.get(Note, note_id)
        if not note:
            fail(f"No note #{note_id}", json_out=json_out)
        note.pinned = pinned
        db.add(note)
    verb = "Pinned" if pinned else "Unpinned"
    ok(f"{verb} note #{note_id}", json_out=json_out, data={"id": note_id, "pinned": pinned})


@app.command()
def rm(note_id: int = typer.Argument(..., help="Note ID"), json_out: JsonOpt = False) -> None:
    """📝 Delete a note."""
    with session() as db:
        note = db.get(Note, note_id)
        if not note:
            fail(f"No note #{note_id}", json_out=json_out)
        db.delete(note)
    ok(f"Deleted note #{note_id}", json_out=json_out, data={"deleted": note_id})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Note stats."""
    with session() as db:
        notes = list(db.exec(select(Note)).all())
    data = {
        "total": len(notes),
        "pinned": sum(1 for n in notes if n.pinned),
        "tagged": sum(1 for n in notes if n.tags),
    }
    render_record(data, json_out=json_out, title="📊 Notes stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `update` is the SQL-natural synonym for `edit`; both work.
app.command(name="update", help="Alias for `edit`")(edit)

# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
