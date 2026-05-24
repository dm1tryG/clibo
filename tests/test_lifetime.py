"""Tests for ``clibo lifetime`` — all-time cross-tool aggregates."""

from __future__ import annotations

from datetime import date


def test_lifetime_empty_state(cli):
    data = cli.json("lifetime")
    assert data["earliest_log"] is None
    assert data["years_tracking"] == 0
    assert data["money"]["income_total"] == 0
    assert data["money"]["expense_total"] == 0


def test_lifetime_money_aggregates_across_years(cli):
    """Lifetime sums everything regardless of year."""
    cli.run("income", "add", "OldSalary", "-a", "5000", "-d", "2024-06-15")
    cli.run("income", "add", "NewSalary", "-a", "7000")
    cli.run("expense", "add", "OldRent", "-a", "1500", "-d", "2024-06-15")
    cli.run("expense", "add", "NewRent", "-a", "1700")
    data = cli.json("lifetime")
    assert data["money"]["income_total"] == 12000.0
    assert data["money"]["expense_total"] == 3200.0
    assert data["money"]["net_cash_flow"] == 8800.0


def test_lifetime_earliest_log_is_minimum(cli):
    """earliest_log picks the oldest date across all tables."""
    cli.run("income", "add", "Old", "-a", "100", "-d", "2024-06-15")
    cli.run("workout", "log", "run", "--duration", "30", "-d", "2023-03-10")
    cli.run("writing", "log", "novel", "-w", "500")
    data = cli.json("lifetime")
    assert data["earliest_log"] == "2023-03-10"
    # years_tracking computed from earliest_log → today
    assert data["years_tracking"] >= 1


def test_lifetime_books_finished(cli):
    cli.run("books", "add", "A", "-p", "300", "-s", "finished")
    cli.run("books", "add", "B", "-p", "200", "-s", "finished")
    cli.run("books", "add", "C", "-p", "150", "-s", "reading")
    data = cli.json("lifetime")
    h = data["hobbies"]
    assert h["books_finished"] == 2
    assert h["pages_read"] == 500


def test_lifetime_weight_range(cli):
    cli.run("weight", "log", "72", "-d", "2024-01-15")
    cli.run("weight", "log", "70", "-d", "2025-01-15")
    cli.run("weight", "log", "68")
    data = cli.json("lifetime")
    h = data["health"]
    assert h["weight_min"] == 68.0
    assert h["weight_max"] == 72.0
    assert h["weight_first"] == 72.0  # oldest entry
    assert h["weight_last"] == 68.0   # newest entry


def test_lifetime_health_aggregates(cli):
    cli.run("workout", "log", "run", "--duration", "30")
    cli.run("workout", "log", "lift", "--duration", "45", "-d", "yesterday")
    cli.run("meditate", "log", "10")
    cli.run("meditate", "log", "15", "-d", "yesterday")
    cli.run("sleep", "log", "7.5")
    cli.run("sleep", "log", "8", "-d", "yesterday")
    cli.run("mileage", "log", "5", "-a", "run")
    data = cli.json("lifetime")
    h = data["health"]
    assert h["workouts"] == 2
    assert h["workout_minutes"] == 75
    assert h["days_meditated"] == 2
    assert h["meditation_minutes"] == 25
    assert h["days_slept_logged"] == 2
    assert h["avg_sleep_hours"] == 7.75
    assert h["mileage_km"] == 5.0


def test_lifetime_productivity_aggregates(cli):
    cli.run("todo", "add", "T1")
    cli.run("todo", "done", "1")
    cli.run("focus", "log", "25")
    cli.run("focus", "log", "50")
    cli.run("journal", "write", "Entry")
    data = cli.json("lifetime")
    p = data["productivity"]
    assert p["tasks_done"] == 1
    assert p["focus_minutes"] == 75
    assert p["journal_entries"] == 1


def test_lifetime_writing_aggregates(cli):
    cli.run("writing", "log", "novel", "-w", "500")
    cli.run("writing", "log", "blog", "-w", "1500")
    data = cli.json("lifetime")
    h = data["hobbies"]
    assert h["writing_words"] == 2000
    assert h["writing_sessions"] == 2


def test_lifetime_human_view_runs_empty(cli):
    result = cli.run("lifetime")
    assert result.exit_code == 0
    assert "Nothing logged" in result.output


def test_lifetime_human_view_runs_populated(cli):
    cli.run("income", "add", "Salary", "-a", "5000")
    result = cli.run("lifetime")
    assert result.exit_code == 0
    assert "Lifetime" in result.output
    assert "Money" in result.output


def test_lifetime_years_tracking_for_today_only_logs(cli):
    """A single same-day log → years_tracking = 1, not 0."""
    cli.run("income", "add", "Today", "-a", "100")
    data = cli.json("lifetime")
    assert data["earliest_log"] == date.today().isoformat()
    assert data["years_tracking"] == 1
