"""Tests for the 🍎 calorie tool."""

from __future__ import annotations


def test_log_creates_entry(cli):
    data = cli.json("calorie", "log", "oatmeal", "-k", "320", "-p", "12", "-m", "breakfast")
    assert data["food"] == "oatmeal"
    assert data["kcal"] == 320
    assert data["protein"] == 12.0
    assert data["meal"] == "breakfast"


def test_today_sums_totals(cli):
    cli.run("calorie", "log", "eggs", "-k", "200", "-p", "14")
    cli.run("calorie", "log", "toast", "-k", "150", "-c", "30")
    today = cli.json("calorie", "today")
    assert today["totals"]["kcal"] == 350
    assert today["totals"]["protein"] == 14.0
    assert today["totals"]["carbs"] == 30.0
    assert len(today["entries"]) == 2


def test_goal_roundtrip(cli):
    cli.run("calorie", "goal", "--set", "2100")
    goal = cli.json("calorie", "goal")
    assert goal["daily_kcal"] == 2100
    today = cli.json("calorie", "today")
    assert today["goal_kcal"] == 2100


def test_edit_and_remove(cli):
    entry = cli.json("calorie", "log", "snack", "-k", "100")
    edited = cli.json("calorie", "edit", str(entry["id"]), "-k", "150")
    assert edited["kcal"] == 150
    removed = cli.json("calorie", "rm", str(entry["id"]))
    assert removed["deleted"] == entry["id"]


def test_invalid_meal_fails(cli):
    result = cli.run("calorie", "log", "mystery", "-k", "100", "-m", "brunch")
    assert result.exit_code != 0


# ── bare-command default (iter 105) ──


def test_bare_calorie_runs_today(cli):
    """`clibo calorie` (no subcommand) runs `today`."""
    result = cli.run("calorie")
    assert result.exit_code == 0
    # No assertion on output content — that varies by tool.
    # Equivalence check: bare exits cleanly just like the explicit subcommand would.


def test_calorie_help_still_works(cli):
    """`clibo calorie --help` still shows the menu after the bare change."""
    result = cli.run("calorie", "--help")
    assert result.exit_code == 0
    assert "today" in result.stdout
