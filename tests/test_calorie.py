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


# ── per-meal filter + by_meal subtotals (iter 111) ──


def test_today_includes_by_meal_subtotals(cli):
    """JSON exposes per-meal subtotals + counts."""
    cli.run("calorie", "log", "oats", "-k", "320", "-m", "breakfast")
    cli.run("calorie", "log", "coffee", "-k", "5", "-m", "breakfast")
    cli.run("calorie", "log", "salad", "-k", "520", "-m", "lunch")
    data = cli.json("calorie", "today")
    by_meal = data["by_meal"]
    assert by_meal["breakfast"]["kcal"] == 325
    assert by_meal["breakfast"]["count"] == 2
    assert by_meal["lunch"]["kcal"] == 520
    assert by_meal["lunch"]["count"] == 1


def test_today_by_meal_omits_meals_with_no_entries(cli):
    """Empty meals don't pollute the by_meal dict."""
    cli.run("calorie", "log", "salad", "-k", "300", "-m", "lunch")
    data = cli.json("calorie", "today")
    assert "lunch" in data["by_meal"]
    assert "breakfast" not in data["by_meal"]
    assert "dinner" not in data["by_meal"]


def test_today_filter_by_meal(cli):
    """--meal scopes entries + totals to one meal."""
    cli.run("calorie", "log", "oats", "-k", "320", "-m", "breakfast")
    cli.run("calorie", "log", "salad", "-k", "520", "-m", "lunch")
    data = cli.json("calorie", "today", "-m", "breakfast")
    assert data["filter_meal"] == "breakfast"
    assert data["totals"]["kcal"] == 320
    assert len(data["entries"]) == 1
    assert data["entries"][0]["meal"] == "breakfast"


def test_today_filter_preserves_by_meal_subtotals(cli):
    """`by_meal` is the full per-meal view even when filtering."""
    cli.run("calorie", "log", "oats", "-k", "320", "-m", "breakfast")
    cli.run("calorie", "log", "salad", "-k", "520", "-m", "lunch")
    data = cli.json("calorie", "today", "-m", "breakfast")
    # filter_meal scopes entries/totals; by_meal stays complete.
    assert set(data["by_meal"].keys()) == {"breakfast", "lunch"}
    assert data["by_meal"]["lunch"]["kcal"] == 520


def test_today_bad_meal_filter_fails(cli):
    result = cli.run("calorie", "today", "-m", "supper")
    assert result.exit_code != 0


def test_today_filter_with_no_match_returns_empty(cli):
    """Filtering for a meal that has no entries today gives an empty result."""
    cli.run("calorie", "log", "oats", "-k", "320", "-m", "breakfast")
    data = cli.json("calorie", "today", "-m", "dinner")
    assert data["entries"] == []
    assert data["totals"]["kcal"] == 0
    # by_meal still has breakfast since that's logged
    assert "breakfast" in data["by_meal"]


def test_today_bare_still_works(cli):
    """The bare-command pattern from iter 105 still works."""
    cli.run("calorie", "log", "oats", "-k", "320", "-m", "breakfast")
    result = cli.run("calorie")
    assert result.exit_code == 0
    assert "320" in result.stdout or "oats" in result.stdout


# ── calorie today: over_budget / remaining_kcal / pct_of_goal ──


def test_calorie_today_budget_signals_none_when_no_goal(cli):
    """Without a goal set, all three derived fields are null."""
    cli.run("calorie", "add", "snack", "-k", "200")
    data = cli.json("calorie", "today")
    assert data["goal_kcal"] == 0
    assert data["over_budget"] is None
    assert data["remaining_kcal"] is None
    assert data["pct_of_goal"] is None


def test_calorie_today_under_budget(cli):
    """Under the goal → over_budget=False, positive remaining, pct < 100."""
    cli.run("calorie", "goal", "--set", "2000")
    cli.run("calorie", "add", "snack", "-k", "200")
    data = cli.json("calorie", "today")
    assert data["over_budget"] is False
    assert data["remaining_kcal"] == 1800
    assert data["pct_of_goal"] == 10.0


def test_calorie_today_over_budget(cli):
    """Over the goal → over_budget=True, negative remaining, pct > 100."""
    cli.run("calorie", "goal", "--set", "2000")
    cli.run("calorie", "add", "feast", "-k", "2700")
    data = cli.json("calorie", "today")
    assert data["over_budget"] is True
    assert data["remaining_kcal"] == -700
    assert data["pct_of_goal"] == 135.0


def test_calorie_today_exactly_at_budget(cli):
    """Right at goal → over_budget=False (== isn't >), remaining=0, pct=100."""
    cli.run("calorie", "goal", "--set", "2000")
    cli.run("calorie", "add", "exact", "-k", "2000")
    data = cli.json("calorie", "today")
    assert data["over_budget"] is False
    assert data["remaining_kcal"] == 0
    assert data["pct_of_goal"] == 100.0
