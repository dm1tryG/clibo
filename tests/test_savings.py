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


# ── savings stats: biggest_deposit / avg_deposit / deposits_count ──


def test_savings_stats_biggest_deposit_picks_max(cli):
    cli.run("savings", "add", "Emergency", "-t", "5000")
    cli.run("savings", "deposit", "Emergency", "200")
    cli.run("savings", "deposit", "Emergency", "1500")
    cli.run("savings", "deposit", "Emergency", "50")
    data = cli.json("savings", "stats")
    assert data["biggest_deposit"]["amount"] == 1500.0


def test_savings_stats_excludes_withdrawals_from_biggest(cli):
    """Withdrawals (negative amounts) shouldn't compete for 'biggest'."""
    cli.run("savings", "add", "G", "-t", "5000")
    cli.run("savings", "deposit", "G", "200")
    cli.run("savings", "withdraw", "G", "9999")
    data = cli.json("savings", "stats")
    assert data["biggest_deposit"]["amount"] == 200.0


def test_savings_stats_avg_deposit_excludes_withdrawals(cli):
    cli.run("savings", "add", "G", "-t", "5000")
    cli.run("savings", "deposit", "G", "100")
    cli.run("savings", "deposit", "G", "200")
    cli.run("savings", "withdraw", "G", "50")
    data = cli.json("savings", "stats")
    # Average over positive deposits only: (100+200)/2 = 150
    assert data["avg_deposit"] == 150.0
    assert data["deposits_count"] == 2


def test_savings_stats_no_deposits_yet(cli):
    """Goal with no deposits → null biggest, null avg, count 0."""
    cli.run("savings", "add", "Empty", "-t", "1000")
    data = cli.json("savings", "stats")
    assert data["biggest_deposit"] is None
    assert data["avg_deposit"] is None
    assert data["deposits_count"] == 0
