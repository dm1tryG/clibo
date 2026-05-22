"""Tests for the 🐷 savings tool."""

from __future__ import annotations


def test_add_goal(cli):
    data = cli.json("savings", "add", "Laptop", "-t", "1500")
    assert data["name"] == "Laptop"
    assert data["target"] == 1500.0
    assert data["saved"] == 0.0


def test_deposit_tracks_progress(cli):
    cli.run("savings", "add", "Vacation", "-t", "1000")
    cli.run("savings", "deposit", "Vacation", "200")
    data = cli.json("savings", "deposit", "Vacation", "300")
    assert data["saved"] == 500.0
    assert data["remaining"] == 500.0
    assert data["progress_pct"] == 50.0


def test_withdraw_reduces_saved(cli):
    cli.run("savings", "add", "Fund", "-t", "1000")
    cli.run("savings", "deposit", "Fund", "400")
    data = cli.json("savings", "withdraw", "Fund", "100")
    assert data["saved"] == 300.0


def test_achieved_flag(cli):
    cli.run("savings", "add", "Phone", "-t", "500")
    data = cli.json("savings", "deposit", "Phone", "500")
    assert data["achieved"] is True


def test_stats_totals(cli):
    cli.run("savings", "add", "A", "-t", "1000")
    cli.run("savings", "add", "B", "-t", "1000")
    cli.run("savings", "deposit", "A", "750")
    stats = cli.json("savings", "stats")
    assert stats["total_target"] == 2000.0
    assert stats["total_saved"] == 750.0


def test_deposit_unknown_goal_fails(cli):
    result = cli.run("savings", "deposit", "Ghost", "100")
    assert result.exit_code != 0
