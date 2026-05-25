"""Tests for the ⚖️ weight tool."""

from __future__ import annotations


def test_log_records_weight(cli):
    data = cli.json("weight", "log", "75.5")
    assert data["weight_kg"] == 75.5


def test_bmi_uses_height(cli):
    cli.run("weight", "height", "--set", "178")
    data = cli.json("weight", "log", "75")
    assert "bmi" in data
    assert 23 < data["bmi"] < 24


def test_stats_tracks_change(cli):
    cli.run("weight", "log", "74", "-d", "yesterday")
    cli.run("weight", "log", "75", "-d", "today")
    stats = cli.json("weight", "stats")
    assert stats["measurements"] == 2
    assert stats["change_kg"] == 1.0
    assert stats["latest_kg"] == 75


def test_stats_without_data_fails(cli):
    result = cli.run("weight", "stats")
    assert result.exit_code != 0


# ── weight log accepts kg/lb unit suffixes ──


def test_weight_log_kg_suffix(cli):
    data = cli.json("weight", "log", "70.5kg")
    assert data["weight_kg"] == 70.5


def test_weight_log_lb_converts(cli):
    """165 lb → ~74.84 kg via 1 lb = 0.45359237 kg."""
    data = cli.json("weight", "log", "165lb")
    assert data["weight_kg"] == 74.84


def test_weight_log_lbs_with_space(cli):
    data = cli.json("weight", "log", "200 lbs")
    assert data["weight_kg"] == 90.72


def test_weight_log_plain_number_still_works(cli):
    data = cli.json("weight", "log", "72.3")
    assert data["weight_kg"] == 72.3


def test_weight_log_bad_input_fails(cli):
    result = cli.run("weight", "log", "heavy")
    assert result.exit_code != 0
