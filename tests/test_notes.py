"""Tests for the 📝 notes tool."""

from __future__ import annotations


def test_add_note(cli):
    data = cli.json("notes", "add", "Idea", "-b", "Build a CLI toolbox", "-t", "work")
    assert data["title"] == "Idea"
    assert data["body"] == "Build a CLI toolbox"


def test_search_matches_body(cli):
    cli.run("notes", "add", "Recipe", "-b", "needs flour and sugar")
    cli.run("notes", "add", "Other", "-b", "unrelated text")
    results = cli.json("notes", "search", "flour")
    assert len(results) == 1
    assert results[0]["title"] == "Recipe"


def test_pin_sorts_first(cli):
    cli.run("notes", "add", "First")
    second = cli.json("notes", "add", "Second")
    cli.run("notes", "pin", str(second["id"]))
    notes = cli.json("notes", "list")
    assert notes[0]["title"] == "Second"
    assert notes[0]["pinned"] is True


def test_edit_updates_body(cli):
    note = cli.json("notes", "add", "Draft", "-b", "old")
    edited = cli.json("notes", "edit", str(note["id"]), "-b", "new")
    assert edited["body"] == "new"


def test_remove(cli):
    note = cli.json("notes", "add", "Temp")
    removed = cli.json("notes", "rm", str(note["id"]))
    assert removed["deleted"] == note["id"]


def test_show_missing_fails(cli):
    result = cli.run("notes", "show", "999")
    assert result.exit_code != 0
