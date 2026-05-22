"""Tests for the 🎯 goals tool."""

from __future__ import annotations


def test_add_goal(cli):
    data = cli.json("goals", "add", "Learn Spanish", "-D", "Reach B1 level")
    assert data["name"] == "Learn Spanish"
    assert data["progress_pct"] == 0.0


def test_milestones_drive_progress(cli):
    cli.run("goals", "add", "Ship app")
    cli.run("goals", "milestone", "Ship app", "Design")
    m2 = cli.json("goals", "milestone", "Ship app", "Build")
    checked = cli.json("goals", "check", str(m2["id"]))
    assert checked["milestones_total"] == 2
    assert checked["milestones_done"] == 1
    assert checked["progress_pct"] == 50.0


def test_uncheck_milestone(cli):
    cli.run("goals", "add", "Goal")
    ms = cli.json("goals", "milestone", "Goal", "Step")
    cli.run("goals", "check", str(ms["id"]))
    data = cli.json("goals", "uncheck", str(ms["id"]))
    assert data["milestones_done"] == 0


def test_complete_goal(cli):
    cli.run("goals", "add", "Quick win")
    data = cli.json("goals", "complete", "Quick win")
    assert data["done"] is True
    assert cli.json("goals", "list") == []


def test_show_lists_milestones(cli):
    cli.run("goals", "add", "Big goal")
    cli.run("goals", "milestone", "Big goal", "First step")
    detail = cli.json("goals", "show", "Big goal")
    assert len(detail["milestones"]) == 1


def test_stats(cli):
    cli.run("goals", "add", "A")
    cli.run("goals", "add", "B")
    cli.run("goals", "complete", "A")
    stats = cli.json("goals", "stats")
    assert stats["total_goals"] == 2
    assert stats["achieved"] == 1


def test_milestone_unknown_goal_fails(cli):
    result = cli.run("goals", "milestone", "Ghost", "Step")
    assert result.exit_code != 0
