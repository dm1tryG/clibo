"""Tests for ``clibo recent``."""

from __future__ import annotations


def test_recent_empty(cli):
    data = cli.json("recent")
    assert data["count"] == 0
    assert data["events"] == []


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


# ── symptom events in the activity feed (iter 96) ──


def test_recent_includes_symptom_events(cli):
    cli.run("symptom", "log", "back pain", "-i", "7", "-l", "lumbar")
    events = cli.json("recent")["events"]
    syms = [e for e in events if e["source"] == "symptom"]
    assert len(syms) == 1
    assert "back pain" in syms[0]["summary"]
    assert "7/10" in syms[0]["summary"]
    assert "lumbar" in syms[0]["summary"]


def test_recent_symptom_omits_location_when_missing(cli):
    cli.run("symptom", "log", "headache", "-i", "4")
    events = cli.json("recent")["events"]
    syms = [e for e in events if e["source"] == "symptom"]
    assert len(syms) == 1
    assert "(" not in syms[0]["summary"]  # no empty parens


# ── recent --tool filter: 'when did I last do X?' ──


def test_recent_tool_filter_returns_only_matching_source(cli):
    cli.run("workout", "log", "running", "--duration", "30")
    cli.run("expense", "add", "coffee", "-a", "5", "-c", "food")
    cli.run("journal", "write", "Test entry")
    data = cli.json("recent", "--tool", "workout")
    sources = {e["source"] for e in data["events"]}
    assert sources == {"workout"}
    assert data["count"] == 1
    assert data["tool"] == "workout"


def test_recent_tool_filter_case_insensitive(cli):
    cli.run("workout", "log", "running", "--duration", "30")
    data = cli.json("recent", "--tool", "WORKOUT")
    assert data["count"] == 1
    assert data["tool"] == "workout"


def test_recent_tool_filter_empty_when_no_matching(cli):
    """Filtering to a tool with no entries returns 0, not all entries."""
    cli.run("journal", "write", "Test entry")
    data = cli.json("recent", "--tool", "workout")
    assert data["count"] == 0
    assert data["events"] == []


def test_recent_no_filter_keeps_tool_null(cli):
    """Without `--tool`, the `tool` JSON field is null."""
    cli.run("journal", "write", "Test entry")
    data = cli.json("recent")
    assert data["tool"] is None


def test_recent_invalid_tool_fails(cli):
    """Typo'd source name should fail loudly, not silently return nothing."""
    result = cli.run("recent", "--tool", "nonsense")
    assert result.exit_code != 0
    assert "Unknown source" in result.output


def test_recent_invalid_tool_json_returns_error(cli):
    """Same in JSON mode — error shape rather than empty list."""
    result = cli.run("recent", "--tool", "nonsense", "--json")
    assert result.exit_code != 0
    # The shared `fail` helper emits a JSON error object on --json.
    import json
    data = json.loads(result.output)
    assert data.get("ok") is False
