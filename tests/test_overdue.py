"""Tests for ``clibo overdue`` — past-due items across every tracker."""

from __future__ import annotations

from datetime import date, timedelta


def _ago(n: int) -> str:
    """ISO-format a date n days ago — `parse_date` accepts these."""
    return (date.today() - timedelta(days=n)).isoformat()


def _in(n: int) -> str:
    return (date.today() + timedelta(days=n)).isoformat()


def test_overdue_empty_state(cli):
    """Nothing overdue → graceful empty list, not a crash."""
    data = cli.json("overdue")
    assert data["total"] == 0
    assert data["items"] == []
    assert data["by_kind"] == {}
    assert data["asof"] == date.today().isoformat()
    assert data["max_days"] is None


def test_overdue_collects_tasks(cli):
    cli.run("todo", "add", "Late task", "-d", _ago(3))
    data = cli.json("overdue")
    assert data["total"] == 1
    it = data["items"][0]
    assert it["kind"] == "task"
    assert it["title"] == "Late task"
    assert it["days_overdue"] == 3


def test_overdue_collects_bills(cli):
    cli.run("bills", "add", "Internet", "-a", "50", "-d", _ago(5))
    data = cli.json("overdue")
    bills = [it for it in data["items"] if it["kind"] == "bill"]
    assert len(bills) == 1
    assert bills[0]["title"] == "Internet"
    assert bills[0]["days_overdue"] == 5


def test_overdue_collects_followups(cli):
    cli.run("followup", "add", "Anna", "-d", _ago(2), "-r", "doc")
    data = cli.json("overdue")
    f = [it for it in data["items"] if it["kind"] == "followup"]
    assert f[0]["title"] == "Anna"
    assert f[0]["detail"] == "doc"


def test_overdue_excludes_done_tasks(cli):
    """Tasks marked done don't appear — they're not overdue anymore."""
    cli.run("todo", "add", "Was late", "-d", _ago(3))
    cli.run("todo", "done", "1")
    data = cli.json("overdue")
    assert data["total"] == 0


def test_overdue_excludes_paid_bills(cli):
    cli.run("bills", "add", "Was late", "-a", "10", "-d", _ago(3))
    cli.run("bills", "pay", "1")
    assert cli.json("overdue")["total"] == 0


def test_overdue_excludes_future_tasks(cli):
    """A task due tomorrow is upcoming, not overdue."""
    cli.run("todo", "add", "Tomorrow", "-d", _in(1))
    assert cli.json("overdue")["total"] == 0


def test_overdue_excludes_today(cli):
    """Today isn't 'overdue' — it's due today."""
    cli.run("todo", "add", "Today", "-d", _in(0))
    assert cli.json("overdue")["total"] == 0


def test_overdue_sorts_most_overdue_first(cli):
    """Worst slip first — the order a human triages in."""
    cli.run("todo", "add", "Mildly late", "-d", _ago(1))
    cli.run("todo", "add", "Very late", "-d", _ago(10))
    cli.run("todo", "add", "Somewhat late", "-d", _ago(4))
    titles = [it["title"] for it in cli.json("overdue")["items"]]
    assert titles == ["Very late", "Somewhat late", "Mildly late"]


def test_overdue_days_filter_recent_only(cli):
    """`--days 3` shows only items overdue by ≤ 3 days."""
    cli.run("todo", "add", "Old", "-d", _ago(10))
    cli.run("todo", "add", "Recent", "-d", _ago(2))
    data = cli.json("overdue", "--days", "3")
    titles = [it["title"] for it in data["items"]]
    assert "Recent" in titles
    assert "Old" not in titles
    assert data["max_days"] == 3


def test_overdue_groups_by_kind(cli):
    """`by_kind` collates items of the same type for the human view."""
    cli.run("todo", "add", "Task A", "-d", _ago(3))
    cli.run("todo", "add", "Task B", "-d", _ago(1))
    cli.run("bills", "add", "Bill", "-a", "20", "-d", _ago(2))
    by_kind = cli.json("overdue")["by_kind"]
    assert len(by_kind["task"]) == 2
    assert len(by_kind["bill"]) == 1


def test_overdue_includes_chores(cli):
    """Chores past their next-due slot are overdue too."""
    cli.run("chores", "add", "Vacuum", "--every", "7")
    # Walk last_done back two cycles via direct SQL.
    import os
    import sqlite3
    home = os.environ["CLIBO_HOME"]
    con = sqlite3.connect(f"{home}/clibo.db")
    long_ago = (date.today() - timedelta(days=20)).isoformat()
    con.execute("UPDATE chores_chore SET last_done=? WHERE id=1", (long_ago,))
    con.commit()
    con.close()
    data = cli.json("overdue")
    chores = [it for it in data["items"] if it["kind"] == "chore"]
    assert len(chores) == 1
    assert chores[0]["title"] == "Vacuum"


def test_overdue_negative_days_fails(cli):
    result = cli.run("overdue", "--days", "-1")
    assert result.exit_code != 0


def test_overdue_human_view_runs(cli):
    """Smoke: Rich render works empty + populated."""
    empty = cli.run("overdue")
    assert empty.exit_code == 0
    assert "Nothing's overdue" in empty.output

    cli.run("todo", "add", "Slipped", "-d", _ago(3))
    populated = cli.run("overdue")
    assert populated.exit_code == 0
    assert "Slipped" in populated.output
    assert "3 days ago" in populated.output
