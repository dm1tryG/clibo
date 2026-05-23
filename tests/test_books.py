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
