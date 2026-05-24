"""Tests for ``clibo upcoming`` / ``clibo agenda`` — the next-N-days view."""

from __future__ import annotations

from datetime import date, timedelta


def _in_days(n: int) -> str:
    """ISO-format a date n days from today — `parse_date` accepts these."""
    return (date.today() + timedelta(days=n)).isoformat()


def test_upcoming_empty_state(cli):
    """Nothing scheduled → snapshot still returns the window."""
    data = cli.json("upcoming")
    assert data["days"] == 7
    assert data["total"] == 0
    assert data["items"] == []
    assert data["by_date"] == []
    assert data["start"] == date.today().isoformat()


def test_upcoming_groups_tasks_bills_events(cli):
    cli.run("todo", "add", "Pay rent", "-d", _in_days(4), "-p", "high")
    cli.run("bills", "add", "Internet", "-a", "50", "-d", _in_days(3))
    cli.run("events", "add", "Dentist", "-d", _in_days(5))
    data = cli.json("upcoming")
    kinds = sorted(it["kind"] for it in data["items"])
    assert kinds == ["bill", "event", "task"]
    assert data["total"] == 3


def test_upcoming_sorts_chronologically(cli):
    cli.run("todo", "add", "Later", "-d", _in_days(5))
    cli.run("todo", "add", "Sooner", "-d", _in_days(1))
    cli.run("todo", "add", "Soonest", "-d", _in_days(0))
    items = cli.json("upcoming")["items"]
    titles = [it["title"] for it in items]
    assert titles == ["Soonest", "Sooner", "Later"]


def test_upcoming_excludes_overdue_tasks(cli):
    """Overdue tasks are someone else's problem (live on `today`)."""
    cli.run("todo", "add", "Late", "-d", _in_days(-3))
    cli.run("todo", "add", "Soon", "-d", _in_days(2))
    titles = [it["title"] for it in cli.json("upcoming")["items"]]
    assert "Late" not in titles
    assert "Soon" in titles


def test_upcoming_excludes_done_tasks(cli):
    cli.run("todo", "add", "Finished", "-d", _in_days(2))
    cli.run("todo", "done", "1")
    titles = [it["title"] for it in cli.json("upcoming")["items"]]
    assert "Finished" not in titles


def test_upcoming_excludes_paid_bills(cli):
    cli.run("bills", "add", "Internet", "-a", "50", "-d", _in_days(3))
    cli.run("bills", "pay", "1")
    kinds = [it["kind"] for it in cli.json("upcoming")["items"]]
    assert "bill" not in kinds


def test_upcoming_window_excludes_far_future(cli):
    """Default window is 7 days; items at day 15 don't appear."""
    cli.run("todo", "add", "Soon", "-d", _in_days(2))
    cli.run("todo", "add", "Far", "-d", _in_days(15))
    titles = [it["title"] for it in cli.json("upcoming")["items"]]
    assert "Soon" in titles
    assert "Far" not in titles


def test_upcoming_days_flag_widens(cli):
    """`--days 30` reaches further out."""
    cli.run("todo", "add", "Far", "-d", _in_days(15))
    titles = [it["title"] for it in cli.json("upcoming", "--days", "30")["items"]]
    assert "Far" in titles


def test_upcoming_includes_followups_and_birthdays(cli):
    """Follow-ups and birthdays make it into the agenda too."""
    cli.run("followup", "add", "Anna", "-d", _in_days(2), "-r", "doc review")
    birthday_md = (date.today() + timedelta(days=4)).strftime("%m-%d")
    cli.run("birthdays", "add", "Sarah", "-d", birthday_md)
    kinds = {it["kind"] for it in cli.json("upcoming")["items"]}
    assert "followup" in kinds
    assert "birthday" in kinds


def test_upcoming_by_date_groups_same_day_items(cli):
    """Two items on the same date land under one `by_date` entry."""
    cli.run("todo", "add", "Task one", "-d", _in_days(3))
    cli.run("bills", "add", "Bill one", "-a", "10", "-d", _in_days(3))
    data = cli.json("upcoming")
    same_day = [d for d in data["by_date"]
                if d["date"] == _in_days(3)]
    assert len(same_day) == 1
    assert len(same_day[0]["items"]) == 2


def test_upcoming_negative_days_fails(cli):
    result = cli.run("upcoming", "--days", "0")
    assert result.exit_code != 0


def test_agenda_alias_runs_upcoming(cli):
    """`clibo agenda` is a more natural-sounding synonym for `upcoming`."""
    cli.run("todo", "add", "Pay rent", "-d", _in_days(4))
    data = cli.json("agenda")
    assert data["days"] == 7
    assert any(it["title"] == "Pay rent" for it in data["items"])


def test_upcoming_human_view_runs(cli):
    """Rich human view shouldn't crash on empty or populated input."""
    empty = cli.run("upcoming")
    assert empty.exit_code == 0
    assert "Nothing on the radar" in empty.output

    cli.run("todo", "add", "Pay rent", "-d", _in_days(4), "-p", "high")
    populated = cli.run("upcoming")
    assert populated.exit_code == 0
    assert "Pay rent" in populated.output
    assert "This week" in populated.output
