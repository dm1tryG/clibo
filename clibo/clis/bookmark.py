"""🔖 bookmark — bookmarks & link saver."""

from __future__ import annotations

import webbrowser
from datetime import datetime

import typer
from sqlalchemy import or_
from sqlmodel import Field, SQLModel, select

from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "bookmark"
HELP = "🔖 Bookmarks & link saver"
EMOJI = "🔖"


class Bookmark(SQLModel, table=True):
    """A saved link."""

    __tablename__ = "bookmark_bookmark"

    id: int | None = Field(default=None, primary_key=True)
    url: str
    title: str | None = None
    tags: str | None = None
    category: str = "other"
    favorite: bool = False
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _resolve(db, ident: str) -> Bookmark | None:
    """Resolve a CLI arg to a Bookmark by ID, title or URL (fuzzy).

    Search hits ``title`` first, then ``url``, then falls back to the
    generic helper. Most-recent wins ties.
    """
    from clibo.core.base import lookup_by_id_or_name
    if ident.isdigit():
        bm = db.get(Bookmark, int(ident))
        if bm:
            return bm
    pattern = f"%{ident}%"
    # Title match first (most natural), then URL match, then generic.
    return db.exec(
        select(Bookmark)
        .where(Bookmark.title.ilike(pattern))
        .order_by(Bookmark.id.desc())
    ).first() or db.exec(
        select(Bookmark)
        .where(Bookmark.url.ilike(pattern))
        .order_by(Bookmark.id.desc())
    ).first() or lookup_by_id_or_name(db, Bookmark, ident, Bookmark.title)


def _row(bookmark: Bookmark) -> dict:
    return {
        "id": bookmark.id,
        "title": bookmark.title or bookmark.url,
        "url": bookmark.url,
        "tags": bookmark.tags,
        "category": bookmark.category,
        "favorite": bookmark.favorite,
        "note": bookmark.note,
    }


