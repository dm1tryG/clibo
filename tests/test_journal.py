"""Tests for the 📔 journal tool."""

from __future__ import annotations


def test_write_entry(cli):
    data = cli.json("journal", "write", "Today I shipped a feature", "-m", "4")
    assert data["body"] == "Today I shipped a feature"
    assert data["mood"] == 4


def test_today_lists_entries(cli):
    cli.run("journal", "write", "Morning thoughts")
    cli.run("journal", "write", "Evening reflection")
    today = cli.json("journal", "today")
    assert len(today["entries"]) == 2


def test_search_matches_body(cli):
    cli.run("journal", "write", "A great hike in the mountains")
    cli.run("journal", "write", "Quiet day at home")
    results = cli.json("journal", "search", "hike")
    assert len(results) == 1


def test_edit_updates_body(cli):
    entry = cli.json("journal", "write", "draft")
    edited = cli.json("journal", "edit", str(entry["id"]), "-b", "final")
    assert edited["body"] == "final"


def test_stats_streak(cli):
    cli.run("journal", "write", "yesterday entry", "-d", "yesterday")
    cli.run("journal", "write", "today entry", "-d", "today")
    stats = cli.json("journal", "stats")
    assert stats["days_journaled"] == 2
    assert stats["current_streak"] == 2


def test_invalid_mood_fails(cli):
    result = cli.run("journal", "write", "bad mood", "-m", "9")
    assert result.exit_code != 0
