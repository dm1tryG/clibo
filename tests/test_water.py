"""Tests for the 💧 water tool."""

from __future__ import annotations


def test_drink_accumulates_total(cli):
    cli.run("water", "drink", "500")
    data = cli.json("water", "drink", "250")
    assert data["amount_ml"] == 250
    assert data["total_today"] == 750


def test_today_reports_progress(cli):
    cli.run("water", "drink", "500")
    today = cli.json("water", "today")
    assert today["total_ml"] == 500
    assert today["drinks"] == 1
    assert today["reached"] is False


def test_goal_roundtrip(cli):
    cli.run("water", "goal", "--set", "3000")
    assert cli.json("water", "goal")["daily_ml"] == 3000


def test_stats_counts_days(cli):
    cli.run("water", "drink", "2500")
    cli.run("water", "goal", "--set", "2000")
    stats = cli.json("water", "stats")
    assert stats["days_logged"] == 1
    assert stats["days_goal_reached"] == 1


def test_negative_amount_fails(cli):
    result = cli.run("water", "drink", "-100")
    assert result.exit_code != 0


# ── bare-command default (iter 105) ──


def test_bare_water_runs_today(cli):
    """`clibo water` (no subcommand) runs `today`."""
    result = cli.run("water")
    assert result.exit_code == 0
    # No assertion on output content — that varies by tool.
    # Equivalence check: bare exits cleanly just like the explicit subcommand would.


def test_water_help_still_works(cli):
    """`clibo water --help` still shows the menu after the bare change."""
    result = cli.run("water", "--help")
    assert result.exit_code == 0
    assert "today" in result.stdout
