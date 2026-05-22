"""Tests for the 🔖 bookmark tool."""

from __future__ import annotations


def test_add_bookmark(cli):
    data = cli.json("bookmark", "add", "https://example.com", "-t", "Example", "--tag", "ref")
    assert data["url"] == "https://example.com"
    assert data["title"] == "Example"


def test_search_matches_url_and_title(cli):
    cli.run("bookmark", "add", "https://python.org", "-t", "Python")
    cli.run("bookmark", "add", "https://rust-lang.org", "-t", "Rust")
    results = cli.json("bookmark", "search", "python")
    assert len(results) == 1
    assert results[0]["title"] == "Python"


def test_favorite_toggle_and_filter(cli):
    bm = cli.json("bookmark", "add", "https://fav.com")
    cli.run("bookmark", "fav", str(bm["id"]))
    favs = cli.json("bookmark", "list", "--favorites")
    assert len(favs) == 1
    cli.run("bookmark", "unfav", str(bm["id"]))
    assert cli.json("bookmark", "list", "--favorites") == []


def test_open_returns_url_in_json(cli):
    bm = cli.json("bookmark", "add", "https://open-me.com")
    opened = cli.json("bookmark", "open", str(bm["id"]))
    assert opened["url"] == "https://open-me.com"
    assert opened["opened"] is False


def test_stats(cli):
    cli.run("bookmark", "add", "https://a.com", "-c", "docs")
    cli.run("bookmark", "add", "https://b.com", "-c", "docs")
    stats = cli.json("bookmark", "stats")
    assert stats["total"] == 2
    assert stats["by_category"]["docs"] == 2


def test_remove(cli):
    bm = cli.json("bookmark", "add", "https://temp.com")
    removed = cli.json("bookmark", "rm", str(bm["id"]))
    assert removed["deleted"] == bm["id"]
