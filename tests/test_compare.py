"""Tests for `clibo compare` — week-over-week diff view."""

from __future__ import annotations


def test_compare_empty(cli):
    """No data → all rows have None/0 values, zero rows visible."""
    data = cli.json("compare")
    assert "current" in data and "prior" in data
    assert isinstance(data["rows"], list)
    # All rows present (we always return them); but every value is 0 or None.
    for row in data["rows"]:
        # Every row is either both-empty or non-zero on the displayed side.
        assert "label" in row
        assert "delta_pct" in row


def test_compare_steps_better_when_higher_this_week(cli):
    # Seed prior week (8 days ago) low; this week high.
    cli.run("steps", "log", "5000", "-d", "8 days ago")
    cli.run("steps", "log", "9000", "-d", "yesterday")
    data = cli.json("compare")
    steps = next(r for r in data["rows"] if r["label"] == "Steps total")
    assert steps["current"] == 9000
    assert steps["prior"] == 5000
    assert steps["direction"] == "better"


def test_compare_caffeine_worse_when_higher_this_week(cli):
    # Caffeine: less is better (polarity = -1).
    cli.run("caffeine", "log", "espresso", "-d", "8 days ago")     # 63
    cli.run("caffeine", "log", "cold-brew", "-d", "yesterday")     # 200
    data = cli.json("compare")
    caf = next(r for r in data["rows"] if r["label"] == "Caffeine mg")
    assert caf["current"] == 200
    assert caf["prior"] == 63
    assert caf["direction"] == "worse"


def test_compare_expenses_worse_when_higher(cli):
    cli.run("expense", "add", "lunch", "-a", "10", "-d", "8 days ago")
    cli.run("expense", "add", "dinner", "-a", "50", "-d", "yesterday")
    data = cli.json("compare")
    exp = next(r for r in data["rows"] if r["label"] == "Expenses total")
    assert exp["direction"] == "worse"


def test_compare_donations_better_when_higher(cli):
    cli.run("donations", "log", "Red Cross", "-a", "10", "-d", "8 days ago")
    cli.run("donations", "log", "MSF", "-a", "100", "-d", "yesterday")
    data = cli.json("compare")
    don = next(r for r in data["rows"] if r["label"] == "Donations total")
    assert don["direction"] == "better"


def test_compare_neutral_when_equal(cli):
    cli.run("mood", "log", "4", "-d", "8 days ago")
    cli.run("mood", "log", "4", "-d", "yesterday")
    data = cli.json("compare")
    mood = next(r for r in data["rows"] if r["label"] == "Mood avg")
    assert mood["current"] == mood["prior"]
    assert mood["direction"] == "neutral"


def test_compare_n_a_when_one_side_empty(cli):
    """No prior-week sleep → direction is 'n/a'."""
    cli.run("sleep", "log", "7.5", "-d", "yesterday")
    data = cli.json("compare")
    sleep = next(r for r in data["rows"] if r["label"] == "Sleep avg")
    assert sleep["current"] == 7.5
    assert sleep["prior"] is None
    assert sleep["direction"] == "n/a"


def test_compare_delta_pct(cli):
    cli.run("steps", "log", "5000", "-d", "8 days ago")
    cli.run("steps", "log", "10000", "-d", "yesterday")
    data = cli.json("compare")
    steps = next(r for r in data["rows"] if r["label"] == "Steps total")
    # Delta pct from 5000 → 10000 is +100%.
    assert steps["delta_pct"] == 100.0


# ──────────────────────────────────────────────────────────────────────
# `clibo compare --month` (iter 80)
# ──────────────────────────────────────────────────────────────────────


def test_compare_month_default_is_current_vs_previous(cli):
    """No args → this calendar month vs the previous one."""
    data = cli.json("compare", "--month")
    assert "current" in data and "prior" in data
    assert data["current"]["month"] != data["prior"]["month"] or \
           data["current"]["year"] != data["prior"]["year"]


def test_compare_month_arbitrary_pair(cli):
    """`-y -m` selects any calendar month and compares vs its predecessor."""
    cli.run("expense", "add", "april stuff", "-a", "100", "-d", "2025-04-15")
    cli.run("expense", "add", "may stuff", "-a", "200", "-d", "2025-05-15")
    data = cli.json("compare", "--month", "-y", "2025", "-m", "5")
    assert data["current"]["month"] == 5
    assert data["prior"]["month"] == 4
    exp = next(r for r in data["rows"] if r["label"] == "Expenses")
    assert exp["current"] == 200.0
    assert exp["prior"] == 100.0
    assert exp["direction"] == "worse"  # expenses up = worse


