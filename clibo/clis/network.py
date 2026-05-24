"""🌐 network — networking & people-you-met log."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlalchemy import or_
from sqlmodel import Field, SQLModel, select

from clibo.core.base import humanize_delta, parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "network"
HELP = "🌐 Networking & people-you-met log"
EMOJI = "🌐"


class Connection(SQLModel, table=True):
    """A person you met — where, when and in what context."""

    __tablename__ = "network_connection"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    company: str | None = None
    met_where: str | None = None
    context: str | None = None
    met_date: date = Field(default_factory=date.today, index=True)
    notes: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _row(conn: Connection) -> dict:
    return {
        "id": conn.id,
        "name": conn.name,
        "company": conn.company,
        "met_where": conn.met_where,
        "context": conn.context,
        "met_date": conn.met_date,
        "met_ago": humanize_delta(conn.met_date),
        "notes": conn.notes,
    }


@app.command()
def add(
    name: str = typer.Argument(..., help="Person's name"),
    where: str = typer.Option(None, "--where", "-w", help="Where you met"),
    context: str = typer.Option(None, "--context", "-c", help="How/why you met"),
    company: str = typer.Option(None, "--company", help="Their company"),
    on: str = typer.Option("today", "--date", "-d", help="Date you met"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🌐 Log someone you met."""
    conn = Connection(
        name=name, company=company, met_where=where, context=context,
        met_date=parse_date(on), notes=note,
    )
    with session() as db:
        db.add(conn)
        db.flush()
        db.refresh(conn)
        data = _row(conn)
    where_txt = f" at {where}" if where else ""
    ok(f"Logged {EMOJI} {name}{where_txt}", json_out=json_out, data=data)


@app.command(name="list")
def list_connections(
    days: int = typer.Option(90, "--days", help="Look back this many days"),
    json_out: JsonOpt = False,
) -> None:
    """🌐 List people you've met."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        connections = list(
            db.exec(
                select(Connection)
                .where(Connection.met_date >= since)
                .order_by(Connection.met_date.desc(), Connection.id.desc())
            ).all()
        )
    render_rows(
        [_row(c) for c in connections],
        [("id", "ID"), ("name", "Name"), ("company", "Company"),
         ("met_where", "Met At"), ("met_date", "Date"), ("met_ago", "When")],
        json_out=json_out,
        title="🌐 Network",
        empty="No connections yet — try: clibo network add 'Sam' -w 'PyCon'",
    )


@app.command()
def show(
    connection: str = typer.Argument(..., help="Connection ID or name (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """🌐 Show one connection in detail. Accepts a numeric ID or a name."""
    from clibo.core.base import lookup_by_id_or_name
    with session() as db:
        conn = lookup_by_id_or_name(db, Connection, connection, Connection.name)
        if not conn:
            fail(f"No connection matching {connection!r}", json_out=json_out)
        data = _row(conn) | {"created_at": conn.created_at}
    render_record(data, json_out=json_out, title=f"🌐 {data['name']}")


@app.command()
def edit(
    connection: str = typer.Argument(..., help="Connection ID or name (fuzzy)"),
    name: str = typer.Option(None, "--name", help="New name"),
    company: str = typer.Option(None, "--company", "-c", help="New company"),
    met_where: str = typer.Option(None, "--where", "-w",
                                    help="Where you met"),
    context: str = typer.Option(None, "--context", "-x",
                                  help="New context note"),
    json_out: JsonOpt = False,
) -> None:
    """🌐 Edit a connection. Accepts a numeric ID or a name."""
    from clibo.core.base import lookup_by_id_or_name
    with session() as db:
        conn = lookup_by_id_or_name(db, Connection, connection, Connection.name)
        if not conn:
            fail(f"No connection matching {connection!r}", json_out=json_out)
        if name is not None:
            conn.name = name
        if company is not None:
            conn.company = company
        if met_where is not None:
            conn.met_where = met_where
        if context is not None:
            conn.context = context
        db.add(conn)
        db.flush()
        data = _row(conn)
    ok(f"Updated connection #{conn.id}", json_out=json_out, data=data)


@app.command()
def search(
    query: str = typer.Argument(..., help="Text to search for"),
    json_out: JsonOpt = False,
) -> None:
    """🔍 Search connections by name, company, place or context."""
    pattern = f"%{query}%"
    with session() as db:
        connections = list(
            db.exec(
                select(Connection).where(
                    or_(
                        Connection.name.ilike(pattern),
                        Connection.company.ilike(pattern),
                        Connection.met_where.ilike(pattern),
                        Connection.context.ilike(pattern),
                    )
                ).order_by(Connection.met_date.desc())
            ).all()
        )
    render_rows(
        [_row(c) for c in connections],
        [("id", "ID"), ("name", "Name"), ("company", "Company"),
         ("met_where", "Met At"), ("met_date", "Date")],
        json_out=json_out,
        title=f"🔍 Network matching '{query}'",
        empty=f"No connections match '{query}'.",
    )


@app.command()
def rm(
    connection: str = typer.Argument(..., help="Connection ID or name (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """🌐 Delete a connection."""
    from clibo.core.base import lookup_by_id_or_name
    with session() as db:
        conn = lookup_by_id_or_name(db, Connection, connection, Connection.name)
        if not conn:
            fail(f"No connection matching {connection!r}", json_out=json_out)
        cid = conn.id
        db.delete(conn)
    ok(f"Deleted connection #{cid}", json_out=json_out, data={"deleted": cid})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Networking stats."""
    since = date.today() - timedelta(days=30)
    with session() as db:
        connections = list(db.exec(select(Connection)).all())
    by_place: dict[str, int] = {}
    for conn in connections:
        if conn.met_where:
            by_place[conn.met_where] = by_place.get(conn.met_where, 0) + 1
    top = sorted(by_place.items(), key=lambda kv: kv[1], reverse=True)[:3]
    data = {
        "total": len(connections),
        "met_last_30d": sum(1 for c in connections if c.met_date >= since),
        "top_places": [{"place": p, "count": n} for p, n in top],
    }
    render_record(data, json_out=json_out, title="📊 Network stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)
