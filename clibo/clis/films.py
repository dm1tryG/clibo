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
    """One movie or show on your list.

    For TV shows, ``season`` and ``episode`` track the *last watched
    episode* — a single pointer rather than a per-episode log. That's
    what users actually want to recall ("where was I in Better Call
    Saul?") without the heft of an episodes table.
    """

    __tablename__ = "films_film"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    kind: str = "movie"
    year: int | None = None
    status: str = "watchlist"
    rating: int | None = None  # 1–5
    watched_on: date | None = None
    season: int | None = None    # last watched season (shows only)
    episode: int | None = None   # last watched episode within that season
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _resolve(db, ident: str) -> Film | None:
    """Look up a film by numeric ID or by (case-insensitive) title."""
    if ident.isdigit():
        film = db.get(Film, int(ident))
        if film:
            return film
    # Exact title match wins over substring (so "Dune" finds "Dune" not "Dune: Part Two").
    return db.exec(select(Film).where(Film.title.ilike(ident))).first() \
        or db.exec(select(Film).where(Film.title.ilike(f"%{ident}%"))).first()


def _progress_str(film: Film) -> str | None:
    """Render the S<n>E<n> pointer for shows, ``None`` for movies or pre-progress."""
    if film.season is None and film.episode is None:
        return None
    if film.season is not None and film.episode is not None:
        return f"S{film.season:02d}E{film.episode:02d}"
    if film.season is not None:
        return f"S{film.season:02d}"
    return f"E{film.episode:02d}"


