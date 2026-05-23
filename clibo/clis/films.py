"""🎬 films — movie & show watchlist with ratings."""

from __future__ import annotations

from datetime import date, datetime

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "films"
HELP = "🎬 Movie & show watchlist with ratings"
EMOJI = "🎬"
STATUSES = ["watchlist", "watching", "watched", "dropped"]
KINDS = ["movie", "show"]


class Film(SQLModel, table=True):
    """One movie or show on your list."""

    __tablename__ = "films_film"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    kind: str = "movie"
    year: int | None = None
    status: str = "watchlist"
    rating: int | None = None  # 1–5
    watched_on: date | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _resolve(db, ident: str) -> Film | None:
    """Look up a film by numeric ID or by (case-insensitive) title."""
    if ident.isdigit():
        film = db.get(Film, int(ident))
        if film:
            return film
    return db.exec(select(Film).where(Film.title.ilike(f"%{ident}%"))).first()


def _row(film: Film) -> dict:
    return {
        "id": film.id,
        "title": film.title,
        "kind": film.kind,
        "year": film.year,
        "status": film.status,
        "rating": film.rating,
        "watched_on": film.watched_on,
        "note": film.note,
    }


def _status_cell(status: str) -> str:
    return {
        "watchlist": "[dim]watchlist[/dim]",
        "watching": "[cyan]watching[/cyan]",
        "watched": "[green]✓ watched[/green]",
        "dropped": "[yellow]dropped[/yellow]",
    }.get(status, status)


@app.command()
def add(
    title: str = typer.Argument(..., help="Film or show title"),
    kind: str = typer.Option("movie", "--kind", "-k", help="movie / show"),
    year: int = typer.Option(None, "--year", "-y", help="Release year"),
    status: str = typer.Option("watchlist", "--status", "-s", help=f"{'/'.join(STATUSES)}"),
    rating: int = typer.Option(None, "--rating", "-r", help="Rating 1–5"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🎬 Add a film to your list."""
    kind = kind.lower()
    if kind not in KINDS:
        fail(f"Kind must be one of: {', '.join(KINDS)}", json_out=json_out)
    status = status.lower()
    if status not in STATUSES:
        fail(f"Status must be one of: {', '.join(STATUSES)}", json_out=json_out)
    if rating is not None and not 1 <= rating <= 5:
        fail("Rating must be 1–5", json_out=json_out)
    film = Film(
        title=title, kind=kind, year=year, status=status, rating=rating, note=note,
        watched_on=date.today() if status == "watched" else None,
    )
    with session() as db:
        db.add(film)
        db.flush()
        db.refresh(film)
        data = _row(film)
    ok(f"Added {EMOJI} '{title}'" + (f" ({year})" if year else ""),
       json_out=json_out, data=data)


@app.command()
def watched(
    film: str = typer.Argument(..., help="Title (fuzzy) or ID"),
    rating: int = typer.Option(None, "--rating", "-r", help="Rating 1–5"),
    json_out: JsonOpt = False,
) -> None:
    """✅ Mark a film as watched, optionally with a rating."""
    if rating is not None and not 1 <= rating <= 5:
        fail("Rating must be 1–5", json_out=json_out)
    with session() as db:
        target = _resolve(db, film)
        if not target:
            fail(f"No film matching {film!r}", json_out=json_out)
        target.status = "watched"
        target.watched_on = date.today()
        if rating is not None:
            target.rating = rating
        db.add(target)
        db.flush()
        data = _row(target)
    ok(f"Watched '{target.title}'" + (f" — {rating}★" if rating else ""),
       json_out=json_out, data=data)


@app.command()
def rate(
    film: str = typer.Argument(..., help="Title (fuzzy) or ID"),
    rating: int = typer.Argument(..., help="Rating 1–5"),
    json_out: JsonOpt = False,
) -> None:
    """⭐ Set or change a film's rating."""
    if not 1 <= rating <= 5:
        fail("Rating must be 1–5", json_out=json_out)
    with session() as db:
        target = _resolve(db, film)
        if not target:
            fail(f"No film matching {film!r}", json_out=json_out)
        target.rating = rating
        db.add(target)
        db.flush()
        data = _row(target)
    ok(f"Rated '{target.title}' — {rating}★", json_out=json_out, data=data)


@app.command(name="list")
def list_films(
    status: str = typer.Option(None, "--status", "-s", help="Filter by status"),
    kind: str = typer.Option(None, "--kind", "-k", help="movie / show"),
    json_out: JsonOpt = False,
) -> None:
    """🎬 List films."""
    if status and status.lower() not in STATUSES:
        fail(f"Status must be one of: {', '.join(STATUSES)}", json_out=json_out)
    if kind and kind.lower() not in KINDS:
        fail(f"Kind must be one of: {', '.join(KINDS)}", json_out=json_out)
    with session() as db:
        query = select(Film)
        if status:
            query = query.where(Film.status == status.lower())
        if kind:
            query = query.where(Film.kind == kind.lower())
        films = list(db.exec(query.order_by(Film.status, Film.title)).all())
    render_rows(
        [_row(f) for f in films],
        [("id", "ID"), ("title", "Title"), ("kind", "Kind"),
         ("year", "Year"), ("status", "Status"), ("rating", "★")],
        json_out=json_out,
        title="🎬 Films",
        formatters={
            "status": lambda v, r: _status_cell(v),
            "rating": lambda v, r: ("★" * v + "☆" * (5 - v)) if v else "[dim]—[/dim]",
        },
        empty="No films yet — try: clibo films add 'Dune' -y 2021 -k movie",
    )


@app.command()
def rm(film_id: int = typer.Argument(..., help="Film ID"), json_out: JsonOpt = False) -> None:
    """🎬 Delete a film."""
    with session() as db:
        target = db.get(Film, film_id)
        if not target:
            fail(f"No film #{film_id}", json_out=json_out)
        db.delete(target)
    ok(f"Deleted film #{film_id}", json_out=json_out, data={"deleted": film_id})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Watchlist stats — watched, average rating, top-rated."""
    with session() as db:
        films = list(db.exec(select(Film)).all())
    watched_films = [f for f in films if f.status == "watched"]
    ratings = [f.rating for f in watched_films if f.rating]
    top = sorted([f for f in watched_films if f.rating],
                 key=lambda f: (-f.rating, f.title))[:3]
    data = {
        "total": len(films),
        "watched": len(watched_films),
        "watchlist": sum(1 for f in films if f.status == "watchlist"),
        "movies": sum(1 for f in films if f.kind == "movie"),
        "shows": sum(1 for f in films if f.kind == "show"),
        "avg_rating": round(sum(ratings) / len(ratings), 1) if ratings else None,
        "top_rated": [{"title": f.title, "rating": f.rating} for f in top],
    }
    render_record(data, json_out=json_out, title="📊 Films stats")
