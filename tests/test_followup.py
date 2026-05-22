"""Tests for the 🔔 followup tool."""

from __future__ import annotations

from datetime import date, timedelta


def test_add_followup(cli):
    data = cli.json("followup", "add", "Anna", "-d", "2026-12-01", "-r", "send proposal")
    assert data["person"] == "Anna"
    assert data["reason"] == "send proposal"


def test_overdue_status(cli):
    past = (date.today() - timedelta(days=3)).isoformat()
    data = cli.json("followup", "add", "Bob", "-d", past)
    assert data["status"] == "overdue"


def test_done_hides_from_list(cli):
    fu = cli.json("followup", "add", "Carol", "-d", "2026-12-01")
    cli.run("followup", "done", str(fu["id"]))
    assert cli.json("followup", "list") == []
    assert len(cli.json("followup", "list", "--all")) == 1


def test_snooze_pushes_due_date(cli):
    fu = cli.json("followup", "add", "Dave", "-d", "today")
    snoozed = cli.json("followup", "snooze", str(fu["id"]), "--days", "10")
    expected = (date.today() + timedelta(days=10)).isoformat()
    assert snoozed["due_date"] == expected


def test_due_includes_overdue(cli):
    past = (date.today() - timedelta(days=1)).isoformat()
    cli.run("followup", "add", "Soon", "-d", past)
    cli.run("followup", "add", "Far", "-d", "2027-01-01")
    due = cli.json("followup", "due", "--days", "7")
    assert len(due) == 1


def test_stats(cli):
    past = (date.today() - timedelta(days=1)).isoformat()
    cli.run("followup", "add", "X", "-d", past)
    stats = cli.json("followup", "stats")
    assert stats["pending"] == 1
    assert stats["overdue"] == 1
