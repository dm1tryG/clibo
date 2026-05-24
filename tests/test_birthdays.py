"""Tests for the 🎂 birthdays tool."""

from __future__ import annotations

from datetime import date


def test_add_birthday(cli):
    data = cli.json("birthdays", "add", "Mom", "-d", "04-15")
    assert data["person"] == "Mom"
    assert data["kind"] == "birthday"
    assert data["date"] == "04-15"


def test_add_with_year_computes_age(cli):
    data = cli.json("birthdays", "add", "Dad", "-d", "1960-06-20")
    assert data["turning"] is not None


def test_today_detects_today(cli):
    today = date.today()
    cli.run("birthdays", "add", "Now Person", "-d", f"{today.month:02d}-{today.day:02d}")
    result = cli.json("birthdays", "today")
    assert len(result["occasions"]) == 1


def test_upcoming_window(cli):
    today = date.today()
    cli.run("birthdays", "add", "Soon", "-d", f"{today.month:02d}-{today.day:02d}")
    upcoming = cli.json("birthdays", "upcoming", "--days", "7")
    assert len(upcoming) == 1


def test_anniversary_kind(cli):
    data = cli.json("birthdays", "add", "Wedding", "-d", "08-10", "-k", "anniversary")
    assert data["kind"] == "anniversary"


def test_invalid_kind_fails(cli):
    result = cli.run("birthdays", "add", "Bad", "-d", "01-01", "-k", "nameday")
    assert result.exit_code != 0


def test_add_with_month_name_date(cli):
    """'March 12' / 'Mar 12' / '12 March' all work as natural-language input."""
    data = cli.json("birthdays", "add", "Dad", "-d", "March 12")
    assert data["date"] == "03-12"
    assert data["turning"] is None  # no year provided

    data = cli.json("birthdays", "add", "Friend", "-d", "12 mar")
    assert data["date"] == "03-12"

    data = cli.json("birthdays", "add", "Sister", "-d", "Mar 12 1985")
    assert data["date"] == "03-12"
    assert data["turning"] is not None


# ── new edit + rm by person (iter 84) ──


def test_birthdays_edit_by_person(cli):
    cli.run("birthdays", "add", "Dad", "-d", "March 12")
    cli.run("birthdays", "edit", "Dad", "-d", "March 15")
    data = cli.json("birthdays", "list")
    dad = next(o for o in data if o["person"] == "Dad")
    assert dad["date"] == "03-15"


def test_birthdays_rm_by_person(cli):
    cli.run("birthdays", "add", "Dad", "-d", "March 12")
    cli.run("birthdays", "rm", "Dad")
    listing = cli.json("birthdays", "list")
    assert not any(o["person"] == "Dad" for o in listing)



# ── bare-command default (iter 110) ──


def test_bare_birthdays_runs_upcoming(cli):
    """`clibo birthdays` (no subcommand) runs `upcoming`."""
    result = cli.run("birthdays")
    assert result.exit_code == 0


def test_birthdays_help_still_works(cli):
    """`clibo birthdays --help` still shows the menu after the bare change."""
    result = cli.run("birthdays", "--help")
    assert result.exit_code == 0
    assert "upcoming" in result.stdout