@app.command()
def add(
    url: str = typer.Argument(..., help="The link to save"),
    title: str = typer.Option(None, "--title", "-t", help="A title for the link"),
    tag: str = typer.Option(None, "--tag", help="Comma-separated tags"),
    category: str = typer.Option("other", "--category", "-c", help="Category"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🔖 Save a bookmark."""
    bookmark = Bookmark(
        url=url, title=title, tags=tag, category=category.lower(), note=note,
    )
    with session() as db:
        db.add(bookmark)
        db.flush()
        db.refresh(bookmark)
        data = _row(bookmark)
    ok(f"Saved {EMOJI} {title or url}", json_out=json_out, data=data)


@app.command(name="list")
def list_bookmarks(
    tag: str = typer.Option(None, "--tag", help="Filter by tag"),
    category: str = typer.Option(None, "--category", "-c", help="Filter by category"),
    favorites: bool = typer.Option(False, "--favorites", "-f", help="Only favorites"),
    json_out: JsonOpt = False,
) -> None:
    """🔖 List saved bookmarks."""
    with session() as db:
        query = select(Bookmark)
        if tag:
            query = query.where(Bookmark.tags.ilike(f"%{tag}%"))
        if category:
            query = query.where(Bookmark.category == category.lower())
        if favorites:
            query = query.where(Bookmark.favorite == True)  # noqa: E712
        bookmarks = list(db.exec(query.order_by(Bookmark.created_at.desc())).all())
    render_rows(
        [_row(b) for b in bookmarks],
        [("id", "ID"), ("favorite", "★"), ("title", "Title"),
         ("url", "URL"), ("tags", "Tags"), ("category", "Category")],
        json_out=json_out,
        title="🔖 Bookmarks",
        formatters={"favorite": lambda v, r: "[yellow]★[/yellow]" if v else "[dim]·[/dim]"},
        empty="No bookmarks yet — try: clibo bookmark add https://example.com -t 'Example'",
    )


@app.command()
def show(
    bookmark: str = typer.Argument(..., help="Bookmark ID, title or URL (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """🔖 Show one bookmark. Accepts a numeric ID, title or URL substring."""
    with session() as db:
        target = _resolve(db, bookmark)
        if not target:
            fail(f"No bookmark matching {bookmark!r}", json_out=json_out)
        data = _row(target) | {"created_at": target.created_at}
    render_record(data, json_out=json_out, title=f"🔖 Bookmark #{target.id}")


@app.command()
def search(
    query: str = typer.Argument(..., help="Text to search in titles, URLs and tags"),
    json_out: JsonOpt = False,
) -> None:
    """🔍 Search bookmarks."""
    pattern = f"%{query}%"
    with session() as db:
        bookmarks = list(
            db.exec(
                select(Bookmark).where(
                    or_(
                        Bookmark.title.ilike(pattern),
                        Bookmark.url.ilike(pattern),
                        Bookmark.tags.ilike(pattern),
                    )
                ).order_by(Bookmark.created_at.desc())
            ).all()
        )
    render_rows(
        [_row(b) for b in bookmarks],
        [("id", "ID"), ("title", "Title"), ("url", "URL"), ("tags", "Tags")],
        json_out=json_out,
        title=f"🔍 Bookmarks matching '{query}'",
        empty=f"No bookmarks match '{query}'.",
    )


@app.command(name="open")
def open_bookmark(
    bookmark: str = typer.Argument(..., help="Bookmark ID, title or URL (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """🌐 Open a bookmark in your web browser."""
    with session() as db:
        target = _resolve(db, bookmark)
        if not target:
            fail(f"No bookmark matching {bookmark!r}", json_out=json_out)
        bid, url = target.id, target.url
    if json_out:
        render_record({"id": bid, "url": url, "opened": False}, json_out=True)
        return
    webbrowser.open(url)
    ok(f"Opening {url}", json_out=False)


@app.command()
def fav(
    bookmark: str = typer.Argument(..., help="Bookmark ID, title or URL (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """⭐ Mark a bookmark as a favorite."""
    _set_favorite(bookmark, True, json_out)


@app.command()
def unfav(
    bookmark: str = typer.Argument(..., help="Bookmark ID, title or URL (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """⭐ Remove a bookmark from favorites."""
    _set_favorite(bookmark, False, json_out)


def _set_favorite(ident: str, favorite: bool, json_out: bool) -> None:
    with session() as db:
        target = _resolve(db, ident)
        if not target:
            fail(f"No bookmark matching {ident!r}", json_out=json_out)
        target.favorite = favorite
        db.add(target)
        bid = target.id
    verb = "Favorited" if favorite else "Unfavorited"
    ok(f"{verb} bookmark #{bid}", json_out=json_out,
       data={"id": bid, "favorite": favorite})


@app.command()
def edit(
    bookmark: str = typer.Argument(..., help="Bookmark ID, title or URL (fuzzy)"),
    title: str = typer.Option(None, "--title", "-t", help="New title"),
    url: str = typer.Option(None, "--url", "-u", help="New URL"),
    tag: str = typer.Option(None, "--tag", help="New comma-separated tags"),
    category: str = typer.Option(None, "--category", "-c"),
    note: str = typer.Option(None, "--note", "-n"),
    json_out: JsonOpt = False,
) -> None:
    """🔖 Edit a bookmark. Accepts a numeric ID, title or URL substring."""
    with session() as db:
        target = _resolve(db, bookmark)
        if not target:
            fail(f"No bookmark matching {bookmark!r}", json_out=json_out)
        if title is not None:
            target.title = title
        if url is not None:
            target.url = url
        if tag is not None:
            target.tags = tag
        if category is not None:
            target.category = category.lower()
        if note is not None:
            target.note = note
        db.add(target)
        db.flush()
        data = _row(target)
    ok(f"Updated bookmark #{target.id}", json_out=json_out, data=data)


@app.command()
def rm(
    bookmark: str = typer.Argument(..., help="Bookmark ID, title or URL (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """🔖 Delete a bookmark."""
    with session() as db:
        target = _resolve(db, bookmark)
        if not target:
            fail(f"No bookmark matching {bookmark!r}", json_out=json_out)
        bid = target.id
        db.delete(target)
    ok(f"Deleted bookmark #{bid}", json_out=json_out, data={"deleted": bid})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Bookmark stats."""
    with session() as db:
        bookmarks = list(db.exec(select(Bookmark)).all())
    by_category: dict[str, int] = {}
    for bookmark in bookmarks:
        by_category[bookmark.category] = by_category.get(bookmark.category, 0) + 1
    data = {
        "total": len(bookmarks),
        "favorites": sum(1 for b in bookmarks if b.favorite),
        "by_category": by_category,
    }
    render_record(data, json_out=json_out, title="📊 Bookmark stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)
