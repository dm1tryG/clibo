"""Tests for the 🔥 habit tool."""

from __future__ import annotations


def test_add_habit(cli):
    data = cli.json("habit", "add", "Read 10 pages", "-t", "5")
    assert data["name"] == "Read 10 pages"
    assert data["target_per_week"] == 5
    assert data["current_streak"] == 0


def test_check_builds_streak(cli):
    cli.run("habit", "add", "Exercise")
    cli.run("habit", "check", "Exercise", "-d", "yesterday")
    data = cli.json("habit", "check", "Exercise", "-d", "today")
    assert data["current_streak"] == 2
    assert data["done_today"] is True


def test_check_is_idempotent(cli):
    cli.run("habit", "add", "Water")
    cli.run("habit", "check", "Water")
    data = cli.json("habit", "check", "Water")
    assert data["total_checks"] == 1


def test_uncheck_removes(cli):
    cli.run("habit", "add", "Meditate")
    cli.run("habit", "check", "Meditate")
    data = cli.json("habit", "uncheck", "Meditate")
    assert data["done_today"] is False
    assert data["total_checks"] == 0


def test_today_splits_done_pending(cli):
    cli.run("habit", "add", "A")
    cli.run("habit", "add", "B")
    cli.run("habit", "check", "A")
    today = cli.json("habit", "today")
    assert len(today["done"]) == 1
    assert len(today["pending"]) == 1


def test_stats_longest_streak(cli):
    cli.run("habit", "add", "Journal")
    cli.run("habit", "check", "Journal", "-d", "yesterday")
    cli.run("habit", "check", "Journal", "-d", "today")
    stats = cli.json("habit", "stats", "Journal")
    assert stats["longest_streak"] == 2


def test_invalid_target_fails(cli):
    result = cli.run("habit", "add", "Bad", "-t", "9")
    assert result.exit_code != 0
