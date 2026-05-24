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


def test_tags_covers_beyond_50_tools(cli):
    """ideas, quotes, lessons and cv all have a tags column."""
    cli.run("ideas", "add", "thing", "-t", "marketing")
    cli.run("quotes", "add", "wisdom", "-t", "marketing")
    cli.run("lessons", "add", "lesson one", "-t", "marketing")
    cli.run("cv", "add", "Marketing lead", "-o", "X", "-t", "marketing")
    data = cli.json("tags")
    marketing = next(r for r in data["tags"] if r["tag"] == "marketing")
    assert marketing["count"] == 4
    assert marketing["by_source"] == {
        "ideas": 1, "quotes": 1, "lessons": 1, "cv": 1
    }


# ── tagged: drill into one tag across every source ──


def test_tagged_pulls_from_every_source(cli):
    cli.run("notes", "add", "Note 1", "-b", "body", "-t", "urgent")
    cli.run("todo", "add", "Task A", "-t", "urgent")
    cli.run("ideas", "add", "Idea X", "-t", "urgent")
    data = cli.json("tagged", "urgent")
    sources = {it["source"] for it in data["items"]}
    assert sources == {"notes", "todo", "ideas"}
    assert data["count"] == 3
    assert data["tag"] == "urgent"


def test_tagged_excludes_other_tags(cli):
    cli.run("todo", "add", "Urgent task", "-t", "urgent")
    cli.run("todo", "add", "Work task", "-t", "work")
    data = cli.json("tagged", "urgent")
    titles = {it["label"] for it in data["items"]}
    assert titles == {"Urgent task"}


def test_tagged_case_insensitive(cli):
    cli.run("todo", "add", "Item", "-t", "Urgent")
    data = cli.json("tagged", "URGENT")
    assert data["count"] == 1
    assert data["tag"] == "urgent"


def test_tagged_multitag_match(cli):
    """An item with multiple tags appears under each one."""
    cli.run("notes", "add", "N", "-b", "b", "-t", "urgent,work")
    urgent = cli.json("tagged", "urgent")
    work = cli.json("tagged", "work")
    assert {it["label"] for it in urgent["items"]} == {"N"}
    assert {it["label"] for it in work["items"]} == {"N"}


def test_tagged_empty_state(cli):
    data = cli.json("tagged", "nonexistent")
    assert data == {"tag": "nonexistent", "count": 0, "items": []}


def test_tagged_item_carries_all_its_tags(cli):
    cli.run("notes", "add", "Multi", "-b", "b", "-t", "alpha,beta,gamma")
    data = cli.json("tagged", "beta")
    assert sorted(data["items"][0]["tags"]) == ["alpha", "beta", "gamma"]


def test_tagged_human_view_runs(cli):
    cli.run("todo", "add", "T1", "-t", "urgent")
    result = cli.run("tagged", "urgent")
    assert result.exit_code == 0
    assert "T1" in result.output
    assert "urgent" in result.output
