"""🗓️ meetings — meeting notes & action items."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, console, fail, ok, render_record, render_rows

NAME = "meetings"
HELP = "🗓️ Meeting notes & action items"
EMOJI = "🗓️"


class Meeting(SQLModel, table=True):
    """A meeting with notes and attendees."""

    __tablename__ = "meetings_meeting"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    meeting_date: date = Field(default_factory=date.today, index=True)
    attendees: str | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


class ActionItem(SQLModel, table=True):
    """A follow-up action that came out of a meeting."""

    __tablename__ = "meetings_action"

    id: int | None = Field(default=None, primary_key=True)
    meeting_id: int = Field(index=True)
    summary: str
    owner: str | None = None
    done: bool = False
    done_at: date | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context, json_out: JsonOpt = False) -> None:
    """Default: ``clibo meetings`` (bare) lists recent meetings (last 30d)."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(list_meetings, days=30, json_out=json_out)


def _resolve(db, ident: str) -> Meeting | None:
    """Look up a meeting by numeric ID, exact title, then substring (most-recent wins).

    Matches the iter-84/85 pattern across the codebase: integer ID
    first, exact case-insensitive title, then a fuzzy substring
    match preferring the most-recently-added row.
    """
    from clibo.core.base import lookup_by_id_or_name
    if ident.isdigit():
        meeting = db.get(Meeting, int(ident))
        if meeting:
            return meeting
    # Exact wins, then fall back to substring with most-recent.
    return db.exec(
        select(Meeting).where(Meeting.title.ilike(ident))
        .order_by(Meeting.id.desc())
    ).first() or db.exec(
        select(Meeting).where(Meeting.title.ilike(f"%{ident}%"))
        .order_by(Meeting.id.desc())
    ).first() or lookup_by_id_or_name(db, Meeting, ident, Meeting.title)


def _row(db, meeting: Meeting) -> dict:
    actions = db.exec(select(ActionItem).where(ActionItem.meeting_id == meeting.id)).all()
    return {
        "id": meeting.id,
        "title": meeting.title,
        "meeting_date": meeting.meeting_date,
        "attendees": meeting.attendees,
        "notes": meeting.notes,
        "action_items": len(actions),
        "open_actions": sum(1 for a in actions if not a.done),
    }


@app.command()
def add(
    title: str = typer.Argument(..., help="Meeting title"),
    on: str = typer.Option("today", "--date", "-d", help="Meeting date"),
    attendees: str = typer.Option(None, "--attendees", "-a", help="Comma-separated attendees"),
    notes: str = typer.Option(None, "--notes", "-N", help="Meeting notes"),
    action_items: list[str] = typer.Option(
        [], "--action", "-A",
        help="Action item — repeat for multiple, "
             "use 'OWNER: summary' to set the owner inline",
    ),
    json_out: JsonOpt = False,
) -> None:
    """🗓️ Record a meeting.

    Pass ``--action`` (or ``-A``) one or more times to capture action
    items inline at creation — saves a follow-up ``meetings action``
    call for the natural *"we discussed X, Bob will do Y"* flow.
    Prefix with ``OWNER:`` to set the owner: ``-A "Bob: send timeline"``.
    """
    meeting = Meeting(title=title, meeting_date=parse_date(on),
                       attendees=attendees, notes=notes)
    with session() as db:
        db.add(meeting)
        db.flush()
        db.refresh(meeting)
        for raw in action_items:
            if not raw.strip():
                continue
            # "Bob: send timeline" → owner=Bob, summary=send timeline
            if ":" in raw:
                owner, _, summary = raw.partition(":")
                owner = owner.strip() or None
                summary = summary.strip()
            else:
                owner = None
                summary = raw.strip()
            if summary:
                db.add(ActionItem(
                    meeting_id=meeting.id, summary=summary, owner=owner
                ))
        db.flush()
        data = _row(db, meeting)
    suffix = (f" · {data['action_items']} action item"
              f"{'s' if data['action_items'] != 1 else ''}"
              if data["action_items"] else "")
    ok(f"Added {EMOJI} meeting '{title}' ({meeting.meeting_date}){suffix}",
       json_out=json_out, data=data)


