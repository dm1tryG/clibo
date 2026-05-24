"""Tests for the 📚 books tool."""

from __future__ import annotations


def test_add_book(cli):
    data = cli.json("books", "add", "Atomic Habits", "-a", "James Clear", "-p", "320")
    assert data["title"] == "Atomic Habits"
    assert data["author"] == "James Clear"
    assert data["status"] == "wishlist"


def test_read_promotes_and_finishes(cli):
    cli.run("books", "add", "Short Book", "-p", "100")
    progress = cli.json("books", "read", "Short Book", "40")
    assert progress["status"] == "reading"
    assert progress["pages_read"] == 40
    done = cli.json("books", "read", "Short Book", "60")
    assert done["status"] == "finished"
    assert done["pages_read"] == 100


def test_finish_with_rating(cli):
    cli.run("books", "add", "Doorstopper", "-p", "500")
    data = cli.json("books", "finish", "Doorstopper", "-r", "5")
    assert data["status"] == "finished"
    assert data["rating"] == 5


def test_list_filters_by_status(cli):
    cli.run("books", "add", "Wish 1", "-s", "wishlist")
    cli.run("books", "add", "Wish 2", "-s", "wishlist")
    cli.run("books", "add", "Read 1", "-s", "finished")
    wishlist = cli.json("books", "list", "-s", "wishlist")
    assert len(wishlist) == 2


def test_stats(cli):
    cli.run("books", "add", "A", "-p", "100", "-s", "finished", "-r", "4")
    cli.run("books", "add", "B", "-p", "200", "-s", "finished", "-r", "5")
    cli.run("books", "add", "C", "-s", "reading")
    stats = cli.json("books", "stats")
    assert stats["total"] == 3
    assert stats["finished"] == 2
    assert stats["avg_rating"] == 4.5


def test_invalid_rating_fails(cli):
    result = cli.run("books", "add", "Bad", "-r", "9")
    assert result.exit_code != 0


def test_log_is_alias_for_read(cli):
    """`books log 30 <title>` is the natural-language form of `books read`."""
    read_help = cli.run("books", "read", "--help")
    log_help = cli.run("books", "log", "--help")
    assert read_help.exit_code == 0 and "Usage:" in read_help.output
    assert log_help.exit_code == 0 and "Usage:" in log_help.output
    cli.run("books", "add", "Atomic Habits", "-a", "James Clear")
    data = cli.json("books", "log", "Atomic Habits", "30")
    assert data["pages_read"] == 30


# ── reading sessions: --minutes + history + edit + rm-by-title (iter 91) ──


def test_read_with_minutes_writes_session(cli):
    cli.run("books", "add", "Atomic Habits", "-p", "320")
    data = cli.json("books", "read", "Atomic Habits", "30", "--minutes", "45")
    assert data["session_pages"] == 30
    assert data["session_minutes"] == 45
    assert data["session_pages_per_hour"] == 40.0


def test_read_minutes_optional(cli):
    """Existing flag-free usage stays compatible."""
    cli.run("books", "add", "Some Book", "-p", "200")
    data = cli.json("books", "read", "Some Book", "20")
    assert data["session_minutes"] == 0
    assert data["session_pages_per_hour"] is None


def test_read_backdate_session(cli):
    cli.run("books", "add", "Atomic Habits", "-p", "320")
    cli.run("books", "read", "Atomic Habits", "30", "-t", "45",
                    "-d", "yesterday")
    # entry_date is on the session not the book row, so check via history
    history = cli.json("books", "history")
    assert any(h["book"] == "Atomic Habits" and h["pages"] == 30
               for h in history)


def test_read_negative_minutes_fails(cli):
    cli.run("books", "add", "X", "-p", "100")
    result = cli.run("books", "read", "X", "10", "-t", "-1")
    assert result.exit_code != 0


def test_history_filters_by_book(cli):
    cli.run("books", "add", "Book A", "-p", "200")
    cli.run("books", "add", "Book B", "-p", "200")
    cli.run("books", "read", "Book A", "10", "-t", "20")
    cli.run("books", "read", "Book B", "15", "-t", "20")
    a_only = cli.json("books", "history", "--book", "Book A")
    assert all(h["book"] == "Book A" for h in a_only)


