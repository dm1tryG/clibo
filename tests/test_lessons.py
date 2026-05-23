"""Tests for the 📓 lessons tool."""

from __future__ import annotations


def test_add_lesson(cli):
    data = cli.json(
        "lessons", "add",
        "always set max-attempts on retry logic",
        "-x", "infinite loop in prod last Tuesday",
        "-c", "coding",
        "-t", "reliability,retries",
    )
    assert data["takeaway"] == "always set max-attempts on retry logic"
    assert data["context"] == "infinite loop in prod last Tuesday"
    assert data["category"] == "coding"
    assert data["tags"] == "reliability,retries"


def test_list_filters_by_category(cli):
    cli.run("lessons", "add", "work lesson 1", "-c", "work")
    cli.run("lessons", "add", "life lesson 1", "-c", "life")
    cli.run("lessons", "add", "work lesson 2", "-c", "work")
    work = cli.json("lessons", "list", "-c", "work")
    assert len(work) == 2


def test_search_in_context(cli):
    cli.run("lessons", "add", "lesson 1", "-x", "during the migration")
    cli.run("lessons", "add", "lesson 2", "-x", "while writing the parser")
    results = cli.json("lessons", "search", "migration")
    assert len(results) == 1


def test_random_picks(cli):
    cli.run("lessons", "add", "only one")
    chosen = cli.json("lessons", "random")
    assert chosen["takeaway"] == "only one"


def test_random_without_lessons_fails(cli):
    result = cli.run("lessons", "random")
    assert result.exit_code != 0


def test_stats(cli):
    cli.run("lessons", "add", "a", "-c", "coding", "-x", "context")
    cli.run("lessons", "add", "b", "-c", "coding")
    cli.run("lessons", "add", "c", "-c", "life")
    stats = cli.json("lessons", "stats")
    assert stats["total"] == 3
    assert stats["by_category"]["coding"] == 2
    assert stats["with_context"] == 1
