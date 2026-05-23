"""🌙 dreams — dream journal with vividness, lucid flag, and symbols."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta

import typer
from sqlalchemy import or_
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, console, fail, ok, render_record, render_rows

NAME = "dreams"
HELP = "🌙 Dream journal — vividness, lucid flag, symbols"
EMOJI = "🌙"


class Dream(SQLModel, table=True):
    """One dream entry."""

    __tablename__ = "dreams_dream"

    id: int | None = Field(default=None, primary_key=True)
    summary: str
    description: str | None = None
    entry_date: date = Field(default_factory=date.today, index=True)
    vividness: int = 3  # 1-5
    lucid: bool = False
    symbols: str | None = None  # comma-separated tags
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _row(dream: Dream) -> dict:
    return {
        "id": dream.id,
        "entry_date": dream.entry_date,
        "summary": dream.summary,
        "description": dream.description,
        "vividness": dream.vividness,
        "lucid": dream.lucid,
        "symbols": dream.symbols,
    }


def _split_symbols(value: str | None) -> list[str]:
    if not value:
        return []
    return [s.strip().lower() for s in value.split(",") if s.strip()]


@app.command()
def add(
    summary: str = typer.Argument(..., help="One-line headline for the dream"),
    description: str = typer.Option(None, "--desc", "-D", help="Full narrative"),
    vividness: int = typer.Option(3, "--vivid", "-v", help="Vividness 1-5"),
    lucid: bool = typer.Option(False, "--lucid", help="Was this a lucid dream?"),
    symbols: str = typer.Option(None, "--symbols", "-s",
                                 help="Comma-separated symbol tags (e.g. flying,water)"),
    on: str = typer.Option("today", "--date", "-d", help="Date dreamt"),
    json_out: JsonOpt = False,
) -> None:
    """🌙 Log a dream."""
    if not 1 <= vividness <= 5:
        fail("Vividness must be 1-5", json_out=json_out)
    dream = Dream(
        summary=summary, description=description, vividness=vividness, lucid=lucid,
        symbols=symbols, entry_date=parse_date(on),
    )
    with session() as db:
        db.add(dream)
        db.flush()
        db.refresh(dream)
        data = _row(dream)
    flair = " 🪄 lucid" if lucid else ""
    ok(f"Logged {EMOJI} {summary} (vivid {vividness}/5){flair}",
       json_out=json_out, data=data)


@app.command()
def today(json_out: JsonOpt = False) -> None:
    """🌙 Show today's dream entries."""
    with session() as db:
        dreams = list(
            db.exec(
                select(Dream)
                .where(Dream.entry_date == date.today())
                .order_by(Dream.id)
            ).all()
        )
    if json_out:
        render_record(
            {"date": date.today(), "dreams": [_row(d) for d in dreams]}, json_out=True
        )
        return
    if not dreams:
        console.print("\n  🌙 [dim]No dreams logged for today.[/dim]\n")
        return
    console.print(f"\n🌙 [bold]Dreams[/bold] · {date.today():%A %d %B}\n")
    for dream in dreams:
        flair = "  🪄 lucid" if dream.lucid else ""
        stars = "★" * dream.vividness + "☆" * (5 - dream.vividness)
        console.print(f"  [bold]{dream.summary}[/bold]   [dim]{stars}[/dim]{flair}")
        if dream.symbols:
            console.print(f"    [dim]symbols: {dream.symbols}[/dim]")
        if dream.description:
            console.print(f"    {dream.description}")
        console.print()