def test_history_filters_by_days(cli):
    cli.run("books", "add", "Old", "-p", "200")
    cli.run("books", "read", "Old", "5", "-t", "10", "-d", "30 days ago")
    cli.run("books", "read", "Old", "5", "-t", "10")
    recent = cli.json("books", "history", "--days", "7")
    assert len(recent) == 1


def test_history_empty(cli):
    cli.run("books", "add", "Atomic Habits", "-p", "320")
    history = cli.json("books", "history")
    assert history == []


def test_edit_by_title(cli):
    cli.run("books", "add", "Original Title", "-p", "300")
    edited = cli.json("books", "edit", "Original Title", "-t", "New Title")
    assert edited["title"] == "New Title"


def test_edit_status_to_finished_stamps_date(cli):
    cli.run("books", "add", "Some Book", "-p", "100")
    edited = cli.json("books", "edit", "Some Book", "-s", "finished")
    assert edited["status"] == "finished"
    assert edited["finished"] is not None


def test_edit_pages_read_override(cli):
    cli.run("books", "add", "X", "-p", "300")
    edited = cli.json("books", "edit", "X", "--pages-read", "150")
    assert edited["pages_read"] == 150
    assert edited["progress_pct"] == 50.0


def test_edit_rejects_bad_rating(cli):
    cli.run("books", "add", "X", "-p", "100")
    result = cli.run("books", "edit", "X", "-r", "9")
    assert result.exit_code != 0


def test_rm_by_title(cli):
    cli.run("books", "add", "Doomed", "-p", "100")
    cli.json("books", "rm", "Doomed")
    listing = cli.json("books", "list")
    assert not any(b["title"] == "Doomed" for b in listing)


def test_rm_cascades_sessions(cli):
    """Deleting a book also deletes its reading sessions."""
    cli.run("books", "add", "Cascading", "-p", "100")
    cli.run("books", "read", "Cascading", "10", "-t", "20")
    cli.run("books", "read", "Cascading", "15")
    cli.json("books", "rm", "Cascading")
    history = cli.json("books", "history")
    assert history == []


def test_rm_unknown_fails(cli):
    result = cli.run("books", "rm", "ghost-book-xyz")
    assert result.exit_code != 0


def test_resolve_exact_match_wins_over_substring(cli):
    """`books show 'Dune'` finds Dune (exact), not 'Dune: Part Two'."""
    cli.run("books", "add", "Dune: Part Two", "-p", "300")
    cli.run("books", "add", "Dune", "-p", "400")
    data = cli.json("books", "show", "Dune")
    assert data["title"] == "Dune"


def test_stats_includes_session_pace(cli):
    cli.run("books", "add", "Atomic Habits", "-p", "320")
    cli.run("books", "read", "Atomic Habits", "30", "-t", "45")
    cli.run("books", "read", "Atomic Habits", "20", "-t", "15")
    stats = cli.json("books", "stats")
    assert stats["sessions_logged"] == 2
    assert stats["session_pages"] == 50
    assert stats["session_minutes"] == 60
    assert stats["avg_pages_per_hour"] == 50.0
    assert stats["days_read"] == 1


# ── books year subcommand + stats.by_year (iter 116) ──


def test_books_year_current(cli):
    """`books year` defaults to current calendar year."""
    cli.run("books", "add", "Atomic Habits", "-p", "320")
    cli.run("books", "finish", "Atomic Habits", "-r", "5")
    from datetime import date
    data = cli.json("books", "year")
    assert data["year"] == date.today().year
    assert data["books_finished"] == 1
    assert "Atomic Habits" in data["titles"]
    assert data["avg_rating"] == 5


