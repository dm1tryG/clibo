"""❤️ donations — charitable giving log with tax-year and recipient stats.

Could in theory live under `expense` with category=donation, but giving has
its own shape that doesn't fit a generic expense row:

- **Calendar-year totals** matter for tax filing — separate from
  fiscal-year expense reporting and aggregated independently.
- **Tax-deductible vs not** — political contributions, GoFundMe gifts to
  individuals, and many international NGOs aren't deductible. The flag is
  important come tax time and the default is *deductible*.
- **Recipient as structured data** — repeat giving to the same org should
  cluster cleanly; you want "Red Cross: $250 across 5 gifts in 2026", not
  five expense rows with slightly-different descriptions.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.clis.expense import get_currency, money
from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "donations"
HELP = "❤️ Charitable giving log (tax-year aware)"
EMOJI = "❤️"


class Donation(SQLModel, table=True):
    """One donation event."""

    __tablename__ = "donation_entry"

    id: int | None = Field(default=None, primary_key=True)
    recipient: str
    amount: float
    tax_deductible: bool = True
    receipt: str | None = None     # receipt or transaction reference
    entry_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    note: str | None = None


app = typer.Typer(no_args_is_help=True, help=HELP)


def _resolve(db, ident: str) -> Donation | None:
    """Resolve a CLI arg to a Donation by ID or recipient (most-recent first).

    Repeat giving to the same org means a name lookup is many-to-one;
    we prefer the most-recently-added entry. Pass the ID to be precise.
    """
    from clibo.core.base import lookup_by_id_or_name
    if ident.isdigit():
        entry = db.get(Donation, int(ident))
        if entry:
            return entry
    return db.exec(
        select(Donation)
        .where(Donation.recipient.ilike(f"%{ident}%"))
        .order_by(Donation.id.desc())
    ).first() or lookup_by_id_or_name(db, Donation, ident, Donation.recipient)


def _row(entry: Donation) -> dict:
    return {
        "id": entry.id,
        "entry_date": entry.entry_date,
        "recipient": entry.recipient,
        "amount": entry.amount,
        "tax_deductible": entry.tax_deductible,
        "receipt": entry.receipt,
        "note": entry.note,
    }


@app.command()
def log(
    recipient: str = typer.Argument(..., help="Receiving org (e.g. 'Red Cross')"),
    amount: float = typer.Option(..., "--amount", "-a", help="Donation amount"),
    not_deductible: bool = typer.Option(
        False, "--no-deductible",
        help="Mark as NOT tax-deductible (the default is deductible)",
    ),
    receipt: str = typer.Option(None, "--receipt", "-r",
                                 help="Receipt / transaction number"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """❤️ Log a charitable donation."""
    if amount <= 0:
        fail("Amount must be positive", json_out=json_out)
    entry = Donation(
        recipient=recipient.strip(),
        amount=round(amount, 2),
        tax_deductible=not not_deductible,
        receipt=receipt,
        entry_date=parse_date(on),
        note=note,
    )
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        data = _row(entry)
    flag = "" if entry.tax_deductible else " [not tax-deductible]"
    ok(f"Logged {EMOJI} {money(entry.amount)} to {entry.recipient}{flag}",
       json_out=json_out, data=data)


# `add` is a friendlier alias for `log` (predictable verbs across tools).
app.command(name="add", help="Alias for `log`")(log)


@app.command(name="list")
def list_entries(
    year: int = typer.Option(None, "--year", "-y", help="Filter by calendar year"),
    recipient: str = typer.Option(None, "--recipient", "-R",
                                   help="Filter by recipient (exact match)"),
    json_out: JsonOpt = False,
) -> None:
    """❤️ Recent donations (newest first)."""
    with session() as db:
        query = select(Donation)
        if year:
            start = date(year, 1, 1)
            end = date(year, 12, 31)
            query = query.where(Donation.entry_date >= start)
            query = query.where(Donation.entry_date <= end)
        if recipient:
            query = query.where(Donation.recipient == recipient)
        entries = list(
            db.exec(query.order_by(Donation.entry_date.desc(),
                                   Donation.id.desc())).all()
        )
    render_rows(
        [_row(e) for e in entries],
        [("id", "ID"), ("entry_date", "Date"), ("recipient", "Recipient"),
         ("amount", "Amount"), ("tax_deductible", "Tax?"),
         ("receipt", "Receipt"), ("note", "Note")],
        json_out=json_out,
        title=f"{EMOJI} Donations",
        empty="No donations yet — try: clibo donations log 'Red Cross' -a 50",
        formatters={
            "amount": lambda v, r: money(v),
            "tax_deductible": lambda v, r: "[green]✓[/green]" if v else "[dim]·[/dim]",
        },
    )


@app.command()
def year(
    yr: int = typer.Option(None, "--year", "-y",
                            help="Calendar year (default: current)"),
    json_out: JsonOpt = False,
) -> None:
    """🗓️ Annual giving summary — total, deductible total, by recipient."""
    target_year = yr or date.today().year
    start = date(target_year, 1, 1)
    end = date(target_year, 12, 31)
    with session() as db:
        entries = list(
            db.exec(
                select(Donation)
                .where(Donation.entry_date >= start)
                .where(Donation.entry_date <= end)
            ).all()
        )
    total = round(sum(e.amount for e in entries), 2)
    deductible_total = round(
        sum(e.amount for e in entries if e.tax_deductible), 2
    )
    by_recipient: dict[str, float] = {}
    for entry in entries:
        by_recipient[entry.recipient] = round(
            by_recipient.get(entry.recipient, 0) + entry.amount, 2
        )
    by_recipient_sorted = sorted(by_recipient.items(), key=lambda kv: -kv[1])
    data = {
        "year": target_year,
        "count": len(entries),
        "total": total,
        "deductible_total": deductible_total,
        "non_deductible_total": round(total - deductible_total, 2),
        "recipients": len(by_recipient),
        "by_recipient": [
            {"recipient": r, "amount": a} for r, a in by_recipient_sorted
        ],
        "currency": get_currency(),
    }
    render_record(data, json_out=json_out,
                  title=f"🗓️ Donations · {target_year}")


@app.command()
def top(
    days: int = typer.Option(365, "--days",
                              help="Look back this many days (default: a year)"),
    limit: int = typer.Option(10, "--limit", "-n", help="How many to show"),
    json_out: JsonOpt = False,
) -> None:
    """🏆 Top recipients by total amount in the window."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        entries = list(
            db.exec(
                select(Donation).where(Donation.entry_date >= since)
            ).all()
        )
    if not entries:
        fail("No donations in this window", json_out=json_out)
    counts: Counter[str] = Counter()
    totals: dict[str, float] = {}
    for entry in entries:
        counts[entry.recipient] += 1
        totals[entry.recipient] = round(
            totals.get(entry.recipient, 0) + entry.amount, 2
        )
    top_list = sorted(totals.items(), key=lambda kv: -kv[1])[:limit]
    rows = [
        {"recipient": r, "total": t, "gifts": counts[r]}
        for r, t in top_list
    ]
    render_rows(
        rows,
        [("recipient", "Recipient"), ("total", "Total"), ("gifts", "Gifts")],
        json_out=json_out,
        title=f"🏆 Top recipients · last {days}d",
        formatters={"total": lambda v, r: money(v)},
    )


