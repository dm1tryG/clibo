"""Tests for the 📅 events tool."""

from __future__ import annotations

from datetime import date, timedelta


def test_add_event(cli):
    data = cli.json("events", "add", "Dentist", "-d", "2026-12-01", "-t", "09:00")
    assert data["title"] == "Dentist"
    assert data["event_date"] == "2026-12-01"
    assert data["event_time"] == "09:00"


def test_list_hides_past_by_default(cli):
    past = (date.today() - timedelta(days=5)).isoformat()
    cli.run("events", "add", "Old", "-d", past)
    cli.run("events", "add", "Future", "-d", "2027-01-01")
    events = cli.json("events", "list")
    assert len(events) == 1
    assert events[0]["title"] == "Future"
    assert len(cli.json("events", "list", "--all")) == 2


def test_today_filters_to_today(cli):
    cli.run("events", "add", "Now", "-d", "today")
    cli.run("events", "add", "Later", "-d", "2027-01-01")
    today = cli.json("events", "today")
    assert len(today["events"]) == 1
    assert today["events"][0]["title"] == "Now"


def test_upcoming_window(cli):
    soon = (date.today() + timedelta(days=3)).isoformat()
    far = (date.today() + timedelta(days=30)).isoformat()
    cli.run("events", "add", "Soon", "-d", soon)
    cli.run("events", "add", "Far", "-d", far)
    upcoming = cli.json("events", "upcoming", "--days", "7")
    assert len(upcoming) == 1


def test_edit_event(cli):
    event = cli.json("events", "add", "Meeting", "-d", "2026-12-01")
    edited = cli.json("events", "edit", str(event["id"]), "--title", "Standup")
    assert edited["title"] == "Standup"


def test_stats(cli):
    cli.run("events", "add", "Future", "-d", "2027-06-01")
    stats = cli.json("events", "stats")
    assert stats["total_events"] == 1
    assert stats["upcoming"] == 1


def test_list_filters_by_category(cli):
    cli.run("events", "add", "Dentist visit", "-d", "2027-06-01",
            "-c", "health")
    cli.run("events", "add", "Standup", "-d", "2027-06-02",
            "-c", "work")
    cli.run("events", "add", "Lunch with Anna", "-d", "2027-06-03",
            "-c", "social")
    only_health = cli.json("events", "list", "-c", "health")
    assert {e["title"] for e in only_health} == {"Dentist visit"}


def test_list_no_filter_returns_all_upcoming(cli):
    cli.run("events", "add", "A", "-d", "2027-06-01", "-c", "x")
    cli.run("events", "add", "B", "-d", "2027-06-02", "-c", "y")
    rows = cli.json("events", "list")
    assert len(rows) == 2
