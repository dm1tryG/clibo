"""Tests for the 💰 networth tool."""

from __future__ import annotations


def test_add_asset_and_liability(cli):
    asset = cli.json("networth", "add", "Cash", "-a", "5000", "-t", "asset")
    assert asset["kind"] == "asset"
    debt = cli.json("networth", "add", "Loan", "-a", "2000", "-t", "liability")
    assert debt["kind"] == "liability"


def test_worth_computes_net(cli):
    cli.run("networth", "add", "Savings", "-a", "10000", "-t", "asset")
    cli.run("networth", "add", "Card", "-a", "3000", "-t", "liability")
    worth = cli.json("networth", "worth")
    assert worth["total_assets"] == 10000.0
    assert worth["total_liabilities"] == 3000.0
    assert worth["net_worth"] == 7000.0


def test_update_changes_value(cli):
    item = cli.json("networth", "add", "Stocks", "-a", "1000", "-t", "asset")
    updated = cli.json("networth", "update", str(item["id"]), "1500")
    assert updated["amount"] == 1500.0


def test_snapshot_and_history(cli):
    cli.run("networth", "add", "Cash", "-a", "4000", "-t", "asset")
    snap = cli.json("networth", "snapshot")
    assert snap["net_worth"] == 4000.0
    history = cli.json("networth", "history")
    assert len(history) == 1


def test_invalid_type_fails(cli):
    result = cli.run("networth", "add", "Mystery", "-a", "100", "-t", "investment")
    assert result.exit_code != 0
