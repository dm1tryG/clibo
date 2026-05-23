"""Tests for the 📦 packages tool."""

from __future__ import annotations

from datetime import date, timedelta


def test_add_basic(cli):
    data = cli.json("packages", "add", "Amazon")
    assert data["sender"] == "Amazon"
    assert data["status"] == "ordered"
    assert data["tracking_number"] is None


def test_add_with_full_fields(cli):
    data = cli.json(
        "packages", "add", "Best Buy",
        "-t", "1Z9999999",
        "-c", "ups",
        "-D", "Mechanical keyboard",
        "-e", "in 3 days",
        "-n", "leave at door",
    )
    assert data["tracking_number"] == "1Z9999999"
    assert data["carrier"] == "ups"
    assert data["description"] == "Mechanical keyboard"
    assert data["expected_date"] is not None
    assert data["note"] == "leave at door"


def test_log_is_alias_for_add(cli):
    add_help = cli.run("packages", "add", "--help")
    log_help = cli.run("packages", "log", "--help")
    assert add_help.exit_code == 0 and "Usage:" in add_help.output
    assert log_help.exit_code == 0 and "Usage:" in log_help.output
    cli.run("packages", "log", "Amazon")
    rows = cli.json("packages", "list")
    assert len(rows) == 1


def test_add_rejects_invalid_status(cli):
    result = cli.run("packages", "add", "Amazon", "-s", "wormhole")
    assert result.exit_code != 0


def test_received_marks_delivered(cli):
    pkg = cli.json("packages", "add", "Amazon", "-e", "in 3 days")
    data = cli.json("packages", "received", str(pkg["id"]))
    assert data["status"] == "delivered"
    assert data["received_date"] == str(date.today())


def test_received_unknown_id_fails(cli):
    result = cli.run("packages", "received", "999")
    assert result.exit_code != 0


def test_update_changes_status_and_eta(cli):
    pkg = cli.json("packages", "add", "Amazon", "-e", "in 3 days")
    data = cli.json("packages", "update", str(pkg["id"]),
                     "-s", "in_transit", "-e", "in 1 day")
    assert data["status"] == "in_transit"


def test_update_rejects_invalid_status(cli):
    pkg = cli.json("packages", "add", "Amazon")
    result = cli.run("packages", "update", str(pkg["id"]), "-s", "lost-cosmos")
    assert result.exit_code != 0


def test_pending_excludes_delivered_and_lost(cli):
    a = cli.json("packages", "add", "A")
    cli.json("packages", "add", "B")
    cli.json("packages", "add", "C")
    cli.run("packages", "received", str(a["id"]))
    pending = cli.json("packages", "pending")
    names = {p["sender"] for p in pending}
    assert names == {"B", "C"}


def test_pending_is_late_flag(cli):
    today = date.today()
    cli.json("packages", "add", "LateOne",
              "-e", str(today - timedelta(days=1)))
    cli.json("packages", "add", "OnTime",
              "-e", str(today + timedelta(days=5)))
    pending = cli.json("packages", "pending")
    by = {p["sender"]: p for p in pending}
    assert by["LateOne"]["is_late"] is True
    assert by["OnTime"]["is_late"] is False


def test_pending_late_only_flag(cli):
    today = date.today()
    cli.json("packages", "add", "Late",
              "-e", str(today - timedelta(days=1)))
    cli.json("packages", "add", "Fine",
              "-e", str(today + timedelta(days=5)))
    only_late = cli.json("packages", "pending", "--late")
    assert {p["sender"] for p in only_late} == {"Late"}


def test_pending_sorts_late_first(cli):
    today = date.today()
    cli.json("packages", "add", "OnTime",
              "-e", str(today + timedelta(days=2)))
    cli.json("packages", "add", "Late",
              "-e", str(today - timedelta(days=1)))
    pending = cli.json("packages", "pending")
    # Late packages should come first.
    assert pending[0]["sender"] == "Late"


def test_list_active_only_by_default(cli):
    a = cli.json("packages", "add", "Delivered")
    cli.run("packages", "received", str(a["id"]))
    cli.json("packages", "add", "InFlight")
    active = cli.json("packages", "list")
    assert {p["sender"] for p in active} == {"InFlight"}


def test_list_with_all_includes_delivered(cli):
    a = cli.json("packages", "add", "Done")
    cli.run("packages", "received", str(a["id"]))
    cli.json("packages", "add", "Open")
    rows = cli.json("packages", "list", "--all")
    assert {p["sender"] for p in rows} == {"Done", "Open"}


def test_list_filters_by_status(cli):
    a = cli.json("packages", "add", "Done")
    cli.run("packages", "received", str(a["id"]))
    cli.json("packages", "add", "Open")
    delivered = cli.json("packages", "list", "-s", "delivered")
    assert {p["sender"] for p in delivered} == {"Done"}


def test_list_filters_by_carrier(cli):
    cli.json("packages", "add", "X", "-c", "ups")
    cli.json("packages", "add", "Y", "-c", "fedex")
    only_ups = cli.json("packages", "list", "-c", "ups")
    assert {p["sender"] for p in only_ups} == {"X"}


def test_show(cli):
    pkg = cli.json("packages", "add", "Amazon", "-D", "keyboard")
    fetched = cli.json("packages", "show", str(pkg["id"]))
    assert fetched["description"] == "keyboard"


def test_rm(cli):
    pkg = cli.json("packages", "add", "Amazon")
    cli.run("packages", "rm", str(pkg["id"]))
    assert cli.json("packages", "list") == []


def test_stats(cli):
    today = date.today()
    # Two delivered packages — one on-time, one late.
    on_time = cli.json("packages", "add", "OnTime",
                        "-e", str(today + timedelta(days=2)),
                        "--ordered", str(today - timedelta(days=2)))
    late = cli.json("packages", "add", "WasLate",
                     "-e", str(today - timedelta(days=2)),
                     "--ordered", str(today - timedelta(days=5)))
    cli.run("packages", "received", str(on_time["id"]))
    cli.run("packages", "received", str(late["id"]))
    cli.json("packages", "add", "StillOut", "-c", "ups")
    data = cli.json("packages", "stats")
    assert data["total"] == 3
    assert data["delivered_in_window"] == 2
    assert data["on_time"] == 1
    assert data["late_arrivals"] == 1
    assert data["currently_pending"] == 1
    assert data["by_status"]["delivered"] == 2


def test_searchable_and_in_recent(cli):
    cli.run(
        "packages", "add", "Best Buy",
        "-t", "TRACK-XYZ-12345",
        "-D", "mechanical keyboard",
        "-n", "for the office",
    )
    by_sender = cli.json("search", "Best Buy")
    assert any(h["source"] == "packages" for h in by_sender["results"])
    by_tracking = cli.json("search", "TRACK-XYZ")
    assert any(h["source"] == "packages" for h in by_tracking["results"])
    by_desc = cli.json("search", "keyboard")
    assert any(h["source"] == "packages" for h in by_desc["results"])
    recent = cli.json("recent")
    assert any(e["source"] == "packages" for e in recent["events"])
