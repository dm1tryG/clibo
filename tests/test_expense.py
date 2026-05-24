"""Tests for the 💸 expense tool."""

from __future__ import annotations


def test_add_expense(cli):
    data = cli.json("expense", "add", "coffee", "-a", "4.5", "-c", "Food")
    assert data["amount"] == 4.5
    assert data["category"] == "food"
    assert data["description"] == "coffee"


def test_month_breakdown(cli):
    cli.run("expense", "add", "lunch", "-a", "12", "-c", "food")
    cli.run("expense", "add", "bus", "-a", "3", "-c", "transport")
    cli.run("expense", "add", "dinner", "-a", "20", "-c", "food")
    month = cli.json("expense", "month")
    assert month["total"] == 35.0
    food = next(r for r in month["by_category"] if r["category"] == "food")
    assert food["amount"] == 32.0


def test_currency_roundtrip(cli):
    cli.run("expense", "currency", "--set", "eur")
    assert cli.json("expense", "currency")["currency"] == "EUR"


def test_stats_top_categories(cli):
    cli.run("expense", "add", "rent", "-a", "800", "-c", "housing")
    cli.run("expense", "add", "snack", "-a", "5", "-c", "food")
    stats = cli.json("expense", "stats")
    assert stats["total"] == 805.0
    assert stats["top_categories"][0]["category"] == "housing"


def test_edit_and_remove(cli):
    entry = cli.json("expense", "add", "thing", "-a", "10")
    edited = cli.json("expense", "edit", str(entry["id"]), "-a", "15")
    assert edited["amount"] == 15.0
    removed = cli.json("expense", "rm", str(entry["id"]))
    assert removed["deleted"] == entry["id"]


def test_negative_amount_fails(cli):
    result = cli.run("expense", "add", "bad", "-a", "-5")
    assert result.exit_code != 0



# ── bare-command default (iter 107) ──


def test_bare_expense_runs_month(cli):
    """`clibo expense` (no subcommand) runs `month`."""
    result = cli.run("expense")
    assert result.exit_code == 0


def test_expense_help_still_works(cli):
    """`clibo expense --help` still shows the menu after the bare change."""
    result = cli.run("expense", "--help")
    assert result.exit_code == 0
    assert "month" in result.stdout
