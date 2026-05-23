"""Tests for the 🗓️ month rollup view."""

from __future__ import annotations

from datetime import date


def _this_month() -> tuple[int, int]:
    today = date.today()
    return today.year, today.month


def test_month_empty(cli):
    yr, mo = _this_month()
    data = cli.json("month")
    assert data["year"] == yr
    assert data["month"] == mo
    assert data["money"]["expenses"]["entries"] == 0
    assert data["money"]["income"]["entries"] == 0


def test_month_money_block(cli):
    cli.run("income", "add", "salary", "-a", "3000")
    cli.run("expense", "add", "rent", "-a", "1200", "-c", "housing")
    cli.run("expense", "add", "groceries", "-a", "200", "-c", "food")
    cli.run("donations", "log", "Red Cross", "-a", "50")
    data = cli.json("month")
    m = data["money"]
    assert m["income"]["total"] == 3000.0
    assert m["expenses"]["total"] == 1400.0
    assert m["donations"]["total"] == 50.0
    # Top expense category is rent (housing).
    assert m["expenses"]["top_category"] is not None
    assert m["expenses"]["top_category"][0] == "housing"


def test_month_net_cash_flow(cli):
    cli.run("income", "add", "salary", "-a", "3000")
    cli.run("expense", "add", "rent", "-a", "1200")
    data = cli.json("month")
    # 3000 income − 1200 expense − 0 donations − 0 bills = 1800
    assert data["money"]["net_cash_flow"] == 1800.0


def test_month_health_aggregates(cli):
    cli.run("steps", "log", "8500")
    cli.run("workout", "log", "running", "-t", "30", "-c", "350")
    cli.run("caffeine", "log", "espresso")
    cli.run("sleep", "log", "7.5")
    data = cli.json("month")
    assert data["steps"]["total"] == 8500
    assert data["workouts"]["sessions"] == 1
    assert data["caffeine"]["total_mg"] == 63
    assert data["sleep"]["avg_hours"] == 7.5


def test_month_productivity(cli):
    cli.run("focus", "log", "25")
    cli.run("journal", "write", "today's note")
    cli.run("gratitude", "add", "coffee")
    cli.run("todo", "add", "X")
    cli.run("todo", "done", "1")
    data = cli.json("month")
    p = data["productivity"]
    assert p["focus"]["total_minutes"] == 25
    assert p["journal_entries"] == 1
    assert p["gratitude_entries"] == 1
    assert p["tasks_completed"] == 1


def test_month_invest_transactions(cli):
    cli.run("invest", "buy", "AAPL", "5", "200")
    cli.run("invest", "buy", "BTC", "0.5", "40000", "-k", "crypto")
    data = cli.json("month")
    assert data["money"]["invest"]["transactions"] == 2
    assert data["money"]["invest"]["buys_total"] == 1000.0 + 20000.0


def test_month_specific_year_month(cli):
    """`--year` and `--month` let you look at past months."""
    # Seed expenses in two different months.
    cli.run("expense", "add", "may1", "-a", "10", "-d", "2025-05-15")
    cli.run("expense", "add", "jun1", "-a", "20", "-d", "2025-06-15")
    may = cli.json("month", "-y", "2025", "-m", "5")
    june = cli.json("month", "-y", "2025", "-m", "6")
    assert may["money"]["expenses"]["total"] == 10.0
    assert june["money"]["expenses"]["total"] == 20.0


def test_month_invalid_month(cli):
    result = cli.run("month", "-m", "13")
    assert result.exit_code != 0


def test_month_books_finished(cli):
    cli.run("books", "add", "Sapiens", "-a", "Harari", "-p", "100")
    cli.run("books", "read", "Sapiens", "100")  # finishes it
    data = cli.json("month")
    titles = {b["title"] for b in data["hobbies"]["books_finished"]}
    assert "Sapiens" in titles


def test_month_days_count(cli):
    """31-day months should report 31 days."""
    data = cli.json("month", "-y", "2025", "-m", "1")  # January 2025
    assert data["days"] == 31
    feb = cli.json("month", "-y", "2025", "-m", "2")
    assert feb["days"] == 28  # 2025 is not a leap year
    leap_feb = cli.json("month", "-y", "2024", "-m", "2")
    assert leap_feb["days"] == 29