def _row(film: Film) -> dict:
    return {
        "id": film.id,
        "title": film.title,
        "kind": film.kind,
        "year": film.year,
        "status": film.status,
        "rating": film.rating,
        "watched_on": film.watched_on,
        "season": film.season,
        "episode": film.episode,
        "progress": _progress_str(film),
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
    season: int = typer.Option(None, "--season", "-S",
                                help="Current season (shows only)"),
    episode: int = typer.Option(None, "--episode", "-E",
                                 help="Current episode within the season"),
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
    if (season is not None or episode is not None) and kind != "show":
        fail("Season/episode only make sense with --kind show", json_out=json_out)
    if season is not None and season < 1:
        fail("Season must be ≥ 1", json_out=json_out)
    if episode is not None and episode < 1:
        fail("Episode must be ≥ 1", json_out=json_out)
    # If they're tracking progress, the show is clearly being watched —
    # auto-bump status from the default "watchlist" so the list view reflects reality.
    if (season is not None or episode is not None) and status == "watchlist":
        status = "watching"
    film = Film(
        title=title, kind=kind, year=year, status=status, rating=rating, note=note,
        season=season, episode=episode,
        watched_on=date.today() if status == "watched" else None,
    )
    with session() as db:
        db.add(film)
        db.flush()
        db.refresh(film)
        data = _row(film)
    suffix = f" ({year})" if year else ""
    prog = _progress_str(film)
    if prog:
        suffix += f" · {prog}"
    ok(f"Added {EMOJI} '{title}'{suffix}", json_out=json_out, data=data)


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
def progress(
    film: str = typer.Argument(..., help="Show title (fuzzy) or ID"),
    season: int = typer.Option(None, "--season", "-S", help="Current season"),
    episode: int = typer.Option(None, "--episode", "-E", help="Current episode"),
    bump: bool = typer.Option(False, "--bump", "-b",
                               help="Increment the episode by 1 (no flags needed)"),
    json_out: JsonOpt = False,
) -> None:
    """📺 Update the last-watched episode pointer for a TV show.

    Three modes:
      • ``-S 6 -E 5`` — set the pointer absolutely
      • ``-E 5``       — keep the current season, set the episode
      • ``--bump``     — increment the episode by 1

    Sets status to ``watching`` so the show shows up in the list as
    in-flight rather than ``watchlist``.
    """
    if season is not None and season < 1:
        fail("Season must be ≥ 1", json_out=json_out)
    if episode is not None and episode < 1:
        fail("Episode must be ≥ 1", json_out=json_out)
    if not bump and season is None and episode is None:
        fail("Specify --season/--episode or --bump", json_out=json_out)
    with session() as db:
        target = _resolve(db, film)
        if not target:
            fail(f"No film matching {film!r}", json_out=json_out)
        if target.kind != "show":
            fail(f"'{target.title}' is a {target.kind}, not a show",
                 json_out=json_out)
        if bump:
            target.episode = (target.episode or 0) + 1
            if target.season is None:
                target.season = 1
        else:
            if season is not None:
                target.season = season
            if episode is not None:
                target.episode = episode
        if target.status in ("watchlist",):
            target.status = "watching"
        db.add(target)
        db.flush()
        data = _row(target)
    ok(f"📺 '{target.title}' → {_progress_str(target)}",
       json_out=json_out, data=data)


@app.command()
def show(
    film: str = typer.Argument(..., help="Title (fuzzy) or ID"),
    json_out: JsonOpt = False,
) -> None:
    """🎬 Show one film/show with current progress."""
    with session() as db:
        target = _resolve(db, film)
        if not target:
            fail(f"No film matching {film!r}", json_out=json_out)
        data = _row(target) | {"created_at": target.created_at}
    render_record(data, json_out=json_out, title=f"🎬 {target.title}")


@app.command()
def edit(
    film: str = typer.Argument(..., help="Title (fuzzy) or ID"),
    title: str = typer.Option(None, "--title", "-t", help="New title"),
    kind: str = typer.Option(None, "--kind", "-k", help="movie / show"),
    year: int = typer.Option(None, "--year", "-y"),
    status: str = typer.Option(None, "--status", "-s",
                                help=f"{'/'.join(STATUSES)}"),
    rating: int = typer.Option(None, "--rating", "-r", help="Rating 1–5"),
    season: int = typer.Option(None, "--season", "-S"),
    episode: int = typer.Option(None, "--episode", "-E"),
    note: str = typer.Option(None, "--note", "-n"),
    json_out: JsonOpt = False,
) -> None:
    """🎬 Edit a film. Accepts a numeric ID or a title (fuzzy)."""
    if kind and kind.lower() not in KINDS:
        fail(f"Kind must be one of: {', '.join(KINDS)}", json_out=json_out)
    if status and status.lower() not in STATUSES:
        fail(f"Status must be one of: {', '.join(STATUSES)}", json_out=json_out)
    if rating is not None and not 1 <= rating <= 5:
        fail("Rating must be 1–5", json_out=json_out)
    with session() as db:
        target = _resolve(db, film)
        if not target:
            fail(f"No film matching {film!r}", json_out=json_out)
        if title is not None:
            target.title = title
        if kind is not None:
            target.kind = kind.lower()
        if year is not None:
            target.year = year
        if status is not None:
            target.status = status.lower()
            if status.lower() == "watched":
                target.watched_on = date.today()
        if rating is not None:
            target.rating = rating
        if season is not None:
            target.season = season
        if episode is not None:
            target.episode = episode
        if note is not None:
            target.note = note
        db.add(target)
        db.flush()
        data = _row(target)
    ok(f"Updated film #{target.id} — {target.title}",
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
         ("year", "Year"), ("status", "Status"), ("progress", "Progress"),
         ("rating", "★")],
        json_out=json_out,
        title="🎬 Films",
        formatters={
            "status": lambda v, r: _status_cell(v),
            "rating": lambda v, r: ("★" * v + "☆" * (5 - v)) if v else "[dim]—[/dim]",
            "progress": lambda v, r: (f"[cyan]{v}[/cyan]" if v else "[dim]—[/dim]"),
        },
        empty="No films yet — try: clibo films add 'Dune' -y 2021 -k movie",
    )


@app.command()
def rm(
    film: str = typer.Argument(..., help="Title (fuzzy) or ID"),
    json_out: JsonOpt = False,
) -> None:
    """🎬 Delete a film. Accepts a numeric ID or a title."""
    with session() as db:
        target = _resolve(db, film)
        if not target:
            fail(f"No film matching {film!r}", json_out=json_out)
        fid = target.id
        db.delete(target)
    ok(f"Deleted film #{fid}", json_out=json_out, data={"deleted": fid})


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
