"""Tests for the 😴 sleep tool."""

from __future__ import annotations


def test_log_records_sleep(cli):
    data = cli.json("sleep", "log", "7.5", "-q", "4")
    assert data["hours"] == 7.5
    assert data["quality"] == 4
    assert data["quality_label"] == "good"


def test_last_returns_most_recent(cli):
    cli.run("sleep", "log", "6", "-d", "yesterday")
    cli.run("sleep", "log", "8", "-d", "today")
    last = cli.json("sleep", "last")
    assert last["hours"] == 8


def test_goal_roundtrip(cli):
    cli.run("sleep", "goal", "--set", "9")
    assert cli.json("sleep", "goal")["goal_hours"] == 9.0


def test_stats_averages(cli):
    cli.run("sleep", "log", "6", "-q", "2", "-d", "yesterday")
    cli.run("sleep", "log", "8", "-q", "4", "-d", "today")
    stats = cli.json("sleep", "stats")
    assert stats["nights_logged"] == 2
    assert stats["avg_hours"] == 7.0
    assert stats["avg_quality"] == 3.0


def test_invalid_quality_fails(cli):
    result = cli.run("sleep", "log", "7", "-q", "9")
    assert result.exit_code != 0
