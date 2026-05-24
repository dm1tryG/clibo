"""Tests for the shared parse_minutes / parse_hours helpers.

These power the H:MM notation across sleep / focus / meditate /
stretches / workout. Pinning them here so any change to the parsing
contract fails loudly in one focused place.
"""

from __future__ import annotations

import pytest
import typer

from clibo.core.base import parse_hours, parse_minutes

# ── parse_minutes ────────────────────────────────────────────────────────


def test_parse_minutes_plain_int_string():
    assert parse_minutes("45") == 45


def test_parse_minutes_plain_int():
    assert parse_minutes(45) == 45


def test_parse_minutes_hh_mm():
    assert parse_minutes("1:25") == 85


def test_parse_minutes_hh_mm_zero_hours():
    assert parse_minutes("0:25") == 25


def test_parse_minutes_hh_mm_two_hours():
    assert parse_minutes("2:00") == 120


def test_parse_minutes_strips_whitespace():
    assert parse_minutes("  45  ") == 45
    assert parse_minutes("1:25 ") == 85


def test_parse_minutes_bad_hh_mm_fails():
    with pytest.raises(typer.BadParameter):
        parse_minutes("1:bad")


def test_parse_minutes_bad_string_fails():
    with pytest.raises(typer.BadParameter):
        parse_minutes("lots")


# ── parse_hours ──────────────────────────────────────────────────────────


def test_parse_hours_decimal_string():
    assert parse_hours("7.5") == 7.5


def test_parse_hours_float():
    assert parse_hours(7.5) == 7.5


def test_parse_hours_int():
    assert parse_hours(8) == 8.0


def test_parse_hours_hh_mm():
    assert parse_hours("7:30") == 7.5


def test_parse_hours_hh_mm_zero_minutes():
    assert parse_hours("8:00") == 8.0


def test_parse_hours_hh_mm_quarter():
    assert parse_hours("6:15") == 6.25


def test_parse_hours_bad_hh_mm_fails():
    with pytest.raises(typer.BadParameter):
        parse_hours("7:bad")


def test_parse_hours_bad_string_fails():
    with pytest.raises(typer.BadParameter):
        parse_hours("lots")
