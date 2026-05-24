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


# ── focus stats: best_session + best_day ──


def test_focus_stats_best_session_picks_longest(cli):
    """best_session is the longest single block; best_day sums same-date."""
    cli.run("focus", "log", "25", "-t", "code")
    cli.run("focus", "log", "60", "-t", "writing")
    cli.run("focus", "log", "25")
    data = cli.json("focus", "stats")
    assert data["best_session"]["minutes"] == 60
    assert data["best_session"]["task"] == "writing"
    # All three sessions are today → best_day sums them.
    assert data["best_day"]["minutes"] == 25 + 60 + 25


def test_focus_stats_best_day_is_largest_total(cli):
    """When sessions span multiple days, best_day picks the biggest sum."""
    cli.run("focus", "log", "30", "-d", "yesterday")
    cli.run("focus", "log", "40", "-d", "yesterday")
    cli.run("focus", "log", "60")
    data = cli.json("focus", "stats")
    # Yesterday: 70 total. Today: 60. Yesterday wins on best_day.
    assert data["best_day"]["minutes"] == 70
    # But the longest individual session is today's 60.
    assert data["best_session"]["minutes"] == 60


# ── focus today: remaining_minutes + pct_of_goal ──


def test_focus_today_remaining_and_pct(cli):
    cli.run("focus", "log", "25")
    data = cli.json("focus", "today")
    assert data["total_minutes"] == 25
    assert data["goal_minutes"] == 100
    assert data["remaining_minutes"] == 75
    assert data["pct_of_goal"] == 25.0
    assert data["reached"] is False


def test_focus_today_remaining_floors_at_zero_when_reached(cli):
    cli.run("focus", "log", "120")
    data = cli.json("focus", "today")
    assert data["remaining_minutes"] == 0
    assert data["reached"] is True
    assert data["pct_of_goal"] == 120.0


# ── focus log accepts H:MM notation ──


def test_focus_log_accepts_hh_mm(cli):
    """`focus log 1:25` → 85 minutes."""
    data = cli.json("focus", "log", "1:25")
    assert data["minutes"] == 85


def test_focus_log_plain_int_still_works(cli):
    data = cli.json("focus", "log", "45")
    assert data["minutes"] == 45


def test_focus_log_default_pomodoro_with_no_arg(cli):
    """Omitting the arg uses the default pomodoro length (25)."""
    data = cli.json("focus", "log")
    assert data["minutes"] == 25


def test_focus_log_bad_hh_mm_fails(cli):
    result = cli.run("focus", "log", "1:bad")
    assert result.exit_code != 0


def test_focus_log_bad_input_fails(cli):
    result = cli.run("focus", "log", "lots")
    assert result.exit_code != 0


def test_focus_log_hh_mm_two_hours(cli):
    data = cli.json("focus", "log", "2:00")
    assert data["minutes"] == 120
