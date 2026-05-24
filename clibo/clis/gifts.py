"""🎁 gifts — gift ideas & giving tracker."""

from __future__ import annotations

from datetime import datetime

import typer
from sqlmodel import Field, SQLModel, select

from clibo.clis.expense import get_currency, money
from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "gifts"
HELP = "🎁 Gift ideas & giving tracker"
EMOJI = "🎁"
STATUSES = ["idea", "bought", "given"]


class Gift(SQLModel, table=True):
    """A gift idea for someone, tracked from idea to given."""

    __tablename__ = "gifts_gift"

    id: int | None = Field(default=None, primary_key=True)
    recipient: str
    idea: str
    occasion: str | None = None
    price: float = 0.0
    status: str = "idea"
    url: str | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _row(gift: Gift) -> dict:
    return {
        "id": gift.id,
        "recipient": gift.recipient,
        "idea": gift.idea,
        "occasion": gift.occasion,
        "price": gift.price,
        "status": gift.status,
        "url": gift.url,
        "notes": gift.notes,
    }


def _status_cell(status: str) -> str:
    return {
        "idea": "[yellow]💡 idea[/yellow]",
        "bought": "[cyan]🛍️ bought[/cyan]",
        "given": "[green]✓ given[/green]",
    }.get(status, status)


@app.command()
def add(
    recipient: str = typer.Argument(..., help="Who the gift is for"),
    idea: str = typer.Argument(..., help="The gift idea"),
    occasion: str = typer.Option(None, "--occasion", "-o", help="e.g. birthday, holiday"),
    price: float = typer.Option(0, "--price", "-p", help="Estimated price"),
    url: str = typer.Option(None, "--url", "-u", help="Link to the gift"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🎁 Add a gift idea."""
    if price < 0:
        fail("Price cannot be negative", json_out=json_out)
    gift = Gift(recipient=recipient, idea=idea, occasion=occasion,
                price=price, url=url, notes=note)
    with session() as db:
        db.add(gift)
        db.flush()
        db.refresh(gift)
        data = _row(gift)
    ok(f"Added {EMOJI} gift idea for {recipient}: {idea}", json_out=json_out, data=data)


@app.command(name="list")
def list_gifts(
    recipient: str = typer.Option(None, "--recipient", "-r", help="Filter by recipient"),
    status: str = typer.Option(None, "--status", "-s", help="Filter by status"),
    json_out: JsonOpt = False,
) -> None:
    """🎁 List gift ideas."""
    if status and status.lower() not in STATUSES:
        fail(f"Status must be one of: {', '.join(STATUSES)}", json_out=json_out)
    with session() as db:
        query = select(Gift)
        if recipient:
            query = query.where(Gift.recipient.ilike(f"%{recipient}%"))
        if status:
            query = query.where(Gift.status == status.lower())
        gifts = list(db.exec(query.order_by(Gift.recipient, Gift.id)).all())
    render_rows(
        [_row(g) for g in gifts],
        [("id", "ID"), ("recipient", "For"), ("idea", "Idea"),
         ("occasion", "Occasion"), ("price", "Price"), ("status", "Status")],
        json_out=json_out,
        title="🎁 Gift ideas",
        formatters={
            "price": lambda v, r: money(v) if v else "[dim]—[/dim]",
            "status": lambda v, r: _status_cell(v),
        },
        empty="No gift ideas yet — try: clibo gifts add 'Mom' 'cookbook' -o birthday",
    )


def _resolve_gift(db, ident: str) -> Gift | None:
    """Resolve a CLI arg to a Gift row by ID or recipient (most-recent first).

    A person can have multiple gifts; for name lookups we prefer the
    most-recently-added one. Pass the explicit ID to disambiguate.
    """
    from clibo.core.base import lookup_by_id_or_name
    if ident.isdigit():
        gift = db.get(Gift, int(ident))
        if gift:
            return gift
    # Prefer most-recent gift to this recipient.
    return db.exec(
        select(Gift)
        .where(Gift.recipient.ilike(f"%{ident}%"))
        .order_by(Gift.id.desc())
    ).first() or lookup_by_id_or_name(db, Gift, ident, Gift.recipient)


@app.command()
def show(
    gift: str = typer.Argument(..., help="Gift ID or recipient name (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """🎁 Show one gift idea. Accepts a numeric ID or a recipient name."""
    with session() as db:
        target = _resolve_gift(db, gift)
        if not target:
            fail(f"No gift matching {gift!r}", json_out=json_out)
        data = _row(target) | {"created_at": target.created_at}
    render_record(data, json_out=json_out, title=f"🎁 Gift #{target.id}")


def _set_status(ident: str, status: str, json_out: bool) -> None:
    with session() as db:
        gift = _resolve_gift(db, ident)
        if not gift:
            fail(f"No gift matching {ident!r}", json_out=json_out)
        gid = gift.id
        gift.status = status
        db.add(gift)
        db.flush()
        data = _row(gift)
    ok(f"Marked gift #{gid} as {status}", json_out=json_out, data=data)


@app.command()
def bought(
    gift: str = typer.Argument(..., help="Gift ID or recipient name"),
    json_out: JsonOpt = False,
) -> None:
    """🛍️ Mark a gift as bought."""
    _set_status(gift, "bought", json_out)


@app.command()
def given(
    gift: str = typer.Argument(..., help="Gift ID or recipient name"),
    json_out: JsonOpt = False,
) -> None:
    """🎁 Mark a gift as given."""
    _set_status(gift, "given", json_out)


@app.command()
def rm(
    gift: str = typer.Argument(..., help="Gift ID or recipient name"),
    json_out: JsonOpt = False,
) -> None:
    """🎁 Delete a gift idea."""
    with session() as db:
        target = _resolve_gift(db, gift)
        if not target:
            fail(f"No gift matching {gift!r}", json_out=json_out)
        gid = target.id
        db.delete(target)
    ok(f"Deleted gift #{gid}", json_out=json_out, data={"deleted": gid})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Gift stats — counts and spending."""
    with session() as db:
        gifts = list(db.exec(select(Gift)).all())
    by_status = {s: sum(1 for g in gifts if g.status == s) for s in STATUSES}
    spent = round(sum(g.price for g in gifts if g.status in ("bought", "given")), 2)
    data = {
        "total": len(gifts),
        "by_status": by_status,
        "recipients": len({g.recipient for g in gifts}),
        "spent": spent,
        "currency": get_currency(),
    }
    render_record(data, json_out=json_out, title="📊 Gift stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)
