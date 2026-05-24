"""🔁 subs — recurring subscriptions tracker."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.clis.expense import get_currency, money
from clibo.core.base import humanize_delta, parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, console, fail, ok, render_record, render_rows

NAME = "subs"
HELP = "🔁 Recurring subscriptions tracker"
EMOJI = "🔁"

#: billing cycle -> multiplier that converts one charge into a monthly cost
CYCLES: dict[str, float] = {"weekly": 52 / 12, "monthly": 1.0, "yearly": 1 / 12}


class Subscription(SQLModel, table=True):
    """A recurring paid subscription."""

    __tablename__ = "subs_subscription"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    amount: float
    cycle: str = "monthly"
    category: str = "other"
    next_billing: date | None = None
    active: bool = True
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context) -> None:
    """Default: ``clibo subs`` (bare) runs the ``total`` summary."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(total, json_out=False)


def _monthly(sub: Subscription) -> float:
    """Normalised monthly cost of a subscription."""
    return round(sub.amount * CYCLES.get(sub.cycle, 1.0), 2)


def _resolve(db, ident: str) -> Subscription | None:
    """Resolve a CLI arg to a Subscription by ID or name (fuzzy)."""
    from clibo.core.base import lookup_by_id_or_name
    return lookup_by_id_or_name(db, Subscription, ident, Subscription.name)


def _row(sub: Subscription) -> dict:
    return {
        "id": sub.id,
        "name": sub.name,
        "amount": sub.amount,
        "cycle": sub.cycle,
        "category": sub.category,
        "monthly_cost": _monthly(sub),
        "next_billing": sub.next_billing,
        "active": sub.active,
        "note": sub.note,
    }


