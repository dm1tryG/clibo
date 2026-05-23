"""Tests for the 💬 quotes tool."""

from __future__ import annotations


def test_add_quote(cli):
    data = cli.json(
        "quotes", "add",
        "Make it work, make it right, make it fast",
        "-a", "Kent Beck",
        "-s", "Extreme Programming Explained",
    )
    assert data["text"] == "Make it work, make it right, make it fast"
    assert data["author"] == "Kent Beck"
    assert data["source"] == "Extreme Programming Explained"


def test_search_by_author(cli):
    cli.run("quotes", "add", "first", "-a", "Anne")
    cli.run("quotes", "add", "second", "-a", "Bob")
    results = cli.json("quotes", "search", "anne")
    assert len(results) == 1


def test_search_by_text(cli):
    cli.run("quotes", "add", "The unexamined life")
    cli.run("quotes", "add", "Stay hungry")
    results = cli.json("quotes", "search", "examined")
    assert len(results) == 1


def test_list_filters_by_author(cli):
    cli.run("quotes", "add", "a", "-a", "Beck")
    cli.run("quotes", "add", "b", "-a", "Beck")
    cli.run("quotes", "add", "c", "-a", "Knuth")
    beck = cli.json("quotes", "list", "-a", "Beck")
    assert len(beck) == 2


def test_random_picks(cli):
    cli.run("quotes", "add", "only one", "-a", "Author")
    chosen = cli.json("quotes", "random")
    assert chosen["text"] == "only one"


def test_random_without_quotes_fails(cli):
    result = cli.run("quotes", "random")
    assert result.exit_code != 0


def test_stats_top_authors(cli):
    cli.run("quotes", "add", "a1", "-a", "Beck")
    cli.run("quotes", "add", "a2", "-a", "Beck")
    cli.run("quotes", "add", "a3", "-a", "Beck")
    cli.run("quotes", "add", "b1", "-a", "Knuth")
    stats = cli.json("quotes", "stats")
    assert stats["total"] == 4
    assert stats["top_authors"][0] == {"author": "Beck", "count": 3}
