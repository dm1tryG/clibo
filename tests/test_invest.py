"""Tests for the 📈 invest tool."""

from __future__ import annotations

import pytest


def test_buy_basic(cli):
    data = cli.json("invest", "buy", "AAPL", "5", "200")
    assert data["ticker"] == "AAPL"
    assert data["action"] == "buy"
    assert data["shares"] == 5.0
    assert data["price_per_share"] == 200.0
    assert data["total"] == 1000.0
    assert data["kind"] == "stock"  # default


def test_buy_with_kind(cli):
    data = cli.json("invest", "buy", "BTC", "0.5", "42000", "-k", "crypto")
    assert data["kind"] == "crypto"
    assert data["shares"] == 0.5
    assert data["total"] == 21000.0


def test_buy_normalizes_ticker_to_upper(cli):
    data = cli.json("invest", "buy", "aapl", "5", "200")
    assert data["ticker"] == "AAPL"


def test_buy_rejects_zero_or_negative_shares(cli):
    assert cli.run("invest", "buy", "AAPL", "0", "200").exit_code != 0
    assert cli.run("invest", "buy", "AAPL", "-1", "200").exit_code != 0


def test_buy_rejects_negative_price(cli):
    result = cli.run("invest", "buy", "AAPL", "5", "-100")
    assert result.exit_code != 0


def test_buy_rejects_invalid_kind(cli):
    result = cli.run("invest", "buy", "AAPL", "5", "200", "-k", "foo")
    assert result.exit_code != 0


def test_positions_aggregate_multiple_buys(cli):
    cli.run("invest", "buy", "AAPL", "5", "200")    # basis: 1000
    cli.run("invest", "buy", "AAPL", "3", "220")    # basis: + 660 = 1660
    positions = cli.json("invest", "positions")
    aapl = next(p for p in positions if p["ticker"] == "AAPL")
    assert aapl["shares"] == 8.0
    assert aapl["cost_basis"] == 1660.0
    # avg cost = 1660 / 8 = 207.50
    assert aapl["avg_cost"] == pytest.approx(207.5, rel=1e-3)


def test_sell_reduces_position_and_computes_realized_pl(cli):
    cli.run("invest", "buy", "AAPL", "10", "100")   # basis 1000, avg 100
    data = cli.json("invest", "sell", "AAPL", "4", "150")
    # Per-share basis = 100, sold at 150, gain = 50 × 4 = 200
    assert data["realized_pl_this_sale"] == 200.0
    assert data["remaining_shares"] == 6.0
    positions = cli.json("invest", "positions")
    aapl = next(p for p in positions if p["ticker"] == "AAPL")
    assert aapl["shares"] == 6.0
    # Cost basis reduced proportionally: 1000 - (4 × 100) = 600
    assert aapl["cost_basis"] == 600.0


def test_sell_more_than_owned_fails(cli):
    cli.run("invest", "buy", "AAPL", "5", "100")
    result = cli.run("invest", "sell", "AAPL", "10", "120")
    assert result.exit_code != 0


def test_sell_with_no_position_fails(cli):
    result = cli.run("invest", "sell", "AAPL", "1", "100")
    assert result.exit_code != 0


def test_positions_excludes_fully_sold(cli):
    cli.run("invest", "buy", "AAPL", "5", "100")
    cli.run("invest", "sell", "AAPL", "5", "150")
    positions = cli.json("invest", "positions")
    tickers = {p["ticker"] for p in positions}
    assert "AAPL" not in tickers


def test_price_sets_and_drives_unrealized_pl(cli):
    cli.run("invest", "buy", "AAPL", "10", "100")
    cli.run("invest", "price", "AAPL", "120")
    positions = cli.json("invest", "positions")
    aapl = next(p for p in positions if p["ticker"] == "AAPL")
    assert aapl["current_price"] == 120.0
    assert aapl["market_value"] == 1200.0
    assert aapl["unrealized_pl"] == 200.0


def test_price_update_overrides_previous(cli):
    cli.run("invest", "buy", "AAPL", "10", "100")
    cli.run("invest", "price", "AAPL", "120")
    cli.run("invest", "price", "AAPL", "150")
    positions = cli.json("invest", "positions")
    aapl = next(p for p in positions if p["ticker"] == "AAPL")
    assert aapl["current_price"] == 150.0


def test_positions_show_no_price_as_null(cli):
    cli.run("invest", "buy", "AAPL", "10", "100")
    positions = cli.json("invest", "positions")
    aapl = next(p for p in positions if p["ticker"] == "AAPL")
    assert aapl["current_price"] is None
    assert aapl["market_value"] is None
    assert aapl["unrealized_pl"] is None


def test_show_includes_transactions(cli):
    cli.run("invest", "buy", "AAPL", "5", "200")
    cli.run("invest", "buy", "AAPL", "3", "220")
    data = cli.json("invest", "show", "AAPL")
    assert data["ticker"] == "AAPL"
    assert data["shares"] == 8.0
    assert len(data["transactions"]) == 2


def test_show_unknown_ticker_fails(cli):
    result = cli.run("invest", "show", "ZZZZ")
    assert result.exit_code != 0


def test_history_filters_by_ticker(cli):
    cli.run("invest", "buy", "AAPL", "5", "200")
    cli.run("invest", "buy", "GOOG", "2", "150")
    aapl_only = cli.json("invest", "history", "-t", "AAPL")
    assert {t["ticker"] for t in aapl_only} == {"AAPL"}


def test_rm(cli):
    txn = cli.json("invest", "buy", "AAPL", "5", "200")
    cli.run("invest", "rm", str(txn["id"]))
    positions = cli.json("invest", "positions")
    assert positions == []


def test_stats(cli):
    cli.run("invest", "buy", "AAPL", "10", "100")   # basis 1000
    cli.run("invest", "buy", "BTC", "0.5", "40000", "-k", "crypto")  # basis 20000
    cli.run("invest", "sell", "AAPL", "4", "150")   # realized: +200
    cli.run("invest", "price", "AAPL", "120")        # 6 left × (120-100) = 120 unrealized
    cli.run("invest", "price", "BTC", "45000")       # 0.5 × (45000-40000) = 2500 unrealized
    data = cli.json("invest", "stats")
    assert data["active_positions"] == 2
    # remaining basis = (1000 - 400) + 20000 = 20600
    assert data["total_invested_basis"] == 20600.0
    assert data["realized_pl_lifetime"] == 200.0
    assert data["unrealized_pl"] == pytest.approx(2620.0, rel=1e-3)
    assert data["by_kind_basis"] == {"stock": 600.0, "crypto": 20000.0}


def test_searchable_and_in_recent(cli):
    cli.run("invest", "buy", "AAPL", "5", "200", "-n", "long-term hold")
    by_ticker = cli.json("search", "AAPL")
    assert any(h["source"] == "invest" for h in by_ticker["results"])
    by_note = cli.json("search", "long-term")
    assert any(h["source"] == "invest" for h in by_note["results"])
    recent = cli.json("recent")
    assert any(e["source"] == "invest" for e in recent["events"])
