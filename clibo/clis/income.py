"""💵 income — counterpart to expense: track money coming in."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.clis.expense import get_currency, money
from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, bar, console, fail, ok, render_record, render_rows

NAME = "income"
HELP = "💵 Income tracker — counterpart to expense"
EMOJI = "💵"


class IncomeEntry(SQLModel, table=True):
    """One incoming-money event."""

    __tablename__ = "income_entry"

    id: int | None = Field(default=None, primary_key=True)
    amount: float
    source: str
    category: str = "other"
    entry_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    note: str | None = None


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context) -> None:
    """Default: ``clibo income`` (bare) runs the ``month`` summary."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(month, month_spec=None, json_out=False)


def _row(entry: IncomeEntry) -> dict:
    return {
        "id": entry.id,
        "entry_date": entry.entry_date,
        "amount": entry.amount,
        "source": entry.source,
        "category": entry.category,
        "note": entry.note,
    }


def _resolve(db, ident: str) -> IncomeEntry | None:
    """Resolve a CLI arg to an IncomeEntry by ID or source name.

    A source pays you many times, so for name lookups we prefer the
    most-recently-added entry. Pass the explicit ID to disambiguate.
    """
    from clibo.core.base import lookup_by_id_or_name
    if ident.isdigit():
        entry = db.get(IncomeEntry, int(ident))
        if entry:
            return entry
    return db.exec(
        select(IncomeEntry)
        .where(IncomeEntry.source.ilike(f"%{ident}%"))
        .order_by(IncomeEntry.id.desc())
    ).first() or lookup_by_id_or_name(db, IncomeEntry, ident, IncomeEntry.source)


def _month_range(spec: str | None) -> tuple[date, date, str]:
    """Resolve a ``YYYY-MM`` spec (or None = current month) to a date range."""
    if spec:
        try:
            anchor = datetime.strptime(spec, "%Y-%m").date()
        except ValueError as exc:
            raise typer.BadParameter("Month must be YYYY-MM") from exc
    else:
        anchor = date.today()
    first = anchor.replace(day=1)
    nxt = (first.replace(year=first.year + 1, month=1) if first.month == 12
           else first.replace(month=first.month + 1))
    return first, nxt, first.strftime("%Y-%m")


