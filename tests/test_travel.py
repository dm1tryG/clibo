"""Tests for the ✈️ travel tool."""

from __future__ import annotations


def test_add_trip(cli):
    data = cli.json("travel", "add", "Paris weekend", "-d", "Paris",
                    "--start", "2026-08-10", "--end", "2026-08-13", "-b", "1500")
    assert data["name"] == "Paris weekend"
    assert data["destination"] == "Paris"
    assert data["budget"] == 1500.0


def test_plan_itinerary(cli):
    cli.run("travel", "add", "Trip", "--start", "2026-08-10")
    data = cli.json("travel", "plan", "Trip", "2026-08-10", "Outbound flight",
                    "-t", "09:30", "-c", "flight", "--cost", "250")
    assert data["title"] == "Outbound flight"
    assert data["category"] == "flight"


def test_show_lists_events(cli):
    cli.run("travel", "add", "Roma")
    cli.run("travel", "plan", "Roma", "2026-09-01", "Colosseum tour")
    cli.run("travel", "plan", "Roma", "2026-09-01", "Pasta dinner",
            "-c", "food", "--cost", "40")
    detail = cli.json("travel", "show", "Roma")
    assert len(detail["itinerary"]) == 2
    assert detail["spent"] == 40.0


def test_budget_remaining(cli):
    cli.run("travel", "add", "Vacay", "-b", "1000")
    cli.run("travel", "plan", "Vacay", "2027-01-01", "Hotel",
            "-c", "hotel", "--cost", "400")
    detail = cli.json("travel", "show", "Vacay")
    assert detail["spent"] == 400.0
    assert detail["remaining"] == 600.0


def test_upcoming_filters(cli):
    cli.run("travel", "add", "Past trip", "--start", "2020-01-01")
    cli.run("travel", "add", "Future trip", "--start", "2027-01-01")
    upcoming = cli.json("travel", "upcoming")
    assert len(upcoming) == 1
    assert upcoming[0]["name"] == "Future trip"


def test_stats_counts_days(cli):
    cli.run("travel", "add", "Three days", "--start", "2026-08-10", "--end", "2026-08-12")
    stats = cli.json("travel", "stats")
    assert stats["trips"] == 1
    assert stats["days_traveled"] == 3
