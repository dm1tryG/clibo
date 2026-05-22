"""Shared pytest fixtures.

Every test runs against a throwaway SQLite database in a temp directory, so
tests never touch a real ``~/.clibo`` and never interfere with each other.
"""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from clibo.core import db
from clibo.main import app


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Point clibo at a fresh database for the duration of one test."""
    monkeypatch.setenv("CLIBO_HOME", str(tmp_path))
    db.reset_engine()
    yield
    db.reset_engine()


@pytest.fixture
def cli():
    """A Typer ``CliRunner`` plus helpers for running clibo commands."""
    runner = CliRunner()

    class Clibo:
        def run(self, *args: str):
            """Invoke ``clibo <args>`` and return the Click result."""
            return runner.invoke(app, list(args))

        def json(self, *args: str):
            """Invoke a command with ``--json`` and parse its stdout."""
            result = runner.invoke(app, [*args, "--json"])
            assert result.exit_code == 0, result.output
            return json.loads(result.stdout)

    return Clibo()
