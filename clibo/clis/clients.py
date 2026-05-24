"""🧑‍💼 clients — freelance client manager."""

from __future__ import annotations

from datetime import date, datetime

import typer
from sqlmodel import Field, SQLModel, select

from clibo.clis.expense import get_currency, money
from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "clients"
HELP = "🧑‍💼 Freelance client manager"
EMOJI = "🧑‍💼"
STATUSES = ["prospect", "active", "past"]


class Client(SQLModel, table=True):
    """A freelance client."""

    __tablename__ = "clients_client"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    company: str | None = None
    email: str | None = None
    hourly_rate: float = 0.0
    status: str = "active"
    notes: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


class ClientHours(SQLModel, table=True):
    """A block of hours worked for a client."""

    __tablename__ = "clients_hours"

    id: int | None = Field(default=None, primary_key=True)
    client_id: int = Field(index=True)
    hours: float
    description: str | None = None
    entry_date: date = Field(default_factory=date.today)
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _resolve(db, ident: str) -> Client | None:
    """Look up a client by numeric ID or by (case-insensitive) name match.

    Tries exact name first (handles short-name shadows), then substring.
    """
    if ident.isdigit():
        client = db.get(Client, int(ident))
        if client:
            return client
    exact = db.exec(select(Client).where(Client.name.ilike(ident))).first()
    if exact:
        return exact
    return db.exec(
        select(Client).where(Client.name.ilike(f"%{ident}%"))
    ).first()


def _hours(db, client_id: int) -> float:
    """Total hours logged for a client."""
    rows = db.exec(select(ClientHours).where(ClientHours.client_id == client_id)).all()
    return round(sum(r.hours for r in rows), 2)


def _row(db, client: Client) -> dict:
    hours = _hours(db, client.id)
    return {
        "id": client.id,
        "name": client.name,
        "company": client.company,
        "email": client.email,
        "hourly_rate": client.hourly_rate,
        "status": client.status,
        "hours_logged": hours,
        "earnings": round(hours * client.hourly_rate, 2),
        "notes": client.notes,
    }


