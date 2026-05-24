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


# ── expense year + stats.by_year (iter 122) ──


def test_expense_year_current(cli):
    cli.run("expense", "add", "rent", "-a", "1500", "-c", "housing")
    cli.run("expense", "add", "groceries", "-a", "200", "-c", "food")
    data = cli.json("expense", "year")
    from datetime import date
    assert data["year"] == date.today().year
    assert data["total"] == 1700
    assert data["expenses"] == 2
    by_cat = {r["category"]: r["amount"] for r in data["by_category"]}
    assert by_cat["housing"] == 1500
    assert by_cat["food"] == 200


def test_expense_year_specific(cli):
    """`expense year -y 2025` filters by year."""
    cli.run("expense", "add", "rent", "-a", "1500", "-c", "housing")
    cli.run("expense", "add", "vacation", "-a", "3000", "-c", "travel")
    # Backdate one
    import sqlite3

    from clibo.core import config
    db = sqlite3.connect(str(config.db_path()))
    db.execute("UPDATE expense_entry SET entry_date='2025-08-15' WHERE description='vacation'")
    db.commit()
    db.close()
    data = cli.json("expense", "year", "-y", "2025")
    assert data["year"] == 2025
    assert data["total"] == 3000
    assert data["expenses"] == 1


def test_expense_year_biggest_month_and_expense(cli):
    cli.run("expense", "add", "small", "-a", "10", "-c", "food")
    cli.run("expense", "add", "huge", "-a", "5000", "-c", "travel")
    data = cli.json("expense", "year")
    assert data["biggest_expense"]["description"] == "huge"
    assert data["biggest_expense"]["amount"] == 5000
    assert data["biggest_month"]["amount"] == 5010


def test_expense_year_by_month_has_12(cli):
    """`by_month` has all 12 months, zeroed where empty."""
    cli.run("expense", "add", "rent", "-a", "1500", "-c", "housing")
    data = cli.json("expense", "year")
    assert len(data["by_month"]) == 12
    assert {m["month"] for m in data["by_month"]} == set(range(1, 13))


def test_expense_stats_includes_by_year(cli):
    cli.run("expense", "add", "rent", "-a", "1500", "-c", "housing")
    data = cli.json("expense", "stats")
    assert "by_year" in data
    from datetime import date
    assert data["by_year"][0]["year"] == date.today().year
    assert data["by_year"][0]["total"] == 1500
