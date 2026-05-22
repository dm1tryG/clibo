"""Tests for the 🍽️ meals tool."""

from __future__ import annotations


def test_plan_meal(cli):
    data = cli.json("meals", "plan", "today", "dinner", "Pasta carbonara")
    assert data["meal_type"] == "dinner"
    assert data["dish"] == "Pasta carbonara"


def test_today_lists_meals(cli):
    cli.run("meals", "plan", "today", "breakfast", "Oatmeal")
    cli.run("meals", "plan", "today", "dinner", "Stir fry")
    today = cli.json("meals", "today")
    assert len(today) == 2


def test_week_grid(cli):
    cli.run("meals", "plan", "today", "lunch", "Sandwich")
    week = cli.json("meals", "week")
    assert len(week["days"]) == 7
    assert any(d.get("lunch") == "Sandwich" for d in week["days"])


def test_clear_removes_day(cli):
    cli.run("meals", "plan", "today", "breakfast", "Eggs")
    cli.run("meals", "plan", "today", "lunch", "Soup")
    cleared = cli.json("meals", "clear", "today")
    assert cleared["cleared"] == 2
    assert cli.json("meals", "today") == []


def test_stats(cli):
    cli.run("meals", "plan", "today", "dinner", "A")
    cli.run("meals", "plan", "tomorrow", "dinner", "B")
    stats = cli.json("meals", "stats")
    assert stats["total_planned"] == 2
    assert stats["by_meal_type"]["dinner"] == 2


def test_invalid_meal_type_fails(cli):
    result = cli.run("meals", "plan", "today", "brunch", "Pancakes")
    assert result.exit_code != 0