def test_compare_month_january_wraps_to_december(cli):
    """January's previous month is December of the year before."""
    data = cli.json("compare", "--month", "-y", "2026", "-m", "1")
    assert data["prior"]["year"] == 2025
    assert data["prior"]["month"] == 12


def test_compare_month_donations_better_when_higher(cli):
    cli.run("donations", "log", "Red Cross", "-a", "20",
            "-d", "2025-04-15")
    cli.run("donations", "log", "MSF", "-a", "100",
            "-d", "2025-05-15")
    data = cli.json("compare", "--month", "-y", "2025", "-m", "5")
    don = next(r for r in data["rows"] if r["label"] == "Donations")
    assert don["direction"] == "better"


# ── year-over-year compare (compare --year-mode) ──


def test_compare_year_mode_defaults_to_current_vs_previous(cli):
    from datetime import date
    data = cli.json("compare", "--year-mode")
    assert data["current"]["year"] == date.today().year
    assert data["prior"]["year"] == date.today().year - 1


def test_compare_year_mode_arbitrary_year(cli):
    """Anchor year picks any past pair (e.g. 2023 vs 2022)."""
    data = cli.json("compare", "--year-mode", "-y", "2023")
    assert data["current"]["year"] == 2023
    assert data["prior"]["year"] == 2022


def test_compare_year_money_aggregates(cli):
    cli.run("income", "add", "Old", "-a", "1000", "-d", "2025-06-15")
    cli.run("income", "add", "New", "-a", "5000", "-d", "2026-06-15")
    cli.run("expense", "add", "Old", "-a", "300", "-d", "2025-06-15")
    cli.run("expense", "add", "New", "-a", "500", "-d", "2026-06-15")
    data = cli.json("compare", "--year-mode", "-y", "2026")
    income_row = next(r for r in data["rows"] if r["label"] == "Income")
    assert income_row["current"] == 5000.0
    assert income_row["prior"] == 1000.0
    assert income_row["direction"] == "better"  # higher income is better


def test_compare_year_expenses_worse_when_higher(cli):
    """Expenses going up year-on-year is `worse`."""
    cli.run("expense", "add", "Old", "-a", "300", "-d", "2025-06-15")
    cli.run("expense", "add", "New", "-a", "1500", "-d", "2026-06-15")
    data = cli.json("compare", "--year-mode", "-y", "2026")
    expenses = next(r for r in data["rows"] if r["label"] == "Expenses")
    assert expenses["direction"] == "worse"


def test_compare_year_books_finished(cli):
    """Backdate one book's `finished` to last year via SQL — `books add`
    only sets it to today."""
    cli.run("books", "add", "Old", "-p", "200", "-s", "finished")
    cli.run("books", "add", "New A", "-p", "100", "-s", "finished")
    cli.run("books", "add", "New B", "-p", "150", "-s", "finished")
    import os
    import sqlite3
    from datetime import date
    last_year = date(date.today().year - 1, 8, 1).isoformat()
    con = sqlite3.connect(f"{os.environ['CLIBO_HOME']}/clibo.db")
    con.execute(
        "UPDATE books_book SET finished=? WHERE title='Old'",
        (last_year,),
    )
    con.commit()
    con.close()
    data = cli.json("compare", "--year-mode")
    books = next(r for r in data["rows"] if r["label"] == "Books finished")
    assert books["current"] == 2
    assert books["prior"] == 1
    assert books["direction"] == "better"


def test_compare_year_delta_pct(cli):
    cli.run("income", "add", "Old", "-a", "1000", "-d", "2025-06-15")
    cli.run("income", "add", "New", "-a", "2000", "-d", "2026-06-15")
    data = cli.json("compare", "--year-mode", "-y", "2026")
    income = next(r for r in data["rows"] if r["label"] == "Income")
    # 100% increase over 1000 → delta_pct = 100.0
    assert income["delta_pct"] == 100.0


def test_compare_year_empty_renders_nothing_logged(cli):
    """No data in either year → human view shouldn't crash."""
    result = cli.run("compare", "--year-mode", "-y", "1999")
    assert result.exit_code == 0


def test_compare_year_mode_human_view_runs(cli):
    cli.run("income", "add", "Salary", "-a", "5000")
    result = cli.run("compare", "--year-mode")
    assert result.exit_code == 0
    # Both year labels appear in the header
    from datetime import date
    assert str(date.today().year) in result.output
    assert str(date.today().year - 1) in result.output