@app.command()
def add(
    name: str = typer.Argument(..., help="Subscription name, e.g. Netflix"),
    amount: float = typer.Option(..., "--amount", "-a", help="Charge per cycle"),
    cycle: str = typer.Option("monthly", "--cycle", "-c", help="weekly / monthly / yearly"),
    category: str = typer.Option("other", "--category", help="Category, e.g. streaming"),
    next_billing: str = typer.Option(None, "--next", help="Next billing date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🔁 Add a recurring subscription."""
    cycle = cycle.lower()
    if cycle not in CYCLES:
        fail(f"Cycle must be one of: {', '.join(CYCLES)}", json_out=json_out)
    if amount <= 0:
        fail("Amount must be positive", json_out=json_out)
    sub = Subscription(
        name=name, amount=amount, cycle=cycle, category=category.lower(),
        next_billing=parse_date(next_billing) if next_billing else None, note=note,
    )
    with session() as db:
        db.add(sub)
        db.flush()
        db.refresh(sub)
        data = _row(sub)
    ok(f"Added {EMOJI} {name} — {money(amount)}/{cycle} (~{money(_monthly(sub))}/mo)",
       json_out=json_out, data=data)


@app.command(name="list")
def list_subs(
    show_all: bool = typer.Option(False, "--all", help="Include cancelled subscriptions"),
    json_out: JsonOpt = False,
) -> None:
    """🔁 List your subscriptions."""
    with session() as db:
        query = select(Subscription)
        if not show_all:
            query = query.where(Subscription.active == True)  # noqa: E712
        subs = list(db.exec(query.order_by(Subscription.name)).all())
    render_rows(
        [_row(s) for s in subs],
        [("id", "ID"), ("name", "Name"), ("amount", "Charge"), ("cycle", "Cycle"),
         ("monthly_cost", "Per Month"), ("category", "Category"), ("next_billing", "Next")],
        json_out=json_out,
        title="🔁 Subscriptions",
        formatters={
            "amount": lambda v, r: money(v),
            "monthly_cost": lambda v, r: money(v),
        },
        empty="No subscriptions yet — try: clibo subs add Netflix -a 12.99",
    )


@app.command()
def total(json_out: JsonOpt = False) -> None:
    """💰 Total cost of all active subscriptions."""
    with session() as db:
        subs = list(
            db.exec(select(Subscription).where(Subscription.active == True)).all()  # noqa: E712
        )
    monthly = round(sum(_monthly(s) for s in subs), 2)
    data = {
        "active_subscriptions": len(subs),
        "monthly_cost": monthly,
        "yearly_cost": round(monthly * 12, 2),
        "currency": get_currency(),
    }
    if json_out:
        render_record(data, json_out=True)
        return
    console.print(f"\n🔁 [bold]{len(subs)}[/bold] active subscriptions\n")
    console.print(f"  💰 [bold cyan]{money(monthly)}[/bold cyan] / month")
    console.print(f"  📅 [bold]{money(data['yearly_cost'])}[/bold] / year\n")


@app.command()
def upcoming(
    days: int = typer.Option(14, "--days", help="Look ahead this many days"),
    json_out: JsonOpt = False,
) -> None:
    """🔔 Subscriptions billing soon."""
    horizon = date.today() + timedelta(days=days)
    with session() as db:
        subs = list(
            db.exec(
                select(Subscription)
                .where(Subscription.active == True)  # noqa: E712
                .where(Subscription.next_billing != None)  # noqa: E711
                .where(Subscription.next_billing <= horizon)
                .order_by(Subscription.next_billing)
            ).all()
        )
    rows = [_row(s) | {"bills_in": humanize_delta(s.next_billing)} for s in subs]
    render_rows(
        rows,
        [("name", "Name"), ("amount", "Charge"), ("next_billing", "Next Billing"),
         ("bills_in", "When")],
        json_out=json_out,
        title=f"🔔 Billing in the next {days} days",
        formatters={"amount": lambda v, r: money(v)},
        empty="Nothing billing soon (set --next dates when adding subs).",
    )


@app.command()
def show(
    sub: str = typer.Argument(..., help="Subscription ID or name (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """🔁 Show one subscription. Accepts a numeric ID or a name."""
    with session() as db:
        target = _resolve(db, sub)
        if not target:
            fail(f"No subscription matching {sub!r}", json_out=json_out)
        data = _row(target) | {"created_at": target.created_at}
    render_record(data, json_out=json_out, title=f"🔁 {target.name}")


@app.command()
def edit(
    sub: str = typer.Argument(..., help="Subscription ID or name (fuzzy)"),
    name: str = typer.Option(None, "--name", help="New name"),
    amount: float = typer.Option(None, "--amount", "-a", help="New charge"),
    cycle: str = typer.Option(None, "--cycle", "-c",
                              help="weekly / monthly / yearly"),
    category: str = typer.Option(None, "--category", help="New category"),
    next_billing: str = typer.Option(None, "--next", help="Next billing date"),
    note: str = typer.Option(None, "--note", "-n"),
    json_out: JsonOpt = False,
) -> None:
    """🔁 Edit a subscription. Accepts a numeric ID or a name."""
    with session() as db:
        target = _resolve(db, sub)
        if not target:
            fail(f"No subscription matching {sub!r}", json_out=json_out)
        if name is not None:
            target.name = name
        if amount is not None:
            if amount <= 0:
                fail("Amount must be positive", json_out=json_out)
            target.amount = amount
        if cycle is not None:
            if cycle.lower() not in CYCLES:
                fail(f"Cycle must be one of: {', '.join(CYCLES)}",
                     json_out=json_out)
            target.cycle = cycle.lower()
        if category is not None:
            target.category = category.lower()
        if next_billing is not None:
            target.next_billing = parse_date(next_billing)
        if note is not None:
            target.note = note
        db.add(target)
        db.flush()
        data = _row(target)
    ok(f"Updated subscription #{target.id} — {target.name}",
       json_out=json_out, data=data)


@app.command()
def cancel(
    sub: str = typer.Argument(..., help="Subscription ID or name (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """🔁 Mark a subscription as cancelled (keeps it in history)."""
    with session() as db:
        target = _resolve(db, sub)
        if not target:
            fail(f"No subscription matching {sub!r}", json_out=json_out)
        target.active = False
        db.add(target)
    ok(f"Cancelled {EMOJI} {target.name}", json_out=json_out,
       data={"id": target.id, "active": False})


@app.command()
def rm(
    sub: str = typer.Argument(..., help="Subscription ID or name (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """🔁 Delete a subscription."""
    with session() as db:
        target = _resolve(db, sub)
        if not target:
            fail(f"No subscription matching {sub!r}", json_out=json_out)
        sid = target.id
        db.delete(target)
    ok(f"Deleted subscription #{sid}", json_out=json_out, data={"deleted": sid})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Subscription stats by category."""
    with session() as db:
        subs = list(
            db.exec(select(Subscription).where(Subscription.active == True)).all()  # noqa: E712
        )
    by_cat: dict[str, float] = {}
    for sub in subs:
        by_cat[sub.category] = round(by_cat.get(sub.category, 0) + _monthly(sub), 2)
    top = sorted(by_cat.items(), key=lambda kv: kv[1], reverse=True)
    data = {
        "active_subscriptions": len(subs),
        "monthly_cost": round(sum(_monthly(s) for s in subs), 2),
        "by_category": [{"category": c, "monthly_cost": a} for c, a in top],
        "currency": get_currency(),
    }
    render_record(data, json_out=json_out, title="📊 Subscription stats")
