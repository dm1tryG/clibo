"""👥 crm — contacts CRM."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlalchemy import or_
from sqlmodel import Field, SQLModel, select

from clibo.core.base import humanize_delta, parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "crm"
HELP = "👥 Contacts CRM"
EMOJI = "👥"
STATUSES = ["lead", "active", "customer", "cold"]


class Contact(SQLModel, table=True):
    """A person or company in your contacts."""

    __tablename__ = "crm_contact"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    company: str | None = None
    email: str | None = None
    phone: str | None = None
    tags: str | None = None
    status: str = "active"
    notes: str | None = None
    last_contact: date | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _resolve(db, ident: str) -> Contact | None:
    """Look up a contact by numeric ID or by (case-insensitive) name match."""
    if ident.isdigit():
        contact = db.get(Contact, int(ident))
        if contact:
            return contact
    return db.exec(
        select(Contact).where(Contact.name.ilike(f"%{ident}%"))
    ).first()


def _row(contact: Contact) -> dict:
    return {
        "id": contact.id,
        "name": contact.name,
        "company": contact.company,
        "email": contact.email,
        "phone": contact.phone,
        "tags": contact.tags,
        "status": contact.status,
        "last_contact": contact.last_contact,
        "last_contact_ago": humanize_delta(contact.last_contact) if contact.last_contact else None,
        "notes": contact.notes,
    }


def _status_cell(status: str) -> str:
    return {
        "lead": "[yellow]lead[/yellow]",
        "active": "[green]active[/green]",
        "customer": "[cyan]customer[/cyan]",
        "cold": "[dim]cold[/dim]",
    }.get(status, status)


@app.command()
def add(
    name: str = typer.Argument(..., help="Contact name"),
    company: str = typer.Option(None, "--company", "-c", help="Company"),
    email: str = typer.Option(None, "--email", "-e", help="Email address"),
    phone: str = typer.Option(None, "--phone", "-p", help="Phone number"),
    tag: str = typer.Option(None, "--tag", "-t", help="Comma-separated tags"),
    status: str = typer.Option("active", "--status", "-s", help="lead/active/customer/cold"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """👥 Add a contact."""
    status = status.lower()
    if status not in STATUSES:
        fail(f"Status must be one of: {', '.join(STATUSES)}", json_out=json_out)
    contact = Contact(
        name=name, company=company, email=email, phone=phone,
        tags=tag, status=status, notes=note,
    )
    with session() as db:
        db.add(contact)
        db.flush()
        db.refresh(contact)
        data = _row(contact)
    ok(f"Added {EMOJI} {name}" + (f" ({company})" if company else ""),
       json_out=json_out, data=data)


@app.command(name="list")
def list_contacts(
    status: str = typer.Option(None, "--status", "-s", help="Filter by status"),
    tag: str = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    json_out: JsonOpt = False,
) -> None:
    """👥 List contacts."""
    if status and status.lower() not in STATUSES:
        fail(f"Status must be one of: {', '.join(STATUSES)}", json_out=json_out)
    with session() as db:
        query = select(Contact)
        if status:
            query = query.where(Contact.status == status.lower())
        if tag:
            query = query.where(Contact.tags.ilike(f"%{tag}%"))
        contacts = list(db.exec(query.order_by(Contact.name)).all())
    render_rows(
        [_row(c) for c in contacts],
        [("id", "ID"), ("name", "Name"), ("company", "Company"),
         ("status", "Status"), ("email", "Email"), ("last_contact_ago", "Last Contact")],
        json_out=json_out,
        title="👥 Contacts",
        formatters={"status": lambda v, r: _status_cell(v)},
        empty="No contacts yet — try: clibo crm add 'Anna Petrova' -c Acme",
    )


@app.command()
def show(
    contact: str = typer.Argument(..., help="Contact ID or name (fuzzy match)"),
    json_out: JsonOpt = False,
) -> None:
    """👥 Show one contact in detail. Accepts a numeric ID or a name."""
    with session() as db:
        target = _resolve(db, contact)
        if not target:
            fail(f"No contact matching {contact!r}", json_out=json_out)
        data = _row(target) | {"created_at": target.created_at}
    render_record(data, json_out=json_out, title=f"👥 {data['name']}")


@app.command()
def edit(
    contact: str = typer.Argument(..., help="Contact ID or name (fuzzy match)"),
    name: str = typer.Option(None, "--name", help="New name"),
    company: str = typer.Option(None, "--company", "-c"),
    email: str = typer.Option(None, "--email", "-e"),
    phone: str = typer.Option(None, "--phone", "-p"),
    tag: str = typer.Option(None, "--tag", "-t"),
    status: str = typer.Option(None, "--status", "-s"),
    note: str = typer.Option(None, "--note", "-n"),
    json_out: JsonOpt = False,
) -> None:
    """👥 Edit a contact. Accepts a numeric ID or a name."""
    if status and status.lower() not in STATUSES:
        fail(f"Status must be one of: {', '.join(STATUSES)}", json_out=json_out)
    with session() as db:
        target = _resolve(db, contact)
        if not target:
            fail(f"No contact matching {contact!r}", json_out=json_out)
        for field, value in {"name": name, "company": company, "email": email,
                             "phone": phone, "tags": tag, "notes": note}.items():
            if value is not None:
                setattr(target, field, value)
        if status is not None:
            target.status = status.lower()
        db.add(target)
        db.flush()
        data = _row(target)
    ok(f"Updated contact #{target.id}", json_out=json_out, data=data)


@app.command()
def touch(
    contact: str = typer.Argument(..., help="Contact ID or name (fuzzy match)"),
    on: str = typer.Option("today", "--date", "-d", help="Date of contact"),
    json_out: JsonOpt = False,
) -> None:
    """🤝 Record that you were in touch with a contact."""
    with session() as db:
        target = _resolve(db, contact)
        if not target:
            fail(f"No contact matching {contact!r}", json_out=json_out)
        target.last_contact = parse_date(on)
        db.add(target)
        db.flush()
        data = _row(target)
    ok(f"Logged contact with {target.name}", json_out=json_out, data=data)


@app.command()
def search(
    query: str = typer.Argument(..., help="Text to search for"),
    json_out: JsonOpt = False,
) -> None:
    """🔍 Search contacts by name, company, email or tags."""
    pattern = f"%{query}%"
    with session() as db:
        contacts = list(
            db.exec(
                select(Contact).where(
                    or_(
                        Contact.name.ilike(pattern),
                        Contact.company.ilike(pattern),
                        Contact.email.ilike(pattern),
                        Contact.tags.ilike(pattern),
                    )
                ).order_by(Contact.name)
            ).all()
        )
    render_rows(
        [_row(c) for c in contacts],
        [("id", "ID"), ("name", "Name"), ("company", "Company"),
         ("status", "Status"), ("email", "Email")],
        json_out=json_out,
        title=f"🔍 Contacts matching '{query}'",
        formatters={"status": lambda v, r: _status_cell(v)},
        empty=f"No contacts match '{query}'.",
    )


@app.command()
def rm(
    contact: str = typer.Argument(..., help="Contact ID or name (fuzzy match)"),
    json_out: JsonOpt = False,
) -> None:
    """👥 Delete a contact. Accepts a numeric ID or a name."""
    with session() as db:
        target = _resolve(db, contact)
        if not target:
            fail(f"No contact matching {contact!r}", json_out=json_out)
        cid = target.id
        db.delete(target)
    ok(f"Deleted contact #{cid}", json_out=json_out, data={"deleted": cid})


@app.command()
def dormant(
    days: int = typer.Option(
        90, "--days", "-d",
        help="Threshold in days since last contact (default 90)",
    ),
    include_never: bool = typer.Option(
        True, "--include-never/--skip-never",
        help="Include contacts you've never touched (default: include)",
    ),
    json_out: JsonOpt = False,
) -> None:
    """🥶 List contacts you haven't touched in a while.

    Surfaces the data `crm touch` collects: who's overdue for a check-in.
    Sorted oldest-touch first, with never-contacted at the top.
    """
    if days < 0:
        fail("--days must be non-negative", json_out=json_out)
    cutoff = date.today() - timedelta(days=days)
    with session() as db:
        contacts = list(
            db.exec(
                select(Contact).where(Contact.status == "active")
            ).all()
        )
    dormant_rows = []
    for c in contacts:
        if c.last_contact is None:
            if include_never:
                dormant_rows.append(c)
        elif c.last_contact <= cutoff:
            dormant_rows.append(c)
    # Sort: never-contacted first, then oldest last_contact first.
    dormant_rows.sort(
        key=lambda c: (c.last_contact is not None,
                       c.last_contact or date.min)
    )
    rows = [_row(c) | {
        "last_contact_ago": (
            humanize_delta(c.last_contact) if c.last_contact else "never"
        ),
    } for c in dormant_rows]
    render_rows(
        rows,
        [("id", "ID"), ("name", "Name"), ("company", "Company"),
         ("last_contact_ago", "Last contact"), ("status", "Status")],
        json_out=json_out,
        title=f"🥶 Dormant contacts · >{days}d since touch",
        empty=f"Nobody's gone dormant (everyone touched within {days} days).",
    )


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Contact stats by status."""
    with session() as db:
        contacts = list(db.exec(select(Contact)).all())
    by_status = {s: sum(1 for c in contacts if c.status == s) for s in STATUSES}
    data = {
        "total": len(contacts),
        "by_status": by_status,
        "with_company": sum(1 for c in contacts if c.company),
        "never_contacted": sum(1 for c in contacts if not c.last_contact),
    }
    render_record(data, json_out=json_out, title="📊 CRM stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `update` is the SQL-natural synonym for `edit`; both work.
app.command(name="update", help="Alias for `edit`")(edit)

# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
