"""Tests for the 📉 debt tool."""

from __future__ import annotations


def test_add_debt(cli):
    data = cli.json("debt", "add", "Car loan", "-a", "8000", "-c", "Bank")
    assert data["name"] == "Car loan"
    assert data["principal"] == 8000.0
    assert data["remaining"] == 8000.0


def test_pay_reduces_remaining(cli):
    cli.run("debt", "add", "Loan", "-a", "1000")
    cli.run("debt", "pay", "Loan", "300")
    data = cli.json("debt", "pay", "Loan", "200")
    assert data["paid"] == 500.0
    assert data["remaining"] == 500.0
    assert data["progress_pct"] == 50.0


def test_cleared_flag(cli):
    cli.run("debt", "add", "Small", "-a", "100")
    data = cli.json("debt", "pay", "Small", "100")
    assert data["cleared"] is True


def test_show_lists_payments(cli):
    cli.run("debt", "add", "Mortgage", "-a", "5000")
    cli.run("debt", "pay", "Mortgage", "500")
    detail = cli.json("debt", "show", "Mortgage")
    assert len(detail["payments"]) == 1
    assert detail["payments"][0]["amount"] == 500.0


def test_stats_totals(cli):
    cli.run("debt", "add", "X", "-a", "2000")
    cli.run("debt", "pay", "X", "800")
    stats = cli.json("debt", "stats")
    assert stats["total_borrowed"] == 2000.0
    assert stats["total_paid"] == 800.0
    assert stats["total_remaining"] == 1200.0


def test_pay_unknown_debt_fails(cli):
    result = cli.run("debt", "pay", "Ghost", "100")
    assert result.exit_code != 0
