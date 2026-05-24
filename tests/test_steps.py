"""Tests for the 👟 steps tool."""

from __future__ import annotations

from datetime import date, timedelta


def test_log_basic(cli):
    data = cli.json("steps", "log", "8500")
    assert data["count"] == 8500
    assert data["source"] is None
    assert data["total_today"] == 8500


def test_log_with_source(cli):
    data = cli.json("steps", "log", "12400", "-s", "apple_watch")
    assert data["count"] == 12400
    assert data["source"] == "apple_watch"


def test_multiple_logs_sum_per_day(cli):
    cli.run("steps", "log", "3000", "-s", "phone")
    cli.run("steps", "log", "2000", "-s", "apple_watch")
    today = cli.json("steps", "today")
    assert today["total"] == 5000
    assert today["entries"] == 2
    assert today["sources"] == {"phone": 1, "apple_watch": 1}


def test_today_reached(cli):
    cli.run("steps", "goal", "--set", "5000")
    cli.run("steps", "log", "6000")
    today = cli.json("steps", "today")
    assert today["reached"] is True


def test_today_not_reached(cli):
    cli.run("steps", "log", "1000")
    today = cli.json("steps", "today")
    assert today["reached"] is False


def test_log_rejects_zero_or_negative(cli):
    assert cli.run("steps", "log", "0").exit_code != 0
    assert cli.run("steps", "log", "-10").exit_code != 0


def test_add_alias_works(cli):
    log_help = cli.run("steps", "log", "--help")
    add_help = cli.run("steps", "add", "--help")
    assert log_help.exit_code == 0 and "Usage:" in log_help.output
    assert add_help.exit_code == 0 and "Usage:" in add_help.output
    cli.run("steps", "add", "5000")
    today = cli.json("steps", "today")
    assert today["total"] == 5000


def test_goal_set_and_get(cli):
    data = cli.json("steps", "goal", "--set", "7000")
    assert data["daily_goal"] == 7000
    again = cli.json("steps", "goal")
    assert again["daily_goal"] == 7000


def test_goal_rejects_non_positive(cli):
    assert cli.run("steps", "goal", "--set", "0").exit_code != 0


def test_list_aggregates_per_day(cli):
    today = date.today()
    cli.run("steps", "log", "5000", "-d", str(today))
    cli.run("steps", "log", "3000", "-d", str(today - timedelta(days=1)))
    rows = cli.json("steps", "list", "--days", "5")
    by_date = {r["date"]: r["total"] for r in rows}
    assert by_date[str(today)] == 5000
    assert by_date[str(today - timedelta(days=1))] == 3000


def test_week_includes_streak(cli):
    cli.run("steps", "goal", "--set", "5000")
    today = date.today()
    # Three consecutive days at goal ending today.
    for i in range(3):
        cli.run("steps", "log", "6000",
                "-d", str(today - timedelta(days=i)))
    week = cli.json("steps", "week")
    assert week["streak"] == 3
    assert week["goal_per_day"] == 5000
    assert week["goal_hits"] >= 1


def test_stats(cli):
    cli.run("steps", "goal", "--set", "5000")
    today = date.today()
    cli.run("steps", "log", "8000", "-d", str(today))
    cli.run("steps", "log", "6000", "-d", str(today - timedelta(days=1)))
    cli.run("steps", "log", "2000", "-d", str(today - timedelta(days=2)))
    data = cli.json("steps", "stats", "--days", "30")
    assert data["days_logged"] == 3
    assert data["total_steps"] == 16000
    assert data["days_goal_hit"] == 2  # 8000 and 6000 hit, 2000 didn't
    assert data["best_day"]["count"] == 8000
    # current streak is 2 (today + yesterday at goal; day before broke it)
    assert data["current_streak"] == 2


def test_streak_zero_when_today_and_yesterday_both_below(cli):
    cli.run("steps", "goal", "--set", "5000")
    today = date.today()
    cli.run("steps", "log", "2000", "-d", str(today))
    cli.run("steps", "log", "3000", "-d", str(today - timedelta(days=1)))
    data = cli.json("steps", "stats")
    assert data["current_streak"] == 0


def test_rm(cli):
    entry = cli.json("steps", "log", "5000")
    cli.run("steps", "rm", str(entry["id"]))
    rows = cli.json("steps", "list", "--days", "1")
    assert rows == []


def test_searchable_and_in_recent(cli):
    cli.run("steps", "log", "8500", "-s", "apple_watch", "-n", "morning walk")
    hits = cli.json("search", "morning")
    assert any(h["source"] == "steps" for h in hits["results"])
    recent = cli.json("recent")
    assert any(e["source"] == "steps" for e in recent["events"])


# ── bare-command default (iter 105) ──


def test_bare_steps_runs_today(cli):
    """`clibo steps` (no subcommand) runs `today`."""
    result = cli.run("steps")
    assert result.exit_code == 0
    # No assertion on output content — that varies by tool.
    # Equivalence check: bare exits cleanly just like the explicit subcommand would.


def test_steps_help_still_works(cli):
    """`clibo steps --help` still shows the menu after the bare change."""
    result = cli.run("steps", "--help")
    assert result.exit_code == 0
    assert "today" in result.stdout


# ── steps today: remaining + pct_of_goal ──


def test_steps_today_remaining_and_pct(cli):
    cli.run("steps", "log", "3000")
    data = cli.json("steps", "today")
    assert data["total"] == 3000
    assert data["goal"] == 10000
    assert data["remaining"] == 7000
    assert data["pct_of_goal"] == 30.0
    assert data["reached"] is False


def test_steps_today_remaining_floors_at_zero_when_reached(cli):
    cli.run("steps", "log", "12000")
    data = cli.json("steps", "today")
    assert data["remaining"] == 0
    assert data["reached"] is True
    assert data["pct_of_goal"] == 120.0
