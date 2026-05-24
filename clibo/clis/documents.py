"""📑 documents — important documents with expiry tracking.

Passports, driver's licenses, insurance policies, professional certs, visas,
warranties — everything with an expiry date that, if missed, costs you money
or a trip. Not the same as ``events`` (one-off dates) or ``bills`` (recurring
due dates with amounts).

The killer view is ``documents expiring`` — what's coming up in the next 90
days, sorted by urgency, with a colour-coded warning level.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import humanize_delta, parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "documents"
HELP = "📑 Important documents with expiry tracking"
EMOJI = "📑"

KINDS = [
    "passport", "license", "id", "insurance", "cert", "visa",
    "membership", "warranty", "lease", "other",
]


class Document(SQLModel, table=True):
    """One important document with an expiry date."""

    __tablename__ = "document_entry"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    kind: str = "other"
    expires: date = Field(index=True)
    issued: date | None = None
    number: str | None = None       # serial / policy / passport number
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context) -> None:
    """Default: ``clibo documents`` (bare) runs the ``expiring`` summary."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(expiring, days=90, json_out=False)


def _urgency(days_until: int) -> str:
    """Human-readable urgency bucket for an expiry."""
    if days_until < 0:
        return "expired"
    if days_until <= 30:
        return "critical"
    if days_until <= 90:
        return "soon"
    if days_until <= 365:
        return "watch"
    return "ok"


def _row(doc: Document) -> dict:
    days_until = (doc.expires - date.today()).days
    return {
        "id": doc.id,
        "name": doc.name,
        "kind": doc.kind,
        "expires": doc.expires,
        "days_until": days_until,
        "humanized": humanize_delta(doc.expires),
        "urgency": _urgency(days_until),
        "issued": doc.issued,
        "number": doc.number,
        "note": doc.note,
    }


