"""Tests for ``clibo import`` (paired with ``clibo export``)."""

from __future__ import annotations

import json


def test_round_trip(cli, tmp_path):
    cli.run("todo", "add", "Task A")
    cli.run("todo", "add", "Task B")
    cli.run("water", "drink", "500")
    dump = tmp_path / "dump.json"
    cli.run("export", str(dump))

    # wipe the todo table and re-import — the water row's primary key still
    # exists in the live DB, so OR IGNORE drops it; only the todos come back.
    for task in cli.json("todo", "list"):
        cli.run("todo", "rm", str(task["id"]))
    assert cli.json("todo", "list") == []

    result = cli.json("import", str(dump))
    assert result["tables"]["todo_task"] == 2
    assert len(cli.json("todo", "list")) == 2


def test_import_or_ignore_skips_existing(cli, tmp_path):
    cli.run("todo", "add", "Original")
    dump = tmp_path / "dump.json"
    cli.run("export", str(dump))

    # Add a new row, then re-import the dump — only the original should be skipped.
    cli.run("todo", "add", "Added later")
    result = cli.json("import", str(dump))
    # The original row's primary key conflicts; should be ignored (0 inserts).
    assert result["tables"].get("todo_task", 0) == 0
    assert len(cli.json("todo", "list")) == 2


def test_import_replace_wipes_first(cli, tmp_path):
    cli.run("todo", "add", "Old task")
    dump = tmp_path / "dump.json"
    cli.run("export", str(dump))

    # Add data that's not in the dump
    cli.run("todo", "add", "Will be wiped")
    assert len(cli.json("todo", "list")) == 2

    cli.run("import", str(dump), "--replace")
    tasks = cli.json("todo", "list")
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Old task"


def test_import_missing_file_fails(cli, tmp_path):
    result = cli.run("import", str(tmp_path / "nope.json"))
    assert result.exit_code != 0


def test_import_rejects_garbage(cli, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"not_a_clibo_export": True}))
    result = cli.run("import", str(bad))
    assert result.exit_code != 0
