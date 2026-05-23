"""Tests for the 🏋️ workout tool."""

from __future__ import annotations


def test_log_strength_computes_volume(cli):
    data = cli.json("workout", "log", "squat", "-s", "5", "-r", "5", "-w", "80")
    assert data["exercise"] == "squat"
    assert data["volume_kg"] == 2000.0


def test_today_aggregates(cli):
    cli.run("workout", "log", "bench", "-s", "3", "-r", "10", "-w", "60")
    cli.run("workout", "log", "run", "-t", "25")
    today = cli.json("workout", "today")
    assert len(today["exercises"]) == 2
    assert today["total_minutes"] == 25
    assert today["total_volume_kg"] == 1800.0


def test_stats_lists_top_exercises(cli):
    cli.run("workout", "log", "squat", "-s", "5", "-r", "5", "-w", "80")
    cli.run("workout", "log", "squat", "-s", "5", "-r", "5", "-w", "85")
    cli.run("workout", "log", "deadlift", "-s", "1", "-r", "5", "-w", "100")
    stats = cli.json("workout", "stats")
    assert stats["exercises_logged"] == 3
    assert stats["top_exercises"][0]["exercise"] == "squat"
    assert stats["top_exercises"][0]["count"] == 2


def test_remove(cli):
    entry = cli.json("workout", "log", "plank", "-t", "2")
    removed = cli.json("workout", "rm", str(entry["id"]))
    assert removed["deleted"] == entry["id"]


def test_log_calories_burned(cli):
    """The new --calories flag captures kcal burned in this session."""
    data = cli.json("workout", "log", "jogging", "-t", "30", "-c", "350")
    assert data["duration_min"] == 30
    assert data["kcal_burned"] == 350


def test_log_without_calories_leaves_field_null(cli):
    data = cli.json("workout", "log", "squat", "-s", "5", "-r", "5", "-w", "80")
    assert data["kcal_burned"] is None


def test_log_calories_can_be_zero(cli):
    data = cli.json("workout", "log", "rest pose", "-c", "0")
    assert data["kcal_burned"] == 0


def test_log_rejects_negative_calories(cli):
    result = cli.run("workout", "log", "jogging", "-t", "30", "-c", "-50")
    assert result.exit_code != 0


def test_today_totals_kcal(cli):
    cli.run("workout", "log", "jogging", "-t", "30", "-c", "350")
    cli.run("workout", "log", "cycling", "-t", "45", "-c", "400")
    cli.run("workout", "log", "squat", "-s", "5", "-r", "5", "-w", "80")
    today = cli.json("workout", "today")
    assert today["total_kcal"] == 750
    assert today["total_minutes"] == 75
    # the squat session contributes 0 kcal (no flag passed)
    by_ex = {r["exercise"]: r["kcal_burned"] for r in today["exercises"]}
    assert by_ex["squat"] is None


def test_stats_includes_kcal_total(cli):
    cli.run("workout", "log", "jogging", "-t", "30", "-c", "300")
    cli.run("workout", "log", "running", "-t", "20", "-c", "250")
    stats = cli.json("workout", "stats")
    assert stats["total_kcal_burned"] == 550
