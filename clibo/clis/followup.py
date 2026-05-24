"""🔔 followup — follow-up reminders for people."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import humanize_delta, parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "followup"
HELP = "🔔 Follow-up reminders for people"
EMOJI = "🔔"


class FollowUp(SQLModel, table=True):
    """A reminder to get back in touch with someone."""

    __tablename__ = "followup_followup"

    id: int | None = Field(default=None, primary_key=True)
    person: str
    reason: str | None = None
    due_date: date = Field(index=True)
    done: bool = False
    done_at: date | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context) -> None:
    """Default: ``clibo followup`` (bare) runs the ``due`` summary."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(due, days=7, json_out=False)


def _resolve(db, ident: str) -> FollowUp | None:
    """Look up a follow-up by numeric ID or by person name.

    For names, prefers a pending (not-done) follow-up; falls back to the
    most-recently-due one. People with multiple follow-ups: pass the ID
    to disambiguate.
    """
    if ident.isdigit():
        fu = db.get(FollowUp, int(ident))
        if fu:
            return fu
    # Pending follow-ups first.
    pending = db.exec(
        select(FollowUp)
        .where(FollowUp.person.ilike(f"%{ident}%"))
        .where(FollowUp.done == False)  # noqa: E712
        .order_by(FollowUp.due_date)
    ).first()
    if pending:
        return pending
    return db.exec(
        select(FollowUp)
        .where(FollowUp.person.ilike(f"%{ident}%"))
        .order_by(FollowUp.due_date.desc())
    ).first()


def _status(fu: FollowUp) -> str:
    if fu.done:
        return "done"
    days = (fu.due_date - date.today()).days
    if days < 0:
        return "overdue"
    if days <= 2:
        return "due soon"
    return "upcoming"


def _row(fu: FollowUp) -> dict:
    return {
        "id": fu.id,
        "person": fu.person,
        "reason": fu.reason,
        "due_date": fu.due_date,
        "due_in": humanize_delta(fu.due_date),
        "days_until_due": (fu.due_date - date.today()).days,
        "status": _status(fu),
        "done": fu.done,
        "note": fu.note,
    }


def _status_cell(status: str) -> str:
    return {
        "done": "[green]✓ done[/green]",
        "overdue": "[red]⚠ overdue[/red]",
        "due soon": "[yellow]⏰ due soon[/yellow]",
        "upcoming": "[cyan]upcoming[/cyan]",
    }.get(status, status)


@app.command()
def add(
    person: str = typer.Argument(..., help="Who to follow up with"),
    due: str = typer.Option(..., "--due", "-d", help="When to follow up"),
    reason: str = typer.Option(None, "--reason", "-r", help="Why follow up"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🔔 Add a follow-up reminder."""
    fu = FollowUp(person=person, due_date=parse_date(due), reason=reason, note=note)
    with session() as db:
        db.add(fu)
        db.flush()
        db.refresh(fu)
        data = _row(fu)
    ok(f"Added {EMOJI} follow-up with {person} — due {fu.due_date} ({data['due_in']})",
       json_out=json_out, data=data)


@app.command(name="list")
def list_followups(
    show_all: bool = typer.Option(False, "--all", help="Include completed follow-ups"),
    json_out: JsonOpt = False,
) -> None:
    """🔔 List follow-ups, soonest due first."""
    with session() as db:
        query = select(FollowUp)
        if not show_all:
            query = query.where(FollowUp.done == False)  # noqa: E712
        followups = list(db.exec(query.order_by(FollowUp.due_date)).all())
    render_rows(
        [_row(f) for f in followups],
        [("id", "ID"), ("person", "Person"), ("reason", "Reason"),
         ("due_date", "Due"), ("due_in", "When"), ("status", "Status")],
        json_out=json_out,
        title="🔔 Follow-ups",
        formatters={"status": lambda v, r: _status_cell(v)},
        empty="No follow-ups — try: clibo followup add 'Anna' -d 2026-06-01 -r 'send proposal'",
    )


@app.command()
def done(
    followup: str = typer.Argument(..., help="Follow-up ID or person name"),
    json_out: JsonOpt = False,
) -> None:
    """🔔 Mark a follow-up as done. Accepts a numeric ID or a person name."""
    with session() as db:
        fu = _resolve(db, followup)
        if not fu:
            fail(f"No follow-up matching {followup!r}", json_out=json_out)
        fu.done = True
        fu.done_at = date.today()
        db.add(fu)
        db.flush()
        data = _row(fu)
    ok(f"Followed up with {fu.person} ✓", json_out=json_out, data=data)


@app.command()
def due(
    days: int = typer.Option(7, "--days", help="Look ahead this many days"),
    json_out: JsonOpt = False,
) -> None:
    """🔔 Follow-ups that are overdue or due soon."""
    horizon = date.today() + timedelta(days=days)
    with session() as db:
        followups = list(
            db.exec(
                select(FollowUp)
                .where(FollowUp.done == False)  # noqa: E712
                .where(FollowUp.due_date <= horizon)
                .order_by(FollowUp.due_date)
            ).all()
        )
    render_rows(
        [_row(f) for f in followups],
        [("id", "ID"), ("person", "Person"), ("reason", "Reason"),
         ("due_date", "Due"), ("due_in", "When"), ("status", "Status")],
        json_out=json_out,
        title=f"🔔 Follow-ups due within {days} days",
        formatters={"status": lambda v, r: _status_cell(v)},
        empty="Nothing to follow up on — you're on top of it! ✨",
    )


@app.command()
def snooze(
    followup: str = typer.Argument(..., help="Follow-up ID or person name"),
    days: int = typer.Option(7, "--days", help="Push the due date out by this many days"),
    json_out: JsonOpt = False,
) -> None:
    """😴 Push a follow-up's due date later."""
    with session() as db:
        fu = _resolve(db, followup)
        if not fu:
            fail(f"No follow-up matching {followup!r}", json_out=json_out)
        fu.due_date = date.today() + timedelta(days=days)
        db.add(fu)
        db.flush()
        data = _row(fu)
    ok(f"Snoozed follow-up with {fu.person} to {fu.due_date}",
       json_out=json_out, data=data)


@app.command()
def rm(
    followup: str = typer.Argument(..., help="Follow-up ID or person name"),
    json_out: JsonOpt = False,
) -> None:
    """🔔 Delete a follow-up."""
    with session() as db:
        fu = _resolve(db, followup)
        if not fu:
            fail(f"No follow-up matching {followup!r}", json_out=json_out)
        fid = fu.id
        db.delete(fu)
    ok(f"Deleted follow-up #{fid}", json_out=json_out, data={"deleted": fid})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Follow-up stats."""
    with session() as db:
        followups = list(db.exec(select(FollowUp)).all())
    pending = [f for f in followups if not f.done]
    overdue = [f for f in pending if f.due_date < date.today()]
    data = {
        "total": len(followups),
        "pending": len(pending),
        "overdue": len(overdue),
        "done": sum(1 for f in followups if f.done),
    }
    render_record(data, json_out=json_out, title="📊 Follow-up stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
