"""Tests for the extended ``parse_date`` helper."""

from __future__ import annotations

from datetime import date, timedelta

from clibo.core.base import parse_date


def test_today_and_synonyms():
    assert parse_date("today") == date.today()
    assert parse_date("now") == date.today()
    assert parse_date(None) == date.today()


def test_yesterday_tomorrow():
    assert parse_date("yesterday") == date.today() - timedelta(days=1)
    assert parse_date("tomorrow") == date.today() + timedelta(days=1)


def test_relative_n_days():
    assert parse_date("3 days ago") == date.today() - timedelta(days=3)
    assert parse_date("7 days ago") == date.today() - timedelta(days=7)
    assert parse_date("5 days from now") == date.today() + timedelta(days=5)


def test_relative_weeks():
    assert parse_date("2 weeks ago") == date.today() - timedelta(days=14)
    assert parse_date("1 week from now") == date.today() + timedelta(days=7)


def test_last_next_shortcuts():
    assert parse_date("last week") == date.today() - timedelta(days=7)
    assert parse_date("next month") == date.today() + timedelta(days=30)


def test_iso_and_short_forms():
    assert parse_date("2026-05-23") == date(2026, 5, 23)
    assert parse_date("23.05.2026") == date(2026, 5, 23)


def test_unrecognized_raises():
    import pytest
    import typer
    with pytest.raises(typer.BadParameter):
        parse_date("whenever")
