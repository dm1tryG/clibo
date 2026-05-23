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
