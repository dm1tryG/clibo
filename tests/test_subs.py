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


# ── name-resolution on show/edit/cancel/rm (iter 85) ──


def test_subs_show_by_name(cli):
    cli.run("subs", "add", "Netflix", "-a", "16")
    data = cli.json("subs", "show", "Netflix")
    assert data["name"] == "Netflix"
    assert data["monthly_cost"] == 16.0


def test_subs_show_fuzzy_match(cli):
    cli.run("subs", "add", "Netflix Premium", "-a", "20")
    data = cli.json("subs", "show", "netflix")
    assert data["name"] == "Netflix Premium"


def test_subs_edit_by_name(cli):
    cli.run("subs", "add", "Netflix", "-a", "16")
    edited = cli.json("subs", "edit", "Netflix", "-a", "20")
    assert edited["amount"] == 20.0


def test_subs_cancel_by_name(cli):
    cli.run("subs", "add", "Netflix", "-a", "16")
    cli.run("subs", "cancel", "Netflix")
    listing = cli.json("subs", "list", "--all")
    netflix = next(s for s in listing if s["name"] == "Netflix")
    assert netflix["active"] is False


def test_subs_rm_by_name(cli):
    cli.run("subs", "add", "Spotify", "-a", "10")
    cli.json("subs", "rm", "Spotify")
    listing = cli.json("subs", "list", "--all")
    assert not any(s["name"] == "Spotify" for s in listing)


def test_subs_edit_rejects_bad_cycle(cli):
    cli.run("subs", "add", "Netflix", "-a", "16")
    result = cli.run("subs", "edit", "Netflix", "-c", "fortnightly")
    assert result.exit_code != 0


def test_subs_unknown_name_fails(cli):
    result = cli.run("subs", "show", "ghost")
    assert result.exit_code != 0
