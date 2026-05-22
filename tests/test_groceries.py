"""Tests for the 🛒 groceries tool."""

from __future__ import annotations


def test_add_item(cli):
    data = cli.json("groceries", "add", "milk", "-q", "2 L", "-c", "dairy")
    assert data["name"] == "milk"
    assert data["quantity"] == "2 L"
    assert data["bought"] is False


def test_buy_hides_from_default_list(cli):
    item = cli.json("groceries", "add", "bread")
    cli.run("groceries", "buy", str(item["id"]))
    assert cli.json("groceries", "list") == []
    assert len(cli.json("groceries", "list", "--all")) == 1


def test_unbuy_restores(cli):
    item = cli.json("groceries", "add", "eggs")
    cli.run("groceries", "buy", str(item["id"]))
    data = cli.json("groceries", "unbuy", str(item["id"]))
    assert data["bought"] is False


def test_clear_removes_bought(cli):
    a = cli.json("groceries", "add", "apples")
    cli.run("groceries", "add", "oranges")
    cli.run("groceries", "buy", str(a["id"]))
    cleared = cli.json("groceries", "clear")
    assert cleared["cleared"] == 1
    assert len(cli.json("groceries", "list", "--all")) == 1


def test_stats(cli):
    a = cli.json("groceries", "add", "item1")
    cli.run("groceries", "add", "item2")
    cli.run("groceries", "buy", str(a["id"]))
    stats = cli.json("groceries", "stats")
    assert stats["total"] == 2
    assert stats["pending"] == 1
    assert stats["bought"] == 1
