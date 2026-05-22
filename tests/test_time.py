"""Tests for the ⏱️ time tool."""

from __future__ import annotations


def test_log_time(cli):
    data = cli.json("time", "log", "clibo", "90", "-t", "coding")
    assert data["project"] == "clibo"
    assert data["minutes"] == 90


def test_start_stop_flow(cli):
    started = cli.json("time", "start", "writing")
    assert started["project"] == "writing"
    status = cli.json("time", "status")
    assert status["running"] is True
    stopped = cli.json("time", "stop")
    assert stopped["project"] == "writing"
    assert cli.json("time", "status")["running"] is False


def test_double_start_fails(cli):
    cli.run("time", "start", "one")
    result = cli.run("time", "start", "two")
    assert result.exit_code != 0


def test_report_groups_by_project(cli):
    cli.run("time", "log", "alpha", "60")
    cli.run("time", "log", "alpha", "30")
    cli.run("time", "log", "beta", "30")
    report = cli.json("time", "report")
    assert report["total_minutes"] == 120
    alpha = next(r for r in report["by_project"] if r["project"] == "alpha")
    assert alpha["minutes"] == 90


def test_stats_window(cli):
    cli.run("time", "log", "proj", "120")
    stats = cli.json("time", "stats")
    assert stats["total_minutes"] == 120
    assert stats["total_hours"] == 2.0


def test_stop_without_timer_fails(cli):
    result = cli.run("time", "stop")
    assert result.exit_code != 0
