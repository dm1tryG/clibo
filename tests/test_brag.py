"""Tests for the 🏆 brag tool."""

from __future__ import annotations


def test_add_achievement(cli):
    data = cli.json("brag", "add", "Shipped the new API", "-i", "Cut latency 40%")
    assert data["title"] == "Shipped the new API"
    assert data["impact"] == "Cut latency 40%"


def test_list_recent(cli):
    cli.run("brag", "add", "Win one")
    cli.run("brag", "add", "Win two")
    achievements = cli.json("brag", "list")
    assert len(achievements) == 2


def test_search_matches_impact(cli):
    cli.run("brag", "add", "Project A", "-i", "saved the company money")
    cli.run("brag", "add", "Project B", "-i", "improved morale")
    results = cli.json("brag", "search", "money")
    assert len(results) == 1


def test_since_filters_by_date(cli):
    cli.run("brag", "add", "Old win", "-d", "2026-01-01")
    cli.run("brag", "add", "Recent win", "-d", "2026-05-01")
    result = cli.json("brag", "since", "2026-03-01")
    assert result["count"] == 1
    assert result["achievements"][0]["title"] == "Recent win"


def test_stats(cli):
    cli.run("brag", "add", "A", "-c", "work")
    cli.run("brag", "add", "B", "-c", "learning")
    stats = cli.json("brag", "stats")
    assert stats["total"] == 2
    assert stats["by_category"]["work"] == 1
