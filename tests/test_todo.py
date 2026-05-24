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


# ── delete alias (iter 121) — applies across every tool with `rm` ──


def test_delete_alias_works(cli):
    """`todo delete` is the English-natural synonym for `rm`."""
    cli.run("todo", "add", "doomed")
    data = cli.json("todo", "delete", "1")
    assert data["deleted"] == 1
    listing = cli.json("todo", "list")
    assert not any(t["id"] == 1 for t in listing)


def test_rm_still_works(cli):
    """Back-compat: original `rm` still works."""
    cli.run("todo", "add", "doomed")
    data = cli.json("todo", "rm", "1")
    assert data["deleted"] == 1


# ── update / remove aliases (iter 123) ──


def test_update_alias_works(cli):
    """`todo update` is the SQL-natural synonym for `edit`."""
    cli.run("todo", "add", "old title")
    data = cli.json("todo", "update", "1", "--title", "new title")
    assert data["title"] == "new title"


def test_remove_alias_works(cli):
    """`todo remove` is a third synonym for `rm` / `delete`."""
    cli.run("todo", "add", "doomed")
    data = cli.json("todo", "remove", "1")
    assert data["deleted"] == 1


def test_all_four_delete_synonyms_work(cli):
    """rm / delete / remove all do the same thing.

    SQLite reuses IDs after rows are deleted, so each iteration looks
    up the freshly-created task's id rather than assuming 1/2/3.
    """
    for verb in ("rm", "delete", "remove"):
        added = cli.json("todo", "add", f"task via {verb}")
        result = cli.run("todo", verb, str(added["id"]))
        assert result.exit_code == 0


# ── todo stats: oldest pending / most overdue / backlog age ──


def test_stats_oldest_pending_picks_earliest_created(cli, tmp_path):
    """Of two pending tasks, the one with the older created_at is oldest."""
    cli.run("todo", "add", "Old task")
    cli.run("todo", "add", "New task")
    # Backdate task 1's creation via SQL — `todo add` always stamps now.
    import sqlite3
    con = sqlite3.connect(f"{tmp_path}/clibo.db")
    con.execute("UPDATE todo_task SET created_at='2026-04-01 12:00:00' WHERE id=1")
    con.commit()
    con.close()
    data = cli.json("todo", "stats")
    assert data["oldest_pending"]["id"] == 1
    assert data["oldest_pending"]["title"] == "Old task"
    assert data["oldest_pending"]["age_days"] > 0


def test_stats_oldest_pending_ignores_done(cli, tmp_path):
    """Done tasks don't count as 'pending' for oldest_pending."""
    cli.run("todo", "add", "Old finished")
    cli.run("todo", "add", "Recent open")
    import sqlite3
    con = sqlite3.connect(f"{tmp_path}/clibo.db")
    con.execute("UPDATE todo_task SET created_at='2026-04-01 12:00:00' WHERE id=1")
    con.commit()
    con.close()
    cli.run("todo", "done", "1")
    data = cli.json("todo", "stats")
    # Only "Recent open" is pending now.
    assert data["oldest_pending"]["title"] == "Recent open"


def test_stats_most_overdue_picks_largest_days_past(cli):
    cli.run("todo", "add", "Less late", "-d", "2 days ago")
    cli.run("todo", "add", "Most late", "-d", "10 days ago")
    cli.run("todo", "add", "On time", "-d", "today")
    data = cli.json("todo", "stats")
    assert data["most_overdue"]["title"] == "Most late"
    assert data["most_overdue"]["days_overdue"] == 10


def test_stats_avg_backlog_age_days(cli, tmp_path):
    """Average of pending tasks' ages."""
    cli.run("todo", "add", "T1")
    cli.run("todo", "add", "T2")
    import sqlite3
    con = sqlite3.connect(f"{tmp_path}/clibo.db")
    con.execute("UPDATE todo_task SET created_at='2026-05-04 12:00:00' WHERE id=1")  # 20d
    con.execute("UPDATE todo_task SET created_at='2026-05-14 12:00:00' WHERE id=2")  # 10d
    con.commit()
    con.close()
    data = cli.json("todo", "stats")
    # 20 + 10 = 30, avg 15
    assert data["avg_backlog_age_days"] == 15.0


def test_stats_empty_returns_null_extremes(cli):
    """Empty DB → oldest_pending and most_overdue are null."""
    data = cli.json("todo", "stats")
    assert data["oldest_pending"] is None
    assert data["most_overdue"] is None
    assert data["avg_backlog_age_days"] == 0.0


def test_stats_most_overdue_null_when_no_overdue(cli):
    """No overdue → most_overdue is null even if there are pending tasks."""
    cli.run("todo", "add", "Future", "-d", "tomorrow")
    data = cli.json("todo", "stats")
    assert data["most_overdue"] is None
    # But oldest_pending still surfaces the future-dated task.
    assert data["oldest_pending"]["title"] == "Future"


# ── todo snooze — push due date forward ──


def test_snooze_pushes_existing_due_forward(cli):
    """A task due today snoozed by 1 lands tomorrow."""
    today_iso = date.today().isoformat()
    cli.run("todo", "add", "Has due", "-d", today_iso)
    data = cli.json("todo", "snooze", "1")
    assert data["due"] == (date.today() + timedelta(days=1)).isoformat()


def test_snooze_with_no_prior_due_anchors_on_today(cli):
    """No due → snooze sets it to today + N."""
    cli.run("todo", "add", "No due")
    data = cli.json("todo", "snooze", "1", "--days", "5")
    assert data["due"] == (date.today() + timedelta(days=5)).isoformat()


def test_snooze_rolls_forward_from_existing_due(cli):
    """A task already 3 days out, snoozed by 2, lands 5 days out."""
    target = (date.today() + timedelta(days=3)).isoformat()
    cli.run("todo", "add", "Future", "-d", target)
    data = cli.json("todo", "snooze", "1", "-d", "2")
    expected = (date.today() + timedelta(days=5)).isoformat()
    assert data["due"] == expected


def test_snooze_default_is_one_day(cli):
    """No `--days` → +1 day."""
    cli.run("todo", "add", "T")
    data = cli.json("todo", "snooze", "1")
    assert data["due"] == (date.today() + timedelta(days=1)).isoformat()


def test_snooze_zero_or_negative_days_fails(cli):
    cli.run("todo", "add", "T")
    assert cli.run("todo", "snooze", "1", "-d", "0").exit_code != 0
    assert cli.run("todo", "snooze", "1", "-d", "-1").exit_code != 0


def test_snooze_unknown_task_fails(cli):
    result = cli.run("todo", "snooze", "99")
    assert result.exit_code != 0


def test_snooze_does_not_affect_other_fields(cli):
    """Snooze only touches `due` — title, priority etc. are preserved."""
    cli.run("todo", "add", "Important", "-p", "high", "-d", "today")
    data = cli.json("todo", "snooze", "1", "-d", "3")
    assert data["title"] == "Important"
    assert data["priority"] == "high"
    assert data["done"] is False