@app.command()
def add(
    source: str = typer.Argument(..., help="Where the money came from (e.g. 'Acme Corp', 'gig')"),
    amount: float = typer.Option(..., "--amount", "-a", help="Amount received"),
    category: str = typer.Option("other", "--category", "-c",
                                 help="freelance / salary / gift / refund / dividend / other"),
    on: str = typer.Option("today", "--date", "-d", help="Date received"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """💵 Log an income event."""
    if amount <= 0:
        fail("Amount must be positive", json_out=json_out)
    entry = IncomeEntry(
        amount=amount, source=source, category=category.lower(),
        entry_date=parse_date(on), note=note,
    )
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        data = _row(entry)
    ok(f"Logged {EMOJI} {money(amount)} from {source} ({category})",
       json_out=json_out, data=data)


@app.command(name="list")
def list_entries(
    days: int = typer.Option(30, "--days", help="Look back this many days"),
    category: str = typer.Option(None, "--category", "-c", help="Filter by category"),
    json_out: JsonOpt = False,
) -> None:
    """💵 List recent income entries."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        query = select(IncomeEntry).where(IncomeEntry.entry_date >= since)
        if category:
            query = query.where(IncomeEntry.category == category.lower())
        entries = list(
            db.exec(query.order_by(IncomeEntry.entry_date.desc(), IncomeEntry.id.desc())).all()
        )
    render_rows(
        [_row(e) for e in entries],
        [("id", "ID"), ("entry_date", "Date"), ("amount", "Amount"),
         ("source", "Source"), ("category", "Category")],
        json_out=json_out,
        title="💵 Income",
        formatters={"amount": lambda v, r: money(v)},
        empty="No income yet — try: clibo income add 'freelance gig' -a 500 -c freelance",
    )


@app.command()
def month(
    month_spec: str = typer.Option(None, "--month", "-m", help="YYYY-MM (default: this month)"),
    json_out: JsonOpt = False,
) -> None:
    """📅 This month's income, broken down by category."""
    first, nxt, label = _month_range(month_spec)
    with session() as db:
        entries = list(
            db.exec(
                select(IncomeEntry).where(
                    IncomeEntry.entry_date >= first, IncomeEntry.entry_date < nxt
                )
            ).all()
        )
    total = round(sum(e.amount for e in entries), 2)
    by_cat: dict[str, float] = {}
    for entry in entries:
        by_cat[entry.category] = round(by_cat.get(entry.category, 0) + entry.amount, 2)
    rows = [
        {"category": cat, "amount": amt,
         "share": round(amt / total * 100, 1) if total else 0.0}
        for cat, amt in sorted(by_cat.items(), key=lambda kv: kv[1], reverse=True)
    ]
    if json_out:
        render_record(
            {"month": label, "total": total, "entries": len(entries),
             "by_category": rows, "currency": get_currency()},
            json_out=True,
        )
        return
    render_rows(
        rows,
        [("category", "Category"), ("amount", "Amount"), ("share", "Share")],
        json_out=False,
        title=f"💵 Income · {label}",
        formatters={
            "amount": lambda v, r: money(v),
            "share": lambda v, r: bar(v, 100),
        },
        empty=f"No income in {label}.",
    )
    if rows:
        console.print(f"  💰 [bold]Total:[/bold] {money(total)}   ·   {len(entries)} entries")


@app.command()
def show(
    entry: str = typer.Argument(..., help="Entry ID or source name (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """💵 Show one income entry. Accepts a numeric ID or a source name."""
    with session() as db:
        target = _resolve(db, entry)
        if not target:
            fail(f"No income entry matching {entry!r}", json_out=json_out)
        data = _row(target) | {"created_at": target.created_at}
    render_record(data, json_out=json_out, title=f"💵 Income #{target.id}")


@app.command()
def edit(
    entry: str = typer.Argument(..., help="Entry ID or source name (fuzzy)"),
    amount: float = typer.Option(None, "--amount", "-a"),
    source: str = typer.Option(None, "--source"),
    category: str = typer.Option(None, "--category", "-c"),
    note: str = typer.Option(None, "--note", "-n"),
    json_out: JsonOpt = False,
) -> None:
    """💵 Edit an income entry. Accepts a numeric ID or a source name."""
    with session() as db:
        target = _resolve(db, entry)
        if not target:
            fail(f"No income entry matching {entry!r}", json_out=json_out)
        for field, value in {"amount": amount, "source": source,
                             "category": category, "note": note}.items():
            if value is not None:
                setattr(target, field, value.lower() if field == "category" else value)
        db.add(target)
        db.flush()
        data = _row(target)
    ok(f"Updated income #{target.id}", json_out=json_out, data=data)


@app.command()
def rm(
    entry: str = typer.Argument(..., help="Entry ID or source name (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """💵 Delete an income entry. Accepts a numeric ID or a source name."""
    with session() as db:
        target = _resolve(db, entry)
        if not target:
            fail(f"No income entry matching {entry!r}", json_out=json_out)
        eid = target.id
        db.delete(target)
    ok(f"Deleted income entry #{eid}", json_out=json_out, data={"deleted": eid})


@app.command()
def year(
    yr: int = typer.Option(None, "--year", "-y",
                            help="Calendar year (default: current)"),
    json_out: JsonOpt = False,
) -> None:
    """📅 Annual income — total, by_category, by_month, biggest source.

    Mirrors `expense year` / `donations year`. Answers
    *"how much did I make this year?"* + the per-month breakdown.
    """
    target_year = yr or date.today().year
    start = date(target_year, 1, 1)
    end = date(target_year, 12, 31)
    with session() as db:
        entries = list(
            db.exec(
                select(IncomeEntry)
                .where(IncomeEntry.entry_date >= start)
                .where(IncomeEntry.entry_date <= end)
            ).all()
        )
    total = round(sum(e.amount for e in entries), 2)
    by_cat: dict[str, float] = {}
    by_source: dict[str, float] = {}
    by_month: dict[int, float] = {}
    for e in entries:
        by_cat[e.category] = round(by_cat.get(e.category, 0) + e.amount, 2)
        by_source[e.source] = round(by_source.get(e.source, 0) + e.amount, 2)
        by_month[e.entry_date.month] = round(
            by_month.get(e.entry_date.month, 0) + e.amount, 2
        )
    biggest_month = (
        max(by_month.items(), key=lambda kv: kv[1]) if by_month else None
    )
    top_sources = sorted(by_source.items(), key=lambda kv: -kv[1])[:5]
    data = {
        "year": target_year,
        "entries": len(entries),
        "total": total,
        "avg_per_month": round(total / 12, 2) if total else 0.0,
        "by_category": [
            {"category": c, "amount": a}
            for c, a in sorted(by_cat.items(), key=lambda kv: -kv[1])
        ],
        "by_month": [
            {"month": m, "amount": by_month.get(m, 0.0)}
            for m in range(1, 13)
        ],
        "top_sources": [
            {"source": s, "amount": a} for s, a in top_sources
        ],
        "biggest_month": (
            {"month": biggest_month[0], "amount": biggest_month[1]}
            if biggest_month else None
        ),
        "currency": get_currency(),
    }
    render_record(data, json_out=json_out, title=f"📅 Income · {target_year}")


@app.command()
def stats(
    days: int = typer.Option(30, "--days", help="Window size in days"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Income stats over the last N days."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        entries = list(
            db.exec(select(IncomeEntry).where(IncomeEntry.entry_date >= since)).all()
        )
    if not entries:
        fail("No income in this window", json_out=json_out)
    total = round(sum(e.amount for e in entries), 2)
    by_cat: dict[str, float] = {}
    for entry in entries:
        by_cat[entry.category] = round(by_cat.get(entry.category, 0) + entry.amount, 2)
    top = sorted(by_cat.items(), key=lambda kv: kv[1], reverse=True)[:5]
    # Lifetime by-year aggregation — "which year did I earn the most?"
    with session() as db:
        all_entries = list(db.exec(select(IncomeEntry)).all())
    by_year: dict[int, float] = {}
    for e in all_entries:
        by_year[e.entry_date.year] = round(
            by_year.get(e.entry_date.year, 0) + e.amount, 2
        )
    by_year_rows = [
        {"year": y, "total": amt}
        for y, amt in sorted(by_year.items(), reverse=True)
    ]
    data = {
        "window_days": days,
        "entries": len(entries),
        "total": total,
        "avg_per_day": round(total / days, 2),
        "biggest": max(e.amount for e in entries),
        "top_categories": [{"category": c, "amount": a} for c, a in top],
        "currency": get_currency(),
        "by_year": by_year_rows,
    }
    render_record(data, json_out=json_out, title=f"📊 Income stats · last {days}d")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `update` is the SQL-natural synonym for `edit`; both work.
app.command(name="update", help="Alias for `edit`")(edit)

# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
