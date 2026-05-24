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



# ── bare-command default (iter 106) ──


def test_bare_mileage_runs_week(cli):
    """`clibo mileage` (no subcommand) runs `week`."""
    result = cli.run("mileage")
    assert result.exit_code == 0


def test_mileage_help_still_works(cli):
    """`clibo mileage --help` still shows the menu after the bare change."""
    result = cli.run("mileage", "--help")
    assert result.exit_code == 0
    assert "week" in result.stdout


# ── streak subcommand (iter 113) ──


def test_mileage_streak_empty(cli):
    data = cli.json("mileage", "streak")
    assert data["current_streak"] == 0
    assert data["longest_streak"] == 0
    assert data["days_logged"] == 0


def test_mileage_streak_consecutive(cli):
    cli.run("mileage", "log", "5", "-a", "run")
    cli.run("mileage", "log", "3", "-a", "walk", "-d", "yesterday")
    cli.run("mileage", "log", "8", "-a", "cycle", "-d", "2 days ago")
    data = cli.json("mileage", "streak")
    assert data["current_streak"] == 3
    assert data["longest_streak"] == 3
    assert data["days_logged"] == 3


def test_mileage_streak_breaks_with_gap(cli):
    cli.run("mileage", "log", "5")
    cli.run("mileage", "log", "5", "-d", "3 days ago")
    cli.run("mileage", "log", "5", "-d", "4 days ago")
    data = cli.json("mileage", "streak")
    assert data["current_streak"] == 1
    assert data["longest_streak"] == 2


# ── mileage stats: best_pace ──


def test_mileage_stats_best_pace_picks_fastest_session(cli):
    """The session with the lowest min/km wins, not the longest."""
    cli.run("mileage", "log", "5", "-a", "run", "-t", "30")    # 6.0 min/km
    cli.run("mileage", "log", "10", "-a", "run", "-t", "50")   # 5.0 min/km (faster)
    cli.run("mileage", "log", "3", "-a", "run", "-t", "21")    # 7.0 min/km
    data = cli.json("mileage", "stats")
    assert data["best_pace_min_per_km"] == 5.0
    # And the surfacing session points at the right entry.
    best = data["best_pace_session"]
    assert best["distance_km"] == 10.0
    assert best["duration_min"] == 50
    assert best["pace_min_per_km"] == 5.0


def test_mileage_stats_best_pace_ignores_sessions_without_duration(cli):
    """Walks/sessions missing duration_min don't have a pace — skip them."""
    cli.run("mileage", "log", "5", "-a", "walk")                # no duration
    cli.run("mileage", "log", "10", "-a", "run", "-t", "60")    # 6.0 min/km
    data = cli.json("mileage", "stats")
    assert data["best_pace_min_per_km"] == 6.0
    assert data["best_pace_session"]["activity"] == "run"


def test_mileage_stats_best_pace_null_when_no_pace_data(cli):
    """All sessions lack duration → best_pace fields are null."""
    cli.run("mileage", "log", "5")
    cli.run("mileage", "log", "3")
    data = cli.json("mileage", "stats")
    assert data["best_pace_min_per_km"] is None
    assert data["best_pace_session"] is None


def test_mileage_stats_best_and_avg_can_differ(cli):
    """Avg pace is the average; best_pace is the fastest single session."""
    cli.run("mileage", "log", "5", "-a", "run", "-t", "30")   # 6.0
    cli.run("mileage", "log", "5", "-a", "run", "-t", "40")   # 8.0
    data = cli.json("mileage", "stats")
    assert data["best_pace_min_per_km"] == 6.0
    assert data["avg_pace_min_per_km"] == 7.0
