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


# ── streak shape upgrade (iter 113) ──


def test_meditate_streak_includes_longest(cli):
    """The upgraded streak shape now exposes longest_streak (was missing)."""
    cli.run("meditate", "log", "15")
    cli.run("meditate", "log", "10", "-d", "yesterday")
    data = cli.json("meditate", "streak")
    assert data["current_streak"] == 2
    assert data["longest_streak"] == 2
    # days_practiced kept for back-compat; days_logged is the new uniform name.
    assert data["days_practiced"] == 2
    assert data["days_logged"] == 2


# ── meditate stats: longest_session_entry (full reference) ──


def test_meditate_stats_longest_session_entry(cli):
    """longest_session_entry surfaces the actual entry behind the scalar."""
    cli.run("meditate", "log", "10", "-k", "mindfulness")
    cli.run("meditate", "log", "25", "-k", "guided")
    stats = cli.json("meditate", "stats")
    # Back-compat scalar still works.
    assert stats["longest_session"] == 25
    # New dict points at the actual entry.
    entry = stats["longest_session_entry"]
    assert entry["id"] == 2
    assert entry["minutes"] == 25
    assert entry["kind"] == "guided"
