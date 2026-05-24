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


# ── drive trips (iter 102) ──


def test_drive_with_km(cli):
    data = cli.json("car", "drive", "client meeting", "--km", "47",
                    "-c", "business")
    assert data["purpose"] == "client meeting"
    assert data["distance_km"] == 47.0
    assert data["category"] == "business"
    assert data["kind"] == "drive"


def test_drive_with_miles_converts_to_km(cli):
    """47 mi = 75.64 km (mile = 1.609344 km)."""
    data = cli.json("car", "drive", "trip", "--mi", "47", "-c", "business")
    assert data["distance_km"] == 75.64


def test_drive_with_odometer_pair_auto_computes_distance(cli):
    data = cli.json("car", "drive", "errands",
                    "--start-odo", "50000", "--end-odo", "50080")
    assert data["distance_km"] == 80.0
    assert data["odometer_start"] == 50000
    assert data["odometer_end"] == 50080


def test_drive_default_category_is_personal(cli):
    data = cli.json("car", "drive", "trip", "--km", "10")
    assert data["category"] == "personal"


def test_drive_rejects_no_distance(cli):
    result = cli.run("car", "drive", "trip")
    assert result.exit_code != 0


def test_drive_rejects_bad_category(cli):
    result = cli.run("car", "drive", "trip", "--km", "10", "-c", "vacation")
    assert result.exit_code != 0


def test_drive_rejects_negative_distance(cli):
    result = cli.run("car", "drive", "trip", "--km", "-5")
    assert result.exit_code != 0


def test_drive_rejects_inverted_odometer(cli):
    result = cli.run("car", "drive", "trip",
                     "--start-odo", "100", "--end-odo", "50")
    assert result.exit_code != 0


def test_list_includes_drives(cli):
    cli.run("car", "fuel", "45.5", "-o", "50000", "-c", "65")
    cli.run("car", "drive", "client meeting", "--km", "47", "-c", "business")
    rows = cli.json("car", "list")
    kinds = [r.get("kind") for r in rows]
    assert "fuel" in kinds
    assert "drive" in kinds


def test_list_filter_drive_only(cli):
    cli.run("car", "fuel", "30", "-c", "40")
    cli.run("car", "drive", "x", "--km", "10")
    rows = cli.json("car", "list", "-k", "drive")
    assert all(r["kind"] == "drive" for r in rows)


def test_stats_includes_drive_breakdown(cli):
    cli.run("car", "drive", "to-client", "--km", "47", "-c", "business")
    cli.run("car", "drive", "commute", "--km", "12", "-c", "commute")
    cli.run("car", "drive", "errands", "--km", "20", "-c", "personal")
    stats = cli.json("car", "stats")
    assert stats["drive_entries"] == 3
    assert stats["drive_total_km"] == 79.0
    by_cat = {r["category"]: r["km"] for r in stats["drive_by_category"]}
    assert by_cat["business"] == 47.0
    assert by_cat["commute"] == 12.0
    assert by_cat["personal"] == 20.0


def test_rm_drive_uses_flag(cli):
    cli.run("car", "drive", "doomed", "--km", "10")
    cli.json("car", "rm", "1", "--drive")
    rows = cli.json("car", "list", "-k", "drive")
    assert not any(r["kind"] == "drive" for r in rows)


def test_rm_fuel_unchanged_without_flag(cli):
    """`car rm 1` (no --drive) still deletes a fuel/service entry."""
    cli.run("car", "fuel", "30")
    cli.json("car", "rm", "1")
    rows = cli.json("car", "list", "-k", "fuel")
    assert rows == []
