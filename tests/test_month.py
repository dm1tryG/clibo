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


# ── writing + reading-sessions on month (iter 94) ──


def test_month_includes_writing(cli):
    data = cli.json("month")
    assert "writing" in data["productivity"]
    assert data["productivity"]["writing"]["sessions"] == 0
    assert data["productivity"]["writing"]["total_words"] == 0


def test_month_writing_aggregates(cli):
    cli.run("writing", "log", "novel", "-w", "1200", "-t", "45")
    cli.run("writing", "log", "blog", "-w", "400", "-d", "5 days ago")
    data = cli.json("month")
    w = data["productivity"]["writing"]
    assert w["sessions"] == 2
    assert w["total_words"] == 1600
    assert w["days_written"] == 2
    assert w["avg_words_per_active_day"] == 800.0
    top = {p["category"]: p["amount"] for p in w["top_projects"]}
    assert top["novel"] == 1200
    assert top["blog"] == 400


def test_month_includes_reading(cli):
    data = cli.json("month")
    assert "reading" in data["hobbies"]
    assert data["hobbies"]["reading"]["sessions"] == 0
    assert data["hobbies"]["reading"]["books"] == []


def test_month_reading_sessions_aggregate(cli):
    cli.run("books", "add", "Atomic Habits", "-p", "320")
    cli.run("books", "read", "Atomic Habits", "30", "-t", "45")
    cli.run("books", "read", "Atomic Habits", "25", "-t", "30", "-d", "3 days ago")
    data = cli.json("month")
    r = data["hobbies"]["reading"]
    assert r["sessions"] == 2
    assert r["pages"] == 55
    assert r["minutes"] == 75
    assert r["days_read"] == 2
    assert r["books"] == ["Atomic Habits"]


# ── symptom block on month (iter 96) ──


def test_month_includes_symptoms_block(cli):
    data = cli.json("month")
    assert "symptoms" in data
    s = data["symptoms"]
    assert s["episodes"] == 0
    assert s["worst_intensity"] == 0


def test_month_symptoms_aggregates(cli):
    cli.run("symptom", "log", "back pain", "-i", "7")
    cli.run("symptom", "log", "back pain", "-i", "5", "-d", "2 days ago")
    cli.run("symptom", "log", "migraine", "-i", "9", "-d", "5 days ago")
    s = cli.json("month")["symptoms"]
    assert s["episodes"] == 3
    assert s["days_affected"] == 3
    assert s["worst_intensity"] == 9
    assert s["worst_name"] == "migraine"
