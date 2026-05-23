"""Tests for the 🧲 leads tool."""

from __future__ import annotations


def test_add_deal(cli):
    data = cli.json("leads", "add", "Acme contract", "-v", "5000", "-c", "Acme")
    assert data["name"] == "Acme contract"
    assert data["value"] == 5000.0
    assert data["stage"] == "new"


def test_move_stage(cli):
    deal = cli.json("leads", "add", "Deal", "-v", "1000")
    moved = cli.json("leads", "move", str(deal["id"]), "qualified")
    assert moved["stage"] == "qualified"


def test_pipeline_groups_open_deals(cli):
    cli.run("leads", "add", "A", "-v", "1000", "-s", "new")
    cli.run("leads", "add", "B", "-v", "2000", "-s", "qualified")
    cli.run("leads", "add", "C", "-v", "9000", "-s", "won")
    pipe = cli.json("leads", "pipeline")
    assert pipe["open_value"] == 3000.0
    qualified = next(r for r in pipe["by_stage"] if r["stage"] == "qualified")
    assert qualified["value"] == 2000.0


def test_stats_win_rate(cli):
    a = cli.json("leads", "add", "Won deal", "-v", "1000")
    b = cli.json("leads", "add", "Lost deal", "-v", "500")
    cli.run("leads", "move", str(a["id"]), "won")
    cli.run("leads", "move", str(b["id"]), "lost")
    stats = cli.json("leads", "stats")
    assert stats["won_deals"] == 1
    assert stats["win_rate_pct"] == 50.0


def test_invalid_stage_fails(cli):
    result = cli.run("leads", "add", "Bad", "-s", "negotiating")
    assert result.exit_code != 0


# ── name resolution (iter 84) ──


def test_leads_show_by_name(cli):
    cli.run("leads", "add", "BigCorp deal", "-v", "50000", "-s", "qualified")
    data = cli.json("leads", "show", "BigCorp")
    assert "BigCorp" in data["name"]


def test_leads_move_by_name(cli):
    cli.run("leads", "add", "BigCorp deal", "-v", "50000")
    cli.run("leads", "move", "BigCorp", "won")
    data = cli.json("leads", "show", "BigCorp")
    assert data["stage"] == "won"
