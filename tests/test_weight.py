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
