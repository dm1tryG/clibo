"""Tests for the 💵 income tool."""

from __future__ import annotations


def test_add_income(cli):
    data = cli.json("income", "add", "freelance gig", "-a", "500", "-c", "freelance")
    assert data["amount"] == 500.0
    assert data["source"] == "freelance gig"
    assert data["category"] == "freelance"


def test_month_breakdown(cli):
    cli.run("income", "add", "ACME salary", "-a", "3000", "-c", "salary")
    cli.run("income", "add", "side gig", "-a", "500", "-c", "freelance")
    cli.run("income", "add", "another gig", "-a", "200", "-c", "freelance")
    month = cli.json("income", "month")
    assert month["total"] == 3700.0
    salary = next(r for r in month["by_category"] if r["category"] == "salary")
    assert salary["amount"] == 3000.0
    freelance = next(r for r in month["by_category"] if r["category"] == "freelance")
    assert freelance["amount"] == 700.0


def test_stats_top_categories(cli):
    cli.run("income", "add", "Big Corp", "-a", "5000", "-c", "salary")
    cli.run("income", "add", "Gift from mom", "-a", "100", "-c", "gift")
    stats = cli.json("income", "stats")
    assert stats["total"] == 5100.0
    assert stats["biggest"] == 5000.0
    assert stats["top_categories"][0]["category"] == "salary"


def test_edit_amount(cli):
    entry = cli.json("income", "add", "Gig", "-a", "100")
    edited = cli.json("income", "edit", str(entry["id"]), "-a", "150")
    assert edited["amount"] == 150.0


def test_negative_amount_fails(cli):
    result = cli.run("income", "add", "Bad", "-a", "-5")
    assert result.exit_code != 0
