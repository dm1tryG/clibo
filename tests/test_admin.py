"""Tests for ``clibo backup`` / ``clibo restore`` / ``clibo export``."""

from __future__ import annotations

import json
from pathlib import Path


def test_backup_creates_file(cli, tmp_path):
    cli.run("todo", "add", "Sample task")
    dest = tmp_path / "backup.db"
    result = cli.json("backup", str(dest))
    assert dest.exists()
    assert result["path"] == str(dest)


def test_backup_default_path(cli):
    cli.run("todo", "add", "Sample")
    result = cli.json("backup")
    backup_path = Path(result["path"])
    assert backup_path.exists()
    assert backup_path.suffix == ".db"


def test_export_writes_json(cli, tmp_path):
    cli.run("todo", "add", "Exported task")
    cli.run("water", "drink", "250")
    dest = tmp_path / "dump.json"
    result = cli.json("export", str(dest))
    assert dest.exists()
    payload = json.loads(dest.read_text())
    assert payload["version"] == 1
    assert "todo_task" in payload["tables"]
    assert len(payload["tables"]["todo_task"]) == 1
    assert result["rows"] >= 2


def test_restore_round_trip(cli, tmp_path):
    cli.run("todo", "add", "Original task")
    backup = tmp_path / "snapshot.db"
    cli.run("backup", str(backup))
    # mutate after backup
    cli.run("todo", "add", "Added after backup")
    assert len(cli.json("todo", "list")) == 2
    # restore — only the original should remain
    cli.run("restore", str(backup))
    tasks = cli.json("todo", "list")
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Original task"


def test_restore_missing_file_fails(cli, tmp_path):
    missing = tmp_path / "nope.db"
    result = cli.run("restore", str(missing))
    assert result.exit_code != 0
