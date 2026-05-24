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


# ── inline actions + fuzzy resolve + edit + rm-by-name (iter 109) ──


def test_add_with_inline_actions(cli):
    """Repeatable -A flag captures action items at meeting creation."""
    data = cli.json(
        "meetings", "add", "Sync",
        "-A", "Bob: send timeline",
        "-A", "Alice: draft proposal",
        "-A", "me: schedule follow-up",
    )
    assert data["action_items"] == 3
    assert data["open_actions"] == 3


def test_inline_action_with_owner_prefix(cli):
    """`-A 'Bob: foo'` parses to owner=Bob, summary=foo."""
    cli.run("meetings", "add", "Sync", "-A", "Bob: send timeline")
    shown = cli.json("meetings", "show", "Sync")
    assert len(shown["actions"]) == 1
    assert shown["actions"][0]["owner"] == "Bob"
    assert shown["actions"][0]["summary"] == "send timeline"


def test_inline_action_without_owner(cli):
    """`-A 'plain summary'` → owner=None."""
    cli.run("meetings", "add", "Sync", "-A", "review the docs")
    shown = cli.json("meetings", "show", "Sync")
    assert shown["actions"][0]["owner"] is None
    assert shown["actions"][0]["summary"] == "review the docs"


def test_inline_actions_skip_empty(cli):
    """Empty -A strings (e.g. -A '') don't create blank rows."""
    cli.run("meetings", "add", "Sync", "-A", "real one", "-A", "", "-A", "   ")
    shown = cli.json("meetings", "show", "Sync")
    assert len(shown["actions"]) == 1


def test_action_fuzzy_meeting_match(cli):
    """`meetings action 'Acme' ...` finds 'Acme Q3 roadmap' by substring."""
    cli.run("meetings", "add", "Acme Q3 roadmap")
    data = cli.json("meetings", "action", "Acme", "follow up")
    assert data["meeting"] == "Acme Q3 roadmap"


def test_action_fuzzy_picks_most_recent(cli):
    """Two meetings sharing a substring — pick the newer one."""
    cli.run("meetings", "add", "Acme Q2 review")
    cli.run("meetings", "add", "Acme Q3 roadmap")
    data = cli.json("meetings", "action", "Acme", "follow up")
    assert data["meeting"] == "Acme Q3 roadmap"


def test_show_fuzzy_match(cli):
    cli.run("meetings", "add", "Acme Q3 roadmap")
    data = cli.json("meetings", "show", "roadmap")
    assert data["title"] == "Acme Q3 roadmap"


def test_edit_by_name(cli):
    cli.run("meetings", "add", "Sync", "-N", "old notes")
    edited = cli.json("meetings", "edit", "Sync", "-N", "new notes")
    assert edited["notes"] == "new notes"


def test_edit_change_title(cli):
    cli.run("meetings", "add", "Old Title")
    edited = cli.json("meetings", "edit", "Old Title", "-t", "New Title")
    assert edited["title"] == "New Title"


def test_edit_unknown_fails(cli):
    result = cli.run("meetings", "edit", "ghost")
    assert result.exit_code != 0


def test_rm_by_name(cli):
    cli.run("meetings", "add", "Doomed")
    cli.json("meetings", "rm", "Doomed")
    listing = cli.json("meetings", "list")
    assert not any(m["title"] == "Doomed" for m in listing)


def test_rm_cascades_actions(cli):
    """Deleting a meeting also deletes its action items."""
    cli.run("meetings", "add", "Sync", "-A", "task one")
    cli.json("meetings", "rm", "Sync")
    actions = cli.json("meetings", "actions")
    assert actions == []
