"""Tests for the 🌙 dreams tool."""

from __future__ import annotations


def test_add_dream(cli):
    data = cli.json(
        "dreams", "add", "flying over the city",
        "-D", "I could feel the wind",
        "-v", "5",
        "-s", "flying,city,water",
        "--lucid",
    )
    assert data["summary"] == "flying over the city"
    assert data["description"] == "I could feel the wind"
    assert data["vividness"] == 5
    assert data["lucid"] is True
    assert data["symbols"] == "flying,city,water"


def test_default_vividness(cli):
    data = cli.json("dreams", "add", "vague memory")
    assert data["vividness"] == 3
    assert data["lucid"] is False


def test_list_lucid_filter(cli):
    cli.run("dreams", "add", "normal dream")
    cli.run("dreams", "add", "lucid one", "--lucid")
    lucid = cli.json("dreams", "list", "--lucid")
    assert len(lucid) == 1
    assert lucid[0]["summary"] == "lucid one"


def test_symbols_frequency(cli):
    cli.run("dreams", "add", "d1", "-s", "flying,water")
    cli.run("dreams", "add", "d2", "-s", "flying,fire")
    cli.run("dreams", "add", "d3", "-s", "water")
    rows = cli.json("dreams", "symbols")
    by = {r["symbol"]: r["count"] for r in rows}
    assert by["flying"] == 2
    assert by["water"] == 2
    assert by["fire"] == 1


def test_search_in_description(cli):
    cli.run("dreams", "add", "d1", "-D", "felt warm sunshine")
    cli.run("dreams", "add", "d2", "-D", "endless rain")
    results = cli.json("dreams", "search", "sunshine")
    assert len(results) == 1


def test_stats_lucid_rate(cli):
    cli.run("dreams", "add", "a", "-v", "4")
    cli.run("dreams", "add", "b", "-v", "2", "--lucid")
    cli.run("dreams", "add", "c", "-v", "3", "--lucid")
    stats = cli.json("dreams", "stats")
    assert stats["total"] == 3
    assert stats["lucid"] == 2
    assert stats["lucid_rate_pct"] == 66.7
    assert stats["avg_vividness"] == 3.0


def test_invalid_vividness_fails(cli):
    result = cli.run("dreams", "add", "bad", "-v", "9")
    assert result.exit_code != 0



# ── bare-command default (iter 106) ──


def test_bare_dreams_runs_today(cli):
    """`clibo dreams` (no subcommand) runs `today`."""
    result = cli.run("dreams")
    assert result.exit_code == 0


def test_dreams_help_still_works(cli):
    """`clibo dreams --help` still shows the menu after the bare change."""
    result = cli.run("dreams", "--help")
    assert result.exit_code == 0
    assert "today" in result.stdout
