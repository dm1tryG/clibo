"""Tests for the 🚗 car tool."""

from __future__ import annotations


def test_fuel_logs_entry(cli):
    data = cli.json("car", "fuel", "50000", "45.5", "-c", "65")
    assert data["kind"] == "fuel"
    assert data["odometer"] == 50000
    assert data["volume"] == 45.5
    assert data["cost"] == 65.0


def test_service_logs_entry(cli):
    data = cli.json("car", "service", "Oil change", "-c", "80", "-o", "50200")
    assert data["kind"] == "service"
    assert data["service"] == "Oil change"
    assert data["cost"] == 80.0


def test_list_filters_by_kind(cli):
    cli.run("car", "fuel", "1000", "40", "-c", "50")
    cli.run("car", "service", "Tyres", "-c", "200")
    fuels = cli.json("car", "list", "-k", "fuel")
    assert len(fuels) == 1
    assert fuels[0]["kind"] == "fuel"


def test_stats_sums_costs(cli):
    cli.run("car", "fuel", "1000", "40", "-c", "50")
    cli.run("car", "fuel", "1500", "45", "-c", "60")
    cli.run("car", "service", "Wash", "-c", "20")
    stats = cli.json("car", "stats")
    assert stats["fuel_entries"] == 2
    assert stats["service_entries"] == 1
    assert stats["fuel_spent"] == 110.0
    assert stats["service_spent"] == 20.0
    assert stats["total_spent"] == 130.0


def test_stats_computes_economy(cli):
    # Economy uses fuel-ups after the first (which only sets the baseline odometer).
    cli.run("car", "fuel", "1000", "30", "-c", "0")
    cli.run("car", "fuel", "1500", "40", "-c", "0")
    stats = cli.json("car", "stats")
    assert stats["avg_economy_per_100"] == 8.0


def test_negative_volume_fails(cli):
    result = cli.run("car", "fuel", "1000", "-5")
    assert result.exit_code != 0