@app.command()
def add(
    name: str = typer.Argument(..., help="What this document is (e.g. 'Passport')"),
    expires: str = typer.Option(..., "--expires", "-e",
                                 help="When it expires (any date format parse_date accepts)"),
    kind: str = typer.Option("other", "--kind", "-k",
                              help=f"One of: {', '.join(KINDS)}"),
    issued: str = typer.Option(None, "--issued", "-i",
                                help="When it was issued (optional)"),
    number: str = typer.Option(None, "--number", "-#",
                                help="Serial / policy / passport number (optional)"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """📑 Add a document with an expiry date."""
    kind = kind.lower()
    if kind not in KINDS:
        fail(f"Kind must be one of: {', '.join(KINDS)}", json_out=json_out)
    expires_dt = parse_date(expires)
    issued_dt = parse_date(issued) if issued else None
    if issued_dt and issued_dt > expires_dt:
        fail("Issued date is after expires — check the dates", json_out=json_out)
    doc = Document(
        name=name, kind=kind, expires=expires_dt, issued=issued_dt,
        number=number, note=note,
    )
    with session() as db:
        db.add(doc)
        db.flush()
        db.refresh(doc)
        data = _row(doc)
    ok(
        f"Added {EMOJI} {kind}: {name} — expires {expires_dt} ({data['humanized']})",
        json_out=json_out,
        data=data,
    )


@app.command(name="list")
def list_docs(
    kind: str = typer.Option(None, "--kind", "-k", help="Filter by kind"),
    show_expired: bool = typer.Option(False, "--expired",
                                       help="Include expired documents"),
    json_out: JsonOpt = False,
) -> None:
    """📑 List documents, soonest expiry first."""
    if kind and kind.lower() not in KINDS:
        fail(f"Kind must be one of: {', '.join(KINDS)}", json_out=json_out)
    with session() as db:
        query = select(Document)
        if kind:
            query = query.where(Document.kind == kind.lower())
        if not show_expired:
            query = query.where(Document.expires >= date.today())
        docs = list(db.exec(query.order_by(Document.expires)).all())
    render_rows(
        [_row(d) for d in docs],
        [("id", "ID"), ("kind", "Kind"), ("name", "Name"),
         ("expires", "Expires"), ("humanized", "In"), ("urgency", "")],
        json_out=json_out,
        title=f"{EMOJI} Documents",
        empty=("No documents on file yet — try: "
               "clibo documents add 'Passport' -e 2030-06-15 -k passport"),
        formatters={
            "urgency": lambda v, r: {
                "expired": "[red]✗ expired[/red]",
                "critical": "[red]⚠ critical[/red]",
                "soon": "[yellow]· soon[/yellow]",
                "watch": "[dim]watch[/dim]",
                "ok": "[green]ok[/green]",
            }.get(v, v),
        },
    )


@app.command()
def expiring(
    days: int = typer.Option(90, "--days",
                              help="Window: expiries within this many days"),
    json_out: JsonOpt = False,
) -> None:
    """⏳ Documents expiring within N days — the headline view."""
    today = date.today()
    cutoff = today + timedelta(days=days)
    with session() as db:
        docs = list(
            db.exec(
                select(Document)
                .where(Document.expires >= today)
                .where(Document.expires <= cutoff)
                .order_by(Document.expires)
            ).all()
        )
    render_rows(
        [_row(d) for d in docs],
        [("id", "ID"), ("kind", "Kind"), ("name", "Name"),
         ("expires", "Expires"), ("humanized", "In"), ("urgency", "")],
        json_out=json_out,
        title=f"⏳ Expiring in {days}d",
        empty=f"[green]Nothing expiring in the next {days} days.[/green]",
        formatters={
            "urgency": lambda v, r: {
                "critical": "[red]⚠[/red]",
                "soon": "[yellow]·[/yellow]",
                "watch": "[dim]·[/dim]",
                "ok": "[green]·[/green]",
            }.get(v, ""),
        },
    )


@app.command()
def expired(json_out: JsonOpt = False) -> None:
    """❌ Documents that have already expired."""
    today = date.today()
    with session() as db:
        docs = list(
            db.exec(
                select(Document)
                .where(Document.expires < today)
                .order_by(Document.expires.desc())
            ).all()
        )
    render_rows(
        [_row(d) for d in docs],
        [("id", "ID"), ("kind", "Kind"), ("name", "Name"),
         ("expires", "Expired"), ("humanized", "Ago")],
        json_out=json_out,
        title=f"{EMOJI} Expired documents",
        empty="[green]Nothing expired — well kept![/green]",
    )


@app.command()
def show(doc_id: int = typer.Argument(..., help="Document ID"),
         json_out: JsonOpt = False) -> None:
    """📑 Show one document with all its details."""
    with session() as db:
        doc = db.get(Document, doc_id)
        if not doc:
            fail(f"No document #{doc_id}", json_out=json_out)
        data = _row(doc)
    render_record(data, json_out=json_out, title=f"{EMOJI} {doc.name}")


@app.command()
def rm(doc_id: int = typer.Argument(..., help="Document ID"),
       json_out: JsonOpt = False) -> None:
    """📑 Delete a document."""
    with session() as db:
        doc = db.get(Document, doc_id)
        if not doc:
            fail(f"No document #{doc_id}", json_out=json_out)
        db.delete(doc)
    ok(f"Deleted document #{doc_id}",
       json_out=json_out, data={"deleted": doc_id})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Document stats — counts by kind, soonest and farthest expiries."""
    today = date.today()
    with session() as db:
        docs = list(db.exec(select(Document)).all())
    if not docs:
        fail("No documents yet", json_out=json_out)
    by_kind = Counter(d.kind for d in docs)
    by_urgency: Counter[str] = Counter()
    for d in docs:
        by_urgency[_urgency((d.expires - today).days)] += 1
    active = [d for d in docs if d.expires >= today]
    soonest = min(active, key=lambda d: d.expires) if active else None
    farthest = max(active, key=lambda d: d.expires) if active else None
    data = {
        "total": len(docs),
        "active": len(active),
        "expired": len(docs) - len(active),
        "by_kind": dict(by_kind),
        "by_urgency": dict(by_urgency),
        "soonest": {"name": soonest.name, "expires": soonest.expires}
            if soonest else None,
        "farthest": {"name": farthest.name, "expires": farthest.expires}
            if farthest else None,
    }
    render_record(data, json_out=json_out, title=f"{EMOJI} Document stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
