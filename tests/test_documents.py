"""Tests for the 📑 documents tool."""

from __future__ import annotations

from datetime import date, timedelta


def test_add_basic(cli):
    data = cli.json(
        "documents", "add", "Passport",
        "-e", "2030-06-15", "-k", "passport",
    )
    assert data["name"] == "Passport"
    assert data["kind"] == "passport"
    assert data["expires"] == "2030-06-15"
    assert data["days_until"] > 0


def test_add_invalid_kind(cli):
    result = cli.run(
        "documents", "add", "Thing", "-e", "2030-01-01", "-k", "foo",
    )
    assert result.exit_code != 0


def test_add_with_issued_and_number(cli):
    data = cli.json(
        "documents", "add", "Driver's License",
        "-e", "2028-04-12", "-k", "license",
        "-i", "2018-04-12", "-#", "DL-12345-67",
    )
    assert data["issued"] == "2018-04-12"
    assert data["number"] == "DL-12345-67"


def test_add_rejects_issued_after_expires(cli):
    result = cli.run(
        "documents", "add", "Bad",
        "-e", "2020-01-01", "-i", "2025-01-01",
    )
    assert result.exit_code != 0


def test_add_accepts_natural_language_dates(cli):
    """Iter 57's parse_date extension means month-name forms work here too."""
    data = cli.json(
        "documents", "add", "Visa",
        "-e", "March 15 2028", "-k", "visa",
    )
    assert data["expires"] == "2028-03-15"


def test_urgency_buckets(cli):
    today = date.today()
    # critical: ≤ 30 days
    crit = cli.json("documents", "add", "Crit",
                     "-e", str(today + timedelta(days=10)))
    assert crit["urgency"] == "critical"
    # soon: ≤ 90 days
    soon = cli.json("documents", "add", "Soon",
                     "-e", str(today + timedelta(days=60)))
    assert soon["urgency"] == "soon"
    # watch: ≤ 1 year
    watch = cli.json("documents", "add", "Watch",
                      "-e", str(today + timedelta(days=200)))
    assert watch["urgency"] == "watch"
    # ok: > 1 year
    ok = cli.json("documents", "add", "OK",
                   "-e", str(today + timedelta(days=400)))
    assert ok["urgency"] == "ok"
    # expired
    expired = cli.json("documents", "add", "Old",
                        "-e", str(today - timedelta(days=5)))
    assert expired["urgency"] == "expired"


def test_list_default_hides_expired(cli):
    today = date.today()
    cli.run("documents", "add", "Active",
            "-e", str(today + timedelta(days=30)))
    cli.run("documents", "add", "Expired",
            "-e", str(today - timedelta(days=5)))
    rows = cli.json("documents", "list")
    names = {r["name"] for r in rows}
    assert "Active" in names
    assert "Expired" not in names


def test_list_with_expired_flag_includes_them(cli):
    today = date.today()
    cli.run("documents", "add", "Expired",
            "-e", str(today - timedelta(days=5)))
    rows = cli.json("documents", "list", "--expired")
    assert any(r["name"] == "Expired" for r in rows)


def test_list_filters_by_kind(cli):
    today = date.today()
    cli.run("documents", "add", "Passport",
            "-e", str(today + timedelta(days=30)), "-k", "passport")
    cli.run("documents", "add", "License",
            "-e", str(today + timedelta(days=30)), "-k", "license")
    only_passport = cli.json("documents", "list", "-k", "passport")
    assert {r["kind"] for r in only_passport} == {"passport"}


def test_list_sorted_soonest_first(cli):
    today = date.today()
    cli.run("documents", "add", "Far",
            "-e", str(today + timedelta(days=300)))
    cli.run("documents", "add", "Near",
            "-e", str(today + timedelta(days=15)))
    cli.run("documents", "add", "Middle",
            "-e", str(today + timedelta(days=60)))
    rows = cli.json("documents", "list")
    assert [r["name"] for r in rows] == ["Near", "Middle", "Far"]


def test_expiring_window(cli):
    today = date.today()
    cli.run("documents", "add", "WithinWindow",
            "-e", str(today + timedelta(days=20)))
    cli.run("documents", "add", "OutsideWindow",
            "-e", str(today + timedelta(days=200)))
    cli.run("documents", "add", "AlreadyExpired",
            "-e", str(today - timedelta(days=5)))
    rows = cli.json("documents", "expiring", "--days", "90")
    names = {r["name"] for r in rows}
    assert names == {"WithinWindow"}


def test_expired_lists_only_expired(cli):
    today = date.today()
    cli.run("documents", "add", "Gone",
            "-e", str(today - timedelta(days=10)))
    cli.run("documents", "add", "Still",
            "-e", str(today + timedelta(days=10)))
    rows = cli.json("documents", "expired")
    assert {r["name"] for r in rows} == {"Gone"}


def test_show(cli):
    entry = cli.json(
        "documents", "add", "Passport",
        "-e", "2030-06-15", "-k", "passport", "-#", "AB1234567",
    )
    fetched = cli.json("documents", "show", str(entry["id"]))
    assert fetched["name"] == "Passport"
    assert fetched["number"] == "AB1234567"


def test_rm(cli):
    entry = cli.json(
        "documents", "add", "Gone", "-e", "2030-01-01",
    )
    cli.run("documents", "rm", str(entry["id"]))
    rows = cli.json("documents", "list")
    assert rows == []


def test_stats(cli):
    today = date.today()
    cli.run("documents", "add", "Passport",
            "-e", str(today + timedelta(days=300)), "-k", "passport")
    cli.run("documents", "add", "License",
            "-e", str(today + timedelta(days=15)), "-k", "license")
    cli.run("documents", "add", "Old",
            "-e", str(today - timedelta(days=5)), "-k", "membership")
    data = cli.json("documents", "stats")
    assert data["total"] == 3
    assert data["active"] == 2
    assert data["expired"] == 1
    assert data["by_kind"] == {"passport": 1, "license": 1, "membership": 1}
    assert data["soonest"]["name"] == "License"
    assert data["farthest"]["name"] == "Passport"


def test_searchable_and_in_recent(cli):
    cli.run(
        "documents", "add", "Travel Insurance ACME",
        "-e", "2030-01-01", "-k", "insurance",
        "-#", "POL-12345", "-n", "covers winter sports",
    )
    hits = cli.json("search", "ACME")
    assert any(h["source"] == "documents" for h in hits["results"])
    by_number = cli.json("search", "POL-12345")
    assert any(h["source"] == "documents" for h in by_number["results"])
    recent = cli.json("recent")
    assert any(e["source"] == "documents" for e in recent["events"])
