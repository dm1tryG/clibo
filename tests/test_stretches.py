"""Tests for the 🧎 stretches tool."""

from __future__ import annotations

import pytest


def test_log_basic(cli):
    data = cli.json("stretches", "log", "hamstrings", "-m", "10")
    assert data["area"] == "hamstrings"
    assert data["duration_min"] == 10
    assert data["difficulty"] is None
    assert data["poses"] is None


def test_log_with_poses_and_difficulty(cli):
    data = cli.json(
        "stretches", "log", "hips", "-m", "15",
        "-p", "pigeon, downward-dog", "-D", "5", "-n", "deep session",
    )
    assert data["area"] == "hips"
    assert data["duration_min"] == 15
    assert data["difficulty"] == 5
    assert data["poses"] == "pigeon, downward-dog"
    assert data["note"] == "deep session"


def test_add_is_alias_for_log(cli):
    log_help = cli.run("stretches", "log", "--help")
    add_help = cli.run("stretches", "add", "--help")
    assert log_help.exit_code == 0 and "Usage:" in log_help.output
    assert add_help.exit_code == 0 and "Usage:" in add_help.output
    # Behavioural — `add` actually persists.
    cli.run("stretches", "add", "neck", "-m", "5")
    rows = cli.json("stretches", "list", "--days", "1")
    assert len(rows) == 1
    assert rows[0]["area"] == "neck"


def test_difficulty_out_of_range_rejected(cli):
    result = cli.run("stretches", "log", "hips", "-m", "10", "-D", "9")
    assert result.exit_code != 0


def test_zero_minutes_rejected(cli):
    result = cli.run("stretches", "log", "back", "-m", "0")
    assert result.exit_code != 0


def test_today_and_total(cli):
    cli.run("stretches", "log", "back", "-m", "10")
    cli.run("stretches", "log", "shoulders", "-m", "5")
    today = cli.json("stretches", "today")
    assert today["sessions"] == 2
    assert today["total_minutes"] == 15


def test_list_filters_by_area(cli):
    cli.run("stretches", "log", "hips", "-m", "10")
    cli.run("stretches", "log", "neck", "-m", "5")
    only_hips = cli.json("stretches", "list", "--area", "hips")
    assert {r["area"] for r in only_hips} == {"hips"}


def test_areas_breakdown(cli):
    cli.run("stretches", "log", "hips", "-m", "10")
    cli.run("stretches", "log", "hips", "-m", "5")
    cli.run("stretches", "log", "neck", "-m", "5")
    rows = cli.json("stretches", "areas")
    by = {r["area"]: r for r in rows}
    assert by["hips"]["sessions"] == 2
    assert by["hips"]["total_minutes"] == 15
    assert by["neck"]["sessions"] == 1


def test_stats(cli):
    cli.run("stretches", "log", "hips", "-m", "10", "-D", "3")
    cli.run("stretches", "log", "back", "-m", "20", "-D", "5")
    data = cli.json("stretches", "stats")
    assert data["sessions"] == 2
    assert data["total_minutes"] == 30
    assert data["avg_minutes_per_session"] == 15.0
    assert data["avg_difficulty"] == pytest.approx(4.0)
    assert data["top_area"] == "back"


def test_rm(cli):
    entry = cli.json("stretches", "log", "back", "-m", "5")
    cli.run("stretches", "rm", str(entry["id"]))
    rows = cli.json("stretches", "list")
    assert rows == []


def test_searchable_and_in_recent(cli):
    cli.run("stretches", "log", "hamstrings", "-m", "10",
            "-p", "forward fold", "-n", "felt much better")
    # appears in global search (poses + note are indexed)
    hits = cli.json("search", "forward")
    assert any(h["source"] == "stretches" for h in hits["results"])
    # appears in the recent feed
    recent = cli.json("recent")
    assert any(event["source"] == "stretches" for event in recent["events"])
