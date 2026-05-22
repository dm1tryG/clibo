"""Tests for the 🧾 bills tool."""

from __future__ import annotations

from datetime import date, timedelta


def test_add_bill(cli):
    data = cli.json("bills", "add", "Rent", "-d", "2026-12-01", "-a", "900")
    assert data["name"] == "Rent"
    assert data["amount"] == 900.0
    assert data["due_date"] == "2026-12-01"


def test_overdue_status(cli):
    past = (date.today() - timedelta(days=5)).isoformat()
    data = cli.json("bills", "add", "Late", "-d", past, "-a", "50")
    assert data["status"] == "overdue"


def test_pay_marks_paid(cli):
    bill = cli.json("bills", "add", "Water", "-d", "2026-12-15", "-a", "30")
    paid = cli.json("bills", "pay", str(bill["id"]))
    assert paid["paid"] is True
    assert cli.json("bills", "list") == []
    assert len(cli.json("bills", "list", "--all")) == 1


def test_due_includes_overdue(cli):
    past = (date.today() - timedelta(days=2)).isoformat()
    cli.run("bills", "add", "Old", "-d", past, "-a", "10")
    cli.run("bills", "add", "Far", "-d", "2027-01-01", "-a", "10")
    due = cli.json("bills", "due", "--days", "7")
    assert len(due) == 1
    assert due[0]["name"] == "Old"


def test_stats_counts_overdue(cli):
    past = (date.today() - timedelta(days=1)).isoformat()
    cli.run("bills", "add", "Overdue", "-d", past, "-a", "100")
    stats = cli.json("bills", "stats")
    assert stats["unpaid"] == 1
    assert stats["overdue"] == 1
    assert stats["overdue_amount"] == 100.0
