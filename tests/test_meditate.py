"""Tests for the 🧘 meditate tool."""

from __future__ import annotations


def test_log_session(cli):
    data = cli.json("meditate", "log", "15", "-k", "Breathing")
    assert data["minutes"] == 15
    assert data["kind"] == "breathing"


def test_today_sums_minutes(cli):
    cli.run("meditate", "log", "10")
    cli.run("meditate", "log", "5")
    today = cli.json("meditate", "today")
    assert today["total_minutes"] == 15
    assert len(today["sessions"]) == 2


def test_goal_roundtrip(cli):
    cli.run("meditate", "goal", "--set", "20")
    assert cli.json("meditate", "goal")["daily_min"] == 20


def test_streak_counts_consecutive_days(cli):
    cli.run("meditate", "log", "10", "-d", "today")
    cli.run("meditate", "log", "10", "-d", "yesterday")
    streak = cli.json("meditate", "streak")
    assert streak["current_streak"] == 2


def test_stats_window(cli):
    cli.run("meditate", "log", "10")
    cli.run("meditate", "log", "20")
    stats = cli.json("meditate", "stats")
    assert stats["sessions"] == 2
    assert stats["total_minutes"] == 30
    assert stats["longest_session"] == 20


def test_negative_minutes_fails(cli):
    result = cli.run("meditate", "log", "-5")
    assert result.exit_code != 0
