"""Tests for the 🎁 gifts tool."""

from __future__ import annotations


def test_add_gift(cli):
    data = cli.json("gifts", "add", "Mom", "cookbook", "-o", "birthday", "-p", "30")
    assert data["recipient"] == "Mom"
    assert data["idea"] == "cookbook"
    assert data["status"] == "idea"


def test_status_flow(cli):
    gift = cli.json("gifts", "add", "Dad", "headphones", "-p", "100")
    bought = cli.json("gifts", "bought", str(gift["id"]))
    assert bought["status"] == "bought"
    given = cli.json("gifts", "given", str(gift["id"]))
    assert given["status"] == "given"


def test_list_filters_by_recipient(cli):
    cli.run("gifts", "add", "Alice", "book")
    cli.run("gifts", "add", "Bob", "mug")
    alice = cli.json("gifts", "list", "-r", "Alice")
    assert len(alice) == 1


def test_stats_counts_spending(cli):
    g = cli.json("gifts", "add", "Friend", "candle", "-p", "25")
    cli.run("gifts", "bought", str(g["id"]))
    cli.run("gifts", "add", "Other", "idea only", "-p", "999")
    stats = cli.json("gifts", "stats")
    assert stats["total"] == 2
    assert stats["spent"] == 25.0


def test_negative_price_fails(cli):
    result = cli.run("gifts", "add", "X", "thing", "-p", "-5")
    assert result.exit_code != 0
