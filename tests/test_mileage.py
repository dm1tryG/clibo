"""Tests for the 🏃 mileage tool."""

from __future__ import annotations


def test_log_distance(cli):
    data = cli.json("mileage", "log", "5", "-a", "run", "-t", "30")
    assert data["distance_km"] == 5.0
    assert data["activity"] == "run"
    assert data["pace_min_per_km"] == 6.0


def test_log_walk_no_duration(cli):
    data = cli.json("mileage", "log", "2.5", "-a", "walk")
    assert data["distance_km"] == 2.5
    assert data["pace_min_per_km"] is None


def test_week_totals(cli):
    cli.run("mileage", "log", "5", "-a", "run")
    cli.run("mileage", "log", "3", "-a", "walk")
    cli.run("mileage", "goal", "--set", "20")
    week = cli.json("mileage", "week")
    assert week["total_km"] == 8.0
    assert week["sessions"] == 2
    assert week["by_activity"] == {"run": 5.0, "walk": 3.0}
    assert week["reached"] is False


def test_stats_pace(cli):
    cli.run("mileage", "log", "10", "-t", "60")
    cli.run("mileage", "log", "5", "-t", "30")
    stats = cli.json("mileage", "stats")
    assert stats["sessions"] == 2
    assert stats["total_km"] == 15.0
    assert stats["avg_pace_min_per_km"] == 6.0


def test_invalid_activity_fails(cli):
    result = cli.run("mileage", "log", "5", "-a", "flying")
    assert result.exit_code != 0


def test_negative_distance_fails(cli):
    result = cli.run("mileage", "log", "-1")
    assert result.exit_code != 0