@app.command(name="list")
def list_dreams(
    days: int = typer.Option(14, "--days", help="Look back this many days"),
    lucid_only: bool = typer.Option(False, "--lucid", help="Only lucid dreams"),
    json_out: JsonOpt = False,
) -> None:
    """🌙 Recent dreams."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        query = select(Dream).where(Dream.entry_date >= since)
        if lucid_only:
            query = query.where(Dream.lucid == True)  # noqa: E712
        dreams = list(
            db.exec(query.order_by(Dream.entry_date.desc(), Dream.id.desc())).all()
        )
    render_rows(
        [_row(d) for d in dreams],
        [("id", "ID"), ("entry_date", "Date"), ("summary", "Summary"),
         ("vividness", "Vivid"), ("lucid", "Lucid"), ("symbols", "Symbols")],
        json_out=json_out,
        title="🌙 Dream journal",
        formatters={
            "vividness": lambda v, r: "★" * v + "☆" * (5 - v),
            "lucid": lambda v, r: "[magenta]🪄[/magenta]" if v else "[dim]·[/dim]",
        },
        empty="No dreams yet — try: clibo dreams add 'flying over the city'",
    )


@app.command()
def show(dream_id: int = typer.Argument(..., help="Dream ID"), json_out: JsonOpt = False) -> None:
    """🌙 Show one dream in detail."""
    with session() as db:
        dream = db.get(Dream, dream_id)
        if not dream:
            fail(f"No dream #{dream_id}", json_out=json_out)
        data = _row(dream)
    if json_out:
        render_record(data, json_out=True)
        return
    flair = "   🪄 [magenta]lucid[/magenta]" if dream.lucid else ""
    stars = "★" * dream.vividness + "☆" * (5 - dream.vividness)
    console.print(f"\n🌙 [bold]{dream.summary}[/bold]   "
                  f"[dim]({dream.entry_date}, vivid {stars})[/dim]{flair}\n")
    if dream.description:
        console.print(f"  {dream.description}\n")
    if dream.symbols:
        console.print(f"  [dim]symbols: {dream.symbols}[/dim]\n")


@app.command()
def search(
    query: str = typer.Argument(..., help="Text to search in summary/description/symbols"),
    json_out: JsonOpt = False,
) -> None:
    """🔍 Search dreams."""
    pattern = f"%{query}%"
    with session() as db:
        dreams = list(
            db.exec(
                select(Dream).where(
                    or_(
                        Dream.summary.ilike(pattern),
                        Dream.description.ilike(pattern),
                        Dream.symbols.ilike(pattern),
                    )
                ).order_by(Dream.entry_date.desc())
            ).all()
        )
    render_rows(
        [_row(d) for d in dreams],
        [("id", "ID"), ("entry_date", "Date"), ("summary", "Summary"),
         ("symbols", "Symbols")],
        json_out=json_out,
        title=f"🔍 Dreams matching '{query}'",
        empty=f"No dreams match '{query}'.",
    )


@app.command()
def symbols(json_out: JsonOpt = False) -> None:
    """🔮 Symbol frequency — recurring dream patterns."""
    with session() as db:
        dreams = list(db.exec(select(Dream)).all())
    counter: Counter[str] = Counter()
    for dream in dreams:
        for symbol in _split_symbols(dream.symbols):
            counter[symbol] += 1
    rows = [
        {"symbol": s, "count": c} for s, c in counter.most_common()
    ]
    render_rows(
        rows,
        [("symbol", "Symbol"), ("count", "Times seen")],
        json_out=json_out,
        title="🔮 Dream symbols",
        empty="No symbols tagged yet — add with `-s flying,water`.",
    )


@app.command()
def rm(dream_id: int = typer.Argument(..., help="Dream ID"), json_out: JsonOpt = False) -> None:
    """🌙 Delete a dream."""
    with session() as db:
        dream = db.get(Dream, dream_id)
        if not dream:
            fail(f"No dream #{dream_id}", json_out=json_out)
        db.delete(dream)
    ok(f"Deleted dream #{dream_id}", json_out=json_out, data={"deleted": dream_id})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Dream stats — counts, lucid rate, average vividness."""
    with session() as db:
        dreams = list(db.exec(select(Dream)).all())
    if not dreams:
        fail("No dreams logged yet", json_out=json_out)
    lucid = sum(1 for d in dreams if d.lucid)
    counter: Counter[str] = Counter()
    for dream in dreams:
        for symbol in _split_symbols(dream.symbols):
            counter[symbol] += 1
    data = {
        "total": len(dreams),
        "lucid": lucid,
        "lucid_rate_pct": round(lucid / len(dreams) * 100, 1),
        "avg_vividness": round(sum(d.vividness for d in dreams) / len(dreams), 1),
        "days_logged": len({d.entry_date for d in dreams}),
        "top_symbols": [{"symbol": s, "count": c} for s, c in counter.most_common(5)],
    }
    render_record(data, json_out=json_out, title="📊 Dream stats")
