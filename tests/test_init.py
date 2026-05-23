"""Tests for ``clibo init`` — the onboarding-defaults command."""

from __future__ import annotations


def test_init_with_no_flags_shows_current_defaults(cli):
    data = cli.json("init")
    assert data["updated"] == {}
    # currency falls back to USD via expense; the rest are unset until init.
    assert "currency" in data["current"]


def test_init_sets_currency_uppercased(cli):
    data = cli.json("init", "--currency", "eur")
    assert data["updated"] == {"currency": "EUR"}
    assert data["current"]["currency"] == "EUR"


def test_init_sets_calorie_and_water_goals(cli):
    data = cli.json(
        "init",
        "--calorie-goal", "2200",
        "--water-goal-ml", "2500",
    )
    assert data["updated"]["calorie_goal"] == 2200
    assert data["updated"]["water_goal_ml"] == 2500
    # And the underlying tools see the new goals immediately.
    assert cli.json("calorie", "goal")["daily_kcal"] == 2200
    assert cli.json("water", "goal")["daily_ml"] == 2500


def test_init_sets_height_for_bmi(cli):
    cli.run("init", "--height-cm", "178")
    cli.run("weight", "log", "75")
    data = cli.json("weight", "stats")
    assert "bmi" in data
    assert 23 < data["bmi"] < 24


def test_init_rejects_negative(cli):
    result = cli.run("init", "--calorie-goal", "-10")
    assert result.exit_code != 0


def test_init_partial_update_preserves_others(cli):
    cli.run("init", "--calorie-goal", "2000", "--water-goal-ml", "2000")
    cli.run("init", "--focus-goal-min", "120")  # don't touch the first two
    state = cli.json("init")["current"]
    assert state["calorie_goal"] == "2000"
    assert state["water_goal_ml"] == "2000"
    assert state["focus_goal_min"] == "120"
