"""Tests for the 💡 ideas tool."""

from __future__ import annotations


def test_capture_idea(cli):
    data = cli.json("ideas", "add", "build a plugin marketplace", "-t", "clibo,community")
    assert data["title"] == "build a plugin marketplace"
    assert data["status"] == "raw"
    assert data["tags"] == "clibo,community"


def test_move_through_lifecycle(cli):
    idea = cli.json("ideas", "add", "Pomodoro variant", "-D", "60/15 instead of 25/5")
    cli.run("ideas", "move", str(idea["id"]), "exploring")
    cli.run("ideas", "move", str(idea["id"]), "validated")
    shipped = cli.json("ideas", "move", str(idea["id"]), "shipped")
    assert shipped["status"] == "shipped"


def test_open_filter(cli):
    cli.run("ideas", "add", "Active 1", "-s", "raw")
    cli.run("ideas", "add", "Active 2", "-s", "exploring")
    cli.run("ideas", "add", "Done", "-s", "shipped")
    cli.run("ideas", "add", "Killed", "-s", "abandoned")
    open_ideas = cli.json("ideas", "list", "--open")
    titles = {i["title"] for i in open_ideas}
    assert titles == {"Active 1", "Active 2"}


def test_search_finds_in_description(cli):
    cli.run("ideas", "add", "X", "-D", "marketplace for plugins")
    cli.run("ideas", "add", "Y", "-D", "unrelated thing")
    results = cli.json("ideas", "search", "marketplace")
    assert len(results) == 1
    assert results[0]["title"] == "X"


def test_pipeline_counts(cli):
    cli.run("ideas", "add", "A", "-s", "raw")
    cli.run("ideas", "add", "B", "-s", "raw")
    cli.run("ideas", "add", "C", "-s", "shipped")
    pipe = cli.json("ideas", "pipeline")
    assert pipe["by_status"]["raw"] == 2
    assert pipe["by_status"]["shipped"] == 1
    assert pipe["total"] == 3


def test_invalid_status_fails(cli):
    result = cli.run("ideas", "add", "Bad", "-s", "incubating")
    assert result.exit_code != 0
