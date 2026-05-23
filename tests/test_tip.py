"""Tests for the 🪙 tip tool."""

from __future__ import annotations

import pytest


def test_log_with_percent(cli):
    data = cli.json("tip", "log", "40", "-p", "20", "-v", "dinner")
    assert data["bill_amount"] == 40.0
    assert data["tip_amount"] == 8.0
    assert data["tip_percent"] == 20.0
    assert data["venue"] == "dinner"
    assert data["service_rating"] is None


def test_log_with_absolute_amount(cli):
    data = cli.json("tip", "log", "50", "-a", "10")
    assert data["bill_amount"] == 50.0
    assert data["tip_amount"] == 10.0
    assert data["tip_percent"] == 20.0


def test_log_requires_exactly_one_of_percent_or_amount(cli):
    neither = cli.run("tip", "log", "40")
    both = cli.run("tip", "log", "40", "-p", "20", "-a", "8")
    assert neither.exit_code != 0
    assert both.exit_code != 0


def test_log_rejects_invalid_rating(cli):
    result = cli.run("tip", "log", "40", "-p", "20", "-r", "9")
    assert result.exit_code != 0


def test_log_rejects_negative_bill(cli):
    result = cli.run("tip", "log", "-10", "-p", "20")
    assert result.exit_code != 0


def test_log_rejects_negative_percent(cli):
    result = cli.run("tip", "log", "40", "-p", "-5")
    assert result.exit_code != 0


def test_add_alias_works(cli):
    log_help = cli.run("tip", "log", "--help")
    add_help = cli.run("tip", "add", "--help")
    assert log_help.exit_code == 0 and "Usage:" in log_help.output
    assert add_help.exit_code == 0 and "Usage:" in add_help.output
    cli.run("tip", "add", "20", "-p", "15", "-v", "café")
    today = cli.json("tip", "today")
    assert today["count"] == 1
    assert today["entries"][0]["venue"] == "café"


def test_calc_does_not_save(cli):
    data = cli.json("tip", "calc", "40", "-p", "20")
    assert data["tip_amount"] == 8.0
    assert data["tip_percent"] == 20.0
    assert data["total"] == 48.0
    # nothing persisted
    today = cli.json("tip", "today")
    assert today["count"] == 0


def test_today_aggregates(cli):
    cli.run("tip", "log", "40", "-p", "20")     # tip = 8
    cli.run("tip", "log", "60", "-p", "15")     # tip = 9
    today = cli.json("tip", "today")
    assert today["count"] == 2
    assert today["total_billed"] == 100.0
    assert today["total_tipped"] == 17.0
    # weighted: 17 / 100 = 17%
    assert today["avg_percent"] == 17.0


def test_list_filters_by_venue(cli):
    cli.run("tip", "log", "40", "-p", "20", "-v", "diner")
    cli.run("tip", "log", "30", "-p", "15", "-v", "café")
    only_diner = cli.json("tip", "list", "--venue", "diner")
    assert {r["venue"] for r in only_diner} == {"diner"}


def test_stats_breakdowns(cli):
    cli.run("tip", "log", "40", "-p", "20", "-v", "diner", "-r", "5")
    cli.run("tip", "log", "60", "-p", "15", "-v", "diner", "-r", "3")
    cli.run("tip", "log", "20", "-p", "10", "-v", "café", "-r", "3")
    data = cli.json("tip", "stats")
    assert data["count"] == 3
    assert data["total_billed"] == 120.0
    assert data["total_tipped"] == pytest.approx(8 + 9 + 2, rel=1e-3)
    # by venue averages
    assert data["by_venue_avg_percent"]["diner"] == 17.5
    assert data["by_venue_avg_percent"]["café"] == 10.0
    # by rating averages — rating 3 entries: 15 and 10 → avg 12.5
    assert data["by_service_rating_avg_percent"]["3"] == 12.5
    assert data["by_service_rating_avg_percent"]["5"] == 20.0


def test_rm(cli):
    entry = cli.json("tip", "log", "40", "-p", "20")
    cli.run("tip", "rm", str(entry["id"]))
    today = cli.json("tip", "today")
    assert today["count"] == 0


def test_show(cli):
    entry = cli.json("tip", "log", "40", "-p", "20", "-v", "diner")
    fetched = cli.json("tip", "show", str(entry["id"]))
    assert fetched["venue"] == "diner"
    assert fetched["tip_percent"] == 20.0


def test_searchable_and_in_recent(cli):
    cli.run("tip", "log", "40", "-p", "20", "-v", "Joe's Diner")
    hits = cli.json("search", "Joe")
    assert any(h["source"] == "tip" for h in hits["results"])
    recent = cli.json("recent")
    assert any(e["source"] == "tip" for e in recent["events"])