def test_books_year_specific(cli):
    """`books year -y 2025` filters by the requested year."""
    cli.run("books", "add", "Atomic Habits", "-p", "320")
    cli.run("books", "finish", "Atomic Habits", "-r", "5")
    cli.run("books", "add", "Range", "-p", "280")
    cli.run("books", "finish", "Range", "-r", "4")
    # Backdate one of the finished dates via SQLite to a past year
    import sqlite3

    from clibo.core import config
    db = sqlite3.connect(str(config.db_path()))
    db.execute("UPDATE books_book SET finished='2025-08-15' WHERE title='Range'")
    db.commit()
    db.close()
    data = cli.json("books", "year", "-y", "2025")
    assert data["year"] == 2025
    assert data["books_finished"] == 1
    assert data["titles"] == ["Range"]


def test_books_year_empty(cli):
    """`books year` on an empty year returns zero counts (not an error)."""
    data = cli.json("books", "year", "-y", "1999")
    assert data["year"] == 1999
    assert data["books_finished"] == 0
    assert data["titles"] == []


def test_books_year_aggregates_sessions(cli):
    """Pages-read and minutes in `books year` come from `BookSession`."""
    cli.run("books", "add", "Dune", "-p", "500")
    cli.run("books", "read", "Dune", "50", "-t", "60")
    data = cli.json("books", "year")
    assert data["sessions"] == 1
    assert data["pages_read"] == 50
    assert data["minutes"] == 60
    assert data["avg_pages_per_hour"] == 50.0


def test_books_year_top_rated_limited_to_three(cli):
    """`top_rated` is capped at 3 entries, sorted desc by rating."""
    for i, r in enumerate([3, 5, 4, 5, 2], start=1):
        cli.run("books", "add", f"Book {i}", "-p", "100")
        cli.run("books", "finish", f"Book {i}", "-r", str(r))
    data = cli.json("books", "year")
    assert len(data["top_rated"]) == 3
    assert data["top_rated"][0]["rating"] == 5
    # All top three should be the highest-rated books
    assert all(b["rating"] >= 4 for b in data["top_rated"])


def test_books_stats_includes_by_year(cli):
    """Lifetime `stats` now includes a `by_year` aggregation."""
    cli.run("books", "add", "Atomic Habits", "-p", "320")
    cli.run("books", "finish", "Atomic Habits", "-r", "5")
    data = cli.json("books", "stats")
    assert "by_year" in data
    assert len(data["by_year"]) == 1
    # Most-recent year first
    from datetime import date
    assert data["by_year"][0]["year"] == date.today().year
    assert data["by_year"][0]["books_finished"] == 1


def test_books_stats_by_year_skips_unfinished(cli):
    """Unfinished books (no `finished` date) don't appear in by_year."""
    cli.run("books", "add", "Reading", "-p", "300", "-s", "reading")
    cli.run("books", "add", "Wishlist", "-p", "300")  # wishlist
    data = cli.json("books", "stats")
    assert data["by_year"] == []


# ── books top: longest / best-rated / most recent ──


def test_books_top_default_sorts_by_pages_desc(cli):
    cli.run("books", "add", "Short", "-p", "100", "-s", "finished", "-r", "3")
    cli.run("books", "add", "Long", "-p", "800", "-s", "finished", "-r", "5")
    cli.run("books", "add", "Medium", "-p", "400", "-s", "finished", "-r", "4")
    rows = cli.json("books", "top")
    assert [r["title"] for r in rows] == ["Long", "Medium", "Short"]


def test_books_top_by_rating(cli):
    cli.run("books", "add", "Best", "-p", "100", "-s", "finished", "-r", "5")
    cli.run("books", "add", "OK", "-p", "100", "-s", "finished", "-r", "3")
    cli.run("books", "add", "Unrated", "-p", "100", "-s", "finished")
    rows = cli.json("books", "top", "--by", "rating")
    titles = [r["title"] for r in rows]
    assert titles == ["Best", "OK"]
    # Unrated finished books are excluded from the rating sort.


def test_books_top_by_recent_skips_never_finished(cli):
    cli.run("books", "add", "Done", "-p", "100", "-s", "finished")
    cli.run("books", "add", "Still reading", "-p", "100", "-s", "reading")
    rows = cli.json("books", "top", "--by", "recent")
    assert [r["title"] for r in rows] == ["Done"]


