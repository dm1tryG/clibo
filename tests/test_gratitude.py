"""Tests for the 🙏 gratitude tool."""

from __future__ import annotations


def test_add_entry(cli):
    data = cli.json("gratitude", "add", "morning coffee")
    assert data["text"] == "morning coffee"
    assert data["current_streak"] == 1


def test_today_lists_entries(cli):
    cli.run("gratitude", "add", "sunshine")
    cli.run("gratitude", "add", "good book")
    today = cli.json("gratitude", "today")
    assert len(today["entries"]) == 2
    assert today["current_streak"] == 1


def test_streak_builds(cli):
    cli.run("gratitude", "add", "yesterday thing", "-d", "yesterday")
    cli.run("gratitude", "add", "today thing")
    streak = cli.json("gratitude", "streak")
    assert streak["current_streak"] == 2
    assert streak["longest_streak"] == 2


def test_longest_streak_remembers(cli):
    # 3-day streak two weeks ago, then a 1-day break, then today
    cli.run("gratitude", "add", "a", "-d", "10 days ago")
    cli.run("gratitude", "add", "b", "-d", "9 days ago")
    cli.run("gratitude", "add", "c", "-d", "8 days ago")
    cli.run("gratitude", "add", "today entry")
    streak = cli.json("gratitude", "streak")
    assert streak["current_streak"] == 1
    assert streak["longest_streak"] == 3


def test_stats_avg_per_day(cli):
    cli.run("gratitude", "add", "one")
    cli.run("gratitude", "add", "two")
    cli.run("gratitude", "add", "three")
    stats = cli.json("gratitude", "stats")
    assert stats["entries"] == 3
    assert stats["days_practised"] == 1
    assert stats["avg_per_day"] == 3.0


def test_remove(cli):
    entry = cli.json("gratitude", "add", "temp")
    removed = cli.json("gratitude", "rm", str(entry["id"]))
    assert removed["deleted"] == entry["id"]



# ── bare-command default (iter 106) ──


def test_bare_gratitude_runs_today(cli):
    """`clibo gratitude` (no subcommand) runs `today`."""
    result = cli.run("gratitude")
    assert result.exit_code == 0


def test_gratitude_help_still_works(cli):
    """`clibo gratitude --help` still shows the menu after the bare change."""
    result = cli.run("gratitude", "--help")
    assert result.exit_code == 0
    assert "today" in result.stdout