@app.command(name="list")
def list_meetings(
    days: int = typer.Option(30, "--days", help="Look back this many days"),
    json_out: JsonOpt = False,
) -> None:
    """🗓️ List recent meetings."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        meetings = list(
            db.exec(
                select(Meeting)
                .where(Meeting.meeting_date >= since)
                .order_by(Meeting.meeting_date.desc(), Meeting.id.desc())
            ).all()
        )
        rows = [_row(db, m) for m in meetings]
    render_rows(
        rows,
        [("id", "ID"), ("meeting_date", "Date"), ("title", "Title"),
         ("attendees", "Attendees"), ("open_actions", "Open Actions")],
        json_out=json_out,
        title="🗓️ Meetings",
        empty="No meetings yet — try: clibo meetings add 'Weekly sync'",
    )


@app.command()
def show(
    meeting: str = typer.Argument(..., help="Meeting title or ID"),
    json_out: JsonOpt = False,
) -> None:
    """🗓️ Show a meeting with its notes and action items."""
    with session() as db:
        target = _resolve(db, meeting)
        if not target:
            fail(f"No meeting matching {meeting!r}", json_out=json_out)
        data = _row(db, target)
        actions = [
            {"id": a.id, "summary": a.summary, "owner": a.owner, "done": a.done}
            for a in db.exec(
                select(ActionItem).where(ActionItem.meeting_id == target.id).order_by(ActionItem.id)
            ).all()
        ]
    if json_out:
        render_record(data | {"actions": actions}, json_out=True)
        return
    render_record(data, json_out=False, title=f"🗓️ {target.title}")
    if target.notes:
        console.print(target.notes)
    render_rows(
        actions,
        [("id", "ID"), ("done", "✓"), ("summary", "Action item"), ("owner", "Owner")],
        json_out=False,
        title="Action items",
        empty="No action items — add with: clibo meetings action <meeting> '<task>'",
    )


@app.command()
def action(
    meeting: str = typer.Argument(..., help="Meeting title or ID"),
    summary: str = typer.Argument(..., help="The action item"),
    owner: str = typer.Option(None, "--owner", "-o", help="Who owns it"),
    json_out: JsonOpt = False,
) -> None:
    """🗓️ Add an action item to a meeting."""
    with session() as db:
        target = _resolve(db, meeting)
        if not target:
            fail(f"No meeting matching {meeting!r}", json_out=json_out)
        item = ActionItem(meeting_id=target.id, summary=summary, owner=owner)
        db.add(item)
        db.flush()
        db.refresh(item)
        data = {"id": item.id, "meeting": target.title, "summary": summary,
                "owner": owner, "done": False}
    ok(f"Added action item to '{target.title}': {summary}", json_out=json_out, data=data)


@app.command()
def check(action_id: int = typer.Argument(..., help="Action item ID"), json_out: JsonOpt = False) -> None:
    """🗓️ Mark an action item as done."""
    with session() as db:
        item = db.get(ActionItem, action_id)
        if not item:
            fail(f"No action item #{action_id}", json_out=json_out)
        item.done = True
        item.done_at = date.today()
        db.add(item)
        db.flush()
        data = {"id": item.id, "summary": item.summary, "done": True}
    ok(f"Action item done ✓: {item.summary}", json_out=json_out, data=data)


@app.command()
def actions(json_out: JsonOpt = False) -> None:
    """📋 List all open action items across meetings."""
    with session() as db:
        items = list(
            db.exec(select(ActionItem).where(ActionItem.done == False)).all()  # noqa: E712
        )
        titles = {m.id: m.title for m in db.exec(select(Meeting)).all()}
    rows = [
        {"id": a.id, "summary": a.summary, "owner": a.owner,
         "meeting": titles.get(a.meeting_id, "?")}
        for a in items
    ]
    render_rows(
        rows,
        [("id", "ID"), ("summary", "Action item"), ("owner", "Owner"), ("meeting", "Meeting")],
        json_out=json_out,
        title="📋 Open action items",
        empty="No open action items — all clear! ✨",
    )


@app.command()
def edit(
    meeting: str = typer.Argument(..., help="Meeting title (fuzzy) or ID"),
    title: str = typer.Option(None, "--title", "-t", help="New title"),
    on: str = typer.Option(None, "--date", "-d", help="New date"),
    attendees: str = typer.Option(
        None, "--attendees", "-a", help="New attendees (comma-separated)"
    ),
    notes: str = typer.Option(None, "--notes", "-N", help="Replace the notes"),
    json_out: JsonOpt = False,
) -> None:
    """🗓️ Edit a meeting. Accepts a numeric ID or a title (fuzzy)."""
    with session() as db:
        target = _resolve(db, meeting)
        if not target:
            fail(f"No meeting matching {meeting!r}", json_out=json_out)
        if title is not None:
            target.title = title
        if on is not None:
            target.meeting_date = parse_date(on)
        if attendees is not None:
            target.attendees = attendees
        if notes is not None:
            target.notes = notes
        db.add(target)
        db.flush()
        data = _row(db, target)
    ok(f"Updated meeting #{target.id} — {target.title}",
       json_out=json_out, data=data)


@app.command()
def rm(
    meeting: str = typer.Argument(..., help="Meeting title (fuzzy) or ID"),
    json_out: JsonOpt = False,
) -> None:
    """🗓️ Delete a meeting and all its action items."""
    with session() as db:
        target = _resolve(db, meeting)
        if not target:
            fail(f"No meeting matching {meeting!r}", json_out=json_out)
        mid = target.id
        for item in db.exec(select(ActionItem).where(ActionItem.meeting_id == mid)).all():
            db.delete(item)
        db.delete(target)
    ok(f"Deleted meeting #{mid}", json_out=json_out, data={"deleted": mid})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Meeting stats."""
    with session() as db:
        meetings = list(db.exec(select(Meeting)).all())
        items = list(db.exec(select(ActionItem)).all())
    data = {
        "total_meetings": len(meetings),
        "action_items": len(items),
        "open_actions": sum(1 for a in items if not a.done),
        "done_actions": sum(1 for a in items if a.done),
    }
    render_record(data, json_out=json_out, title="📊 Meeting stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `update` is the SQL-natural synonym for `edit`; both work.
app.command(name="update", help="Alias for `edit`")(edit)

# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
