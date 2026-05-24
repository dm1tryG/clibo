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


# ── name resolution by person (iter 82) ──


def test_followup_done_by_person_name(cli):
    cli.run("followup", "add", "Alice", "--due", "in 3 days")
    cli.run("followup", "done", "Alice")
    listing = cli.json("followup", "list", "--all")  # include done
    alice = next(f for f in listing if f["person"] == "Alice")
    assert alice["done"] is True


def test_followup_done_prefers_pending(cli):
    """Done resolves to the first pending follow-up for that person."""
    cli.run("followup", "add", "Alice", "--due", "in 3 days")
    cli.run("followup", "done", "Alice")
    cli.run("followup", "add", "Alice", "--due", "in 7 days")
    cli.run("followup", "done", "Alice")
    listing = cli.json("followup", "list", "--all")
    alices = [f for f in listing if f["person"] == "Alice"]
    assert len(alices) == 2
    assert all(f["done"] for f in alices)


def test_followup_snooze_by_name(cli):
    cli.run("followup", "add", "Bob", "--due", "in 3 days")
    cli.run("followup", "snooze", "Bob", "--days", "14")
    listing = cli.json("followup", "list")
    bob = next(f for f in listing if f["person"] == "Bob")
    assert bob["due_date"]  # populated


def test_followup_rm_by_name(cli):
    cli.run("followup", "add", "Bob", "--due", "in 3 days")
    cli.run("followup", "rm", "Bob")
    listing = cli.json("followup", "list", "--all")
    assert not any(f["person"] == "Bob" for f in listing)



# ── bare-command default (iter 110) ──


def test_bare_followup_runs_due(cli):
    """`clibo followup` (no subcommand) runs `due`."""
    result = cli.run("followup")
    assert result.exit_code == 0


def test_followup_help_still_works(cli):
    """`clibo followup --help` still shows the menu after the bare change."""
    result = cli.run("followup", "--help")
    assert result.exit_code == 0
    assert "due" in result.stdout
