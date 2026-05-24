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


# ── name-resolution on show/edit/rm (iter 85) ──


def test_income_show_by_source_name(cli):
    cli.run("income", "add", "Acme Corp", "-a", "1200", "-c", "freelance")
    data = cli.json("income", "show", "Acme")
    assert data["source"] == "Acme Corp"


def test_income_edit_by_source_name(cli):
    cli.run("income", "add", "Acme Corp", "-a", "1200")
    edited = cli.json("income", "edit", "Acme", "-a", "1500")
    assert edited["amount"] == 1500.0


def test_income_rm_by_source_name(cli):
    cli.run("income", "add", "Stripe", "-a", "9500", "-c", "salary")
    cli.json("income", "rm", "Stripe")
    listing = cli.json("income", "list")
    assert not any(e["source"] == "Stripe" for e in listing)


def test_income_resolves_most_recent_when_multiple(cli):
    """One source can pay you many times — name lookups pick the latest."""
    cli.run("income", "add", "Acme Corp", "-a", "1000")
    latest = cli.json("income", "add", "Acme Corp", "-a", "2000")
    data = cli.json("income", "show", "Acme")
    assert data["id"] == latest["id"]
    assert data["amount"] == 2000.0


def test_income_unknown_source_fails(cli):
    result = cli.run("income", "show", "ghost")
    assert result.exit_code != 0



# ── bare-command default (iter 107) ──


def test_bare_income_runs_month(cli):
    """`clibo income` (no subcommand) runs `month`."""
    result = cli.run("income")
    assert result.exit_code == 0


def test_income_help_still_works(cli):
    """`clibo income --help` still shows the menu after the bare change."""
    result = cli.run("income", "--help")
    assert result.exit_code == 0
    assert "month" in result.stdout
