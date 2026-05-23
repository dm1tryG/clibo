"""Tests for the 🚗 car tool."""

from __future__ import annotations


def test_fuel_logs_entry_backcompat_positional(cli):
    """The legacy two-positional form `car fuel ODO VOL` still works."""
    data = cli.json("car", "fuel", "50000", "45.5", "-c", "65")
    assert data["kind"] == "fuel"
    assert data["odometer"] == 50000
    assert data["volume"] == 45.5
    assert data["cost"] == 65.0


def test_fuel_without_odometer(cli):
    """The friendly form: VOLUME alone — common when filling up casually."""
    data = cli.json("car", "fuel", "45.5", "-c", "60")
    assert data["kind"] == "fuel"
    assert data["volume"] == 45.5
    assert data["odometer"] is None
    assert data["cost"] == 60.0


def test_fuel_with_odometer_option(cli):
    """The friendly form with optional `-o/--odometer`."""
    data = cli.json("car", "fuel", "45.5", "-o", "52340", "-c", "68")
    assert data["volume"] == 45.5
    assert data["odometer"] == 52340
    assert data["cost"] == 68.0


def test_fuel_rejects_both_old_and_new_odometer(cli):
    """If both the legacy positional and the `-o` option are given, fail."""
    result = cli.run("car", "fuel", "50000", "45.5", "-o", "60000")
    assert result.exit_code != 0


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


def test_stats_skips_no_odometer_fuelups(cli):
    """Fill-ups without an odometer don't crash economy — they're skipped."""
    cli.run("car", "fuel", "30")                # no odometer
    cli.run("car", "fuel", "40", "-o", "1500")  # odometer only
    cli.run("car", "fuel", "35", "-o", "2000")
    stats = cli.json("car", "stats")
    # Three fill-ups, but economy uses only the two with odometers,
    # so distance = 2000-1500 = 500 and fuel after first = 35.
    # 35 / 500 * 100 = 7.0
    assert stats["fuel_entries"] == 3
    assert stats["avg_economy_per_100"] == 7.0


def test_negative_volume_fails(cli):
    result = cli.run("car", "fuel", "1000", "-5")
    assert result.exit_code != 0
