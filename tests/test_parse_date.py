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


# ──────────────────────────────────────────────────────────────────────
# New natural-language vocabulary (iter 57).
# ──────────────────────────────────────────────────────────────────────


def test_in_n_units_is_synonym_for_from_now():
    """`in 2 weeks` is what the agent naturally translates to."""
    assert parse_date("in 14 days") == date.today() + timedelta(days=14)
    assert parse_date("in 2 weeks") == date.today() + timedelta(days=14)
    assert parse_date("in 1 month") == date.today() + timedelta(days=30)
    assert parse_date("in 3 years") == date.today() + timedelta(days=3 * 365)


def test_weekday_alone_is_next_occurrence():
    """`monday` means the next coming Monday — never today."""
    today = date.today()
    result = parse_date("monday")
    assert result.weekday() == 0
    assert result > today
    assert (result - today).days <= 7


def test_next_weekday_is_future():
    today = date.today()
    result = parse_date("next friday")
    assert result.weekday() == 4
    assert result > today


def test_this_weekday_allows_today():
    """`this <today's weekday>` returns today (the others jump to the future)."""
    today = date.today()
    name = ["monday", "tuesday", "wednesday", "thursday", "friday",
            "saturday", "sunday"][today.weekday()]
    assert parse_date(f"this {name}") == today


def test_last_weekday_is_past():
    today = date.today()
    result = parse_date("last monday")
    assert result.weekday() == 0
    assert result < today
    assert (today - result).days <= 7


def test_weekday_abbreviations():
    assert parse_date("mon").weekday() == 0
    assert parse_date("next fri").weekday() == 4
    assert parse_date("last wed").weekday() == 2
    assert parse_date("sun").weekday() == 6


def test_month_name_with_year():
    assert parse_date("March 12 1985") == date(1985, 3, 12)
    assert parse_date("12 March 1985") == date(1985, 3, 12)
    assert parse_date("Mar 12 1985") == date(1985, 3, 12)


def test_month_name_without_year_uses_current_year():
    expected = date(date.today().year, 3, 12)
    assert parse_date("March 12") == expected
    assert parse_date("12 March") == expected
    assert parse_date("Mar 12") == expected
    assert parse_date("12 mar") == expected


def test_month_name_trailing_dot():
    assert parse_date("Mar. 12 1985") == date(1985, 3, 12)
    assert parse_date("Sept. 1") == date(date.today().year, 9, 1)


def test_month_name_invalid_day_raises():
    import pytest
    import typer
    with pytest.raises(typer.BadParameter):
        parse_date("March 99")


def test_case_insensitive():
    assert parse_date("MARCH 12 1985") == date(1985, 3, 12)
    assert parse_date("Next FRIDAY").weekday() == 4
    assert parse_date("In 2 Weeks") == date.today() + timedelta(days=14)
