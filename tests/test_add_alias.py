"""Every time-stamped tool exposes both `log` and `add` for the same action.

The README/AGENTS docs promise predictable verbs (`add`, `list`, `show`, …)
across every tool. Time-stamped tools naturally use `log` as their primary
verb — that's kept — but `add` is registered as an alias so a user (or
agent) typing `clibo mood add 4` gets the same effect as `clibo mood log 4`.
"""

from __future__ import annotations

import pytest

TOOLS_WITH_LOG_ALIAS = [
    "mood",
    "weight",
    "sleep",
    "calorie",
    "focus",
    "meditate",
    "mileage",
    "period",
    "time",
    "workout",
]


@pytest.mark.parametrize("tool", TOOLS_WITH_LOG_ALIAS)
def test_add_is_alias_for_log(cli, tool):
    """`<tool> add --help` and `<tool> log --help` must both exist."""
    log_help = cli.run(tool, "log", "--help")
    add_help = cli.run(tool, "add", "--help")
    assert log_help.exit_code == 0
    assert add_help.exit_code == 0
    assert "Usage:" in log_help.output
    assert "Usage:" in add_help.output


def test_mood_add_actually_logs(cli):
    cli.run("mood", "add", "5", "-e", "great")
    today = cli.json("mood", "today")
    assert len(today["checkins"]) == 1
    assert today["checkins"][0]["score"] == 5


def test_weight_add_actually_logs(cli):
    cli.run("weight", "add", "78")
    data = cli.json("weight", "list")
    assert len(data) == 1
    assert data[0]["weight_kg"] == 78
