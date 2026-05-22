"""Tests for the 💊 meds tool."""

from __future__ import annotations


def test_add_medication(cli):
    data = cli.json("meds", "add", "Vitamin D", "-d", "1000IU", "-t", "1")
    assert data["name"] == "Vitamin D"
    assert data["dosage"] == "1000IU"
    assert data["times_per_day"] == 1


def test_take_by_name_and_id(cli):
    med = cli.json("meds", "add", "Aspirin", "-t", "2")
    by_name = cli.json("meds", "take", "Aspirin")
    assert by_name["taken_today"] == 1
    by_id = cli.json("meds", "take", str(med["id"]))
    assert by_id["taken_today"] == 2


def test_today_tracks_progress(cli):
    cli.run("meds", "add", "Iron", "-t", "2")
    cli.run("meds", "take", "Iron")
    today = cli.json("meds", "today")
    med = today["medications"][0]
    assert med["taken"] == 1
    assert med["remaining"] == 1
    assert med["done"] is False


def test_stop_hides_from_list(cli):
    med = cli.json("meds", "add", "Temp")
    cli.run("meds", "stop", str(med["id"]))
    assert cli.json("meds", "list") == []
    assert len(cli.json("meds", "list", "--all")) == 1


def test_adherence_stats(cli):
    cli.run("meds", "add", "Daily", "-t", "1")
    cli.run("meds", "take", "Daily")
    stats = cli.json("meds", "stats", "--days", "1")
    assert stats["doses_taken"] == 1
    assert stats["doses_expected"] == 1
    assert stats["adherence_pct"] == 100


def test_take_unknown_fails(cli):
    result = cli.run("meds", "take", "Nonexistent")
    assert result.exit_code != 0
