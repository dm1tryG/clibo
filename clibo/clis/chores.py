"""🧹 chores — household chores rotation."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import humanize_delta
from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "chores"
HELP = "🧹 Household chores rotation"
EMOJI = "🧹"


class Chore(SQLModel, table=True):
    """A recurring household chore."""

    __tablename__ = "chores_chore"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    frequency_days: int = 7
    assignee: str | None = None
    last_done: date | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context, json_out: JsonOpt = False) -> None:
    """Default: ``clibo chores`` (bare) runs the ``due`` summary."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(due, json_out=json_out)


def _resolve(db, ident: str) -> Chore | None:
    """Look up a chore by numeric ID or by (case-insensitive) name."""
    if ident.isdigit():
        chore = db.get(Chore, int(ident))
        if chore:
            return chore
    return db.exec(select(Chore).where(Chore.name.ilike(ident))).first()


def _next_due(chore: Chore) -> date:
    """When the chore is next due (today if it has never been done)."""
    if chore.last_done is None:
        return date.today()
    return chore.last_done + timedelta(days=chore.frequency_days)


def _status(chore: Chore) -> str:
    days = (_next_due(chore) - date.today()).days
    if days < 0:
        return "overdue"
    if days == 0:
        return "due"
    return "upcoming"


def _row(chore: Chore) -> dict:
    nxt = _next_due(chore)
    return {
        "id": chore.id,
        "name": chore.name,
        "frequency_days": chore.frequency_days,
        "assignee": chore.assignee,
        "last_done": chore.last_done,
        "next_due": nxt,
        "due_in": humanize_delta(nxt),
        "status": _status(chore),
    }


def _status_cell(status: str) -> str:
    return {
        "overdue": "[red]⚠ overdue[/red]",
        "due": "[yellow]⏰ due[/yellow]",
        "upcoming": "[green]upcoming[/green]",
    }.get(status, status)


@app.command()
def add(
    name: str = typer.Argument(..., help="Chore name, e.g. 'Vacuum'"),
    every: int = typer.Option(7, "--every", "-e", help="Repeat every N days"),
    assignee: str = typer.Option(None, "--assignee", "-a", help="Who does it"),
    json_out: JsonOpt = False,
) -> None:
    """🧹 Add a recurring chore."""
    if every < 1:
        fail("Frequency must be at least 1 day", json_out=json_out)
    chore = Chore(name=name, frequency_days=every, assignee=assignee)
    with session() as db:
        db.add(chore)
        db.flush()
        db.refresh(chore)
        data = _row(chore)
    ok(f"Added {EMOJI} chore '{name}' (every {every}d)", json_out=json_out, data=data)


@app.command(name="list")
def list_chores(json_out: JsonOpt = False) -> None:
    """🧹 List chores, soonest due first."""
    with session() as db:
        chores = list(db.exec(select(Chore)).all())
    rows = sorted((_row(c) for c in chores), key=lambda r: r["next_due"])
    render_rows(
        rows,
        [("id", "ID"), ("name", "Chore"), ("assignee", "Assignee"),
         ("frequency_days", "Every"), ("next_due", "Next Due"),
         ("due_in", "When"), ("status", "Status")],
        json_out=json_out,
        title="🧹 Chores",
        formatters={
            "frequency_days": lambda v, r: f"{v}d",
            "status": lambda v, r: _status_cell(v),
        },
        empty="No chores yet — try: clibo chores add 'Take out trash' -e 3",
    )


@app.command()
def done(
    chore: str = typer.Argument(..., help="Chore name or ID"),
    json_out: JsonOpt = False,
) -> None:
    """🧹 Mark a chore as done today."""
    with session() as db:
        target = _resolve(db, chore)
        if not target:
            fail(f"No chore matching {chore!r}", json_out=json_out)
        target.last_done = date.today()
        db.add(target)
        db.flush()
        data = _row(target)
    ok(f"Done {EMOJI} {target.name} — next due {data['next_due']}",
       json_out=json_out, data=data)


@app.command()
def due(json_out: JsonOpt = False) -> None:
    """🔔 Chores that are due or overdue."""
    with session() as db:
        chores = list(db.exec(select(Chore)).all())
    rows = sorted(
        (r for c in chores if (r := _row(c))["status"] in ("due", "overdue")),
        key=lambda r: r["next_due"],
    )
    render_rows(
        rows,
        [("id", "ID"), ("name", "Chore"), ("assignee", "Assignee"),
         ("due_in", "When"), ("status", "Status")],
        json_out=json_out,
        title="🔔 Chores due now",
        formatters={"status": lambda v, r: _status_cell(v)},
        empty="Nothing due — the house is in order! ✨",
    )


@app.command()
def rm(chore_id: int = typer.Argument(..., help="Chore ID"), json_out: JsonOpt = False) -> None:
    """🧹 Delete a chore."""
    with session() as db:
        chore = db.get(Chore, chore_id)
        if not chore:
            fail(f"No chore #{chore_id}", json_out=json_out)
        db.delete(chore)
    ok(f"Deleted chore #{chore_id}", json_out=json_out, data={"deleted": chore_id})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Chore stats."""
    with session() as db:
        chores = list(db.exec(select(Chore)).all())
    rows = [_row(c) for c in chores]
    data = {
        "total": len(chores),
        "overdue": sum(1 for r in rows if r["status"] == "overdue"),
        "due": sum(1 for r in rows if r["status"] == "due"),
        "assignees": len({c.assignee for c in chores if c.assignee}),
    }
    render_record(data, json_out=json_out, title="📊 Chore stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
