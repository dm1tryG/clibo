"""📚 books — reading log: what you're reading, progress, ratings."""

from __future__ import annotations

from datetime import date, datetime

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.db import session
from clibo.core.output import JsonOpt, bar, fail, ok, render_record, render_rows

NAME = "books"
HELP = "📚 Reading log — what you're reading, progress, ratings"
EMOJI = "📚"
STATUSES = ["wishlist", "reading", "finished", "dnf"]


class Book(SQLModel, table=True):
    """One book you're tracking."""

    __tablename__ = "books_book"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    author: str | None = None
    status: str = "wishlist"
    pages: int = 0
    pages_read: int = 0
    rating: int | None = None  # 1–5
    started: date | None = None
    finished: date | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _resolve(db, ident: str) -> Book | None:
    """Look up a book by numeric ID or by (case-insensitive) title."""
    if ident.isdigit():
        book = db.get(Book, int(ident))
        if book:
            return book
    return db.exec(select(Book).where(Book.title.ilike(f"%{ident}%"))).first()


def _row(book: Book) -> dict:
    progress = (
        round(book.pages_read / book.pages * 100, 1)
        if book.pages and book.pages_read else 0.0
    )
    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "status": book.status,
        "pages": book.pages,
        "pages_read": book.pages_read,
        "progress_pct": progress,
        "rating": book.rating,
        "started": book.started,
        "finished": book.finished,
        "note": book.note,
    }


def _status_cell(status: str) -> str:
    return {
        "wishlist": "[dim]wishlist[/dim]",
        "reading": "[cyan]reading[/cyan]",
        "finished": "[green]✓ finished[/green]",
        "dnf": "[yellow]dnf[/yellow]",
    }.get(status, status)


