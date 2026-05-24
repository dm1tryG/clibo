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


# ── income year + stats.by_year (iter 122) ──


def test_income_year_current(cli):
    cli.run("income", "add", "Stripe", "-a", "5000", "-c", "salary")
    cli.run("income", "add", "Acme freelance", "-a", "2000", "-c", "freelance")
    data = cli.json("income", "year")
    from datetime import date
    assert data["year"] == date.today().year
    assert data["total"] == 7000
    assert data["entries"] == 2
    top_sources = {r["source"]: r["amount"] for r in data["top_sources"]}
    assert top_sources["Stripe"] == 5000
    assert top_sources["Acme freelance"] == 2000


def test_income_year_by_category(cli):
    cli.run("income", "add", "Stripe", "-a", "5000", "-c", "salary")
    cli.run("income", "add", "Acme", "-a", "2000", "-c", "freelance")
    data = cli.json("income", "year")
    by_cat = {r["category"]: r["amount"] for r in data["by_category"]}
    assert by_cat["salary"] == 5000
    assert by_cat["freelance"] == 2000


def test_income_year_specific(cli):
    cli.run("income", "add", "Stripe", "-a", "5000")
    cli.run("income", "add", "Old gig", "-a", "1000")
    import sqlite3

    from clibo.core import config
    db = sqlite3.connect(str(config.db_path()))
    db.execute("UPDATE income_entry SET entry_date='2024-12-31' WHERE source='Old gig'")
    db.commit()
    db.close()
    data = cli.json("income", "year", "-y", "2024")
    assert data["year"] == 2024
    assert data["total"] == 1000


def test_income_stats_includes_by_year(cli):
    cli.run("income", "add", "Stripe", "-a", "5000")
    data = cli.json("income", "stats")
    assert "by_year" in data
    assert data["by_year"][0]["total"] == 5000


# ── income year --category / --source filters (iter 126) ──


def test_income_year_filter_by_category(cli):
    """`--category salary` scopes to salary entries only."""
    cli.run("income", "add", "Acme", "-a", "5000", "-c", "salary")
    cli.run("income", "add", "Acme", "-a", "5000", "-c", "salary")
    cli.run("income", "add", "Stripe", "-a", "1000", "-c", "freelance")
    data = cli.json("income", "year", "--category", "salary")
    assert data["total"] == 10000.0
    assert data["entries"] == 2
    assert data["category"] == "salary"


def test_income_year_filter_by_source(cli):
    """`--source acme` answers 'how much did Acme pay me this year?'."""
    cli.run("income", "add", "Acme Corp", "-a", "5000", "-c", "salary")
    cli.run("income", "add", "Acme Corp", "-a", "3000", "-c", "salary")
    cli.run("income", "add", "Stripe", "-a", "1000", "-c", "freelance")
    data = cli.json("income", "year", "--source", "acme")
    assert data["total"] == 8000.0
    assert data["entries"] == 2
    assert data["source"] == "acme"


def test_income_year_combine_filters(cli):
    """`--category salary --source acme` intersects both filters."""
    cli.run("income", "add", "Acme", "-a", "5000", "-c", "salary")
    cli.run("income", "add", "Acme", "-a", "500", "-c", "gift")
    cli.run("income", "add", "Stripe", "-a", "1000", "-c", "salary")
    data = cli.json("income", "year", "--category", "salary", "--source", "acme")
    assert data["total"] == 5000.0
    assert data["entries"] == 1


def test_income_year_source_is_fuzzy_substring(cli):
    """`--source corp` matches `Acme Corp` (case-insensitive substring)."""
    cli.run("income", "add", "Acme Corp", "-a", "5000")
    cli.run("income", "add", "Stripe", "-a", "1000")
    data = cli.json("income", "year", "--source", "CORP")
    assert data["entries"] == 1
    assert data["total"] == 5000.0


def test_income_year_no_filter_keeps_fields_null(cli):
    """Without filters, both `category` and `source` are None."""
    cli.run("income", "add", "Anywhere", "-a", "100")
    data = cli.json("income", "year")
    assert data["category"] is None
    assert data["source"] is None


# ── income top: biggest paydays ──


def test_income_top_sorts_by_amount_desc(cli):
    cli.run("income", "add", "Acme", "-a", "5000", "-c", "salary")
    cli.run("income", "add", "Stripe", "-a", "1000", "-c", "freelance")
    cli.run("income", "add", "Gift", "-a", "100", "-c", "gift")
    rows = cli.json("income", "top")
    assert [r["amount"] for r in rows] == [5000.0, 1000.0, 100.0]


def test_income_top_limit_and_source_filter(cli):
    cli.run("income", "add", "Acme Corp", "-a", "5000", "-c", "salary")
    cli.run("income", "add", "Acme Corp", "-a", "3000", "-c", "salary")
    cli.run("income", "add", "Stripe", "-a", "1000")
    rows = cli.json("income", "top", "-n", "5", "--source", "acme")
    assert len(rows) == 2
    assert all("Acme" in r["source"] for r in rows)


def test_income_top_category_filter(cli):
    cli.run("income", "add", "Acme", "-a", "5000", "-c", "salary")
    cli.run("income", "add", "Stripe", "-a", "1000", "-c", "freelance")
    rows = cli.json("income", "top", "-c", "freelance")
    assert [r["amount"] for r in rows] == [1000.0]


def test_income_top_invalid_limit_fails(cli):
    result = cli.run("income", "top", "--limit", "-1")
    assert result.exit_code != 0
