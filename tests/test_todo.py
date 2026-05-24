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


# ── date filters on `todo list` (iter 117) ──


def test_list_due_today(cli):
    cli.run("todo", "add", "Call mom", "-d", "today")
    cli.run("todo", "add", "Buy milk", "-d", "tomorrow")
    cli.run("todo", "add", "No date")
    data = cli.json("todo", "list", "--due", "today")
    titles = [t["title"] for t in data]
    assert "Call mom" in titles
    assert "Buy milk" not in titles
    assert "No date" not in titles


def test_list_due_tomorrow(cli):
    cli.run("todo", "add", "Call mom", "-d", "today")
    cli.run("todo", "add", "Buy milk", "-d", "tomorrow")
    data = cli.json("todo", "list", "--due", "tomorrow")
    titles = [t["title"] for t in data]
    assert titles == ["Buy milk"]


def test_list_due_iso_date(cli):
    """`--due 2026-06-01` exact-matches by date."""
    cli.run("todo", "add", "Specific", "-d", "2026-06-01")
    cli.run("todo", "add", "Other", "-d", "2026-06-02")
    data = cli.json("todo", "list", "--due", "2026-06-01")
    assert [t["title"] for t in data] == ["Specific"]


def test_list_overdue(cli):
    cli.run("todo", "add", "Late", "-d", "5 days ago")
    cli.run("todo", "add", "Today", "-d", "today")
    cli.run("todo", "add", "Future", "-d", "tomorrow")
    data = cli.json("todo", "list", "--overdue")
    titles = [t["title"] for t in data]
    assert "Late" in titles
    assert "Today" not in titles
    assert "Future" not in titles


def test_list_overdue_skips_done(cli):
    """Overdue but completed tasks shouldn't appear in --overdue."""
    cli.run("todo", "add", "Done late", "-d", "5 days ago")
    cli.run("todo", "done", "1")
    cli.run("todo", "add", "Still late", "-d", "3 days ago")
    data = cli.json("todo", "list", "--overdue")
    assert [t["title"] for t in data] == ["Still late"]


def test_list_due_within_7(cli):
    """--due-within N captures overdue + today + next-N-days."""
    cli.run("todo", "add", "Past", "-d", "3 days ago")
    cli.run("todo", "add", "Today", "-d", "today")
    cli.run("todo", "add", "Soon", "-d", "in 5 days")
    cli.run("todo", "add", "Later", "-d", "in 15 days")
    cli.run("todo", "add", "No date")
    data = cli.json("todo", "list", "--due-within", "7")
    titles = {t["title"] for t in data}
    assert titles == {"Past", "Today", "Soon"}


def test_list_due_within_excludes_no_date(cli):
    """Date filters only apply to tasks that have a due date."""
    cli.run("todo", "add", "Dated", "-d", "tomorrow")
    cli.run("todo", "add", "Undated")
    data = cli.json("todo", "list", "--due-within", "30")
    assert [t["title"] for t in data] == ["Dated"]


def test_list_due_wins_over_due_within(cli):
    """When both --due and --due-within are passed, --due takes precedence."""
    cli.run("todo", "add", "Today", "-d", "today")
    cli.run("todo", "add", "Tomorrow", "-d", "tomorrow")
    data = cli.json("todo", "list", "--due", "today", "--due-within", "30")
    assert [t["title"] for t in data] == ["Today"]


def test_list_due_invalid_date_fails(cli):
    result = cli.run("todo", "list", "--due", "not a date")
    assert result.exit_code != 0


def test_list_due_within_negative_fails(cli):
    result = cli.run("todo", "list", "--due-within", "-5")
    assert result.exit_code != 0


def test_list_date_filters_combine_with_project(cli):
    """`--due today --project Acme` filters intersect."""
    cli.run("todo", "add", "Acme task", "-d", "today", "-P", "Acme")
    cli.run("todo", "add", "Other task", "-d", "today", "-P", "Other")
    data = cli.json("todo", "list", "--due", "today", "-P", "Acme")
    assert [t["title"] for t in data] == ["Acme task"]


# ── complete alias for done (iter 120) ──


def test_complete_alias_works(cli):
    """`todo complete` is the formal-prose synonym for `done`."""
    cli.run("todo", "add", "test task")
    data = cli.json("todo", "complete", "1")
    assert data["done"] is True
    assert data["done_at"] is not None


def test_done_still_works(cli):
    """Back-compat: original `done` verb unchanged."""
    cli.run("todo", "add", "another task")
    data = cli.json("todo", "done", "1")
    assert data["done"] is True
