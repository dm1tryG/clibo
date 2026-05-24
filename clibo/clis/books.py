"""📚 books — reading log: what you're reading, progress, ratings."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
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


class BookSession(SQLModel, table=True):
    """One reading session — N pages on a book on a day, optionally timed.

    The parent ``Book.pages_read`` is the running total; this table stores
    the per-session events so users can answer "when did I last read?",
    "what was my reading pace last week?" — questions the counter alone
    can't.
    """

    __tablename__ = "books_session"

    id: int | None = Field(default=None, primary_key=True)
    book_id: int = Field(index=True)
    pages: int
    duration_min: int = 0
    entry_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    note: str | None = None


app = typer.Typer(no_args_is_help=True, help=HELP)


def _resolve(db, ident: str) -> Book | None:
    """Look up a book by numeric ID or by case-insensitive title (exact wins over substring)."""
    if ident.isdigit():
        book = db.get(Book, int(ident))
        if book:
            return book
    return db.exec(select(Book).where(Book.title.ilike(ident))).first() \
        or db.exec(select(Book).where(Book.title.ilike(f"%{ident}%"))).first()


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
    minutes: int = typer.Option(
        0, "--minutes", "-t", help="Minutes spent (enables pages/hour pace)"
    ),
    on: str = typer.Option("today", "--date", "-d", help="Date of the session"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """📖 Log a reading session — add to ``pages_read`` and record the
    session row in ``books_session`` (for history & pace queries).
    """
    if pages <= 0:
        fail("Pages must be positive", json_out=json_out)
    if minutes < 0:
        fail("Minutes cannot be negative", json_out=json_out)
    entry_date = parse_date(on)
    with session() as db:
        target = _resolve(db, book)
        if not target:
            fail(f"No book matching {book!r}", json_out=json_out)
        if target.status == "wishlist":
            target.status = "reading"
            target.started = target.started or entry_date
        target.pages_read += pages
        if target.pages and target.pages_read >= target.pages:
            target.status = "finished"
            target.finished = target.finished or entry_date
        db.add(target)
        db.flush()
        # Per-session row — what `history` and pace queries read from.
        sess = BookSession(
            book_id=target.id, pages=pages, duration_min=minutes,
            entry_date=entry_date, note=note,
        )
        db.add(sess)
        db.flush()
        db.refresh(sess)
        data = _row(target) | {
            "session_id": sess.id,
            "session_pages": pages,
            "session_minutes": minutes,
            "session_pages_per_hour": (
                round(pages / minutes * 60, 1) if minutes else None
            ),
        }
    flair = "  🎉 finished!" if data["status"] == "finished" else ""
    pace = f" · {data['session_pages_per_hour']} p/h" if minutes else ""
    ok(f"Read {pages}p of '{target.title}' — {target.pages_read}/{target.pages or '?'} "
       f"({data['progress_pct']}%){pace}{flair}",
       json_out=json_out, data=data)


# `log` is a friendlier alias for `read` — agents naturally translate
# "I read 30 pages today" to `books log 30`.
app.command(name="log", help="Alias for `read` — log a reading session")(read)


@app.command()
def history(
    days: int = typer.Option(14, "--days", help="Look back this many days"),
    book: str = typer.Option(
        None, "--book", "-b", help="Filter to one book (title fuzzy or ID)"
    ),
    json_out: JsonOpt = False,
) -> None:
    """📖 Recent reading sessions across all books."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        query = select(BookSession).where(BookSession.entry_date >= since)
        if book:
            target = _resolve(db, book)
            if not target:
                fail(f"No book matching {book!r}", json_out=json_out)
            query = query.where(BookSession.book_id == target.id)
        sessions = list(
            db.exec(
                query.order_by(
                    BookSession.entry_date.desc(), BookSession.id.desc()
                )
            ).all()
        )
        titles = {b.id: b.title for b in db.exec(select(Book)).all()}
    rows = [
        {
            "id": s.id,
            "entry_date": s.entry_date,
            "book": titles.get(s.book_id, "?"),
            "pages": s.pages,
            "minutes": s.duration_min,
            "pages_per_hour": (
                round(s.pages / s.duration_min * 60, 1) if s.duration_min else None
            ),
            "note": s.note,
        }
        for s in sessions
    ]
    render_rows(
        rows,
        [("entry_date", "Date"), ("book", "Book"),
         ("pages", "Pages"), ("minutes", "Min"),
         ("pages_per_hour", "p/h")],
        json_out=json_out,
        title=f"📖 Reading history · last {days}d",
        formatters={
            "minutes": lambda v, r: f"{v}" if v else "[dim]—[/dim]",
            "pages_per_hour": lambda v, r: f"{v}" if v else "[dim]—[/dim]",
        },
        empty="No reading sessions yet — try: clibo books read 'Atomic Habits' 30 -t 45",
    )


