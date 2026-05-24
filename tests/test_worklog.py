"""Tests for the 🗒️ worklog tool."""

from __future__ import annotations


def test_add_entry(cli):
    data = cli.json("worklog", "add", "Fixed the build", "-k", "done")
    assert data["summary"] == "Fixed the build"
    assert data["kind"] == "done"


def test_today_lists_entries(cli):
    cli.run("worklog", "add", "Task A")
    cli.run("worklog", "add", "Task B", "-k", "doing")
    today = cli.json("worklog", "today")
    assert len(today) == 2


def test_standup_buckets(cli):
    cli.run("worklog", "add", "Shipped feature", "-k", "done", "-d", "yesterday")
    cli.run("worklog", "add", "Reviewing PRs", "-k", "doing", "-d", "today")
    cli.run("worklog", "add", "Waiting on API", "-k", "blocked", "-d", "today")
    standup = cli.json("worklog", "standup")
    assert len(standup["yesterday_done"]) == 1
    assert len(standup["today_doing"]) == 1
    assert len(standup["blockers"]) == 1


def test_stats_by_kind(cli):
    cli.run("worklog", "add", "A", "-k", "done")
    cli.run("worklog", "add", "B", "-k", "done")
    cli.run("worklog", "add", "C", "-k", "blocked")
    stats = cli.json("worklog", "stats")
    assert stats["entries"] == 3
    assert stats["by_kind"]["done"] == 2
    assert stats["by_kind"]["blocked"] == 1


def test_invalid_kind_fails(cli):
    result = cli.run("worklog", "add", "Bad", "-k", "maybe")
    assert result.exit_code != 0



# ── bare-command default (iter 106) ──


def test_bare_worklog_runs_today(cli):
    """`clibo worklog` (no subcommand) runs `today`."""
    result = cli.run("worklog")
    assert result.exit_code == 0


def test_worklog_help_still_works(cli):
    """`clibo worklog --help` still shows the menu after the bare change."""
    result = cli.run("worklog", "--help")
    assert result.exit_code == 0
    assert "today" in result.stdout