@app.command()
def add(
    title: str = typer.Argument(..., help="Book title"),
    author: str = typer.Option(None, "--author", "-a", help="Author"),
    pages: int = typer.Option(0, "--pages", "-p", help="Total pages"),
    status: str = typer.Option("wishlist", "--status", "-s", help=f"{'/'.join(STATUSES)}"),
    rating: int = typer.Option(None, "--rating", "-r", help="Rating 1–5 (for finished)"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """📚 Add a book to your shelf."""
    status = status.lower()
    if status not in STATUSES:
        fail(f"Status must be one of: {', '.join(STATUSES)}", json_out=json_out)
    if rating is not None and not 1 <= rating <= 5:
        fail("Rating must be 1–5", json_out=json_out)
    book = Book(
        title=title, author=author, status=status, pages=pages, rating=rating, note=note,
        started=date.today() if status == "reading" else None,
        finished=date.today() if status == "finished" else None,
    )
    with session() as db:
        db.add(book)
        db.flush()
        db.refresh(book)
        data = _row(book)
    detail = f" by {author}" if author else ""
    ok(f"Added {EMOJI} '{title}'{detail} ({status})", json_out=json_out, data=data)


@app.command()
def read(
    book: str = typer.Argument(..., help="Book title (fuzzy) or ID"),
    pages: int = typer.Argument(..., help="Pages read in this session"),
    json_out: JsonOpt = False,
) -> None:
    """📖 Log a reading session — add to ``pages_read``."""
    if pages <= 0:
        fail("Pages must be positive", json_out=json_out)
    with session() as db:
        target = _resolve(db, book)
        if not target:
            fail(f"No book matching {book!r}", json_out=json_out)
        if target.status == "wishlist":
            target.status = "reading"
            target.started = date.today()
        target.pages_read += pages
        if target.pages and target.pages_read >= target.pages:
            target.status = "finished"
            target.finished = date.today()
        db.add(target)
        db.flush()
        data = _row(target)
    flair = "  🎉 finished!" if data["status"] == "finished" else ""
    ok(f"Read {pages}p of '{target.title}' — {target.pages_read}/{target.pages or '?'} "
       f"({data['progress_pct']}%){flair}",
       json_out=json_out, data=data)


@app.command()
def start(
    book: str = typer.Argument(..., help="Book title or ID"),
    json_out: JsonOpt = False,
) -> None:
    """📖 Mark a wishlist book as currently reading."""
    with session() as db:
        target = _resolve(db, book)
        if not target:
            fail(f"No book matching {book!r}", json_out=json_out)
        target.status = "reading"
        target.started = target.started or date.today()
        db.add(target)
        db.flush()
        data = _row(target)
    ok(f"Started reading '{target.title}'", json_out=json_out, data=data)


@app.command()
def finish(
    book: str = typer.Argument(..., help="Book title or ID"),
    rating: int = typer.Option(None, "--rating", "-r", help="Rating 1–5"),
    json_out: JsonOpt = False,
) -> None:
    """🏁 Mark a book finished, optionally with a rating."""
    if rating is not None and not 1 <= rating <= 5:
        fail("Rating must be 1–5", json_out=json_out)
    with session() as db:
        target = _resolve(db, book)
        if not target:
            fail(f"No book matching {book!r}", json_out=json_out)
        target.status = "finished"
        target.finished = date.today()
        if target.pages and target.pages_read < target.pages:
            target.pages_read = target.pages
        if rating is not None:
            target.rating = rating
        db.add(target)
        db.flush()
        data = _row(target)
    ok(f"Finished '{target.title}' 🎉" + (f" — {rating}★" if rating else ""),
       json_out=json_out, data=data)


@app.command(name="list")
def list_books(
    status: str = typer.Option(None, "--status", "-s", help="Filter by status"),
    json_out: JsonOpt = False,
) -> None:
    """📚 List your books."""
    if status and status.lower() not in STATUSES:
        fail(f"Status must be one of: {', '.join(STATUSES)}", json_out=json_out)
    with session() as db:
        query = select(Book)
        if status:
            query = query.where(Book.status == status.lower())
        books = list(db.exec(query.order_by(Book.status, Book.title)).all())
    render_rows(
        [_row(b) for b in books],
        [("id", "ID"), ("title", "Title"), ("author", "Author"),
         ("status", "Status"), ("progress_pct", "Progress"),
         ("rating", "★")],
        json_out=json_out,
        title="📚 Books",
        formatters={
            "status": lambda v, r: _status_cell(v),
            "progress_pct": lambda v, r: bar(v, 100, width=14) if r["pages"] else "[dim]—[/dim]",
            "rating": lambda v, r: ("★" * v + "☆" * (5 - v)) if v else "[dim]—[/dim]",
        },
        empty="No books yet — try: clibo books add 'Atomic Habits' -a 'James Clear' -p 320",
    )


@app.command()
def show(book: str = typer.Argument(..., help="Book title or ID"), json_out: JsonOpt = False) -> None:
    """📚 Show one book in detail."""
    with session() as db:
        target = _resolve(db, book)
        if not target:
            fail(f"No book matching {book!r}", json_out=json_out)
        data = _row(target)
    render_record(data, json_out=json_out, title=f"📚 {data['title']}")


@app.command()
def rm(book_id: int = typer.Argument(..., help="Book ID"), json_out: JsonOpt = False) -> None:
    """📚 Delete a book from your shelf."""
    with session() as db:
        target = db.get(Book, book_id)
        if not target:
            fail(f"No book #{book_id}", json_out=json_out)
        db.delete(target)
    ok(f"Deleted book #{book_id}", json_out=json_out, data={"deleted": book_id})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Reading stats — finished, in-progress, pages read."""
    with session() as db:
        books = list(db.exec(select(Book)).all())
    finished = [b for b in books if b.status == "finished"]
    ratings = [b.rating for b in finished if b.rating]
    data = {
        "total": len(books),
        "reading": sum(1 for b in books if b.status == "reading"),
        "finished": len(finished),
        "wishlist": sum(1 for b in books if b.status == "wishlist"),
        "total_pages_read": sum(b.pages_read for b in books),
        "avg_rating": round(sum(ratings) / len(ratings), 1) if ratings else None,
    }
    render_record(data, json_out=json_out, title="📊 Reading stats")
