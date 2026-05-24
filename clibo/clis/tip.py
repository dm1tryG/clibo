"""🪙 tip — tipping tracker (separate from expense for tip-behaviour stats).

Logs each tip you leave with the bill amount, tip amount and the resulting
percent so you can see your average generosity, how it varies by venue
type, and whether service ratings correlate with what you leave.

Distinct from `expense`:
- captures the tip *separately* from the bill
- stores `tip_percent` for "what's my average tip %?" queries
- venue/service-rating breakdowns aren't natural on a generic expense row
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.clis.expense import get_currency, money
from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, console, fail, ok, render_record, render_rows

NAME = "tip"
HELP = "🪙 Tipping tracker — bill, tip %, venue and service rating"
EMOJI = "🪙"


class TipEntry(SQLModel, table=True):
    """One tip event — bill, tip amount and the resulting percent."""

    __tablename__ = "tip_entry"

    id: int | None = Field(default=None, primary_key=True)
    bill_amount: float
    tip_amount: float
    tip_percent: float          # 100 * tip_amount / bill_amount, stored for queries
    venue: str | None = None
    service_rating: int | None = None  # 1-5, optional
    entry_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    note: str | None = None


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context, json_out: JsonOpt = False) -> None:
    """Default: ``clibo tip`` (bare) shows today's tips."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(today, json_out=json_out)


def _row(entry: TipEntry) -> dict:
    return {
        "id": entry.id,
        "entry_date": entry.entry_date,
        "bill_amount": entry.bill_amount,
        "tip_amount": entry.tip_amount,
        "tip_percent": entry.tip_percent,
        "venue": entry.venue,
        "service_rating": entry.service_rating,
        "note": entry.note,
    }


def _resolve_tip(
    bill: float, percent: float | None, amount: float | None
) -> tuple[float, float]:
    """Given exactly one of percent/amount, return (tip_amount, tip_percent)."""
    if (percent is None) == (amount is None):
        raise typer.BadParameter(
            "Provide exactly one of --percent / -p or --amount / -a"
        )
    if percent is not None:
        if percent < 0:
            raise typer.BadParameter("Tip percent cannot be negative")
        return round(bill * percent / 100, 2), round(percent, 2)
    if amount < 0:
        raise typer.BadParameter("Tip amount cannot be negative")
    pct = round(100 * amount / bill, 2) if bill > 0 else 0.0
    return round(amount, 2), pct


