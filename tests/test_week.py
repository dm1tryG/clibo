"""Tests for ``clibo week`` and its collector."""

from __future__ import annotations

from datetime import date, timedelta


def test_week_empty(cli):
    data = cli.json("week")
    assert data["days"] == 7
    assert data["sleep"]["nights_logged"] == 0
    assert data["expenses"]["entries"] == 0
    assert data["tasks"]["completed"] == 0


def test_week_sleep_and_focus(cli):
    cli.run("sleep", "log", "7", "-q", "4", "-d", "yesterday")
    cli.run("sleep", "log", "8", "-q", "5", "-d", "today")
    cli.run("focus", "log", "25", "-t", "writing")
    cli.run("focus", "log", "40", "-t", "review")
    data = cli.json("week")
    assert data["sleep"]["nights_logged"] == 2
    assert data["sleep"]["avg_hours"] == 7.5
    assert data["focus"]["sessions"] == 2
    assert data["focus"]["total_minutes"] == 65


def test_week_habits_track_target(cli):
    cli.run("habit", "add", "Stretch", "-t", "3")
    cli.run("habit", "check", "Stretch", "-d", "today")
    cli.run("habit", "check", "Stretch", "-d", "yesterday")
    cli.run("habit", "check", "Stretch", "-d", "2 days ago" if False else (date.today() - timedelta(days=2)).isoformat())
    data = cli.json("week")
    assert data["habits"]["tracked"] == 1
    habit = data["habits"]["items"][0]
    assert habit["done"] == 3
    assert habit["hit_target"] is True


def test_week_expenses_top_category(cli):
    cli.run("expense", "add", "lunch", "-a", "12", "-c", "food")
    cli.run("expense", "add", "dinner", "-a", "20", "-c", "food")
    cli.run("expense", "add", "bus", "-a", "3", "-c", "transport")
    data = cli.json("week")
    assert data["expenses"]["entries"] == 3
    assert data["expenses"]["total"] == 35.0
    assert data["expenses"]["top_category"]["category"] == "food"
    assert data["expenses"]["top_category"]["amount"] == 32.0


def test_week_tasks_completed_counted(cli):
    cli.run("todo", "add", "Done thing")
    task = cli.json("todo", "list")[0]
    cli.run("todo", "done", str(task["id"]))
    cli.run("todo", "add", "Still pending")
    data = cli.json("week")
    assert data["tasks"]["completed"] == 1


def test_week_water_goal_reached(cli):
    cli.run("water", "goal", "--set", "2000")
    cli.run("water", "drink", "2500")
    data = cli.json("week")
    assert data["water"]["days_logged"] == 1
    assert data["water"]["days_goal_reached"] == 1
