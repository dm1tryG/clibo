"""Tests for the ❤️ vitals tool."""

from __future__ import annotations


def test_bp_classifies(cli):
    normal = cli.json("vitals", "bp", "118", "75")
    assert normal["category"] == "normal"
    high = cli.json("vitals", "bp", "150", "95")
    assert high["category"] == "stage 2 hypertension"


def test_pulse_and_glucose(cli):
    pulse = cli.json("vitals", "pulse", "72")
    assert pulse["reading"] == "72 bpm"
    glucose = cli.json("vitals", "glucose", "95", "-u", "mg/dL")
    assert glucose["value"] == 95


def test_latest_per_kind(cli):
    cli.run("vitals", "pulse", "70")
    cli.run("vitals", "pulse", "80")
    cli.run("vitals", "spo2", "98")
    latest = cli.json("vitals", "latest")
    assert latest["pulse"]["value"] == 80
    assert latest["spo2"]["value"] == 98


def test_stats_for_kind(cli):
    cli.run("vitals", "pulse", "60")
    cli.run("vitals", "pulse", "80")
    stats = cli.json("vitals", "stats", "pulse")
    assert stats["readings"] == 2
    assert stats["avg"] == 70.0
    assert stats["min"] == 60
    assert stats["max"] == 80


def test_stats_unknown_kind_fails(cli):
    result = cli.run("vitals", "stats", "height")
    assert result.exit_code != 0
