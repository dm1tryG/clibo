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


# ── add alias + bare-command default (iter 119) ──


def test_add_alias_works(cli):
    """`budget add` is the natural verb agents reach for first."""
    data = cli.json("budget", "add", "food", "200")
    assert data["category"] == "food"
    assert data["monthly_limit"] == 200


def test_add_alias_updates_existing(cli):
    """`budget add` on an existing category updates the limit (same as set)."""
    cli.json("budget", "add", "food", "200")
    updated = cli.json("budget", "add", "food", "350")
    assert updated["monthly_limit"] == 350


def test_set_and_add_produce_equivalent_rows(cli):
    """Both verbs write to the same Budget row — no duplicate."""
    cli.json("budget", "add", "food", "200")
    cli.json("budget", "set", "food", "250")
    listed = cli.json("budget", "list")["budgets"]
    food_rows = [b for b in listed if b["category"] == "food"]
    assert len(food_rows) == 1
    assert food_rows[0]["limit"] == 250


def test_add_rejects_zero(cli):
    """Validation flows through to the alias too."""
    result = cli.run("budget", "add", "food", "0")
    assert result.exit_code != 0


def test_bare_budget_runs_list(cli):
    """`clibo budget` (no subcommand) runs `list`."""
    cli.run("budget", "add", "food", "200")
    cli.run("expense", "add", "groceries", "-a", "85", "-c", "food")
    result = cli.run("budget")
    assert result.exit_code == 0
    # The list rendering shows the category and the limit
    assert "food" in result.stdout
    assert "200" in result.stdout


def test_bare_budget_empty_state(cli):
    """Bare `clibo budget` with no budgets — friendly empty-state, exit 0."""
    result = cli.run("budget")
    assert result.exit_code == 0
    assert "No budgets" in result.stdout
    assert "clibo budget add" in result.stdout


def test_budget_help_still_works(cli):
    """`clibo budget --help` still shows the menu, and lists both add and set."""
    result = cli.run("budget", "--help")
    assert result.exit_code == 0
    assert "set" in result.stdout
    assert "add" in result.stdout
