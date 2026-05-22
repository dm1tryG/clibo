"""Tests for the ✅ todo tool."""

from __future__ import annotations

from datetime import date, timedelta


def test_add_task(cli):
    data = cli.json("todo", "add", "Buy milk", "-p", "high")
    assert data["title"] == "Buy milk"
    assert data["priority"] == "high"
    assert data["done"] is False


def test_done_and_undone(cli):
    task = cli.json("todo", "add", "Write report")
    done = cli.json("todo", "done", str(task["id"]))
    assert done["done"] is True
    assert done["done_at"] is not None
    reopened = cli.json("todo", "undone", str(task["id"]))
    assert reopened["done"] is False


def test_list_hides_done_by_default(cli):
    task = cli.json("todo", "add", "One-off")
    cli.run("todo", "done", str(task["id"]))
    assert cli.json("todo", "list") == []
    assert len(cli.json("todo", "list", "--all")) == 1


def test_list_sorts_by_priority(cli):
    cli.run("todo", "add", "Low one", "-p", "low")
    cli.run("todo", "add", "High one", "-p", "high")
    tasks = cli.json("todo", "list")
    assert tasks[0]["title"] == "High one"


def test_overdue_flag(cli):
    past = (date.today() - timedelta(days=2)).isoformat()
    data = cli.json("todo", "add", "Late task", "-d", past)
    assert data["overdue"] is True


def test_stats_counts(cli):
    a = cli.json("todo", "add", "A")
    cli.run("todo", "add", "B")
    cli.run("todo", "done", str(a["id"]))
    stats = cli.json("todo", "stats")
    assert stats["total"] == 2
    assert stats["pending"] == 1
    assert stats["done"] == 1


def test_invalid_priority_fails(cli):
    result = cli.run("todo", "add", "Bad", "-p", "urgent")
    assert result.exit_code != 0
