"""Tests for the 💼 jobs tool."""

from __future__ import annotations


def test_add_application(cli):
    data = cli.json("jobs", "add", "Acme", "Senior Engineer", "-l", "Remote")
    assert data["company"] == "Acme"
    assert data["role"] == "Senior Engineer"
    assert data["status"] == "applied"


def test_move_status(cli):
    job = cli.json("jobs", "add", "Globex", "Developer")
    moved = cli.json("jobs", "move", str(job["id"]), "interviewing")
    assert moved["status"] == "interviewing"


def test_list_filters_by_status(cli):
    cli.run("jobs", "add", "A", "Role A", "-s", "applied")
    cli.run("jobs", "add", "B", "Role B", "-s", "rejected")
    applied = cli.json("jobs", "list", "-s", "applied")
    assert len(applied) == 1
    assert applied[0]["company"] == "A"


def test_pipeline_counts(cli):
    cli.run("jobs", "add", "A", "R", "-s", "applied")
    cli.run("jobs", "add", "B", "R", "-s", "applied")
    cli.run("jobs", "add", "C", "R", "-s", "offer")
    pipe = cli.json("jobs", "pipeline")
    assert pipe["by_status"]["applied"] == 2
    assert pipe["by_status"]["offer"] == 1


def test_stats(cli):
    cli.run("jobs", "add", "A", "R", "-s", "interviewing")
    cli.run("jobs", "add", "B", "R", "-s", "rejected")
    stats = cli.json("jobs", "stats")
    assert stats["total"] == 2
    assert stats["interviewing"] == 1


def test_invalid_status_fails(cli):
    result = cli.run("jobs", "add", "Bad", "Role", "-s", "ghosted")
    assert result.exit_code != 0
