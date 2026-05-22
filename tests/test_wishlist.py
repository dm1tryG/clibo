"""Tests for the ⭐ wishlist tool."""

from __future__ import annotations


def test_add_item(cli):
    data = cli.json("wishlist", "add", "Standing desk", "-p", "350", "-P", "4")
    assert data["name"] == "Standing desk"
    assert data["price"] == 350.0
    assert data["priority"] == 4


def test_list_sorted_by_priority(cli):
    cli.run("wishlist", "add", "Low", "-P", "1")
    cli.run("wishlist", "add", "High", "-P", "5")
    items = cli.json("wishlist", "list")
    assert items[0]["name"] == "High"


def test_buy_hides_from_default_list(cli):
    item = cli.json("wishlist", "add", "Headphones", "-p", "200")
    cli.run("wishlist", "buy", str(item["id"]))
    assert cli.json("wishlist", "list") == []
    assert len(cli.json("wishlist", "list", "--all")) == 1


def test_stats_pending_cost(cli):
    cli.run("wishlist", "add", "A", "-p", "100")
    cli.run("wishlist", "add", "B", "-p", "50")
    stats = cli.json("wishlist", "stats")
    assert stats["pending"] == 2
    assert stats["pending_cost"] == 150.0


def test_invalid_priority_fails(cli):
    result = cli.run("wishlist", "add", "Bad", "-P", "9")
    assert result.exit_code != 0
