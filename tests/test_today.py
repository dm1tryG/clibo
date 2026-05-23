"""Tests for ``clibo today`` and the dashboard collector."""

from __future__ import annotations

from datetime import date, timedelta


def test_today_empty_state(cli):
    data = cli.json("today")
    assert data["tasks"]["pending"] == 0
    assert data["habits"]["total"] == 0
    assert data["events"] == []
    assert data["bills"] == []


def test_today_aggregates_tasks(cli):
    past = (date.today() - timedelta(days=2)).isoformat()
    cli.run("todo", "add", "Overdue thing", "-d", past, "-p", "high")
    cli.run("todo", "add", "Today thing", "-d", "today")
    data = cli.json("today")
    assert data["tasks"]["pending"] == 2
    assert len(data["tasks"]["overdue"]) == 1
    assert data["tasks"]["overdue"][0]["title"] == "Overdue thing"
    assert len(data["tasks"]["due_today"]) == 1


def test_today_includes_water_and_habits(cli):
    cli.run("water", "drink", "500")
    cli.run("habit", "add", "Read")
    cli.run("habit", "check", "Read")
    data = cli.json("today")
    assert data["water"]["total_ml"] == 500
    assert data["habits"]["total"] == 1
    assert data["habits"]["done_today"] == 1


def test_today_bills_and_followups(cli):
    past = (date.today() - timedelta(days=1)).isoformat()
    cli.run("bills", "add", "Internet", "-d", past, "-a", "40")
    cli.run("followup", "add", "Anna", "-d", past)
    data = cli.json("today")
    assert any(b["overdue"] for b in data["bills"])
    assert any(f["overdue"] for f in data["followups"])


def test_today_birthdays(cli):
    today = date.today()
    cli.run("birthdays", "add", "Mom", "-d", f"{today.month:02d}-{today.day:02d}")
    data = cli.json("today")
    assert any(b["person"] == "Mom" for b in data["birthdays"])


def test_today_plants_and_chores(cli):
    cli.run("plants", "add", "Basil", "-w", "1")
    cli.run("chores", "add", "Dishes", "-e", "1")
    data = cli.json("today")
    assert any(p["name"] == "Basil" for p in data["plants_thirsty"])
    assert any(c["name"] == "Dishes" for c in data["chores_due"])
