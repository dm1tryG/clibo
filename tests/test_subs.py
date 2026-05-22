"""Tests for the 🔁 subs tool."""

from __future__ import annotations


def test_add_subscription(cli):
    data = cli.json("subs", "add", "Netflix", "-a", "12.99", "-c", "monthly")
    assert data["name"] == "Netflix"
    assert data["cycle"] == "monthly"
    assert data["monthly_cost"] == 12.99


def test_yearly_normalises_to_monthly(cli):
    data = cli.json("subs", "add", "Domain", "-a", "120", "-c", "yearly")
    assert data["monthly_cost"] == 10.0


def test_total_sums_active(cli):
    cli.run("subs", "add", "A", "-a", "10", "-c", "monthly")
    cli.run("subs", "add", "B", "-a", "120", "-c", "yearly")
    total = cli.json("subs", "total")
    assert total["monthly_cost"] == 20.0
    assert total["yearly_cost"] == 240.0


def test_cancel_excludes_from_list(cli):
    sub = cli.json("subs", "add", "Temp", "-a", "5")
    cli.run("subs", "cancel", str(sub["id"]))
    assert cli.json("subs", "list") == []
    assert len(cli.json("subs", "list", "--all")) == 1


def test_upcoming_filters_by_date(cli):
    cli.run("subs", "add", "Soon", "-a", "9", "--next", "today")
    upcoming = cli.json("subs", "upcoming", "--days", "7")
    assert len(upcoming) == 1
    assert upcoming[0]["name"] == "Soon"


def test_invalid_cycle_fails(cli):
    result = cli.run("subs", "add", "Bad", "-a", "5", "-c", "daily")
    assert result.exit_code != 0
