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


# ── bare-command default + show alias (iter 103) ──


def test_bare_networth_runs_worth(cli):
    """`clibo networth` (no subcommand) shows the net worth summary."""
    cli.run("networth", "add", "Savings", "-a", "10000", "-t", "asset")
    cli.run("networth", "add", "Credit card", "-a", "1500", "-t", "liability")
    # Use the rendered output since the bare form doesn't have --json
    result = cli.run("networth")
    assert result.exit_code == 0
    out = result.stdout
    assert "Net worth" in out
    assert "10000" in out or "10,000" in out  # assets
    assert "1500" in out or "1,500" in out    # liabilities


def test_networth_show_alias(cli):
    """`clibo networth show` is identical to `clibo networth worth`."""
    cli.run("networth", "add", "Cash", "-a", "5000", "-t", "asset")
    show = cli.json("networth", "show")
    worth = cli.json("networth", "worth")
    assert show == worth
    assert show["net_worth"] == 5000.0


def test_networth_show_alias_with_json(cli):
    cli.run("networth", "add", "Cash", "-a", "5000", "-t", "asset")
    data = cli.json("networth", "show")
    assert data["net_worth"] == 5000.0
    assert data["total_assets"] == 5000.0


def test_networth_help_still_works(cli):
    """`clibo networth --help` still shows the menu after the bare change."""
    result = cli.run("networth", "--help")
    assert result.exit_code == 0
    assert "add" in result.stdout
    assert "snapshot" in result.stdout
