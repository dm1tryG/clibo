"""Tests for the 🗓️ meetings tool."""

from __future__ import annotations


def test_add_meeting(cli):
    data = cli.json("meetings", "add", "Weekly sync", "-a", "Anna,Bob")
    assert data["title"] == "Weekly sync"
    assert data["attendees"] == "Anna,Bob"


def test_action_items_flow(cli):
    cli.run("meetings", "add", "Planning")
    item = cli.json("meetings", "action", "Planning", "Write the spec", "-o", "Anna")
    assert item["summary"] == "Write the spec"
    detail = cli.json("meetings", "show", "Planning")
    assert detail["action_items"] == 1
    assert detail["open_actions"] == 1
    cli.run("meetings", "check", str(item["id"]))
    detail2 = cli.json("meetings", "show", "Planning")
    assert detail2["open_actions"] == 0


def test_actions_lists_open_across_meetings(cli):
    cli.run("meetings", "add", "M1")
    cli.run("meetings", "add", "M2")
    cli.run("meetings", "action", "M1", "Task one")
    cli.run("meetings", "action", "M2", "Task two")
    actions = cli.json("meetings", "actions")
    assert len(actions) == 2


def test_stats(cli):
    cli.run("meetings", "add", "Meeting")
    cli.run("meetings", "action", "Meeting", "An action")
    stats = cli.json("meetings", "stats")
    assert stats["total_meetings"] == 1
    assert stats["open_actions"] == 1


def test_action_unknown_meeting_fails(cli):
    result = cli.run("meetings", "action", "Ghost", "Task")
    assert result.exit_code != 0
