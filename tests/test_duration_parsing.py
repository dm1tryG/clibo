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


# ── parse_weight_kg ──────────────────────────────────────────────────────


from clibo.core.base import parse_weight_kg  # noqa: E402


def test_parse_weight_kg_plain_float():
    assert parse_weight_kg(70.5) == 70.5


def test_parse_weight_kg_plain_string():
    assert parse_weight_kg("70.5") == 70.5


def test_parse_weight_kg_with_kg_suffix():
    assert parse_weight_kg("70.5kg") == 70.5


def test_parse_weight_kg_with_kg_suffix_and_space():
    assert parse_weight_kg("70.5 kg") == 70.5


def test_parse_weight_kg_lb_converts_to_kg():
    """165 lb × 0.45359237 = 74.84 kg (rounded to 2 dp)."""
    assert parse_weight_kg("165lb") == 74.84


def test_parse_weight_kg_lbs_plural_works():
    """'200 lbs' (with space + plural) → 90.72 kg."""
    assert parse_weight_kg("200 lbs") == 90.72


def test_parse_weight_kg_strips_case():
    """Mixed-case suffixes parse the same as lower-case."""
    assert parse_weight_kg("70KG") == 70.0
    assert parse_weight_kg("165LB") == 74.84


def test_parse_weight_kg_bad_input_fails():
    with pytest.raises(typer.BadParameter):
        parse_weight_kg("heavy")
