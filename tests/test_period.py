"""Tests for the 🌸 period tool."""

from __future__ import annotations


def test_start_and_end(cli):
    cli.run("period", "start", "-d", "2026-05-01", "-f", "medium")
    entries = cli.json("period", "list")
    assert entries[0]["start_date"] == "2026-05-01"
    assert entries[0]["flow"] == "medium"
    ended = cli.json("period", "end", "-d", "2026-05-05")
    assert ended["length_days"] == 5


def test_log_complete_period(cli):
    data = cli.json("period", "log", "-s", "2026-04-01", "-e", "2026-04-05")
    assert data["length_days"] == 5


def test_predict_uses_cycle_history(cli):
    cli.run("period", "start", "-d", "2026-03-01")
    cli.run("period", "start", "-d", "2026-03-29")
    pred = cli.json("period", "predict")
    assert pred["avg_cycle_days"] == 28
    assert pred["cycles_observed"] == 1
    assert pred["next_predicted_start"] == "2026-04-26"


def test_stats_computes_cycle(cli):
    cli.run("period", "start", "-d", "2026-01-01")
    cli.run("period", "start", "-d", "2026-01-29")
    cli.run("period", "start", "-d", "2026-02-26")
    stats = cli.json("period", "stats")
    assert stats["periods_logged"] == 3
    assert stats["avg_cycle_days"] == 28.0


def test_end_before_start_fails(cli):
    cli.run("period", "start", "-d", "2026-05-10")
    result = cli.run("period", "end", "-d", "2026-05-01")
    assert result.exit_code != 0


def test_predict_without_data_fails(cli):
    result = cli.run("period", "predict")
    assert result.exit_code != 0
