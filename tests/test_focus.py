"""Tests for the 🍅 focus tool."""

from __future__ import annotations


def test_log_session(cli):
    data = cli.json("focus", "log", "25", "-t", "deep work")
    assert data["minutes"] == 25
    assert data["task"] == "deep work"


def test_timer_json_skips_countdown(cli):
    data = cli.json("focus", "timer", "-m", "25", "-t", "writing")
    assert data["minutes"] == 25


def test_today_sums_minutes(cli):
    cli.run("focus", "log", "25")
    cli.run("focus", "log", "15")
    today = cli.json("focus", "today")
    assert today["total_minutes"] == 40
    assert today["sessions"] == 2


def test_goal_roundtrip(cli):
    cli.run("focus", "goal", "--set", "120")
    assert cli.json("focus", "goal")["daily_min"] == 120


def test_stats_window(cli):
    cli.run("focus", "log", "30")
    cli.run("focus", "log", "30")
    stats = cli.json("focus", "stats")
    assert stats["sessions"] == 2
    assert stats["total_minutes"] == 60
    assert stats["total_hours"] == 1.0


def test_negative_minutes_fails(cli):
    result = cli.run("focus", "log", "-5")
    assert result.exit_code != 0



# ── bare-command default (iter 106) ──


def test_bare_focus_runs_today(cli):
    """`clibo focus` (no subcommand) runs `today`."""
    result = cli.run("focus")
    assert result.exit_code == 0


def test_focus_help_still_works(cli):
    """`clibo focus --help` still shows the menu after the bare change."""
    result = cli.run("focus", "--help")
    assert result.exit_code == 0
    assert "today" in result.stdout
