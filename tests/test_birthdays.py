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