def test_books_top_status_filter(cli):
    cli.run("books", "add", "Finished", "-p", "100", "-s", "finished")
    cli.run("books", "add", "InProgress", "-p", "500", "-s", "reading")
    # Default status=finished excludes the in-progress book.
    finished_rows = cli.json("books", "top")
    assert [r["title"] for r in finished_rows] == ["Finished"]
    # `--status any` includes both, longest first.
    any_rows = cli.json("books", "top", "--status", "any")
    assert [r["title"] for r in any_rows] == ["InProgress", "Finished"]


def test_books_top_limit(cli):
    for n, p in enumerate([100, 200, 300, 400], start=1):
        cli.run("books", "add", f"Book{n}", "-p", str(p), "-s", "finished")
    rows = cli.json("books", "top", "--limit", "2")
    assert len(rows) == 2
    assert rows[0]["pages"] == 400


def test_books_top_invalid_by_fails(cli):
    result = cli.run("books", "top", "--by", "nonsense")
    assert result.exit_code != 0


def test_books_top_invalid_status_fails(cli):
    result = cli.run("books", "top", "--status", "nonsense")
    assert result.exit_code != 0


def test_books_top_empty_returns_empty_list(cli):
    rows = cli.json("books", "top")
    assert rows == []


# ── books stale: in-progress reads that have gone cold ──


def test_books_stale_excludes_books_with_recent_sessions(cli):
    """A book read today shouldn't show up in stale."""
    cli.run("books", "add", "Fresh", "-p", "300", "-s", "reading")
    cli.run("books", "read", "Fresh", "50")  # today
    rows = cli.json("books", "stale")
    assert rows == []


def test_books_stale_picks_old_reads(cli):
    """A book whose last session is older than --days appears."""
    cli.run("books", "add", "Stale", "-p", "400", "-s", "reading")
    cli.run("books", "read", "Stale", "50", "-d", "30 days ago")
    rows = cli.json("books", "stale")
    titles = [r["title"] for r in rows]
    assert "Stale" in titles
    stale = next(r for r in rows if r["title"] == "Stale")
    assert stale["days_since_last_session"] >= 29


def test_books_stale_excludes_finished_and_wishlist(cli):
    """Only `reading`-status books are eligible — finished/wishlist excluded."""
    cli.run("books", "add", "Done", "-p", "100", "-s", "finished")
    cli.run("books", "add", "Wished", "-p", "200")  # wishlist
    cli.run("books", "add", "Open", "-p", "300", "-s", "reading")
    cli.run("books", "read", "Open", "10", "-d", "30 days ago")
    rows = cli.json("books", "stale")
    titles = {r["title"] for r in rows}
    assert titles == {"Open"}


def test_books_stale_threshold(cli):
    """`--days 60` only flags books over that threshold."""
    cli.run("books", "add", "Recent stale", "-p", "300", "-s", "reading")
    cli.run("books", "add", "Very stale", "-p", "400", "-s", "reading")
    cli.run("books", "read", "Recent stale", "20", "-d", "20 days ago")
    cli.run("books", "read", "Very stale", "30", "-d", "90 days ago")
    rows = cli.json("books", "stale", "--days", "60")
    titles = [r["title"] for r in rows]
    assert titles == ["Very stale"]


def test_books_stale_negative_days_fails(cli):
    result = cli.run("books", "stale", "--days", "-1")
    assert result.exit_code != 0


def test_books_stale_sorted_longest_untouched_first(cli):
    cli.run("books", "add", "Older", "-p", "300", "-s", "reading")
    cli.run("books", "add", "Newer", "-p", "300", "-s", "reading")
    cli.run("books", "read", "Older", "50", "-d", "60 days ago")
    cli.run("books", "read", "Newer", "50", "-d", "30 days ago")
    rows = cli.json("books", "stale")
    assert [r["title"] for r in rows] == ["Older", "Newer"]


def test_books_stale_empty_when_all_fresh(cli):
    cli.run("books", "add", "Fresh", "-p", "300", "-s", "reading")
    cli.run("books", "read", "Fresh", "50")
    result = cli.run("books", "stale")
    assert result.exit_code == 0
    assert "All in-progress" in result.output
