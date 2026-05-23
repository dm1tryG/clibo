"""Tests for ``clibo recent``."""

from __future__ import annotations


def test_recent_empty(cli):
    data = cli.json("recent")
    assert data == {"count": 0, "events": []}


def test_recent_lists_across_tools(cli):
    cli.run("todo", "add", "Ship clibo")
    cli.run("water", "drink", "500")
    cli.run("notes", "add", "Idea", "-b", "Build something")
    cli.run("habit", "add", "Read")
    cli.run("habit", "check", "Read")
    data = cli.json("recent")
    sources = {event["source"] for event in data["events"]}
    assert {"todo", "water", "notes", "habit"} <= sources
    assert data["count"] >= 4


def test_recent_summary_strings_are_meaningful(cli):
    cli.run("calorie", "log", "oatmeal", "-k", "320", "-m", "breakfast")
    cli.run("expense", "add", "lunch", "-a", "12", "-c", "food")
    data = cli.json("recent")
    calorie_event = next(e for e in data["events"] if e["source"] == "calorie")
    assert "oatmeal" in calorie_event["summary"]
    assert "320" in calorie_event["summary"]
    expense_event = next(e for e in data["events"] if e["source"] == "expense")
    assert "lunch" in expense_event["summary"]


def test_recent_sorted_newest_first(cli):
    cli.run("todo", "add", "First")
    cli.run("todo", "add", "Second")
    cli.run("todo", "add", "Third")
    events = cli.json("recent")["events"]
    todo_events = [e for e in events if e["source"] == "todo"]
    # newest-first ordering — Third should appear before Second/First
    titles = [e["summary"] for e in todo_events]
    assert titles.index("added task Third") < titles.index("added task First")


def test_recent_limit_honored(cli):
    for i in range(5):
        cli.run("notes", "add", f"Note {i}")
    data = cli.json("recent", "--limit", "3")
    assert data["count"] == 3
    assert len(data["events"]) == 3


def test_recent_includes_ago(cli):
    cli.run("notes", "add", "Just now")
    events = cli.json("recent")["events"]
    assert "ago" in events[0] or events[0]["ago"] == "just now"


# ── writing + reading-sessions in the activity feed (iter 93) ──


def test_recent_includes_writing_events(cli):
    cli.run("writing", "log", "novel", "-w", "1200", "-t", "45")
    events = cli.json("recent")["events"]
    writing = [e for e in events if e["source"] == "writing"]
    assert len(writing) == 1
    assert "1200w" in writing[0]["summary"]
    assert "novel" in writing[0]["summary"]
    assert "45 min" in writing[0]["summary"]


def test_recent_includes_reading_sessions(cli):
    cli.run("books", "add", "Atomic Habits", "-p", "320")
    cli.run("books", "read", "Atomic Habits", "30", "-t", "45")
    events = cli.json("recent")["events"]
    reading = [e for e in events if e["source"] == "reading"]
    assert len(reading) == 1
    assert "30p" in reading[0]["summary"]
    assert "Atomic Habits" in reading[0]["summary"]
