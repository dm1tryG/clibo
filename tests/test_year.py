"""Tests for ``clibo year`` — calendar-year cross-tool rollup."""

from __future__ import annotations

from datetime import date


def test_year_empty_state(cli):
    data = cli.json("year")
    assert data["year"] == date.today().year
    assert data["money"]["income_total"] == 0
    assert data["money"]["expense_total"] == 0
    assert data["money"]["net_cash_flow"] == 0
    assert data["productivity"]["tasks_done"] == 0


def test_year_money_aggregates(cli):
    cli.run("income", "add", "Salary", "-a", "5000")
    cli.run("income", "add", "Bonus", "-a", "1000")
    cli.run("expense", "add", "Rent", "-a", "1500")
    cli.run("expense", "add", "Food", "-a", "300")
    cli.run("donations", "log", "Charity", "-a", "100")
    data = cli.json("year")
    assert data["money"]["income_total"] == 6000.0
    assert data["money"]["expense_total"] == 1800.0
    assert data["money"]["donations_total"] == 100.0
    # net = income - expenses - donations
    assert data["money"]["net_cash_flow"] == 4100.0


def test_year_productivity_aggregates(cli):
    cli.run("todo", "add", "T1")
    cli.run("todo", "add", "T2")
    cli.run("todo", "done", "1")
    cli.run("focus", "log", "25")
    cli.run("focus", "log", "50")
    cli.run("journal", "write", "Entry one")
    cli.run("journal", "write", "Entry two", "-d", "yesterday")
    data = cli.json("year")
    assert data["productivity"]["tasks_done"] == 1
    assert data["productivity"]["focus_minutes"] == 75
    assert data["productivity"]["journal_entries"] == 2
    assert data["productivity"]["days_journaled"] == 2


def test_year_hobbies_aggregates(cli):
    cli.run("books", "add", "Book A", "-p", "300", "-s", "finished")
    cli.run("books", "add", "Book B", "-p", "200", "-s", "finished")
    cli.run("films", "add", "Film X")
    cli.run("films", "watched", "Film X")
    cli.run("writing", "log", "novel", "-w", "1500")
    data = cli.json("year")
    h = data["hobbies"]
    assert h["books_finished"] == 2
    assert h["pages_read"] == 500
    assert h["films_watched"] == 1
    assert h["writing_words"] == 1500
    assert h["writing_sessions"] == 1


def test_year_health_aggregates(cli):
    cli.run("workout", "log", "running", "--duration", "30")
    cli.run("workout", "log", "lifting", "--duration", "45")
    cli.run("meditate", "log", "10")
    cli.run("meditate", "log", "15", "-d", "yesterday")
    cli.run("sleep", "log", "7.5")
    cli.run("sleep", "log", "8", "-d", "yesterday")
    cli.run("mileage", "log", "5", "-a", "run")
    data = cli.json("year")
    h = data["health"]
    assert h["workouts"] == 2
    assert h["workout_minutes"] == 75
    assert h["days_meditated"] == 2
    assert h["meditation_minutes"] == 25
    assert h["days_slept_logged"] == 2
    assert h["avg_sleep_hours"] == 7.75
    assert h["mileage_km"] == 5.0


def test_year_weight_change(cli):
    cli.run("weight", "log", "70", "-d", "2026-01-15")
    cli.run("weight", "log", "68", "-d", "2026-05-15")
    data = cli.json("year", "--year", "2026")
    assert data["health"]["weight_first"] == 70.0
    assert data["health"]["weight_last"] == 68.0
    assert data["health"]["weight_change_kg"] == -2.0


def test_year_specific_year_filters(cli):
    cli.run("income", "add", "Salary", "-a", "1000")
    # Backdate one row to last year via SQL.
    import os
    import sqlite3
    home = os.environ["CLIBO_HOME"]
    cli.run("income", "add", "OldSalary", "-a", "9999")
    con = sqlite3.connect(f"{home}/clibo.db")
    con.execute(
        "UPDATE income_entry SET entry_date='2020-06-01' "
        "WHERE source='OldSalary'"
    )
    con.commit()
    con.close()
    data_2020 = cli.json("year", "--year", "2020")
    assert data_2020["money"]["income_total"] == 9999.0


def test_year_biggest_expense_month(cli):
    """The month with the largest spending is surfaced as a 1-12 integer."""
    cli.run("expense", "add", "Big", "-a", "5000", "-d", "2026-08-15")
    cli.run("expense", "add", "Small", "-a", "100", "-d", "2026-03-15")
    data = cli.json("year", "--year", "2026")
    assert data["money"]["biggest_expense_month"] == 8


def test_year_human_view_runs(cli):
    cli.run("income", "add", "Salary", "-a", "5000")
    result = cli.run("year")
    assert result.exit_code == 0
    assert str(date.today().year) in result.output
    assert "Money" in result.output


def test_year_empty_human_view_says_nothing_logged(cli):
    result = cli.run("year", "--year", "1999")
    assert result.exit_code == 0
    assert "Nothing logged" in result.output