@app.command()
def log(
    bill: float = typer.Argument(..., help="The pre-tip bill amount"),
    percent: float = typer.Option(None, "--percent", "-p",
                                   help="Tip as a percent of the bill"),
    amount: float = typer.Option(None, "--amount", "-a",
                                  help="Tip as an absolute amount"),
    venue: str = typer.Option(None, "--venue", "-v",
                               help="Where (e.g. 'Joe's Diner')"),
    rating: int = typer.Option(None, "--rating", "-r",
                                help="Service rating 1-5"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🪙 Log a tip event (bill + percent or absolute amount)."""
    if bill <= 0:
        fail("Bill amount must be positive", json_out=json_out)
    if rating is not None and rating not in range(1, 6):
        fail("Rating must be 1-5", json_out=json_out)
    tip_amount, tip_percent = _resolve_tip(bill, percent, amount)
    entry = TipEntry(
        bill_amount=round(bill, 2),
        tip_amount=tip_amount,
        tip_percent=tip_percent,
        venue=venue,
        service_rating=rating,
        entry_date=parse_date(on),
        note=note,
    )
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        data = _row(entry)
    where = f" @ {venue}" if venue else ""
    ok(
        f"Logged {EMOJI} {money(tip_amount)} tip on {money(bill)} "
        f"({tip_percent:g}%){where}",
        json_out=json_out,
        data=data,
    )


# `add` is a friendlier alias for `log` (predictable verbs across tools).
app.command(name="add", help="Alias for `log`")(log)


@app.command()
def calc(
    bill: float = typer.Argument(..., help="The pre-tip bill amount"),
    percent: float = typer.Option(None, "--percent", "-p",
                                   help="Compute the tip amount for this percent"),
    amount: float = typer.Option(None, "--amount", "-a",
                                  help="Compute the percent for this tip amount"),
    json_out: JsonOpt = False,
) -> None:
    """🧮 Compute a tip without saving — quick calculator."""
    if bill <= 0:
        fail("Bill amount must be positive", json_out=json_out)
    try:
        tip_amount, tip_percent = _resolve_tip(bill, percent, amount)
    except typer.BadParameter as exc:
        fail(str(exc), json_out=json_out)
    total = round(bill + tip_amount, 2)
    data = {
        "bill": round(bill, 2),
        "tip_amount": tip_amount,
        "tip_percent": tip_percent,
        "total": total,
        "currency": get_currency(),
    }
    if json_out:
        render_record(data, json_out=True)
        return
    console.print(
        f"\n🧮  {money(bill)}  +  [bold cyan]{money(tip_amount)}[/bold cyan]  "
        f"({tip_percent:g}%)  =  [bold]{money(total)}[/bold]\n"
    )


@app.command()
def today(json_out: JsonOpt = False) -> None:
    """🪙 Today's tips."""
    day = date.today()
    with session() as db:
        entries = list(
            db.exec(select(TipEntry).where(TipEntry.entry_date == day)).all()
        )
    total_tipped = round(sum(e.tip_amount for e in entries), 2)
    total_billed = round(sum(e.bill_amount for e in entries), 2)
    avg_pct = (round(100 * total_tipped / total_billed, 2)
               if total_billed > 0 else 0.0)
    if json_out:
        render_record(
            {
                "date": day,
                "count": len(entries),
                "total_billed": total_billed,
                "total_tipped": total_tipped,
                "avg_percent": avg_pct,
                "entries": [_row(e) for e in entries],
            },
            json_out=True,
        )
        return
    if not entries:
        console.print(f"\n{EMOJI} [dim]No tips logged today.[/dim]\n")
        return
    console.print(f"\n{EMOJI} [bold]Tips today[/bold] · {day:%a %d %b}\n")
    for entry in entries:
        venue = f" @ {entry.venue}" if entry.venue else ""
        rating = f" · ★{entry.service_rating}" if entry.service_rating else ""
        console.print(
            f"  • {money(entry.tip_amount)} on {money(entry.bill_amount)} "
            f"({entry.tip_percent:g}%){venue}{rating}"
        )
    console.print(
        f"\n  [bold]{money(total_tipped)}[/bold] tipped on "
        f"{money(total_billed)}  ·  avg {avg_pct:g}%\n"
    )


@app.command(name="list")
def list_entries(
    days: int = typer.Option(30, "--days", help="Look back this many days"),
    venue: str = typer.Option(None, "--venue", "-v", help="Filter by venue"),
    json_out: JsonOpt = False,
) -> None:
    """🪙 Recent tips."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        query = select(TipEntry).where(TipEntry.entry_date >= since)
        if venue:
            query = query.where(TipEntry.venue == venue)
        entries = list(
            db.exec(query.order_by(TipEntry.entry_date.desc(),
                                   TipEntry.id.desc())).all()
        )
    render_rows(
        [_row(e) for e in entries],
        [("id", "ID"), ("entry_date", "Date"), ("bill_amount", "Bill"),
         ("tip_amount", "Tip"), ("tip_percent", "%"),
         ("venue", "Venue"), ("service_rating", "★")],
        json_out=json_out,
        title=f"{EMOJI} Tips — last {days}d",
        empty="No tips yet — try: clibo tip log 40 -p 20 -v dinner",
        formatters={
            "bill_amount": lambda v, r: money(v),
            "tip_amount": lambda v, r: money(v),
            "tip_percent": lambda v, r: f"{v:g}%",
        },
    )


@app.command()
def show(entry_id: int = typer.Argument(..., help="Tip entry ID"),
         json_out: JsonOpt = False) -> None:
    """🪙 Show one tip entry."""
    with session() as db:
        entry = db.get(TipEntry, entry_id)
        if not entry:
            fail(f"No tip entry #{entry_id}", json_out=json_out)
        data = _row(entry)
    render_record(data, json_out=json_out, title=f"{EMOJI} Tip #{entry_id}")


@app.command()
def rm(entry_id: int = typer.Argument(..., help="Tip entry ID"),
       json_out: JsonOpt = False) -> None:
    """🪙 Delete a tip entry."""
    with session() as db:
        entry = db.get(TipEntry, entry_id)
        if not entry:
            fail(f"No tip entry #{entry_id}", json_out=json_out)
        db.delete(entry)
    ok(f"Deleted tip entry #{entry_id}",
       json_out=json_out, data={"deleted": entry_id})


@app.command()
def stats(
    days: int = typer.Option(90, "--days", help="Window size in days"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Tipping stats — generosity, by venue, by service rating."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        entries = list(
            db.exec(select(TipEntry).where(TipEntry.entry_date >= since)).all()
        )
    if not entries:
        fail("No tips in this window", json_out=json_out)
    total_billed = round(sum(e.bill_amount for e in entries), 2)
    total_tipped = round(sum(e.tip_amount for e in entries), 2)
    avg_pct = round(sum(e.tip_percent for e in entries) / len(entries), 2)
    # weighted by bill amount (the "true" percentage you tip)
    weighted_pct = (round(100 * total_tipped / total_billed, 2)
                    if total_billed > 0 else 0.0)
    biggest = max(entries, key=lambda e: e.tip_amount)
    most_generous_pct = max(entries, key=lambda e: e.tip_percent)
    venues = Counter(e.venue for e in entries if e.venue)
    by_venue_pct: dict[str, float] = {}
    by_venue_count: dict[str, int] = dict(venues)
    for v in venues:
        venue_entries = [e for e in entries if e.venue == v]
        by_venue_pct[v] = round(
            sum(e.tip_percent for e in venue_entries) / len(venue_entries), 2
        )
    by_rating_pct: dict[int, float] = {}
    for r in range(1, 6):
        rating_entries = [e for e in entries if e.service_rating == r]
        if rating_entries:
            by_rating_pct[r] = round(
                sum(e.tip_percent for e in rating_entries) / len(rating_entries), 2
            )
    data = {
        "window_days": days,
        "count": len(entries),
        "total_billed": total_billed,
        "total_tipped": total_tipped,
        "avg_tip_percent": avg_pct,
        "weighted_tip_percent": weighted_pct,
        "biggest_tip": {
            "amount": biggest.tip_amount,
            "bill": biggest.bill_amount,
            "venue": biggest.venue,
        },
        "most_generous_percent": {
            "percent": most_generous_pct.tip_percent,
            "amount": most_generous_pct.tip_amount,
            "venue": most_generous_pct.venue,
        },
        "by_venue_count": by_venue_count,
        "by_venue_avg_percent": by_venue_pct,
        "by_service_rating_avg_percent": by_rating_pct,
        "currency": get_currency(),
    }
    render_record(data, json_out=json_out, title=f"📊 Tip stats · last {days}d")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
