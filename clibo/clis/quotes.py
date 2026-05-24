"""💬 quotes — a personal commonplace book of quotes worth keeping."""

from __future__ import annotations

import random
from datetime import datetime

import typer
from sqlalchemy import or_
from sqlmodel import Field, SQLModel, select

from clibo.core.db import session
from clibo.core.output import JsonOpt, console, fail, ok, render_record, render_rows

NAME = "quotes"
HELP = "💬 A commonplace book of quotes worth keeping"
EMOJI = "💬"


class Quote(SQLModel, table=True):
    """One saved quote with optional author and source."""

    __tablename__ = "quotes_quote"

    id: int | None = Field(default=None, primary_key=True)
    text: str
    author: str | None = None
    source: str | None = None
    tags: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _row(quote: Quote) -> dict:
    return {
        "id": quote.id,
        "text": quote.text,
        "author": quote.author,
        "source": quote.source,
        "tags": quote.tags,
        "created_at": quote.created_at,
    }


@app.command()
def add(
    text: str = typer.Argument(..., help="The quote itself"),
    author: str = typer.Option(None, "--author", "-a", help="Who said it"),
    source: str = typer.Option(None, "--source", "-s", help="Where it's from (book, talk, URL)"),
    tag: str = typer.Option(None, "--tag", "-t", help="Comma-separated tags"),
    json_out: JsonOpt = False,
) -> None:
    """💬 Save a quote."""
    quote = Quote(text=text, author=author, source=source, tags=tag)
    with session() as db:
        db.add(quote)
        db.flush()
        db.refresh(quote)
        data = _row(quote)
    attrib = f" — {author}" if author else ""
    ok(f"Saved {EMOJI} \"{text[:60]}{'…' if len(text) > 60 else ''}\"{attrib}",
       json_out=json_out, data=data)


@app.command(name="list")
def list_quotes(
    author: str = typer.Option(None, "--author", "-a", help="Filter by author"),
    tag: str = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    json_out: JsonOpt = False,
) -> None:
    """💬 List quotes."""
    with session() as db:
        query = select(Quote)
        if author:
            query = query.where(Quote.author.ilike(f"%{author}%"))
        if tag:
            query = query.where(Quote.tags.ilike(f"%{tag}%"))
        quotes = list(db.exec(query.order_by(Quote.id.desc())).all())
    render_rows(
        [_row(q) for q in quotes],
        [("id", "ID"), ("text", "Quote"), ("author", "Author"),
         ("source", "Source"), ("tags", "Tags")],
        json_out=json_out,
        title="💬 Quotes",
        empty="No quotes yet — try: clibo quotes add 'wisdom' -a 'sage' -s 'book'",
    )


@app.command()
def show(quote_id: int = typer.Argument(..., help="Quote ID"), json_out: JsonOpt = False) -> None:
    """💬 Show one quote."""
    with session() as db:
        quote = db.get(Quote, quote_id)
        if not quote:
            fail(f"No quote #{quote_id}", json_out=json_out)
        data = _row(quote)
    if json_out:
        render_record(data, json_out=True)
        return
    console.print(f"\n  [italic]\"{quote.text}\"[/italic]")
    if quote.author:
        console.print(f"     — [bold]{quote.author}[/bold]"
                      + (f", [dim]{quote.source}[/dim]" if quote.source else ""))
    elif quote.source:
        console.print(f"     [dim]{quote.source}[/dim]")
    if quote.tags:
        console.print(f"     [dim]tags: {quote.tags}[/dim]")
    console.print()


@app.command()
def search(
    query: str = typer.Argument(..., help="Text to search in quote/author/source/tags"),
    json_out: JsonOpt = False,
) -> None:
    """🔍 Search quotes."""
    pattern = f"%{query}%"
    with session() as db:
        quotes = list(
            db.exec(
                select(Quote).where(
                    or_(
                        Quote.text.ilike(pattern),
                        Quote.author.ilike(pattern),
                        Quote.source.ilike(pattern),
                        Quote.tags.ilike(pattern),
                    )
                ).order_by(Quote.id.desc())
            ).all()
        )
    render_rows(
        [_row(q) for q in quotes],
        [("id", "ID"), ("text", "Quote"), ("author", "Author")],
        json_out=json_out,
        title=f"🔍 Quotes matching '{query}'",
        empty=f"No quotes match '{query}'.",
    )


@app.command(name="random")
def pick(json_out: JsonOpt = False) -> None:
    """🎲 Pick one random quote — for inspiration."""
    with session() as db:
        quotes = list(db.exec(select(Quote)).all())
    if not quotes:
        fail("No quotes saved yet — add one first", json_out=json_out)
    chosen = random.choice(quotes)
    data = _row(chosen)
    if json_out:
        render_record(data, json_out=True)
        return
    console.print(f"\n  💬 [italic]\"{chosen.text}\"[/italic]")
    if chosen.author:
        console.print(f"     — [bold]{chosen.author}[/bold]")
    console.print()


@app.command()
def rm(quote_id: int = typer.Argument(..., help="Quote ID"), json_out: JsonOpt = False) -> None:
    """💬 Delete a quote."""
    with session() as db:
        quote = db.get(Quote, quote_id)
        if not quote:
            fail(f"No quote #{quote_id}", json_out=json_out)
        db.delete(quote)
    ok(f"Deleted quote #{quote_id}", json_out=json_out, data={"deleted": quote_id})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Quote stats — counts and most-quoted authors."""
    with session() as db:
        quotes = list(db.exec(select(Quote)).all())
    by_author: dict[str, int] = {}
    for quote in quotes:
        if quote.author:
            by_author[quote.author] = by_author.get(quote.author, 0) + 1
    top = sorted(by_author.items(), key=lambda kv: kv[1], reverse=True)[:5]
    data = {
        "total": len(quotes),
        "with_author": sum(1 for q in quotes if q.author),
        "with_source": sum(1 for q in quotes if q.source),
        "unique_authors": len(by_author),
        "top_authors": [{"author": a, "count": n} for a, n in top],
    }
    render_record(data, json_out=json_out, title="📊 Quote stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)
