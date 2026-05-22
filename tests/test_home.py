"""Tests for the 🏠 home tool."""

from __future__ import annotations


def test_add_entry(cli):
    data = cli.json("home", "add", "Painted bedroom", "-k", "improvement", "-c", "200", "-l", "bedroom")
    assert data["title"] == "Painted bedroom"
    assert data["kind"] == "improvement"
    assert data["cost"] == 200.0


def test_list_filters_by_kind(cli):
    cli.run("home", "add", "Fixed leak", "-k", "repair", "-c", "150")
    cli.run("home", "add", "Painted walls", "-k", "improvement", "-c", "100")
    repairs = cli.json("home", "list", "-k", "repair")
    assert len(repairs) == 1
    assert repairs[0]["title"] == "Fixed leak"


def test_list_filters_by_location(cli):
    cli.run("home", "add", "Kitchen sink fix", "-l", "kitchen")
    cli.run("home", "add", "Bathroom tile", "-l", "bathroom")
    kitchen = cli.json("home", "list", "-l", "kitchen")
    assert len(kitchen) == 1


def test_stats_by_kind_and_location(cli):
    cli.run("home", "add", "A", "-k", "repair", "-c", "100", "-l", "kitchen")
    cli.run("home", "add", "B", "-k", "improvement", "-c", "300", "-l", "kitchen")
    cli.run("home", "add", "C", "-k", "repair", "-c", "50", "-l", "bathroom")
    stats = cli.json("home", "stats")
    assert stats["total_entries"] == 3
    assert stats["total_spent"] == 450.0
    assert stats["by_kind"]["repair"] == 150.0
    assert stats["by_location"]["kitchen"] == 400.0


def test_invalid_kind_fails(cli):
    result = cli.run("home", "add", "Bad", "-k", "renovation")
    assert result.exit_code != 0
