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
