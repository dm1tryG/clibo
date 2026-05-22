"""Tests for the 🔍 global search command."""

from __future__ import annotations


def test_search_finds_notes(cli):
    cli.run("notes", "add", "Idea", "-b", "Build a CLI toolbox with rainbow output")
    cli.run("notes", "add", "Other", "-b", "unrelated text")
    result = cli.json("search", "rainbow")
    assert result["count"] == 1
    assert result["results"][0]["source"] == "notes"


def test_search_spans_multiple_tools(cli):
    cli.run("notes", "add", "Acme research")
    cli.run("crm", "add", "Anna", "-c", "Acme")
    cli.run("todo", "add", "Email Acme about contract")
    cli.run("bookmark", "add", "https://acme.example.com", "-t", "Acme docs")
    result = cli.json("search", "acme")
    sources = {hit["source"] for hit in result["results"]}
    assert sources >= {"notes", "todo", "crm", "bookmark"}
    assert result["count"] >= 4


def test_search_includes_recipes_and_brag(cli):
    cli.run("recipes", "add", "Pasta", "-i", "spaghetti, tomatoes, basil")
    cli.run("brag", "add", "Shipped basil parser", "-i", "Cut parse time")
    result = cli.json("search", "basil")
    sources = {hit["source"] for hit in result["results"]}
    assert "recipes" in sources
    assert "brag" in sources


def test_search_no_matches(cli):
    cli.run("notes", "add", "Existing")
    result = cli.json("search", "nothing-matches-this")
    assert result["count"] == 0
    assert result["results"] == []


def test_search_each_result_has_snippet(cli):
    cli.run("journal", "write", "A productive day building widgets")
    result = cli.json("search", "widgets")
    assert all(hit["snippet"] for hit in result["results"])
