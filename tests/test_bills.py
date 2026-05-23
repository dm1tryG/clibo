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


# ── name-resolution on pay/unpay/show/edit/rm (iter 85) ──


def test_bills_show_by_name(cli):
    cli.run("bills", "add", "Electricity", "-d", "2026-06-01", "-a", "80")
    data = cli.json("bills", "show", "Electricity")
    assert data["name"] == "Electricity"
    assert data["amount"] == 80.0


def test_bills_pay_by_name(cli):
    cli.run("bills", "add", "Electricity", "-d", "2026-06-01", "-a", "80")
    paid = cli.json("bills", "pay", "Electricity")
    assert paid["paid"] is True


def test_bills_pay_prefers_unpaid_when_multiple(cli):
    """Monthly recurring bill with same name — pay should land on the unpaid one."""
    paid = cli.json("bills", "add", "Electricity",
                    "-d", "2026-04-01", "-a", "75")
    cli.run("bills", "pay", str(paid["id"]))  # April already paid
    unpaid = cli.json("bills", "add", "Electricity",
                      "-d", "2026-05-01", "-a", "80")
    res = cli.json("bills", "pay", "Electricity")
    assert res["id"] == unpaid["id"]
    assert res["paid"] is True


def test_bills_unpay_by_name(cli):
    bill = cli.json("bills", "add", "Water", "-d", "2026-06-01", "-a", "30")
    cli.run("bills", "pay", str(bill["id"]))
    out = cli.json("bills", "unpay", "Water")
    assert out["paid"] is False


def test_bills_edit_by_name(cli):
    cli.run("bills", "add", "Electricity", "-d", "2026-06-01", "-a", "80")
    edited = cli.json("bills", "edit", "Electricity", "-a", "92")
    assert edited["amount"] == 92.0


def test_bills_rm_by_name(cli):
    cli.run("bills", "add", "Gas", "-d", "2026-06-01", "-a", "40")
    cli.json("bills", "rm", "Gas")
    listing = cli.json("bills", "list", "--all")
    assert not any(b["name"] == "Gas" for b in listing)


def test_bills_unknown_name_fails(cli):
    result = cli.run("bills", "show", "ghost")
    assert result.exit_code != 0
