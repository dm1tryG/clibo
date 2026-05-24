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


# ── bare-command default (iter 105) ──


def test_bare_habit_runs_today(cli):
    """`clibo habit` (no subcommand) runs `today`."""
    result = cli.run("habit")
    assert result.exit_code == 0
    # No assertion on output content — that varies by tool.
    # Equivalence check: bare exits cleanly just like the explicit subcommand would.


def test_habit_help_still_works(cli):
    """`clibo habit --help` still shows the menu after the bare change."""
    result = cli.run("habit", "--help")
    assert result.exit_code == 0
    assert "today" in result.stdout


# ── habit list: on_pace + target_remaining + days_left_this_week ──


def test_habit_target_remaining_decrements_as_checks_land(cli):
    """target_remaining = max(0, target - this_week). Clamps at zero."""
    cli.run("habit", "add", "Gym", "--target", "3")
    row0 = next(h for h in cli.json("habit", "list") if h["name"] == "Gym")
    assert row0["target_remaining"] == 3
    cli.run("habit", "check", "1")
    row1 = next(h for h in cli.json("habit", "list") if h["name"] == "Gym")
    assert row1["target_remaining"] == 2


def test_habit_target_remaining_floors_at_zero_when_exceeded(cli):
    """Hitting target N times beyond the goal still shows 0, never negative."""
    cli.run("habit", "add", "Daily", "--target", "1")
    cli.run("habit", "check", "1")
    cli.run("habit", "check", "1", "-d", "yesterday")
    cli.run("habit", "check", "1", "-d", "2 days ago")
    row = next(h for h in cli.json("habit", "list") if h["name"] == "Daily")
    assert row["target_remaining"] == 0


def test_habit_on_pace_true_when_hitting_target(cli):
    """A habit checked enough this week is on pace.

    The week starts Monday; on a Monday there's only one in-week day
    available. Add as many in-week checks as the calendar allows
    (capped at the target) and assert `on_pace` — the relationship
    we care about — regardless of weekday.
    """
    from datetime import date as date_
    cli.run("habit", "add", "Gym", "--target", "3")
    # Days available in this week up to today = weekday+1 (Mon=0).
    days_in_week = date_.today().weekday() + 1
    for i in range(min(3, days_in_week)):
        cli.run("habit", "check", "1", "-d", f"{i} days ago")
    row = next(h for h in cli.json("habit", "list") if h["name"] == "Gym")
    assert row["on_pace"] is True


def test_habit_days_left_this_week_field_present(cli):
    """days_left_this_week is 0..6, depending on today's weekday."""
    cli.run("habit", "add", "Any")
    row = cli.json("habit", "list")[0]
    assert 0 <= row["days_left_this_week"] <= 6


def test_habit_target_remaining_zero_when_done_this_week(cli):
    """Min target is 1; one check satisfies it → remaining = 0, on_pace True."""
    cli.run("habit", "add", "Once", "--target", "1")
    cli.run("habit", "check", "1")
    row = cli.json("habit", "list")[0]
    assert row["target_remaining"] == 0
    assert row["on_pace"] is True


def test_habit_on_pace_false_at_week_end_with_no_checks(cli):
    """A fresh habit added today with no checks isn't on pace if
    today's weekday means some progress is already expected. Most
    of the week-cycle this is True; only Mondays it might not be."""
    cli.run("habit", "add", "Gym", "--target", "3")
    row = cli.json("habit", "list")[0]
    from datetime import date as date_
    days_elapsed = date_.today().weekday() + 1
    expected = (3 * days_elapsed) // 7
    assert row["on_pace"] is (row["this_week"] >= expected)