@app.command()
def show(
    entry: str = typer.Argument(..., help="Donation ID or recipient name (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """❤️ Show one donation. Accepts a numeric ID or a recipient name."""
    with session() as db:
        target = _resolve(db, entry)
        if not target:
            fail(f"No donation matching {entry!r}", json_out=json_out)
        data = _row(target)
    render_record(data, json_out=json_out,
                  title=f"{EMOJI} Donation #{target.id}")


@app.command()
def edit(
    entry: str = typer.Argument(..., help="Donation ID or recipient name (fuzzy)"),
    amount: float = typer.Option(None, "--amount", "-a", help="New amount"),
    recipient: str = typer.Option(None, "--recipient", "-R", help="New recipient"),
    receipt: str = typer.Option(None, "--receipt", "-r", help="Receipt / tx ref"),
    not_deductible: bool = typer.Option(
        False, "--no-deductible", help="Flip to NOT tax-deductible"
    ),
    deductible: bool = typer.Option(
        False, "--deductible", help="Flip back to tax-deductible"
    ),
    note: str = typer.Option(None, "--note", "-n"),
    json_out: JsonOpt = False,
) -> None:
    """❤️ Edit a donation. Accepts a numeric ID or a recipient name."""
    with session() as db:
        target = _resolve(db, entry)
        if not target:
            fail(f"No donation matching {entry!r}", json_out=json_out)
        if amount is not None:
            if amount <= 0:
                fail("Amount must be positive", json_out=json_out)
            target.amount = round(amount, 2)
        if recipient is not None:
            target.recipient = recipient.strip()
        if receipt is not None:
            target.receipt = receipt
        if note is not None:
            target.note = note
        if not_deductible:
            target.tax_deductible = False
        if deductible:
            target.tax_deductible = True
        db.add(target)
        db.flush()
        data = _row(target)
    ok(f"Updated donation #{target.id}", json_out=json_out, data=data)


@app.command()
def rm(
    entry: str = typer.Argument(..., help="Donation ID or recipient name (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """❤️ Delete a donation. Accepts a numeric ID or a recipient name."""
    with session() as db:
        target = _resolve(db, entry)
        if not target:
            fail(f"No donation matching {entry!r}", json_out=json_out)
        did = target.id
        db.delete(target)
    ok(f"Deleted donation #{did}",
       json_out=json_out, data={"deleted": did})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Lifetime stats — total given, by year, top recipient."""
    with session() as db:
        entries = list(db.exec(select(Donation)).all())
    if not entries:
        fail("No donations yet", json_out=json_out)
    total = round(sum(e.amount for e in entries), 2)
    deductible_total = round(
        sum(e.amount for e in entries if e.tax_deductible), 2
    )
    by_year: dict[int, float] = {}
    by_recipient: dict[str, float] = {}
    for entry in entries:
        yr = entry.entry_date.year
        by_year[yr] = round(by_year.get(yr, 0) + entry.amount, 2)
        by_recipient[entry.recipient] = round(
            by_recipient.get(entry.recipient, 0) + entry.amount, 2
        )
    top_recipient, top_amount = max(by_recipient.items(), key=lambda kv: kv[1])
    data = {
        "lifetime_count": len(entries),
        "lifetime_total": total,
        "lifetime_deductible_total": deductible_total,
        "recipients": len(by_recipient),
        "top_recipient": {"recipient": top_recipient, "total": top_amount},
        "by_year": {str(y): a for y, a in sorted(by_year.items())},
        "currency": get_currency(),
    }
    render_record(data, json_out=json_out, title="📊 Donations · lifetime")
