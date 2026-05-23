"""Tests for the 🧹 chores tool."""

from __future__ import annotations


def test_add_chore(cli):
    data = cli.json("chores", "add", "Vacuum", "-e", "7", "-a", "Anna")
    assert data["name"] == "Vacuum"
    assert data["frequency_days"] == 7
    assert data["assignee"] == "Anna"


def test_new_chore_is_due(cli):
    data = cli.json("chores", "add", "Dishes", "-e", "1")
    assert data["status"] == "due"


def test_done_pushes_next_due(cli):
    cli.run("chores", "add", "Mop", "-e", "5")
    done = cli.json("chores", "done", "Mop")
    assert done["status"] == "upcoming"
    assert done["last_done"] is not None


def test_due_lists_only_due(cli):
    cli.run("chores", "add", "Now chore", "-e", "3")
    later = cli.json("chores", "add", "Later chore", "-e", "3")
    cli.run("chores", "done", str(later["id"]))
    due = cli.json("chores", "due")
    assert len(due) == 1
    assert due[0]["name"] == "Now chore"


def test_stats(cli):
    cli.run("chores", "add", "A", "-e", "1")
    stats = cli.json("chores", "stats")
    assert stats["total"] == 1
    assert stats["due"] == 1


def test_invalid_frequency_fails(cli):
    result = cli.run("chores", "add", "Bad", "-e", "0")
    assert result.exit_code != 0
