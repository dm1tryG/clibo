"""🔖 bookmark — bookmarks & link saver."""

from __future__ import annotations

import webbrowser
from datetime import datetime

import typer
from sqlalchemy import or_
from sqlmodel import Field, SQLModel, select

from clibo.core.db import session
from clibo.core.output import JsonOpt, console, fail, ok, render_record, render_rows

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
def show(bookmark_id: int = typer.Argument(..., help="Bookmark ID"), json_out: JsonOpt = False) -> None:
    """🔖 Show one bookmark."""
    with session() as db:
        bookmark = db.get(Bookmark, bookmark_id)
        if not bookmark:
            fail(f"No bookmark #{bookmark_id}", json_out=json_out)
        data = _row(bookmark) | {"created_at": bookmark.created_at}
    render_record(data, json_out=json_out, title=f"🔖 Bookmark #{bookmark_id}")


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
    bookmark_id: int = typer.Argument(..., help="Bookmark ID"),
    json_out: JsonOpt = False,
) -> None:
    """🌐 Open a bookmark in your web browser."""
    with session() as db:
        bookmark = db.get(Bookmark, bookmark_id)
        if not bookmark:
            fail(f"No bookmark #{bookmark_id}", json_out=json_out)
        url = bookmark.url
    if json_out:
        render_record({"id": bookmark_id, "url": url, "opened": False}, json_out=True)
        return
    webbrowser.open(url)
    ok(f"Opening {url}", json_out=False)


@app.command()
def fav(bookmark_id: int = typer.Argument(..., help="Bookmark ID"), json_out: JsonOpt = False) -> None:
    """⭐ Mark a bookmark as a favorite."""
    _set_favorite(bookmark_id, True, json_out)


@app.command()
def unfav(bookmark_id: int = typer.Argument(..., help="Bookmark ID"), json_out: JsonOpt = False) -> None:
    """⭐ Remove a bookmark from favorites."""
    _set_favorite(bookmark_id, False, json_out)


def _set_favorite(bookmark_id: int, favorite: bool, json_out: bool) -> None:
    with session() as db:
        bookmark = db.get(Bookmark, bookmark_id)
        if not bookmark:
            fail(f"No bookmark #{bookmark_id}", json_out=json_out)
        bookmark.favorite = favorite
        db.add(bookmark)
    verb = "Favorited" if favorite else "Unfavorited"
    ok(f"{verb} bookmark #{bookmark_id}", json_out=json_out,
       data={"id": bookmark_id, "favorite": favorite})


@app.command()
def rm(bookmark_id: int = typer.Argument(..., help="Bookmark ID"), json_out: JsonOpt = False) -> None:
    """🔖 Delete a bookmark."""
    with session() as db:
        bookmark = db.get(Bookmark, bookmark_id)
        if not bookmark:
            fail(f"No bookmark #{bookmark_id}", json_out=json_out)
        db.delete(bookmark)
    ok(f"Deleted bookmark #{bookmark_id}", json_out=json_out, data={"deleted": bookmark_id})


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
