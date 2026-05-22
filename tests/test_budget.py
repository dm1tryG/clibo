"""Tests for the 📊 budget tool."""

from __future__ import annotations


def test_set_and_list(cli):
    cli.run("budget", "set", "food", "400")
    listing = cli.json("budget", "list")
    assert listing["budgets"][0]["category"] == "food"
    assert listing["budgets"][0]["limit"] == 400.0


def test_set_updates_existing(cli):
    cli.run("budget", "set", "food", "400")
    cli.run("budget", "set", "food", "500")
    listing = cli.json("budget", "list")
    assert len(listing["budgets"]) == 1
    assert listing["budgets"][0]["limit"] == 500.0


def test_tracks_spending_from_expenses(cli):
    cli.run("budget", "set", "food", "100")
    cli.run("expense", "add", "groceries", "-a", "60", "-c", "food")
    cli.run("expense", "add", "snack", "-a", "10", "-c", "food")
    row = cli.json("budget", "check", "food")
    assert row["spent"] == 70.0
    assert row["remaining"] == 30.0
    assert row["over_budget"] is False


def test_over_budget_flag(cli):
    cli.run("budget", "set", "fun", "20")
    cli.run("expense", "add", "movie", "-a", "30", "-c", "fun")
    status = cli.json("budget", "status")
    assert "fun" in status["over_budget_categories"]


def test_remove_budget(cli):
    cli.run("budget", "set", "travel", "1000")
    removed = cli.json("budget", "rm", "travel")
    assert removed["deleted"] == "travel"


def test_check_missing_fails(cli):
    result = cli.run("budget", "check", "nonexistent")
    assert result.exit_code != 0
