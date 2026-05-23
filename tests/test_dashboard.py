"""Tests for ``clibo dashboard`` — customizable widget dashboard."""

from __future__ import annotations


def test_default_widgets(cli):
    data = cli.json("dashboard")
    names = {w["name"] for w in data["widgets"]}
    # The default set includes at least these three.
    assert {"tasks", "habits", "water"} <= names


def test_widget_data_populates(cli):
    cli.run("todo", "add", "Ship it", "-p", "high", "-d", "today")
    cli.run("water", "drink", "500")
    data = cli.json("dashboard")
    by = {w["name"]: w for w in data["widgets"]}
    assert by["tasks"]["data"]["pending"] == 1
    assert by["water"]["data"]["total_ml"] == 500


def test_add_remove_widget(cli):
    cli.run("dashboard", "add", "sleep")
    after_add = cli.json("dashboard")
    assert any(w["name"] == "sleep" for w in after_add["widgets"])
    cli.run("dashboard", "remove", "sleep")
    after_remove = cli.json("dashboard")
    assert not any(w["name"] == "sleep" for w in after_remove["widgets"])


def test_add_unknown_widget_fails(cli):
    result = cli.run("dashboard", "add", "nonsense")
    assert result.exit_code != 0


def test_remove_not_active_fails(cli):
    # `mileage` is registered but not in the default set.
    result = cli.run("dashboard", "remove", "mileage")
    assert result.exit_code != 0


def test_clear_and_reset(cli):
    cli.run("dashboard", "clear")
    cleared = cli.json("dashboard")
    assert cleared["widgets"] == []
    cli.run("dashboard", "reset")
    reset_data = cli.json("dashboard")
    names = {w["name"] for w in reset_data["widgets"]}
    assert "tasks" in names


def test_list_marks_active(cli):
    rows = cli.json("dashboard", "list")
    by = {r["name"]: r for r in rows}
    assert by["tasks"]["active"] is True
    assert by["sleep"]["active"] is False
