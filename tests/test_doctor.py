"""Tests for ``clibo doctor``."""

from __future__ import annotations

from clibo import __version__


def test_doctor_reports_install(cli):
    data = cli.json("doctor")
    assert data["version"] == __version__
    assert data["tools_built"] == 50
    assert data["tools_planned"] == 50
    assert data["healthy"] is True
    assert data["database_exists"] is True


def test_doctor_counts_rows(cli):
    cli.run("todo", "add", "task one")
    cli.run("todo", "add", "task two")
    cli.run("water", "drink", "500")
    data = cli.json("doctor")
    assert data["rows_per_table"].get("todo_task") == 2
    assert data["rows_per_table"].get("water_log") == 1
    assert data["total_rows"] >= 3


def test_doctor_python_version(cli):
    data = cli.json("doctor")
    parts = data["python"].split(".")
    assert int(parts[0]) >= 3