@app.command()
def edit(
    book: str = typer.Argument(..., help="Book title (fuzzy) or ID"),
    title: str = typer.Option(None, "--title", "-t", help="New title"),
    author: str = typer.Option(None, "--author", "-a", help="New author"),
    pages: int = typer.Option(None, "--pages", "-p", help="Total pages"),
    pages_read: int = typer.Option(
        None, "--pages-read", help="Override the running total"
    ),
    status: str = typer.Option(None, "--status", "-s",
                                help=f"{'/'.join(STATUSES)}"),
    rating: int = typer.Option(None, "--rating", "-r", help="Rating 1–5"),
    note: str = typer.Option(None, "--note", "-n"),
    json_out: JsonOpt = False,
) -> None:
    """📚 Edit a book. Accepts a numeric ID or a title (fuzzy)."""
    if status and status.lower() not in STATUSES:
        fail(f"Status must be one of: {', '.join(STATUSES)}", json_out=json_out)
    if rating is not None and not 1 <= rating <= 5:
        fail("Rating must be 1–5", json_out=json_out)
    if pages is not None and pages < 0:
        fail("Pages cannot be negative", json_out=json_out)
    if pages_read is not None and pages_read < 0:
        fail("Pages read cannot be negative", json_out=json_out)
    with session() as db:
        target = _resolve(db, book)
        if not target:
            fail(f"No book matching {book!r}", json_out=json_out)
        if title is not None:
            target.title = title
        if author is not None:
            target.author = author
        if pages is not None:
            target.pages = pages
        if pages_read is not None:
            target.pages_read = pages_read
        if status is not None:
            target.status = status.lower()
            if status.lower() == "finished":
                target.finished = target.finished or date.today()
            if status.lower() == "reading":
                target.started = target.started or date.today()
        if rating is not None:
            target.rating = rating
        if note is not None:
            target.note = note
        db.add(target)
        db.flush()
        data = _row(target)
    ok(f"Updated book #{target.id} — {target.title}",
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
def rm(
    book: str = typer.Argument(..., help="Book title (fuzzy) or ID"),
    json_out: JsonOpt = False,
) -> None:
    """📚 Delete a book from your shelf and all its reading sessions."""
    with session() as db:
        target = _resolve(db, book)
        if not target:
            fail(f"No book matching {book!r}", json_out=json_out)
        bid = target.id
        for s in db.exec(select(BookSession).where(BookSession.book_id == bid)).all():
            db.delete(s)
        db.delete(target)
    ok(f"Deleted book #{bid}", json_out=json_out, data={"deleted": bid})


@app.command()
def year(
    yr: int = typer.Option(None, "--year", "-y",
                            help="Calendar year (default: current)"),
    json_out: JsonOpt = False,
) -> None:
    """📅 Annual reading summary — books finished, pages read, sessions.

    Answers *"how was my year of reading?"* — total books finished
    that year, avg rating, pages read in sessions during the year,
    best-rated finishes.
    """
    target_year = yr or date.today().year
    start = date(target_year, 1, 1)
    end = date(target_year, 12, 31)
    with session() as db:
        finished_books = list(
            db.exec(
                select(Book)
                .where(Book.finished != None)  # noqa: E711
                .where(Book.finished >= start)
                .where(Book.finished <= end)
                .order_by(Book.finished.desc())
            ).all()
        )
        year_sessions = list(
            db.exec(
                select(BookSession)
                .where(BookSession.entry_date >= start)
                .where(BookSession.entry_date <= end)
            ).all()
        )
    ratings = [b.rating for b in finished_books if b.rating]
    sess_pages = sum(s.pages for s in year_sessions)
    sess_minutes = sum(s.duration_min for s in year_sessions)
    days_read = {s.entry_date for s in year_sessions}
    top_rated = sorted(
        (b for b in finished_books if b.rating),
        key=lambda b: (-b.rating, b.title),
    )[:3]
    data = {
        "year": target_year,
        "books_finished": len(finished_books),
        "avg_rating": (
            round(sum(ratings) / len(ratings), 1) if ratings else None
        ),
        "sessions": len(year_sessions),
        "pages_read": sess_pages,
        "minutes": sess_minutes,
        "days_read": len(days_read),
        "avg_pages_per_hour": (
            round(sess_pages / sess_minutes * 60, 1)
            if sess_minutes else None
        ),
        "titles": [b.title for b in finished_books],
        "top_rated": [
            {"title": b.title, "author": b.author, "rating": b.rating}
            for b in top_rated
        ],
    }
    render_record(data, json_out=json_out,
                  title=f"📅 Reading · {target_year}")


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Reading stats — finished, in-progress, pages read, session pace."""
    with session() as db:
        books = list(db.exec(select(Book)).all())
        sessions = list(db.exec(select(BookSession)).all())
    finished = [b for b in books if b.status == "finished"]
    ratings = [b.rating for b in finished if b.rating]
    session_pages = sum(s.pages for s in sessions)
    session_minutes = sum(s.duration_min for s in sessions)
    days_read = {s.entry_date for s in sessions}
    # Lifetime by-year breakdown — "what was my best year?"
    by_year: dict[int, int] = {}
    for b in finished:
        if b.finished is not None:
            by_year[b.finished.year] = by_year.get(b.finished.year, 0) + 1
    by_year_rows = [
        {"year": y, "books_finished": c}
        for y, c in sorted(by_year.items(), reverse=True)
    ]
    data = {
        "total": len(books),
        "reading": sum(1 for b in books if b.status == "reading"),
        "finished": len(finished),
        "wishlist": sum(1 for b in books if b.status == "wishlist"),
        "total_pages_read": sum(b.pages_read for b in books),
        "avg_rating": round(sum(ratings) / len(ratings), 1) if ratings else None,
        "sessions_logged": len(sessions),
        "session_pages": session_pages,
        "session_minutes": session_minutes,
        "avg_pages_per_hour": (
            round(session_pages / session_minutes * 60, 1)
            if session_minutes else None
        ),
        "days_read": len(days_read),
        "by_year": by_year_rows,
    }
    render_record(data, json_out=json_out, title="📊 Reading stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `update` is the SQL-natural synonym for `edit`; both work.
app.command(name="update", help="Alias for `edit`")(edit)

# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