@app.command()
def add(
    name: str = typer.Argument(..., help="Client name"),
    rate: float = typer.Option(0, "--rate", "-r", help="Hourly rate"),
    company: str = typer.Option(None, "--company", "-c", help="Company"),
    email: str = typer.Option(None, "--email", "-e", help="Email"),
    status: str = typer.Option("active", "--status", "-s", help="prospect/active/past"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🧑‍💼 Add a client."""
    status = status.lower()
    if status not in STATUSES:
        fail(f"Status must be one of: {', '.join(STATUSES)}", json_out=json_out)
    if rate < 0:
        fail("Rate cannot be negative", json_out=json_out)
    client = Client(
        name=name, company=company, email=email,
        hourly_rate=rate, status=status, notes=note,
    )
    with session() as db:
        db.add(client)
        db.flush()
        db.refresh(client)
        data = _row(db, client)
    ok(f"Added {EMOJI} client '{name}'" + (f" — {money(rate)}/h" if rate else ""),
       json_out=json_out, data=data)


@app.command()
def log(
    client: str = typer.Argument(..., help="Client name or ID"),
    hours: float = typer.Argument(..., help="Hours worked"),
    description: str = typer.Option(None, "--desc", "-D", help="What you did"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    json_out: JsonOpt = False,
) -> None:
    """🧑‍💼 Log hours worked for a client."""
    if hours <= 0:
        fail("Hours must be positive", json_out=json_out)
    with session() as db:
        target = _resolve(db, client)
        if not target:
            fail(f"No client matching {client!r}", json_out=json_out)
        db.add(ClientHours(client_id=target.id, hours=hours,
                           description=description, entry_date=parse_date(on)))
        db.flush()
        data = _row(db, target)
    ok(f"Logged {hours:g}h for '{target.name}' — {data['hours_logged']:g}h total "
       f"({money(data['earnings'])})", json_out=json_out, data=data)


@app.command(name="list")
def list_clients(
    status: str = typer.Option(None, "--status", "-s", help="Filter by status"),
    json_out: JsonOpt = False,
) -> None:
    """🧑‍💼 List clients."""
    if status and status.lower() not in STATUSES:
        fail(f"Status must be one of: {', '.join(STATUSES)}", json_out=json_out)
    with session() as db:
        query = select(Client)
        if status:
            query = query.where(Client.status == status.lower())
        clients = list(db.exec(query.order_by(Client.name)).all())
        rows = [_row(db, c) for c in clients]
    render_rows(
        rows,
        [("id", "ID"), ("name", "Name"), ("company", "Company"),
         ("status", "Status"), ("hourly_rate", "Rate"),
         ("hours_logged", "Hours"), ("earnings", "Earnings")],
        json_out=json_out,
        title="🧑‍💼 Clients",
        formatters={
            "hourly_rate": lambda v, r: money(v) if v else "[dim]—[/dim]",
            "earnings": lambda v, r: money(v),
        },
        empty="No clients yet — try: clibo clients add 'Acme Inc' -r 80",
    )


@app.command()
def show(
    client: str = typer.Argument(..., help="Client name or ID"),
    json_out: JsonOpt = False,
) -> None:
    """🧑‍💼 Show a client with their logged hours."""
    with session() as db:
        target = _resolve(db, client)
        if not target:
            fail(f"No client matching {client!r}", json_out=json_out)
        data = _row(db, target)
        hours = [
            {"id": h.id, "entry_date": h.entry_date, "hours": h.hours,
             "description": h.description}
            for h in db.exec(
                select(ClientHours)
                .where(ClientHours.client_id == target.id)
                .order_by(ClientHours.entry_date.desc(), ClientHours.id.desc())
            ).all()
        ]
    if json_out:
        render_record(data | {"hours_log": hours}, json_out=True)
        return
    render_record(data, json_out=False, title=f"🧑‍💼 {target.name}")
    render_rows(
        hours,
        [("id", "ID"), ("entry_date", "Date"), ("hours", "Hours"), ("description", "Work")],
        json_out=False,
        title="Hours log",
        empty="No hours logged yet.",
    )


@app.command()
def edit(
    client: str = typer.Argument(..., help="Client name or ID"),
    rate: float = typer.Option(None, "--rate", "-r", help="New hourly rate"),
    status: str = typer.Option(None, "--status", "-s", help="New status"),
    email: str = typer.Option(None, "--email", "-e"),
    note: str = typer.Option(None, "--note", "-n"),
    json_out: JsonOpt = False,
) -> None:
    """🧑‍💼 Edit a client. Accepts a numeric ID or a name."""
    if status and status.lower() not in STATUSES:
        fail(f"Status must be one of: {', '.join(STATUSES)}", json_out=json_out)
    with session() as db:
        target = _resolve(db, client)
        if not target:
            fail(f"No client matching {client!r}", json_out=json_out)
        if rate is not None:
            target.hourly_rate = rate
        if status is not None:
            target.status = status.lower()
        if email is not None:
            target.email = email
        if note is not None:
            target.notes = note
        db.add(target)
        db.flush()
        data = _row(db, target)
    ok(f"Updated client #{target.id}", json_out=json_out, data=data)


@app.command()
def rm(
    client: str = typer.Argument(..., help="Client name or ID"),
    json_out: JsonOpt = False,
) -> None:
    """🧑‍💼 Delete a client and their hours log."""
    with session() as db:
        target = _resolve(db, client)
        if not target:
            fail(f"No client matching {client!r}", json_out=json_out)
        cid = target.id
        for row in db.exec(select(ClientHours).where(ClientHours.client_id == cid)).all():
            db.delete(row)
        db.delete(target)
    ok(f"Deleted client #{cid}", json_out=json_out, data={"deleted": cid})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Client stats — earnings and activity."""
    with session() as db:
        clients = list(db.exec(select(Client)).all())
        rows = [_row(db, c) for c in clients]
    data = {
        "total_clients": len(clients),
        "active": sum(1 for c in clients if c.status == "active"),
        "total_hours": round(sum(r["hours_logged"] for r in rows), 2),
        "total_earnings": round(sum(r["earnings"] for r in rows), 2),
        "currency": get_currency(),
    }
    render_record(data, json_out=json_out, title="📊 Client stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)
