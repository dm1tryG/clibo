"""Tests for ``clibo tags``."""

from __future__ import annotations


def test_tags_empty(cli):
    data = cli.json("tags")
    assert data == {"count": 0, "tags": []}


def test_tag_counted_once_per_record(cli):
    cli.run("notes", "add", "First", "-t", "work")
    cli.run("notes", "add", "Second", "-t", "work,personal")
    data = cli.json("tags")
    counts = {row["tag"]: row["count"] for row in data["tags"]}
    assert counts == {"work": 2, "personal": 1}


def test_tag_groups_by_source(cli):
    cli.run("notes", "add", "Idea", "-t", "work")
    cli.run("todo", "add", "Task", "-t", "work")
    cli.run("bookmark", "add", "https://x.com", "--tag", "work,reading")
    data = cli.json("tags")
    work = next(r for r in data["tags"] if r["tag"] == "work")
    assert work["count"] == 3
    assert work["by_source"] == {"notes": 1, "todo": 1, "bookmark": 1}
    reading = next(r for r in data["tags"] if r["tag"] == "reading")
    assert reading["by_source"] == {"bookmark": 1}


def test_tags_normalised_to_lowercase(cli):
    cli.run("notes", "add", "Caps", "-t", "Work")
    cli.run("notes", "add", "lower", "-t", "work")
    data = cli.json("tags")
    assert len(data["tags"]) == 1
    assert data["tags"][0] == {"tag": "work", "count": 2, "by_source": {"notes": 2}}


def test_tags_sorted_by_count_desc(cli):
    cli.run("notes", "add", "a", "-t", "rare")
    cli.run("notes", "add", "b", "-t", "common")
    cli.run("notes", "add", "c", "-t", "common")
    cli.run("notes", "add", "d", "-t", "common")
    data = cli.json("tags")
    assert [r["tag"] for r in data["tags"]] == ["common", "rare"]


def test_tags_spans_many_sources(cli):
    cli.run("crm", "add", "Anna", "-t", "vip")
    cli.run("brag", "add", "Win", "-t", "vip")
    cli.run("recipes", "add", "Pasta", "-t", "vip")
    data = cli.json("tags")
    vip = next(r for r in data["tags"] if r["tag"] == "vip")
    assert vip["count"] == 3
    assert vip["by_source"] == {"crm": 1, "brag": 1, "recipes": 1}
